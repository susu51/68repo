"""
Shared Authentication Dependencies for FastAPI Routes
Provides reusable JWT authentication and role-based dependencies
Now supports BOTH cookie and bearer token authentication
"""
from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os
from models import UserRole
from typing import Optional

security = HTTPBearer(auto_error=False)  # Make it optional

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Verify JWT token from cookie OR bearer token - shared across all route modules"""
    try:
        # Try cookie first (primary method)
        token = request.cookies.get("access_token")
        print(f"🔍 AUTH: Cookie token present: {token is not None}")
        
        # Fallback to bearer token if no cookie
        if not token and credentials:
            token = credentials.credentials
            print(f"🔍 AUTH: Using bearer token")
        
        if not token:
            print("❌ AUTH: No token found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated - no token provided"
            )
        
        secret_key = os.environ.get("JWT_SECRET", "kuryecini_secret_key_2024")
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        email = payload.get("sub")
        
        # Get user from database (no test users)
        from server import db
        user = await db.users.find_one({"email": email})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
            
        return {
            "id": user.get("id", str(user.get("_id", ""))),
            "email": user["email"],
            "role": user.get("role", "customer"),
            "kyc_status": user.get("kyc_status", "pending"),
            "business_name": user.get("business_name", ""),
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "is_active": user.get("is_active", True)
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

async def get_business_user(current_user: dict = Depends(get_current_user)):
    """Require business role"""
    if current_user.get("role") != UserRole.BUSINESS.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business access required"
        )
    return current_user

async def get_approved_business_user(current_user: dict = Depends(get_current_user)):
    """Get current user and verify business role + KYC approval (Legacy - Bearer token only)"""
    if current_user.get("role") != UserRole.BUSINESS.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Business access required"
        )
    
    # Check KYC status
    kyc_status = current_user.get("kyc_status", "pending")
    if kyc_status != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"KYC approval required. Current status: {kyc_status}. Please wait for admin approval."
        )
    
    return current_user

async def get_approved_business_user_cookie():
    """Get current user from cookie and verify business role + KYC approval"""
    # Import here to avoid circular dependency
    from auth_cookie import get_current_user_from_cookie_or_bearer
    from fastapi import Request, Depends
    
    async def _inner(request: Request, current_user: dict = Depends(get_current_user_from_cookie_or_bearer)):
        if current_user.get("role") != UserRole.BUSINESS.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Business access required"
            )
        
        # Check KYC status
        kyc_status = current_user.get("kyc_status", "pending")
        if kyc_status != "approved":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"KYC approval required. Current status: {kyc_status}. Please wait for admin approval."
            )
        
        return current_user
    
    return _inner

async def get_customer_user(current_user: dict = Depends(get_current_user)):
    """Require customer role"""
    if current_user.get("role") != UserRole.CUSTOMER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer access required"
        )
    return current_user

async def get_courier_user(current_user: dict = Depends(get_current_user)):
    """Require courier role"""
    if current_user.get("role") != UserRole.COURIER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Courier access required"
        )
    return current_user

async def get_admin_user(current_user: dict = Depends(get_current_user)):
    """Require admin role"""
    if current_user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user