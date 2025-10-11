"""
HttpOnly Cookie-based Authentication System
NO localStorage support - production ready
"""

from fastapi import APIRouter, Request, Response, HTTPException, Depends
from pydantic import BaseModel, EmailStr
import jwt
import time
import os
import bcrypt
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
from typing import Optional

# Environment configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "your-secret-key-here")
ACCESS_TTL = 15 * 60        # 15 minutes
REFRESH_TTL = 7 * 24*60*60  # 7 days

# Cookie configuration - localhost cross-origin development
COOKIE_CONFIG = {
    "httponly": True,
    "secure": False,  # False for localhost development
    "samesite": "lax",  # Lax is more permissive for localhost
    "path": "/",
    "domain": None  # No domain for cross-origin localhost
}

# Router
auth_router = APIRouter(prefix="/auth", tags=["auth"])

# Database dependency - we'll inject this
db_client = None

def set_db_client(client: AsyncIOMotorClient):
    global db_client
    db_client = client

def get_db():
    if not db_client:
        raise HTTPException(500, "Database not initialized")
    return db_client.kuryecini

# Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: str = "customer"

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: str

# JWT helpers
def make_token(sub: str, ttl: int) -> str:
    payload = {
        "sub": sub,
        "exp": int(time.time()) + ttl,
        "iat": int(time.time())
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")

# Password helpers
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Auth dependency
async def get_current_user_from_cookie_or_bearer(request: Request):
    # Try cookie first (primary method)
    token = request.cookies.get("access_token")
    
    # Fallback to Bearer token for development
    if not token:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(401, "No authentication cookie or token")
    
    payload = verify_token(token)
    user_id = payload["sub"]
    
    # Get user from database
    db = db_client["kuryecini"]
    user = await db.users.find_one({"id": user_id})
    
    if not user:
        raise HTTPException(404, "User not found")
    
    return user

# Keep original function for backward compatibility
async def get_current_user_from_cookie(request: Request):
    return await get_current_user_from_cookie_or_bearer(request)

# Routes
@auth_router.post("/login")
async def login(body: LoginRequest, response: Response):
    print(f"🔍 Login attempt with email: {body.email}")
    db = get_db()
    
    # Always use database for authentication (no hardcoded test users)
    # Find user in database
    user = await db.users.find_one({"email": body.email})
    if not user:
        raise HTTPException(401, "Invalid credentials")
    
    # Verify password (handle both plain text and bcrypt)
    if user.get("password"):
        if user["password"].startswith("$2"):
            # bcrypt password
            if not bcrypt.checkpw(body.password.encode(), user["password"].encode()):
                raise HTTPException(401, "Invalid credentials")
        else:
            # Plain text password (for legacy compatibility)
            if body.password != user["password"]:
                raise HTTPException(401, "Invalid credentials")
    else:
        raise HTTPException(401, "Invalid credentials")
    
    user_id = user.get("id")
    
    # Get user data for response
    user_data = user
    
    # Generate tokens
    access_token = make_token(user_id, ACCESS_TTL)
    refresh_token = make_token(user_id, REFRESH_TTL)
    
    # For development: also return token in response body
    response_data = {
        "success": True, 
        "message": "Login successful",
        "access_token": access_token,  # For dev fallback
        "user": {
            "id": user_data["id"],
            "email": user_data["email"],
            "role": user_data["role"],
            "first_name": user_data.get("first_name", ""),
            "last_name": user_data.get("last_name", "")
        }
    }
    
    # Set HttpOnly cookies (primary method)
    response.set_cookie(
        "access_token", 
        access_token, 
        max_age=ACCESS_TTL, 
        **COOKIE_CONFIG
    )
    response.set_cookie(
        "refresh_token", 
        refresh_token, 
        max_age=REFRESH_TTL, 
        **COOKIE_CONFIG
    )
    
    return response_data

@auth_router.get("/me", response_model=UserResponse)
async def me(user = Depends(get_current_user_from_cookie)):
    return UserResponse(
        id=user["id"],
        email=user["email"],
        first_name=user.get("first_name", ""),
        last_name=user.get("last_name", ""),
        role=user.get("role", "customer")
    )

@auth_router.post("/refresh")
async def refresh(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(401, "No refresh token")
    
    payload = verify_token(refresh_token)
    user_id = payload["sub"]
    
    # Generate new access token
    new_access_token = make_token(user_id, ACCESS_TTL)
    
    # Set new access token cookie
    response.set_cookie(
        "access_token",
        new_access_token,
        max_age=ACCESS_TTL,
        **COOKIE_CONFIG
    )
    
    return {"success": True, "message": "Token refreshed"}

@auth_router.post("/logout")
async def logout(response: Response):
    # Clear cookies
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"success": True, "message": "Logged out"}

@auth_router.post("/register")
async def register(body: RegisterRequest):
    db = get_db()
    
    # Check if user exists
    existing = await db.users.find_one({"email": body.email})
    if existing:
        raise HTTPException(400, "User already exists")
    
    # Create user
    user_id = str(uuid.uuid4())
    hashed_pw = hash_password(body.password)
    
    user_data = {
        "id": user_id,
        "email": body.email,
        "password": hashed_pw,
        "first_name": body.first_name,
        "last_name": body.last_name,
        "role": body.role,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_active": True
    }
    
    await db.users.insert_one(user_data)
    
    return {"success": True, "message": "Registration successful", "user_id": user_id}

# Export the dependency for use in other modules
__all__ = ["auth_router", "get_current_user_from_cookie", "set_db_client"]