"""
Database models for the transcription service.

Defines SQLAlchemy models for jobs and related entities.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Job(Base):
    """
    Job model for transcription jobs.
    
    Tracks the status and metadata of audio transcription jobs.
    """
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, index=True)
    status = Column(String, nullable=False, index=True)  # pending, processing, completed, failed
    audio_file_path = Column(String, nullable=True)
    transcript = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Job(id={self.id}, status={self.status})>"
