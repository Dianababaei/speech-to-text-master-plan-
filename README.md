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

## License

[Add your license here]
