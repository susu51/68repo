"""
Secure Cookie-based Authentication System
JWT tokens as httpOnly cookies with CSRF protection
"""

import os
import jwt
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, Response, Depends, Cookie
from fastapi.security import HTTPBearer
from pydantic import BaseModel
import hashlib
import logging

logger = logging.getLogger(__name__)

# Security configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'dev-secret-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', '24'))
CSRF_SECRET = os.environ.get('CSRF_SECRET', 'csrf-secret-change-in-production')

class AuthTokens(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    csrf_token: str

class UserSession(BaseModel):
    user_id: str
    email: str
    role: str
    phone: Optional[str] = None
    name: Optional[str] = None
    csrf_token: str
    exp: int
    iat: int

def generate_csrf_token() -> str:
    """Generate cryptographically secure CSRF token"""
    return secrets.token_urlsafe(32)

def create_csrf_signature(token: str, user_id: str) -> str:
    """Create CSRF token signature for validation"""
    message = f"{token}:{user_id}:{CSRF_SECRET}"
    return hashlib.sha256(message.encode()).hexdigest()

def validate_csrf_token(token: str, user_id: str, signature: str) -> bool:
    """Validate CSRF token against signature"""
    expected_signature = create_csrf_signature(token, user_id)
    return secrets.compare_digest(expected_signature, signature)

def create_auth_tokens(user_data: Dict[str, Any]) -> AuthTokens:
    """Create JWT access token and CSRF token"""
    now = datetime.now(timezone.utc)
    exp = now + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    # Generate CSRF token
    csrf_token = generate_csrf_token()
    
    # JWT payload
    payload = {
        'user_id': str(user_data['id']),
        'email': user_data['email'],
        'role': user_data['role'],
        'phone': user_data.get('phone'),
        'name': user_data.get('name'),
        'csrf_token': csrf_token,
        'exp': int(exp.timestamp()),
        'iat': int(now.timestamp()),
        'iss': 'kuryecini-auth'
    }
    
    # Create JWT token
    access_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return AuthTokens(
        access_token=access_token,
        csrf_token=csrf_token
    )

def verify_jwt_token(token: str) -> Optional[UserSession]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Validate expiration
        exp = payload.get('exp')
        if not exp or datetime.now(timezone.utc).timestamp() > exp:
            logger.warning("JWT token expired")
            return None
        
        # Validate issuer
        if payload.get('iss') != 'kuryecini-auth':
            logger.warning("Invalid JWT issuer")
            return None
        
        return UserSession(**payload)
        
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None
    except Exception as e:
        logger.error(f"JWT verification error: {e}")
        return None

def set_auth_cookies(response: Response, tokens: AuthTokens, domain: Optional[str] = None):
    """Set secure httpOnly authentication cookies"""
    is_production = os.environ.get('ENVIRONMENT') == 'production'
    
    # Set JWT token cookie (httpOnly, secure)
    response.set_cookie(
        key="kuryecini_token",
        value=tokens.access_token,
        max_age=JWT_EXPIRATION_HOURS * 3600,  # Convert hours to seconds
        httponly=True,  # Prevent XSS
        secure=is_production,  # HTTPS only in production
        samesite="lax",  # CSRF protection
        domain=domain,
        path="/"
    )
    
    # Set CSRF token cookie (readable by JS for header)
    response.set_cookie(
        key="kuryecini_csrf",
        value=tokens.csrf_token,
        max_age=JWT_EXPIRATION_HOURS * 3600,
        httponly=False,  # JS needs to read this
        secure=is_production,
        samesite="lax",
        domain=domain,
        path="/"
    )
    
    logger.info("Authentication cookies set successfully")

def clear_auth_cookies(response: Response, domain: Optional[str] = None):
    """Clear authentication cookies on logout"""
    response.set_cookie(
        key="kuryecini_token",
        value="",
        max_age=0,
        httponly=True,
        secure=os.environ.get('ENVIRONMENT') == 'production',
        samesite="lax",
        domain=domain,
        path="/"
    )
    
    response.set_cookie(
        key="kuryecini_csrf",
        value="",
        max_age=0,
        httponly=False,
        secure=os.environ.get('ENVIRONMENT') == 'production',
        samesite="lax",
        domain=domain,
        path="/"
    )
    
    logger.info("Authentication cookies cleared")

# Dependency for getting current user from cookies
def get_current_user(
    request: Request,
    kuryecini_token: Optional[str] = Cookie(None),
    kuryecini_csrf: Optional[str] = Cookie(None)
) -> UserSession:
    """Get current user from httpOnly cookie"""
    
    if not kuryecini_token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Cookie"}
        )
    
    # Verify JWT token
    user_session = verify_jwt_token(kuryecini_token)
    if not user_session:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication",
            headers={"WWW-Authenticate": "Cookie"}
        )
    
    return user_session

# Dependency for CSRF protection on state-changing operations
def verify_csrf_token(
    request: Request,
    current_user: UserSession = Depends(get_current_user)
) -> UserSession:
    """Verify CSRF token for state-changing operations"""
    
    # Get CSRF token from header
    csrf_header = request.headers.get('X-CSRF-Token')
    if not csrf_header:
        raise HTTPException(
            status_code=403,
            detail="CSRF token required in X-CSRF-Token header"
        )
    
    # Validate CSRF token matches the one in JWT
    if not secrets.compare_digest(csrf_header, current_user.csrf_token):
        raise HTTPException(
            status_code=403,
            detail="Invalid CSRF token"
        )
    
    logger.debug(f"CSRF token validated for user {current_user.user_id}")
    return current_user

# Optional dependency for routes that don't require authentication
def get_current_user_optional(
    kuryecini_token: Optional[str] = Cookie(None)
) -> Optional[UserSession]:
    """Get current user if authenticated, None otherwise"""
    if not kuryecini_token:
        return None
    
    return verify_jwt_token(kuryecini_token)

# Rate limiting helper for login attempts
login_attempts = {}

def check_login_rate_limit(identifier: str, max_attempts: int = 5) -> bool:
    """Check if login attempts exceed rate limit"""
    now = datetime.now(timezone.utc).timestamp()
    
    if identifier not in login_attempts:
        login_attempts[identifier] = []
    
    # Clean old attempts (older than 15 minutes)
    login_attempts[identifier] = [
        attempt_time for attempt_time in login_attempts[identifier]
        if now - attempt_time < 900  # 15 minutes
    ]
    
    if len(login_attempts[identifier]) >= max_attempts:
        return False
    
    return True

def record_login_attempt(identifier: str):
    """Record a login attempt"""
    now = datetime.now(timezone.utc).timestamp()
    
    if identifier not in login_attempts:
        login_attempts[identifier] = []
    
    login_attempts[identifier].append(now)

def clear_login_attempts(identifier: str):
    """Clear login attempts after successful login"""
    if identifier in login_attempts:
        del login_attempts[identifier]

# Middleware for security headers
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response as StarletteResponse

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses"""
    
    async def dispatch(self, request: StarletteRequest, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY" 
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # HSTS in production
        if os.environ.get('ENVIRONMENT') == 'production':
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # Content Security Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # React needs unsafe-inline/eval
            "style-src 'self' 'unsafe-inline'",  # Tailwind needs unsafe-inline
            "img-src 'self' data: https: blob:",
            "connect-src 'self' https://tile.openstreetmap.org",
            "font-src 'self'",
            "object-src 'none'",
            "media-src 'self'",
            "frame-src 'none'"
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        return response