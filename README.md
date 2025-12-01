# OpenAI Whisper API Integration

A robust integration layer for OpenAI's Whisper API to handle audio transcription with comprehensive error handling, retry logic, and multilingual support.

## Features

- ✅ **Multiple Audio Formats**: Supports WAV, MP3, M4A, MP4, MPEG, MPGA, WebM, OGG, and FLAC
- ✅ **Multilingual Support**: Automatic language detection with code-switching preservation
- ✅ **Robust Error Handling**: Specific exception types for different error scenarios
- ✅ **Retry Logic**: Exponential backoff for transient failures (network errors, 5xx)
- ✅ **Configurable**: Environment variable-based configuration
- ✅ **Production Ready**: Comprehensive logging and monitoring capabilities
- ✅ **Fully Tested**: Unit tests with mocked API responses

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export OPENAI_API_KEY="your-api-key-here"
export OPENAI_MODEL="whisper-1"  # Optional: defaults to whisper-1
export OPENAI_TIMEOUT="60"       # Optional: defaults to 60 seconds
```

## Quick Start

### Basic Usage

```python
from app.services.openai_service import transcribe_audio

# Transcribe an audio file
text = transcribe_audio("/path/to/audio.mp3")
print(text)
```

### With Language Specification

```python
# Specify language for better accuracy (ISO-639-1 code)
text = transcribe_audio("/path/to/audio.mp3", language="es")
```

### Using the Service Class

```python
from app.services.openai_service import OpenAITranscriptionService

# Create service instance
service = OpenAITranscriptionService()

# Transcribe audio
text = service.transcribe_audio("/path/to/audio.mp3")
```

## Configuration

All configuration is done via environment variables:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | None | Yes |
| `OPENAI_MODEL` | Whisper model to use | `whisper-1` | No |
| `OPENAI_TIMEOUT` | API request timeout (seconds) | `60` | No |
| `OPENAI_MAX_RETRIES` | Maximum retry attempts | `3` | No |
| `OPENAI_INITIAL_RETRY_DELAY` | Initial retry delay (seconds) | `1.0` | No |
| `OPENAI_MAX_RETRY_DELAY` | Maximum retry delay (seconds) | `60.0` | No |
| `OPENAI_RETRY_MULTIPLIER` | Retry backoff multiplier | `2.0` | No |

### Supported Models

- `whisper-1` (default): Standard Whisper model
- `gpt-4o-transcribe`: Advanced GPT-4o transcription model

## Error Handling

The integration provides specific exception types for different error scenarios:

```python
from app.exceptions import (
    APIKeyError,           # 401: Invalid or missing API key
    AudioFormatError,      # 400: Invalid audio format
    RateLimitError,        # 429: Rate limit exceeded
    APITimeoutError,       # Request timeout
    NetworkError,          # Network/connection errors
    ServerError,           # 5xx: Server errors
    FileNotFoundError,     # File doesn't exist
    MaxRetriesExceededError  # All retry attempts failed
)

try:
    text = transcribe_audio("/path/to/audio.mp3")
except APIKeyError as e:
    print(f"API key error: {e}")
except AudioFormatError as e:
    print(f"Invalid audio format: {e}")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except MaxRetriesExceededError as e:
    print(f"Failed after {e.attempts} attempts: {e.last_error}")
```

## Retry Behavior

The service automatically retries **transient errors** with exponential backoff:

- **Retried**: Network errors, server errors (5xx), timeouts
- **Not Retried**: Authentication errors, invalid audio format, rate limits
- **Backoff**: Exponential with configurable initial delay and multiplier
- **Max Delay**: Capped at configured maximum

Example retry sequence (default config):
- Attempt 1: Immediate
- Attempt 2: After 1.0s
- Attempt 3: After 2.0s
- Attempt 4: After 4.0s

## Logging

The service logs important events for debugging and monitoring:

```python
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Service logs will include:
# - Client initialization
# - Transcription start (file, size, model)
# - Transcription completion (duration, text length)
# - Errors and retry attempts
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_openai_service.py

# Run specific test
pytest tests/test_openai_service.py::TestOpenAITranscriptionService::test_transcribe_audio_success
```

## Multilingual Support

### Automatic Language Detection

By default, Whisper automatically detects the language:

```python
text = transcribe_audio("multilingual_audio.mp3")
# Whisper detects language automatically
```

### Explicit Language Specification

For better accuracy, specify the primary language:

```python
# Spanish audio
text = transcribe_audio("spanish_audio.mp3", language="es")

# Chinese audio
text = transcribe_audio("chinese_audio.mp3", language="zh")

# Arabic audio
text = transcribe_audio("arabic_audio.mp3", language="ar")
```

### Code-Switching

The service preserves original language/script for each word in multilingual audio:

```python
# Audio with English and Spanish
text = transcribe_audio("code_switched_audio.mp3")
# Result: "Hello amigo, how are you? Muy bien, gracias!"
```

## Architecture

```
app/
├── __init__.py
├── config.py              # Configuration from environment variables
├── exceptions.py          # Custom exception classes
└── services/
    ├── __init__.py
    └── openai_service.py  # Main transcription service

tests/
├── __init__.py
└── test_openai_service.py # Comprehensive unit tests
```

## API Reference

### `transcribe_audio(file_path: str, language: Optional[str] = None) -> str`

Convenience function to transcribe audio using the global service instance.

**Parameters:**
- `file_path` (str): Path to the audio file
- `language` (Optional[str]): ISO-639-1 language code (e.g., 'en', 'es', 'zh')

**Returns:**
- str: Plain text transcription

**Raises:**
- Various `TranscriptionError` subclasses based on error type

### `OpenAITranscriptionService`

Main service class for transcription operations.

**Methods:**
- `transcribe_audio(file_path: str, language: Optional[str] = None) -> str`: Transcribe audio file

## Production Checklist

Before deploying to production:

- [ ] Set `OPENAI_API_KEY` in production environment
- [ ] Configure appropriate `OPENAI_TIMEOUT` for your audio files
- [ ] Set up logging aggregation (e.g., CloudWatch, Datadog)
- [ ] Monitor API call metrics (duration, file size, errors)
- [ ] Set up alerts for `MaxRetriesExceededError` and `RateLimitError`
- [ ] Consider audio file size limits (25MB for Whisper API)
- [ ] Implement rate limiting on your end if processing high volumes
- [ ] Test with representative audio samples from your use case

## Limitations

- **File Size**: OpenAI Whisper API has a 25MB file size limit
- **File Format**: Only audio formats are supported (no video processing)
- **Rate Limits**: Subject to OpenAI API rate limits (varies by account tier)
- **Cost**: Each API call incurs charges based on audio duration

## Troubleshooting

### "OPENAI_API_KEY environment variable is not set"

Set your API key:
```bash
export OPENAI_API_KEY="sk-..."
```

### "Invalid audio format"

Ensure your file is in a supported format (WAV, MP3, M4A, etc.) and not corrupted.

### "Rate limit exceeded"

Wait for the specified `retry_after` duration or upgrade your OpenAI account tier.

### "Request timed out"

Increase the timeout for large files:
```bash
export OPENAI_TIMEOUT="120"
```

### "Maximum retry attempts exceeded"

Check your network connection and OpenAI service status. The error message includes the last error encountered.

## License

This project is part of a speech-to-text prototype for client demos.

## Support

For issues or questions, please check:
1. OpenAI API status: https://status.openai.com/
2. OpenAI documentation: https://platform.openai.com/docs/guides/speech-to-text
3. Project logs for detailed error messages
