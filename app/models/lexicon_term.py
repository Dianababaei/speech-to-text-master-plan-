"""
Lexicon Term Model

This module defines the SQLAlchemy model for domain-specific terminology mappings.

Table: lexicon_terms
Purpose: Store domain-specific terminology mappings (e.g., radiology terms) used 
         in post-processing transcriptions

Fields:
- id: Unique identifier for each lexicon term record (UUID)
- lexicon_id: Domain identifier (e.g., 'radiology', 'cardiology', 'general')
- term: Original term to match during post-processing (e.g., "CT scan")
- replacement: Corrected/standardized term to replace the original
- created_at: Timestamp of term creation (auto-set)
- updated_at: Timestamp of last modification (auto-updated)
- is_active: Flag to enable/disable terms without deletion (soft delete)

Indexes:
- Composite index on (lexicon_id, term) for fast lookups during post-processing
- Index on lexicon_id for filtering by lexicon
- Index on is_active for querying active terms only

Design Considerations:
- Schema supports future versioning: timestamps track when terms were added/modified
- Soft delete via is_active flag preserves history
- Flat key-value structure (term → replacement) as specified in requirements
- No unique constraint on term alone (same term can exist in different lexicons)
- Supports multiple active terms per lexicon (no uniqueness constraint enforced at DB level)
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

# Import Base from api_key module to ensure all models share the same Base
from app.models.api_key import Base


class LexiconTerm(Base):
    """
    SQLAlchemy model for domain-specific terminology mappings.
    
    This model stores term replacements used during post-processing of
    transcriptions to standardize medical/technical terminology.
    """
    
    __tablename__ = "lexicon_terms"
    
    # Primary key - UUID for distributed system compatibility
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Unique identifier for the lexicon term record"
    )
    
    # Lexicon domain identifier
    lexicon_id = Column(
        String(100),
        nullable=False,
        comment="Domain identifier (e.g., 'radiology', 'cardiology', 'general')"
    )
    
    # Original term to match
    term = Column(
        String(255),
        nullable=False,
        comment="Original term to match during post-processing"
    )
    
    # Replacement/corrected term
    replacement = Column(
        String(255),
        nullable=False,
        comment="Corrected/standardized term to replace the original"
    )
    
    # Active status for soft delete
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Flag to enable/disable the term without deletion (soft delete)"
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
    
    # Table-level constraints and indexes
    __table_args__ = (
        # Composite index on (lexicon_id, term) for fast lookups during post-processing
        Index('ix_lexicon_terms_lexicon_id_term', 'lexicon_id', 'term'),
        
        # Index on lexicon_id for filtering by lexicon
        Index('ix_lexicon_terms_lexicon_id', 'lexicon_id'),
        
        # Index on is_active for querying active terms only
        Index('ix_lexicon_terms_is_active', 'is_active'),
        
        # Table comment
        {'comment': 'Stores domain-specific terminology mappings for post-processing transcriptions'}
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
            f"is_active={self.is_active}, "
            f"created_at={self.created_at})>"
        )
