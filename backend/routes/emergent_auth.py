"""
Emergent Auth Integration for Kuryecini
Provides Google OAuth authentication via Emergent Auth service
"""
from fastapi import APIRouter, HTTPException, Request, Response, status, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, timezone, timedelta
import os
import uuid
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth/emergent", tags=["Emergent Auth"])

# Will be set from server.py
db_client = None

def set_db_client(client):
    global db_client
    db_client = client


class UserSession(BaseModel):
    """User session model matching Emergent Auth response"""
    user_id: str = Field(alias="id")
    email: EmailStr
    name: str
    picture: Optional[str] = None
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        populate_by_name = True


class SessionDataResponse(BaseModel):
    """Response from Emergent Auth session-data endpoint"""
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    session_token: str


@router.get("/session-data")
async def get_session_data(request: Request):
    """
    Process session_id from Emergent Auth and return user data
    Called by frontend after OAuth redirect
    """
    session_id = request.headers.get("X-Session-ID")
    
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Session-ID header"
        )
    
    try:
        # Call Emergent Auth to get user data
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id}
            )
            response.raise_for_status()
            session_data = response.json()
        
        logger.info(f"Received session data for email: {session_data['email']}")
        
        # Check if user exists in database
        db = db_client["kuryecini"]
        users_collection = db["users"]
        
        user = await users_collection.find_one({"email": session_data["email"]})
        
        if not user:
            # Create new user
            user_id = str(uuid.uuid4())
            new_user = {
                "id": user_id,
                "email": session_data["email"],
                "name": session_data["name"],
                "picture": session_data.get("picture"),
                "role": "customer",  # Default role for Google auth users
                "created_at": datetime.now(timezone.utc)
            }
            await users_collection.insert_one(new_user)
            logger.info(f"Created new user: {user_id}")
        else:
            user_id = user["id"]
            logger.info(f"Existing user logged in: {user_id}")
        
        # Store session in database
        sessions_collection = db["user_sessions"]
        session_token = session_data["session_token"]
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        session_doc = {
            "user_id": user_id,
            "session_token": session_token,
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc)
        }
        
        await sessions_collection.insert_one(session_doc)
        logger.info(f"Stored session for user: {user_id}")
        
        # Return user data with session token
        return {
            "id": user_id,
            "email": session_data["email"],
            "name": session_data["name"],
            "picture": session_data.get("picture"),
            "session_token": session_token
        }
        
    except httpx.HTTPStatusError as e:
        logger.error(f"Emergent Auth API error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session ID"
        )
    except Exception as e:
        logger.error(f"Session data error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process session"
        )


@router.get("/me")
async def get_current_user(request: Request):
    """
    Get current authenticated user from session token
    Checks both cookie and Authorization header
    """
    # Try cookie first
    session_token = request.cookies.get("session_token")
    
    # Fallback to Authorization header for development
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
    
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        db = db_client["kuryecini"]
        sessions_collection = db["user_sessions"]
        
        # Find valid session
        session = await sessions_collection.find_one({
            "session_token": session_token,
            "expires_at": {"$gt": datetime.now(timezone.utc)}
        })
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )
        
        # Get user data
        users_collection = db["users"]
        user = await users_collection.find_one({"id": session["user_id"]})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "picture": user.get("picture"),
            "role": user.get("role", "customer")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user data"
        )


@router.post("/logout")
async def logout(request: Request, response: Response):
    """
    Logout user by deleting session
    """
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
    
    if session_token:
        try:
            db = db_client["kuryecini"]
            sessions_collection = db["user_sessions"]
            await sessions_collection.delete_one({"session_token": session_token})
            logger.info("Session deleted successfully")
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
    
    # Clear cookie
    response.delete_cookie(
        key="session_token",
        path="/",
        domain=None
    )
    
    return {"message": "Logged out successfully"}
