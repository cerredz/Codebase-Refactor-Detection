'''
Class to handle user Authentication:
- handles creating header footprints
- handles creating functions thats data will be used prior to making server requests from client
- (does not handle corresponding verification function, will be done in middleware class)
- 
'''

import jwt
import hashlib
import hmac
import time
import secrets
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import os

class Auth:
    
    def generate_jwt_token(self, user_id: str, role: str, expires_in_minutes: int = 60) -> str:
        """
        PURPOSE: Generates JWT tokens for authenticated user sessions
        SECURITY ASPECT: Authentication & Authorization
        USAGE: Client receives this token after login, sends in Authorization header
        MIDDLEWARE VERIFICATION: Validates token signature, expiry, and extracts user context
        """
        payload = {'user_id': user_id, 'role': role, 'exp': datetime.utcnow() + timedelta(minutes=expires_in_minutes)}
        return jwt.encode(payload, os.getenv("JWT_SECRET", "default-secret"), algorithm="HS256")
    
    def create_request_signature(self, method: str, path: str, body: str, timestamp: datetime, action: str) -> str:
        """
        PURPOSE: Creates HMAC signature for request integrity verification
        SECURITY ASPECT: Request Tampering Prevention & API Security
        USAGE: Client signs each API request with method+path+body+timestamp
        MIDDLEWARE VERIFICATION: Recreates signature to ensure request wasn't modified in transit
        """
        message = f"{method}|{path}|{body}|{timestamp.isoformat()}|{action}"
        return hmac.new(os.getenv("HMAC_REQUEST_KEY", "default").encode(), message.encode(), hashlib.sha256).hexdigest()
    
    def generate_rate_limit_token(self, client_ip: str, user_id: Optional[str] = None) -> Tuple[str, int]:
        """
        PURPOSE: Generates time-based tokens for rate limiting enforcement
        SECURITY ASPECT: DDoS Protection & Resource Abuse Prevention
        USAGE: Client includes token in headers, server tracks usage per token
        MIDDLEWARE VERIFICATION: Validates token freshness and checks against rate limits
        """
        window = int(time.time() // 60)  # 1-minute windows
        identifier = f"{client_ip}:{user_id or 'anon'}:{window}"
        token = hashlib.sha256(identifier.encode()).hexdigest()[:16]
        return token, window
    
    def create_client_fingerprint(self, user_agent: str, ip_address: str, additional_headers: Dict[str, str]) -> str:
        """
        PURPOSE: Creates unique client fingerprint for session binding
        SECURITY ASPECT: Session Hijacking Prevention & Device Tracking
        USAGE: Generated on first request, stored in secure cookie/header
        MIDDLEWARE VERIFICATION: Ensures requests come from same client environment
        """
        fingerprint_data = f"{user_agent}|{ip_address}|{'|'.join(f'{k}:{v}' for k, v in sorted(additional_headers.items()))}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:32]
    
    def generate_csrf_token(self, session_id: str, timestamp: int) -> str:
        """
        PURPOSE: Generates CSRF tokens for state-changing operations
        SECURITY ASPECT: Cross-Site Request Forgery Protection
        USAGE: Embedded in forms/AJAX requests for POST/PUT/DELETE operations
        MIDDLEWARE VERIFICATION: Validates token matches session and hasn't expired
        """
        message = f"{session_id}:{timestamp}:{secrets.token_hex(8)}"
        return hashlib.sha256(message.encode()).hexdigest()[:24]
    
    def create_api_key_signature(self, api_key: str, scope: str, expires_at: int) -> Tuple[str, str]:
        """
        PURPOSE: Generates API key signatures for service-to-service authentication
        SECURITY ASPECT: External Integration Security & Service Authentication
        USAGE: Third-party services use this for accessing marketplace APIs
        MIDDLEWARE VERIFICATION: Validates API key scope and signature integrity
        RETURNS: (public_identifier, signed_token) tuple
        """
        public_id = hashlib.sha256(f"{api_key}:{scope}".encode()).hexdigest()[:16]
        signed_token = hmac.new(api_key.encode(), f"{scope}:{expires_at}".encode(), hashlib.sha256).hexdigest()
        return public_id, signed_token

    def generate_audit_token(self, user_id: str, action: str, resource_id: str, ip_address: str) -> str:
        """
        PURPOSE: Creates immutable audit trail tokens for sensitive operations
        SECURITY ASPECT: Compliance & Security Monitoring
        USAGE: Generated for critical actions (deletions, purchases, admin operations)
        MIDDLEWARE VERIFICATION: Logs to audit system, validates action legitimacy
        """
        timestamp = int(time.time())
        audit_data = f"{user_id}:{action}:{resource_id}:{ip_address}:{timestamp}"
        return hmac.new(os.getenv("AUDIT_SECRET", "audit-key").encode(), audit_data.encode(), hashlib.sha256).hexdigest()

    def create_content_validation_hash(self, content: bytes, content_type: str, uploader_id: str) -> str:
        """
        PURPOSE: Generates secure hashes for uploaded AI workflows/automations
        SECURITY ASPECT: Content Integrity & Malware Prevention
        USAGE: Hash stored with uploaded files, verified on download/execution
        MIDDLEWARE VERIFICATION: Ensures content hasn't been tampered with or replaced
        """
        metadata = f"{content_type}:{uploader_id}:{len(content)}"
        combined = hashlib.sha256(content + metadata.encode()).hexdigest()
        return hmac.new(os.getenv("CONTENT_KEY", "content").encode(), combined.encode(), hashlib.sha256).hexdigest()[:32]

    def generate_webhook_signature(self, payload: str, webhook_id: str, timestamp: int) -> str:
        """
        PURPOSE: Creates signatures for outgoing webhook payloads to external services
        SECURITY ASPECT: External Integration Security & Payload Verification
        USAGE: Added to webhook headers for marketplace event notifications
        MIDDLEWARE VERIFICATION: Recipients can verify webhook authenticity
        """
        message = f"{webhook_id}:{timestamp}:{payload}"
        return hmac.new(os.getenv("WEBHOOK_SECRET", "webhook").encode(), message.encode(), hashlib.sha256).hexdigest()

    def create_session_refresh_token(self, user_id: str, session_id: str, device_fingerprint: str) -> Tuple[str, int]:
        """
        PURPOSE: Generates long-lived refresh tokens for seamless session renewal
        SECURITY ASPECT: Session Management & Token Rotation
        USAGE: Stored securely client-side, used to get new JWT tokens
        MIDDLEWARE VERIFICATION: Validates refresh token and issues new JWT
        """
        expires_at = int(time.time()) + (30 * 24 * 3600)  # 30 days
        token_data = f"{user_id}:{session_id}:{device_fingerprint}:{expires_at}"
        refresh_token = hmac.new(os.getenv("REFRESH_SECRET", "refresh").encode(), token_data.encode(), hashlib.sha256).hexdigest()
        return refresh_token, expires_at

    def generate_privilege_escalation_token(self, user_id: str, elevated_role: str, duration_minutes: int, requesting_admin: str) -> str:
        """
        PURPOSE: Creates time-limited tokens for temporary privilege elevation
        SECURITY ASPECT: Principle of Least Privilege & Admin Security
        USAGE: For temporary admin access, support escalation, emergency operations
        MIDDLEWARE VERIFICATION: Validates elevation request and enforces time limits
        """
        expires_at = int(time.time()) + (duration_minutes * 60)
        escalation_data = f"{user_id}:{elevated_role}:{expires_at}:{requesting_admin}:{secrets.token_hex(8)}"
        return hashlib.sha256(escalation_data.encode()).hexdigest()[:40]

    def create_device_binding_token(self, user_id: str, device_info: Dict[str, str], trust_level: str) -> str:
        """
        PURPOSE: Binds user sessions to specific trusted devices
        SECURITY ASPECT: Device Authentication & Account Takeover Prevention
        USAGE: Generated for "remember this device" functionality
        MIDDLEWARE VERIFICATION: Ensures requests come from pre-authorized devices
        """
        device_signature = '|'.join(f"{k}:{v}" for k, v in sorted(device_info.items()))
        binding_data = f"{user_id}:{trust_level}:{device_signature}:{int(time.time())}"
        return hmac.new(os.getenv("DEVICE_SECRET", "device").encode(), binding_data.encode(), hashlib.sha256).hexdigest()[:48]