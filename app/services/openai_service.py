"""
OpenAI Whisper API integration service.

NOTE: This module is assumed to be implemented from task #34 (previous task).
The implementation here provides the interface that the worker expects.
"""
from typing import Optional
from pathlib import Path
import openai
from app.config import OPENAI_API_KEY, OPENAI_MODEL
from app.utils.logging import get_logger

logger = get_logger(__name__)


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
        
        # Configure OpenAI
        openai.api_key = OPENAI_API_KEY
        
        # Open and transcribe audio file
        with open(audio_file_path, "rb") as audio_file:
            # Prepare API call parameters
            kwargs = {
                "model": OPENAI_MODEL,
                "file": audio_file,
            }
            
            if language:
                kwargs["language"] = language
            if prompt:
                kwargs["prompt"] = prompt
            
            # Call OpenAI Whisper API
            response = openai.Audio.transcribe(**kwargs)
        
        # Extract transcription text
        transcription = response.get("text", "")
        
        logger.info(
            f"OpenAI transcription completed successfully. "
            f"Length: {len(transcription)} characters"
        )
        
        return transcription
    
    except openai.error.RateLimitError as e:
        logger.error(f"OpenAI rate limit exceeded: {str(e)}")
        raise OpenAIQuotaError(f"OpenAI quota exceeded: {str(e)}")
    
    except openai.error.APIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise OpenAIAPIError(f"OpenAI API error: {str(e)}")
    
    except openai.error.AuthenticationError as e:
        logger.error(f"OpenAI authentication error: {str(e)}")
        raise OpenAIAPIError(f"OpenAI authentication failed: {str(e)}")
    
    except Exception as e:
        logger.error(f"Unexpected error during transcription: {str(e)}")
        raise OpenAIAPIError(f"Transcription failed: {str(e)}")
