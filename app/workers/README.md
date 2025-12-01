# Transcription Worker

This module contains the worker implementation for processing transcription jobs asynchronously.

## Overview

The worker orchestrates the complete transcription workflow:

1. **Fetch Job** - Load job metadata from database
2. **Update Status** - Mark job as 'processing' with timestamp
3. **Load Audio** - Validate and load audio file from temporary storage
4. **Transcribe** - Call OpenAI Whisper API for transcription
5. **Store Original** - Save raw transcription as `original_text`
6. **Post-Process** - Apply lexicon-based corrections and cleanup
7. **Store Processed** - Save final transcription as `processed_text`
8. **Complete** - Mark job as 'completed' with timestamp
9. **Cleanup** - Delete temporary audio file

## Worker Function

### `process_transcription_job(job_id: str)`

Main entry point for processing a transcription job.

**Parameters:**
- `job_id` (str): The ID of the job to process

**Behavior:**
- Processes job through complete transcription workflow
- Updates job status at each step
- Logs all operations with structured context
- Handles errors gracefully with appropriate status updates
- Always cleans up temporary files (success or failure)

## Error Handling

The worker implements comprehensive error handling:

### Database Errors
- **Action**: Log error, mark job as failed, don't retry
- **Status**: Job marked as 'failed' with error message
- **Cleanup**: Audio file deleted if possible

### File Not Found
- **Action**: Log error, mark job as failed, don't retry
- **Status**: Job marked as 'failed' with error message
- **Cleanup**: Audio file deletion skipped (doesn't exist)

### OpenAI API Errors
- **Quota Exceeded**: Log with details, mark as failed, can be retried externally
- **API Error**: Log with details, mark as failed, don't retry
- **Authentication**: Log error, mark as failed, don't retry
- **Status**: Job marked as 'failed' with detailed error message
- **Cleanup**: Audio file deleted

### Post-Processing Errors
- **Action**: Log warning, still mark job as completed
- **Status**: Job marked as 'completed' (original_text is valid)
- **Result**: Only `original_text` is stored, `processed_text` is NULL
- **Cleanup**: Audio file deleted

### Unexpected Exceptions
- **Action**: Log full traceback, mark job as failed
- **Status**: Job marked as 'failed' with full error details
- **Cleanup**: Audio file deleted

## Usage

### With Redis Queue (RQ)

```python
from redis import Redis
from rq import Queue
from app.workers.transcription_worker import process_transcription_job

# Setup Redis connection
redis_conn = Redis(host='localhost', port=6379, db=0)
queue = Queue('transcription', connection=redis_conn)

# Enqueue a job
job = queue.enqueue(process_transcription_job, job_id='abc-123-def-456')
```

### With RQ Worker

Start a worker process:

```bash
rq worker transcription --url redis://localhost:6379/0
```

### Direct Invocation (for testing)

```python
from app.workers.transcription_worker import process_transcription_job

# Process job directly (blocking)
process_transcription_job('abc-123-def-456')
```

## Logging

All operations are logged with structured context including:

- `job_id`: Job identifier
- `status`: Current job status
- `duration`: Operation duration in seconds
- `error_type`: Type of error if applicable
- `file_path`: Audio file path

Example log output (JSON format):

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "app.workers.transcription_worker",
  "message": "Job completed successfully",
  "job_id": "abc-123-def-456",
  "status": "completed",
  "duration": 12.45
}
```

## Job Status Flow

```
pending → processing → completed
                    → failed
```

- **pending**: Initial state when job is created
- **processing**: Worker has picked up job and is actively processing
- **completed**: Job finished successfully (with or without post-processing)
- **failed**: Job failed at any step (error details in error_message)

## Dependencies

### External Services
- **OpenAI Whisper API**: For audio transcription
- **Redis**: For job queue
- **Database**: For job metadata storage

### Internal Modules
- `app.services.openai_service`: OpenAI API integration
- `app.services.postprocessing_service`: Post-processing pipeline
- `app.services.job_service`: Job status management
- `app.utils.logging`: Structured logging
- `app.utils.database`: Database session management

## Configuration

Configuration is managed through environment variables:

- `DATABASE_URL`: Database connection string
- `REDIS_URL`: Redis connection string
- `TEMP_AUDIO_DIR`: Directory for temporary audio files
- `OPENAI_API_KEY`: OpenAI API key
- `OPENAI_MODEL`: OpenAI model to use (default: whisper-1)
- `LOG_LEVEL`: Logging level (default: INFO)
- `LOG_FORMAT`: Log format - 'json' or 'text' (default: json)

## Testing

Example test setup:

```python
import pytest
from unittest.mock import patch, MagicMock
from app.workers.transcription_worker import process_transcription_job

@patch('app.workers.transcription_worker.transcribe_audio')
@patch('app.workers.transcription_worker.get_job')
@patch('app.workers.transcription_worker.update_job_status')
def test_successful_transcription(mock_update, mock_get_job, mock_transcribe):
    # Setup mocks
    mock_job = MagicMock()
    mock_job.id = 'test-job-id'
    mock_job.audio_file_path = '/tmp/test.mp3'
    mock_job.lexicon_id = 'lexicon-1'
    mock_get_job.return_value = mock_job
    mock_transcribe.return_value = "Transcribed text"
    
    # Process job
    process_transcription_job('test-job-id')
    
    # Verify status updates
    assert mock_update.call_count >= 2  # processing and completed
    mock_transcribe.assert_called_once()
```

## Performance Considerations

- **Timeout**: Set appropriate timeout for RQ jobs (recommended: 600s for typical audio files)
- **Concurrency**: Multiple workers can run in parallel
- **Memory**: Each worker holds audio file in memory during processing
- **Retry**: Failed jobs with quota errors can be retried externally

## Future Enhancements

- Implement automatic retry logic for transient failures
- Add progress tracking for long audio files
- Implement streaming transcription for real-time processing
- Add support for batch processing multiple files
- Implement job prioritization
