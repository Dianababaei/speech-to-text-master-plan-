"""
OpenAI Whisper API integration service.

Provides audio transcription functionality with comprehensive error handling,
retry logic, and multilingual support.
"""
import logging
import os
import time
from pathlib import Path
from typing import Optional

import openai
from openai import OpenAI, OpenAIError

from app.config import config
from app.exceptions import (
    APIKeyError,
    APITimeoutError,
    AudioFormatError,
    FileNotFoundError,
    MaxRetriesExceededError,
    NetworkError,
    RateLimitError,
    ServerError,
    TranscriptionError,
)

# Configure logging
logger = logging.getLogger(__name__)


class OpenAITranscriptionService:
    """Service for transcribing audio files using OpenAI's Whisper API."""
    
    def __init__(self):
        """Initialize the OpenAI transcription service."""
        self.client: Optional[OpenAI] = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """
        Initialize OpenAI client with API key.
        
        Raises:
            APIKeyError: If API key is not configured.
        """
        try:
            config.validate()
            self.client = OpenAI(
                api_key=config.api_key,
                timeout=config.timeout,
            )
            logger.info(
                "OpenAI client initialized successfully "
                f"(model={config.model}, timeout={config.timeout}s)"
            )
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            raise APIKeyError(str(e))
    
    def _validate_audio_file(self, file_path: str) -> Path:
        """
        Validate that the audio file exists and is accessible.
        
        Args:
            file_path: Path to the audio file.
            
        Returns:
            Path object for the validated file.
            
        Raises:
            FileNotFoundError: If file doesn't exist or isn't accessible.
            AudioFormatError: If file extension is not supported.
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.error(f"Audio file not found: {file_path}")
            raise FileNotFoundError(file_path)
        
        if not path.is_file():
            logger.error(f"Path is not a file: {file_path}")
            raise FileNotFoundError(file_path)
        
        # Validate file extension
        supported_formats = {".wav", ".mp3", ".m4a", ".mp4", ".mpeg", ".mpga", ".webm", ".ogg", ".flac"}
        if path.suffix.lower() not in supported_formats:
            logger.error(f"Unsupported audio format: {path.suffix}")
            raise AudioFormatError(
                f"Unsupported audio format: {path.suffix}. "
                f"Supported formats: {', '.join(sorted(supported_formats))}"
            )
        
        return path
    
    def _call_transcription_api(
        self,
        audio_file_path: Path,
        language: Optional[str] = None
    ) -> str:
        """
        Make a single API call to transcribe audio.
        
        Args:
            audio_file_path: Path to the audio file.
            language: Optional ISO-639-1 language code (e.g., 'en', 'es', 'zh').
            
        Returns:
            Transcribed text as plain string.
            
        Raises:
            Various TranscriptionError subclasses based on error type.
        """
        try:
            file_size = audio_file_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            logger.info(
                f"Starting transcription: file={audio_file_path.name}, "
                f"size={file_size_mb:.2f}MB, model={config.model}"
            )
            
            start_time = time.time()
            
            # Open and send file to OpenAI API
            with open(audio_file_path, "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    model=config.model,
                    file=audio_file,
                    response_format="text",  # Plain text only
                    language=language,  # Optional, Whisper will auto-detect if None
                )
            
            duration = time.time() - start_time
            
            # Response is already plain text when response_format="text"
            transcription = response if isinstance(response, str) else str(response)
            
            logger.info(
                f"Transcription completed: file={audio_file_path.name}, "
                f"duration={duration:.2f}s, "
                f"text_length={len(transcription)} chars"
            )
            
            return transcription
            
        except openai.AuthenticationError as e:
            logger.error(f"Authentication error: {e}")
            raise APIKeyError(f"Invalid API key: {e}")
        
        except openai.BadRequestError as e:
            logger.error(f"Bad request error: {e}")
            # Check if it's an audio format issue
            if "audio" in str(e).lower() or "format" in str(e).lower():
                raise AudioFormatError(f"Invalid audio format: {e}")
            raise AudioFormatError(f"Bad request: {e}")
        
        except openai.RateLimitError as e:
            # Extract retry-after header if available
            retry_after = getattr(e, "retry_after", None)
            logger.warning(f"Rate limit exceeded: {e}, retry_after={retry_after}")
            raise RateLimitError(str(e), retry_after=retry_after)
        
        except openai.APITimeoutError as e:
            logger.error(f"API timeout: {e}")
            raise APITimeoutError(f"Request timed out after {config.timeout}s: {e}")
        
        except openai.APIConnectionError as e:
            logger.error(f"Network/connection error: {e}")
            raise NetworkError(f"Failed to connect to OpenAI API: {e}")
        
        except openai.InternalServerError as e:
            logger.error(f"OpenAI server error (500): {e}")
            raise ServerError(f"OpenAI server error: {e}", status_code=500)
        
        except OpenAIError as e:
            # Catch-all for other OpenAI errors
            logger.error(f"OpenAI API error: {e}")
            raise TranscriptionError(f"OpenAI API error: {e}")
        
        except OSError as e:
            logger.error(f"File I/O error: {e}")
            raise FileNotFoundError(str(audio_file_path))
        
        except Exception as e:
            logger.error(f"Unexpected error during transcription: {e}", exc_info=True)
            raise TranscriptionError(f"Unexpected error: {e}")
    
    def _should_retry(self, error: Exception) -> bool:
        """
        Determine if an error is transient and should be retried.
        
        Args:
            error: The exception that occurred.
            
        Returns:
            True if the error is transient and retry is appropriate.
        """
        # Retry transient errors: network errors and 5xx server errors
        return isinstance(error, (NetworkError, ServerError, APITimeoutError))
    
    def _calculate_retry_delay(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay for retry attempt.
        
        Args:
            attempt: The retry attempt number (0-indexed).
            
        Returns:
            Delay in seconds.
        """
        delay = config.initial_retry_delay * (config.retry_multiplier ** attempt)
        return min(delay, config.max_retry_delay)
    
    def transcribe_audio(
        self,
        file_path: str,
        language: Optional[str] = None
    ) -> str:
        """
        Transcribe audio file to text using OpenAI Whisper API.
        
        This function handles:
        - Multiple audio formats (WAV, MP3, M4A, etc.)
        - Automatic language detection (or explicit language specification)
        - Code-switching (preserves original language/script per word)
        - Retry logic with exponential backoff for transient failures
        - Comprehensive error handling with descriptive messages
        
        Args:
            file_path: Path to the audio file to transcribe.
            language: Optional ISO-639-1 language code (e.g., 'en', 'es', 'zh').
                     If None, Whisper will automatically detect the language.
        
        Returns:
            Plain text transcription preserving original language/script.
        
        Raises:
            FileNotFoundError: Audio file doesn't exist or isn't accessible.
            AudioFormatError: Audio format is invalid or unsupported.
            APIKeyError: API key is missing or invalid.
            RateLimitError: API rate limit exceeded (429).
            APITimeoutError: Request timed out.
            MaxRetriesExceededError: All retry attempts failed.
            TranscriptionError: Other transcription errors.
        
        Example:
            >>> service = OpenAITranscriptionService()
            >>> text = service.transcribe_audio("/path/to/audio.mp3")
            >>> print(text)
            'This is the transcribed text...'
        """
        # Validate file before attempting transcription
        audio_file_path = self._validate_audio_file(file_path)
        
        last_error = None
        
        # Main retry loop
        for attempt in range(config.max_retries + 1):
            try:
                return self._call_transcription_api(audio_file_path, language)
            
            except RateLimitError as e:
                # Don't retry rate limits, return immediately with guidance
                logger.error(f"Rate limit error (attempt {attempt + 1}): {e}")
                if e.retry_after:
                    raise RateLimitError(
                        f"API rate limit exceeded. Retry after {e.retry_after} seconds.",
                        retry_after=e.retry_after
                    )
                raise
            
            except (APIKeyError, AudioFormatError, FileNotFoundError) as e:
                # Don't retry non-transient errors
                logger.error(f"Non-retryable error: {e}")
                raise
            
            except TranscriptionError as e:
                last_error = e
                
                # Check if we should retry
                if not self._should_retry(e):
                    logger.error(f"Non-retryable transcription error: {e}")
                    raise
                
                # Check if we have retries left
                if attempt >= config.max_retries:
                    logger.error(
                        f"Max retries ({config.max_retries}) exceeded. "
                        f"Last error: {e}"
                    )
                    raise MaxRetriesExceededError(attempt + 1, e)
                
                # Calculate backoff delay
                delay = self._calculate_retry_delay(attempt)
                logger.warning(
                    f"Transient error on attempt {attempt + 1}/{config.max_retries + 1}: "
                    f"{type(e).__name__}: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                time.sleep(delay)
        
        # Should never reach here, but just in case
        raise MaxRetriesExceededError(config.max_retries + 1, last_error)


# Global service instance
_service_instance: Optional[OpenAITranscriptionService] = None


def get_service() -> OpenAITranscriptionService:
    """
    Get or create the global OpenAI transcription service instance.
    
    Returns:
        OpenAITranscriptionService instance.
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = OpenAITranscriptionService()
    return _service_instance


def transcribe_audio(file_path: str, language: Optional[str] = None) -> str:
    """
    Convenience function to transcribe audio using the global service instance.
    
    Args:
        file_path: Path to the audio file to transcribe.
        language: Optional ISO-639-1 language code.
    
    Returns:
        Plain text transcription.
    
    Raises:
        Various TranscriptionError subclasses based on error type.
    """
    service = get_service()
    return service.transcribe_audio(file_path, language)
