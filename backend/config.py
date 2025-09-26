from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # MongoDB
    mongo_url: str = os.getenv("MONGO_URL", "mongodb://localhost:27017/delivertr")
    db_name: str = os.getenv("DB_NAME", "delivertr_database")
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")
    
    # JWT Configuration
    jwt_secret_key: str = "your-super-secret-jwt-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_min: int = 15
    jwt_refresh_ttl_day: int = 7
    
    # SMS Configuration
    netgsm_user: Optional[str] = None
    netgsm_pass: Optional[str] = None
    netgsm_header: str = "DELIVERTR"
    
    # OTP Configuration
    otp_ttl_sec: int = 120  # 2 minutes
    otp_max_attempts: int = 5
    otp_length: int = 6
    
    # Rate Limiting
    rate_limit_per_ip_per_min: int = 30
    rate_limit_per_phone_per_min: int = 2
    rate_limit_lockout_min: int = 10
    
    # Feature Flags
    auth_phone_sms: bool = True
    auth_email_login: bool = False
    sms_mock_mode: bool = True  # True for development, False for production
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    
    # Security
    bcrypt_rounds: int = 12
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()