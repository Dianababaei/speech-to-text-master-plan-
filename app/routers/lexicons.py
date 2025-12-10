"""
API endpoints for lexicon import/export operations.

Provides REST endpoints to import terms from JSON/CSV files and export
terms in JSON/CSV formats.
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import (
    APIRouter, 
    Depends, 
    File, 
    UploadFile, 
    HTTPException, 
    status,
    Query
)
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth import get_api_key
from app.database import get_db
from app.schemas.lexicons import (
    ImportSummaryResponse,
    ExportFormat,
    ErrorDetail
)
from app.services.lexicon_service import (
    validate_terms_for_import,
    import_terms_to_database,
    export_terms_from_database
)
from app.utils.file_parsers import (
    validate_file_size,
    parse_json_file,
    parse_csv_file,
    generate_json_export,
    generate_csv_export
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/lexicons",
    tags=["Lexicons"],
    dependencies=[Depends(get_api_key)]  # Require authentication for all endpoints
)


@router.post(
    "/{lexicon_id}/import",
    response_model=ImportSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Import lexicon terms from file",
    description="""
    Import lexicon terms from a JSON or CSV file.
    
    **Supported Formats:**
    - **JSON**: Array of objects with 'term' and 'replacement' fields
      ```json
      [
        {"term": "CT scan", "replacement": "computed tomography"},
        {"term": "MRI", "replacement": "magnetic resonance imaging"}
      ]
      ```
    - **CSV**: Two columns with header row (term, replacement)
      ```csv
      term,replacement
      CT scan,computed tomography
      MRI,magnetic resonance imaging
      ```
    
    **Validation:**
    - File size must not exceed 10MB
    - All terms must have non-empty term and replacement values
    - Duplicate terms within the file are skipped
    - Terms that already exist in the lexicon (case-insensitive) are skipped
    
    **Import Behavior:**
    - Import is atomic: all valid terms are imported or none (on error)
    - Skipped terms are reported in the response with reasons
    - Returns summary with counts of imported and skipped terms
    """,
    responses={
        200: {
            "description": "Import completed successfully",
            "model": ImportSummaryResponse
        },
        400: {
            "description": "Invalid file format or validation error",
            "model": ErrorDetail
        },
        401: {
            "description": "Missing or invalid API key",
            "model": ErrorDetail
        },
        413: {
            "description": "File size exceeds maximum (10MB)",
            "model": ErrorDetail
        }
    }
)
async def list_lexicons(
    db: Session = Depends(get_db)
) -> LexiconListResponse:
    """
    Get all available lexicons with metadata.
    
    Args:
        db: Database session (injected)
    
    Returns:
        LexiconListResponse: List of lexicons with metadata
    """
    try:
        logger.info("Fetching all lexicons")
        lexicons = get_all_lexicons(db, use_cache=True)
        
        logger.info(f"Returning {len(lexicons)} lexicons")
        return LexiconListResponse(lexicons=lexicons)
        
    except Exception as e:
        logger.error(f"Error fetching lexicons: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve lexicons"
from app.models.api_key import ApiKey
from app.schemas.lexicon import (
    TermCreate, 
    TermUpdate, 
    TermResponse, 
    TermListResponse
)
from app.services import lexicon_service
from app.services.lexicon_validator import validate_term
from app.services.lexicon_service import invalidate_lexicon_cache


router = APIRouter(
    prefix="/lexicons",
    tags=["lexicons"],
    dependencies=[Depends(get_api_key)]
)


def validate_lexicon_id(lexicon_id: str) -> str:
    """
    Validate lexicon_id format.
    
    Args:
        lexicon_id: The lexicon identifier to validate
    
    Returns:
        str: The validated lexicon_id
    
    Raises:
        HTTPException: If lexicon_id is invalid
    """
    # Alphanumeric and hyphens/underscores only, max 100 chars
    if not lexicon_id or len(lexicon_id) > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Lexicon ID must be between 1 and 100 characters"
        )
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', lexicon_id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Lexicon ID must contain only alphanumeric characters, hyphens, and underscores"
        )
    
    return lexicon_id


@router.post(
    "/{lexicon_id}/terms",
    response_model=TermResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add new term to lexicon",
    description="Create a new term in the specified lexicon with comprehensive validation"
)
async def create_term(
    lexicon_id: str = Path(..., description="Lexicon identifier (e.g., 'radiology', 'cardiology')"),
    term_data: TermCreate = ...,
async def import_lexicon_terms(
    lexicon_id: str,
    file: UploadFile = File(..., description="JSON or CSV file containing lexicon terms"),
    db: Session = Depends(get_db),
    api_key=Depends(get_api_key)
):
    """
    Import lexicon terms from an uploaded file.
    
    Validation includes:
    - Format validation (length limits, no empty strings)
    - Uniqueness check (case-insensitive)
    - Circular replacement detection
    - Conflict detection (overlapping terms)
    
    Returns the created term with ID and timestamps.
    Validates the file format, checks for duplicates and conflicts,
    and imports all valid terms in an atomic transaction.
    """
    logger.info(f"Import request for lexicon '{lexicon_id}' with file '{file.filename}'")
    
    # Comprehensive validation
    validation_result = validate_term(
        db=db,
        lexicon_id=lexicon_id,
        term=term_data.term,
        replacement=term_data.replacement,
        check_conflicts=True
    )
    
    # Check for validation errors
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=validation_result.to_error_detail("Term validation failed")
        )
    
    try:
        # Create term using service
        new_term = lexicon_service.create_term(db, lexicon_id, term_data)
        
        # Invalidate cache for this lexicon to ensure fresh data
        invalidate_lexicon_cache(lexicon_id)
        
        return new_term
    
    except ValueError as e:
        # Term already exists (shouldn't happen due to validation, but keep as safety net)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    # Validate file size
    await validate_file_size(file)
    
    # Determine file format and parse
    filename_lower = file.filename.lower() if file.filename else ""
    
    if filename_lower.endswith('.json'):
        terms = await parse_json_file(file)
    elif filename_lower.endswith('.csv'):
        terms = await parse_csv_file(file)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Please upload a .json or .csv file."
        )
    
    logger.info(f"Parsed {len(terms)} terms from file")
    
    # Validate terms for import (check duplicates and conflicts)
    valid_terms, skipped_terms = validate_terms_for_import(lexicon_id, terms, db)
    
    logger.info(f"Validation complete: {len(valid_terms)} valid, {len(skipped_terms)} skipped")
    
    # Import valid terms to database (atomic transaction)
    imported_count = 0
    errors = []
    
    if valid_terms:
        try:
            imported_count = import_terms_to_database(lexicon_id, valid_terms, db)
        except Exception as e:
            logger.error(f"Database error during import: {str(e)}")
            errors.append(f"Database error: {str(e)}")
    
    # Return summary
    return ImportSummaryResponse(
        imported=imported_count,
        skipped=len(skipped_terms),
        errors=errors,
        skipped_terms=skipped_terms
    )


@router.get(
    "/{lexicon_id}/export",
    summary="Export lexicon terms to file",
    description="""
    Export all active terms from a lexicon in JSON or CSV format.
    
    **Export Formats:**
    - **JSON** (default): Array of objects with 'term' and 'replacement' fields
    - **CSV**: Two columns with header row (term, replacement)
    
    **Query Parameters:**
    - `format`: Specify export format ('json' or 'csv', default: 'json')
    
    **Response:**
    - Sets appropriate Content-Type header (application/json or text/csv)
    - Sets Content-Disposition header for file download
    - Filename format: `{lexicon_id}_terms_{timestamp}.{json|csv}`
    """,
    responses={
        200: {
            "description": "Export successful",
            "content": {
                "application/json": {
                    "example": [
                        {"term": "CT scan", "replacement": "computed tomography"},
                        {"term": "MRI", "replacement": "magnetic resonance imaging"}
                    ]
                },
                "text/csv": {
                    "example": "term,replacement\nCT scan,computed tomography\nMRI,magnetic resonance imaging\n"
                }
            }
        },
        400: {
            "description": "Invalid format parameter",
            "model": ErrorDetail
        },
        401: {
            "description": "Missing or invalid API key",
            "model": ErrorDetail
        }
    }
)
async def export_lexicon_terms(
    lexicon_id: str,
    db: Session = Depends(get_db)
) -> LexiconDetailResponse:
    """
    Get metadata for a specific lexicon.
    
    Args:
        lexicon_id: Unique lexicon identifier (e.g., "radiology")
        db: Database session (injected)
    
    Returns:
        LexiconDetailResponse: Lexicon metadata
    
    Raises:
        HTTPException: 404 if lexicon not found or has no active terms
    """
    try:
        logger.info(f"Fetching lexicon: {lexicon_id}")
        lexicon = get_lexicon_by_id(db, lexicon_id, use_cache=True)
        
        if not lexicon:
            logger.warning(f"Lexicon not found: {lexicon_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lexicon '{lexicon_id}' not found or has no active terms"
            )
        
        logger.info(f"Returning lexicon {lexicon_id} with {lexicon.term_count} terms")
        return LexiconDetailResponse(
            lexicon_id=lexicon.lexicon_id,
            term_count=lexicon.term_count,
            last_updated=lexicon.last_updated,
            description=lexicon.description
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching lexicon {lexicon_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve lexicon '{lexicon_id}'"
    "/{lexicon_id}/terms/{term_id}",
    response_model=TermResponse,
    summary="Get specific term details",
    description="Retrieve full details of a specific term by ID"
)
async def get_term(
    lexicon_id: str = Path(..., description="Lexicon identifier"),
    term_id: int = Path(..., ge=1, description="Term ID"),
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key)
):
    """
    Get details of a specific term.
    
    - **lexicon_id**: Identifier for the lexicon
    - **term_id**: Unique identifier of the term
    
    Returns full term object including metadata.
    """
    # Validate lexicon_id format
    lexicon_id = validate_lexicon_id(lexicon_id)
    
    try:
        # Get term using service
        term = lexicon_service.get_term_by_id(db, lexicon_id, term_id)
        
        if not term:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Term with ID {term_id} not found in lexicon '{lexicon_id}'"
            )
        
        return term
    
    except HTTPException:
        raise
    
    except Exception as e:
        # Internal server error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve term: {str(e)}"
        )


@router.put(
    "/{lexicon_id}/terms/{term_id}",
    response_model=TermResponse,
    summary="Update existing term",
    description="Update term and replacement text with comprehensive validation"
)
async def update_term(
    lexicon_id: str = Path(..., description="Lexicon identifier"),
    term_id: int = Path(..., ge=1, description="Term ID"),
    term_data: TermUpdate = ...,
    format: ExportFormat = Query(
        ExportFormat.JSON, 
        description="Export format: 'json' or 'csv'"
    ),
    db: Session = Depends(get_db),
    api_key=Depends(get_api_key)
):
    """
    Export all active lexicon terms in the specified format.
    
    - **lexicon_id**: Identifier for the lexicon
    - **term_id**: Unique identifier of the term to update
    - **term**: Updated term text
    - **replacement**: Updated replacement text
    
    Validation includes:
    - Format validation (length limits, no empty strings)
    - Uniqueness check (case-insensitive, excluding current term)
    - Circular replacement detection
    - Conflict detection (overlapping terms)
    
    Returns the updated term with new timestamp.
    Returns a file download response with appropriate headers.
    """
    logger.info(f"Export request for lexicon '{lexicon_id}' in format '{format}'")
    
    # Get terms from database
    terms = export_terms_from_database(lexicon_id, db)
    
    # Generate timestamp for filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    # Generate export content and set headers based on format
    if format == ExportFormat.JSON:
        content = generate_json_export(terms)
        media_type = "application/json"
        filename = f"{lexicon_id}_terms_{timestamp}.json"
    else:  # CSV
        content = generate_csv_export(terms)
        media_type = "text/csv"
        filename = f"{lexicon_id}_terms_{timestamp}.csv"
    
    logger.info(f"Exported {len(terms)} terms from lexicon '{lexicon_id}'")
    
    # Return response with appropriate headers
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
