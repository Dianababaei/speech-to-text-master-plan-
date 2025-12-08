"""
Application configuration settings.
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./transcription.db")

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_URL = os.getenv("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")

# Queue configuration
QUEUE_NAME = os.getenv("QUEUE_NAME", "transcription")

# File storage
TEMP_AUDIO_DIR = Path(os.getenv("TEMP_AUDIO_DIR", "./temp_audio"))
TEMP_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "whisper-1")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "json"  # or "text"

# Lexicon configuration
DEFAULT_LEXICON = os.getenv("DEFAULT_LEXICON", "general")
LEXICON_CACHE_TTL = int(os.getenv("LEXICON_CACHE_TTL", "3600"))  # 1 hour default

# Settings object for backward compatibility
class _Settings:
    """Simple settings object for access to configuration values."""
    
    @property
    def default_lexicon(self):
        return DEFAULT_LEXICON
    
    @property
    def lexicon_cache_ttl(self):
        return LEXICON_CACHE_TTL

settings = _Settings()
