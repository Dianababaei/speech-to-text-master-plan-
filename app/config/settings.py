import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Database configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/dbname"
    )
    
    # Redis configuration
    REDIS_URL: str = os.getenv(
        "REDIS_URL",
        "redis://localhost:6379/0"
    )
    
    # Health check timeout
    HEALTH_CHECK_TIMEOUT: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
