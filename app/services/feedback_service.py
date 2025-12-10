"""
Feedback Service

Business logic for feedback management including status transition validation.
"""

from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackStatus


class InvalidStatusTransitionError(Exception):
    """Raised when an invalid status transition is attempted."""
    pass


def validate_status_transition(current_status: str, new_status: str) -> None:
    """
    Validate that a status transition is allowed.
    
    Status Transition Rules:
    - pending → approved ✓
    - pending → rejected ✓
    - approved → rejected ✗ (invalid)
    - rejected → approved ✗ (invalid)
    - auto-approved → any ✗ (invalid, future state)
    
    Args:
        current_status: Current status of the feedback
        new_status: Desired new status
        
    Raises:
        InvalidStatusTransitionError: If the transition is not allowed
    """
    # Normalize to lowercase for comparison
    current = current_status.lower()
    new = new_status.lower()
    
    # Auto-approved feedback cannot be changed
    if current == FeedbackStatus.AUTO_APPROVED.value:
        raise InvalidStatusTransitionError(
            f"Cannot change status of auto-approved feedback. "
            f"Transition from '{current_status}' to '{new_status}' is not allowed."
        )
    
    # Approved feedback cannot be changed
    if current == FeedbackStatus.APPROVED.value:
        raise InvalidStatusTransitionError(
            f"Cannot change status of already approved feedback. "
            f"Transition from '{current_status}' to '{new_status}' is not allowed."
        )
    
    # Rejected feedback cannot be changed
    if current == FeedbackStatus.REJECTED.value:
        raise InvalidStatusTransitionError(
            f"Cannot change status of already rejected feedback. "
            f"Transition from '{current_status}' to '{new_status}' is not allowed."
        )
    
    # Pending feedback can only transition to approved or rejected
    if current == FeedbackStatus.PENDING.value:
        if new not in [FeedbackStatus.APPROVED.value, FeedbackStatus.REJECTED.value]:
            raise InvalidStatusTransitionError(
                f"Pending feedback can only be approved or rejected. "
                f"Transition from '{current_status}' to '{new_status}' is not allowed."
            )
    
    # If we reach here, the transition is valid
    return


def get_feedback_by_id(db: Session, feedback_id: int) -> Optional[Feedback]:
    """
    Retrieve a feedback record by ID.
    
    Args:
        db: Database session
        feedback_id: ID of the feedback record
        
    Returns:
        Feedback object if found, None otherwise
    """
    return db.query(Feedback).filter(Feedback.id == feedback_id).first()


def update_feedback_status(
    db: Session,
    feedback_id: int,
    new_status: str,
    confidence: Optional[float] = None
) -> Feedback:
    """
    Update the status of a feedback record with validation.
    
    Args:
        db: Database session
        feedback_id: ID of the feedback record to update
        new_status: New status to set (approved, rejected)
        confidence: Optional confidence score (0.0-1.0)
        
    Returns:
        Updated Feedback object
        
    Raises:
        HTTPException: 404 if feedback not found, 400 if invalid transition
    """
    # Get existing feedback record
    feedback = get_feedback_by_id(db, feedback_id)
    
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback with ID {feedback_id} not found"
        )
    
    # Validate status transition
    try:
        validate_status_transition(feedback.status, new_status)
    except InvalidStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Update the feedback record
    feedback.status = new_status
    
    # Update confidence if provided
    if confidence is not None:
        feedback.confidence = confidence
    
    # updated_at will be automatically updated by the onupdate trigger
    
    # Commit the changes
    db.commit()
    db.refresh(feedback)
    
    return feedback
