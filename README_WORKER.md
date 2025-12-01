# Transcription Worker Documentation

This document provides comprehensive information about the Redis queue and worker architecture for the speech-to-text transcription service.

## Overview

The transcription service uses **RQ (Redis Queue)** for asynchronous job processing. This architecture separates the API request/response cycle from the time-consuming transcription tasks, allowing for:

- Non-blocking API responses
- Horizontal scaling of worker processes
- Job retry and failure handling
- Queue monitoring and management

## Architecture Components

### 1. Redis Server
- **Purpose**: Message broker and job queue storage
- **Configuration**: `REDIS_URL` environment variable
- **Default**: `redis://localhost:6379/0`

### 2. Queue Service (`app/services/queue.py`)
- Manages Redis connections
- Provides job enqueuing functions
- Tracks job status and lifecycle
- Handles job cancellation and cleanup

### 3. Worker Process (`app/workers/transcription_worker.py`)
- Processes transcription jobs from the queue
- Handles job failures and retries
- Updates job status in database
- Supports graceful shutdown

## Getting Started

### Prerequisites

1. **Redis Server**: Ensure Redis is installed and running
   ```bash
   # Using Docker
   docker run -d -p 6379:6379 redis:7-alpine
   
   # Or install locally (macOS)
   brew install redis
   redis-server
   
   # Or install locally (Ubuntu/Debian)
   sudo apt-get install redis-server
   sudo systemctl start redis
   ```

2. **Python Dependencies**: Install required packages
   ```bash
   pip install -r requirements.txt
   # or
   pip install -e .
   ```

### Configuration

1. **Copy environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Configure environment variables** in `.env`:
   ```env
   REDIS_URL=redis://localhost:6379/0
   QUEUE_NAME=transcription_jobs
   JOB_TIMEOUT=300
   WORKER_COUNT=2
   ```

## Running Workers

### Method 1: Direct Python Execution

Run a single worker process:

```bash
python -m app.workers.transcription_worker
```

Or using the RQ CLI:

```bash
rq worker transcription_jobs --url redis://localhost:6379/0
```

### Method 2: Docker Compose (Recommended)

Start all services (Redis + Workers):

```bash
docker-compose up -d
```

Scale workers:

```bash
docker-compose up -d --scale worker=4
```

View worker logs:

```bash
docker-compose logs -f worker
```

Stop services:

```bash
docker-compose down
```

### Method 3: Production Deployment

Use a process manager like **systemd** or **supervisor**:

#### Using systemd

Create `/etc/systemd/system/transcription-worker@.service`:

```ini
[Unit]
Description=Transcription Worker %i
After=network.target redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/app
Environment="REDIS_URL=redis://localhost:6379/0"
ExecStart=/path/to/venv/bin/python -m app.workers.transcription_worker
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start multiple workers:

```bash
sudo systemctl enable transcription-worker@{1..4}.service
sudo systemctl start transcription-worker@{1..4}.service
```

## Queue Management

### Enqueueing Jobs

From your application code:

```python
from app.services.queue import enqueue_transcription_job

# Enqueue a transcription job
job = enqueue_transcription_job(
    job_id="unique-job-id-123",
    audio_file_path="/path/to/audio.mp3",
    lexicon_id="medical-terms-v1",
    api_key_id="openai-key-1",
    priority="high",
    timeout=600,
    retry_count=3
)

print(f"Job enqueued: {job.id}")
```

### Checking Job Status

```python
from app.services.queue import get_job_status

status = get_job_status("unique-job-id-123")
print(status)
# Output:
# {
#     "job_id": "unique-job-id-123",
#     "status": "started",
#     "created_at": "2024-01-15T10:30:00",
#     "started_at": "2024-01-15T10:30:05",
#     "ended_at": None,
#     "result": None,
#     "exc_info": None,
#     "meta": {"priority": "high"}
# }
```

### Queue Statistics

```python
from app.services.queue import get_queue_stats

stats = get_queue_stats()
print(stats)
# Output:
# {
#     "queue_name": "transcription_jobs",
#     "queued_count": 5,
#     "started_count": 2,
#     "finished_count": 100,
#     "failed_count": 3,
#     "deferred_count": 0,
#     "scheduled_count": 0
# }
```

### Cancelling Jobs

```python
from app.services.queue import cancel_job

success = cancel_job("unique-job-id-123")
if success:
    print("Job cancelled successfully")
```

## Monitoring and Debugging

### RQ Dashboard (Optional)

Install and run the RQ dashboard for web-based monitoring:

```bash
pip install rq-dashboard
rq-dashboard --redis-url redis://localhost:6379/0
```

Access at: http://localhost:9181

### Command Line Monitoring

Check queue info:

```bash
rq info --url redis://localhost:6379/0
```

View failed jobs:

```bash
rq info --url redis://localhost:6379/0 --only-failures
```

Requeue failed jobs:

```bash
rq requeue --all --url redis://localhost:6379/0
```

Empty queue:

```bash
rq empty transcription_jobs --url redis://localhost:6379/0
```

### Worker Logs

Workers log important events including:
- Job start/completion
- Errors and exceptions
- Shutdown signals

View logs:

```bash
# Docker Compose
docker-compose logs -f worker

# Systemd
sudo journalctl -u transcription-worker@1.service -f
```

## Job Configuration

### Timeouts

Configure job timeout to prevent hanging jobs:

```python
# Default timeout (from environment)
job = enqueue_transcription_job(...)

# Custom timeout
job = enqueue_transcription_job(..., timeout=600)  # 10 minutes
```

### Retries

Failed jobs can be automatically retried:

```python
job = enqueue_transcription_job(
    ...,
    retry_count=3,      # Retry up to 3 times
    retry_delay=60      # Wait 60 seconds between retries
)
```

### Priority Queues

Use separate queues for different priorities:

```python
# High priority queue
job = enqueue_transcription_job(..., priority="high")

# Start worker for high-priority queue
# python -m app.workers.transcription_worker --queue transcription_jobs_high
```

## Scaling Workers

### Horizontal Scaling

Add more worker processes to handle increased load:

```bash
# Docker Compose
docker-compose up -d --scale worker=10

# Systemd
sudo systemctl start transcription-worker@{5..10}.service
```

### Vertical Scaling

Adjust worker resources in `docker-compose.yml`:

```yaml
worker:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 4G
      reservations:
        cpus: '1.0'
        memory: 2G
```

## Graceful Shutdown

Workers handle SIGTERM and SIGINT signals gracefully:

```bash
# Send shutdown signal
docker-compose stop worker

# Or kill specific worker
kill -TERM <worker-pid>
```

The worker will:
1. Stop accepting new jobs
2. Complete current job (if any)
3. Clean up resources
4. Exit cleanly

## Troubleshooting

### Worker Not Connecting to Redis

**Check Redis connectivity:**
```bash
redis-cli -u redis://localhost:6379/0 ping
```

**Verify REDIS_URL:**
```bash
echo $REDIS_URL
```

### Jobs Not Being Processed

**Check worker status:**
```bash
docker-compose ps worker
```

**Verify queue has jobs:**
```bash
rq info --url redis://localhost:6379/0
```

**Check worker logs:**
```bash
docker-compose logs worker
```

### Jobs Failing

**View failed job details:**
```bash
rq info --url redis://localhost:6379/0 --only-failures
```

**Retry failed jobs:**
```bash
rq requeue --all --url redis://localhost:6379/0
```

### High Memory Usage

**Monitor worker memory:**
```bash
docker stats transcription-worker
```

**Reduce worker count or increase memory limits**

## Best Practices

1. **Use unique job IDs**: Prevent duplicate job processing
2. **Set appropriate timeouts**: Match timeout to expected job duration
3. **Monitor queue depth**: Alert when queue grows too large
4. **Log comprehensively**: Include job_id in all log messages
5. **Test retry logic**: Ensure failed jobs can recover
6. **Clean up old jobs**: Run periodic cleanup to prevent Redis bloat
7. **Use health checks**: Monitor worker process health
8. **Set resource limits**: Prevent workers from consuming too many resources

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `QUEUE_NAME` | `transcription_jobs` | Name of the job queue |
| `JOB_TIMEOUT` | `300` | Default job timeout in seconds |
| `WORKER_COUNT` | `2` | Number of worker processes |
| `LOG_LEVEL` | `INFO` | Logging level |

## Additional Resources

- [RQ Documentation](https://python-rq.org/)
- [Redis Documentation](https://redis.io/docs/)
- [RQ Dashboard](https://github.com/Parallels/rq-dashboard)

## Support

For issues or questions, check:
1. Worker logs for error details
2. Redis connectivity and memory usage
3. Queue statistics and failed job information
