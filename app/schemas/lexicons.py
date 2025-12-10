"""
Pydantic schemas for lexicon import/export endpoints.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ExportFormat(str, Enum):
    """Supported export formats."""
    JSON = "json"
    CSV = "csv"


class LexiconTermBase(BaseModel):
    """Base schema for a lexicon term."""
    term: str = Field(..., description="The original term to match")
    replacement: str = Field(..., description="The replacement/corrected term")


class LexiconTermImport(LexiconTermBase):
    """Schema for importing a lexicon term."""
    pass


class SkippedTerm(BaseModel):
    """Schema for a skipped term during import."""
    term: str = Field(..., description="The term that was skipped")
    replacement: str = Field(..., description="The replacement that was skipped")
    reason: str = Field(..., description="Reason why the term was skipped")


class ImportSummaryResponse(BaseModel):
    """
    Response schema for lexicon import operation.
    
    Provides detailed summary of the import including count of imported,
    skipped, and any errors encountered.
    """
    imported: int = Field(..., description="Number of terms successfully imported")
    skipped: int = Field(..., description="Number of terms skipped (duplicates)")
    errors: List[str] = Field(default_factory=list, description="List of error messages")
    skipped_terms: List[SkippedTerm] = Field(
        default_factory=list, 
        description="Details of skipped terms"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "examples": [
                {
                    "imported": 150,
                    "skipped": 5,
                    "errors": [],
                    "skipped_terms": [
                        {
                            "term": "CT scan",
                            "replacement": "computed tomography",
                            "reason": "Duplicate term already exists in lexicon"
                        }
                    ]
                }
            ]
        }


class LexiconTermExport(LexiconTermBase):
    """Schema for exporting a lexicon term."""
    pass


class ErrorDetail(BaseModel):
    """Schema for error details."""
    detail: str = Field(..., description="Error message")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "examples": [
                {
                    "detail": "File size exceeds maximum allowed size"
                },
                {
                    "detail": "Invalid JSON format: Expecting value: line 1 column 1 (char 0)"
                }
            ]
        }
