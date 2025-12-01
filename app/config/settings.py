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
"""
Application configuration settings.

Manages environment variables and configuration for the transcription service.
"""

import os
from functools import lru_cache
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Audio Storage Configuration
    AUDIO_STORAGE_PATH: str = os.getenv("AUDIO_STORAGE_PATH", "/app/audio_storage")
    AUDIO_RETENTION_HOURS: int = int(os.getenv("AUDIO_RETENTION_HOURS", "24"))
    
    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://user:password@db:5432/transcription"
    )
    
    # OpenAI API Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "whisper-1")
    
    # Application Settings
    APP_NAME: str = "Speech-to-Text Transcription Service"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Worker Settings
    CLEANUP_INTERVAL_MINUTES: int = int(os.getenv("CLEANUP_INTERVAL_MINUTES", "60"))
    
    class Config:
        """Pydantic configuration."""
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings: Application settings
    """
    return Settings()
