"""
Job model for transcription jobs.
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, Float, BigInteger, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class Job(Base):
    """
    Represents a transcription job in the system.

    Status values: 'pending', 'processing', 'completed', 'failed'
    """
    __tablename__ = "jobs"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # UUID displayed to users
    job_id = Column(String(100), nullable=False, unique=True, index=True, comment='Unique job identifier (UUID)')

    # Job status
    status = Column(String(50), nullable=False, default="pending", comment='Job status: pending, processing, completed, failed')

    # Audio file information
    audio_filename = Column(String(500), nullable=True, comment='Original audio filename')
    audio_format = Column(String(10), nullable=True, comment='Audio format: wav, mp3, m4a')
    audio_duration = Column(Float, nullable=True, comment='Audio duration in seconds')
    audio_size_bytes = Column(BigInteger, nullable=True, comment='Audio file size in bytes')
    audio_storage_path = Column(String(1000), nullable=True, comment='Path to stored audio file')

    # Language and model
    language = Column(String(10), nullable=True, comment='Primary language code')
    model_name = Column(String(100), nullable=True, comment='OpenAI model used (gpt-4o-transcribe, whisper-1)')

    # Transcription results
    transcription_text = Column(Text, nullable=True, comment='Raw transcription output')
    lexicon_version = Column(String(50), nullable=True, comment='Version of lexicon used')

    # Processing metrics
    processing_time_seconds = Column(Float, nullable=True, comment='Total processing time')

    # Error tracking
    error_message = Column(Text, nullable=True, comment='Error message if job failed')

    # Metadata
    metadata = Column(JSONB, nullable=True, comment='Additional job metadata')

    # API key relationship
    api_key_id = Column(Integer, ForeignKey('api_keys.id', ondelete='SET NULL'), nullable=True, comment='API key used for this job')

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, server_default='CURRENT_TIMESTAMP')
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, server_default='CURRENT_TIMESTAMP')
    started_at = Column(DateTime(timezone=True), nullable=True, comment='When processing started')
    completed_at = Column(DateTime(timezone=True), nullable=True, comment='When job completed or failed')

    # User tracking
    submitted_by = Column(String(100), nullable=True, comment='User who submitted the job')

    def __repr__(self):
        return f"<Job(id={self.id}, job_id={self.job_id}, status={self.status})>"
