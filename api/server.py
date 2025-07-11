from fastapi import FastAPI, File, UploadFile, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
import time
import json
import sys
import os
import shutil
import re
import hashlib
import asyncio
from pathlib import Path
import logging
from collections import defaultdict
from datetime import datetime, timedelta

# Add parent directory to path to import services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.Prep.read_config import read_config
from services.Prep.codebase import *
from services.LSH.lsh import *
from services.Similiarity.find_similiar_regions import *

app = FastAPI()

# Security Configuration
MAX_REQUEST_SIZE = 5 * 1024 * 1024  # 5MB
MAX_FILES_PER_REQUEST = 50
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB per file
RATE_LIMIT_REQUESTS = 10  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds
MAX_ANALYSIS_TIME = 300  # 5 minutes timeout

# Allowed file extensions for code analysis
ALLOWED_EXTENSIONS = {
    '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp',
    '.cs', '.rb', '.go', '.rs', '.php', '.swift', '.kt', '.scala', '.r',
    '.m', '.mm', '.pl', '.sh', '.bash', '.zsh', '.fish', '.vue', '.svelte'
}

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting storage
request_counts = defaultdict(list)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "codebase")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Security Helper Functions
def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    # Check for X-Forwarded-For header (common in reverse proxy setups)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    # Check for X-Real-IP header
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    
    # Fall back to client host
    return request.client.host if request.client else "unknown"

def is_rate_limited(client_ip: str) -> bool:
    """Check if client IP is rate limited"""
    now = datetime.now()
    # Clean old entries
    request_counts[client_ip] = [
        timestamp for timestamp in request_counts[client_ip]
        if now - timestamp < timedelta(seconds=RATE_LIMIT_WINDOW)
    ]
    
    # Check if rate limit exceeded
    if len(request_counts[client_ip]) >= RATE_LIMIT_REQUESTS:
        return True
    
    # Add current request
    request_counts[client_ip].append(now)
    return False

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal attacks"""
    if not filename:
        raise ValueError("Filename cannot be empty")
    
    # Remove directory traversal attempts
    filename = os.path.basename(filename)
    
    # Remove or replace dangerous characters
    filename = re.sub(r'[<>:"|?*]', '_', filename)
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)  # Remove control characters
    
    # Ensure filename isn't too long
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    # Prevent reserved names on Windows
    reserved_names = {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                     'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
                     'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'}
    name_without_ext = os.path.splitext(filename)[0].upper()
    if name_without_ext in reserved_names:
        filename = f"file_{filename}"
    
    return filename

def validate_file(file: UploadFile) -> None:
    """Validate uploaded file for security"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS and file_ext != '':  # Allow extensionless files
        raise HTTPException(
            status_code=400, 
            detail=f"File type '{file_ext}' not allowed. Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    
    # Check file size (this is approximate, actual size check happens during processing)
    if hasattr(file, 'size') and file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, 
            detail=f"File '{file.filename}' is too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )

def scan_file_content(content: bytes, filename: str) -> None:
    """Basic content scanning for malicious patterns"""
    try:
        # Try to decode as text for basic content scanning
        text_content = content.decode('utf-8', errors='ignore').lower()
        
        # Check for suspicious patterns (basic detection)
        suspicious_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',  # JavaScript URLs
            r'vbscript:',   # VBScript URLs
            r'on\w+\s*=',   # Event handlers
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, text_content, re.IGNORECASE | re.DOTALL):
                logger.warning(f"Suspicious content detected in file: {filename}")
                # Don't block, just log - could be legitimate code being analyzed
                break
                
    except Exception as e:
        # If content scanning fails, log but don't block
        logger.warning(f"Could not scan content of file {filename}: {str(e)}")

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        client_ip = get_client_ip(request)
        
        if is_rate_limited(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return Response(
                "Rate limit exceeded. Please wait before making another request.", 
                status_code=429
            )
        
        return await call_next(request)

class MaxRequestSizeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_size: int):
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            return Response("Request body is too large", status_code=413)
        return await call_next(request)

app.add_middleware(MaxRequestSizeMiddleware, max_size=MAX_REQUEST_SIZE)
app.add_middleware(RateLimitMiddleware)

@app.get("/")
async def health_check():
    return {"status": "ok", "message": "Refactor Analyzer API is running"}


@app.post("/refactor")
async def refactor(request: Request, files: List[UploadFile] = File(...)):
    start = time.time()
    saved_files = []
    client_ip = get_client_ip(request)
    
    try:
        # Security validations
        logger.info(f"Refactor request from IP: {client_ip}, files: {len(files)}")
        
        # Check number of files
        if len(files) > MAX_FILES_PER_REQUEST:
            raise HTTPException(
                status_code=400, 
                detail=f"Too many files. Maximum {MAX_FILES_PER_REQUEST} files allowed per request."
            )
        
        # Validate each file before processing
        total_size = 0
        for file in files:
            validate_file(file)
            # Estimate total size (approximate)
            if hasattr(file, 'size') and file.size:
                total_size += file.size
        
        if total_size > MAX_REQUEST_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Total upload size too large. Maximum {MAX_REQUEST_SIZE // (1024*1024)}MB allowed."
            )

        # Clean and prepare upload directory
        if os.path.exists(UPLOAD_DIR):
            # Instead of removing, create a unique subdirectory
            import uuid
            unique_id = str(uuid.uuid4())[:8]
            UPLOAD_DIR_SESSION = os.path.join(UPLOAD_DIR, f"session_{unique_id}")
        else:
            UPLOAD_DIR_SESSION = UPLOAD_DIR
            
        os.makedirs(UPLOAD_DIR_SESSION, exist_ok=True)
        logger.info(f"Using upload directory: {UPLOAD_DIR_SESSION}")

        # Save uploaded files with security measures
        for file in files:
            # Sanitize filename
            safe_filename = sanitize_filename(file.filename)
            file_path = os.path.join(UPLOAD_DIR_SESSION, safe_filename)
            
            # Ensure file path is within upload directory (additional safety)
            file_path = os.path.abspath(file_path)
            upload_dir_abs = os.path.abspath(UPLOAD_DIR_SESSION)
            if not file_path.startswith(upload_dir_abs):
                raise HTTPException(status_code=400, detail="Invalid file path detected")
            
            # Create subdirectories if needed (safely)
            file_dir = os.path.dirname(file_path)
            if file_dir != upload_dir_abs:
                os.makedirs(file_dir, exist_ok=True)
            
            # Read and validate file content
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"File '{safe_filename}' is too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
                )
            
            # Scan file content for basic security
            scan_file_content(content, safe_filename)
            
            # Save file
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            saved_files.append(safe_filename)
            
        logger.info(f"Successfully saved {len(saved_files)} files")

        # Run the algorithm with timeout protection
        async def run_analysis():
            logger.info("Starting code analysis...")
            
            # Temporarily change working directory for the analysis
            original_cwd = os.getcwd()
            try:
                # Change to project root for config access
                project_root = os.path.dirname(os.path.dirname(__file__))
                os.chdir(project_root)
                
                config = read_config()
                logger.info("Config loaded successfully")

                # Read codebase (update to use session directory)
                original_upload_dir = UPLOAD_DIR
                # Temporarily update the global variable for the analysis
                import services.Prep.codebase as codebase_module
                if hasattr(codebase_module, 'UPLOAD_DIR'):
                    codebase_module.UPLOAD_DIR = UPLOAD_DIR_SESSION
                
                file_mappings = read_codebase()
                logger.info(f"Processed {len(file_mappings)} files")

                # LSH algorithm
                signatures, similarity_adjacency_list = lsh(file_mappings, config["candidate_threshold"])
                logger.info("LSH algorithm completed")
                
                # Find similar regions
                region_threshold = -config["region_length"]
                similar_regions = find_similiar_regions(
                    signatures, similarity_adjacency_list, region_threshold, 
                    threshold=config["line_threshold"]
                )
                logger.info(f"Found {len(similar_regions)} similar regions")
                
                # Extract region code
                res = []
                for region in similar_regions:
                    file1 = region[1][0]
                    file2 = region[1][1]
                    file1_start = region[1][2]
                    file1_end = region[1][3]
                    file2_start = region[1][4]
                    file2_end = region[1][5]
                    res.append({
                        "regions": get_similiar_region_code(file1, file2, file1_start, file1_end, file2_start, file2_end), 
                        "file1": file1, 
                        "file2": file2,
                        "file1_start": file1_start,
                        "file1_end": file1_end,
                        "file2_start": file2_start,
                        "file2_end": file2_end
                    })
                
                return res, config, region_threshold
                
            finally:
                os.chdir(original_cwd)
        
        # Run analysis with timeout
        try:
            res, config, region_threshold = await asyncio.wait_for(
                run_analysis(), 
                timeout=MAX_ANALYSIS_TIME
            )
        except asyncio.TimeoutError:
            logger.warning(f"Analysis timeout for IP: {client_ip}")
            raise HTTPException(
                status_code=408, 
                detail=f"Analysis took too long. Maximum processing time is {MAX_ANALYSIS_TIME} seconds."
            )

        end = time.time()
        total_time = end - start

        logger.info(f"Analysis completed: {len(res)} regions found in {total_time:.2f}s for IP: {client_ip}")

        # Clean up session directory after successful analysis
        try:
            if 'UPLOAD_DIR_SESSION' in locals() and os.path.exists(UPLOAD_DIR_SESSION):
                shutil.rmtree(UPLOAD_DIR_SESSION)
                logger.info("Cleaned up session directory")
        except Exception as cleanup_error:
            logger.warning(f"Failed to clean up session directory: {cleanup_error}")

        # Return sanitized config (remove sensitive information)
        safe_config = {
            "region_length": config.get("region_length", "unknown"),
            "candidate_threshold": config.get("candidate_threshold", "unknown"),
            "line_threshold": config.get("line_threshold", "unknown")
        }

        return {
            "saved_files": saved_files,
            "similar_regions": res,
            "analysis_time": total_time,
            "total_regions_found": len(res),
            "region_threshold": -region_threshold,
            "config": safe_config
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions (they're already properly formatted)
        raise
    except Exception as e:
        end = time.time()
        total_time = end - start
        
        # Log the full error for debugging
        logger.error(f"Analysis error for IP {client_ip}: {str(e)}", exc_info=True)
        
        # Clean up session directory on error
        try:
            if 'UPLOAD_DIR_SESSION' in locals() and os.path.exists(UPLOAD_DIR_SESSION):
                shutil.rmtree(UPLOAD_DIR_SESSION)
                logger.info("Cleaned up session directory after error")
        except Exception as cleanup_error:
            logger.warning(f"Failed to clean up session directory after error: {cleanup_error}")
        
        # Return generic error message (don't leak internal details)
        raise HTTPException(
            status_code=500,
            detail="An error occurred during analysis. Please try again with a smaller codebase or contact support."
        )