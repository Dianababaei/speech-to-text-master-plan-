"""
Audio file storage utilities for transcription jobs.

Handles file storage, retrieval, and automatic cleanup of audio files
with configurable retention periods.
"""

import os
import uuid
import shutil
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Base exception for storage-related errors."""
    pass


class DiskSpaceError(StorageError):
    """Raised when disk space is insufficient."""
    pass


class PermissionError(StorageError):
    """Raised when file operations fail due to permissions."""
    pass


def _get_storage_path() -> Path:
    """Get the configured audio storage path."""
    from app.config.settings import get_settings
    settings = get_settings()
    storage_path = Path(settings.AUDIO_STORAGE_PATH)
    
    # Ensure directory exists
    try:
        storage_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create storage directory {storage_path}: {e}")
        raise StorageError(f"Cannot create storage directory: {e}")
    
    return storage_path


def _get_retention_hours() -> int:
    """Get the configured audio retention hours."""
    from app.config.settings import get_settings
    settings = get_settings()
    return settings.AUDIO_RETENTION_HOURS


def check_disk_space(path: Path, required_bytes: int = 100 * 1024 * 1024) -> bool:
    """
    Check if sufficient disk space is available.
    
    Args:
        path: Path to check disk space for
        required_bytes: Minimum required bytes (default: 100MB)
    
    Returns:
        True if sufficient space available, False otherwise
    
    Raises:
        DiskSpaceError: If disk space is critically low
    """
    try:
        stat = shutil.disk_usage(path)
        available_bytes = stat.free
        
        if available_bytes < required_bytes:
            logger.warning(
                f"Low disk space: {available_bytes / (1024**3):.2f}GB available, "
                f"{required_bytes / (1024**3):.2f}GB required"
            )
            if available_bytes < (10 * 1024 * 1024):  # Less than 10MB
                raise DiskSpaceError(
                    f"Critically low disk space: {available_bytes / (1024**2):.2f}MB available"
                )
            return False
        
        return True
    except OSError as e:
        logger.error(f"Failed to check disk space: {e}")
        return True  # Don't block operation if we can't check


def save_audio_file(uploaded_file, job_id: str) -> str:
    """
    Save an uploaded audio file with a unique path.
    
    Args:
        uploaded_file: File object with read() method and filename attribute
        job_id: Job identifier
    
    Returns:
        str: Relative file path where the file was saved
    
    Raises:
        StorageError: If file saving fails
        DiskSpaceError: If insufficient disk space
    """
    try:
        storage_path = _get_storage_path()
        
        # Check disk space before saving
        check_disk_space(storage_path)
        
        # Extract file extension from original filename
        original_filename = getattr(uploaded_file, 'filename', 'audio.wav')
        file_extension = Path(original_filename).suffix or '.wav'
        
        # Generate unique filename using UUID
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = storage_path / unique_filename
        
        # Save the file
        logger.info(f"Saving audio file for job {job_id}: {file_path}")
        
        with open(file_path, 'wb') as f:
            # Handle different file object types
            if hasattr(uploaded_file, 'read'):
                content = uploaded_file.read()
            elif hasattr(uploaded_file, 'file'):
                content = uploaded_file.file.read()
            else:
                content = uploaded_file
            
            f.write(content)
        
        # Return relative path (just the filename)
        relative_path = str(unique_filename)
        logger.info(f"Successfully saved audio file: {relative_path}")
        
        return relative_path
        
    except OSError as e:
        if e.errno == 28:  # No space left on device
            logger.error(f"Disk full while saving file for job {job_id}")
            raise DiskSpaceError("Disk space exhausted")
        elif e.errno == 13:  # Permission denied
            logger.error(f"Permission denied while saving file for job {job_id}")
            raise StorageError("Permission denied for file operation")
        else:
            logger.error(f"OS error while saving file for job {job_id}: {e}")
            raise StorageError(f"File operation failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error saving file for job {job_id}: {e}")
        raise StorageError(f"Failed to save audio file: {e}")


def get_audio_file_path(job_id: str, relative_path: str) -> Path:
    """
    Get the full path to an audio file by job ID.
    
    Args:
        job_id: Job identifier
        relative_path: Relative path stored in database
    
    Returns:
        Path: Full path to the audio file
    
    Raises:
        StorageError: If file doesn't exist or path is invalid
    """
    try:
        storage_path = _get_storage_path()
        full_path = storage_path / relative_path
        
        # Validate the path is within storage directory (security check)
        try:
            full_path.resolve().relative_to(storage_path.resolve())
        except ValueError:
            logger.error(f"Path traversal attempt detected for job {job_id}: {relative_path}")
            raise StorageError("Invalid file path")
        
        if not full_path.exists():
            logger.warning(f"Audio file not found for job {job_id}: {full_path}")
            raise StorageError(f"Audio file not found: {relative_path}")
        
        return full_path
        
    except StorageError:
        raise
    except Exception as e:
        logger.error(f"Error getting file path for job {job_id}: {e}")
        raise StorageError(f"Failed to get audio file path: {e}")


def delete_audio_file(file_path: str) -> bool:
    """
    Delete an audio file with error handling.
    
    Args:
        file_path: Relative path to the file to delete
    
    Returns:
        bool: True if file was deleted, False if file didn't exist
    
    Raises:
        StorageError: If deletion fails due to permissions or other errors
    """
    try:
        storage_path = _get_storage_path()
        full_path = storage_path / file_path
        
        # Validate the path is within storage directory (security check)
        try:
            full_path.resolve().relative_to(storage_path.resolve())
        except ValueError:
            logger.error(f"Path traversal attempt detected during deletion: {file_path}")
            raise StorageError("Invalid file path")
        
        if not full_path.exists():
            logger.info(f"File already deleted or doesn't exist: {file_path}")
            return False
        
        full_path.unlink()
        logger.info(f"Successfully deleted audio file: {file_path}")
        return True
        
    except OSError as e:
        if e.errno == 13:  # Permission denied
            logger.error(f"Permission denied while deleting file {file_path}")
            raise StorageError("Permission denied for file deletion")
        else:
            logger.error(f"OS error while deleting file {file_path}: {e}")
            raise StorageError(f"Failed to delete file: {e}")
    except StorageError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting file {file_path}: {e}")
        raise StorageError(f"Failed to delete audio file: {e}")


def cleanup_old_audio_files(db_session) -> dict:
    """
    Clean up audio files for completed/failed jobs older than retention period.
    
    This function queries the database for jobs that are completed or failed
    and older than the configured retention period, then deletes their audio files.
    
    Args:
        db_session: Database session for querying jobs
    
    Returns:
        dict: Statistics about the cleanup operation
            {
                'scanned': int,
                'deleted': int,
                'failed': int,
                'errors': list
            }
    """
    from app.models import Job  # Import here to avoid circular imports
    
    retention_hours = _get_retention_hours()
    cutoff_time = datetime.utcnow() - timedelta(hours=retention_hours)
    
    logger.info(f"Starting cleanup of audio files older than {retention_hours} hours")
    
    stats = {
        'scanned': 0,
        'deleted': 0,
        'failed': 0,
        'errors': []
    }
    
    try:
        # Query jobs that are completed/failed and older than retention period
        # Assuming Job model has status and updated_at/completed_at fields
        old_jobs = db_session.query(Job).filter(
            Job.status.in_(['completed', 'failed']),
            Job.updated_at < cutoff_time,
            Job.audio_file_path.isnot(None)
        ).all()
        
        stats['scanned'] = len(old_jobs)
        logger.info(f"Found {stats['scanned']} jobs with audio files to clean up")
        
        for job in old_jobs:
            try:
                if delete_audio_file(job.audio_file_path):
                    stats['deleted'] += 1
                    # Update job record to clear the file path
                    job.audio_file_path = None
                    db_session.commit()
            except StorageError as e:
                stats['failed'] += 1
                error_msg = f"Failed to delete file for job {job.id}: {e}"
                logger.error(error_msg)
                stats['errors'].append(error_msg)
                db_session.rollback()
            except Exception as e:
                stats['failed'] += 1
                error_msg = f"Unexpected error cleaning up job {job.id}: {e}"
                logger.error(error_msg)
                stats['errors'].append(error_msg)
                db_session.rollback()
        
        logger.info(
            f"Cleanup complete: {stats['deleted']} deleted, "
            f"{stats['failed']} failed out of {stats['scanned']} scanned"
        )
        
    except Exception as e:
        error_msg = f"Error during cleanup operation: {e}"
        logger.error(error_msg)
        stats['errors'].append(error_msg)
    
    return stats


def get_storage_stats() -> dict:
    """
    Get statistics about the audio storage.
    
    Returns:
        dict: Storage statistics including disk usage and file count
    """
    try:
        storage_path = _get_storage_path()
        stat = shutil.disk_usage(storage_path)
        
        # Count audio files
        file_count = len([f for f in storage_path.iterdir() if f.is_file()])
        
        # Calculate total size of audio files
        total_size = sum(f.stat().st_size for f in storage_path.iterdir() if f.is_file())
        
        return {
            'storage_path': str(storage_path),
            'total_space_gb': stat.total / (1024**3),
            'used_space_gb': stat.used / (1024**3),
            'free_space_gb': stat.free / (1024**3),
            'file_count': file_count,
            'total_file_size_mb': total_size / (1024**2)
        }
    except Exception as e:
        logger.error(f"Error getting storage stats: {e}")
        return {
            'error': str(e)
        }
