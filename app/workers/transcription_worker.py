"""
Worker for processing transcription jobs.

This module contains the main worker function that orchestrates the complete
transcription workflow from job pickup to result storage.
"""
import os
import traceback
from pathlib import Path
from time import time
from typing import Optional

from app.models.job import Job
from app.services.job_service import (
    get_job,
    update_job_status,
    JobNotFoundError,
    JobServiceError,
)
from app.services.openai_service import (
    transcribe_audio,
    OpenAIServiceError,
    OpenAIQuotaError,
    OpenAIAPIError,
)
from app.services.postprocessing_service import (
    create_pipeline,
    PostProcessingError,
)
from app.utils.database import db_session_context
from app.utils.logging import get_logger, log_with_context
from app.config import TEMP_AUDIO_DIR

logger = get_logger(__name__)


def cleanup_audio_file(file_path: str, job_id: str) -> None:
    """
    Clean up temporary audio file with error handling.
    
    Args:
        file_path: Path to audio file to delete
        job_id: Job ID for logging context
    """
    if not file_path:
        return
    
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            log_with_context(
                logger,
                logger.INFO,
                f"Audio file cleaned up successfully",
                job_id=job_id,
                file_path=file_path
            )
        else:
            log_with_context(
                logger,
                logger.WARNING,
                f"Audio file not found for cleanup (may have been deleted already)",
                job_id=job_id,
                file_path=file_path
            )
    except Exception as e:
        log_with_context(
            logger,
            logger.ERROR,
            f"Error cleaning up audio file: {str(e)}",
            job_id=job_id,
            file_path=file_path,
            error_type=type(e).__name__
        )


def load_audio_file(file_path: str, job_id: str) -> Path:
    """
    Load and validate audio file.
    
    Args:
        file_path: Path to audio file
        job_id: Job ID for logging context
    
    Returns:
        Path object for the audio file
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is not readable or invalid format
    """
    path = Path(file_path)
    
    # Check if file exists
    if not path.exists():
        log_with_context(
            logger,
            logger.ERROR,
            f"Audio file not found",
            job_id=job_id,
            file_path=file_path
        )
        raise FileNotFoundError(f"Audio file not found: {file_path}")
    
    # Check if file is readable
    if not os.access(path, os.R_OK):
        log_with_context(
            logger,
            logger.ERROR,
            f"Audio file is not readable",
            job_id=job_id,
            file_path=file_path
        )
        raise ValueError(f"Audio file is not readable: {file_path}")
    
    # Check file extension (basic format validation)
    valid_extensions = {".wav", ".mp3", ".m4a", ".mp4", ".mpeg", ".mpga", ".webm"}
    if path.suffix.lower() not in valid_extensions:
        log_with_context(
            logger,
            logger.WARNING,
            f"Audio file has unexpected extension: {path.suffix}",
            job_id=job_id,
            file_path=file_path
        )
    
    log_with_context(
        logger,
        logger.INFO,
        f"Audio file loaded and validated",
        job_id=job_id,
        file_path=file_path
    )
    
    return path


def process_transcription_job(job_id: str) -> None:
    """
    Main worker function to process a transcription job.
    
    This function orchestrates the complete transcription workflow:
    1. Fetch job from database
    2. Update job status to 'processing'
    3. Load audio file from temporary storage
    4. Call OpenAI service for transcription
    5. Store original_text
    6. Trigger post-processing pipeline
    7. Store processed_text
    8. Update job status to 'completed'
    9. Clean up temporary audio file
    
    On error:
    - Update status to 'failed'
    - Store error_message
    - Clean up audio file
    
    Args:
        job_id: The ID of the job to process
    """
    start_time = time()
    audio_file_path = None
    
    log_with_context(
        logger,
        logger.INFO,
        f"Starting transcription job processing",
        job_id=job_id
    )
    
    try:
        # Step 1: Fetch job from database
        with db_session_context() as session:
            try:
                job = get_job(job_id, session=session)
                audio_file_path = job.audio_file_path
                lexicon_id = job.lexicon_id
                
                log_with_context(
                    logger,
                    logger.INFO,
                    f"Job loaded from database",
                    job_id=job_id,
                    status=job.status,
                    file_path=audio_file_path
                )
            
            except JobNotFoundError as e:
                log_with_context(
                    logger,
                    logger.ERROR,
                    f"Job not found in database: {str(e)}",
                    job_id=job_id,
                    error_type="JobNotFoundError"
                )
                # Can't update status if job doesn't exist
                return
            
            except JobServiceError as e:
                log_with_context(
                    logger,
                    logger.ERROR,
                    f"Database error loading job: {str(e)}",
                    job_id=job_id,
                    error_type="JobServiceError"
                )
                # Can't proceed if database is failing
                return
        
        # Step 2: Update job status to 'processing'
        try:
            with db_session_context() as session:
                update_job_status(job_id, "processing", session=session)
            
            log_with_context(
                logger,
                logger.INFO,
                f"Job status updated to processing",
                job_id=job_id,
                status="processing"
            )
        
        except (JobServiceError, JobNotFoundError) as e:
            log_with_context(
                logger,
                logger.ERROR,
                f"Failed to update job status to processing: {str(e)}",
                job_id=job_id,
                error_type=type(e).__name__
            )
            # Continue anyway - we'll try to mark as failed at the end
        
        # Step 3: Load audio file
        try:
            audio_path = load_audio_file(audio_file_path, job_id)
        
        except FileNotFoundError as e:
            error_msg = f"Audio file not found: {str(e)}"
            log_with_context(
                logger,
                logger.ERROR,
                error_msg,
                job_id=job_id,
                error_type="FileNotFoundError",
                file_path=audio_file_path
            )
            
            # Mark job as failed
            try:
                with db_session_context() as session:
                    update_job_status(
                        job_id,
                        "failed",
                        session=session,
                        error_message=error_msg
                    )
            except Exception as update_error:
                log_with_context(
                    logger,
                    logger.ERROR,
                    f"Failed to mark job as failed: {str(update_error)}",
                    job_id=job_id
                )
            
            return
        
        except ValueError as e:
            error_msg = f"Invalid audio file: {str(e)}"
            log_with_context(
                logger,
                logger.ERROR,
                error_msg,
                job_id=job_id,
                error_type="ValueError",
                file_path=audio_file_path
            )
            
            # Mark job as failed
            try:
                with db_session_context() as session:
                    update_job_status(
                        job_id,
                        "failed",
                        session=session,
                        error_message=error_msg
                    )
            except Exception as update_error:
                log_with_context(
                    logger,
                    logger.ERROR,
                    f"Failed to mark job as failed: {str(update_error)}",
                    job_id=job_id
                )
            
            # Cleanup
            cleanup_audio_file(audio_file_path, job_id)
            return
        
        # Step 4: Call OpenAI service for transcription
        original_text = None
        try:
            transcription_start = time()
            original_text = transcribe_audio(str(audio_path))
            transcription_duration = time() - transcription_start
            
            log_with_context(
                logger,
                logger.INFO,
                f"OpenAI transcription completed",
                job_id=job_id,
                duration=transcription_duration
            )
        
        except OpenAIQuotaError as e:
            error_msg = f"OpenAI quota exceeded: {str(e)}"
            log_with_context(
                logger,
                logger.ERROR,
                error_msg,
                job_id=job_id,
                error_type="OpenAIQuotaError"
            )
            
            # Mark job as failed (could be retried later by external system)
            try:
                with db_session_context() as session:
                    update_job_status(
                        job_id,
                        "failed",
                        session=session,
                        error_message=error_msg
                    )
            except Exception as update_error:
                log_with_context(
                    logger,
                    logger.ERROR,
                    f"Failed to mark job as failed: {str(update_error)}",
                    job_id=job_id
                )
            
            # Cleanup
            cleanup_audio_file(audio_file_path, job_id)
            return
        
        except OpenAIAPIError as e:
            error_msg = f"OpenAI API error: {str(e)}"
            log_with_context(
                logger,
                logger.ERROR,
                error_msg,
                job_id=job_id,
                error_type="OpenAIAPIError"
            )
            
            # Mark job as failed
            try:
                with db_session_context() as session:
                    update_job_status(
                        job_id,
                        "failed",
                        session=session,
                        error_message=error_msg
                    )
            except Exception as update_error:
                log_with_context(
                    logger,
                    logger.ERROR,
                    f"Failed to mark job as failed: {str(update_error)}",
                    job_id=job_id
                )
            
            # Cleanup
            cleanup_audio_file(audio_file_path, job_id)
            return
        
        except OpenAIServiceError as e:
            error_msg = f"OpenAI service error: {str(e)}"
            log_with_context(
                logger,
                logger.ERROR,
                error_msg,
                job_id=job_id,
                error_type="OpenAIServiceError"
            )
            
            # Mark job as failed
            try:
                with db_session_context() as session:
                    update_job_status(
                        job_id,
                        "failed",
                        session=session,
                        error_message=error_msg
                    )
            except Exception as update_error:
                log_with_context(
                    logger,
                    logger.ERROR,
                    f"Failed to mark job as failed: {str(update_error)}",
                    job_id=job_id
                )
            
            # Cleanup
            cleanup_audio_file(audio_file_path, job_id)
            return
        
        # Step 5: Store original_text in database
        try:
            with db_session_context() as session:
                update_job_status(
                    job_id,
                    "processing",
                    session=session,
                    original_text=original_text
                )
            
            log_with_context(
                logger,
                logger.INFO,
                f"Original transcription text stored",
                job_id=job_id
            )
        
        except (JobServiceError, JobNotFoundError) as e:
            error_msg = f"Failed to store original_text: {str(e)}"
            log_with_context(
                logger,
                logger.ERROR,
                error_msg,
                job_id=job_id,
                error_type=type(e).__name__
            )
            
            # Mark job as failed
            try:
                with db_session_context() as session:
                    update_job_status(
                        job_id,
                        "failed",
                        session=session,
                        error_message=error_msg,
                        original_text=original_text  # Try to save it anyway
                    )
            except Exception as update_error:
                log_with_context(
                    logger,
                    logger.ERROR,
                    f"Failed to mark job as failed: {str(update_error)}",
                    job_id=job_id
                )
            
            # Cleanup
            cleanup_audio_file(audio_file_path, job_id)
            return
        
        # Step 6: Trigger post-processing pipeline
        processed_text = None
        post_processing_failed = False
        
        try:
            postproc_start = time()
            
            # Create pipeline with default configuration
            pipeline = create_pipeline()
            
            # Process with database session for lexicon lookup
            with db_session_context() as session:
                processed_text = pipeline.process(
                    original_text,
                    lexicon_id=lexicon_id,
                    db=session,
                    job_id=job_id
                )
            
            postproc_duration = time() - postproc_start
            
            log_with_context(
                logger,
                logger.INFO,
                f"Post-processing completed",
                job_id=job_id,
                duration=postproc_duration
            )
        
        except PostProcessingError as e:
            # Post-processing failure is not fatal - we still have original_text
            log_with_context(
                logger,
                logger.WARNING,
                f"Post-processing failed, but original_text is valid: {str(e)}",
                job_id=job_id,
                error_type="PostProcessingError"
            )
            post_processing_failed = True
            processed_text = None  # No processed text available
        
        except Exception as e:
            # Unexpected post-processing error
            log_with_context(
                logger,
                logger.WARNING,
                f"Unexpected post-processing error: {str(e)}",
                job_id=job_id,
                error_type=type(e).__name__
            )
            post_processing_failed = True
            processed_text = None
        
        # Step 7: Store processed_text and update to completed
        try:
            with db_session_context() as session:
                update_job_status(
                    job_id,
                    "completed",
                    session=session,
                    processed_text=processed_text
                )
            
            total_duration = time() - start_time
            
            log_with_context(
                logger,
                logger.INFO,
                f"Job completed successfully",
                job_id=job_id,
                status="completed",
                duration=total_duration
            )
            
            if post_processing_failed:
                log_with_context(
                    logger,
                    logger.WARNING,
                    f"Job completed with post-processing warning",
                    job_id=job_id
                )
        
        except (JobServiceError, JobNotFoundError) as e:
            error_msg = f"Failed to mark job as completed: {str(e)}"
            log_with_context(
                logger,
                logger.ERROR,
                error_msg,
                job_id=job_id,
                error_type=type(e).__name__
            )
            
            # Try to mark as failed
            try:
                with db_session_context() as session:
                    update_job_status(
                        job_id,
                        "failed",
                        session=session,
                        error_message=error_msg
                    )
            except Exception as update_error:
                log_with_context(
                    logger,
                    logger.ERROR,
                    f"Failed to mark job as failed: {str(update_error)}",
                    job_id=job_id
                )
        
        # Step 8: Clean up temporary audio file
        cleanup_audio_file(audio_file_path, job_id)
        
        total_duration = time() - start_time
        log_with_context(
            logger,
            logger.INFO,
            f"Job processing completed",
            job_id=job_id,
            duration=total_duration
        )
    
    except Exception as e:
        # Catch-all for unexpected exceptions
        total_duration = time() - start_time
        error_msg = f"Unexpected error during job processing: {str(e)}"
        error_traceback = traceback.format_exc()
        
        log_with_context(
            logger,
            logger.ERROR,
            f"{error_msg}\n{error_traceback}",
            job_id=job_id,
            error_type=type(e).__name__,
            duration=total_duration
        )
        
        # Try to mark job as failed
        try:
            with db_session_context() as session:
                update_job_status(
                    job_id,
                    "failed",
                    session=session,
                    error_message=f"{error_msg}\n{error_traceback}"
                )
        except Exception as update_error:
            log_with_context(
                logger,
                logger.ERROR,
                f"Failed to mark job as failed after unexpected error: {str(update_error)}",
                job_id=job_id
            )
        
        # Clean up audio file
        if audio_file_path:
            cleanup_audio_file(audio_file_path, job_id)


# Worker function registration for RQ (Redis Queue)
# This decorator is typically used to register the function with the queue
# Example usage with RQ:
#
# from redis import Redis
# from rq import Queue
#
# redis_conn = Redis(host='localhost', port=6379, db=0)
# queue = Queue('transcription', connection=redis_conn)
#
# # Enqueue a job
# job = queue.enqueue(process_transcription_job, job_id='some-job-id')
#
# # Or use the @job decorator if using RQ workers directly:
# from rq.decorators import job
# 
# @job('transcription', connection=redis_conn, timeout=600)
# def process_transcription_job_decorated(job_id: str):
#     return process_transcription_job(job_id)
