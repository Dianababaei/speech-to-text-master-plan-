from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.database import Base


class APIKey(Base):
    """Model for API key authentication."""
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    is_active = Column(Integer, default=1)  # SQLite doesn't have boolean
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now())


class Job(Base):
    """Model for transcription job."""
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(String, nullable=False, default="pending", index=True)
    lexicon_id = Column(String, nullable=False, default="radiology")
    audio_file_path = Column(String, nullable=False)
    audio_format = Column(String, nullable=False)
    api_key_id = Column(String, ForeignKey("api_keys.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Results (populated after processing)
    transcript = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
