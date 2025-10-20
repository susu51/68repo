"""
Application Settings - Environment-based Configuration
Replaces hardcoded values with environment variables
"""

import os
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings from environment"""
    
    # Database Configuration
    DATABASE_URL: str = Field(
        default="mongodb://localhost:27017/kuryecini",
        env="MONGO_URL",
        description="MongoDB connection string"
    )
    DB_CONNECT_TIMEOUT_MS: int = Field(
        default=3000,
        description="MongoDB connection timeout in milliseconds"
    )
    DB_SERVER_SELECTION_TIMEOUT_MS: int = Field(
        default=5000,
        description="MongoDB server selection timeout in milliseconds"
    )
    APP_NAME: str = Field(
        default="kuryecini",
        description="Application name for MongoDB connection"
    )
    
    # Redis/Cache Configuration
    REDIS_ENABLED: bool = Field(
        default=False,
        description="Enable Redis caching (optional)"
    )
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    CACHE_DEFAULT_TTL_S: int = Field(
        default=60,
        description="Default cache TTL in seconds"
    )
    
    # Performance Monitoring
    PERF_P95_TARGET_MS: int = Field(
        default=300,
        description="Target p95 latency in milliseconds"
    )
    ERROR_RATE_TARGET_PCT: float = Field(
        default=1.0,
        description="Target error rate percentage"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False


# Global settings instance
settings = Settings()
