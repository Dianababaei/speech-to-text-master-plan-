"""
Unit tests for post-processing service.

Tests lexicon-based text replacement with:
- Case preservation
- Longest-match-first
- Unicode/Persian text handling
- Edge cases
"""
import pytest

pytestmark = [pytest.mark.unit, pytest.mark.lexicon]
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from app.services.postprocessing_service import (
    apply_lexicon_corrections,
    apply_lexicon_replacements,
    process_transcription,
    _preserve_case,
    PostProcessingError
)


class TestCasePreservation:
    """Test case preservation logic."""
    
    def test_preserve_case_all_uppercase(self):
        """Test case preservation for all uppercase original."""
        assert _preserve_case("MRI", "mri") == "MRI"
        assert _preserve_case("CT", "ct") == "CT"
        assert _preserve_case("SCAN", "scan") == "SCAN"
    
    def test_preserve_case_title_case(self):
        """Test case preservation for title case original."""
        assert _preserve_case("Mri", "mri") == "Mri"
        assert _preserve_case("Scan", "scan") == "Scan"
        assert _preserve_case("Patient", "patient") == "Patient"
    
    def test_preserve_case_lowercase(self):
        """Test case preservation for lowercase original - keeps replacement as-is."""
        assert _preserve_case("mri", "MRI") == "MRI"
        assert _preserve_case("scan", "SCAN") == "SCAN"
        assert _preserve_case("ct", "CT") == "CT"
    
    def test_preserve_case_mixed(self):
        """Test case preservation for mixed case - keeps replacement as-is."""
        assert _preserve_case("MrI", "mri") == "mri"
        assert _preserve_case("sCaN", "scan") == "scan"


class TestSimpleReplacements:
    """Test simple lexicon replacements."""
    
    def test_single_term_replacement(self):
        """Test replacing a single term."""
        lexicon = {"mri": "MRI"}
        text = "The patient needs an mri scan."
        result = apply_lexicon_corrections(text, lexicon)
        assert result == "The patient needs an MRI scan."
    
    def test_multiple_term_replacements(self):
        """Test replacing multiple different terms."""
        lexicon = {
            "mri": "MRI",
            "ct": "CT",
            "xray": "X-ray"
        }
        text = "The patient had an mri, ct, and xray."
        result = apply_lexicon_corrections(text, lexicon)
        assert result == "The patient had an MRI, CT, and X-ray."
    
    def test_multiple_occurrences(self):
        """Test replacing multiple occurrences of the same term."""
        lexicon = {"mri": "MRI"}
        text = "First mri was inconclusive. Second mri showed results."
        result = apply_lexicon_corrections(text, lexicon)
        assert result == "First MRI was inconclusive. Second MRI showed results."
    
    def test_empty_lexicon(self):
        """Test with empty lexicon returns original text."""
        lexicon = {}
        text = "Original text"
        result = apply_lexicon_corrections(text, lexicon)
        assert result == "Original text"
    
    def test_empty_text(self):
        """Test with empty text."""
        lexicon = {"mri": "MRI"}
        text = ""
        result = apply_lexicon_corrections(text, lexicon)
        assert result == ""


class TestCaseInsensitiveMatching:
    """Test case-insensitive matching with case preservation."""
    
    def test_uppercase_match(self):
        """Test matching uppercase text."""
        lexicon = {"mri": "MRI"}
        text = "The MRI scan was clear."
        result = apply_lexicon_corrections(text, lexicon)
        assert result == "The MRI scan was clear."
    
    def test_lowercase_match(self):
        """Test matching lowercase text."""
        lexicon = {"mri": "MRI"}
        text = "The mri scan was clear."
        result = apply_lexicon_corrections(text, lexicon)
        assert result == "The MRI scan was clear."
    
    def test_title_case_match(self):
        """Test matching title case text."""
        lexicon = {"mri": "MRI"}
        text = "Mri results are pending."
        result = apply_lexicon_corrections(text, lexicon)
        assert result == "Mri results are pending."
    
    def test_mixed_case_in_document(self):
        """Test handling mixed case occurrences in same document."""
        lexicon = {"mri": "MRI"}
        text = "The MRI and mri and Mri scans."
        result = apply_lexicon_corrections(text, lexicon)
        # Each occurrence preserves its original case pattern
        assert result == "The MRI and MRI and Mri scans."


class TestWholeWordMatching:
    """Test whole-word matching to avoid partial matches."""
    
    def test_avoids_partial_match_prefix(self):
        """Test that 'scan' doesn't match 'scanning'."""
        lexicon = {"scan": "SCAN"}
        text = "The patient is scanning the document."
        result = apply_lexicon_corrections(text, lexicon)
        assert result == "The patient is scanning the document."
    
    def test_avoids_partial_match_suffix(self):
        """Test that 'scan' doesn't match 'prescan'."""
        lexicon = {"scan": "SCAN"}
        text = "The prescan preparation is complete."
        result = apply_lexicon_corrections(text, lexicon)
        assert result == "The prescan preparation is complete."
    
    def test_matches_with_punctuation(self):
        """Test matching terms adjacent to punctuation."""
        lexicon = {"mri": "MRI"}
        text = "The mri, ct, and xray results."
        result = apply_lexicon_corrections(text, lexicon)
        assert "MRI," in result
    
    def test_matches_at_start(self):
        """Test matching term at start of text."""
        lexicon = {"mri": "MRI"}
        text = "mri scan completed successfully."
        result = apply_lexicon_corrections(text, lexicon)
        assert result.startswith("MRI")
    
    def test_matches_at_end(self):
        """Test matching term at end of text."""
        lexicon = {"mri": "MRI"}
        text = "Patient underwent an mri"
        result = apply_lexicon_corrections(text, lexicon)
        assert result.endswith("MRI")


class TestLongestMatchFirst:
    """Test longest-match-first strategy."""
    
    def test_prefers_longer_match(self):
        """Test that longer terms are matched before shorter ones."""
        lexicon = {
            "mri": "MRI",
            "mri scan": "MRI Scan"
        }
        text = "The patient needs an mri scan."
        result = apply_lexicon_corrections(text, lexicon)
        # Should match "mri scan" as a whole, not "mri" then "scan"
        assert "MRI Scan" in result
    
    def test_multiple_overlapping_terms(self):
        """Test with multiple overlapping term options."""
        lexicon = {
            "heart": "cardiac",
            "heart attack": "myocardial infarction",
            "heart attack symptoms": "MI symptoms"
        }
        text = "The patient showed heart attack symptoms."
        result = apply_lexicon_corrections(text, lexicon)
        # Should match the longest: "heart attack symptoms"
        assert "MI symptoms" in result
    
    def test_non_overlapping_terms(self):
        """Test that non-overlapping terms are all replaced."""
        lexicon = {
            "mri": "MRI",
            "ct": "CT"
        }
        text = "Both mri and ct were performed."
        result = apply_lexicon_corrections(text, lexicon)
        assert "MRI" in result
        assert "CT" in result


class TestPersianText:
    """Test Persian/Farsi text handling."""
    
    def test_persian_term_replacement(self):
        """Test replacing Persian terms."""
        lexicon = {
            "ام آر آی": "MRI",
            "سی تی": "CT"
        }
        text = "بیمار نیاز به ام آر آی دارد"
        result = apply_lexicon_corrections(text, lexicon)
        assert "MRI" in result
    
    def test_mixed_persian_english(self):
        """Test mixed Persian and English text."""
        lexicon = {
            "mri": "MRI",
            "اسکن": "scan"
        }
        text = "The patient needs an mri and اسکن"
        result = apply_lexicon_corrections(text, lexicon)
        assert "MRI" in result
        assert "scan" in result
    
    def test_persian_unicode_handling(self):
        """Test proper Unicode handling for Persian characters."""
        lexicon = {
            "قلب": "heart",
            "بیمار": "patient"
        }
        text = "قلب بیمار سالم است"
        result = apply_lexicon_corrections(text, lexicon)
        # Ensure no encoding errors (mojibake)
        assert "heart" in result
        assert "patient" in result
        # Original Persian characters should be preserved if not replaced
        assert "است" in result


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_special_characters_in_term(self):
        """Test terms with special regex characters."""
        lexicon = {
            "c++": "C++",
            "a/b": "A/B"
        }
        text = "Programming in c++ and testing a/b."
        result = apply_lexicon_corrections(text, lexicon)
        assert "C++" in result
        assert "A/B" in result
    
    def test_numbers_in_term(self):
        """Test terms with numbers."""
        lexicon = {
            "covid19": "COVID-19",
            "h1n1": "H1N1"
        }
        text = "Testing for covid19 and h1n1."
        result = apply_lexicon_corrections(text, lexicon)
        assert "COVID-19" in result
        assert "H1N1" in result
    
    def test_hyphenated_terms(self):
        """Test hyphenated terms."""
        lexicon = {
            "x-ray": "X-ray",
            "follow-up": "follow up"
        }
        text = "Schedule x-ray and follow-up."
        result = apply_lexicon_corrections(text, lexicon)
        assert "X-ray" in result
    
    def test_term_with_apostrophe(self):
        """Test terms with apostrophes."""
        lexicon = {
            "alzheimer's": "Alzheimer's disease"
        }
        text = "Patient has alzheimer's symptoms."
        result = apply_lexicon_corrections(text, lexicon)
        assert "Alzheimer's disease" in result
    
    def test_very_long_text(self):
        """Test performance with longer text."""
        lexicon = {
            "mri": "MRI",
            "ct": "CT",
            "xray": "X-ray"
        }
        # Create a long text with repeated terms
        text = " ".join(["The patient needs an mri, ct, and xray."] * 100)
        result = apply_lexicon_corrections(text, lexicon)
        # Just verify it completes without error
        assert "MRI" in result
        assert "CT" in result
        assert "X-ray" in result
    
    def test_none_lexicon(self):
        """Test handling None lexicon gracefully."""
        text = "Some text"
        result = apply_lexicon_corrections(text, None)
        assert result == text


class TestApplyLexiconReplacements:
    """Test the apply_lexicon_replacements convenience function."""
    
    @patch('app.services.postprocessing_service.load_lexicon_sync')
    def test_loads_and_applies_lexicon(self, mock_load_lexicon):
        """Test that function loads lexicon and applies it."""
        mock_db = Mock(spec=Session)
        mock_load_lexicon.return_value = {"mri": "MRI"}
        
        text = "Patient needs an mri."
        result = apply_lexicon_replacements(text, "radiology", mock_db)
        
        mock_load_lexicon.assert_called_once_with(mock_db, "radiology")
        assert "MRI" in result
    
    @patch('app.services.postprocessing_service.load_lexicon_sync')
    def test_handles_empty_lexicon(self, mock_load_lexicon):
        """Test handling when lexicon is empty."""
        mock_db = Mock(spec=Session)
        mock_load_lexicon.return_value = {}
        
        text = "Original text"
        result = apply_lexicon_replacements(text, "nonexistent", mock_db)
        
        assert result == text
    
    @patch('app.services.postprocessing_service.load_lexicon_sync')
    def test_handles_lexicon_load_error(self, mock_load_lexicon):
        """Test error handling when lexicon loading fails."""
        mock_db = Mock(spec=Session)
        mock_load_lexicon.side_effect = Exception("Database error")
        
        with pytest.raises(PostProcessingError):
            apply_lexicon_replacements("text", "radiology", mock_db)


class TestProcessTranscription:
    """Test the main process_transcription function."""
    
    @patch('app.services.postprocessing_service.apply_lexicon_replacements')
    def test_applies_lexicon_when_provided(self, mock_apply):
        """Test that lexicon is applied when lexicon_id and db provided."""
        mock_db = Mock(spec=Session)
        mock_apply.return_value = "Processed text"
        
        result = process_transcription("Original text", "radiology", mock_db)
        
        mock_apply.assert_called_once_with("Original text", "radiology", mock_db)
        assert result == "Processed text"
    
    def test_skips_lexicon_when_no_id(self):
        """Test that processing continues without lexicon when no ID provided."""
        mock_db = Mock(spec=Session)
        
        text = "Original text"
        result = process_transcription(text, None, mock_db)
        
        assert result == text
    
    def test_skips_lexicon_when_no_db(self):
        """Test that processing continues without lexicon when no DB provided."""
        text = "Original text"
        result = process_transcription(text, "radiology", None)
        
        assert result == text
    
    @patch('app.services.postprocessing_service.apply_lexicon_replacements')
    def test_handles_lexicon_error_gracefully(self, mock_apply):
        """Test that errors in lexicon application are handled gracefully."""
        mock_db = Mock(spec=Session)
        mock_apply.side_effect = PostProcessingError("Lexicon error")
        
        text = "Original text"
        # Should not raise, just continue without corrections
        result = process_transcription(text, "radiology", mock_db)
        
        # Should return original text when lexicon fails
        assert result == text


class TestRealWorldScenarios:
    """Test real-world medical transcription scenarios."""
    
    def test_radiology_report(self):
        """Test typical radiology report corrections."""
        lexicon = {
            "mri": "MRI",
            "ct": "CT",
            "xray": "X-ray",
            "mri scan": "MRI scan",
            "contrast": "contrast agent"
        }
        text = """
        Patient underwent mri scan with contrast. 
        Previous ct and xray showed no abnormalities.
        The MRI indicates possible inflammation.
        """
        result = apply_lexicon_corrections(text, lexicon)
        
        assert "MRI scan" in result
        assert "contrast agent" in result
        assert "CT" in result
        assert "X-ray" in result
    
    def test_cardiology_report(self):
        """Test typical cardiology report corrections."""
        lexicon = {
            "ekg": "EKG",
            "ecg": "ECG",
            "bp": "blood pressure",
            "bpm": "BPM"
        }
        text = "Patient's ekg shows normal rhythm at 75 bpm. The bp is 120/80."
        result = apply_lexicon_corrections(text, lexicon)
        
        assert "EKG" in result
        assert "BPM" in result
        assert "blood pressure" in result
    
    def test_mixed_language_medical_report(self):
        """Test medical report with mixed English and Persian."""
        lexicon = {
            "mri": "MRI",
            "بیمار": "patient",
            "نتیجه": "result"
        }
        text = "The mri for بیمار shows نتیجه is normal."
        result = apply_lexicon_corrections(text, lexicon)
        
        assert "MRI" in result
        assert "patient" in result
        assert "result" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
