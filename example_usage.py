#!/usr/bin/env python
"""
Example usage of the transcription queue service.

This script demonstrates how to:
1. Enqueue a transcription job
2. Check job status
3. Monitor queue statistics
4. Cancel a job
"""

import time
from app.services.queue import (
    enqueue_transcription_job,
    get_job_status,
    get_queue_stats,
    cancel_job
)


def main():
    print("=" * 80)
    print("Transcription Queue Service - Example Usage")
    print("=" * 80)
    
    # Example 1: Enqueue a transcription job
    print("\n1. Enqueueing a transcription job...")
    try:
        job = enqueue_transcription_job(
            job_id="example-job-001",
            audio_file_path="/path/to/audio/sample.mp3",
            lexicon_id="medical-terms-v1",
            api_key_id="openai-key-1",
            priority="normal",
            timeout=300,
            retry_count=3
        )
        print(f"   ✓ Job enqueued successfully!")
        print(f"   Job ID: {job.id}")
        print(f"   Status: {job.get_status()}")
    except Exception as e:
        print(f"   ✗ Failed to enqueue job: {e}")
        return
    
    # Example 2: Check job status
    print("\n2. Checking job status...")
    time.sleep(1)  # Wait a moment
    status = get_job_status("example-job-001")
    if status:
        print(f"   Job ID: {status['job_id']}")
        print(f"   Status: {status['status']}")
        print(f"   Created at: {status['created_at']}")
        print(f"   Started at: {status['started_at']}")
    else:
        print("   ✗ Could not retrieve job status")
    
    # Example 3: Queue statistics
    print("\n3. Queue statistics...")
    stats = get_queue_stats()
    if stats:
        print(f"   Queue name: {stats['queue_name']}")
        print(f"   Queued jobs: {stats['queued_count']}")
        print(f"   Running jobs: {stats['started_count']}")
        print(f"   Completed jobs: {stats['finished_count']}")
        print(f"   Failed jobs: {stats['failed_count']}")
    else:
        print("   ✗ Could not retrieve queue statistics")
    
    # Example 4: Cancel a job (optional)
    print("\n4. Cancelling the job (demonstration)...")
    time.sleep(2)  # Wait a bit before cancelling
    cancelled = cancel_job("example-job-001")
    if cancelled:
        print("   ✓ Job cancelled successfully")
    else:
        print("   ✗ Job could not be cancelled (may have already completed)")
    
    print("\n" + "=" * 80)
    print("Example completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
