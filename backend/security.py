"""
Production Security Configuration
Handles rate limiting, CORS, HTTPS enforcement, and security headers
"""

import os
import time
from typing import Dict, Any
from fastapi import HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

# Rate Limiting Store (In production, use Redis)
rate_limit_store: Dict[str, Dict[str, Any]] = {}

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware to prevent abuse"""
    
    def __init__(self, app, calls_per_minute: int = 100, calls_per_hour: int = 1000):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.calls_per_hour = calls_per_hour
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()
        
        # Initialize client data if not exists
        if client_ip not in rate_limit_store:
            rate_limit_store[client_ip] = {
                'minute_calls': [],
                'hour_calls': []
            }
        
        client_data = rate_limit_store[client_ip]
        
        # Clean old entries
        client_data['minute_calls'] = [
            call_time for call_time in client_data['minute_calls']
            if current_time - call_time < 60
        ]
        client_data['hour_calls'] = [
            call_time for call_time in client_data['hour_calls']
            if current_time - call_time < 3600
        ]
        
        # Check rate limits
        if len(client_data['minute_calls']) >= self.calls_per_minute:
            logger.warning(f"Rate limit exceeded for IP {client_ip}: {len(client_data['minute_calls'])} calls per minute")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": 60
                }
            )
        
        if len(client_data['hour_calls']) >= self.calls_per_hour:
            logger.warning(f"Hourly rate limit exceeded for IP {client_ip}: {len(client_data['hour_calls'])} calls per hour")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests this hour. Please try again later.",
                    "retry_after": 3600
                }
            )
        
        # Record this call
        client_data['minute_calls'].append(current_time)
        client_data['hour_calls'].append(current_time)
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.calls_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(self.calls_per_minute - len(client_data['minute_calls']))
        response.headers["X-RateLimit-Reset"] = str(int(current_time + 60))
        
        return response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=*, camera=(), microphone=()"
        
        # HSTS (only in production with HTTPS)
        if os.environ.get('ENVIRONMENT') == 'production':
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        return response

def setup_security_middleware(app):
    """Setup all security middleware for the FastAPI app"""
    environment = os.environ.get('ENVIRONMENT', 'development')
    
    # HTTPS redirect in production
    if environment == 'production':
        app.add_middleware(HTTPSRedirectMiddleware)
    
    # Trusted hosts
    allowed_hosts = os.environ.get('CORS_ALLOWED_ORIGINS', 'localhost').split(',')
    trusted_hosts = ['localhost', '127.0.0.1', '0.0.0.0']
    
    for host in allowed_hosts:
        # Extract domain from URL
        if '://' in host:
            domain = host.split('://')[1]
            trusted_hosts.append(domain)
        else:
            trusted_hosts.append(host)
    
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)
    
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Rate limiting
    rate_limit_per_minute = int(os.environ.get('RATE_LIMIT_PER_MINUTE', '100'))
    rate_limit_per_hour = int(os.environ.get('RATE_LIMIT_PER_HOUR', '1000'))
    app.add_middleware(RateLimitMiddleware, 
                      calls_per_minute=rate_limit_per_minute,
                      calls_per_hour=rate_limit_per_hour)
    
    # CORS with restricted origins in production
    allowed_origins = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
    
    if environment == 'production':
        # Restrictive CORS for production
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["*"],
            max_age=3600,  # Cache preflight requests for 1 hour
        )
    else:
        # Permissive CORS for development
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    logger.info(f"Security middleware configured for {environment} environment")
    logger.info(f"Allowed origins: {allowed_origins}")
    logger.info(f"Rate limits: {rate_limit_per_minute}/min, {rate_limit_per_hour}/hour")

# Brute force protection for login endpoints
login_attempts: Dict[str, Dict[str, Any]] = {}

def check_brute_force_protection(ip_address: str, max_attempts: int = 5, window_minutes: int = 15) -> bool:
    """
    Check if IP address has exceeded login attempts
    Returns True if allowed, False if blocked
    """
    current_time = time.time()
    
    if ip_address not in login_attempts:
        login_attempts[ip_address] = {
            'attempts': [],
            'blocked_until': None
        }
    
    client_data = login_attempts[ip_address]
    
    # Check if currently blocked
    if client_data['blocked_until'] and current_time < client_data['blocked_until']:
        return False
    
    # Clean old attempts
    window_seconds = window_minutes * 60
    client_data['attempts'] = [
        attempt_time for attempt_time in client_data['attempts']
        if current_time - attempt_time < window_seconds
    ]
    
    # Check if attempts exceeded
    if len(client_data['attempts']) >= max_attempts:
        # Block for double the window time
        client_data['blocked_until'] = current_time + (window_seconds * 2)
        logger.warning(f"IP {ip_address} blocked due to {len(client_data['attempts'])} failed login attempts")
        return False
    
    return True

def record_failed_login_attempt(ip_address: str):
    """Record a failed login attempt for an IP address"""
    current_time = time.time()
    
    if ip_address not in login_attempts:
        login_attempts[ip_address] = {
            'attempts': [],
            'blocked_until': None
        }
    
    login_attempts[ip_address]['attempts'].append(current_time)

def clear_login_attempts(ip_address: str):
    """Clear login attempts for an IP address after successful login"""
    if ip_address in login_attempts:
        login_attempts[ip_address]['attempts'] = []
        login_attempts[ip_address]['blocked_until'] = None