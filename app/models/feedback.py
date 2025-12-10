"""
Feedback Model

This module defines the SQLAlchemy model for feedback management.

Table: feedback
Purpose: Store user-submitted corrections and feedback on transcriptions

Fields:
- id: Unique identifier (primary key)
- job_id: Foreign key to jobs table
- original_text: Original transcription text
- corrected_text: Corrected text by reviewer
- diff_data: JSONB field with detailed diff information
- edit_distance: Levenshtein edit distance
- accuracy_score: Calculated accuracy score (0-1)
- review_time_seconds: Time spent reviewing
- reviewer: User who provided feedback
- review_notes: Additional notes from reviewer
- extracted_terms: JSONB field with new terms extracted from corrections
- feedback_type: Type of feedback (correction, validation, quality_issue)
- is_processed: Whether feedback has been processed for learning
- status: Feedback approval status (pending, approved, rejected, auto-approved)
- confidence: Confidence score for the feedback (0.0-1.0)
- metadata: JSONB field for additional metadata
- created_at: Timestamp of feedback creation
- updated_at: Timestamp of last modification
- processed_at: When feedback was processed
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.api_key import Base


class Feedback(Base):
    """
    SQLAlchemy model for feedback storage and management.
    
    This model handles user-submitted corrections and feedback on transcriptions,
    including approval workflow and status tracking.
    """
    
    __tablename__ = "feedback"
    
    # Primary key
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
        comment="Unique identifier for the feedback record"
    )
    
    # Foreign key to jobs
    job_id = Column(
        Integer,
        ForeignKey('jobs.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="Reference to the transcription job"
    )
    
    # Text fields
    original_text = Column(
        Text,
        nullable=False,
        comment="Original transcription text"
    )
    
    corrected_text = Column(
        Text,
        nullable=False,
        comment="Corrected text by reviewer"
    )
    
    # Diff and accuracy metrics
    diff_data = Column(
        JSONB,
        nullable=True,
        comment="Detailed diff information"
    )
    
    edit_distance = Column(
        Integer,
        nullable=True,
        comment="Levenshtein edit distance"
    )
    
    accuracy_score = Column(
        Float,
        nullable=True,
        comment="Calculated accuracy score (0-1)"
    )
    
    # Review metadata
    review_time_seconds = Column(
        Integer,
        nullable=True,
        comment="Time spent reviewing"
    )
    
    reviewer = Column(
        String(100),
        nullable=True,
        index=True,
        comment="User who provided feedback"
    )
    
    review_notes = Column(
        Text,
        nullable=True,
        comment="Additional notes from reviewer"
    )
    
    # Extracted terms and type
    extracted_terms = Column(
        JSONB,
        nullable=True,
        comment="New terms extracted from corrections"
    )
    
    feedback_type = Column(
        String(50),
        nullable=True,
        index=True,
        comment="Type: correction, validation, quality_issue"
    )
    
    # Processing status
    is_processed = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default='false',
        index=True,
        comment="Whether feedback has been processed for learning"
    )
    
    # Approval status (new field)
    status = Column(
        String(50),
        nullable=False,
        default='pending',
        server_default='pending',
        index=True,
        comment="Feedback status: pending, approved, rejected, auto-approved"
    )
    
    # Confidence score (new field for future use)
    confidence = Column(
        Float,
        nullable=True,
        comment="Confidence score for the feedback (0.0-1.0)"
    )
    
    # Additional metadata
    metadata = Column(
        JSONB,
        nullable=True,
        comment="Additional feedback metadata"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="Timestamp when the feedback was created"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp when the feedback was last modified"
    )
    
    processed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When feedback was processed"
    )
    
    def __repr__(self):
        """
        String representation of the Feedback model for debugging.
        
        Returns:
            str: A readable representation showing key attributes
        """
        return (
            f"<Feedback(id={self.id}, "
            f"job_id={self.job_id}, "
            f"status='{self.status}', "
            f"reviewer='{self.reviewer}', "
            f"created_at={self.created_at})>"
        )
