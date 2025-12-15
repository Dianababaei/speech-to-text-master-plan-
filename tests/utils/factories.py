"""
Test data factories for creating realistic test objects.

Provides factory functions to generate test data for:
- Jobs (in various states)
- Feedback records
- API keys
- Lexicon terms
- Random test data (IDs, timestamps, etc.)
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import uuid
import random
import string
import hashlib


# Random data generators
def generate_job_id() -> str:
    """Generate a random job ID (UUID)."""
    return str(uuid.uuid4())


def generate_api_key() -> str:
    """Generate a random API key."""
    return f"sk-{''.join(random.choices(string.ascii_letters + string.digits, k=48))}"


def generate_hash(value: str) -> str:
    """
    Generate a simple hash for a value.
    
    For testing purposes, uses SHA256. In production, use bcrypt/argon2.
    """
    return hashlib.sha256(value.encode()).hexdigest()


def generate_timestamp(days_ago: int = 0, hours_ago: int = 0) -> datetime:
    """
    Generate a timestamp relative to now.
    
    Args:
        days_ago: Number of days in the past
        hours_ago: Number of hours in the past
    
    Returns:
        datetime object
    """
    now = datetime.utcnow()
    delta = timedelta(days=days_ago, hours=hours_ago)
    return now - delta


def random_choice(items: List[Any]) -> Any:
    """Get a random item from a list."""
    return random.choice(items)


# Job factory functions
def create_job(
    job_id: Optional[str] = None,
    status: str = "pending",
    audio_filename: Optional[str] = None,
    audio_format: str = "mp3",
    transcription_text: Optional[str] = None,
    error_message: Optional[str] = None,
    language: str = "en",
    model_name: str = "whisper-1",
    api_key_id: Optional[int] = None,
    created_at: Optional[datetime] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a test job record.
    
    Args:
        job_id: Job UUID (generates if not provided)
        status: Job status (pending, processing, completed, failed)
        audio_filename: Original audio filename
        audio_format: Audio format (wav, mp3, m4a)
        transcription_text: Transcription result
        error_message: Error message for failed jobs
        language: Language code
        model_name: OpenAI model name
        api_key_id: API key ID
        created_at: Creation timestamp
        **kwargs: Additional fields
    
    Returns:
        Dict containing job data
    """
    if job_id is None:
        job_id = generate_job_id()
    
    if audio_filename is None:
        audio_filename = f"audio_{job_id[:8]}.{audio_format}"
    
    if created_at is None:
        created_at = datetime.utcnow()
    
    job_data = {
        "job_id": job_id,
        "status": status,
        "audio_filename": audio_filename,
        "audio_format": audio_format,
        "audio_duration": random.uniform(10.0, 300.0),
        "audio_size_bytes": random.randint(100000, 5000000),
        "audio_storage_path": f"/tmp/audio/{audio_filename}",
        "language": language,
        "model_name": model_name,
        "transcription_text": transcription_text,
        "error_message": error_message,
        "api_key_id": api_key_id,
        "created_at": created_at,
        "updated_at": created_at,
        "started_at": None,
        "completed_at": None,
        "processing_time_seconds": None,
        "lexicon_version": "v1",
        "metadata": {},
        "submitted_by": "test_user",
    }
    
    # Set timestamps based on status
    if status in ["processing", "completed", "failed"]:
        job_data["started_at"] = created_at + timedelta(seconds=5)
    
    if status in ["completed", "failed"]:
        job_data["completed_at"] = created_at + timedelta(seconds=30)
        job_data["processing_time_seconds"] = 25.0
    
    # Add sample transcription for completed jobs
    if status == "completed" and transcription_text is None:
        job_data["transcription_text"] = "Sample transcription text for testing purposes."
    
    # Merge with any additional kwargs
    job_data.update(kwargs)
    
    return job_data


def create_pending_job(**kwargs) -> Dict[str, Any]:
    """Create a pending job."""
    return create_job(status="pending", **kwargs)


def create_processing_job(**kwargs) -> Dict[str, Any]:
    """Create a processing job."""
    return create_job(status="processing", **kwargs)


def create_completed_job(**kwargs) -> Dict[str, Any]:
    """Create a completed job."""
    return create_job(
        status="completed",
        transcription_text="This is a completed transcription with sample medical text.",
        **kwargs
    )


def create_failed_job(**kwargs) -> Dict[str, Any]:
    """Create a failed job."""
    return create_job(
        status="failed",
        error_message="OpenAI API error: Rate limit exceeded",
        **kwargs
    )


# Feedback factory functions
def create_feedback(
    job_id: int,
    original_text: str = "Original transcription text",
    corrected_text: str = "Corrected transcription text",
    status: str = "pending",
    reviewer: Optional[str] = None,
    feedback_type: str = "correction",
    is_processed: bool = False,
    created_at: Optional[datetime] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a test feedback record.
    
    Args:
        job_id: Job ID (internal integer ID)
        original_text: Original transcription
        corrected_text: Corrected transcription
        status: Feedback status (pending, approved, rejected)
        reviewer: Reviewer username
        feedback_type: Type (correction, validation, quality_issue)
        is_processed: Whether processed
        created_at: Creation timestamp
        **kwargs: Additional fields
    
    Returns:
        Dict containing feedback data (minimal required fields only)
    """
    if created_at is None:
        created_at = datetime.utcnow()
    
    # Calculate diff metrics
    edit_distance = abs(len(original_text) - len(corrected_text))
    accuracy_score = 1.0 - (edit_distance / max(len(original_text), 1))
    
    # Only include essential fields to avoid conflicts with duplicate definitions
    feedback_data = {
        "job_id": job_id,
        "original_text": original_text,
        "corrected_text": corrected_text,
        "status": status,
        "reviewer": reviewer or "test_reviewer",
        "feedback_type": feedback_type,
        "is_processed": is_processed,
        "edit_distance": edit_distance,
        "accuracy_score": accuracy_score,
        "review_time_seconds": random.randint(60, 600),
        "review_notes": "Test review notes",
        "confidence": random.uniform(0.7, 1.0),
        "frequency": 1,
        "created_by": "test_user",
        "lexicon_id": "radiology",
    }
    
    # Add optional fields if needed
    if "diff_data" not in kwargs:
        feedback_data["diff_data"] = {"additions": [], "deletions": [], "changes": []}
    if "extracted_terms" not in kwargs:
        feedback_data["extracted_terms"] = []
    if "metadata" not in kwargs:
        feedback_data["metadata"] = {}
    
    if is_processed and "processed_at" not in kwargs:
        feedback_data["processed_at"] = created_at + timedelta(hours=1)
    
    feedback_data.update(kwargs)
    return feedback_data


def create_pending_feedback(**kwargs) -> Dict[str, Any]:
    """Create pending feedback."""
    return create_feedback(status="pending", **kwargs)


def create_approved_feedback(**kwargs) -> Dict[str, Any]:
    """Create approved feedback."""
    return create_feedback(status="approved", is_processed=True, **kwargs)


def create_rejected_feedback(**kwargs) -> Dict[str, Any]:
    """Create rejected feedback."""
    return create_feedback(status="rejected", **kwargs)


# API Key factory functions
def create_api_key(
    key_hash: Optional[str] = None,
    project_name: str = "Test Project",
    description: Optional[str] = None,
    is_active: bool = True,
    is_admin: bool = False,
    rate_limit: int = 100,
    created_at: Optional[datetime] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a test API key record.
    
    Args:
        key_hash: Hashed API key (generates if not provided)
        project_name: Project name
        description: Project description
        is_active: Whether key is active
        is_admin: Whether key has admin privileges
        rate_limit: Rate limit (requests per minute)
        created_at: Creation timestamp
        **kwargs: Additional fields
    
    Returns:
        Dict containing API key data
    """
    if key_hash is None:
        test_key = generate_api_key()
        key_hash = generate_hash(test_key)
    
    if created_at is None:
        created_at = datetime.utcnow()
    
    api_key_data = {
        "id": uuid.uuid4(),
        "key_hash": key_hash,
        "project_name": project_name,
        "description": description or f"Test API key for {project_name}",
        "is_active": is_active,
        "is_admin": is_admin,
        "rate_limit": rate_limit,
        "created_at": created_at,
        "updated_at": created_at,
        "last_used_at": None
    }
    
    api_key_data.update(kwargs)
    return api_key_data


def create_active_api_key(**kwargs) -> Dict[str, Any]:
    """Create an active API key."""
    return create_api_key(is_active=True, **kwargs)


def create_inactive_api_key(**kwargs) -> Dict[str, Any]:
    """Create an inactive API key."""
    return create_api_key(is_active=False, **kwargs)


def create_admin_api_key(**kwargs) -> Dict[str, Any]:
    """Create an admin API key."""
    return create_api_key(is_admin=True, rate_limit=1000, **kwargs)


def create_rate_limited_api_key(limit: int = 10, **kwargs) -> Dict[str, Any]:
    """Create a rate-limited API key."""
    return create_api_key(rate_limit=limit, **kwargs)


# Lexicon Term factory functions
def create_lexicon_term(
    lexicon_id: str = "radiology",
    term: str = "mri",
    replacement: str = "MRI",
    is_active: bool = True,
    created_at: Optional[datetime] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a test lexicon term record.
    
    Args:
        lexicon_id: Lexicon identifier (radiology, cardiology, general)
        term: Original term
        replacement: Replacement term
        is_active: Whether term is active
        created_at: Creation timestamp
        **kwargs: Additional fields
    
    Returns:
        Dict containing lexicon term data
    """
    if created_at is None:
        created_at = datetime.utcnow()
    
    term_data = {
        "id": uuid.uuid4(),
        "lexicon_id": lexicon_id,
        "term": term,
        "replacement": replacement,
        "is_active": is_active,
        "created_at": created_at,
        "updated_at": created_at
    }
    
    term_data.update(kwargs)
    return term_data


def create_radiology_term(term: str, replacement: str, **kwargs) -> Dict[str, Any]:
    """Create a radiology lexicon term."""
    return create_lexicon_term(lexicon_id="radiology", term=term, replacement=replacement, **kwargs)


def create_cardiology_term(term: str, replacement: str, **kwargs) -> Dict[str, Any]:
    """Create a cardiology lexicon term."""
    return create_lexicon_term(lexicon_id="cardiology", term=term, replacement=replacement, **kwargs)


def create_general_term(term: str, replacement: str, **kwargs) -> Dict[str, Any]:
    """Create a general lexicon term."""
    return create_lexicon_term(lexicon_id="general", term=term, replacement=replacement, **kwargs)


# Batch creation helpers
def create_multiple_jobs(count: int, **kwargs) -> List[Dict[str, Any]]:
    """Create multiple jobs with varying statuses."""
    jobs = []
    statuses = ["pending", "processing", "completed", "failed"]
    
    for i in range(count):
        status = statuses[i % len(statuses)]
        job = create_job(status=status, **kwargs)
        jobs.append(job)
    
    return jobs


def create_multiple_feedback(job_ids: List[int], **kwargs) -> List[Dict[str, Any]]:
    """Create multiple feedback records."""
    feedbacks = []
    statuses = ["pending", "approved", "rejected"]
    
    for i, job_id in enumerate(job_ids):
        status = statuses[i % len(statuses)]
        feedback = create_feedback(job_id=job_id, status=status, **kwargs)
        feedbacks.append(feedback)
    
    return feedbacks


def create_lexicon_terms_batch(lexicon_id: str, terms: List[tuple]) -> List[Dict[str, Any]]:
    """
    Create multiple lexicon terms.
    
    Args:
        lexicon_id: Lexicon identifier
        terms: List of (term, replacement) tuples
    
    Returns:
        List of lexicon term dicts
    """
    return [
        create_lexicon_term(lexicon_id=lexicon_id, term=term, replacement=replacement)
        for term, replacement in terms
    ]
