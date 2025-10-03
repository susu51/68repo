"""
Token service for password reset functionality
"""
import os
import uuid
import hmac
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional

class TokenService:
    """Password reset token management"""
    
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET", "change_me_long")
        self.token_expiry_minutes = 30
    
    def generate_reset_token(self) -> str:
        """Generate a secure password reset token"""
        # Generate UUID4 token
        token_uuid = str(uuid.uuid4())
        
        # Create HMAC for additional security
        hmac_signature = hmac.new(
            self.secret_key.encode(),
            token_uuid.encode(),
            hashlib.sha256
        ).hexdigest()[:16]
        
        # Combine UUID with HMAC prefix
        return f"{hmac_signature}-{token_uuid}"
    
    def get_token_expiry(self) -> datetime:
        """Get expiry time for new tokens"""
        return datetime.now(timezone.utc) + timedelta(minutes=self.token_expiry_minutes)
    
    def verify_token_format(self, token: str) -> bool:
        """Verify token has correct format"""
        try:
            if not token or len(token) < 20:
                return False
            
            parts = token.split('-', 1)
            if len(parts) != 2:
                return False
            
            hmac_part, uuid_part = parts
            
            # Verify HMAC
            expected_hmac = hmac.new(
                self.secret_key.encode(),
                uuid_part.encode(),
                hashlib.sha256
            ).hexdigest()[:16]
            
            return hmac.compare_digest(hmac_part, expected_hmac)
        except:
            return False

# Global token service instance
token_service = TokenService()