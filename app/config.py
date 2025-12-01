"""
Configuration module for OpenAI API settings.

Loads configuration from environment variables with sensible defaults.
"""
import os
from typing import Optional


class OpenAIConfig:
    """Configuration for OpenAI API integration."""
    
    def __init__(self):
        """Initialize OpenAI configuration from environment variables."""
        self.api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.model: str = os.getenv("OPENAI_MODEL", "whisper-1")
        self.timeout: int = int(os.getenv("OPENAI_TIMEOUT", "60"))
        self.max_retries: int = int(os.getenv("OPENAI_MAX_RETRIES", "3"))
        self.initial_retry_delay: float = float(os.getenv("OPENAI_INITIAL_RETRY_DELAY", "1.0"))
        self.max_retry_delay: float = float(os.getenv("OPENAI_MAX_RETRY_DELAY", "60.0"))
        self.retry_multiplier: float = float(os.getenv("OPENAI_RETRY_MULTIPLIER", "2.0"))
    
    def validate(self) -> None:
        """
        Validate configuration at startup.
        
        Raises:
            ValueError: If required configuration is missing or invalid.
        """
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set. "
                "Please configure your OpenAI API key."
            )
        
        if self.model not in ["whisper-1", "gpt-4o-transcribe"]:
            raise ValueError(
                f"Invalid model '{self.model}'. "
                "Must be 'whisper-1' or 'gpt-4o-transcribe'."
            )
        
        if self.timeout <= 0:
            raise ValueError(f"Timeout must be positive, got {self.timeout}")
        
        if self.max_retries < 0:
            raise ValueError(f"Max retries must be non-negative, got {self.max_retries}")


# Global configuration instance
config = OpenAIConfig()
