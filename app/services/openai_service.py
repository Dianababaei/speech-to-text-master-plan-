"""
OpenAI Whisper API integration service.

NOTE: This module is assumed to be implemented from task #34 (previous task).
The implementation here provides the interface that the worker expects.
"""
from typing import Optional
from pathlib import Path
from io import BufferedReader
from openai import OpenAI, APIError, RateLimitError, AuthenticationError
from app.config.settings import get_settings
from app.utils.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

def get_openai_client():
    """Get OpenAI client instance."""
    return OpenAI(api_key=settings.OPENAI_API_KEY)


class OpenAIServiceError(Exception):
    """Base exception for OpenAI service errors."""
    pass


class OpenAIAPIError(OpenAIServiceError):
    """Raised when OpenAI API returns an error."""
    pass


class OpenAIQuotaError(OpenAIServiceError):
    """Raised when OpenAI API quota is exceeded (can retry later)."""
    pass


def transcribe_audio(
    audio_file_path: str,
    language: Optional[str] = None,
    prompt: Optional[str] = None
) -> str:
    """
    Transcribe audio file using OpenAI Whisper API.
    
    Args:
        audio_file_path: Path to audio file to transcribe
        language: Optional language code (e.g., 'en', 'es')
        prompt: Optional prompt to guide transcription
    
    Returns:
        Transcribed text
    
    Raises:
        OpenAIAPIError: If API call fails
        OpenAIQuotaError: If quota exceeded
        FileNotFoundError: If audio file doesn't exist
    """
    # Validate file exists
    file_path = Path(audio_file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
    
    try:
        logger.info(f"Starting OpenAI transcription for file: {audio_file_path}")

        # Get OpenAI client
        client = get_openai_client()

        # Open and transcribe audio file - use Path directly
        # The OpenAI SDK handles Path objects correctly
        kwargs = {
            "model": getattr(settings, 'OPENAI_MODEL', 'whisper-1'),
            "file": open(audio_file_path, "rb"),
        }

        if language:
            kwargs["language"] = language
        if prompt:
            kwargs["prompt"] = prompt

        # Call OpenAI Whisper API (new v1.0+ API)
        try:
            response = client.audio.transcriptions.create(**kwargs)
        finally:
            # Close the file handle
            kwargs["file"].close()

        # Extract transcription text
        transcription = response.text

        logger.info(
            f"OpenAI transcription completed successfully. "
            f"Length: {len(transcription)} characters"
        )

        return transcription

    except RateLimitError as e:
        logger.error(f"OpenAI rate limit exceeded: {str(e)}")
        raise OpenAIQuotaError(f"OpenAI quota exceeded: {str(e)}")

    except APIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise OpenAIAPIError(f"OpenAI API error: {str(e)}")

    except AuthenticationError as e:
        logger.error(f"OpenAI authentication error: {str(e)}")
        raise OpenAIAPIError(f"OpenAI authentication failed: {str(e)}")

    except Exception as e:
        logger.error(f"Unexpected error during transcription: {str(e)}")
        raise OpenAIAPIError(f"Transcription failed: {str(e)}")
