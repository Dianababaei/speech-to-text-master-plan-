"""
Lexicon Models

This module defines SQLAlchemy models and Pydantic schemas for lexicon management.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field

Base = declarative_base()


class LexiconTerm(Base):
    """
    SQLAlchemy model for lexicon terms.
    
    Maps to the lexicon_terms table in the database.
    """
    __tablename__ = "lexicon_terms"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    term = Column(String(255), nullable=False, unique=True, comment='The lexicon term')
    normalized_term = Column(String(255), nullable=False, comment='Normalized/lowercased version for matching')
    category = Column(String(100), nullable=True, comment='Category (e.g., drug, brand, medical)')
    lexicon_id = Column(String(100), nullable=True, index=True, comment='Lexicon identifier (e.g., radiology, cardiology)')
    language = Column(String(10), nullable=True, comment='ISO language code')
    frequency = Column(Integer, nullable=False, default=0, server_default='0', comment='Usage frequency counter')
    confidence_boost = Column(Float, nullable=True, comment='Confidence boost factor for this term')
    alternatives = Column(JSONB, nullable=True, comment='Alternative spellings or variations')
    metadata = Column(JSONB, nullable=True, comment='Additional metadata')
    source = Column(String(100), nullable=True, comment='Source of the term')
    is_active = Column(Boolean, nullable=False, default=True, server_default='true')
    created_at = Column(DateTime(timezone=True), nullable=False, server_default='CURRENT_TIMESTAMP')
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default='CURRENT_TIMESTAMP')
    created_by = Column(String(100), nullable=True, comment='User or system that created the term')
    
    def __repr__(self):
        return f"<LexiconTerm(id={self.id}, term='{self.term}', lexicon_id='{self.lexicon_id}')>"


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
