"""
Feedback model for transcription corrections.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.models.api_key import Base


class Feedback(Base):
    """
    Represents feedback/corrections submitted for transcription jobs.

    This model stores user-submitted corrections to transcriptions for
    continuous improvement and lexicon learning.
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

    # Foreign key to jobs table
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
        index=True,
        comment="Lexicon used for this transcription"
    )

    # Transcription texts
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

    # Extracted terms
    extracted_terms = Column(
        JSONB,
        nullable=True,
        comment="New terms extracted from corrections"
    )

    # Classification and type
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
        comment="Whether feedback has been processed for learning"
    )

    # Status for admin review workflow
    status = Column(
        String(50),
        nullable=False,
        default='pending',
        index=True,
        comment="Status: pending, approved, rejected"
    )

    # Additional metrics
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
        index=True,
        comment="User who submitted the feedback"
    )

    # Additional metadata - avoid 'metadata' name conflict with SQLAlchemy
    feedback_metadata = Column(
        'metadata',
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
        comment="Timestamp when the feedback was last updated"
    )

    processed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When feedback was processed for learning"
    )

    # Table-level constraints and indexes
    __table_args__ = (
        {'comment': 'User-submitted corrections and feedback for learning'}
    )

    def __repr__(self):
        """String representation of the Feedback model for debugging."""
        return (
            f"<Feedback(id={self.id}, "
            f"job_id={self.job_id}, "
            f"status='{self.status}', "
            f"reviewer='{self.reviewer}')>"
        )
