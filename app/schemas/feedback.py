"""
Feedback Schemas

Pydantic models for feedback request/response validation and serialization.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class FeedbackStatus(str, Enum):
    """Enum for feedback status values."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto-approved"


class FeedbackStatusUpdate(BaseModel):
    """
    Schema for updating feedback status.
    
    Used in PATCH /feedback/{feedback_id} endpoint.
    """
    status: FeedbackStatus = Field(
        ...,
        description="New status for the feedback. Must be 'approved' or 'rejected' for pending feedback."
    )
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Optional confidence score (0.0-1.0) for future use"
    )
    
    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        """Validate confidence is within range if provided."""
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "approved",
                "confidence": 0.95
            }
        }


class FeedbackResponse(BaseModel):
    """
    Schema for feedback response.
    
    Returns complete feedback record with all fields.
    """
    id: int = Field(..., description="Unique feedback ID")
    job_id: int = Field(..., description="ID of associated transcription job")
    original_text: str = Field(..., description="Original transcription text")
    corrected_text: str = Field(..., description="Corrected text by reviewer")
    diff_data: Optional[Dict[str, Any]] = Field(None, description="Detailed diff information")
    edit_distance: Optional[int] = Field(None, description="Levenshtein edit distance")
    accuracy_score: Optional[float] = Field(None, description="Calculated accuracy score (0-1)")
    review_time_seconds: Optional[int] = Field(None, description="Time spent reviewing")
    reviewer: Optional[str] = Field(None, description="User who provided feedback")
    review_notes: Optional[str] = Field(None, description="Additional notes from reviewer")
    extracted_terms: Optional[List[Dict[str, Any]]] = Field(None, description="New terms extracted from corrections")
    feedback_type: Optional[str] = Field(None, description="Type: correction, validation, quality_issue")
    is_processed: bool = Field(..., description="Whether feedback has been processed for learning")
    status: str = Field(..., description="Feedback status: pending, approved, rejected, auto-approved")
    confidence: Optional[float] = Field(None, description="Confidence score for the feedback (0.0-1.0)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional feedback metadata")
    created_at: datetime = Field(..., description="Timestamp when feedback was created")
    updated_at: datetime = Field(..., description="Timestamp when feedback was last modified")
    processed_at: Optional[datetime] = Field(None, description="When feedback was processed")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 123,
                "job_id": 456,
                "original_text": "The patient has diabetis",
                "corrected_text": "The patient has diabetes",
                "diff_data": {"changes": [{"type": "replace", "old": "diabetis", "new": "diabetes"}]},
                "edit_distance": 1,
                "accuracy_score": 0.95,
                "review_time_seconds": 120,
                "reviewer": "dr.smith",
                "review_notes": "Fixed spelling error",
                "extracted_terms": [{"term": "diabetes", "type": "medical"}],
                "feedback_type": "correction",
                "is_processed": False,
                "status": "approved",
                "confidence": 0.95,
                "metadata": {},
                "created_at": "2024-01-20T10:30:00Z",
                "updated_at": "2024-01-20T10:35:00Z",
                "processed_at": None
            }
        }
