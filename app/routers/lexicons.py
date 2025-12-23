"""
API endpoints for lexicon import/export operations.

Provides REST endpoints to import terms from JSON/CSV files and export
terms in JSON/CSV formats.
"""

import logging
from datetime import datetime
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
    summary="Import lexicon terms from file"
)
async def import_lexicon_terms(
    lexicon_id: str,
    file: UploadFile = File(..., description="JSON or CSV file containing lexicon terms"),
    db: Session = Depends(get_db),
    api_key=Depends(get_api_key)
):
    """
    Import lexicon terms from an uploaded file.

    Validates the file format, checks for duplicates and conflicts,
    and imports all valid terms in an atomic transaction.
    """
    logger.info(f"Import request for lexicon '{lexicon_id}' with file '{file.filename}'")

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
    summary="Export lexicon terms to file"
)
async def export_lexicon_terms(
    lexicon_id: str,
    format: ExportFormat = Query(
        ExportFormat.JSON,
        description="Export format: 'json' or 'csv'"
    ),
    db: Session = Depends(get_db),
    api_key=Depends(get_api_key)
):
    """
    Export all active lexicon terms in the specified format.

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
