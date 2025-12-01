"""
Queue service module for managing transcription jobs using Redis and RQ.

This module provides functions to:
- Initialize Redis connection
- Enqueue transcription jobs
- Get job status
- Manage job lifecycle
"""

import os
import logging
from typing import Optional, Dict, Any
from redis import Redis
from rq import Queue
from rq.job import Job

logger = logging.getLogger(__name__)

# Configuration from environment variables
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_NAME = os.getenv("QUEUE_NAME", "transcription_jobs")
DEFAULT_JOB_TIMEOUT = int(os.getenv("JOB_TIMEOUT", "300"))  # 5 minutes default

# Global Redis connection and queue instances
_redis_connection: Optional[Redis] = None
_transcription_queue: Optional[Queue] = None


def get_redis_connection() -> Redis:
    """
    Get or create Redis connection.
    
    Returns:
        Redis: Redis connection instance
    """
    global _redis_connection
    
    if _redis_connection is None:
        logger.info(f"Connecting to Redis at {REDIS_URL}")
        _redis_connection = Redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_keepalive=True,
            socket_connect_timeout=5,
            health_check_interval=30
        )
        # Test connection
        _redis_connection.ping()
        logger.info("Successfully connected to Redis")
    
    return _redis_connection


def get_queue() -> Queue:
    """
    Get or create RQ Queue instance.
    
    Returns:
        Queue: RQ Queue instance for transcription jobs
    """
    global _transcription_queue
    
    if _transcription_queue is None:
        redis_conn = get_redis_connection()
        _transcription_queue = Queue(
            name=QUEUE_NAME,
            connection=redis_conn,
            default_timeout=DEFAULT_JOB_TIMEOUT
        )
        logger.info(f"Queue '{QUEUE_NAME}' initialized")
    
    return _transcription_queue


def enqueue_transcription_job(
    job_id: str,
    audio_file_path: str,
    lexicon_id: Optional[str] = None,
    api_key_id: Optional[str] = None,
    priority: str = "normal",
    timeout: Optional[int] = None,
    retry_count: int = 3,
    retry_delay: int = 60
) -> Job:
    """
    Enqueue a transcription job to be processed asynchronously.
    
    Args:
        job_id: Unique identifier for the job
        audio_file_path: Path to the audio file to transcribe
        lexicon_id: Optional ID of the lexicon to use
        api_key_id: Optional API key identifier for OpenAI
        priority: Job priority ('low', 'normal', 'high')
        timeout: Job timeout in seconds (uses default if not specified)
        retry_count: Number of times to retry failed jobs
        retry_delay: Delay between retries in seconds
    
    Returns:
        Job: RQ Job instance
    """
    queue = get_queue()
    
    # Prepare job metadata
    job_data = {
        "job_id": job_id,
        "audio_file_path": audio_file_path,
        "lexicon_id": lexicon_id,
        "api_key_id": api_key_id,
    }
    
    # Set timeout
    job_timeout = timeout or DEFAULT_JOB_TIMEOUT
    
    logger.info(f"Enqueuing transcription job: {job_id} with priority: {priority}")
    
    try:
        # Import worker function here to avoid circular imports
        from app.workers.transcription_worker import process_transcription_job
        
        # Enqueue the job
        job = queue.enqueue(
            process_transcription_job,
            kwargs=job_data,
            job_id=job_id,
            timeout=job_timeout,
            result_ttl=86400,  # Keep results for 24 hours
            failure_ttl=86400,  # Keep failed job info for 24 hours
            retry=retry_count if retry_count > 0 else None,
            meta={
                "priority": priority,
                "retry_count": retry_count,
                "retry_delay": retry_delay,
            }
        )
        
        logger.info(f"Job {job_id} enqueued successfully with ID: {job.id}")
        return job
        
    except Exception as e:
        logger.error(f"Failed to enqueue job {job_id}: {str(e)}")
        raise


def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the current status of a job.
    
    Args:
        job_id: Unique identifier for the job
    
    Returns:
        Dict containing job status information, or None if job not found
    """
    try:
        redis_conn = get_redis_connection()
        job = Job.fetch(job_id, connection=redis_conn)
        
        status_info = {
            "job_id": job.id,
            "status": job.get_status(),
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "ended_at": job.ended_at.isoformat() if job.ended_at else None,
            "result": job.result if job.is_finished else None,
            "exc_info": job.exc_info if job.is_failed else None,
            "meta": job.meta,
        }
        
        return status_info
        
    except Exception as e:
        logger.error(f"Failed to get job status for {job_id}: {str(e)}")
        return None


def cancel_job(job_id: str) -> bool:
    """
    Cancel a pending or running job.
    
    Args:
        job_id: Unique identifier for the job
    
    Returns:
        bool: True if job was cancelled, False otherwise
    """
    try:
        redis_conn = get_redis_connection()
        job = Job.fetch(job_id, connection=redis_conn)
        
        if job.get_status() in ["queued", "started"]:
            job.cancel()
            logger.info(f"Job {job_id} cancelled successfully")
            return True
        else:
            logger.warning(f"Job {job_id} cannot be cancelled (status: {job.get_status()})")
            return False
            
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {str(e)}")
        return False


def cleanup_old_jobs(days: int = 7) -> int:
    """
    Clean up old finished and failed jobs from Redis.
    
    Args:
        days: Number of days to keep jobs
    
    Returns:
        int: Number of jobs cleaned up
    """
    try:
        queue = get_queue()
        registry_finished = queue.finished_job_registry
        registry_failed = queue.failed_job_registry
        
        # Clean up finished jobs
        finished_job_ids = registry_finished.get_job_ids()
        failed_job_ids = registry_failed.get_job_ids()
        
        count = 0
        for job_id in finished_job_ids + failed_job_ids:
            job = Job.fetch(job_id, connection=get_redis_connection())
            if job.ended_at and (job.ended_at.timestamp() < (days * 86400)):
                job.delete()
                count += 1
        
        logger.info(f"Cleaned up {count} old jobs")
        return count
        
    except Exception as e:
        logger.error(f"Failed to cleanup old jobs: {str(e)}")
        return 0


def get_queue_stats() -> Dict[str, Any]:
    """
    Get statistics about the queue.
    
    Returns:
        Dict containing queue statistics
    """
    try:
        queue = get_queue()
        
        stats = {
            "queue_name": queue.name,
            "queued_count": len(queue),
            "started_count": queue.started_job_registry.count,
            "finished_count": queue.finished_job_registry.count,
            "failed_count": queue.failed_job_registry.count,
            "deferred_count": queue.deferred_job_registry.count,
            "scheduled_count": queue.scheduled_job_registry.count,
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get queue stats: {str(e)}")
        return {}
