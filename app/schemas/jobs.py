"""
Job response schemas for the transcription API.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """
    Job status enumeration.
    
    - **pending**: Job queued but not yet started
    - **processing**: Job is actively being transcribed
    - **completed**: Transcription completed successfully
    - **failed**: Transcription failed due to error
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStatusResponse(BaseModel):
    """
    Response model for job status retrieval.
    
    Represents the current state of a transcription job including
    timestamps, status, and results (if available).
    """
    job_id: UUID = Field(..., description="Unique identifier for the job")
    status: JobStatus = Field(..., description="Current status of the job")
    created_at: datetime = Field(..., description="ISO 8601 timestamp when job was created")
    completed_at: Optional[datetime] = Field(None, description="ISO 8601 timestamp when job completed (null if not completed)")
    original_text: Optional[str] = Field(None, description="Original transcribed text (null for pending/processing jobs)")
    processed_text: Optional[str] = Field(None, description="Post-processed transcription text (null for pending/processing jobs)")
    error_message: Optional[str] = Field(None, description="Error message if job failed (null otherwise)")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "examples": [
                {
                    "job_id": "123e4567-e89b-12d3-a456-426614174000",
                    "status": "completed",
                    "created_at": "2024-01-15T10:30:00Z",
                    "completed_at": "2024-01-15T10:31:30Z",
                    "original_text": "Hello world this is a test transcription",
                    "processed_text": "Hello world, this is a test transcription.",
                    "error_message": None
                },
                {
                    "job_id": "223e4567-e89b-12d3-a456-426614174001",
                    "status": "processing",
                    "created_at": "2024-01-15T10:32:00Z",
                    "completed_at": None,
                    "original_text": None,
                    "processed_text": None,
                    "error_message": None
                },
                {
                    "job_id": "323e4567-e89b-12d3-a456-426614174002",
                    "status": "failed",
                    "created_at": "2024-01-15T10:33:00Z",
                    "completed_at": "2024-01-15T10:33:15Z",
                    "original_text": None,
                    "processed_text": None,
                    "error_message": "Audio file format not supported"
                }
            ]
        }
