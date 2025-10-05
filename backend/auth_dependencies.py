"""
Shared Authentication Dependencies for FastAPI Routes
Provides reusable JWT authentication and role-based dependencies
"""
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os
from models import UserRole

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return user data - shared across all route modules"""
    try:
        token = credentials.credentials
        secret_key = os.environ.get("JWT_SECRET", "kuryecini_secret_key_2024")
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        # Import here to avoid circular imports
        from server import db
        user_email = payload.get("sub")
        user = await db.users.find_one({"email": user_email})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
            
        return {
            "id": user["_id"],
            "email": user["email"],
            "role": user.get("role", "customer")
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