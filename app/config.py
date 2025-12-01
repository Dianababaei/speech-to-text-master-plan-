"""
Configuration management using pydantic-settings.
Environment variables are loaded from .env file or system environment.
"""

from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be overridden via environment variables or .env file.
    Required fields will cause validation errors if not provided.
    """
    
    # Database Configuration
    DATABASE_URL: str = Field(
        ...,
        description="PostgreSQL connection string (e.g., postgresql://user:pass@localhost:5432/dbname)"
    )
    
    # Redis Configuration
    REDIS_URL: str = Field(
        ...,
        description="Redis connection string (e.g., redis://localhost:6379/0)"
    )
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = Field(
        ...,
        description="OpenAI API key for transcription services"
    )
    
    # File Processing Configuration
    MAX_FILE_SIZE: int = Field(
        default=104857600,  # 100 MB in bytes
        description="Maximum file size in bytes for audio uploads"
    )
    
    # Worker Configuration
    MAX_WORKERS: int = Field(
        default=4,
        description="Maximum number of concurrent workers for processing"
    )
    
    # Environment Configuration
    ENVIRONMENT: Literal["dev", "prod"] = Field(
        default="dev",
        description="Application environment (dev or prod)"
    )
    
    # CORS Configuration
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        description="Comma-separated list of allowed CORS origins"
    )
    
    # Application Configuration
    APP_TITLE: str = Field(
        default="Speech-to-Text API",
        description="Application title for OpenAPI docs"
    )
    
    APP_DESCRIPTION: str = Field(
        default="Multi-language speech transcription API using OpenAI models",
        description="Application description for OpenAPI docs"
    )
    
    APP_VERSION: str = Field(
        default="0.1.0",
        description="Application version"
    )
    
    # Logging Configuration
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    @field_validator("MAX_FILE_SIZE")
    @classmethod
    def validate_max_file_size(cls, v: int) -> int:
        """Ensure MAX_FILE_SIZE is positive and reasonable."""
        if v <= 0:
            raise ValueError("MAX_FILE_SIZE must be positive")
        if v > 1073741824:  # 1 GB
            raise ValueError("MAX_FILE_SIZE cannot exceed 1 GB")
        return v
    
    @field_validator("MAX_WORKERS")
    @classmethod
    def validate_max_workers(cls, v: int) -> int:
        """Ensure MAX_WORKERS is positive and reasonable."""
        if v <= 0:
            raise ValueError("MAX_WORKERS must be positive")
        if v > 100:
            raise ValueError("MAX_WORKERS cannot exceed 100")
        return v
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure LOG_LEVEL is valid."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v_upper
    
    def get_cors_origins(self) -> list[str]:
        """Parse CORS_ORIGINS string into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
