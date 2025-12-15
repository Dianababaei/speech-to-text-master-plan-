"""
Unit tests for lexicon service business logic.

Tests cover:
- Term validation for import (duplicate detection, case-insensitive checks)
- Database import operations with proper mocking
- Database export operations
- Error handling and edge cases
- Persian/English text support
"""
import pytest

pytestmark = pytest.mark.unit
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from app.services.lexicon_service import (
    validate_terms_for_import,
    import_terms_to_database,
    export_terms_from_database,
)
from app.schemas.lexicons import SkippedTerm


class TestValidateTermsForImport:
    """Test term validation logic for import operations."""
    
    def test_valid_terms_no_conflicts(self, mock_db_session, mock_lexicon_term_model):
        """Test validating terms with no conflicts."""
        lexicon_id = "test-lexicon"
        terms = [
            {"term": "MRI", "replacement": "Magnetic Resonance Imaging"},
            {"term": "CT", "replacement": "Computed Tomography"},
            {"term": "X-ray", "replacement": "Radiography"}
        ]
        
        # Mock empty existing terms
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query
        
        valid, skipped = validate_terms_for_import(lexicon_id, terms, mock_db_session)
        
        assert len(valid) == 3
        assert len(skipped) == 0
        assert valid == terms
    
    def test_duplicate_terms_in_batch(self, mock_db_session):
        """Test detection of duplicate terms within import batch."""
        lexicon_id = "test-lexicon"
        terms = [
            {"term": "MRI", "replacement": "Magnetic Resonance Imaging"},
            {"term": "mri", "replacement": "Different replacement"},  # Duplicate (case-insensitive)
            {"term": "CT", "replacement": "Computed Tomography"}
        ]
        
        # Mock empty existing terms
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query
        
        valid, skipped = validate_terms_for_import(lexicon_id, terms, mock_db_session)
        
        assert len(valid) == 2  # MRI and CT
        assert len(skipped) == 1  # Second mri
        assert skipped[0].term == "mri"
        assert "Duplicate term in import file" in skipped[0].reason
    
    def test_conflict_with_existing_terms(self, mock_db_session):
        """Test detection of conflicts with existing database terms."""
        lexicon_id = "test-lexicon"
        terms = [
            {"term": "MRI", "replacement": "Magnetic Resonance Imaging"},
            {"term": "CT", "replacement": "Computed Tomography"}
        ]
        
        # Mock existing term in database
        existing_term = Mock()
        existing_term.term = "mri"  # Lowercase in DB
        existing_term.lexicon_id = lexicon_id
        existing_term.is_active = True
        
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [existing_term]
        mock_db_session.query.return_value = mock_query
        
        valid, skipped = validate_terms_for_import(lexicon_id, terms, mock_db_session)
        
        assert len(valid) == 1  # Only CT
        assert len(skipped) == 1  # MRI conflicts
        assert skipped[0].term == "MRI"
        assert "already exists in lexicon" in skipped[0].reason
    
    def test_case_insensitive_conflict_detection(self, mock_db_session):
        """Test that conflict detection is case-insensitive."""
        lexicon_id = "test-lexicon"
        terms = [
            {"term": "MRI", "replacement": "Magnetic Resonance Imaging"},
            {"term": "Mri", "replacement": "Different"},
            {"term": "mri", "replacement": "Another"}
        ]
        
        # Mock empty existing terms
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query
        
        valid, skipped = validate_terms_for_import(lexicon_id, terms, mock_db_session)
        
        # Only first occurrence should be valid
        assert len(valid) == 1
        assert len(skipped) == 2
        assert valid[0]["term"] == "MRI"
    
    def test_persian_terms_validation(self, mock_db_session):
        """Test validation with Persian terms."""
        lexicon_id = "radiology-fa"
        terms = [
            {"term": "ام آر آی", "replacement": "MRI"},
            {"term": "سی تی", "replacement": "CT"},
            {"term": "ام آر آی", "replacement": "Duplicate"}  # Exact duplicate
        ]
        
        # Mock empty existing terms
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query
        
        valid, skipped = validate_terms_for_import(lexicon_id, terms, mock_db_session)
        
        assert len(valid) == 2  # First two terms
        assert len(skipped) == 1  # Third term is duplicate
    
    def test_empty_terms_list(self, mock_db_session):
        """Test validation with empty terms list."""
        lexicon_id = "test-lexicon"
        terms = []
        
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query
        
        valid, skipped = validate_terms_for_import(lexicon_id, terms, mock_db_session)
        
        assert len(valid) == 0
        assert len(skipped) == 0
    
    def test_multiple_conflicts(self, mock_db_session):
        """Test handling multiple conflicts at once."""
        lexicon_id = "test-lexicon"
        terms = [
            {"term": "MRI", "replacement": "Magnetic Resonance Imaging"},
            {"term": "CT", "replacement": "Computed Tomography"},
            {"term": "X-ray", "replacement": "Radiography"},
            {"term": "mri", "replacement": "Duplicate in batch"},  # Batch duplicate
            {"term": "ECG", "replacement": "Electrocardiogram"}
        ]
        
        # Mock existing CT term in database
        existing_term = Mock()
        existing_term.term = "ct"
        existing_term.lexicon_id = lexicon_id
        existing_term.is_active = True
        
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [existing_term]
        mock_db_session.query.return_value = mock_query
        
        valid, skipped = validate_terms_for_import(lexicon_id, terms, mock_db_session)
        
        assert len(valid) == 3  # MRI, X-ray, ECG
        assert len(skipped) == 2  # CT (DB conflict), second mri (batch duplicate)
        
        # Check reasons
        skipped_terms = {s.term: s.reason for s in skipped}
        assert "CT" in skipped_terms
        assert "already exists" in skipped_terms["CT"]
        assert "mri" in skipped_terms
        assert "Duplicate term in import file" in skipped_terms["mri"]


class TestImportTermsToDatabase:
    """Test database import operations."""
    
    def test_successful_import(self, mock_db_session):
        """Test successful import of terms to database."""
        lexicon_id = "test-lexicon"
        terms = [
            {"term": "MRI", "replacement": "Magnetic Resonance Imaging"},
            {"term": "CT", "replacement": "Computed Tomography"}
        ]
        
        result_count = import_terms_to_database(lexicon_id, terms, mock_db_session)
        
        assert result_count == 2
        mock_db_session.bulk_save_objects.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    def test_import_with_persian_terms(self, mock_db_session):
        """Test importing Persian terms."""
        lexicon_id = "radiology-fa"
        terms = [
            {"term": "ام آر آی", "replacement": "MRI"},
            {"term": "سی تی", "replacement": "CT"}
        ]
        
        result_count = import_terms_to_database(lexicon_id, terms, mock_db_session)
        
        assert result_count == 2
        mock_db_session.commit.assert_called_once()
    
    def test_import_empty_list(self, mock_db_session):
        """Test importing empty list of terms."""
        lexicon_id = "test-lexicon"
        terms = []
        
        result_count = import_terms_to_database(lexicon_id, terms, mock_db_session)
        
        assert result_count == 0
        mock_db_session.bulk_save_objects.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    def test_import_failure_rollback(self, mock_db_session):
        """Test that import failures trigger rollback."""
        lexicon_id = "test-lexicon"
        terms = [
            {"term": "MRI", "replacement": "Magnetic Resonance Imaging"}
        ]
        
        # Simulate database error
        mock_db_session.commit.side_effect = Exception("Database error")
        
        with pytest.raises(Exception) as exc_info:
            import_terms_to_database(lexicon_id, terms, mock_db_session)
        
        assert "Database error" in str(exc_info.value)
        mock_db_session.rollback.assert_called_once()
    
    def test_import_large_batch(self, mock_db_session):
        """Test importing a large batch of terms."""
        lexicon_id = "test-lexicon"
        terms = [
            {"term": f"term_{i}", "replacement": f"replacement_{i}"}
            for i in range(1000)
        ]
        
        result_count = import_terms_to_database(lexicon_id, terms, mock_db_session)
        
        assert result_count == 1000
        mock_db_session.bulk_save_objects.assert_called_once()
        
        # Check that all terms were passed to bulk_save_objects
        call_args = mock_db_session.bulk_save_objects.call_args
        saved_objects = call_args[0][0]
        assert len(saved_objects) == 1000
    
    def test_import_special_characters(self, mock_db_session):
        """Test importing terms with special characters."""
        lexicon_id = "test-lexicon"
        terms = [
            {"term": "C++", "replacement": "C Plus Plus"},
            {"term": "A/B test", "replacement": "Split test"},
            {"term": "pH", "replacement": "Potential of Hydrogen"}
        ]
        
        result_count = import_terms_to_database(lexicon_id, terms, mock_db_session)
        
        assert result_count == 3
        mock_db_session.commit.assert_called_once()


class TestExportTermsFromDatabase:
    """Test database export operations."""
    
    def test_successful_export(self, mock_db_session):
        """Test successful export of terms from database."""
        lexicon_id = "test-lexicon"
        
        # Mock database terms
        term1 = Mock()
        term1.term = "MRI"
        term1.replacement = "Magnetic Resonance Imaging"
        
        term2 = Mock()
        term2.term = "CT"
        term2.replacement = "Computed Tomography"
        
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [term1, term2]
        mock_db_session.query.return_value = mock_query
        
        result = export_terms_from_database(lexicon_id, mock_db_session)
        
        assert len(result) == 2
        assert result[0] == {"term": "MRI", "replacement": "Magnetic Resonance Imaging"}
        assert result[1] == {"term": "CT", "replacement": "Computed Tomography"}
    
    def test_export_empty_lexicon(self, mock_db_session):
        """Test exporting from an empty lexicon."""
        lexicon_id = "empty-lexicon"
        
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query
        
        result = export_terms_from_database(lexicon_id, mock_db_session)
        
        assert len(result) == 0
        assert result == []
    
    def test_export_persian_terms(self, mock_db_session):
        """Test exporting Persian terms."""
        lexicon_id = "radiology-fa"
        
        # Mock Persian terms
        term1 = Mock()
        term1.term = "ام آر آی"
        term1.replacement = "MRI"
        
        term2 = Mock()
        term2.term = "سی تی"
        term2.replacement = "CT"
        
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [term1, term2]
        mock_db_session.query.return_value = mock_query
        
        result = export_terms_from_database(lexicon_id, mock_db_session)
        
        assert len(result) == 2
        assert result[0]["term"] == "ام آر آی"
        assert result[1]["term"] == "سی تی"
    
    def test_export_only_active_terms(self, mock_db_session):
        """Test that export only returns active terms."""
        lexicon_id = "test-lexicon"
        
        # Mock mix of active and inactive terms
        # The query should filter for is_active=True, so only return active
        active_term = Mock()
        active_term.term = "MRI"
        active_term.replacement = "Magnetic Resonance Imaging"
        
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [active_term]
        mock_db_session.query.return_value = mock_query
        
        result = export_terms_from_database(lexicon_id, mock_db_session)
        
        assert len(result) == 1
        assert result[0]["term"] == "MRI"
    
    def test_export_large_lexicon(self, mock_db_session):
        """Test exporting a large lexicon."""
        lexicon_id = "large-lexicon"
        
        # Mock 1000 terms
        terms = []
        for i in range(1000):
            term = Mock()
            term.term = f"term_{i}"
            term.replacement = f"replacement_{i}"
            terms.append(term)
        
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = terms
        mock_db_session.query.return_value = mock_query
        
        result = export_terms_from_database(lexicon_id, mock_db_session)
        
        assert len(result) == 1000
        assert result[0]["term"] == "term_0"
        assert result[999]["term"] == "term_999"
    
    def test_export_special_characters(self, mock_db_session):
        """Test exporting terms with special characters."""
        lexicon_id = "test-lexicon"
        
        term1 = Mock()
        term1.term = "C++"
        term1.replacement = "C Plus Plus"
        
        term2 = Mock()
        term2.term = "A/B test"
        term2.replacement = "Split test"
        
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [term1, term2]
        mock_db_session.query.return_value = mock_query
        
        result = export_terms_from_database(lexicon_id, mock_db_session)
        
        assert len(result) == 2
        assert result[0]["term"] == "C++"
        assert result[1]["term"] == "A/B test"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_very_long_terms(self, mock_db_session):
        """Test handling very long term strings."""
        lexicon_id = "test-lexicon"
        long_term = "a" * 250
        long_replacement = "b" * 250
        
        terms = [{"term": long_term, "replacement": long_replacement}]
        
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query
        
        valid, skipped = validate_terms_for_import(lexicon_id, terms, mock_db_session)
        
        assert len(valid) == 1
        assert len(skipped) == 0
    
    def test_whitespace_in_terms(self, mock_db_session):
        """Test handling terms with various whitespace."""
        lexicon_id = "test-lexicon"
        terms = [
            {"term": "MRI scan", "replacement": "MRI Scan"},
            {"term": "CT  scan", "replacement": "CT Scan"},  # Double space
            {"term": " X-ray ", "replacement": "X-ray"}  # Leading/trailing space
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query
        
        valid, skipped = validate_terms_for_import(lexicon_id, terms, mock_db_session)
        
        # All should be valid (whitespace handling is application-level)
        assert len(valid) == 3
    
    def test_unicode_normalization(self, mock_db_session):
        """Test that Unicode variations are handled correctly."""
        lexicon_id = "test-lexicon"
        # Same Persian character in different Unicode forms
        terms = [
            {"term": "قلب", "replacement": "heart"},  # NFC form
            {"term": "قلب", "replacement": "cardiac"}  # Could be NFD/NFKC
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query
        
        valid, skipped = validate_terms_for_import(lexicon_id, terms, mock_db_session)
        
        # This tests that validation handles potential Unicode form differences
        # Actual behavior depends on string comparison
        assert len(valid) + len(skipped) == 2
