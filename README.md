# Speech-to-Text Service (STT)

A **speech-to-text prototype** built with the **OpenAI API** (`gpt-4o-transcribe` / `whisper-1`) that transcribes multi-language audio while preserving each word in its original language or script (code-switching).

## Overview

This service is designed as a **proof of concept (PoC)** for client demos, providing high-accuracy transcription with support for:

- **Multi-language transcription** with code-switching support
- **Custom lexicon** for domain-specific terms (drug names, brand names, etc.)
- **Feedback and learning** system for continuous improvement
- **Plain text output** (no JSON, subtitles, or punctuation correction)
- **Multiple audio formats** (WAV, MP3, M4A)

## Main Components

### 1. ASR Layer (Speech → Text)
- Uses **OpenAI models** for transcription
- Works with streaming or batch audio
- Supports **custom lexicon** for recognizing domain-specific terms
- Produces raw text with high accuracy

### 2. Post-Processing Layer
- **Keeps original language/script** of each word
- **Handles numerals** (e.g., "10 mg") consistently
- **Uses lexicon** to fix misspellings and protect critical words
- **Output format**: plain text paragraph

### 3. Feedback & Learning
- Reviewers can edit transcripts and see differences
- System learns from edits — adding new terms or corrections to lexicon
- Monitors performance metrics (accuracy, edit rate, latency)
- Supports versioning and quick rollback

### 4. Data Layer
- Supports **WAV, MP3, and M4A** audio files
- Maintains **JSON-based lexicon** for each task or flow
- PostgreSQL for persistent storage
- Redis for caching and job queue management

## Project Structure

```
/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app instance
│   ├── config.py            # Settings/configuration
│   ├── models/              # SQLAlchemy models
│   ├── api/                 # API endpoints/routes
│   ├── services/            # Business logic
│   └── utils/               # Utility functions
├── tests/
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
├── migrations/              # Alembic database migrations
├── config/                  # Configuration files
├── pyproject.toml           # Project dependencies
├── .env.example             # Environment variables template
└── README.md                # This file
```

## Prerequisites

- **Python 3.10+**
- **PostgreSQL 14+**
- **Redis 6+**
- **OpenAI API Key** (get it from [OpenAI Platform](https://platform.openai.com/api-keys))

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd stt-service
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

Install core dependencies:
```bash
pip install -e .
```

Install development dependencies (optional but recommended):
```bash
pip install -e ".[dev]"
```

### 4. Configure Environment Variables

Copy the example environment file and configure it:
```bash
cp .env.example .env
```

Edit `.env` with your actual configuration:
- Set your `OPENAI_API_KEY`
- Configure `DATABASE_URL` for your PostgreSQL instance
- Configure `REDIS_URL` for your Redis instance
- Generate `API_KEY_HASH_SECRET` using:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```

### 5. Set Up Database

Start PostgreSQL and create the database:
```bash
createdb stt_db
```

Run database migrations:
```bash
alembic upgrade head
```

### 6. Start Redis

Ensure Redis is running:
```bash
redis-server
# Or if installed via system package manager:
sudo systemctl start redis
```

### 7. Run the Application

Start the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
API documentation (Swagger UI) will be available at `http://localhost:8000/docs`

## Development

### Running Tests

Run all tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=app --cov-report=html
```

Run specific test types:
```bash
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only
```

### Code Formatting

Format code with black:
```bash
black app/ tests/
```

### Linting

Run ruff linter:
```bash
ruff check app/ tests/
```

### Type Checking

Run mypy for type checking:
```bash
mypy app/
```

## Technology Stack

- **Web Framework**: FastAPI (with Uvicorn ASGI server)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migrations**: Alembic
- **Cache/Queue**: Redis
- **HTTP Client**: httpx (for OpenAI API calls)
- **Configuration**: Pydantic Settings
- **Testing**: pytest, pytest-asyncio, pytest-cov

## API Documentation

Once the application is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Environment Variables

See `.env.example` for a complete list of required environment variables and their descriptions.

Key variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `OPENAI_API_KEY`: Your OpenAI API key
- `MAX_FILE_SIZE`: Maximum audio file size (bytes)
- `MAX_WORKERS`: Concurrent processing workers
- `API_KEY_HASH_SECRET`: Secret for API key hashing

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and ensure they pass
4. Format code with black
5. Run linter and fix any issues
6. Submit a pull request

## License

[Add your license information here]

## Support

For issues, questions, or contributions, please [open an issue](link-to-issues) or contact the development team.
