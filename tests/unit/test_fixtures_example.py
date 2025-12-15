"""
Example unit tests demonstrating fixture usage.

These tests show how to use the various fixtures provided in conftest.py
for testing different components of the application.
"""

import pytest
from unittest.mock import Mock, patch


@pytest.mark.unit
def test_with_sample_data(sample_job_data):
    """
    Example test using sample job data fixture.
    
    Demonstrates how to use pre-defined test data fixtures
    for consistent test setup.
    """
    assert sample_job_data["id"] == "test-job-123"
    assert sample_job_data["status"] == "pending"
    assert sample_job_data["transcript"] is None


@pytest.mark.unit
def test_with_lexicon_data(sample_lexicon_data):
    """
    Example test using sample lexicon data.
    
    Shows how to access test lexicon data for testing
    text processing and replacement features.
    """
    assert "mri" in sample_lexicon_data
    assert sample_lexicon_data["mri"] == "MRI"
    assert sample_lexicon_data["ct"] == "CT"


@pytest.mark.unit
def test_with_mock_openai(mock_openai_client):
    """
    Example test using mock OpenAI client.
    
    Demonstrates testing code that uses OpenAI API
    without making real API calls.
    """
    # Mock is already configured with default responses
    result = mock_openai_client.audio.transcriptions.create(
        model="whisper-1",
        file=Mock()
    )
    
    # Verify mock response
    assert hasattr(result, "text")
    assert result.text == "This is a test transcription."


@pytest.mark.unit
def test_with_mock_redis(mock_redis_client):
    """
    Example test using mock Redis client.
    
    Shows how to test Redis-dependent code without
    a real Redis instance.
    """
    # Use mock Redis client
    mock_redis_client.set("test_key", "test_value")
    mock_redis_client.get.return_value = "test_value"
    
    value = mock_redis_client.get("test_key")
    assert value == "test_value"
    
    # Verify calls
    mock_redis_client.set.assert_called_with("test_key", "test_value")


@pytest.mark.unit
def test_with_auth_headers(auth_headers):
    """
    Example test using authentication headers.
    
    Demonstrates testing authenticated API requests
    with pre-configured headers.
    """
    assert "Authorization" in auth_headers
    assert auth_headers["Authorization"].startswith("Bearer ")
    assert "Content-Type" in auth_headers


@pytest.mark.unit
def test_with_test_settings(test_settings):
    """
    Example test using test settings.
    
    Shows how to access test configuration values
    for verifying settings-dependent behavior.
    """
    assert test_settings.TESTING is None or test_settings.DEBUG is True
    assert test_settings.OPENAI_API_KEY == "test-api-key-12345"
    assert test_settings.DATABASE_URL == "sqlite:///:memory:"


@pytest.mark.unit
def test_string_processing(sample_transcription_text):
    """
    Example test demonstrating simple text processing.
    
    Uses sample transcription text to test text manipulation
    or validation logic.
    """
    # Example: Test that text contains expected terms
    assert "patient" in sample_transcription_text.lower()
    assert "mri" in sample_transcription_text.lower()
    assert "scan" in sample_transcription_text.lower()
    
    # Example: Test text length
    assert len(sample_transcription_text) > 0
    assert len(sample_transcription_text.split()) > 5


@pytest.mark.unit
def test_mock_queue_usage(mock_queue):
    """
    Example test using mock queue fixture.
    
    Demonstrates testing background job queueing
    without a real RQ queue.
    """
    # Enqueue a job
    job = mock_queue.enqueue(lambda: "test")
    
    # Verify job properties
    assert job.id == "test-job-123"
    assert job.get_status() == "queued"
    
    # Verify queue was called
    mock_queue.enqueue.assert_called_once()


@pytest.mark.unit
@pytest.mark.parametrize("input_text,expected_length", [
    ("short", 5),
    ("medium text here", 16),
    ("", 0),
])
def test_parametrized_example(input_text, expected_length):
    """
    Example of parametrized test.
    
    Shows how to test multiple cases efficiently
    with different input values.
    """
    assert len(input_text) == expected_length


@pytest.mark.unit
def test_exception_handling():
    """
    Example test for exception handling.
    
    Demonstrates testing that code properly raises
    exceptions for invalid input.
    """
    def divide(a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    
    # Test normal case
    assert divide(10, 2) == 5
    
    # Test exception
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0)


# Example of test class grouping related tests
class TestExampleFeature:
    """
    Group related tests in a class.
    
    This helps organize tests for a specific feature
    or component.
    """
    
    @pytest.mark.unit
    def test_feature_valid_input(self):
        """Test feature with valid input."""
        result = "valid".upper()
        assert result == "VALID"
    
    @pytest.mark.unit
    def test_feature_edge_case(self):
        """Test feature with edge case."""
        result = "".upper()
        assert result == ""
    
    @pytest.mark.unit
    def test_feature_with_fixture(self, sample_job_data):
        """Test feature using fixture."""
        assert sample_job_data["id"] is not None
