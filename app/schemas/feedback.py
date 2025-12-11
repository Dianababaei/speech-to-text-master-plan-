"""
Feedback Schemas

Pydantic models for feedback API request/response validation.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class FeedbackStatus(str, Enum):
    """Valid feedback status values."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class FeedbackQueryParams(BaseModel):
    """Query parameters for feedback listing endpoint."""
    
    status: Optional[FeedbackStatus] = Field(
        None,
        description="Filter by feedback status (pending/approved/rejected)"
    )
    
    lexicon_id: Optional[str] = Field(
        None,
        description="Filter by specific lexicon",
        max_length=100
    )
    
    date_from: Optional[datetime] = Field(
        None,
        description="Filter by created_at >= date (ISO 8601 format)"
    )
    
    date_to: Optional[datetime] = Field(
        None,
        description="Filter by created_at <= date (ISO 8601 format)"
    )
    
    page: int = Field(
        1,
        ge=1,
        description="Page number for pagination (default: 1)"
    )
    
    page_size: int = Field(
        50,
        ge=1,
        le=200,
        description="Records per page (default: 50, max: 200)"
    )
    
    @validator('date_to')
    def validate_date_range(cls, v, values):
        """Validate that date_to is not before date_from."""
        if v and 'date_from' in values and values['date_from']:
            if v < values['date_from']:
                raise ValueError('date_to must be after or equal to date_from')
        return v
    
    class Config:
        use_enum_values = True


class FeedbackResponse(BaseModel):
    """Response model for a single feedback item."""
    
    id: str = Field(..., description="Unique identifier for the feedback record")
    job_id: str = Field(..., description="Reference to the transcription job")
    lexicon_id: Optional[str] = Field(None, description="Lexicon used for this transcription")
    original_text: str = Field(..., description="Original transcription text")
    corrected_text: str = Field(..., description="Corrected text by user")
    status: str = Field(..., description="Status: pending, approved, rejected")
    confidence: Optional[float] = Field(None, description="Confidence score for the correction")
    frequency: int = Field(..., description="Number of times this correction was submitted")
    created_by: Optional[str] = Field(None, description="User who submitted the feedback")
    created_at: datetime = Field(..., description="Timestamp when the feedback was created")
    updated_at: datetime = Field(..., description="Timestamp when the feedback was last modified")
    
    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class FeedbackListResponse(BaseModel):
    """Response model for paginated feedback list."""
    
    total: int = Field(..., description="Total number of feedback records matching filters")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of records per page")
    items: List[FeedbackResponse] = Field(..., description="List of feedback items")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
Pydantic schemas for feedback endpoints.

These schemas define the request and response models for submitting
and retrieving transcription feedback/corrections.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class FeedbackSubmitRequest(BaseModel):
    """
    Request schema for submitting feedback on a transcription.
    
    Allows users to submit corrections to improve transcription accuracy
    and contribute to lexicon learning.
    """
    original_text: str = Field(
        ...,
        description="The original text from the transcription that needs correction",
        min_length=1
    )
    corrected_text: str = Field(
        ...,
        description="The corrected version of the text",
        min_length=1
    )
    lexicon_id: Optional[str] = Field(
        None,
        description="Optional lexicon ID to apply correction to (defaults to job's lexicon)"
    )
    created_by: str = Field(
        ...,
        description="Identifier for who submitted the correction (username, email, or user_id)",
        min_length=1
    )
    
    @field_validator('corrected_text')
    @classmethod
    def validate_corrected_text_different(cls, v, info):
        """Ensure corrected_text is different from original_text."""
        if 'original_text' in info.data and v == info.data['original_text']:
            raise ValueError('corrected_text must be different from original_text')
        return v
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "original_text": "The patient has high blod pressure",
                "corrected_text": "The patient has high blood pressure",
                "lexicon_id": "medical",
                "created_by": "dr.smith@hospital.com"
            }
        }


class FeedbackResponse(BaseModel):
    """
    Response schema for feedback submission.
    
    Returns the created feedback record with its unique identifier
    and metadata.
    """
    feedback_id: int = Field(
        ...,
        description="Unique identifier for the feedback record"
    )
    job_id: UUID = Field(
        ...,
        description="UUID of the transcription job this feedback is for"
    )
    original_text: str = Field(
        ...,
        description="The original text that was corrected"
    )
    corrected_text: str = Field(
        ...,
        description="The corrected text"
    )
    lexicon_id: Optional[str] = Field(
        None,
        description="Lexicon ID this correction is associated with"
    )
    created_by: str = Field(
        ...,
        description="User who submitted the correction"
    )
    status: str = Field(
        ...,
        description="Processing status of the feedback (e.g., 'pending')"
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when feedback was created"
    )
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_schema_extra = {
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
