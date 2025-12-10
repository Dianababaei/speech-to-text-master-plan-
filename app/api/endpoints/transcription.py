"""
Audio upload and job submission endpoints.
"""
import os
import uuid
from pathlib import Path
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from rq import Queue

from app.schemas.jobs import JobCreateResponse, JobStatus
from app.models.job import Job
from app.database import get_db
from app.config.settings import get_settings
from app.redis_client import redis_client
from app.dependencies.auth import get_api_key_id
from app.workers.transcription_worker import process_transcription_job

router = APIRouter(prefix="/jobs", tags=["jobs"])
settings = get_settings()


def save_audio_file(upload_file: UploadFile) -> tuple[str, int, str]:
    """
    Save uploaded audio file to storage.

    Args:
        upload_file: Uploaded file from FastAPI

    Returns:
        Tuple of (file_path, file_size, audio_format)

    Raises:
        HTTPException: If file save fails
    """
    # Ensure storage directory exists
    storage_path = Path(settings.AUDIO_STORAGE_PATH)
    storage_path.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    file_extension = Path(upload_file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = storage_path / unique_filename

    try:
        # Write file to disk
        with open(file_path, "wb") as f:
            content = upload_file.file.read()
            f.write(content)
            file_size = len(content)

        # Determine audio format
        audio_format = file_extension.lstrip(".")

        return str(file_path), file_size, audio_format

    except Exception as e:
        # Clean up partial file if it exists
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save audio file: {str(e)}"
        )


@router.post(
    "/",
    response_model=JobCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload audio and create transcription job",
    description="Upload an audio file and submit it for transcription processing"
)
async def create_transcription_job(
    audio_file: Annotated[UploadFile, File(description="Audio file to transcribe")],
    language: Annotated[Optional[str], Form(description="Language code (e.g., 'en', 'es')")] = None,
    db: Annotated[Session, Depends(get_db)] = None,
    api_key_id: Annotated[int, Depends(get_api_key_id)] = None
) -> JobCreateResponse:
    """
    Upload an audio file and create a transcription job.

    The job will be queued for processing by a background worker.

    **Form Data:**
    - **audio_file**: Audio file (wav, mp3, m4a, etc.)
    - **language**: Optional language code for transcription

    **Authentication:**
    - Requires valid API key in X-API-Key header

    **Response:**
    - Returns job ID and initial status (pending)
    """
    # Validate file type
    allowed_extensions = {".wav", ".mp3", ".m4a", ".mp4", ".mpeg", ".mpga", ".webm"}
    file_extension = Path(audio_file.filename).suffix.lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_extension}. Allowed types: {', '.join(allowed_extensions)}"
        )

    # Save audio file
    try:
        file_path, file_size, audio_format = save_audio_file(audio_file)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing upload: {str(e)}"
        )

    # Create job record in database
    job_id = str(uuid.uuid4())

    try:
        job = Job(
            job_id=job_id,
            status=JobStatus.PENDING.value,
            audio_filename=audio_file.filename,
            audio_format=audio_format,
            audio_size_bytes=file_size,
            audio_storage_path=file_path,
            language=language,
            model_name=settings.OPENAI_MODEL,
            api_key_id=api_key_id
        )

        db.add(job)
        db.commit()
        db.refresh(job)

    except Exception as e:
        # Clean up audio file if database insert fails
        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}"
        )

    # Enqueue job for processing
    try:
        queue = Queue('transcription', connection=redis_client)
        queue.enqueue(
            process_transcription_job,
            job_id,
            job_timeout='10m'
        )
    except Exception as e:
        # Job created but not queued - mark as failed
        job.status = JobStatus.FAILED.value
        job.error_message = f"Failed to queue job: {str(e)}"
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Job created but failed to queue for processing: {str(e)}"
        )

    return JobCreateResponse(
        job_id=job.job_id,
        status=JobStatus.PENDING,
        created_at=job.created_at
    )
