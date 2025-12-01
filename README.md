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
# Speech-to-Text Transcription Service

A production-ready speech-to-text transcription service built with OpenAI API, FastAPI, and Redis Queue for asynchronous job processing.

## Features

- **Multi-language transcription** with code-switching support
- **Asynchronous job processing** using Redis Queue (RQ)
- **Custom lexicon support** for domain-specific terms
- **Scalable worker architecture** with horizontal scaling
- **Job retry and failure handling**
- **Docker support** for easy deployment
# Speech-to-Text Transcription API

Asynchronous audio transcription service with domain-specific lexicon support.

## Features

- **Async Processing**: Submit audio files and receive immediate job_id for status tracking
- **Multiple Formats**: Supports WAV, MP3, and M4A audio files
- **Lexicon Support**: Domain-specific transcription with custom lexicons (e.g., radiology, legal)
- **API Key Authentication**: Secure access control
- **File Validation**: Size and format validation with clear error messages
- **Docker Deployment**: Easy containerized deployment with Docker Compose

## Quick Start

### 1. Setup Environment

- Python 3.9+
- Redis 5.0+
- Docker & Docker Compose (optional)

### Installation

1. **Clone the repository**

2. **Install dependencies**
   ```bash
   pip install -e .
   # or
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Running with Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Scale workers
docker-compose up -d --scale worker=4

# Stop services
docker-compose down
```

### Running Locally

1. **Start Redis**
   ```bash
   redis-server
   ```

2. **Start worker(s)**
   ```bash
   python -m app.workers.transcription_worker
   ```

3. **Start API server** (when implemented)
   ```bash
   uvicorn app.main:app --reload
   ```

## Usage Example

```python
from app.services.queue import enqueue_transcription_job, get_job_status

# Enqueue a transcription job
job = enqueue_transcription_job(
    job_id="unique-job-123",
    audio_file_path="/path/to/audio.mp3",
    lexicon_id="medical-terms",
    api_key_id="openai-key-1"
)

# Check job status
status = get_job_status("unique-job-123")
print(status)
```

See `example_usage.py` for more examples.

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── queue.py              # Queue service (Redis/RQ)
│   └── workers/
│       ├── __init__.py
│       └── transcription_worker.py  # Worker process
├── docker-compose.yml             # Docker services configuration
├── Dockerfile                     # Container image definition
├── pyproject.toml                 # Project dependencies
├── requirements.txt               # Alternative dependencies file
├── .env.example                   # Environment variables template
└── README_WORKER.md               # Detailed worker documentation
```

## Documentation

- **[Worker Documentation](README_WORKER.md)** - Comprehensive guide for workers, queue management, and deployment
- **[Project Description](description.md)** - Original project overview and components

## Configuration

Key environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `QUEUE_NAME` | `transcription_jobs` | Job queue name |
| `JOB_TIMEOUT` | `300` | Job timeout (seconds) |
| `WORKER_COUNT` | `2` | Number of workers |

See `.env.example` for all available options.

## Worker Commands

```bash
# Start worker directly
python -m app.workers.transcription_worker

# Using RQ CLI
rq worker transcription_jobs --url redis://localhost:6379/0

# View queue info
rq info --url redis://localhost:6379/0

# Empty queue
rq empty transcription_jobs --url redis://localhost:6379/0
```

## Monitoring

### RQ Dashboard

```bash
pip install rq-dashboard
rq-dashboard --redis-url redis://localhost:6379/0
```

Access at: http://localhost:9181

### Queue Statistics

```python
from app.services.queue import get_queue_stats

stats = get_queue_stats()
print(f"Queued: {stats['queued_count']}")
print(f"Running: {stats['started_count']}")
print(f"Failed: {stats['failed_count']}")
```

## Development Status

- [x] Redis queue and worker architecture
- [x] Job enqueuing and status tracking
- [x] Docker deployment configuration
- [ ] OpenAI Whisper API integration (upcoming)
- [ ] FastAPI endpoints (upcoming)
- [ ] Database integration (upcoming)

## License

See LICENSE file for details.
```bash
# Copy environment template
cp .env.example .env

# Edit configuration if needed
nano .env
```

### 2. Run with Docker Compose

```bash
# Build and start the service
docker-compose up -d

# View logs
docker-compose logs -f
```

The API will be available at `http://localhost:8000`

### 3. Create API Key (First Time Setup)

```python
# Run Python in the container
docker-compose exec api python

# Create an API key
from app.database import SessionLocal, init_db
from app.models import APIKey
import uuid

init_db()
db = SessionLocal()

api_key = APIKey(
    id=str(uuid.uuid4()),
    key="your-secret-api-key-here",
    name="Test API Key",
    is_active=1
)
db.add(api_key)
db.commit()
print(f"Created API Key: {api_key.key}")
db.close()
```

## API Usage

### Submit Transcription Job

**Endpoint:** `POST /transcribe`

**Headers:**
- `X-API-Key`: Your API key (required)
- `X-Lexicon-ID`: Lexicon to use (optional, defaults to 'radiology')

**Form Data:**
- `audio`: Audio file (WAV, MP3, or M4A)

**Alternative:** You can also pass lexicon via query parameter: `?lexicon=radiology`

**Example with cURL:**

```bash
curl -X POST "http://localhost:8000/transcribe" \
  -H "X-API-Key: your-secret-api-key-here" \
  -H "X-Lexicon-ID: radiology" \
  -F "audio=@/path/to/audio.wav"
```

**Example with Python:**

```python
import requests

url = "http://localhost:8000/transcribe"
headers = {
    "X-API-Key": "your-secret-api-key-here",
    "X-Lexicon-ID": "radiology"
}
files = {
    "audio": open("audio.wav", "rb")
}

response = requests.post(url, headers=headers, files=files)
print(response.json())
```

**Success Response (202 Accepted):**

```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**

- `400 Bad Request`: Invalid file format or missing required fields
- `401 Unauthorized`: Missing or invalid API key
- `413 Payload Too Large`: File exceeds size limit
- `500 Internal Server Error`: Storage or database error

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./data/transcription.db` | Database connection string |
| `AUDIO_STORAGE_PATH` | `/app/audio_storage` | Directory for audio file storage |
| `MAX_FILE_SIZE_MB` | `10` | Maximum file size in megabytes |
| `DEFAULT_LEXICON` | `radiology` | Default lexicon if not specified |

### Supported Audio Formats

- **WAV**: `audio/wav`, `audio/x-wav`
- **MP3**: `audio/mpeg`, `audio/mp3`
- **M4A**: `audio/mp4`, `audio/x-m4a`

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection & session
│   ├── models.py            # SQLAlchemy models
│   ├── auth.py              # API key authentication
│   └── routers/
│       ├── __init__.py
│       └── transcription.py # Transcription endpoint
├── audio_storage/           # Audio file storage (mounted volume)
├── data/                    # Database storage (mounted volume)
├── docker-compose.yml       # Docker Compose configuration
├── Dockerfile               # Docker image definition
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Development

### Run Locally (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p audio_storage data

# Run the server
uvicorn app.main:app --reload
```

### API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Next Steps

After implementing this endpoint, the next steps would be:
1. Implement job status API endpoint to check transcription progress
2. Add background worker for actual transcription processing
3. Implement webhook notifications for job completion
4. Add transcript retrieval endpoint

## Support

For detailed worker documentation, troubleshooting, and best practices, see [README_WORKER.md](README_WORKER.md).
[Add your license here]
