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
        
        user_email = payload.get("sub")
        
        # Handle test users (same as in main server.py)
        test_users = {
            "testcustomer@example.com": {
                "id": "customer-001",
                "email": "testcustomer@example.com", 
                "first_name": "Test",
                "last_name": "Customer",
                "role": "customer",
                "is_active": True
            },
            "testkurye@example.com": {
                "id": "courier-001",
                "email": "testkurye@example.com",
                "first_name": "Test", 
                "last_name": "Courier",
                "role": "courier",
                "is_active": True,
                "kyc_status": "approved"
            },
            "testbusiness@example.com": {
                "id": "business-001",
                "email": "testbusiness@example.com",
                "first_name": "Test",
                "last_name": "Business",
                "role": "business", 
                "business_name": "Test Restaurant",
                "kyc_status": "approved",
                "is_active": True
            }
        }
        
        # Check if it's a test user
        if user_email in test_users:
            return test_users[user_email]
        
        # Import here to avoid circular imports
        from server import db
        user = await db.users.find_one({"email": user_email})
        
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
    """Get current user and verify business role + KYC approval"""
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