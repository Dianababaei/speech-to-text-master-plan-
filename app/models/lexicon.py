"""
Lexicon Models

This module defines SQLAlchemy models and Pydantic schemas for lexicon management.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    Float,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from pydantic import BaseModel, Field

from app.models.api_key import Base


class LexiconTerm(Base):
    """
    SQLAlchemy model for lexicon terms storage and management.

    This model handles domain-specific terms for transcription correction.
    """

    __tablename__ = "lexicon_terms"

    # Primary key
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
        comment="Unique identifier for the term"
    )

    # Lexicon identifier
    lexicon_id = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Identifier for the lexicon (e.g., radiology, cardiology)"
    )

    # Term and its normalized version
    term = Column(
        String(255),
        nullable=False,
        comment="The term to match in transcriptions"
    )

    normalized_term = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Normalized/lowercased version for case-insensitive matching"
    )

    # Replacement term
    replacement = Column(
        String(255),
        nullable=False,
        comment="The corrected/replacement term"
    )

    # Optional categorization and metadata
    category = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Category (e.g., drug, brand, medical)"
    )

    language = Column(
        String(10),
        nullable=True,
        index=True,
        comment="ISO language code (e.g., en, fa, zh)"
    )

    frequency = Column(
        Integer,
        nullable=False,
        default=0,
        server_default='0',
        comment="Usage frequency counter"
    )

    confidence_boost = Column(
        Float,
        nullable=True,
        comment="Confidence boost factor for this term"
    )

    alternatives = Column(
        JSONB,
        nullable=True,
        comment="Alternative spellings or variations"
    )

    term_metadata = Column(
        'metadata',
        JSONB,
        nullable=True,
        comment="Additional metadata"
    )

    source = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Source of the term (manual, learned, imported)"
    )

    # Active status for soft delete
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        server_default='true',
        index=True,
        comment="Flag to enable/disable the term without deletion"
    )

    # Timestamp tracking
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the term was created"
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp when the term was last modified"
    )

    created_by = Column(
        String(100),
        nullable=True,
        comment="User or system that created the term"
    )

    # Table-level constraints and indexes
    __table_args__ = (
        # Unique constraint on lexicon_id and normalized_term
        UniqueConstraint(
            'lexicon_id',
            'normalized_term',
            name='uq_lexicon_terms_lexicon_normalized'
        ),

        # Table comment
        {'comment': 'Domain-specific lexicon terms for transcription improvement'}
    )

    def __repr__(self):
        """
        String representation of the LexiconTerm model for debugging.

        Returns:
            str: A readable representation showing key attributes
        """
        return (
            f"<LexiconTerm(id={self.id}, "
            f"lexicon_id='{self.lexicon_id}', "
            f"term='{self.term}', "
            f"replacement='{self.replacement}', "
            f"is_active={self.is_active})>"
        )


# Pydantic Schemas

class LexiconMetadata(BaseModel):
    """
    Response schema for lexicon metadata.

    Used by both list and detail endpoints.
    """
    lexicon_id: str = Field(..., description="Unique identifier for the lexicon (e.g., 'radiology')")
    term_count: int = Field(..., description="Number of active terms in the lexicon")
    last_updated: datetime = Field(..., description="Timestamp of most recent term modification")
    description: Optional[str] = Field(None, description="Human-readable description of the lexicon")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LexiconListResponse(BaseModel):
    """
    Response schema for GET /lexicons endpoint.

    Returns array of all available lexicons with metadata.
    """
    lexicons: list[LexiconMetadata] = Field(..., description="List of available lexicons")


class LexiconDetailResponse(BaseModel):
    """
    Response schema for GET /lexicons/{lexicon_id} endpoint.

    Returns metadata for a single lexicon.
    """
    lexicon_id: str = Field(..., description="Unique identifier for the lexicon")
    term_count: int = Field(..., description="Number of active terms in the lexicon")
    last_updated: datetime = Field(..., description="Timestamp of most recent term modification")
    description: Optional[str] = Field(None, description="Human-readable description of the lexicon")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
