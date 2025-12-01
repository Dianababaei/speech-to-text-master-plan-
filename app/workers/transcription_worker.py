"""
Transcription worker module for processing audio transcription jobs.

This module contains:
- Worker entry point for RQ
- Job processing function
- Error handling and retry logic
- Graceful shutdown handling
"""

import os
import sys
import signal
import logging
from typing import Optional, Dict, Any
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Track shutdown state
_shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global _shutdown_requested
    signal_name = signal.Signals(signum).name
    logger.info(f"Received signal {signal_name}, initiating graceful shutdown...")
    _shutdown_requested = True


# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


def process_transcription_job(
    job_id: str,
    audio_file_path: str,
    lexicon_id: Optional[str] = None,
    api_key_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Process a transcription job.
    
    This is the main worker function that will be called by RQ workers.
    It processes the audio file and updates the job status in the database.
    
    Args:
        job_id: Unique identifier for the job
        audio_file_path: Path to the audio file to transcribe
        lexicon_id: Optional ID of the lexicon to use
        api_key_id: Optional API key identifier for OpenAI
    
    Returns:
        Dict containing the transcription results
    
    Raises:
        Exception: If job processing fails
    """
    logger.info(f"Starting transcription job {job_id}")
    logger.info(f"Audio file: {audio_file_path}")
    logger.info(f"Lexicon ID: {lexicon_id}")
    logger.info(f"API Key ID: {api_key_id}")
    
    try:
        # Check if shutdown was requested
        if _shutdown_requested:
            logger.warning(f"Job {job_id} cancelled due to shutdown request")
            raise Exception("Worker shutdown requested")
        
        # Validate audio file exists
        audio_path = Path(audio_file_path)
        if not audio_path.exists():
            error_msg = f"Audio file not found: {audio_file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        logger.info(f"Audio file validated: {audio_path.name} ({audio_path.stat().st_size} bytes)")
        
        # TODO: Update job status to 'processing' in database
        # This will be implemented when database integration is added
        # Example:
        # update_job_status(job_id, "processing", {"started_at": datetime.utcnow()})
        
        # TODO: Load lexicon if provided
        # This will be implemented when lexicon service is added
        # Example:
        # lexicon = load_lexicon(lexicon_id) if lexicon_id else None
        
        # TODO: Call OpenAI Whisper API for transcription
        # This will be implemented in the next task
        # Example:
        # transcription_result = transcribe_audio(
        #     audio_file_path=audio_file_path,
        #     lexicon=lexicon,
        #     api_key_id=api_key_id
        # )
        
        # Placeholder result for now
        result = {
            "job_id": job_id,
            "status": "completed",
            "transcription": "Placeholder transcription text",
            "audio_file": audio_file_path,
            "lexicon_id": lexicon_id,
            "processing_time": 0.0,
            "word_count": 0,
        }
        
        # TODO: Update job status to 'completed' in database
        # This will be implemented when database integration is added
        # Example:
        # update_job_status(job_id, "completed", {
        #     "completed_at": datetime.utcnow(),
        #     "result": result
        # })
        
        logger.info(f"Job {job_id} completed successfully")
        return result
        
    except FileNotFoundError as e:
        logger.error(f"Job {job_id} failed: {str(e)}")
        # TODO: Update job status to 'failed' in database
        raise
        
    except Exception as e:
        logger.error(f"Job {job_id} failed with error: {str(e)}", exc_info=True)
        # TODO: Update job status to 'failed' in database
        raise


def start_worker():
    """
    Start the RQ worker process.
    
    This is the main entry point for starting worker processes.
    It can be called from the command line or Docker.
    """
    from redis import Redis
    from rq import Worker
    from app.services.queue import REDIS_URL, QUEUE_NAME
    
    logger.info("=" * 80)
    logger.info("Starting Transcription Worker")
    logger.info("=" * 80)
    logger.info(f"Redis URL: {REDIS_URL}")
    logger.info(f"Queue Name: {QUEUE_NAME}")
    logger.info(f"Worker PID: {os.getpid()}")
    
    # Connect to Redis
    redis_conn = Redis.from_url(
        REDIS_URL,
        decode_responses=True,
        socket_keepalive=True,
        socket_connect_timeout=5
    )
    
    # Test connection
    try:
        redis_conn.ping()
        logger.info("Successfully connected to Redis")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        sys.exit(1)
    
    # Create worker
    worker = Worker(
        [QUEUE_NAME],
        connection=redis_conn,
        name=f"worker-{os.getpid()}",
        log_job_description=True,
    )
    
    logger.info(f"Worker '{worker.name}' ready to process jobs from queue '{QUEUE_NAME}'")
    logger.info("Press Ctrl+C to stop the worker")
    logger.info("=" * 80)
    
    try:
        # Start working
        worker.work(with_scheduler=True)
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:
        logger.error(f"Worker error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Worker shutdown complete")


if __name__ == "__main__":
    start_worker()
