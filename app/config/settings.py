"""
Application configuration settings.

Manages environment variables and configuration for the transcription service.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Audio Storage Configuration
    AUDIO_STORAGE_PATH: str = "/app/audio_storage"
    AUDIO_RETENTION_HOURS: int = 24

    # Database Configuration
    DATABASE_URL: str = "postgresql://user:password@db:5432/transcription"

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    # OpenAI API Configuration
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "whisper-1"

    # Admin Configuration
    ADMIN_API_KEY: str = ""

    # Application Settings
    APP_NAME: str = "Speech-to-Text Transcription Service"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Worker Settings
    CLEANUP_INTERVAL_MINUTES: int = 60

    # Health check timeout
    HEALTH_CHECK_TIMEOUT: int = 5

    # Lexicon Configuration
    DEFAULT_LEXICON: str = "general"
    LEXICON_CACHE_TTL: int = 3600  # 1 hour default

    # Numeral Handling Configuration
    DEFAULT_NUMERAL_STRATEGY: str = "english"

    class Config:
        """Pydantic configuration."""
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Application settings
    """
    return Settings()
