"""
Example usage of the transcription worker.

This script demonstrates how to:
1. Create a job in the database
2. Enqueue it for processing
3. Monitor its progress
"""
import uuid
from datetime import datetime
from redis import Redis
from rq import Queue

from app.models.job import Job, Base
from app.utils.database import engine, get_db_session
from app.workers.transcription_worker import process_transcription_job


def setup_database():
    """Create database tables."""
    Base.metadata.create_all(bind=engine)
    print("Database tables created")


def create_sample_job(audio_file_path: str, lexicon_id: str = None) -> str:
    """
    Create a sample job in the database.
    
    Args:
        audio_file_path: Path to audio file
        lexicon_id: Optional lexicon ID for post-processing
    
    Returns:
        Job ID
    """
    session = get_db_session()
    try:
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            status="pending",
            audio_file_path=audio_file_path,
            lexicon_id=lexicon_id,
            created_at=datetime.utcnow()
        )
        session.add(job)
        session.commit()
        
        print(f"Created job: {job_id}")
        return job_id
    
    finally:
        session.close()


def enqueue_job_with_rq(job_id: str):
    """
    Enqueue job using Redis Queue.
    
    Args:
        job_id: Job ID to enqueue
    """
    # Setup Redis connection
    redis_conn = Redis(host='localhost', port=6379, db=0)
    queue = Queue('transcription', connection=redis_conn)
    
    # Enqueue the job
    rq_job = queue.enqueue(
        process_transcription_job,
        job_id=job_id,
        timeout=600,  # 10 minutes
        result_ttl=3600,  # Keep result for 1 hour
        failure_ttl=86400  # Keep failed job info for 24 hours
    )
    
    print(f"Job enqueued: {rq_job.id}")
    return rq_job


def check_job_status(job_id: str):
    """
    Check job status in database.
    
    Args:
        job_id: Job ID to check
    """
    session = get_db_session()
    try:
        job = session.query(Job).filter(Job.id == job_id).first()
        
        if job:
            print(f"\nJob Status:")
            print(f"  ID: {job.id}")
            print(f"  Status: {job.status}")
            print(f"  Created: {job.created_at}")
            print(f"  Started: {job.started_at}")
            print(f"  Completed: {job.completed_at}")
            print(f"  Original Text Length: {len(job.original_text) if job.original_text else 0}")
            print(f"  Processed Text Length: {len(job.processed_text) if job.processed_text else 0}")
            
            if job.error_message:
                print(f"  Error: {job.error_message}")
        else:
            print(f"Job {job_id} not found")
    
    finally:
        session.close()


def process_job_directly(job_id: str):
    """
    Process job directly without queue (for testing).
    
    Args:
        job_id: Job ID to process
    """
    print(f"Processing job {job_id} directly...")
    process_transcription_job(job_id)
    print("Processing complete")


# Example usage
if __name__ == "__main__":
    import sys
    
    # Setup database (run once)
    setup_database()
    
    # Example 1: Create and process job directly
    if len(sys.argv) > 1 and sys.argv[1] == "direct":
        audio_path = sys.argv[2] if len(sys.argv) > 2 else "/path/to/audio.mp3"
        job_id = create_sample_job(audio_path)
        process_job_directly(job_id)
        check_job_status(job_id)
    
    # Example 2: Create and enqueue job with RQ
    elif len(sys.argv) > 1 and sys.argv[1] == "enqueue":
        audio_path = sys.argv[2] if len(sys.argv) > 2 else "/path/to/audio.mp3"
        job_id = create_sample_job(audio_path)
        enqueue_job_with_rq(job_id)
        print("\nJob enqueued. Start RQ worker with:")
        print("  rq worker transcription --url redis://localhost:6379/0")
    
    # Example 3: Check status of existing job
    elif len(sys.argv) > 1 and sys.argv[1] == "status":
        job_id = sys.argv[2] if len(sys.argv) > 2 else input("Enter job ID: ")
        check_job_status(job_id)
    
    else:
        print("Usage:")
        print("  python worker_example.py direct [audio_path]  - Process job directly")
        print("  python worker_example.py enqueue [audio_path] - Enqueue job with RQ")
        print("  python worker_example.py status [job_id]      - Check job status")
