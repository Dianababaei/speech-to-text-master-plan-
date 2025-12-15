"""
Transcription API request/response schemas.
"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class TranscriptionSubmitResponse(BaseModel):
    """
    Response model for audio transcription submission.
    
    Returns job identifier and status for tracking the asynchronous transcription.
    """
    
    job_id: str = Field(
        ...,
        description="Unique job identifier (UUID) for tracking transcription status",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )
    status: str = Field(
        ...,
        description="Initial job status (always 'pending' on submission)",
        examples=["pending"]
    )
    created_at: str = Field(
        ...,
        description="ISO 8601 timestamp when the job was created",
        examples=["2024-01-15T10:30:00Z"]
    )
    lexicon_id: Optional[str] = Field(
        None,
        description="Lexicon ID that will be used for post-processing",
        examples=["radiology", "legal", "general"]
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "job_id": "123e4567-e89b-12d3-a456-426614174000",
                    "status": "pending",
                    "created_at": "2024-01-15T10:30:00Z",
                    "lexicon_id": "radiology"
                }
            ]
        }
