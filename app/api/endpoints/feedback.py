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
