"""
Job model for transcription jobs.
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Job(Base):
    """
    Represents a transcription job in the system.
    
    Status values: 'pending', 'processing', 'completed', 'failed'
    """
    __tablename__ = "jobs"
    
    id = Column(String(36), primary_key=True)  # UUID as string
    status = Column(String(20), nullable=False, default="pending")
    
    # Audio file information
    audio_file_path = Column(String(500), nullable=True)
    
    # Lexicon for post-processing
    lexicon_id = Column(String(36), nullable=True)
    
    # Transcription results
    original_text = Column(Text, nullable=True)  # Raw transcription from OpenAI
    processed_text = Column(Text, nullable=True)  # After post-processing
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)  # When processing started
    completed_at = Column(DateTime, nullable=True)  # When job finished (success or failure)
    
    def __repr__(self):
        return f"<Job(id={self.id}, status={self.status})>"
