"""
Helper utilities for integration tests.

Provides common utilities for test data creation, validation,
and API interaction patterns.
"""
import time
from typing import Optional, Dict, Any

from fastapi.testclient import TestClient


def wait_for_job_completion(
    client: TestClient,
    job_id: str,
    api_key: str,
    timeout: int = 10,
    poll_interval: float = 0.5
) -> Dict[str, Any]:
    """
    Poll for job completion with timeout.
    
    Args:
        client: FastAPI test client
        job_id: Job ID to poll
        api_key: API key for authentication
        timeout: Maximum time to wait in seconds
        poll_interval: Time between polls in seconds
        
    Returns:
        Final job status response
        
    Raises:
        TimeoutError: If job doesn't complete within timeout
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = client.get(
            f"/jobs/{job_id}",
            headers={"X-API-Key": api_key}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data["status"] in ["completed", "failed"]:
                return data
        
        time.sleep(poll_interval)
    
    raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")


def create_test_audio_file(format: str = "mp3") -> bytes:
    """
    Create minimal valid audio file content for testing.
    
    Args:
        format: Audio format (mp3, wav, m4a)
        
    Returns:
        Bytes content for the audio file
    """
    if format == "mp3":
        # Minimal MP3 header
        return b'\xFF\xFB\x90\x00' + b'\x00' * 1000
    elif format == "wav":
        # Minimal WAV header (RIFF format)
        return b'RIFF' + b'\x00' * 4 + b'WAVE' + b'fmt ' + b'\x00' * 100
    elif format == "m4a":
        # Minimal M4A header
        return b'\x00\x00\x00\x20ftyp' + b'M4A ' + b'\x00' * 100
    else:
        raise ValueError(f"Unsupported format: {format}")


def assert_error_response(
    response,
    expected_status: int,
    expected_detail: Optional[str] = None
):
    """
    Assert that response is an error with expected status and detail.
    
    Args:
        response: Response object from test client
        expected_status: Expected HTTP status code
        expected_detail: Expected error detail message (substring match)
    """
    assert response.status_code == expected_status, \
        f"Expected status {expected_status}, got {response.status_code}: {response.text}"
    
    if expected_detail:
        data = response.json()
        assert "detail" in data, "Error response should contain 'detail' field"
        assert expected_detail.lower() in data["detail"].lower(), \
            f"Expected detail containing '{expected_detail}', got: {data['detail']}"


def assert_datetime_format(datetime_str: str):
    """
    Assert that a string is in valid ISO 8601 datetime format.
    
    Args:
        datetime_str: Datetime string to validate
    """
    from datetime import datetime
    try:
        datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        raise AssertionError(f"Invalid datetime format: {datetime_str}")


def create_multipart_file(filename: str, content: bytes, content_type: str = None):
    """
    Create multipart file data for file upload testing.
    
    Args:
        filename: Name of the file
        content: File content as bytes
        content_type: MIME type (auto-detected if None)
        
    Returns:
        Tuple of (filename, content, content_type)
    """
    if content_type is None:
        if filename.endswith('.mp3'):
            content_type = "audio/mpeg"
        elif filename.endswith('.wav'):
            content_type = "audio/wav"
        elif filename.endswith('.m4a'):
            content_type = "audio/mp4"
        else:
            content_type = "application/octet-stream"
    
    return (filename, content, content_type)
