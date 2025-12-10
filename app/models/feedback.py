"""
Feedback Model

This module defines the SQLAlchemy model for storing manual corrections to transcriptions
for future lexicon improvements.

Table: feedback
Purpose: Store manual corrections to transcriptions with status tracking

Fields:
- id: UUID primary key (auto-generated)
- job_id: UUID foreign key to jobs table (required)
- lexicon_id: VARCHAR, indicates which lexicon this correction applies to (required)
- original_text: TEXT, the original transcription text that needs correction (required)
- corrected_text: TEXT, the manually corrected version (required)
- status: ENUM ('pending', 'approved', 'rejected', 'auto-approved'), default: 'pending'
- confidence: FLOAT, nullable, reserved for future automated confidence scoring
- frequency: INTEGER, default 1, tracks how many times this correction has been submitted
- created_by: VARCHAR, identifier for who submitted the correction (required)
- created_at: TIMESTAMP, auto-set on creation
- updated_at: TIMESTAMP, auto-updated on modification

Indexes:
- Index on status for filtering pending/approved/rejected feedback
- Index on lexicon_id for filtering by domain
- Index on created_at for date range filtering and sorting
- Composite index on (status, lexicon_id) for combined filtering

Constraints:
- Foreign key to jobs table with ON DELETE CASCADE
- Check constraint that corrected_text != original_text
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Text,
    Float,
    Integer,
    DateTime,
    ForeignKey,
    Index,
    CheckConstraint,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

# Import the shared Base from api_key module
from app.models.api_key import Base


class Feedback(Base):
    """
    SQLAlchemy model for feedback storage and tracking.
    
    This model handles manual corrections to transcriptions, which can be used
    to improve lexicon terms and transcription accuracy over time.
    """
    
    __tablename__ = "feedback"
    
    # Primary key - UUID for distributed system compatibility
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Unique identifier for the feedback record"
    )
    
    # Foreign key to jobs table
    job_id = Column(
        String(36),
        ForeignKey('jobs.id', ondelete='CASCADE'),
        nullable=False,
        comment="Reference to the transcription job (UUID as string)"
    )
    
    # Lexicon identifier
    lexicon_id = Column(
        String(255),
        nullable=False,
        comment="Indicates which lexicon this correction applies to"
    )
    
    # Original and corrected text
    original_text = Column(
        Text,
        nullable=False,
        comment="The original transcription text that needs correction"
    )
    
    corrected_text = Column(
        Text,
        nullable=False,
        comment="The manually corrected version"
    )
    
    # Status tracking with ENUM
    status = Column(
        SQLEnum(
            'pending',
            'approved',
            'rejected',
            'auto-approved',
            name='feedback_status_enum',
            create_type=True
        ),
        nullable=False,
        default='pending',
        server_default='pending',
        comment="Status: pending, approved, rejected, or auto-approved"
    )
    
    # Future-ready fields
    confidence = Column(
        Float,
        nullable=True,
        comment="Reserved for future automated confidence scoring (0.0-1.0)"
    )
    
    frequency = Column(
        Integer,
        nullable=False,
        default=1,
        server_default='1',
        comment="Tracks how many times this correction has been submitted"
    )
    
    # Creator tracking
    created_by = Column(
        String(255),
        nullable=False,
        comment="Identifier for who submitted the correction"
    )
    
    # Timestamp tracking
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
    
    # Relationship to Job model
    job = relationship("Job", backref="feedback_items")
    
    # Table-level constraints and indexes
    __table_args__ = (
        # Check constraint: corrected_text must be different from original_text
        CheckConstraint(
            'corrected_text != original_text',
            name='ck_feedback_text_different'
        ),
        
        # Index on status for filtering
        Index('ix_feedback_status', 'status'),
        
        # Index on lexicon_id for filtering by domain
        Index('ix_feedback_lexicon_id', 'lexicon_id'),
        
        # Index on created_at for date range filtering and sorting
        Index('ix_feedback_created_at', 'created_at'),
        
        # Composite index on (status, lexicon_id) for combined filtering
        Index('ix_feedback_status_lexicon_id', 'status', 'lexicon_id'),
        
        # Table comment
        {'comment': 'Stores manual corrections to transcriptions for future lexicon improvements'}
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
            f"lexicon_id='{self.lexicon_id}', "
            f"status='{self.status}', "
            f"created_by='{self.created_by}', "
            f"created_at={self.created_at})>"
        )
