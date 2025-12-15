"""
Job management endpoints for the transcription API.

Note: To ensure invalid UUID formats return 400 instead of 422, register the
validation_exception_handler from app.api.exceptions in your FastAPI app:

    from fastapi.exceptions import RequestValidationError
    from app.api.exceptions import validation_exception_handler
    
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Header, Path, status
from sqlalchemy.orm import Session

from app.schemas.jobs import JobStatusResponse, JobStatus
from app.schemas.errors import ERROR_RESPONSES
from app.database import get_db
from app.models import Job
from app.auth import get_api_key
from app.models import APIKey


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get job status",
    description="Retrieve the current status and results of a transcription job",
    responses={
        200: {
            "description": "Job status retrieved successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "completed": {
                            "summary": "Completed job",
                            "value": {
                                "job_id": "123e4567-e89b-12d3-a456-426614174000",
                                "status": "completed",
                                "created_at": "2024-01-15T10:30:00Z",
                                "completed_at": "2024-01-15T10:31:30Z",
                                "original_text": "Hello world this is a test transcription",
                                "processed_text": "Hello world, this is a test transcription.",
                                "error_message": None
                            }
                        },
                        "processing": {
                            "summary": "Job in progress",
                            "value": {
                                "job_id": "223e4567-e89b-12d3-a456-426614174001",
                                "status": "processing",
                                "created_at": "2024-01-15T10:32:00Z",
                                "completed_at": None,
                                "original_text": None,
                                "processed_text": None,
                                "error_message": None
                            }
                        },
                        "pending": {
                            "summary": "Pending job",
                            "value": {
                                "job_id": "323e4567-e89b-12d3-a456-426614174002",
                                "status": "pending",
                                "created_at": "2024-01-15T10:33:00Z",
                                "completed_at": None,
                                "original_text": None,
                                "processed_text": None,
                                "error_message": None
                            }
                        },
                        "failed": {
                            "summary": "Failed job",
                            "value": {
                                "job_id": "423e4567-e89b-12d3-a456-426614174003",
                                "status": "failed",
                                "created_at": "2024-01-15T10:34:00Z",
                                "completed_at": "2024-01-15T10:34:15Z",
                                "original_text": None,
                                "processed_text": None,
                                "error_message": "Audio file format not supported"
                            }
                        }
                    }
                }
            }
        },
        **{k: v for k, v in ERROR_RESPONSES.items() if k in [400, 401, 404, 500]}
    }
)
async def get_job_status(
    job_id: Annotated[UUID, Path(description="Unique identifier of the job to retrieve")],
    db: Annotated[Session, Depends(get_db)],
    api_key: Annotated[APIKey, Depends(get_api_key)]
) -> JobStatusResponse:
    """
    Retrieve the status and results of a transcription job.
    
    This endpoint allows clients to poll for transcription progress and results.
    Clients can only access jobs associated with their API key.
    
    **Path Parameters:**
    - **job_id**: UUID of the job to retrieve
    
    **Authentication:**
    - Requires valid API key in X-API-Key header
    
    **Response:**
    - Returns job status, timestamps, and results (if available)
    - `original_text` and `processed_text` are null for pending/processing jobs
    - `error_message` is populated only for failed jobs
    
    **Security:**
    - Clients can only access jobs created with their API key
    - Returns 404 for non-existent jobs or jobs belonging to other API keys
    """
    # Validate UUID format (handled automatically by FastAPI/Pydantic)
    # If job_id is not a valid UUID, FastAPI will return 422 Unprocessable Entity
    # We need to catch this and return 400 instead as per requirements
    
    # Query the job by job_id AND api_key_id to ensure authorization
    job = db.query(Job).filter(
        Job.id == str(job_id),
        Job.api_key_id == api_key.id
    ).first()
    
    # If job not found or doesn't belong to this API key, return 404
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Map database model to response schema with proper null handling
    # For pending/processing jobs, original_text and processed_text should be null
    # For failed jobs, error_message should be populated
    original_text = None
    processed_text = None
    if job.status in [JobStatus.COMPLETED.value]:
        original_text = job.original_text
        processed_text = job.processed_text
    
    error_message = None
    if job.status == JobStatus.FAILED.value:
        error_message = job.error_message
    
    return JobStatusResponse(
        job_id=UUID(job.id),
        status=job.status,
        created_at=job.created_at,
        completed_at=job.completed_at,
        original_text=original_text,
        processed_text=processed_text,
        error_message=error_message
    )
