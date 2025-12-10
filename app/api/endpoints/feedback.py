"""
Feedback submission endpoints for the transcription API.

Provides endpoints for submitting corrections to transcriptions
for manual review and lexicon improvement.
"""
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_api_key
from app.models.feedback import Feedback
from app.models.job import Job
from app.models.api_key import ApiKey
from app.schemas.feedback import FeedbackSubmitRequest, FeedbackResponse


logger = logging.getLogger(__name__)

# Create router with /jobs prefix since feedback is nested under jobs
router = APIRouter(prefix="/jobs", tags=["feedback"])


@router.post(
    "/{job_id}/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit feedback for transcription job",
    description="""
    Submit corrections to a transcription for manual review and lexicon improvement.
    
    This endpoint allows users to provide feedback on transcription quality by
    submitting corrections. The feedback is stored for review and can be used to
    improve the lexicon over time.
    
    **Path Parameters:**
    - **job_id**: UUID of the transcription job being corrected
    
    **Request Body:**
    - **original_text**: The text from the transcription that needs correction (required)
    - **corrected_text**: The corrected version of the text (required, must differ from original)
    - **lexicon_id**: Optional lexicon to apply correction to (defaults to job's lexicon)
    - **created_by**: User identifier who submitted the correction (required)
    
    **Authentication:**
    - Requires valid API key in X-API-Key header
    
    **Response:**
    - Returns the created feedback record with a unique feedback_id for tracking
    """,
    responses={
        201: {
            "description": "Feedback successfully created",
            "content": {
                "application/json": {
                    "example": {
                        "feedback_id": 123,
                        "job_id": "123e4567-e89b-12d3-a456-426614174000",
                        "original_text": "The patient has high blod pressure",
                        "corrected_text": "The patient has high blood pressure",
                        "lexicon_id": "medical",
                        "created_by": "dr.smith@hospital.com",
                        "status": "pending",
                        "created_at": "2024-01-15T10:30:00Z"
                    }
                }
            }
        },
        400: {
            "description": "Validation error (empty fields, identical texts, invalid format)",
            "content": {
                "application/json": {
                    "examples": {
                        "identical_texts": {
                            "summary": "Corrected text same as original",
                            "value": {"detail": "corrected_text must be different from original_text"}
                        },
                        "invalid_uuid": {
                            "summary": "Invalid job_id format",
                            "value": {"detail": "Invalid job_id format"}
                        }
                    }
                }
            }
        },
        401: {
            "description": "Missing or invalid API key",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid or inactive API key"}
                }
            }
        },
        404: {
            "description": "Job not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Job with ID 123e4567-e89b-12d3-a456-426614174000 not found"}
                }
            }
        }
    }
)
async def submit_feedback(
    job_id: Annotated[UUID, Path(description="UUID of the transcription job")],
    feedback_data: FeedbackSubmitRequest,
    db: Annotated[Session, Depends(get_db)],
    api_key: Annotated[ApiKey, Depends(get_api_key)]
) -> FeedbackResponse:
    """
    Submit feedback/corrections for a transcription job.
    
    Validates the job exists, ensures the correction is meaningful, and stores
    the feedback for processing. If no lexicon_id is provided, uses the job's
    lexicon.
    
    Args:
        job_id: UUID of the job to submit feedback for
        feedback_data: Feedback submission data
        db: Database session (injected)
        api_key: Validated API key (injected)
    
    Returns:
        FeedbackResponse: Created feedback record with feedback_id
    
    Raises:
        HTTPException 400: Validation errors (empty fields, identical texts)
        HTTPException 404: Job not found
        HTTPException 401: Invalid/missing API key
    """
    logger.info(f"Received feedback submission for job_id: {job_id}")
    
    # Validate job exists by job_id (UUID string)
    job = db.query(Job).filter(Job.job_id == str(job_id)).first()
    
    if not job:
        logger.warning(f"Job not found: {job_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found"
        )
    
    logger.info(f"Found job with internal id: {job.id}")
    
    # Determine lexicon_id (use provided or extract from job's metadata if available)
    lexicon_id = feedback_data.lexicon_id
    if not lexicon_id:
        # Try to get lexicon_id from job metadata or lexicon_version
        if job.metadata and isinstance(job.metadata, dict):
            lexicon_id = job.metadata.get('lexicon_id')
        if not lexicon_id and job.lexicon_version:
            lexicon_id = job.lexicon_version
        logger.info(f"Using job's lexicon_id from metadata/version: {lexicon_id}")
    else:
        logger.info(f"Using provided lexicon_id: {lexicon_id}")
    
    # Create feedback record with metadata
    # Store status='pending', confidence=null, frequency=1 in metadata as per task requirements
    metadata = {
        "lexicon_id": lexicon_id,
        "status": "pending",
        "confidence": None,
        "frequency": 1
    }
    
    feedback = Feedback(
        job_id=job.id,  # Use internal integer id for FK
        original_text=feedback_data.original_text,
        corrected_text=feedback_data.corrected_text,
        reviewer=feedback_data.created_by,
        feedback_type="correction",  # Default type
        is_processed=False,
        metadata=metadata
    )
    
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    logger.info(f"Created feedback record with id: {feedback.id}")
    
    # Return response with feedback_id and job_id as UUID
    return FeedbackResponse(
        feedback_id=feedback.id,
        job_id=UUID(job.job_id),  # Convert back to UUID for response
        original_text=feedback.original_text,
        corrected_text=feedback.corrected_text,
        lexicon_id=lexicon_id,
        created_by=feedback.reviewer,
        status="pending",
        created_at=feedback.created_at
    )
