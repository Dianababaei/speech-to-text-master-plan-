"""
Unit tests for OpenAI transcription service.

Tests all aspects of the transcription service including:
- Successful transcription
- Error handling for various API errors
- Retry logic with exponential backoff
- File validation
- Configuration validation
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import openai

from app.config import OpenAIConfig, config
from app.exceptions import (
    APIKeyError,
    APITimeoutError,
    AudioFormatError,
    FileNotFoundError,
    MaxRetriesExceededError,
    NetworkError,
    RateLimitError,
    ServerError,
)
from app.services.openai_service import OpenAITranscriptionService, transcribe_audio


@pytest.fixture
def mock_config():
    """Fixture to create a test configuration."""
    test_config = OpenAIConfig()
    test_config.api_key = "test-api-key"
    test_config.model = "whisper-1"
    test_config.timeout = 60
    test_config.max_retries = 3
    test_config.initial_retry_delay = 0.1  # Fast retries for tests
    test_config.max_retry_delay = 1.0
    test_config.retry_multiplier = 2.0
    return test_config


@pytest.fixture
def temp_audio_file():
    """Fixture to create a temporary audio file."""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(b"fake audio content")
        temp_path = f.name
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def mock_openai_client():
    """Fixture to create a mocked OpenAI client."""
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create = MagicMock()
    return mock_client


class TestOpenAIConfig:
    """Tests for OpenAI configuration."""
    
    def test_config_defaults(self):
        """Test default configuration values."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            cfg = OpenAIConfig()
            assert cfg.api_key == "test-key"
            assert cfg.model == "whisper-1"
            assert cfg.timeout == 60
            assert cfg.max_retries == 3
    
    def test_config_from_env(self):
        """Test configuration from environment variables."""
        env_vars = {
            "OPENAI_API_KEY": "custom-key",
            "OPENAI_MODEL": "gpt-4o-transcribe",
            "OPENAI_TIMEOUT": "120",
            "OPENAI_MAX_RETRIES": "5",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            cfg = OpenAIConfig()
            assert cfg.api_key == "custom-key"
            assert cfg.model == "gpt-4o-transcribe"
            assert cfg.timeout == 120
            assert cfg.max_retries == 5
    
    def test_config_validation_missing_api_key(self):
        """Test validation fails when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            cfg = OpenAIConfig()
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                cfg.validate()
    
    def test_config_validation_invalid_model(self):
        """Test validation fails for invalid model."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_MODEL": "invalid-model"}, clear=True):
            cfg = OpenAIConfig()
            with pytest.raises(ValueError, match="Invalid model"):
                cfg.validate()
    
    def test_config_validation_invalid_timeout(self):
        """Test validation fails for invalid timeout."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_TIMEOUT": "-1"}, clear=True):
            cfg = OpenAIConfig()
            with pytest.raises(ValueError, match="Timeout must be positive"):
                cfg.validate()


class TestOpenAITranscriptionService:
    """Tests for OpenAI transcription service."""
    
    def test_initialization_success(self, mock_config):
        """Test successful service initialization."""
        with patch("app.services.openai_service.config", mock_config):
            with patch("app.services.openai_service.OpenAI") as mock_openai:
                service = OpenAITranscriptionService()
                assert service.client is not None
                mock_openai.assert_called_once()
    
    def test_initialization_missing_api_key(self):
        """Test initialization fails without API key."""
        bad_config = OpenAIConfig()
        bad_config.api_key = None
        with patch("app.services.openai_service.config", bad_config):
            with pytest.raises(APIKeyError):
                OpenAITranscriptionService()
    
    def test_validate_audio_file_success(self, temp_audio_file, mock_config):
        """Test audio file validation with valid file."""
        with patch("app.services.openai_service.config", mock_config):
            with patch("app.services.openai_service.OpenAI"):
                service = OpenAITranscriptionService()
                path = service._validate_audio_file(temp_audio_file)
                assert isinstance(path, Path)
                assert path.exists()
    
    def test_validate_audio_file_not_found(self, mock_config):
        """Test audio file validation with non-existent file."""
        with patch("app.services.openai_service.config", mock_config):
            with patch("app.services.openai_service.OpenAI"):
                service = OpenAITranscriptionService()
                with pytest.raises(FileNotFoundError):
                    service._validate_audio_file("/nonexistent/file.mp3")
    
    def test_validate_audio_file_unsupported_format(self, mock_config):
        """Test audio file validation with unsupported format."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"not audio")
            temp_path = f.name
        
        try:
            with patch("app.services.openai_service.config", mock_config):
                with patch("app.services.openai_service.OpenAI"):
                    service = OpenAITranscriptionService()
                    with pytest.raises(AudioFormatError, match="Unsupported audio format"):
                        service._validate_audio_file(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_transcribe_audio_success(self, temp_audio_file, mock_config, mock_openai_client):
        """Test successful audio transcription."""
        mock_openai_client.audio.transcriptions.create.return_value = "This is the transcribed text."
        
        with patch("app.services.openai_service.config", mock_config):
            with patch("app.services.openai_service.OpenAI", return_value=mock_openai_client):
                service = OpenAITranscriptionService()
                result = service.transcribe_audio(temp_audio_file)
                
                assert result == "This is the transcribed text."
                mock_openai_client.audio.transcriptions.create.assert_called_once()
                call_kwargs = mock_openai_client.audio.transcriptions.create.call_args[1]
                assert call_kwargs["model"] == "whisper-1"
                assert call_kwargs["response_format"] == "text"
    
    def test_transcribe_audio_with_language(self, temp_audio_file, mock_config, mock_openai_client):
        """Test transcription with explicit language parameter."""
        mock_openai_client.audio.transcriptions.create.return_value = "Transcribed text."
        
        with patch("app.services.openai_service.config", mock_config):
            with patch("app.services.openai_service.OpenAI", return_value=mock_openai_client):
                service = OpenAITranscriptionService()
                result = service.transcribe_audio(temp_audio_file, language="es")
                
                assert result == "Transcribed text."
                call_kwargs = mock_openai_client.audio.transcriptions.create.call_args[1]
                assert call_kwargs["language"] == "es"
    
    def test_transcribe_audio_authentication_error(self, temp_audio_file, mock_config, mock_openai_client):
        """Test handling of authentication errors (401)."""
        mock_openai_client.audio.transcriptions.create.side_effect = openai.AuthenticationError(
            "Invalid API key",
            response=Mock(status_code=401),
            body=None
        )
        
        with patch("app.services.openai_service.config", mock_config):
            with patch("app.services.openai_service.OpenAI", return_value=mock_openai_client):
                service = OpenAITranscriptionService()
                with pytest.raises(APIKeyError, match="Invalid API key"):
                    service.transcribe_audio(temp_audio_file)
    
    def test_transcribe_audio_bad_request_error(self, temp_audio_file, mock_config, mock_openai_client):
        """Test handling of bad request errors (400)."""
        mock_openai_client.audio.transcriptions.create.side_effect = openai.BadRequestError(
            "Invalid audio format",
            response=Mock(status_code=400),
            body=None
        )
        
        with patch("app.services.openai_service.config", mock_config):
            with patch("app.services.openai_service.OpenAI", return_value=mock_openai_client):
                service = OpenAITranscriptionService()
                with pytest.raises(AudioFormatError, match="Invalid audio format"):
                    service.transcribe_audio(temp_audio_file)
    
    def test_transcribe_audio_rate_limit_error(self, temp_audio_file, mock_config, mock_openai_client):
        """Test handling of rate limit errors (429)."""
        mock_openai_client.audio.transcriptions.create.side_effect = openai.RateLimitError(
            "Rate limit exceeded",
            response=Mock(status_code=429),
            body=None
        )
        
        with patch("app.services.openai_service.config", mock_config):
            with patch("app.services.openai_service.OpenAI", return_value=mock_openai_client):
                service = OpenAITranscriptionService()
                with pytest.raises(RateLimitError, match="Rate limit exceeded"):
                    service.transcribe_audio(temp_audio_file)
    
    def test_transcribe_audio_timeout_error(self, temp_audio_file, mock_config, mock_openai_client):
        """Test handling of timeout errors."""
        mock_openai_client.audio.transcriptions.create.side_effect = openai.APITimeoutError(
            "Request timed out"
        )
        
        with patch("app.services.openai_service.config", mock_config):
            with patch("app.services.openai_service.OpenAI", return_value=mock_openai_client):
                service = OpenAITranscriptionService()
                with pytest.raises(MaxRetriesExceededError):  # Timeout is retried
                    service.transcribe_audio(temp_audio_file)
    
    def test_transcribe_audio_network_error(self, temp_audio_file, mock_config, mock_openai_client):
        """Test handling of network errors."""
        mock_openai_client.audio.transcriptions.create.side_effect = openai.APIConnectionError(
            "Connection failed"
        )
        
        with patch("app.services.openai_service.config", mock_config):
            with patch("app.services.openai_service.OpenAI", return_value=mock_openai_client):
                service = OpenAITranscriptionService()
                with pytest.raises(MaxRetriesExceededError):  # Network errors are retried
                    service.transcribe_audio(temp_audio_file)
    
    def test_transcribe_audio_server_error(self, temp_audio_file, mock_config, mock_openai_client):
        """Test handling of server errors (500)."""
        mock_openai_client.audio.transcriptions.create.side_effect = openai.InternalServerError(
            "Internal server error",
            response=Mock(status_code=500),
            body=None
        )
        
        with patch("app.services.openai_service.config", mock_config):
            with patch("app.services.openai_service.OpenAI", return_value=mock_openai_client):
                service = OpenAITranscriptionService()
                with pytest.raises(MaxRetriesExceededError):  # Server errors are retried
                    service.transcribe_audio(temp_audio_file)
    
    def test_retry_logic_eventual_success(self, temp_audio_file, mock_config, mock_openai_client):
        """Test retry logic succeeds after transient failures."""
        # Fail twice, then succeed
        mock_openai_client.audio.transcriptions.create.side_effect = [
            openai.APIConnectionError("Connection failed"),
            openai.InternalServerError("Server error", response=Mock(status_code=500), body=None),
            "Success after retries"
        ]
        
        with patch("app.services.openai_service.config", mock_config):
            with patch("app.services.openai_service.OpenAI", return_value=mock_openai_client):
                service = OpenAITranscriptionService()
                result = service.transcribe_audio(temp_audio_file)
                
                assert result == "Success after retries"
                assert mock_openai_client.audio.transcriptions.create.call_count == 3
    
    def test_retry_logic_max_retries_exceeded(self, temp_audio_file, mock_config, mock_openai_client):
        """Test max retries exceeded with persistent failure."""
        mock_openai_client.audio.transcriptions.create.side_effect = openai.APIConnectionError(
            "Connection failed"
        )
        
        with patch("app.services.openai_service.config", mock_config):
            with patch("app.services.openai_service.OpenAI", return_value=mock_openai_client):
                service = OpenAITranscriptionService()
                with pytest.raises(MaxRetriesExceededError) as exc_info:
                    service.transcribe_audio(temp_audio_file)
                
                assert exc_info.value.attempts == 4  # Initial + 3 retries
                # Should have tried 4 times (initial + 3 retries)
                assert mock_openai_client.audio.transcriptions.create.call_count == 4
    
    def test_no_retry_for_non_transient_errors(self, temp_audio_file, mock_config, mock_openai_client):
        """Test that non-transient errors are not retried."""
        mock_openai_client.audio.transcriptions.create.side_effect = openai.AuthenticationError(
            "Invalid API key",
            response=Mock(status_code=401),
            body=None
        )
        
        with patch("app.services.openai_service.config", mock_config):
            with patch("app.services.openai_service.OpenAI", return_value=mock_openai_client):
                service = OpenAITranscriptionService()
                with pytest.raises(APIKeyError):
                    service.transcribe_audio(temp_audio_file)
                
                # Should only try once (no retries)
                assert mock_openai_client.audio.transcriptions.create.call_count == 1
    
    def test_calculate_retry_delay(self, mock_config):
        """Test exponential backoff calculation."""
        with patch("app.services.openai_service.config", mock_config):
            with patch("app.services.openai_service.OpenAI"):
                service = OpenAITranscriptionService()
                
                # Test exponential growth
                delay0 = service._calculate_retry_delay(0)
                delay1 = service._calculate_retry_delay(1)
                delay2 = service._calculate_retry_delay(2)
                
                assert delay0 == 0.1  # initial_retry_delay
                assert delay1 == 0.2  # 0.1 * 2^1
                assert delay2 == 0.4  # 0.1 * 2^2
                
                # Test max delay cap
                delay_large = service._calculate_retry_delay(10)
                assert delay_large == 1.0  # Capped at max_retry_delay
    
    def test_should_retry(self, mock_config):
        """Test retry decision logic."""
        with patch("app.services.openai_service.config", mock_config):
            with patch("app.services.openai_service.OpenAI"):
                service = OpenAITranscriptionService()
                
                # Should retry transient errors
                assert service._should_retry(NetworkError("Network error"))
                assert service._should_retry(ServerError("Server error"))
                assert service._should_retry(APITimeoutError("Timeout"))
                
                # Should not retry non-transient errors
                assert not service._should_retry(APIKeyError("Bad key"))
                assert not service._should_retry(AudioFormatError("Bad format"))
                assert not service._should_retry(RateLimitError("Rate limit"))


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""
    
    def test_transcribe_audio_convenience_function(self, temp_audio_file, mock_config, mock_openai_client):
        """Test the convenience transcribe_audio function."""
        mock_openai_client.audio.transcriptions.create.return_value = "Transcribed text."
        
        with patch("app.services.openai_service.config", mock_config):
            with patch("app.services.openai_service.OpenAI", return_value=mock_openai_client):
                # Reset the singleton
                import app.services.openai_service as service_module
                service_module._service_instance = None
                
                result = transcribe_audio(temp_audio_file)
                assert result == "Transcribed text."
