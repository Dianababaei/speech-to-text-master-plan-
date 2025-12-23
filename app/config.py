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

# Post-processing pipeline configuration
# Each step can be enabled/disabled via environment variables
# Pipeline processes text through: Lexicon → Cleanup → Numeral handling → GPT cleanup
ENABLE_LEXICON_REPLACEMENT = os.getenv("ENABLE_LEXICON_REPLACEMENT", "true").lower() in ("true", "1", "yes")
ENABLE_TEXT_CLEANUP = os.getenv("ENABLE_TEXT_CLEANUP", "true").lower() in ("true", "1", "yes")
ENABLE_NUMERAL_HANDLING = os.getenv("ENABLE_NUMERAL_HANDLING", "true").lower() in ("true", "1", "yes")
# Enable GPT-4o-mini post-processing for advanced transcription cleanup and formatting
ENABLE_GPT_CLEANUP = os.getenv("ENABLE_GPT_CLEANUP", "true").lower() in ("true", "1", "yes")

# Fuzzy matching configuration
ENABLE_FUZZY_MATCHING = os.getenv("ENABLE_FUZZY_MATCHING", "true").lower() in ("true", "1", "yes")
FUZZY_MATCH_THRESHOLD = int(os.getenv("FUZZY_MATCH_THRESHOLD", "85"))

# Settings object for backward compatibility
class _Settings:
    """Simple settings object for access to configuration values."""
    
    @property
    def default_lexicon(self):
        return DEFAULT_LEXICON
    
    @property
    def lexicon_cache_ttl(self):
        return LEXICON_CACHE_TTL
    
    @property
    def enable_lexicon_replacement(self):
        return ENABLE_LEXICON_REPLACEMENT
    
    @property
    def enable_text_cleanup(self):
        return ENABLE_TEXT_CLEANUP
    
    @property
    def enable_numeral_handling(self):
        return ENABLE_NUMERAL_HANDLING
    
    @property
    def enable_fuzzy_matching(self):
        return ENABLE_FUZZY_MATCHING
    
    @property
    def fuzzy_match_threshold(self):
        return FUZZY_MATCH_THRESHOLD
    
    @property
    def enable_gpt_cleanup(self):
        return ENABLE_GPT_CLEANUP

settings = _Settings()
