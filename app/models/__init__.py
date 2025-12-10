"""
Models package

This package contains all SQLAlchemy models for the application.
"""

from app.models.api_key import ApiKey, Base
from app.models.job import Job
from app.models.lexicon import LexiconTerm
from app.models.feedback import Feedback

# Alias for backward compatibility
APIKey = ApiKey

__all__ = ["ApiKey", "APIKey", "Base", "Job", "LexiconTerm", "Feedback"]
