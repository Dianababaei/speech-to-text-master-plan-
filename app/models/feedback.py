"""
Feedback Model

This module defines the SQLAlchemy model for user-submitted corrections/feedback.

Table: feedback
Purpose: Store user corrections for transcription improvement and learning
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.models import Base


class Feedback(Base):
    """
    SQLAlchemy model for feedback/correction submissions.
    
    This model handles user-submitted corrections to transcriptions,
    enabling continuous improvement and learning from user feedback.
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
    
    # Reference to job
    job_id = Column(
        Integer,
        ForeignKey('jobs.id', ondelete='CASCADE'),
        nullable=False,
        comment="Reference to the transcription job"
    )
    
    # Lexicon reference (for filtering)
    lexicon_id = Column(
        String(100),
        nullable=True,
        comment="Lexicon used for this transcription"
    )
    
    # Correction data
    original_text = Column(
        Text,
        nullable=False,
        comment="Original transcription text"
    )
    
    corrected_text = Column(
        Text,
        nullable=False,
        comment="Corrected text by user"
    )
    
    # Status for admin review workflow
    status = Column(
        String(50),
        nullable=False,
        default='pending',
        comment="Status: pending, approved, rejected"
    )
    
    # Additional metadata
    confidence = Column(
        Float,
        nullable=True,
        comment="Confidence score for the correction"
    )
    
    frequency = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Number of times this correction was submitted"
    )
    
    # User tracking
    created_by = Column(
        String(100),
        nullable=True,
        comment="User who submitted the feedback"
    )
    
    # Additional fields from original schema
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
    
    review_time_seconds = Column(
        Integer,
        nullable=True,
        comment="Time spent reviewing"
    )
    
    reviewer = Column(
        String(100),
        nullable=True,
        comment="User who provided feedback (legacy field)"
    )
    
    review_notes = Column(
        Text,
        nullable=True,
        comment="Additional notes from reviewer"
    )
    
    extracted_terms = Column(
        JSONB,
        nullable=True,
        comment="New terms extracted from corrections"
    )
    
    feedback_type = Column(
        String(50),
        nullable=True,
        comment="Type: correction, validation, quality_issue"
    )
    
    is_processed = Column(
        Integer,  # Using Integer for boolean (0/1)
        nullable=False,
        default=0,
        comment="Whether feedback has been processed for learning"
    )
    
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
    
    # Table-level constraints and indexes
    __table_args__ = (
        Index('ix_feedback_job_id', 'job_id'),
        Index('ix_feedback_status', 'status'),
        Index('ix_feedback_lexicon_id', 'lexicon_id'),
        Index('ix_feedback_created_at', 'created_at'),
        Index('ix_feedback_created_by', 'created_by'),
        {'comment': 'User-submitted corrections and feedback for learning'}
    )
    
    def __repr__(self):
        """String representation of the Feedback model for debugging."""
        return (
            f"<Feedback(id={self.id}, "
            f"job_id={self.job_id}, "
            f"status='{self.status}', "
            f"created_by='{self.created_by}', "
            f"created_at={self.created_at})>"
        )
