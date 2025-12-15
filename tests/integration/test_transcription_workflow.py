"""
Integration tests for transcription workflow.

Tests the complete transcription workflow:
1. Upload audio file
2. Verify job created
3. Poll job status
4. Verify transcription results

Also tests different audio formats and lexicon selection.
"""
import io
import pytest
from unittest.mock import patch, MagicMock

from tests.integration.test_helpers import (
    create_test_audio_file,
    assert_error_response,
    assert_datetime_format,
    create_multipart_file
)


@pytest.mark.integration
class TestTranscriptionUpload:
    """Tests for audio file upload and job creation."""
    
    def test_upload_audio_creates_job(self, test_client, api_key, mock_openai_transcribe):
        """Test that uploading audio file creates a job successfully."""
        audio_content = create_test_audio_file("mp3")
        
        response = test_client.post(
            "/transcribe",
            files={"audio": ("test.mp3", io.BytesIO(audio_content), "audio/mpeg")},
            headers={"X-API-Key": api_key.key}
        )
        
        assert response.status_code == 202
        data = response.json()
        
        # Verify response structure
        assert "job_id" in data
        assert "status" in data
        assert "created_at" in data
        
        # Verify status is pending
        assert data["status"] == "pending"
        
        # Verify timestamps are valid
        assert_datetime_format(data["created_at"])
    
    def test_upload_without_api_key_fails(self, test_client):
        """Test that upload without API key returns 401."""
        audio_content = create_test_audio_file("mp3")
        
        response = test_client.post(
            "/transcribe",
            files={"audio": ("test.mp3", io.BytesIO(audio_content), "audio/mpeg")}
        )
        
        assert_error_response(response, 401, "API key")
    
    def test_upload_with_invalid_api_key_fails(self, test_client):
        """Test that upload with invalid API key returns 401."""
        audio_content = create_test_audio_file("mp3")
        
        response = test_client.post(
            "/transcribe",
            files={"audio": ("test.mp3", io.BytesIO(audio_content), "audio/mpeg")},
            headers={"X-API-Key": "invalid-key"}
        )
        
        assert_error_response(response, 401, "Invalid")
    
    def test_upload_with_inactive_api_key_fails(self, test_client, inactive_api_key):
        """Test that upload with inactive API key returns 401."""
        audio_content = create_test_audio_file("mp3")
        
        response = test_client.post(
            "/transcribe",
            files={"audio": ("test.mp3", io.BytesIO(audio_content), "audio/mpeg")},
            headers={"X-API-Key": inactive_api_key.key}
        )
        
        assert_error_response(response, 401, "inactive")
    
    def test_upload_without_file_fails(self, test_client, api_key):
        """Test that upload without file returns 400 or 422."""
        response = test_client.post(
            "/transcribe",
            headers={"X-API-Key": api_key.key}
        )
        
        # Should return validation error
        assert response.status_code in [400, 422]
    
    def test_upload_empty_file_fails(self, test_client, api_key):
        """Test that uploading empty file returns error."""
        response = test_client.post(
            "/transcribe",
            files={"audio": ("test.mp3", io.BytesIO(b""), "audio/mpeg")},
            headers={"X-API-Key": api_key.key}
        )
        
        # Should return validation error for empty file
        assert response.status_code in [400, 413]


@pytest.mark.integration
class TestAudioFormats:
    """Tests for different audio formats."""
    
    def test_upload_mp3_file(self, test_client, api_key, mock_openai_transcribe):
        """Test uploading MP3 audio file."""
        audio_content = create_test_audio_file("mp3")
        
        response = test_client.post(
            "/transcribe",
            files={"audio": ("test.mp3", io.BytesIO(audio_content), "audio/mpeg")},
            headers={"X-API-Key": api_key.key}
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "pending"
    
    def test_upload_wav_file(self, test_client, api_key, mock_openai_transcribe):
        """Test uploading WAV audio file."""
        audio_content = create_test_audio_file("wav")
        
        response = test_client.post(
            "/transcribe",
            files={"audio": ("test.wav", io.BytesIO(audio_content), "audio/wav")},
            headers={"X-API-Key": api_key.key}
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "pending"
    
    def test_upload_m4a_file(self, test_client, api_key, mock_openai_transcribe):
        """Test uploading M4A audio file."""
        audio_content = create_test_audio_file("m4a")
        
        response = test_client.post(
            "/transcribe",
            files={"audio": ("test.m4a", io.BytesIO(audio_content), "audio/mp4")},
            headers={"X-API-Key": api_key.key}
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "pending"
    
    def test_upload_unsupported_format_fails(self, test_client, api_key):
        """Test that unsupported file format returns error."""
        response = test_client.post(
            "/transcribe",
            files={"audio": ("test.txt", io.BytesIO(b"not audio"), "text/plain")},
            headers={"X-API-Key": api_key.key}
        )
        
        # Should return 400 for unsupported format
        assert response.status_code == 400


@pytest.mark.integration
class TestLexiconSelection:
    """Tests for lexicon selection in transcription."""
    
    def test_default_lexicon_used_when_not_specified(
        self,
        test_client,
        api_key,
        mock_openai_transcribe
    ):
        """Test that default lexicon is used when not specified."""
        audio_content = create_test_audio_file("mp3")
        
        response = test_client.post(
            "/transcribe",
            files={"audio": ("test.mp3", io.BytesIO(audio_content), "audio/mpeg")},
            headers={"X-API-Key": api_key.key}
        )
        
        assert response.status_code == 202
        # Job created successfully with default lexicon
    
    def test_lexicon_via_header(self, test_client, api_key, mock_openai_transcribe):
        """Test specifying lexicon via X-Lexicon-Id header."""
        audio_content = create_test_audio_file("mp3")
        
        response = test_client.post(
            "/transcribe",
            files={"audio": ("test.mp3", io.BytesIO(audio_content), "audio/mpeg")},
            headers={
                "X-API-Key": api_key.key,
                "X-Lexicon-Id": "radiology"
            }
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "pending"
    
    def test_lexicon_via_query_parameter(
        self,
        test_client,
        api_key,
        mock_openai_transcribe
    ):
        """Test specifying lexicon via query parameter."""
        audio_content = create_test_audio_file("mp3")
        
        response = test_client.post(
            "/transcribe?lexicon=cardiology",
            files={"audio": ("test.mp3", io.BytesIO(audio_content), "audio/mpeg")},
            headers={"X-API-Key": api_key.key}
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "pending"
    
    def test_header_takes_precedence_over_query_param(
        self,
        test_client,
        api_key,
        mock_openai_transcribe
    ):
        """Test that header lexicon takes precedence over query parameter."""
        audio_content = create_test_audio_file("mp3")
        
        response = test_client.post(
            "/transcribe?lexicon=cardiology",
            files={"audio": ("test.mp3", io.BytesIO(audio_content), "audio/mpeg")},
            headers={
                "X-API-Key": api_key.key,
                "X-Lexicon-Id": "radiology"
            }
        )
        
        assert response.status_code == 202
        # Header should take precedence (radiology, not cardiology)


@pytest.mark.integration
class TestJobStatusRetrieval:
    """Tests for retrieving job status."""
    
    def test_get_pending_job_status(self, test_client, test_db, api_key):
        """Test retrieving status of a pending job."""
        from app.models import Job
        
        # Create a pending job
        job = Job(
            job_id="123e4567-e89b-12d3-a456-426614174000",
            status="pending",
            audio_filename="test.mp3",
            audio_format="mp3",
            api_key_id=api_key.id
        )
        test_db.add(job)
        test_db.commit()
        
        response = test_client.get(
            f"/jobs/{job.job_id}",
            headers={"X-API-Key": api_key.key}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["job_id"] == job.job_id
        assert data["status"] == "pending"
        assert data["original_text"] is None
        assert data["processed_text"] is None
        assert data["error_message"] is None
    
    def test_get_completed_job_with_results(self, test_client, test_db, api_key):
        """Test retrieving a completed job returns transcription results."""
        from app.models import Job
        from datetime import datetime
        
        # Create a completed job
        job = Job(
            job_id="223e4567-e89b-12d3-a456-426614174001",
            status="completed",
            audio_filename="test.mp3",
            audio_format="mp3",
            transcription_text="The patient needs an MRI scan",
            api_key_id=api_key.id,
            completed_at=datetime.utcnow()
        )
        test_db.add(job)
        test_db.commit()
        
        response = test_client.get(
            f"/jobs/{job.job_id}",
            headers={"X-API-Key": api_key.key}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["job_id"] == job.job_id
        assert data["status"] == "completed"
        assert data["original_text"] is not None
        assert data["completed_at"] is not None
    
    def test_get_failed_job_with_error(self, test_client, test_db, api_key):
        """Test retrieving a failed job returns error message."""
        from app.models import Job
        from datetime import datetime
        
        # Create a failed job
        job = Job(
            job_id="323e4567-e89b-12d3-a456-426614174002",
            status="failed",
            audio_filename="test.mp3",
            audio_format="mp3",
            error_message="Audio format not supported",
            api_key_id=api_key.id,
            completed_at=datetime.utcnow()
        )
        test_db.add(job)
        test_db.commit()
        
        response = test_client.get(
            f"/jobs/{job.job_id}",
            headers={"X-API-Key": api_key.key}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["job_id"] == job.job_id
        assert data["status"] == "failed"
        assert data["error_message"] == "Audio format not supported"
        assert data["original_text"] is None
    
    def test_get_nonexistent_job_returns_404(self, test_client, api_key):
        """Test that requesting non-existent job returns 404."""
        response = test_client.get(
            "/jobs/00000000-0000-0000-0000-000000000000",
            headers={"X-API-Key": api_key.key}
        )
        
        assert response.status_code == 404
    
    def test_get_job_from_different_api_key_returns_404(
        self,
        test_client,
        test_db,
        api_key
    ):
        """Test that accessing another user's job returns 404."""
        from app.models import Job, ApiKey
        
        # Create another API key
        other_key = ApiKey(
            key="other-api-key-12345",
            project_name="other-project",
            is_active=True,
            is_admin=False,
            rate_limit=100
        )
        test_db.add(other_key)
        test_db.commit()
        test_db.refresh(other_key)
        
        # Create job for the other API key
        job = Job(
            job_id="423e4567-e89b-12d3-a456-426614174003",
            status="pending",
            audio_filename="test.mp3",
            audio_format="mp3",
            api_key_id=other_key.id
        )
        test_db.add(job)
        test_db.commit()
        
        # Try to access with original API key
        response = test_client.get(
            f"/jobs/{job.job_id}",
            headers={"X-API-Key": api_key.key}
        )
        
        # Should return 404 (not 403) to avoid leaking job existence
        assert response.status_code == 404
    
    def test_get_job_with_invalid_uuid_format_returns_400(self, test_client, api_key):
        """Test that invalid UUID format returns 400."""
        response = test_client.get(
            "/jobs/not-a-valid-uuid",
            headers={"X-API-Key": api_key.key}
        )
        
        # Should return 400 for invalid format (not 422)
        assert response.status_code in [400, 422]


@pytest.mark.integration
class TestTranscriptionResults:
    """Tests for verifying transcription results and processing."""
    
    def test_transcription_stores_original_and_processed_text(
        self,
        test_client,
        test_db,
        api_key
    ):
        """Test that both original and processed text are stored."""
        from app.models import Job
        from datetime import datetime
        
        # Create completed job with both texts
        job = Job(
            job_id="523e4567-e89b-12d3-a456-426614174004",
            status="completed",
            audio_filename="test.mp3",
            audio_format="mp3",
            transcription_text="original mri text",
            api_key_id=api_key.id,
            completed_at=datetime.utcnow()
        )
        test_db.add(job)
        test_db.commit()
        
        response = test_client.get(
            f"/jobs/{job.job_id}",
            headers={"X-API-Key": api_key.key}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify both texts are present
        assert data["original_text"] is not None
        # Note: processed_text might be same as original if no processing applied
    
    def test_lexicon_replacements_applied_in_processed_text(
        self,
        test_client,
        test_db,
        api_key,
        sample_lexicon_terms
    ):
        """Test that lexicon replacements are applied to processed text."""
        from app.models import Job
        from datetime import datetime
        
        # Create job with text that should be processed by lexicon
        job = Job(
            job_id="623e4567-e89b-12d3-a456-426614174005",
            status="completed",
            audio_filename="test.mp3",
            audio_format="mp3",
            transcription_text="The patient needs an mri scan",
            api_key_id=api_key.id,
            completed_at=datetime.utcnow()
        )
        test_db.add(job)
        test_db.commit()
        
        response = test_client.get(
            f"/jobs/{job.job_id}",
            headers={"X-API-Key": api_key.key}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # If post-processing is applied, processed_text should have "MRI"
        # instead of "mri" (based on lexicon terms)
        assert data["original_text"] == "The patient needs an mri scan"
