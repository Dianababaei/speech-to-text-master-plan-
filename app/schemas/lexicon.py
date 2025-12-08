"""
Lexicon Pydantic Schemas

This module defines the request and response schemas for lexicon term endpoints.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator


class TermCreate(BaseModel):
    """Schema for creating a new lexicon term."""
    
    term: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        description="The term to match in transcriptions"
    )
    replacement: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        description="The corrected/replacement term"
    )
    
    @validator('term', 'replacement')
    def validate_non_empty(cls, v):
        """Validate that strings are not just whitespace."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace only")
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "term": "atreal fibrillation",
                "replacement": "atrial fibrillation"
            }
        }


class TermUpdate(BaseModel):
    """Schema for updating an existing lexicon term."""
    
    term: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        description="The term to match in transcriptions"
    )
    replacement: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        description="The corrected/replacement term"
    )
    
    @validator('term', 'replacement')
    def validate_non_empty(cls, v):
        """Validate that strings are not just whitespace."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace only")
        return v.strip()
    
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
