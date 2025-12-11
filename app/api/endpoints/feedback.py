"""
Feedback Endpoints

REST API endpoints for managing and reviewing user-submitted feedback/corrections.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime

from app.database import get_db
from app.auth import get_admin_api_key
from app.models import APIKey
from app.models.feedback import Feedback
from app.schemas.feedback import (
    FeedbackResponse,
    FeedbackListResponse,
    FeedbackStatus
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/feedback",
    tags=["feedback"],
)


@router.get(
    "",
    response_model=FeedbackListResponse,
    summary="List feedback records",
    description="""
    Retrieve paginated list of user-submitted corrections/feedback with filtering options.
    
    **Admin authentication required** - Must provide X-API-Key header with admin privileges.
    
    ## Query Parameters:
    - `status`: Filter by feedback status (pending/approved/rejected)
    - `lexicon_id`: Filter by specific lexicon
    - `date_from`: Filter by created_at >= date (ISO 8601 format)
    - `date_to`: Filter by created_at <= date (ISO 8601 format)
    - `page`: Page number for pagination (default: 1)
    - `page_size`: Records per page (default: 50, max: 200)
    
    ## Response:
    Returns paginated feedback records with all fields including job_id reference.
    """,
    responses={
        200: {
            "description": "Paginated feedback list",
            "content": {
                "application/json": {
                    "example": {
                        "total": 150,
                        "page": 1,
                        "page_size": 50,
                        "items": [
                            {
                                "id": "123",
                                "job_id": "456",
                                "lexicon_id": "radiology",
                                "original_text": "patient has mild edima",
                                "corrected_text": "patient has mild edema",
                                "status": "pending",
                                "confidence": None,
                                "frequency": 1,
                                "created_by": "user@example.com",
                                "created_at": "2024-01-15T10:30:00Z",
                                "updated_at": "2024-01-15T10:30:00Z"
                            }
                        ]
                    }
                }
            }
        },
        400: {"description": "Invalid query parameters"},
        401: {"description": "Unauthorized - missing or invalid admin API key"}
    }
)
async def list_feedback(
    status: Optional[str] = Query(None, description="Filter by status (pending/approved/rejected)"),
    lexicon_id: Optional[str] = Query(None, description="Filter by lexicon"),
    date_from: Optional[datetime] = Query(None, description="Filter by created_at >= date"),
    date_to: Optional[datetime] = Query(None, description="Filter by created_at <= date"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=200, description="Records per page (max 200)"),
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(get_admin_api_key)
) -> FeedbackListResponse:
    """
    Get paginated list of feedback records with optional filters.
    
    Args:
        status: Filter by feedback status
        lexicon_id: Filter by lexicon identifier
        date_from: Filter by minimum creation date
        date_to: Filter by maximum creation date
        page: Page number for pagination
        page_size: Number of records per page
        db: Database session (injected)
        api_key: Admin API key (injected, validates admin access)
    
    Returns:
        FeedbackListResponse: Paginated list of feedback records
        
    Raises:
        HTTPException: 400 for invalid parameters, 401 for auth errors
    """
    try:
        # Validate status value if provided
        if status:
            valid_statuses = [s.value for s in FeedbackStatus]
            if status not in valid_statuses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                )
        
        # Validate date range
        if date_from and date_to and date_to < date_from:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="date_to must be after or equal to date_from"
            )
        
        # Build base query
        query = db.query(Feedback)
        
        # Apply filters dynamically
        filters = []
        
        if status:
            filters.append(Feedback.status == status)
            logger.debug(f"Filtering by status: {status}")
        
        if lexicon_id:
            filters.append(Feedback.lexicon_id == lexicon_id)
            logger.debug(f"Filtering by lexicon_id: {lexicon_id}")
        
        if date_from:
            filters.append(Feedback.created_at >= date_from)
            logger.debug(f"Filtering by date_from: {date_from}")
        
        if date_to:
            filters.append(Feedback.created_at <= date_to)
            logger.debug(f"Filtering by date_to: {date_to}")
        
        # Apply all filters
        if filters:
            query = query.filter(and_(*filters))
        
        # Get total count before pagination
        total = query.count()
        logger.info(f"Total feedback records matching filters: {total}")
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(Feedback.created_at.desc())
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        feedback_records = query.all()
        logger.info(f"Returning {len(feedback_records)} feedback records (page {page}, size {page_size})")
        
        # Convert to response models
        items = []
        for record in feedback_records:
            items.append(FeedbackResponse(
                id=str(record.id),
                job_id=str(record.job_id),
                lexicon_id=record.lexicon_id,
                original_text=record.original_text,
                corrected_text=record.corrected_text,
                status=record.status,
                confidence=record.confidence,
                frequency=record.frequency,
                created_by=record.created_by or record.reviewer,  # Fallback to reviewer if created_by is None
                created_at=record.created_at,
                updated_at=record.updated_at
            ))
        
        return FeedbackListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=items
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    
    except Exception as e:
        logger.error(f"Error retrieving feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feedback records"
        )
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
