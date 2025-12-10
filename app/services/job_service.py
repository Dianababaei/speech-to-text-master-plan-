"""
Job service for managing transcription job status and metadata.
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.job import Job
from app.utils.database import get_db_session, db_session_context
from app.utils.logging import get_logger, log_with_context

logger = get_logger(__name__)


class JobNotFoundError(Exception):
    """Raised when a job cannot be found in the database."""
    pass


class JobServiceError(Exception):
    """Raised when a job service operation fails."""
    pass


def get_job(job_id: str, session: Optional[Session] = None) -> Job:
    """
    Retrieve a job from the database by ID.
    
    Args:
        job_id: The job ID to retrieve
        session: Optional database session (creates new one if not provided)
        
    Returns:
        Job object
        
    Raises:
        JobNotFoundError: If job doesn't exist
        JobServiceError: If database error occurs
    """
    close_session = False
    if session is None:
        session = get_db_session()
        close_session = True
    
    try:
        job = session.query(Job).filter(Job.job_id == job_id).first()
        
        if job is None:
            log_with_context(
                logger,
                logging.ERROR,
                f"Job not found in database",
                job_id=job_id
            )
            raise JobNotFoundError(f"Job with ID {job_id} not found")
        
        return job
    
    except SQLAlchemyError as e:
        log_with_context(
            logger,
            logging.ERROR,
            f"Database error retrieving job: {str(e)}",
            job_id=job_id,
            error_type=type(e).__name__
        )
        raise JobServiceError(f"Failed to retrieve job: {str(e)}")
    
    finally:
        if close_session:
            session.close()


def update_job_status(
    job_id: str,
    status: str,
    session: Optional[Session] = None,
    **kwargs
) -> Job:
    """
    Update job status and related fields.
    
    Args:
        job_id: The job ID to update
        status: New status ('pending', 'processing', 'completed', 'failed')
        session: Optional database session (creates new one if not provided)
        **kwargs: Additional fields to update (e.g., error_message, original_text, etc.)
            Supported fields:
            - started_at: datetime
            - completed_at: datetime
            - original_text: str
            - processed_text: str
            - error_message: str
            - audio_file_path: str
            - lexicon_id: str
    
    Returns:
        Updated Job object
        
    Raises:
        JobNotFoundError: If job doesn't exist
        JobServiceError: If update fails
    """
    close_session = False
    manage_transaction = False
    
    if session is None:
        session = get_db_session()
        close_session = True
        manage_transaction = True
    
    try:
        # Get the job
        job = session.query(Job).filter(Job.job_id == job_id).first()
        
        if job is None:
            log_with_context(
                logger,
                logging.ERROR,
                f"Job not found for status update",
                job_id=job_id,
                status=status
            )
            raise JobNotFoundError(f"Job with ID {job_id} not found")
        
        old_status = job.status
        
        # Update status
        job.status = status
        
        # Update timestamp based on status
        if status == "processing" and "started_at" not in kwargs:
            job.started_at = datetime.utcnow()
        elif status in ["completed", "failed"] and "completed_at" not in kwargs:
            job.completed_at = datetime.utcnow()
        
        # Update additional fields
        for key, value in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, value)
        
        if manage_transaction:
            session.commit()
            session.refresh(job)
        
        log_with_context(
            logger,
            logging.INFO,
            f"Job status updated: {old_status} -> {status}",
            job_id=job_id,
            status=status
        )
        
        return job
    
    except JobNotFoundError:
        if manage_transaction:
            session.rollback()
        raise
    
    except SQLAlchemyError as e:
        if manage_transaction:
            session.rollback()
        
        log_with_context(
            logger,
            logging.ERROR,
            f"Database error updating job status: {str(e)}",
            job_id=job_id,
            status=status,
            error_type=type(e).__name__
        )
        raise JobServiceError(f"Failed to update job status: {str(e)}")
    
    except Exception as e:
        if manage_transaction:
            session.rollback()
        
        log_with_context(
            logger,
            logging.ERROR,
            f"Unexpected error updating job status: {str(e)}",
            job_id=job_id,
            status=status,
            error_type=type(e).__name__
        )
        raise JobServiceError(f"Unexpected error updating job: {str(e)}")
    
    finally:
        if close_session:
            session.close()


def update_job_fields(
    job_id: str,
    session: Optional[Session] = None,
    **fields
) -> Job:
    """
    Update specific job fields without changing status.
    
    Args:
        job_id: The job ID to update
        session: Optional database session
        **fields: Fields to update
    
    Returns:
        Updated Job object
        
    Raises:
        JobNotFoundError: If job doesn't exist
        JobServiceError: If update fails
    """
    close_session = False
    manage_transaction = False
    
    if session is None:
        session = get_db_session()
        close_session = True
        manage_transaction = True
    
    try:
        job = session.query(Job).filter(Job.job_id == job_id).first()
        
        if job is None:
            raise JobNotFoundError(f"Job with ID {job_id} not found")
        
        # Update fields
        for key, value in fields.items():
            if hasattr(job, key):
                setattr(job, key, value)
        
        if manage_transaction:
            session.commit()
            session.refresh(job)
        
        log_with_context(
            logger,
            logging.DEBUG,
            f"Job fields updated: {', '.join(fields.keys())}",
            job_id=job_id
        )
        
        return job
    
    except JobNotFoundError:
        if manage_transaction:
            session.rollback()
        raise
    
    except SQLAlchemyError as e:
        if manage_transaction:
            session.rollback()
        
        log_with_context(
            logger,
            logging.ERROR,
            f"Database error updating job fields: {str(e)}",
            job_id=job_id,
            error_type=type(e).__name__
        )
        raise JobServiceError(f"Failed to update job fields: {str(e)}")
    
    finally:
        if close_session:
            session.close()
