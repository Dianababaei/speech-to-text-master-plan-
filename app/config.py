from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings and configuration."""
    
    # Database settings
    database_url: str = "sqlite:///./transcription.db"
    
    # Audio storage settings
    audio_storage_path: Path = Path("/app/audio_storage")
    max_file_size_mb: int = 10
    
    # Supported audio formats
    allowed_audio_formats: list[str] = ["wav", "mp3", "m4a"]
    allowed_mime_types: list[str] = [
        "audio/wav",
        "audio/x-wav",
        "audio/mpeg",
        "audio/mp3",
        "audio/mp4",
        "audio/x-m4a",
    ]
    
    # Default lexicon
    default_lexicon: str = "radiology"
    
    # API settings
    api_title: str = "Speech-to-Text Transcription API"
    api_version: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
