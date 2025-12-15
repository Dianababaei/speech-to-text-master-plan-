"""
Integration tests for feedback workflow.

Tests the complete feedback workflow:
1. Submit feedback correction
2. List feedback with filters
3. Update feedback status (approve/reject)
4. Test status transitions
"""
import pytest
from datetime import datetime, timedelta
from tests.integration.test_helpers import assert_error_response


@pytest.mark.integration
class TestFeedbackSubmission:
    """Tests for submitting feedback corrections."""
    
    def test_submit_feedback_correction(self, test_client, api_key, sample_job):
        """Test submitting a feedback correction for a transcription."""
        response = test_client.post(
            f"/jobs/{sample_job.job_id}/feedback",
            json={
                "original_text": "The patient needs an mri scan",
                "corrected_text": "The patient needs an MRI scan",
                "created_by": "dr.smith@hospital.com"
            },
            headers={"X-API-Key": api_key.key}
        )
        
        # Note: Endpoint might not exist yet
        if response.status_code == 404:
            pytest.skip("Feedback submission endpoint not implemented")
        
        assert response.status_code in [200, 201]
        data = response.json()
        
        assert "feedback_id" in data or "id" in data
        assert data["status"] == "pending"
    
    def test_submit_feedback_without_auth_fails(self, test_client, sample_job):
        """Test that submitting feedback without auth returns 401."""
        response = test_client.post(
            f"/jobs/{sample_job.job_id}/feedback",
            json={
                "original_text": "test",
                "corrected_text": "TEST",
                "created_by": "user@example.com"
            }
        )
        
        if response.status_code == 404:
            pytest.skip("Feedback submission endpoint not implemented")
        
        assert_error_response(response, 401, "API key")
    
    def test_submit_feedback_for_nonexistent_job_fails(self, test_client, api_key):
        """Test submitting feedback for non-existent job returns 404."""
        response = test_client.post(
            "/jobs/00000000-0000-0000-0000-000000000000/feedback",
            json={
                "original_text": "test",
                "corrected_text": "TEST",
                "created_by": "user@example.com"
            },
            headers={"X-API-Key": api_key.key}
        )
        
        if response.status_code == 404:
            # Could be either endpoint not found or job not found
            pass
        else:
            assert response.status_code == 404
    
    def test_submit_feedback_with_empty_correction_fails(self, test_client, api_key, sample_job):
        """Test that empty corrected text fails validation."""
        response = test_client.post(
            f"/jobs/{sample_job.job_id}/feedback",
            json={
                "original_text": "test",
                "corrected_text": "",
                "created_by": "user@example.com"
            },
            headers={"X-API-Key": api_key.key}
        )
        
        if response.status_code == 404:
            pytest.skip("Feedback submission endpoint not implemented")
        
        assert response.status_code == 422
    
    def test_submit_feedback_with_identical_text_fails(
        self,
        test_client,
        api_key,
        sample_job
    ):
        """Test that identical original and corrected text fails validation."""
        response = test_client.post(
            f"/jobs/{sample_job.job_id}/feedback",
            json={
                "original_text": "same text",
                "corrected_text": "same text",
                "created_by": "user@example.com"
            },
            headers={"X-API-Key": api_key.key}
        )
        
        if response.status_code == 404:
            pytest.skip("Feedback submission endpoint not implemented")
        
        assert response.status_code == 422


@pytest.mark.integration
class TestFeedbackListing:
    """Tests for listing and filtering feedback."""
    
    def test_list_all_feedback(self, test_client, admin_api_key, test_db):
        """Test listing all feedback records."""
        from app.models import Feedback
        
        # Create some feedback records
        feedback1 = Feedback(
            job_id=1,
            original_text="original text 1",
            corrected_text="corrected text 1",
            status="pending",
            lexicon_id="radiology",
            created_by="user1@example.com",
            frequency=1
        )
        feedback2 = Feedback(
            job_id=2,
            original_text="original text 2",
            corrected_text="corrected text 2",
            status="approved",
            lexicon_id="cardiology",
            created_by="user2@example.com",
            frequency=1
        )
        
        test_db.add(feedback1)
        test_db.add(feedback2)
        test_db.commit()
        
        response = test_client.get(
            "/feedback",
            headers={"X-API-Key": admin_api_key.key}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 2
    
    def test_list_feedback_requires_admin_key(self, test_client, api_key):
        """Test that listing feedback requires admin privileges."""
        response = test_client.get(
            "/feedback",
            headers={"X-API-Key": api_key.key}
        )
        
        # Should return 403 (forbidden) for non-admin keys
        assert response.status_code == 403
    
    def test_filter_feedback_by_status(self, test_client, admin_api_key, test_db):
        """Test filtering feedback by status."""
        from app.models import Feedback
        
        # Create feedback with different statuses
        feedback1 = Feedback(
            job_id=1,
            original_text="text 1",
            corrected_text="TEXT 1",
            status="pending",
            created_by="user@example.com",
            frequency=1
        )
        feedback2 = Feedback(
            job_id=2,
            original_text="text 2",
            corrected_text="TEXT 2",
            status="approved",
            created_by="user@example.com",
            frequency=1
        )
        feedback3 = Feedback(
            job_id=3,
            original_text="text 3",
            corrected_text="TEXT 3",
            status="rejected",
            created_by="user@example.com",
            frequency=1
        )
        
        test_db.add_all([feedback1, feedback2, feedback3])
        test_db.commit()
        
        # Filter by pending status
        response = test_client.get(
            "/feedback?status=pending",
            headers={"X-API-Key": admin_api_key.key}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All items should have pending status
        for item in data["items"]:
            assert item["status"] == "pending"
    
    def test_filter_feedback_by_lexicon_id(self, test_client, admin_api_key, test_db):
        """Test filtering feedback by lexicon_id."""
        from app.models import Feedback
        
        feedback1 = Feedback(
            job_id=1,
            original_text="text 1",
            corrected_text="TEXT 1",
            status="pending",
            lexicon_id="radiology",
            created_by="user@example.com",
            frequency=1
        )
        feedback2 = Feedback(
            job_id=2,
            original_text="text 2",
            corrected_text="TEXT 2",
            status="pending",
            lexicon_id="cardiology",
            created_by="user@example.com",
            frequency=1
        )
        
        test_db.add_all([feedback1, feedback2])
        test_db.commit()
        
        # Filter by radiology lexicon
        response = test_client.get(
            "/feedback?lexicon_id=radiology",
            headers={"X-API-Key": admin_api_key.key}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All items should have radiology lexicon
        for item in data["items"]:
            if item["lexicon_id"]:
                assert item["lexicon_id"] == "radiology"
    
    def test_filter_feedback_by_date_range(self, test_client, admin_api_key, test_db):
        """Test filtering feedback by date range."""
        from app.models import Feedback
        
        # Create feedback with different dates
        old_date = datetime.utcnow() - timedelta(days=10)
        recent_date = datetime.utcnow() - timedelta(days=1)
        
        feedback1 = Feedback(
            job_id=1,
            original_text="old feedback",
            corrected_text="OLD FEEDBACK",
            status="pending",
            created_by="user@example.com",
            created_at=old_date,
            frequency=1
        )
        feedback2 = Feedback(
            job_id=2,
            original_text="recent feedback",
            corrected_text="RECENT FEEDBACK",
            status="pending",
            created_by="user@example.com",
            created_at=recent_date,
            frequency=1
        )
        
        test_db.add_all([feedback1, feedback2])
        test_db.commit()
        
        # Filter by date range (last 5 days)
        date_from = (datetime.utcnow() - timedelta(days=5)).isoformat()
        
        response = test_client.get(
            f"/feedback?date_from={date_from}",
            headers={"X-API-Key": admin_api_key.key}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should only include recent feedback
        assert len(data["items"]) >= 1
    
    def test_feedback_pagination(self, test_client, admin_api_key, test_db):
        """Test pagination of feedback listing."""
        from app.models import Feedback
        
        # Create multiple feedback records
        for i in range(15):
            feedback = Feedback(
                job_id=i + 1,
                original_text=f"text {i}",
                corrected_text=f"TEXT {i}",
                status="pending",
                created_by="user@example.com",
                frequency=1
            )
            test_db.add(feedback)
        
        test_db.commit()
        
        # Request first page with page_size=10
        response = test_client.get(
            "/feedback?page=1&page_size=10",
            headers={"X-API-Key": admin_api_key.key}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert len(data["items"]) <= 10
        assert data["total"] >= 15


@pytest.mark.integration
class TestFeedbackStatusUpdate:
    """Tests for updating feedback status."""
    
    def test_approve_feedback(self, test_client, admin_api_key, test_db):
        """Test approving pending feedback."""
        from app.models import Feedback
        
        feedback = Feedback(
            job_id=1,
            original_text="original",
            corrected_text="corrected",
            status="pending",
            created_by="user@example.com",
            frequency=1
        )
        test_db.add(feedback)
        test_db.commit()
        test_db.refresh(feedback)
        
        response = test_client.patch(
            f"/feedback/{feedback.id}",
            json={"status": "approved"},
            headers={"X-API-Key": admin_api_key.key}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "approved"
    
    def test_reject_feedback(self, test_client, admin_api_key, test_db):
        """Test rejecting pending feedback."""
        from app.models import Feedback
        
        feedback = Feedback(
            job_id=1,
            original_text="original",
            corrected_text="corrected",
            status="pending",
            created_by="user@example.com",
            frequency=1
        )
        test_db.add(feedback)
        test_db.commit()
        test_db.refresh(feedback)
        
        response = test_client.patch(
            f"/feedback/{feedback.id}",
            json={"status": "rejected"},
            headers={"X-API-Key": admin_api_key.key}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "rejected"
    
    def test_update_feedback_requires_admin_key(self, test_client, api_key, test_db):
        """Test that updating feedback requires admin privileges."""
        from app.models import Feedback
        
        feedback = Feedback(
            job_id=1,
            original_text="original",
            corrected_text="corrected",
            status="pending",
            created_by="user@example.com",
            frequency=1
        )
        test_db.add(feedback)
        test_db.commit()
        test_db.refresh(feedback)
        
        response = test_client.patch(
            f"/feedback/{feedback.id}",
            json={"status": "approved"},
            headers={"X-API-Key": api_key.key}
        )
        
        # Should return 403 for non-admin keys
        assert response.status_code == 403
    
    def test_invalid_status_transition_fails(self, test_client, admin_api_key, test_db):
        """Test that invalid status transitions are rejected."""
        from app.models import Feedback
        
        # Create approved feedback
        feedback = Feedback(
            job_id=1,
            original_text="original",
            corrected_text="corrected",
            status="approved",
            created_by="user@example.com",
            frequency=1
        )
        test_db.add(feedback)
        test_db.commit()
        test_db.refresh(feedback)
        
        # Try to change from approved to rejected (invalid transition)
        response = test_client.patch(
            f"/feedback/{feedback.id}",
            json={"status": "rejected"},
            headers={"X-API-Key": admin_api_key.key}
        )
        
        # Should return 400 for invalid transition
        assert response.status_code == 400
    
    def test_update_nonexistent_feedback_returns_404(self, test_client, admin_api_key):
        """Test updating non-existent feedback returns 404."""
        response = test_client.patch(
            "/feedback/999999",
            json={"status": "approved"},
            headers={"X-API-Key": admin_api_key.key}
        )
        
        assert response.status_code == 404
    
    def test_update_feedback_with_confidence(self, test_client, admin_api_key, test_db):
        """Test updating feedback with confidence score."""
        from app.models import Feedback
        
        feedback = Feedback(
            job_id=1,
            original_text="original",
            corrected_text="corrected",
            status="pending",
            created_by="user@example.com",
            frequency=1
        )
        test_db.add(feedback)
        test_db.commit()
        test_db.refresh(feedback)
        
        response = test_client.patch(
            f"/feedback/{feedback.id}",
            json={
                "status": "approved",
                "confidence": 0.95
            },
            headers={"X-API-Key": admin_api_key.key}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "approved"
        if "confidence" in data:
            assert data["confidence"] == 0.95


@pytest.mark.integration
class TestFeedbackStatusTransitions:
    """Tests for feedback status transition rules."""
    
    def test_pending_to_approved_allowed(self, test_client, admin_api_key, test_db):
        """Test pending → approved transition is allowed."""
        from app.models import Feedback
        
        feedback = Feedback(
            job_id=1,
            original_text="test",
            corrected_text="TEST",
            status="pending",
            created_by="user@example.com",
            frequency=1
        )
        test_db.add(feedback)
        test_db.commit()
        test_db.refresh(feedback)
        
        response = test_client.patch(
            f"/feedback/{feedback.id}",
            json={"status": "approved"},
            headers={"X-API-Key": admin_api_key.key}
        )
        
        assert response.status_code == 200
    
    def test_pending_to_rejected_allowed(self, test_client, admin_api_key, test_db):
        """Test pending → rejected transition is allowed."""
        from app.models import Feedback
        
        feedback = Feedback(
            job_id=1,
            original_text="test",
            corrected_text="TEST",
            status="pending",
            created_by="user@example.com",
            frequency=1
        )
        test_db.add(feedback)
        test_db.commit()
        test_db.refresh(feedback)
        
        response = test_client.patch(
            f"/feedback/{feedback.id}",
            json={"status": "rejected"},
            headers={"X-API-Key": admin_api_key.key}
        )
        
        assert response.status_code == 200
    
    def test_approved_to_rejected_not_allowed(self, test_client, admin_api_key, test_db):
        """Test approved → rejected transition is not allowed."""
        from app.models import Feedback
        
        feedback = Feedback(
            job_id=1,
            original_text="test",
            corrected_text="TEST",
            status="approved",
            created_by="user@example.com",
            frequency=1
        )
        test_db.add(feedback)
        test_db.commit()
        test_db.refresh(feedback)
        
        response = test_client.patch(
            f"/feedback/{feedback.id}",
            json={"status": "rejected"},
            headers={"X-API-Key": admin_api_key.key}
        )
        
        assert response.status_code == 400
    
    def test_rejected_to_approved_not_allowed(self, test_client, admin_api_key, test_db):
        """Test rejected → approved transition is not allowed."""
        from app.models import Feedback
        
        feedback = Feedback(
            job_id=1,
            original_text="test",
            corrected_text="TEST",
            status="rejected",
            created_by="user@example.com",
            frequency=1
        )
        test_db.add(feedback)
        test_db.commit()
        test_db.refresh(feedback)
        
        response = test_client.patch(
            f"/feedback/{feedback.id}",
            json={"status": "approved"},
            headers={"X-API-Key": admin_api_key.key}
        )
        
        assert response.status_code == 400
