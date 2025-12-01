"""
Configuration module for the application.

This module manages application settings and configuration, including database
connection parameters. Settings can be overridden using environment variables.

Environment Variables:
    DATABASE_URL: PostgreSQL connection string
                  Format: postgresql://user:password@host:port/dbname
                  Default: postgresql://postgres:postgres@localhost:5432/transcription_db
    
    DB_POOL_SIZE: Number of persistent connections in the pool (default: 5)
    DB_MAX_OVERFLOW: Max additional connections beyond pool_size (default: 10)
    DB_POOL_RECYCLE: Seconds before recycling connections (default: 3600)
    DB_ECHO: Enable SQL query logging for debugging (default: False)
    
    ENVIRONMENT: Application environment (dev/test/production) (default: dev)
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application settings
    environment: str = Field(default="dev", alias="ENVIRONMENT")
    
    # Database connection settings
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/transcription_db",
        alias="DATABASE_URL"
    )
    
    # Database connection pool settings
    db_pool_size: int = Field(default=5, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=10, alias="DB_MAX_OVERFLOW")
    db_pool_recycle: int = Field(default=3600, alias="DB_POOL_RECYCLE")
    db_echo: bool = Field(default=False, alias="DB_ECHO")
    
    # Connection testing
    db_pool_pre_ping: bool = Field(default=True, alias="DB_POOL_PRE_PING")
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() in ["dev", "development"]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() in ["prod", "production"]
    
    @property
    def is_testing(self) -> bool:
        """Check if running in test mode."""
        return self.environment.lower() in ["test", "testing"]


# Create a singleton settings instance
settings = Settings()
