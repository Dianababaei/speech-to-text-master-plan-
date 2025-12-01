"""
Custom exception classes for OpenAI Whisper API integration.

Provides specific exception types for different error scenarios to enable
targeted error handling and recovery strategies.
"""


class TranscriptionError(Exception):
    """Base exception for all transcription-related errors."""
    pass


class APIKeyError(TranscriptionError):
    """Raised when API key is missing or invalid (401)."""
    
    def __init__(self, message: str = "OpenAI API key is missing or invalid"):
        super().__init__(message)


class AudioFormatError(TranscriptionError):
    """Raised when audio format is invalid or unsupported (400)."""
    
    def __init__(self, message: str = "Invalid or unsupported audio format"):
        super().__init__(message)


class RateLimitError(TranscriptionError):
    """Raised when API rate limit is exceeded (429)."""
    
    def __init__(self, message: str = "API rate limit exceeded", retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after  # Seconds to wait before retrying


class APITimeoutError(TranscriptionError):
    """Raised when API request times out."""
    
    def __init__(self, message: str = "API request timed out"):
        super().__init__(message)


class NetworkError(TranscriptionError):
    """Raised for network-related errors (connection, DNS, etc.)."""
    
    def __init__(self, message: str = "Network error occurred"):
        super().__init__(message)


class ServerError(TranscriptionError):
    """Raised for server-side errors (5xx status codes)."""
    
    def __init__(self, message: str = "Server error occurred", status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


class FileNotFoundError(TranscriptionError):
    """Raised when the audio file cannot be found or accessed."""
    
    def __init__(self, file_path: str):
        super().__init__(f"Audio file not found or inaccessible: {file_path}")
        self.file_path = file_path


class MaxRetriesExceededError(TranscriptionError):
    """Raised when maximum retry attempts have been exhausted."""
    
    def __init__(self, attempts: int, last_error: Exception):
        super().__init__(
            f"Maximum retry attempts ({attempts}) exceeded. "
            f"Last error: {type(last_error).__name__}: {str(last_error)}"
        )
        self.attempts = attempts
        self.last_error = last_error
