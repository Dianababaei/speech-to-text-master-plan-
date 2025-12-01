"""
SQLAlchemy model for transcription jobs table.

This module defines the Job model which tracks the complete lifecycle of audio
transcription requests from submission through processing to completion.
"""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey,
    Index,
    Enum as SQLEnum,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.declarative import declarative_base

# Assume Base is defined elsewhere in the application
# from app.database import Base
Base = declarative_base()


class JobStatus(str, enum.Enum):
    """Enumeration of possible job statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(Base):
    """
    SQLAlchemy model for transcription jobs.
    
    Tracks the complete lifecycle of audio transcription requests including
    submission, processing, and completion with support for both raw and
    processed transcription results.
    """
    
    __tablename__ = "jobs"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Unique identifier for the job"
    )
    
    # Foreign key to api_keys table
    api_key_id = Column(
        UUID(as_uuid=True),
        ForeignKey("api_keys.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to the API key used to submit this job"
    )
    
    # Job configuration fields
    lexicon_id = Column(
        String(255),
        nullable=False,
        comment="Domain lexicon to use (e.g., radiology, cardiology)"
    )
    
    audio_file_path = Column(
        String(512),
        nullable=False,
        comment="Storage location of the audio file"
    )
    
    audio_format = Column(
        String(10),
        nullable=False,
        comment="Audio file format (WAV, MP3, or M4A)"
    )
    
    # Job status
    status = Column(
        SQLEnum(JobStatus, name="job_status", create_constraint=True),
        nullable=False,
        default=JobStatus.PENDING,
        comment="Current status of the job"
    )
    
    # Transcription results
    original_text = Column(
        Text,
        nullable=True,
        comment="Raw transcription output from OpenAI API"
    )
    
    processed_text = Column(
        Text,
        nullable=True,
        comment="Transcription after lexicon lookup and post-processing"
    )
    
    # Error handling
    error_message = Column(
        Text,
        nullable=True,
        comment="Detailed error message if status is failed"
    )
    
    # Timestamps
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="Job submission time"
    )
    
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Last modification time"
    )
    
    completed_at = Column(
        DateTime,
        nullable=True,
        comment="Time when processing finished (success or failure)"
    )
    
    # Relationship to api_keys table
    api_key = relationship("ApiKey", back_populates="jobs")
    
    # Table indexes for performance optimization
    __table_args__ = (
        # Index on status for filtering job queues
        Index("idx_jobs_status", "status"),
        
        # Index on created_at for time-based queries and cleanup
        Index("idx_jobs_created_at", "created_at"),
        
        # Composite index on (api_key_id, created_at) for per-client job history
        Index("idx_jobs_api_key_created", "api_key_id", "created_at"),
        
        # Add check constraint for audio format
        CheckConstraint(
            "audio_format IN ('WAV', 'MP3', 'M4A')",
            name="check_audio_format"
        ),
    )
    
    @validates("audio_format")
    def validate_audio_format(self, key: str, value: str) -> str:
        """
        Validate that audio_format is one of the supported formats.
        
        Args:
            key: The field name being validated
            value: The audio format value to validate
            
        Returns:
            The validated (uppercase) audio format
            
        Raises:
            ValueError: If the audio format is not supported
        """
        if value is None:
            raise ValueError("audio_format cannot be None")
        
        # Normalize to uppercase
        normalized_value = value.upper()
        
        allowed_formats = {"WAV", "MP3", "M4A"}
        if normalized_value not in allowed_formats:
            raise ValueError(
                f"Invalid audio format '{value}'. "
                f"Allowed formats: {', '.join(allowed_formats)}"
            )
        
        return normalized_value
    
    def __repr__(self) -> str:
        """
        String representation of the Job instance for debugging.
        
        Returns:
            A string containing key job information
        """
        return (
            f"<Job(id={self.id}, "
            f"status={self.status.value if self.status else None}, "
            f"lexicon_id={self.lexicon_id}, "
            f"audio_format={self.audio_format}, "
            f"created_at={self.created_at}, "
            f"completed_at={self.completed_at})>"
        )
