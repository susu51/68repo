import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from motor.motor_asyncio import AsyncIOMotorDatabase
from config import settings
import logging

logger = logging.getLogger(__name__)

class AuthService:
    """JWT-based authentication service with phone/SMS OTP"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users_collection = db.users
        self.refresh_tokens_collection = db.refresh_tokens
    
    async def create_indexes(self):
        """Create necessary database indexes"""
        # Users collection indexes
        await self.users_collection.create_index([("phone", 1)], unique=True)
        await self.users_collection.create_index([("email", 1)], sparse=True)
        await self.users_collection.create_index([("role", 1)])
        await self.users_collection.create_index([("created_at", 1)])
        
        # Refresh tokens collection indexes
        await self.refresh_tokens_collection.create_index([("token_id", 1)], unique=True)
        await self.refresh_tokens_collection.create_index([("user_id", 1)])
        await self.refresh_tokens_collection.create_index([("expires_at", 1)], expireAfterSeconds=0)
    
    def create_access_token(self, user_data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        # Token expires in 15 minutes
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_ttl_min)
        
        to_encode = {
            "sub": user_data["id"],  # Subject (user ID)
            "phone": user_data["phone"],
            "role": user_data["role"],
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        }
        
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, user_id: str) -> Dict[str, Any]:
        """Create refresh token data"""
        token_id = str(uuid.uuid4())
        expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_ttl_day)
        
        to_encode = {
            "sub": user_id,
            "jti": token_id,  # JWT ID for refresh token tracking
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        }
        
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        
        return {
            "token": encoded_jwt,
            "token_id": token_id,
            "expires_at": expire,
            "user_id": user_id
        }
    
    async def store_refresh_token(self, token_data: Dict[str, Any]) -> bool:
        """Store refresh token in database"""
        try:
            await self.refresh_tokens_collection.insert_one({
                "token_id": token_data["token_id"],
                "user_id": token_data["user_id"],
                "expires_at": token_data["expires_at"],
                "created_at": datetime.now(timezone.utc),
                "is_active": True
            })
            return True
        except Exception as e:
            logger.error(f"Failed to store refresh token: {e}")
            return False
    
    async def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode access token"""
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            
            # Check token type
            if payload.get("type") != "access":
                return None
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
                return None
            
            return payload
        except JWTError:
            return None
    
    async def verify_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify refresh token and check if it exists in database"""
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            
            # Check token type
            if payload.get("type") != "refresh":
                return None
            
            # Check if token exists and is active in database
            token_id = payload.get("jti")
            if not token_id:
                return None
            
            token_record = await self.refresh_tokens_collection.find_one({
                "token_id": token_id,
                "is_active": True,
                "expires_at": {"$gt": datetime.now(timezone.utc)}
            })
            
            if not token_record:
                return None
            
            return payload
        except JWTError:
            return None
    
    async def revoke_refresh_token(self, token_id: str) -> bool:
        """Revoke a refresh token"""
        try:
            result = await self.refresh_tokens_collection.update_one(
                {"token_id": token_id},
                {"$set": {"is_active": False, "revoked_at": datetime.now(timezone.utc)}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to revoke refresh token: {e}")
            return False
    
    async def revoke_all_user_tokens(self, user_id: str) -> bool:
        """Revoke all refresh tokens for a user"""
        try:
            result = await self.refresh_tokens_collection.update_many(
                {"user_id": user_id, "is_active": True},
                {"$set": {"is_active": False, "revoked_at": datetime.now(timezone.utc)}}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to revoke user tokens: {e}")
            return False
    
    async def find_user_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Find user by phone number"""
        try:
            user = await self.users_collection.find_one({"phone": phone})
            if user:
                user["id"] = str(user["_id"])
            return user
        except Exception as e:
            logger.error(f"Failed to find user by phone: {e}")
            return None
    
    async def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new user"""
        try:
            # Add metadata
            user_data["id"] = str(uuid.uuid4())
            user_data["created_at"] = datetime.now(timezone.utc)
            user_data["updated_at"] = datetime.now(timezone.utc)
            user_data["is_active"] = True
            
            # Insert user
            result = await self.users_collection.insert_one(user_data)
            
            # Return user data with database ID
            user_data["_id"] = result.inserted_id
            return user_data
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return None
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user data"""
        try:
            update_data["updated_at"] = datetime.now(timezone.utc)
            result = await self.users_collection.update_one(
                {"id": user_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update user: {e}")
            return False
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            user = await self.users_collection.find_one({"id": user_id})
            if user:
                user["id"] = str(user["_id"]) if "_id" in user else user["id"]
            return user
        except Exception as e:
            logger.error(f"Failed to get user by ID: {e}")
            return None
    
    async def authenticate_user(self, phone: str, otp_verified: bool = False) -> Optional[Dict[str, Any]]:
        """
        Authenticate user after OTP verification
        Returns user data and tokens
        """
        if not otp_verified:
            return None
        
        # Find or create user
        user = await self.find_user_by_phone(phone)
        
        if not user:
            # Create new user if doesn't exist (first time login)
            user_data = {
                "phone": phone,
                "role": "customer",  # Default role
                "email": None,
                "first_name": None,
                "last_name": None,
                "profile_completed": False,
                "kyc_status": "pending" if phone.startswith('+90') else "approved"  # Default KYC for Turkish numbers
            }
            user = await self.create_user(user_data)
            
            if not user:
                return None
        
        # Generate tokens
        access_token = self.create_access_token(user)
        refresh_data = self.create_refresh_token(user["id"])
        
        # Store refresh token
        await self.store_refresh_token(refresh_data)
        
        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_data["token"],
            "token_type": "bearer",
            "expires_in": settings.jwt_access_ttl_min * 60  # in seconds
        }
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Generate new access token using refresh token"""
        # Verify refresh token
        payload = await self.verify_refresh_token(refresh_token)
        if not payload:
            return None
        
        # Get user data
        user_id = payload.get("sub")
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Generate new access token
        access_token = self.create_access_token(user)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.jwt_access_ttl_min * 60
        }
    
    async def logout_user(self, refresh_token: str) -> bool:
        """Logout user by revoking refresh token"""
        try:
            payload = jwt.decode(refresh_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            token_id = payload.get("jti")
            
            if token_id:
                return await self.revoke_refresh_token(token_id)
            return False
        except JWTError:
            return False
    
    async def cleanup_expired_tokens(self):
        """Clean up expired refresh tokens (called periodically)"""
        current_time = datetime.now(timezone.utc)
        
        result = await self.refresh_tokens_collection.delete_many({
            "expires_at": {"$lt": current_time}
        })
        
        logger.info(f"Cleaned up {result.deleted_count} expired refresh tokens")