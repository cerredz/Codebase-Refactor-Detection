from fastapi import FastAPI, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
import time
import json
import sys
import os
import shutil

# Add parent directory to path to import services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))  # Go up to repo root
sys.path.insert(0, project_root)

from services.Prep.read_config import read_config
from services.Prep.codebase import *
from services.LSH.lsh import *
from services.Similiarity.find_similiar_regions import *

app = FastAPI()
MAX_REQUEST_SIZE = 5 * 1024 * 1024 # 5MB

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

@app.get("/")
async def health_check():
    return {"status": "ok", "message": "Refactor Analyzer API is running"}


@app.post("/refactor")
async def refactor(files: List[UploadFile] = File(...)):
    start = time.time()
    saved_files = []
    
    try:
        # delete old codebase if it exists
        if os.path.exists(UPLOAD_DIR):
            shutil.rmtree(UPLOAD_DIR)
               
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # save uploaded files/subfolders to codebase directory
        for file in files:
            file_path = os.path.join(UPLOAD_DIR, file.filename)
            
            # Create subdirectories if needed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(file.filename)

        # run the algorithm - same as main.py
        print("Reading config file...")
        config = read_config()

        # read codebase
        print("Running algorithm to suggest codebase refactors...")
        file_mappings = read_codebase() # normalized code of all files, mapping to original file index

        # find similar lines using lsh
        print("Running the lsh algorithm for similarity searching...")
        signatures, similarity_adjacency_list = lsh(file_mappings, config["candidate_threshold"]) # run the lsh algorithm to hash similar lines
        
        # find similar regions using graph + sliding window
        print("Finding similar regions of code...")
        region_threshold = -config["region_length"] # how many lines of code need to be similar to determine a similar region
        similar_regions = find_similiar_regions(signatures, similarity_adjacency_list, region_threshold, threshold=config["line_threshold"])
        res = []

        # actually get regions of code in similar regions
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

        end = time.time()
        total_time = end - start

        print(f"Found {len(res)} region/s of code greater than {-region_threshold} lines of code in {total_time} seconds.")

        return {
            "saved_files": saved_files,
            "similar_regions": res,
            "analysis_time": total_time,
            "total_regions_found": len(res),
            "region_threshold": -region_threshold,
            "config": config
        }
    
    except Exception as e:
        end = time.time()
        total_time = end - start
        print(f"Error during analysis: {str(e)}")
        return {
            "error": str(e),
            "analysis_time": total_time,
            "saved_files": saved_files
        }