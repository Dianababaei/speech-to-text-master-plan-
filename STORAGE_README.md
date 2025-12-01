# Audio File Storage and Cleanup Implementation

This document describes the audio file storage utilities and automatic cleanup mechanisms for the transcription service.

## Overview

The storage system provides:
- **Secure file storage** with UUID-based unique filenames
- **Automatic cleanup** of old audio files after a configurable retention period
- **Disk space monitoring** with warnings and error handling
- **Docker volume persistence** across container restarts

## Architecture

### Storage Structure

```
/app/audio_storage/
├── <uuid1>.wav
├── <uuid2>.mp3
├── <uuid3>.m4a
└── ...
```

Files are stored with UUID-based names to prevent collisions and enhance security.

## Core Components

### 1. Storage Service (`app/services/storage.py`)

#### Functions

**`save_audio_file(uploaded_file, job_id) -> str`**
- Saves uploaded audio file with unique UUID filename
- Checks disk space before saving
- Returns relative path to stored file
- Handles various file object types (FastAPI UploadFile, file-like objects)

**`get_audio_file_path(job_id, relative_path) -> Path`**
- Retrieves full path to audio file
- Includes security check to prevent path traversal
- Validates file exists

**`delete_audio_file(file_path) -> bool`**
- Deletes audio file with error handling
- Returns True if deleted, False if file didn't exist
- Includes path traversal protection

**`cleanup_old_audio_files(db_session) -> dict`**
- Queries database for completed/failed jobs older than retention period
- Deletes associated audio files
- Returns statistics: scanned, deleted, failed, errors

**`check_disk_space(path, required_bytes) -> bool`**
- Checks available disk space
- Logs warnings if space is low
- Raises DiskSpaceError if critically low (<10MB)

**`get_storage_stats() -> dict`**
- Returns storage statistics (disk usage, file count, total size)

### 2. Configuration (`app/config/settings.py`)

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `AUDIO_STORAGE_PATH` | `/app/audio_storage` | Directory for audio file storage |
| `AUDIO_RETENTION_HOURS` | `24` | Hours to retain audio files after job completion |
| `CLEANUP_INTERVAL_MINUTES` | `60` | Minutes between automatic cleanup runs |

### 3. Background Cleanup Task (`app/main.py`)

- Runs automatically every `CLEANUP_INTERVAL_MINUTES`
- Can be triggered manually via `/admin/cleanup` endpoint
- Uses FastAPI lifespan context manager
- Gracefully handles errors without stopping the service

### 4. Docker Configuration (`docker-compose.yml`)

Volume mount ensures persistence:

```yaml
volumes:
  - audio_storage:/app/audio_storage
```

The volume persists audio files across container restarts during the retention period.

## Usage Examples

### Saving an Audio File

```python
from app.services.storage import save_audio_file

# With FastAPI UploadFile
file_path = save_audio_file(upload_file, job_id="job123")
# Returns: "a1b2c3d4-e5f6-7890-abcd-ef1234567890.wav"

# Store path in database
job.audio_file_path = file_path
db.commit()
```

### Retrieving an Audio File

```python
from app.services.storage import get_audio_file_path

# Get full path to file
full_path = get_audio_file_path(job_id="job123", relative_path=job.audio_file_path)

# Use the file
with open(full_path, 'rb') as f:
    audio_data = f.read()
```

### Deleting an Audio File

```python
from app.services.storage import delete_audio_file

# Delete a file
success = delete_audio_file(job.audio_file_path)
if success:
    job.audio_file_path = None
    db.commit()
```

### Manual Cleanup

```bash
# Trigger cleanup via API
curl -X POST http://localhost:8000/admin/cleanup

# Returns:
{
  "status": "success",
  "message": "Cleanup completed",
  "stats": {
    "scanned": 10,
    "deleted": 8,
    "failed": 0,
    "errors": []
  }
}
```

### Get Storage Statistics

```bash
# Check storage stats
curl http://localhost:8000/storage/stats

# Returns:
{
  "storage_path": "/app/audio_storage",
  "total_space_gb": 100.0,
  "used_space_gb": 45.2,
  "free_space_gb": 54.8,
  "file_count": 42,
  "total_file_size_mb": 1250.5
}
```

## Error Handling

### Exception Types

- **`StorageError`**: Base exception for storage operations
- **`DiskSpaceError`**: Raised when disk space is insufficient
- **`PermissionError`**: Raised for permission-related errors

### Handled Scenarios

1. **Disk Full**: Raises `DiskSpaceError` with clear message
2. **Permission Denied**: Raises `StorageError` indicating permission issue
3. **File Not Found**: Returns False or raises StorageError with details
4. **Path Traversal**: Validates paths to prevent security issues
5. **Invalid File Objects**: Handles various file object types gracefully

## Security Features

1. **UUID Filenames**: Prevents guessing file paths
2. **Path Traversal Protection**: Validates all paths stay within storage directory
3. **Permission Checks**: Proper error handling for permission issues
4. **Isolated Storage**: Files stored in dedicated volume

## Testing

### Manual Testing

```bash
# Start services
docker-compose up -d

# Check storage is mounted
docker-compose exec web ls -la /app/audio_storage

# Test manual cleanup
curl -X POST http://localhost:8000/admin/cleanup

# Check storage stats
curl http://localhost:8000/storage/stats
```

### Cleanup Testing

To test the cleanup function:

1. Create some test jobs with old timestamps
2. Add audio files to storage
3. Run manual cleanup via API
4. Verify files are deleted and job records updated

## Monitoring

### Logs

The storage system logs:
- File save operations
- Cleanup operations with statistics
- Disk space warnings
- All errors with details

Example log output:

```
2024-01-15 10:30:00 - app.services.storage - INFO - Saving audio file for job job123: /app/audio_storage/uuid.wav
2024-01-15 11:00:00 - app.main - INFO - Running scheduled audio file cleanup
2024-01-15 11:00:05 - app.services.storage - INFO - Found 5 jobs with audio files to clean up
2024-01-15 11:00:06 - app.services.storage - INFO - Cleanup complete: 5 deleted, 0 failed out of 5 scanned
```

### Metrics to Monitor

- Disk space usage (via `/storage/stats`)
- Cleanup success rate
- File count over time
- Failed cleanup operations

## Deployment Considerations

### Production Settings

```env
AUDIO_STORAGE_PATH=/app/audio_storage
AUDIO_RETENTION_HOURS=24
CLEANUP_INTERVAL_MINUTES=60
LOG_LEVEL=INFO
```

### Volume Backup

The Docker volume `audio_storage` can be backed up:

```bash
# Backup
docker run --rm -v audio_storage:/data -v $(pwd):/backup alpine tar czf /backup/audio_storage.tar.gz /data

# Restore
docker run --rm -v audio_storage:/data -v $(pwd):/backup alpine tar xzf /backup/audio_storage.tar.gz -C /
```

### Scaling Considerations

For high-volume deployments:
1. Consider cloud storage (S3, GCS) instead of local filesystem
2. Implement distributed cleanup coordination
3. Monitor disk I/O and adjust retention period
4. Use separate volumes for each service instance

## Integration with Worker

The worker process uses the same storage utilities:

```python
from app.services.storage import get_audio_file_path

# In worker job processing
file_path = get_audio_file_path(job.id, job.audio_file_path)

# Process the file
with open(file_path, 'rb') as f:
    # Send to transcription API
    result = transcribe_audio(f)
```

## Troubleshooting

### Issue: Files not being deleted

**Check:**
1. Retention period configuration
2. Job status is 'completed' or 'failed'
3. Job `updated_at` timestamp
4. Cleanup task is running (check logs)

### Issue: Disk space errors

**Solutions:**
1. Reduce retention period
2. Increase volume size
3. Monitor cleanup frequency
4. Check for failed cleanup operations

### Issue: Permission errors

**Check:**
1. Container user has write permissions
2. Volume mount permissions
3. SELinux/AppArmor policies (if applicable)

## Future Enhancements

Potential improvements:
- Cloud storage integration (S3, GCS, Azure Blob)
- Compression of old files before deletion
- Archival to cheaper storage tier
- More granular cleanup policies (by file size, age, etc.)
- Metrics export to Prometheus
- Admin dashboard for storage management
