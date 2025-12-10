"""
Feedback API Endpoints

Endpoints for managing user-submitted corrections and feedback.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_admin_api_key
from app.models import APIKey
from app.schemas.feedback import FeedbackStatusUpdate, FeedbackResponse
from app.services.feedback_service import update_feedback_status


router = APIRouter(
    prefix="/feedback",
    tags=["feedback"],
    dependencies=[Depends(get_admin_api_key)]
)


@router.patch(
    "/{feedback_id}",
    response_model=FeedbackResponse,
    status_code=status.HTTP_200_OK,
    summary="Update feedback status",
    description="""
Update the approval status of a user-submitted correction.

**Admin-level API key required.**

## Status Transition Rules

Valid transitions:
- `pending` → `approved` ✓
- `pending` → `rejected` ✓

Invalid transitions:
- `approved` → `rejected` ✗ (returns 400 error)
- `rejected` → `approved` ✗ (returns 400 error)
- `auto-approved` → any ✗ (returns 400 error)

## Authentication

This endpoint requires an admin-level API key. Admin privileges are determined by:
- Metadata field contains `{"role": "admin"}`, OR
- Project name contains "admin"

## Error Responses

- **401**: Missing or invalid API key
- **403**: Valid API key but not admin-level
- **404**: Feedback ID not found
- **400**: Invalid status transition
- **422**: Validation error (invalid status value or confidence out of range)
    """,
    responses={
        200: {
            "description": "Feedback status updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 123,
                        "job_id": 456,
                        "original_text": "The patient has diabetis",
                        "corrected_text": "The patient has diabetes",
                        "status": "approved",
                        "confidence": 0.95,
                        "created_at": "2024-01-20T10:30:00Z",
                        "updated_at": "2024-01-20T10:35:00Z"
                    }
                }
            }
        },
        400: {
            "description": "Invalid status transition",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Cannot change status of already approved feedback. Transition from 'approved' to 'rejected' is not allowed."
                    }
                }
            }
        },
        404: {
            "description": "Feedback not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Feedback with ID 123 not found"
                    }
                }
            }
        },
        401: {
            "description": "Authentication error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "API key is required. Provide X-API-Key header."
                    }
                }
            }
        },
        403: {
            "description": "Authorization error - admin required",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Admin privileges required. This endpoint requires an admin-level API key."
                    }
                }
            }
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "status"],
                                "msg": "Input should be 'approved' or 'rejected'",
                                "type": "enum"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def update_feedback(
    feedback_id: int,
    update_data: FeedbackStatusUpdate,
    db: Session = Depends(get_db),
    admin_key: APIKey = Depends(get_admin_api_key)
):
    """
    Update the status of a feedback record.
    
    Args:
        feedback_id: ID of the feedback record to update
        update_data: Status update data (status and optional confidence)
        db: Database session (injected)
        admin_key: Admin API key (injected, validates admin access)
        
    Returns:
        Updated feedback record with all fields
        
    Raises:
        HTTPException: 404 if not found, 400 if invalid transition, 403 if not admin
    """
    # Update feedback status using service layer
    feedback = update_feedback_status(
        db=db,
        feedback_id=feedback_id,
        new_status=update_data.status.value,
        confidence=update_data.confidence
    )
    
    return feedback
