"""
Lexicon Term Model

This module defines the SQLAlchemy model for lexicon terms management.

Table: lexicon_terms
Purpose: Store domain-specific terms and their replacements for transcription correction

Fields:
- id: Unique identifier for each term
- lexicon_id: Identifier for the lexicon (e.g., 'radiology', 'cardiology', 'general')
- term: The term to match in transcriptions
- normalized_term: Lowercased version for case-insensitive matching
- replacement: The corrected/replacement term
- category: Optional category for the term
- language: ISO language code
- is_active: Flag for soft delete
- created_at: Timestamp of creation
- updated_at: Timestamp of last modification
- created_by: User who created the term
"""

from datetime import datetime
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
        comment="ISO language code (e.g., en, es, zh)"
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
    
    metadata = Column(
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
