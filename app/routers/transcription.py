from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Header, Query
from sqlalchemy.orm import Session
from typing import Optional
from pathlib import Path
import uuid
import os
from datetime import datetime

from app.database import get_db
from app.models import Job, APIKey
from app.auth import get_api_key
from app.config import settings


router = APIRouter(prefix="", tags=["transcription"])


def get_file_extension(filename: str) -> str:
    """Extract file extension from filename."""
    return Path(filename).suffix.lstrip('.').lower()


def validate_file_format(filename: str, content_type: str) -> tuple[bool, Optional[str]]:
    """
    Validate file format based on extension and MIME type.
    Returns (is_valid, error_message).
    """
    extension = get_file_extension(filename)
    
    # Check extension
    if extension not in settings.allowed_audio_formats:
        return False, f"Invalid file format. Allowed formats: {', '.join(settings.allowed_audio_formats).upper()}"
    
    # Check MIME type (if provided)
    if content_type and content_type not in settings.allowed_mime_types:
        return False, f"Invalid MIME type: {content_type}. Expected audio file."
    
    return True, None


async def validate_file_size(file: UploadFile) -> tuple[bool, Optional[str]]:
    """
    Validate file size against configured limit.
    Returns (is_valid, error_message).
    """
    max_size_bytes = settings.max_file_size_mb * 1024 * 1024
    
    # Read file to check size
    content = await file.read()
    file_size = len(content)
    
    # Reset file pointer for later reading
    await file.seek(0)
    
    if file_size > max_size_bytes:
        return False, f"File size ({file_size / 1024 / 1024:.2f}MB) exceeds maximum allowed size ({settings.max_file_size_mb}MB)"
    
    if file_size == 0:
        return False, "File is empty"
    
    return True, None


def generate_unique_filename(original_filename: str) -> str:
    """Generate unique filename with UUID prefix and original extension."""
    extension = get_file_extension(original_filename)
    unique_id = str(uuid.uuid4())
    return f"{unique_id}.{extension}"


async def save_audio_file(file: UploadFile, filename: str) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Save uploaded file to storage directory.
    Returns (success, file_path, error_message).
    """
    try:
        # Ensure storage directory exists
        storage_path = settings.audio_storage_path
        storage_path.mkdir(parents=True, exist_ok=True)
        
        # Full file path
        file_path = storage_path / filename
        
        # Save file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Return relative path for portability
        relative_path = str(Path("audio_storage") / filename)
        return True, relative_path, None
        
    except PermissionError:
        return False, None, "Permission denied: Cannot write to storage directory"
    except OSError as e:
        if "No space left on device" in str(e):
            return False, None, "Storage is full: No space left on device"
        return False, None, f"Storage error: {str(e)}"
    except Exception as e:
        return False, None, f"Failed to save file: {str(e)}"


@router.post("/transcribe", status_code=status.HTTP_202_ACCEPTED)
async def submit_transcription(
    audio: UploadFile = File(..., description="Audio file to transcribe (WAV, MP3, or M4A)"),
    x_lexicon_id: Optional[str] = Header(None, description="Lexicon ID for domain-specific transcription"),
    lexicon: Optional[str] = Query(None, description="Lexicon ID (alternative to header)"),
    api_key: APIKey = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    """
    Submit an audio file for asynchronous transcription.
    
    **Request:**
    - File: audio file (multipart/form-data)
    - Header or Query: lexicon_id (optional, defaults to 'radiology')
    
    **Response:**
    - 202 Accepted: Job created successfully
    - Returns job_id, status, and created_at timestamp
    
    **Validation:**
    - File format must be WAV, MP3, or M4A
    - File size must not exceed configured limit (default 10MB)
    - Valid API key required (X-API-Key header)
    """
    
    # Extract lexicon_id from header or query param (header takes precedence)
    lexicon_id = x_lexicon_id or lexicon or settings.default_lexicon
    
    # Validate file format
    is_valid_format, format_error = validate_file_format(audio.filename, audio.content_type)
    if not is_valid_format:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=format_error
        )
    
    # Validate file size
    is_valid_size, size_error = await validate_file_size(audio)
    if not is_valid_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=size_error
        )
    
    # Generate unique filename
    unique_filename = generate_unique_filename(audio.filename)
    
    # Save file to storage
    success, file_path, storage_error = await save_audio_file(audio, unique_filename)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=storage_error
        )
    
    # Extract audio format
    audio_format = get_file_extension(audio.filename)
    
    # Create job record in database
    try:
        job = Job(
            id=str(uuid.uuid4()),
            status="pending",
            lexicon_id=lexicon_id,
            audio_file_path=file_path,
            audio_format=audio_format,
            api_key_id=api_key.id
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
    except Exception as e:
        # Clean up file if database operation fails
        try:
            file_full_path = settings.audio_storage_path / unique_filename
            if file_full_path.exists():
                file_full_path.unlink()
        except:
            pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: Failed to create job record"
        )
    
    # Return job information (202 Accepted - async processing)
    return {
        "job_id": job.id,
        "status": job.status,
        "created_at": job.created_at.isoformat() + "Z"
    }
