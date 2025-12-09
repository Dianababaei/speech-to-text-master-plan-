"""
Lexicon Pydantic Schemas

This module defines the request and response schemas for lexicon term endpoints.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator


class TermCreate(BaseModel):
    """
    Schema for creating a new lexicon term.
    
    Note: Additional validation (uniqueness, circular references, conflicts)
    is performed by the lexicon_validator service after schema validation.
    """
    
    term: str = Field(
        ..., 
        min_length=1, 
        max_length=200,  # Updated to match validator MAX_TERM_LENGTH
        description="The term to match in transcriptions (1-200 characters)"
    )
    replacement: str = Field(
        ..., 
        min_length=1, 
        max_length=500,  # Updated to match validator MAX_REPLACEMENT_LENGTH
        description="The corrected/replacement term (1-500 characters)"
    )
    
    @validator('term', 'replacement')
    def validate_non_empty(cls, v, field):
        """Validate that strings are not just whitespace."""
        if not v or not v.strip():
            raise ValueError(f"{field.name.capitalize()} cannot be empty or whitespace only")
        # Return trimmed value
        trimmed = v.strip()
        if v != trimmed:
            # Note: This trimming is informational; the validator service will also warn
            pass
        return trimmed
    
    class Config:
        schema_extra = {
            "example": {
                "term": "atreal fibrillation",
                "replacement": "atrial fibrillation"
            }
        }


class TermUpdate(BaseModel):
    """
    Schema for updating an existing lexicon term.
    
    Note: Additional validation (uniqueness, circular references, conflicts)
    is performed by the lexicon_validator service after schema validation.
    """
    
    term: str = Field(
        ..., 
        min_length=1, 
        max_length=200,  # Updated to match validator MAX_TERM_LENGTH
        description="The term to match in transcriptions (1-200 characters)"
    )
    replacement: str = Field(
        ..., 
        min_length=1, 
        max_length=500,  # Updated to match validator MAX_REPLACEMENT_LENGTH
        description="The corrected/replacement term (1-500 characters)"
    )
    
    @validator('term', 'replacement')
    def validate_non_empty(cls, v, field):
        """Validate that strings are not just whitespace."""
        if not v or not v.strip():
            raise ValueError(f"{field.name.capitalize()} cannot be empty or whitespace only")
        # Return trimmed value
        trimmed = v.strip()
        if v != trimmed:
            # Note: This trimming is informational; the validator service will also warn
            pass
        return trimmed
    
    class Config:
        schema_extra = {
            "example": {
                "term": "atrial fibrillation",
                "replacement": "atrial fibrillation"
            }
        }


class TermResponse(BaseModel):
    """Schema for lexicon term response."""
    
    id: int = Field(..., description="Unique identifier for the term")
    lexicon_id: str = Field(..., description="Lexicon identifier")
    term: str = Field(..., description="The term to match")
    replacement: str = Field(..., description="The replacement term")
    is_active: bool = Field(..., description="Whether the term is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "lexicon_id": "radiology",
                "term": "atreal fibrillation",
                "replacement": "atrial fibrillation",
                "is_active": True,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z"
            }
        }


class TermListResponse(BaseModel):
    """Schema for paginated list of lexicon terms."""
    
    items: List[TermResponse] = Field(..., description="List of terms")
    total: int = Field(..., description="Total number of active terms in the lexicon")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    
    class Config:
        schema_extra = {
            "example": {
                "items": [
                    {
                        "id": 1,
                        "lexicon_id": "radiology",
                        "term": "atreal fibrillation",
                        "replacement": "atrial fibrillation",
                        "is_active": True,
                        "created_at": "2024-01-01T12:00:00Z",
                        "updated_at": "2024-01-01T12:00:00Z"
                    }
                ],
                "total": 100,
                "page": 1,
                "limit": 50
            }
        }
