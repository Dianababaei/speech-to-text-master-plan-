"""
Worker for processing transcription jobs.

This module contains the main worker function that orchestrates the complete
transcription workflow from job pickup to result storage.
"""
import os
import logging
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
from app.services.lexicon_service import build_whisper_prompt_from_lexicon
from app.utils.database import db_session_context
from app.utils.logging import get_logger, log_with_context
from app.config.settings import get_settings

settings = get_settings()
logger = get_logger(__name__)


def save_transcription_to_file(transcription_text: str, audio_filename: str, job_id: str) -> Optional[str]:
    """
    Save transcription to a text file in the transcriptions directory.

    Args:
        transcription_text: The transcription text to save
        audio_filename: Original audio filename (e.g., "63148.mp3")
        job_id: Job ID for logging context

    Returns:
        Path to saved file if successful, None otherwise
    """
    if not transcription_text:
        log_with_context(
            logger,
            logging.WARNING,
            f"No transcription text to save",
            job_id=job_id
        )
        return None

    try:
        # Create transcriptions directory if it doesn't exist
        transcriptions_dir = Path("transcriptions")
        transcriptions_dir.mkdir(exist_ok=True)

        # Generate filename: replace audio extension with .txt
        # e.g., "63148.mp3" -> "63148.txt"
        base_name = Path(audio_filename).stem
        txt_filename = f"{base_name}.txt"
        txt_path = transcriptions_dir / txt_filename

        # Save transcription with UTF-8 encoding for Persian text
        txt_path.write_text(transcription_text, encoding='utf-8')

        log_with_context(
            logger,
            logging.INFO,
            f"Transcription saved to file",
            job_id=job_id,
            file_path=str(txt_path),
            audio_filename=audio_filename
        )

        return str(txt_path)

    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
            f"Failed to save transcription to file: {str(e)}",
            job_id=job_id,
            audio_filename=audio_filename,
            error_type=type(e).__name__
        )
        return None


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
                logging.INFO,
                f"Audio file cleaned up successfully",
                job_id=job_id,
                file_path=file_path
            )
        else:
            log_with_context(
                logger,
                logging.WARNING,
                f"Audio file not found for cleanup (may have been deleted already)",
                job_id=job_id,
                file_path=file_path
            )
    except Exception as e:
        log_with_context(
            logger,
            logging.ERROR,
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
            logging.ERROR,
            f"Audio file not found",
            job_id=job_id,
            file_path=file_path
        )
        raise FileNotFoundError(f"Audio file not found: {file_path}")
    
    # Check if file is readable
    if not os.access(path, os.R_OK):
        log_with_context(
            logger,
            logging.ERROR,
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
            logging.WARNING,
            f"Audio file has unexpected extension: {path.suffix}",
            job_id=job_id,
            file_path=file_path
        )
    
    log_with_context(
        logger,
        logging.INFO,
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
    audio_filename = None

    log_with_context(
        logger,
        logging.INFO,
        f"Starting transcription job processing",
        job_id=job_id
    )

    try:
        # Step 1: Fetch job from database
        with db_session_context() as session:
            try:
                job = get_job(job_id, session=session)
                audio_file_path = job.audio_storage_path
                audio_filename = job.audio_filename
                # Use 'general' lexicon by default if no lexicon_id specified
                lexicon_id = getattr(job, 'lexicon_id', None) or 'general'
                # Get language for Whisper transcription
                language = getattr(job, 'language', None)

                log_with_context(
                    logger,
                    logging.INFO,
                    f"Job loaded from database",
                    job_id=job_id,
                    status=job.status,
                    file_path=audio_file_path,
                    language=language
                )
            
            except JobNotFoundError as e:
                log_with_context(
                    logger,
                    logging.ERROR,
                    f"Job not found in database: {str(e)}",
                    job_id=job_id,
                    error_type="JobNotFoundError"
                )
                # Can't update status if job doesn't exist
                return
            
            except JobServiceError as e:
                log_with_context(
                    logger,
                    logging.ERROR,
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
                logging.INFO,
                f"Job status updated to processing",
                job_id=job_id,
                status="processing"
            )
        
        except (JobServiceError, JobNotFoundError) as e:
            log_with_context(
                logger,
                logging.ERROR,
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
                logging.ERROR,
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
                    logging.ERROR,
                    f"Failed to mark job as failed: {str(update_error)}",
                    job_id=job_id
                )
            
            return
        
        except ValueError as e:
            error_msg = f"Invalid audio file: {str(e)}"
            log_with_context(
                logger,
                logging.ERROR,
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
                    logging.ERROR,
                    f"Failed to mark job as failed: {str(update_error)}",
                    job_id=job_id
                )
            
            # Cleanup
            cleanup_audio_file(audio_file_path, job_id)
            return
        
        # Step 4: Build Whisper prompt from lexicon
        whisper_prompt = None
        try:
            with db_session_context() as session:
                whisper_prompt = build_whisper_prompt_from_lexicon(lexicon_id, session)
                log_with_context(
                    logger,
                    logging.INFO,
                    f"Built Whisper prompt from lexicon",
                    job_id=job_id,
                    lexicon_id=lexicon_id,
                    prompt_length=len(whisper_prompt)
                )
        except Exception as e:
            log_with_context(
                logger,
                logging.WARNING,
                f"Failed to build Whisper prompt, proceeding without it: {str(e)}",
                job_id=job_id,
                error_type=type(e).__name__
            )
            whisper_prompt = None  # Continue without prompt

        # Step 5: Call OpenAI service for transcription
        original_text = None
        try:
            transcription_start = time()
            original_text = transcribe_audio(
                str(audio_path),
                language=language,
                prompt=whisper_prompt
            )
            transcription_duration = time() - transcription_start

            log_with_context(
                logger,
                logging.INFO,
                f"OpenAI transcription completed",
                job_id=job_id,
                duration=transcription_duration,
                language=language,
                used_prompt=whisper_prompt is not None
            )
        
        except OpenAIQuotaError as e:
            error_msg = f"OpenAI quota exceeded: {str(e)}"
            log_with_context(
                logger,
                logging.ERROR,
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
                    logging.ERROR,
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
                logging.ERROR,
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
                    logging.ERROR,
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
                logging.ERROR,
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
                    logging.ERROR,
                    f"Failed to mark job as failed: {str(update_error)}",
                    job_id=job_id
                )
            
            # Cleanup
            cleanup_audio_file(audio_file_path, job_id)
            return
        
        # Step 5: Store transcription_text in database
        try:
            with db_session_context() as session:
                update_job_status(
                    job_id,
                    "processing",
                    session=session,
                    transcription_text=original_text
                )

            log_with_context(
                logger,
                logging.INFO,
                f"Transcription text stored in database",
                job_id=job_id
            )

            # Step 5.5: Save transcription to text file
            if audio_filename:
                save_transcription_to_file(original_text, audio_filename, job_id)

        except (JobServiceError, JobNotFoundError) as e:
            error_msg = f"Failed to store transcription_text: {str(e)}"
            log_with_context(
                logger,
                logging.ERROR,
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
                        transcription_text=original_text  # Try to save it anyway
                    )
            except Exception as update_error:
                log_with_context(
                    logger,
                    logging.ERROR,
                    f"Failed to mark job as failed: {str(update_error)}",
                    job_id=job_id
                )
            
            # Cleanup
            cleanup_audio_file(audio_file_path, job_id)
            return
        
        # Step 6: Trigger post-processing pipeline
        processed_text = None
        confidence_metrics = None

        try:
            postproc_start = time()

            # Create pipeline with default configuration
            pipeline = create_pipeline()

            # Process with database session for lexicon lookup
            with db_session_context() as session:
                processed_text, confidence_metrics = pipeline.process(
                    original_text,
                    lexicon_id=lexicon_id,
                    db=session,
                    job_id=job_id
                )

            postproc_duration = time() - postproc_start

            log_with_context(
                logger,
                logging.INFO,
                f"Post-processing completed",
                job_id=job_id,
                duration=postproc_duration,
                correction_count=confidence_metrics.get('correction_count', 0) if confidence_metrics else 0,
                fuzzy_match_count=confidence_metrics.get('fuzzy_match_count', 0) if confidence_metrics else 0,
                confidence_score=confidence_metrics.get('confidence_score', 0.0) if confidence_metrics else 0.0
            )

            # If post-processing returns None or empty string, fall back to original
            if not processed_text:
                log_with_context(
                    logger,
                    logging.WARNING,
                    f"Post-processing returned empty result, using original_text",
                    job_id=job_id
                )
                processed_text = original_text
                confidence_metrics = None

        except PostProcessingError as e:
            # Post-processing failure is not fatal - we still have original_text
            log_with_context(
                logger,
                logging.WARNING,
                f"Post-processing failed, but original_text is valid: {str(e)}",
                job_id=job_id,
                error_type="PostProcessingError"
            )
            processed_text = original_text
            confidence_metrics = None

        except Exception as e:
            # Unexpected post-processing error
            log_with_context(
                logger,
                logging.ERROR,
                f"Unexpected post-processing error: {str(e)}. Falling back to original_text",
                job_id=job_id,
                error_type=type(e).__name__
            )
            # Fall back to original text
            processed_text = original_text
            confidence_metrics = None
        
        # Step 7: Update job to completed with processed text and confidence metrics
        # Note: transcription_text is already saved in Step 5
        try:
            # Prepare update data
            update_data = {
                "processed_text": processed_text
            }

            # Add confidence metrics if available
            if confidence_metrics:
                update_data["correction_count"] = confidence_metrics.get('correction_count', 0)
                update_data["fuzzy_match_count"] = confidence_metrics.get('fuzzy_match_count', 0)
                update_data["confidence_score"] = confidence_metrics.get('confidence_score', None)
                update_data["confidence_metrics"] = confidence_metrics.get('confidence_metrics', None)

            with db_session_context() as session:
                update_job_status(
                    job_id,
                    "completed",
                    session=session,
                    **update_data
                )
            
            total_duration = time() - start_time
            
            log_with_context(
                logger,
                logging.INFO,
                f"Job completed successfully",
                job_id=job_id,
                status="completed",
                duration=total_duration
            )

        except (JobServiceError, JobNotFoundError) as e:
            error_msg = f"Failed to mark job as completed: {str(e)}"
            log_with_context(
                logger,
                logging.ERROR,
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
                    logging.ERROR,
                    f"Failed to mark job as failed: {str(update_error)}",
                    job_id=job_id
                )
        
        # Step 8: Clean up temporary audio file
        cleanup_audio_file(audio_file_path, job_id)
        
        total_duration = time() - start_time
        log_with_context(
            logger,
            logging.INFO,
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
            logging.ERROR,
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
                logging.ERROR,
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
