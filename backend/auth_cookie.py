"""
HttpOnly Cookie-based Authentication System
NO localStorage support - production ready
"""

from fastapi import APIRouter, Request, Response, HTTPException, Depends, Form, File, UploadFile
from pydantic import BaseModel, EmailStr
import jwt
import time
import os
import bcrypt
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
from typing import Optional
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Environment configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "Kuryecini!SecretKey2025_ChangeMe")
ACCESS_TTL = 15 * 60        # 15 minutes
REFRESH_TTL = 7 * 24*60*60  # 7 days

# Cookie configuration - production settings from environment
COOKIE_DOMAIN = os.environ.get("COOKIE_DOMAIN")
COOKIE_CONFIG = {
    "httponly": True,
    "secure": True,  # True for production HTTPS
    "samesite": "lax",
    "path": "/",
    "domain": COOKIE_DOMAIN if COOKIE_DOMAIN else None
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
    # Extract database name from MONGO_URL or use environment variable
    db_name = os.getenv("DB_NAME")
    if not db_name:
        # Extract from MONGO_URL
        mongo_url = os.getenv("MONGO_URL", "")
        if "/" in mongo_url:
            db_name = mongo_url.split("/")[-1].split("?")[0]
        else:
            db_name = "kuryecini"  # fallback
    return db_client[db_name]

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
    email = payload["sub"]  # Changed: sub contains email, not user_id
    
    # Get user from database - import from server.py
    from server import db
    user = await db.users.find_one({"email": email})  # Changed: lookup by email
    
    if not user:
        raise HTTPException(404, "User not found")
    
    # Debug: Check user ID fields
    print(f"🔍 User document _id: {user.get('_id')}")
    print(f"🔍 User document id: {user.get('id')}")
    print(f"🔍 User email: {user.get('email')}")
    
    # Ensure consistent user ID format - use 'id' field if available, otherwise use '_id'
    if "id" in user and user["id"]:
        # User has custom 'id' field, use it
        pass
    elif "_id" in user:
        # User only has '_id', convert to string and set as 'id'
        user["id"] = str(user["_id"])
    
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
        raise HTTPException(401, "E-posta veya şifre hatalı")
    
    # Verify password (handle both field names and hash types)
    # Check for password_hash (from new registration) or password (legacy)
    stored_password = user.get("password_hash") or user.get("password")
    
    if stored_password:
        if stored_password.startswith("$2"):
            # bcrypt password
            if not bcrypt.checkpw(body.password.encode(), stored_password.encode()):
                raise HTTPException(401, "E-posta veya şifre hatalı")
        else:
            # Plain text password (for legacy compatibility)
            if body.password != stored_password:
                raise HTTPException(401, "E-posta veya şifre hatalı")
    else:
        raise HTTPException(401, "E-posta veya şifre hatalı")
    
    user_id = user.get("id")
    
    # Get user data for response
    user_data = user
    
    # Generate tokens
    access_token = make_token(user.get("email"), ACCESS_TTL)
    refresh_token = make_token(user.get("email"), REFRESH_TTL)
    
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

@auth_router.get("/me")
async def get_current_user(request: Request):
    """Get current authenticated user from cookie"""
    access_token = request.cookies.get("access_token")
    print(f"🔍 /auth/me called, token present: {bool(access_token)}")
    
    if not access_token:
        raise HTTPException(401, "Not authenticated")
    
    try:
        payload = verify_token(access_token)
        email = payload["sub"]
        print(f"🔍 Token verified, email: {email}")
        
        # Get user from database - import from server.py
        from server import db
        user = await db.users.find_one({"email": email})
        print(f"🔍 User lookup result: {user is not None}")
        
        if not user:
            print(f"❌ User not found for email: {email}")
            raise HTTPException(401, "User not found")
        
        print(f"✅ User found: {user.get('email')}, role: {user.get('role')}")
        return {
            "id": user.get("id") or user.get("_id"),
            "email": user.get("email"),
            "role": user.get("role", "customer"),
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "name": user.get("name", "")
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Exception in /auth/me: {type(e).__name__}: {str(e)}")
        raise HTTPException(401, f"Invalid token: {str(e)}")

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
async def register(
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    first_name: str = Form(""),
    last_name: str = Form(""),
    role: str = Form("customer"),
    phone: str = Form(""),
    city: str = Form(""),
    district: str = Form(""),
    vehicle_type: str = Form(""),
    business_name: str = Form(""),
    business_tax_id: str = Form(""),
    license_photo: UploadFile = File(None),
    id_photo: UploadFile = File(None),
    vehicle_photo: UploadFile = File(None),
    business_photo: UploadFile = File(None)
):
    """
    Register new user with role-specific data and file uploads
    """
    import os
    import shutil
    from pathlib import Path
    
    # Import db from server.py
    from server import db
    
    # Check if user exists
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(400, "User already exists")
    
    # Create user
    user_id = str(uuid.uuid4())
    hashed_pw = hash_password(password)
    
    # Create uploads directory if not exists
    uploads_dir = Path("/app/backend/uploads")
    uploads_dir.mkdir(exist_ok=True)
    
    user_uploads_dir = uploads_dir / user_id
    user_uploads_dir.mkdir(exist_ok=True)
    
    user_data = {
        "_id": user_id,
        "id": user_id,
        "email": email,
        "password": hashed_pw,
        "first_name": first_name,
        "last_name": last_name,
        "name": f"{first_name} {last_name}".strip(),
        "role": role,
        "phone": phone,
        "city": city,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "is_active": True,
        "is_verified": False,
        "kyc_status": "pending" if role in ["business", "courier"] else "approved",
        "kyc_documents": []
    }
    
    # Role-specific data and file saving
    if role == "courier":
        user_data["district"] = district
        user_data["vehicle_type"] = vehicle_type
        
        # Save uploaded files
        if license_photo and license_photo.filename:
            license_path = user_uploads_dir / f"license_{license_photo.filename}"
            with license_path.open("wb") as buffer:
                shutil.copyfileobj(license_photo.file, buffer)
            user_data["kyc_documents"].append({
                "type": "license",
                "filename": license_photo.filename,
                "path": f"/uploads/{user_id}/license_{license_photo.filename}"
            })
        
        if id_photo and id_photo.filename:
            id_path = user_uploads_dir / f"id_{id_photo.filename}"
            with id_path.open("wb") as buffer:
                shutil.copyfileobj(id_photo.file, buffer)
            user_data["kyc_documents"].append({
                "type": "id_card",
                "filename": id_photo.filename,
                "path": f"/uploads/{user_id}/id_{id_photo.filename}"
            })
        
        if vehicle_photo and vehicle_photo.filename:
            vehicle_path = user_uploads_dir / f"vehicle_{vehicle_photo.filename}"
            with vehicle_path.open("wb") as buffer:
                shutil.copyfileobj(vehicle_photo.file, buffer)
            user_data["kyc_documents"].append({
                "type": "vehicle_registration",
                "filename": vehicle_photo.filename,
                "path": f"/uploads/{user_id}/vehicle_{vehicle_photo.filename}"
            })
    
    if role == "business":
        user_data["business_name"] = business_name
        user_data["business_tax_id"] = business_tax_id
        
        if business_photo and business_photo.filename:
            business_path = user_uploads_dir / f"business_{business_photo.filename}"
            with business_path.open("wb") as buffer:
                shutil.copyfileobj(business_photo.file, buffer)
            user_data["kyc_documents"].append({
                "type": "business_photo",
                "filename": business_photo.filename,
                "path": f"/uploads/{user_id}/business_{business_photo.filename}"
            })
    
    await db.users.insert_one(user_data)
    
    # Auto-login after registration - generate tokens
    access_token = make_token(email, ACCESS_TTL)
    refresh_token = make_token(email, REFRESH_TTL)
    
    # Set cookies
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
    
    return {
        "success": True, 
        "message": f"{role.title()} registration successful", 
        "user_id": user_id,
        "access_token": access_token,
        "user": {
            "id": user_id,
            "email": email,
            "role": role,
            "first_name": first_name,
            "last_name": last_name,
            "kyc_status": user_data.get("kyc_status")
        }
    }

# Additional dependency for business users with KYC approval
async def get_approved_business_user_from_cookie(request: Request):
    """Get approved business user from cookie - requires KYC approval"""
    current_user = await get_current_user_from_cookie_or_bearer(request)
    
    if current_user.get("role") != "business":
        raise HTTPException(
            status_code=403,
            detail="Business access required"
        )
    
    kyc_status = current_user.get("kyc_status", "pending")
    if kyc_status != "approved":
        raise HTTPException(
            status_code=403,
            detail=f"KYC approval required. Current status: {kyc_status}"
        )
    
    return current_user

# Export the dependency for use in other modules
__all__ = ["auth_router", "get_current_user_from_cookie", "get_current_user_from_cookie_or_bearer", "get_approved_business_user_from_cookie", "set_db_client"]