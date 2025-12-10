"""
Script to create text files for all existing transcriptions in the database.
Run this once to backfill transcription files for jobs that were completed before
the auto-save feature was added.
"""
from pathlib import Path
from app.database import get_db
from app.models.job import Job

def create_transcription_files():
    """Create text files for all completed jobs in the database."""

    # Create transcriptions directory if it doesn't exist
    transcriptions_dir = Path("transcriptions")
    transcriptions_dir.mkdir(exist_ok=True)

    # Get database session
    db = next(get_db())

    try:
        # Query all completed jobs with transcriptions
        jobs = db.query(Job).filter(
            Job.status == "completed",
            Job.transcription_text.isnot(None)
        ).all()

        print(f"Found {len(jobs)} completed jobs with transcriptions")

        created_count = 0
        skipped_count = 0

        for job in jobs:
            # Generate filename from audio filename
            if not job.audio_filename:
                print(f"  Skipping job {job.job_id}: no audio_filename")
                skipped_count += 1
                continue

            base_name = Path(job.audio_filename).stem
            txt_filename = f"{base_name}.txt"
            txt_path = transcriptions_dir / txt_filename

            # Skip if file already exists
            if txt_path.exists():
                print(f"  Skipping {txt_filename}: file already exists")
                skipped_count += 1
                continue

            # Save transcription with UTF-8 encoding for Persian text
            txt_path.write_text(job.transcription_text, encoding='utf-8')
            print(f"  Created {txt_filename}")
            created_count += 1

        print(f"\nSummary:")
        print(f"  Created: {created_count} files")
        print(f"  Skipped: {skipped_count} files")
        print(f"  Total: {len(jobs)} jobs processed")

    finally:
        db.close()

if __name__ == "__main__":
    create_transcription_files()
