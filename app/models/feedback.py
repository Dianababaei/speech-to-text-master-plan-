"""
Feedback model for transcription corrections.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.api_key import Base


class Feedback(Base):
    """
    Represents feedback/corrections submitted for transcription jobs.
    
    This model stores user-submitted corrections to transcriptions for
    continuous improvement and lexicon learning.
    """
    __tablename__ = "feedback"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to jobs table (references the internal integer id)
    job_id = Column(Integer, ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False)
    
    # Transcription texts
    original_text = Column(Text, nullable=False, comment='Original transcription text')
    corrected_text = Column(Text, nullable=False, comment='Corrected text by reviewer')
    
    # Diff and metrics
    diff_data = Column(JSONB, nullable=True, comment='Detailed diff information')
    edit_distance = Column(Integer, nullable=True, comment='Levenshtein edit distance')
    accuracy_score = Column(Float, nullable=True, comment='Calculated accuracy score (0-1)')
    review_time_seconds = Column(Integer, nullable=True, comment='Time spent reviewing')
    
    # Reviewer information
    reviewer = Column(String(100), nullable=True, comment='User who provided feedback')
    review_notes = Column(Text, nullable=True, comment='Additional notes from reviewer')
    
    # Extracted data
    extracted_terms = Column(JSONB, nullable=True, comment='New terms extracted from corrections')
    
    # Classification and status
    feedback_type = Column(String(50), nullable=True, comment='Type: correction, validation, quality_issue')
    is_processed = Column(Boolean, nullable=False, default=False, server_default='false',
                         comment='Whether feedback has been processed for learning')
    
    # Additional metadata (can store lexicon_id, confidence, frequency here)
    metadata = Column(JSONB, nullable=True, comment='Additional feedback metadata')
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow,
                       server_default='CURRENT_TIMESTAMP')
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow,
                       onupdate=datetime.utcnow, server_default='CURRENT_TIMESTAMP')
    processed_at = Column(DateTime(timezone=True), nullable=True, comment='When feedback was processed')
    
    def __repr__(self):
        return f"<Feedback(id={self.id}, job_id={self.job_id}, reviewer={self.reviewer})>"
