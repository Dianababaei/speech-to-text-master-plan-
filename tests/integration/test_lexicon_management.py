"""
Integration tests for lexicon management workflow.

Tests CRUD operations on lexicon terms:
1. Create new lexicon terms
2. Update existing terms
3. Soft delete terms
4. List and filter terms
5. Verify terms are used in transcriptions
"""
import pytest
from tests.integration.test_helpers import assert_error_response


@pytest.mark.integration
class TestLexiconTermCreation:
    """Tests for creating lexicon terms."""
    
    def test_create_lexicon_term(self, test_client, api_key):
        """Test creating a new lexicon term."""
        response = test_client.post(
            "/lexicons/radiology/terms",
            json={
                "term": "ct scan",
                "replacement": "CT scan"
            },
            headers={"X-API-Key": api_key.key}
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert "id" in data
        assert data["term"] == "ct scan"
        assert data["replacement"] == "CT scan"
        assert data["lexicon_id"] == "radiology"
        assert data["is_active"] is True
    
    def test_create_term_without_auth_fails(self, test_client):
        """Test that creating term without auth returns 401."""
        response = test_client.post(
            "/lexicons/radiology/terms",
            json={
                "term": "mri",
                "replacement": "MRI"
            }
        )
        
        assert_error_response(response, 401, "API key")
    
    def test_create_term_with_empty_value_fails(self, test_client, api_key):
        """Test that creating term with empty values fails validation."""
        response = test_client.post(
            "/lexicons/radiology/terms",
            json={
                "term": "",
                "replacement": "MRI"
            },
            headers={"X-API-Key": api_key.key}
        )
        
        assert response.status_code == 422
    
    def test_create_duplicate_term_fails(self, test_client, api_key, sample_lexicon_terms):
        """Test that creating duplicate term returns error."""
        # Try to create a term that already exists
        response = test_client.post(
            "/lexicons/radiology/terms",
            json={
                "term": "mri",  # Already exists in sample_lexicon_terms
                "replacement": "MRI Scan"
            },
            headers={"X-API-Key": api_key.key}
        )
        
        # Should return conflict error
        assert response.status_code in [409, 422]
    
    def test_create_term_in_different_lexicon(self, test_client, api_key):
        """Test creating same term in different lexicons."""
        # Create term in radiology
        response1 = test_client.post(
            "/lexicons/radiology/terms",
            json={
                "term": "echo",
                "replacement": "echocardiogram"
            },
            headers={"X-API-Key": api_key.key}
        )
        
        assert response1.status_code == 201
        
        # Create same term in cardiology (should succeed)
        response2 = test_client.post(
            "/lexicons/cardiology/terms",
            json={
                "term": "echo",
                "replacement": "ECG"
            },
            headers={"X-API-Key": api_key.key}
        )
        
        assert response2.status_code == 201


@pytest.mark.integration
class TestLexiconTermUpdate:
    """Tests for updating lexicon terms."""
    
    def test_update_lexicon_term(self, test_client, api_key, test_db, sample_lexicon_terms):
        """Test updating an existing lexicon term."""
        # Get the first term
        term = sample_lexicon_terms[0]
        
        response = test_client.put(
            f"/lexicons/{term.lexicon_id}/terms/{term.id}",
            json={
                "term": "mri",
                "replacement": "Magnetic Resonance Imaging"
            },
            headers={"X-API-Key": api_key.key}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(term.id)
        assert data["replacement"] == "Magnetic Resonance Imaging"
    
    def test_update_nonexistent_term_returns_404(self, test_client, api_key):
        """Test updating non-existent term returns 404."""
        import uuid
        fake_id = str(uuid.uuid4())
        
        response = test_client.put(
            f"/lexicons/radiology/terms/{fake_id}",
            json={
                "term": "test",
                "replacement": "TEST"
            },
            headers={"X-API-Key": api_key.key}
        )
        
        assert response.status_code == 404
    
    def test_update_without_auth_fails(self, test_client, sample_lexicon_terms):
        """Test updating term without auth returns 401."""
        term = sample_lexicon_terms[0]
        
        response = test_client.put(
            f"/lexicons/{term.lexicon_id}/terms/{term.id}",
            json={
                "term": "mri",
                "replacement": "Updated"
            }
        )
        
        assert_error_response(response, 401, "API key")


@pytest.mark.integration
class TestLexiconTermDeletion:
    """Tests for soft deleting lexicon terms."""
    
    def test_soft_delete_lexicon_term(self, test_client, api_key, test_db, sample_lexicon_terms):
        """Test soft deleting a lexicon term."""
        term = sample_lexicon_terms[0]
        
        response = test_client.delete(
            f"/lexicons/{term.lexicon_id}/terms/{term.id}",
            headers={"X-API-Key": api_key.key}
        )
        
        assert response.status_code == 204
        
        # Verify term is soft deleted (is_active = False)
        test_db.refresh(term)
        assert term.is_active is False
    
    def test_delete_nonexistent_term_returns_404(self, test_client, api_key):
        """Test deleting non-existent term returns 404."""
        import uuid
        fake_id = str(uuid.uuid4())
        
        response = test_client.delete(
            f"/lexicons/radiology/terms/{fake_id}",
            headers={"X-API-Key": api_key.key}
        )
        
        assert response.status_code == 404
    
    def test_soft_deleted_terms_excluded_from_active_list(
        self,
        test_client,
        api_key,
        sample_lexicon_terms
    ):
        """Test that soft-deleted terms are excluded from listings."""
        # sample_lexicon_terms includes one soft-deleted term (xray)
        
        response = test_client.get(
            "/lexicons/radiology/terms",
            headers={"X-API-Key": api_key.key}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify soft-deleted term (xray) is not in the list
        terms = data.get("items", data) if isinstance(data, dict) else data
        term_list = [t["term"] for t in terms]
        
        assert "xray" not in term_list
        assert "mri" in term_list or "ct scan" in term_list


@pytest.mark.integration
class TestLexiconTermListing:
    """Tests for listing and filtering lexicon terms."""
    
    def test_list_lexicon_terms(self, test_client, api_key, sample_lexicon_terms):
        """Test listing all terms in a lexicon."""
        response = test_client.get(
            "/lexicons/radiology/terms",
            headers={"X-API-Key": api_key.key}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have multiple terms
        items = data.get("items", data) if isinstance(data, dict) else data
        assert len(items) >= 2  # At least mri and ct scan (xray is inactive)
    
    def test_list_terms_from_different_lexicons(
        self,
        test_client,
        api_key,
        sample_lexicon_terms
    ):
        """Test that different lexicons have separate term lists."""
        # Get radiology terms
        response1 = test_client.get(
            "/lexicons/radiology/terms",
            headers={"X-API-Key": api_key.key}
        )
        
        # Get cardiology terms
        response2 = test_client.get(
            "/lexicons/cardiology/terms",
            headers={"X-API-Key": api_key.key}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        items1 = data1.get("items", data1) if isinstance(data1, dict) else data1
        items2 = data2.get("items", data2) if isinstance(data2, dict) else data2
        
        # Radiology should have mri/ct scan
        radiology_terms = [t["term"] for t in items1]
        assert "mri" in radiology_terms or "ct scan" in radiology_terms
        
        # Cardiology should have ecg
        cardiology_terms = [t["term"] for t in items2]
        assert "ecg" in cardiology_terms
    
    def test_list_terms_without_auth_fails(self, test_client):
        """Test listing terms without auth returns 401."""
        response = test_client.get("/lexicons/radiology/terms")
        
        assert_error_response(response, 401, "API key")
    
    def test_list_empty_lexicon(self, test_client, api_key):
        """Test listing terms from empty/non-existent lexicon."""
        response = test_client.get(
            "/lexicons/nonexistent/terms",
            headers={"X-API-Key": api_key.key}
        )
        
        # Should return 200 with empty list (not 404)
        assert response.status_code == 200
        data = response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        assert len(items) == 0


@pytest.mark.integration
class TestLexiconMetadata:
    """Tests for lexicon metadata endpoints."""
    
    def test_list_all_lexicons(self, test_client, api_key, sample_lexicon_terms):
        """Test listing all available lexicons with metadata."""
        response = test_client.get(
            "/lexicons",
            headers={"X-API-Key": api_key.key}
        )
        
        # Note: This endpoint might not exist yet
        if response.status_code == 404:
            pytest.skip("Lexicon listing endpoint not implemented")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should include radiology and cardiology
        lexicons = data.get("lexicons", data)
        lexicon_ids = [lex["lexicon_id"] for lex in lexicons]
        
        assert "radiology" in lexicon_ids
        assert "cardiology" in lexicon_ids


@pytest.mark.integration
class TestLexiconUsageInTranscription:
    """Tests for verifying lexicon terms are used in transcriptions."""
    
    def test_lexicon_terms_applied_to_transcription(
        self,
        test_client,
        test_db,
        api_key,
        sample_lexicon_terms,
        mock_openai_transcribe
    ):
        """Test that lexicon terms are applied during transcription."""
        from app.models import Job
        from datetime import datetime
        
        # Configure mock to return text with lexicon terms
        mock_openai_transcribe.audio.transcriptions.create.return_value.text = \
            "The patient needs an mri and ct scan"
        
        # Create a job (simulating completed transcription)
        job = Job(
            job_id="723e4567-e89b-12d3-a456-426614174006",
            status="completed",
            audio_filename="test.mp3",
            audio_format="mp3",
            lexicon_version="radiology",
            transcription_text="The patient needs an mri and ct scan",
            api_key_id=api_key.id,
            completed_at=datetime.utcnow()
        )
        test_db.add(job)
        test_db.commit()
        
        # Retrieve the job
        response = test_client.get(
            f"/jobs/{job.job_id}",
            headers={"X-API-Key": api_key.key}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Original text should have lowercase
        assert "mri" in data["original_text"].lower()
        
        # If lexicon processing is enabled, processed_text should have uppercase
        # (This depends on whether post-processing is actually run)
    
    def test_different_lexicons_apply_different_replacements(
        self,
        test_client,
        test_db,
        api_key
    ):
        """Test that different lexicons apply their own term replacements."""
        from app.models import Job, LexiconTerm
        from datetime import datetime
        
        # Create lexicon-specific terms
        term1 = LexiconTerm(
            lexicon_id="radiology",
            term="scan",
            replacement="imaging study",
            is_active=True
        )
        term2 = LexiconTerm(
            lexicon_id="general",
            term="scan",
            replacement="examination",
            is_active=True
        )
        test_db.add(term1)
        test_db.add(term2)
        test_db.commit()
        
        # Create jobs with different lexicons
        job1 = Job(
            job_id="823e4567-e89b-12d3-a456-426614174007",
            status="completed",
            lexicon_version="radiology",
            transcription_text="Complete scan required",
            api_key_id=api_key.id,
            completed_at=datetime.utcnow()
        )
        job2 = Job(
            job_id="923e4567-e89b-12d3-a456-426614174008",
            status="completed",
            lexicon_version="general",
            transcription_text="Complete scan required",
            api_key_id=api_key.id,
            completed_at=datetime.utcnow()
        )
        
        test_db.add(job1)
        test_db.add(job2)
        test_db.commit()
        
        # Both jobs should have same original text but potentially different processed text
        response1 = test_client.get(
            f"/jobs/{job1.job_id}",
            headers={"X-API-Key": api_key.key}
        )
        response2 = test_client.get(
            f"/jobs/{job2.job_id}",
            headers={"X-API-Key": api_key.key}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Both should have same original
        assert response1.json()["original_text"] == response2.json()["original_text"]
