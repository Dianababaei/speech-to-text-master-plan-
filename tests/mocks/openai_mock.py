"""
Mock OpenAI API service for testing.

Provides realistic mock responses for transcription requests without
making actual API calls, supporting both success and error scenarios.
"""
from typing import Optional, Dict, Any
from unittest.mock import MagicMock
import time


class MockOpenAIResponse:
    """Mock response object from OpenAI API."""
    
    def __init__(self, text: str):
        self.text = text
    
    def get(self, key: str, default=None):
        """Mock dict-like get method."""
        if key == "text":
            return self.text
        return default


class MockOpenAIError(Exception):
    """Base exception for mock OpenAI errors."""
    pass


class MockRateLimitError(MockOpenAIError):
    """Mock rate limit error."""
    pass


class MockAPIError(MockOpenAIError):
    """Mock API error."""
    pass


class MockAuthenticationError(MockOpenAIError):
    """Mock authentication error."""
    pass


class MockTimeoutError(MockOpenAIError):
    """Mock timeout error."""
    pass


class MockInvalidAudioError(MockOpenAIError):
    """Mock invalid audio format error."""
    pass


# Sample transcription responses
SAMPLE_RESPONSES = {
    "english": "Patient presents with chest pain and shortness of breath. Vital signs are stable. Recommend EKG and chest X-ray.",
    "english_radiology": "CT scan of the abdomen shows no acute abnormalities. Liver, spleen, and kidneys appear normal. No evidence of masses or lesions.",
    "english_cardiology": "Echocardiogram reveals normal left ventricular function with ejection fraction of 60%. No valvular abnormalities detected.",
    "persian": "بیمار با درد قفسه سینه و تنگی نفس مراجعه کرده است. علائم حیاتی پایدار است. توصیه به انجام نوار قلب و رادیوگرافی قفسه سینه.",
    "persian_radiology": "سی تی اسکن شکم هیچ ناهنجاری حادی را نشان نمی دهد. کبد، طحال و کلیه ها طبیعی به نظر می رسند.",
    "mixed": "The patient's MRI results show normal findings. بیمار نیاز به پیگیری ندارد. Follow-up in 6 months.",
    "short": "Normal examination.",
    "long": " ".join(["The patient underwent a comprehensive examination."] * 50),
}


def create_mock_openai_service(
    response_type: str = "english",
    should_fail: bool = False,
    error_type: str = "rate_limit",
    delay: float = 0.0
) -> MagicMock:
    """
    Create a mock OpenAI service for testing.
    
    Args:
        response_type: Type of response to return (english, persian, etc.)
        should_fail: Whether the mock should raise an error
        error_type: Type of error to raise (rate_limit, api_error, timeout, auth_error, invalid_audio)
        delay: Simulated API delay in seconds
    
    Returns:
        MagicMock configured to simulate OpenAI API behavior
    """
    mock_service = MagicMock()
    
    if should_fail:
        # Configure error responses
        error_map = {
            "rate_limit": MockRateLimitError("Rate limit exceeded. Please try again later."),
            "api_error": MockAPIError("API error occurred. Please contact support."),
            "timeout": MockTimeoutError("Request timed out after 30 seconds."),
            "auth_error": MockAuthenticationError("Invalid API key provided."),
            "invalid_audio": MockInvalidAudioError("Invalid audio format. Supported formats: wav, mp3, m4a."),
        }
        mock_service.transcribe_audio.side_effect = error_map.get(
            error_type,
            MockAPIError("Unknown error occurred.")
        )
    else:
        # Configure success response
        def mock_transcribe(*args, **kwargs):
            if delay > 0:
                time.sleep(delay)
            return SAMPLE_RESPONSES.get(response_type, SAMPLE_RESPONSES["english"])
        
        mock_service.transcribe_audio.side_effect = mock_transcribe
    
    return mock_service


def create_mock_openai_audio_api() -> MagicMock:
    """
    Create a mock for openai.Audio API.
    
    Returns:
        MagicMock configured to simulate openai.Audio.transcribe
    """
    mock_audio = MagicMock()
    
    def mock_transcribe(*args, **kwargs):
        """Mock transcribe method that returns realistic responses."""
        # Extract file parameter to determine response
        file_obj = kwargs.get("file")
        language = kwargs.get("language", "en")
        
        # Choose response based on language
        if language == "fa" or language == "persian":
            response_text = SAMPLE_RESPONSES["persian"]
        elif language == "en":
            response_text = SAMPLE_RESPONSES["english"]
        else:
            response_text = SAMPLE_RESPONSES["english"]
        
        return MockOpenAIResponse(response_text)
    
    mock_audio.transcribe.side_effect = mock_transcribe
    return mock_audio


def create_mock_openai_client() -> MagicMock:
    """
    Create a full mock OpenAI client.
    
    Returns:
        MagicMock configured to simulate openai module
    """
    mock_client = MagicMock()
    mock_client.Audio = create_mock_openai_audio_api()
    
    # Add error classes
    mock_client.error.RateLimitError = MockRateLimitError
    mock_client.error.APIError = MockAPIError
    mock_client.error.AuthenticationError = MockAuthenticationError
    mock_client.error.Timeout = MockTimeoutError
    
    return mock_client


# Preset mock configurations for common test scenarios
def get_success_mock(response_type: str = "english") -> MagicMock:
    """Get a mock that returns successful transcription."""
    return create_mock_openai_service(response_type=response_type)


def get_rate_limit_mock() -> MagicMock:
    """Get a mock that raises rate limit error."""
    return create_mock_openai_service(should_fail=True, error_type="rate_limit")


def get_api_error_mock() -> MagicMock:
    """Get a mock that raises API error."""
    return create_mock_openai_service(should_fail=True, error_type="api_error")


def get_timeout_mock() -> MagicMock:
    """Get a mock that raises timeout error."""
    return create_mock_openai_service(should_fail=True, error_type="timeout")


def get_auth_error_mock() -> MagicMock:
    """Get a mock that raises authentication error."""
    return create_mock_openai_service(should_fail=True, error_type="auth_error")


def get_invalid_audio_mock() -> MagicMock:
    """Get a mock that raises invalid audio error."""
    return create_mock_openai_service(should_fail=True, error_type="invalid_audio")


def get_slow_mock(delay: float = 2.0) -> MagicMock:
    """Get a mock with simulated network delay."""
    return create_mock_openai_service(delay=delay)
