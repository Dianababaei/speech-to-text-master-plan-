# Speech-to-Text Transcription Service

A production-ready speech-to-text transcription service built with OpenAI API, FastAPI, and Redis Queue for asynchronous job processing.

## Features

- **Multi-language transcription** with code-switching support
- **Asynchronous job processing** using Redis Queue (RQ)
- **Custom lexicon support** for domain-specific terms
- **Scalable worker architecture** with horizontal scaling
- **Job retry and failure handling**
- **Docker support** for easy deployment

## Quick Start

### Prerequisites

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

## Support

For detailed worker documentation, troubleshooting, and best practices, see [README_WORKER.md](README_WORKER.md).
