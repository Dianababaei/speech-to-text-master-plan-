"""
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
