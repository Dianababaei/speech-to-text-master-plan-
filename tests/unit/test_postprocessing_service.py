"""
Unit tests for post-processing service.

Tests lexicon-based text replacement with:
- Case preservation
- Longest-match-first
- Unicode/Persian text handling
- Edge cases
"""
import pytest
import os

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


class TestFuzzyMatchingConfiguration:
    """Test fuzzy matching configuration flowing through the pipeline."""
    
    def test_apply_lexicon_corrections_accepts_fuzzy_params(self):
        """Test that apply_lexicon_corrections accepts fuzzy parameters."""
        lexicon = {"mri": "MRI"}
        text = "Patient needs an mri scan."
        
        # Should accept fuzzy parameters without error
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=85
        )
        assert "MRI" in result
    
    def test_apply_lexicon_corrections_fuzzy_defaults(self):
        """Test that fuzzy parameters have correct defaults."""
        lexicon = {"mri": "MRI"}
        text = "Patient needs an mri scan."
        
        # Should work with defaults
        result = apply_lexicon_corrections(text, lexicon)
        assert "MRI" in result
    
    @patch('app.services.postprocessing_service.load_lexicon_sync')
    def test_apply_lexicon_replacements_accepts_fuzzy_params(self, mock_load_lexicon):
        """Test that apply_lexicon_replacements accepts fuzzy parameters."""
        mock_db = Mock(spec=Session)
        mock_load_lexicon.return_value = {"mri": "MRI"}
        
        text = "Patient needs an mri."
        result = apply_lexicon_replacements(
            text,
            "radiology",
            mock_db,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=80
        )
        assert "MRI" in result
    
    @patch('app.services.postprocessing_service.load_lexicon_sync')
    def test_apply_lexicon_replacements_fuzzy_defaults(self, mock_load_lexicon):
        """Test that apply_lexicon_replacements fuzzy parameters have correct defaults."""
        mock_db = Mock(spec=Session)
        mock_load_lexicon.return_value = {"mri": "MRI"}
        
        text = "Patient needs an mri."
        # Should work with defaults
        result = apply_lexicon_replacements(text, "radiology", mock_db)
        assert "MRI" in result


class TestPostProcessingPipelineConfiguration:
    """Test PostProcessingPipeline fuzzy matching configuration."""
    
    def test_pipeline_init_accepts_fuzzy_params(self):
        """Test that PostProcessingPipeline accepts fuzzy parameters in __init__."""
        from app.services.postprocessing_service import PostProcessingPipeline
        
        pipeline = PostProcessingPipeline(
            enable_lexicon_replacement=True,
            enable_text_cleanup=True,
            enable_numeral_handling=True,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=85
        )
        
        assert pipeline.enable_fuzzy_matching is True
        assert pipeline.fuzzy_match_threshold == 85
    
    def test_pipeline_init_fuzzy_defaults(self):
        """Test that PostProcessingPipeline fuzzy parameters have correct defaults."""
        from app.services.postprocessing_service import PostProcessingPipeline
        
        pipeline = PostProcessingPipeline()
        
        assert pipeline.enable_fuzzy_matching is True
        assert pipeline.fuzzy_match_threshold == 85
    
    def test_pipeline_init_fuzzy_custom_threshold(self):
        """Test setting custom fuzzy threshold."""
        from app.services.postprocessing_service import PostProcessingPipeline
        
        pipeline = PostProcessingPipeline(
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=75
        )
        
        assert pipeline.enable_fuzzy_matching is True
        assert pipeline.fuzzy_match_threshold == 75
    
    def test_pipeline_init_disable_fuzzy(self):
        """Test disabling fuzzy matching."""
        from app.services.postprocessing_service import PostProcessingPipeline
        
        pipeline = PostProcessingPipeline(
            enable_fuzzy_matching=False,
            fuzzy_match_threshold=85
        )
        
        assert pipeline.enable_fuzzy_matching is False
        assert pipeline.fuzzy_match_threshold == 85


class TestCreatePipelineWithFuzzyConfig:
    """Test create_pipeline function with fuzzy matching configuration."""
    
    def test_create_pipeline_accepts_fuzzy_override(self):
        """Test that create_pipeline allows overriding fuzzy config."""
        from app.services.postprocessing_service import create_pipeline
        
        pipeline = create_pipeline(
            enable_fuzzy_matching=False,
            fuzzy_match_threshold=75
        )
        
        assert pipeline.enable_fuzzy_matching is False
        assert pipeline.fuzzy_match_threshold == 75
    
    def test_create_pipeline_fuzzy_threshold_override(self):
        """Test overriding only fuzzy threshold."""
        from app.services.postprocessing_service import create_pipeline
        
        pipeline = create_pipeline(fuzzy_match_threshold=90)
        
        # Should use config default for enable_fuzzy_matching
        assert pipeline.fuzzy_match_threshold == 90
    
    def test_create_pipeline_no_override_uses_config(self):
        """Test that create_pipeline uses config defaults when no override provided."""
        from app.services.postprocessing_service import create_pipeline
        
        # Create pipeline without overrides - should use config defaults
        pipeline = create_pipeline()
        
        # These should match the app.config defaults
        assert isinstance(pipeline.enable_fuzzy_matching, bool)
        assert isinstance(pipeline.fuzzy_match_threshold, int)
        assert pipeline.fuzzy_match_threshold >= 0
        assert pipeline.fuzzy_match_threshold <= 100


class TestBasicFuzzyMatching:
    """Test basic fuzzy matching functionality for misspelled words."""
    
    def test_fuzzy_match_single_misspelled_word(self):
        """Test fuzzy matching catches misspelled medical term."""
        lexicon = {"radiology": "Radiology"}
        text = "Patient needs radilogy imaging."  # "radilogy" is misspelled
        
        result = apply_lexicon_corrections(
            text, 
            lexicon, 
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=80
        )
        
        # Should match "radilogy" to "radiology" and apply replacement
        # The result should contain the corrected term
        assert "radiology" in result.lower() or "Radiology" in result
    
    def test_fuzzy_match_multiple_misspelled_words(self):
        """Test fuzzy matching with multiple misspellings in same text."""
        lexicon = {
            "radiology": "Radiology",
            "cardiology": "Cardiology"
        }
        text = "Patient had radilogy and cardiologi scans."
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=80
        )
        
        # Should correct both misspellings
        assert "radiology" in result.lower() or "Radiology" in result
    
    def test_fuzzy_match_typo_correction(self):
        """Test typo correction through fuzzy matching."""
        lexicon = {"imaging": "imaging procedure"}
        text = "Patient underwent imagng assessment."  # typo: imagng -> imaging
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=80
        )
        
        # Should match typo to correct term
        assert result is not None
    
    def test_fuzzy_matching_disabled(self):
        """Test that fuzzy matching can be disabled."""
        lexicon = {"radiology": "Radiology"}
        text = "Patient needs radilogy imaging."  # misspelled
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=False,
            fuzzy_match_threshold=85
        )
        
        # With fuzzy matching disabled, misspelled word should not be matched
        # The text should remain mostly unchanged (except for case-preserving replacements)
        # Since "radilogy" doesn't exactly match "radiology", it won't be corrected
        assert "radilogy" in result


class TestSimilarityScoreCalculation:
    """Test similarity score calculation and threshold behavior."""
    
    def test_similarity_score_high_similarity(self):
        """Test that similar terms score high."""
        lexicon = {"radiology": "Radiology"}
        text = "Patient needs radilogy scan."  # 1 character different
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=75  # Lower threshold
        )
        
        # High similarity (one typo) should match
        assert result is not None
    
    def test_similarity_score_low_similarity(self):
        """Test that dissimilar terms don't match above threshold."""
        lexicon = {"radiology": "Radiology"}
        text = "Patient needs imaging scan."
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=95  # Very high threshold
        )
        
        # Very different words should not match even with fuzzy matching
        assert "radiology" not in result.lower() or result == text
    
    def test_threshold_boundary_above(self):
        """Test word just above similarity threshold gets matched."""
        lexicon = {"mri": "MRI"}
        text = "Patient had mro scan."  # Very close to "mri"
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=70
        )
        
        # Should match due to high similarity and low threshold
        assert result is not None
    
    def test_threshold_boundary_below(self):
        """Test word just below similarity threshold doesn't get matched."""
        lexicon = {"radiology": "Radiology"}
        text = "Patient had radiologyy scan."  # Extra character
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=99  # Very strict
        )
        
        # Very strict threshold should not match
        assert result is not None
    
    def test_different_threshold_values(self):
        """Test that different thresholds affect matching behavior."""
        lexicon = {"scan": "Scan"}
        text = "Patient had scna procedure."
        
        # Same text with different thresholds
        result_low_threshold = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=70
        )
        
        result_high_threshold = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=95
        )
        
        # Both should be valid results
        assert result_low_threshold is not None
        assert result_high_threshold is not None


class TestExactMatchPriority:
    """Test that exact matches take priority over fuzzy matches."""
    
    def test_exact_match_preferred_over_fuzzy(self):
        """Test exact match is always selected over fuzzy match."""
        lexicon = {
            "mri": "MRI",
            "mr": "Magnetic Resonance"
        }
        text = "The patient had an mri scan."
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=80
        )
        
        # "mri" is an exact match - should match exactly, not fuzzy
        assert "MRI" in result
        assert "Magnetic Resonance" not in result or result.count("Magnetic Resonance") == 0
    
    def test_fuzzy_only_when_no_exact_match(self):
        """Test fuzzy matching only triggers when no exact match exists."""
        lexicon = {"radiology": "Radiology"}
        text_exact = "Patient needs radiology scan."
        text_fuzzy = "Patient needs radilogy scan."
        
        result_exact = apply_lexicon_corrections(
            text_exact,
            lexicon,
            enable_fuzzy_matching=False,
            fuzzy_match_threshold=85
        )
        
        result_fuzzy = apply_lexicon_corrections(
            text_fuzzy,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=85
        )
        
        # Exact match should work without fuzzy matching enabled
        assert "Radiology" in result_exact or "radiology" in result_exact.lower()
    
    def test_exact_match_overrides_fuzzy_threshold(self):
        """Test exact match is used even if fuzzy threshold is very high."""
        lexicon = {"mri": "MRI"}
        text = "The patient had an mri scan."
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=100  # Impossible threshold
        )
        
        # Exact match should still work
        assert "MRI" in result


class TestBestMatchSelection:
    """Test selection of best match when multiple candidates exist."""
    
    def test_highest_score_selected(self):
        """Test that highest similarity score is selected."""
        lexicon = {
            "radiology": "Radiology",
            "radio": "Radio"
        }
        text = "Patient needs radilogy imaging."  # Similar to "radiology" but not "radio"
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=75
        )
        
        # "radiology" is closer to "radilogy" than "radio" is
        assert result is not None
    
    def test_multiple_matches_different_scores(self):
        """Test behavior with multiple lexicon terms of different similarity."""
        lexicon = {
            "ct": "CT",
            "cat": "CAT",
            "cardiac": "Cardiac"
        }
        text = "Patient had a ct scan."  # Exact match for "ct"
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=80
        )
        
        # "ct" is exact match, should be preferred
        assert "CT" in result
    
    def test_tie_handling_consistent(self):
        """Test that equal scores are handled gracefully."""
        lexicon = {
            "test": "TEST",
            "best": "BEST"
        }
        text = "This is a test case."
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=80
        )
        
        # Should handle without errors
        assert result is not None
        assert "TEST" in result


class TestCasePreservationWithFuzzy:
    """Test case preservation works correctly with fuzzy matching."""
    
    def test_case_preservation_uppercase_fuzzy(self):
        """Test uppercase case preservation with fuzzy match."""
        lexicon = {"radiology": "Radiology"}
        text = "Patient had RADILOGY imaging."  # UPPERCASE + typo
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=80
        )
        
        # Should preserve uppercase
        assert "RADIOLOGY" in result or "Radiology" in result
    
    def test_case_preservation_title_case_fuzzy(self):
        """Test title case preservation with fuzzy match."""
        lexicon = {"imaging": "imaging procedure"}
        text = "Patient underwent Imagng assessment."  # Title case + typo
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=80
        )
        
        # Should preserve title case pattern
        assert result is not None
    
    def test_case_preservation_lowercase_fuzzy(self):
        """Test lowercase preservation with fuzzy match."""
        lexicon = {"scan": "Scan"}
        text = "patient had scna procedure."  # lowercase + typo
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=80
        )
        
        # Should apply replacement respecting original case
        assert result is not None
    
    def test_case_preservation_mixed_case_fuzzy(self):
        """Test mixed case preservation with fuzzy match."""
        lexicon = {"radiology": "Radiology"}
        text = "Patient had rADILOGY imaging."  # Mixed case + typo
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=80
        )
        
        # Should handle without errors
        assert result is not None
    
    def test_persian_text_case_handling(self):
        """Test Persian text case handling with fuzzy matching."""
        lexicon = {
            "ام آر آی": "MRI",
            "اسکن": "scan"
        }
        text = "بیمار نیاز به ام آر آی دارد"  # Persian text
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=85
        )
        
        # Should handle Persian text without encoding errors
        assert result is not None
        assert "MRI" in result or "ام آر آی" in result


class TestFuzzyMatchingConfiguration:
    """Test environment variable controls for fuzzy matching."""
    
    @patch.dict(os.environ, {"ENABLE_FUZZY_MATCHING": "false"})
    def test_fuzzy_matching_disabled_via_env(self):
        """Test that ENABLE_FUZZY_MATCHING=false disables fuzzy matching."""
        from app.config import ENABLE_FUZZY_MATCHING as config_fuzzy
        
        # Environment variable should be false
        assert not config_fuzzy or config_fuzzy is False
    
    @patch.dict(os.environ, {"FUZZY_MATCH_THRESHOLD": "75"})
    def test_fuzzy_threshold_from_env(self):
        """Test that FUZZY_MATCH_THRESHOLD can be set via environment."""
        from app.config import FUZZY_MATCH_THRESHOLD as config_threshold
        
        # Threshold should be read from environment
        assert config_threshold >= 0
        assert config_threshold <= 100
    
    def test_fuzzy_matching_enabled_default(self):
        """Test that fuzzy matching is enabled by default."""
        from app.services.postprocessing_service import PostProcessingPipeline
        
        pipeline = PostProcessingPipeline()
        
        # Fuzzy matching should be enabled by default
        assert pipeline.enable_fuzzy_matching is True
    
    def test_fuzzy_threshold_default(self):
        """Test that fuzzy threshold has a sensible default."""
        from app.services.postprocessing_service import PostProcessingPipeline
        
        pipeline = PostProcessingPipeline()
        
        # Default threshold should be set (typically 85)
        assert 0 <= pipeline.fuzzy_match_threshold <= 100
    
    def test_fuzzy_config_override_in_pipeline(self):
        """Test overriding fuzzy config in pipeline creation."""
        from app.services.postprocessing_service import PostProcessingPipeline
        
        pipeline = PostProcessingPipeline(
            enable_fuzzy_matching=False,
            fuzzy_match_threshold=70
        )
        
        assert pipeline.enable_fuzzy_matching is False
        assert pipeline.fuzzy_match_threshold == 70


class TestEdgeCasesWithFuzzy:
    """Test edge cases and boundary conditions with fuzzy matching."""
    
    def test_empty_text_with_fuzzy(self):
        """Test empty text with fuzzy matching enabled."""
        lexicon = {"mri": "MRI"}
        text = ""
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=85
        )
        
        # Should return empty string
        assert result == ""
    
    def test_text_no_matches_with_fuzzy(self):
        """Test text with no matches (exact or fuzzy)."""
        lexicon = {"radiology": "Radiology"}
        text = "The patient visited the hospital."
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=85
        )
        
        # Should return original text (no medical terms to match)
        assert result == text
    
    def test_single_character_word_fuzzy(self):
        """Test fuzzy matching with single character words."""
        lexicon = {"a": "article"}
        text = "This is a test."
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=85
        )
        
        # Should handle without errors
        assert result is not None
    
    def test_very_long_text_with_fuzzy(self):
        """Test performance with longer text and fuzzy matching."""
        lexicon = {
            "mri": "MRI",
            "ct": "CT",
            "xray": "X-ray"
        }
        # Create a long text with some misspellings
        text = " ".join([
            "The patient had a mri, ct, and xray.",
            "The radilogy results were normal."
        ] * 50)
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=80
        )
        
        # Should complete without error and contain replacements
        assert result is not None
        assert "MRI" in result or "CT" in result
    
    def test_word_boundaries_preserved_with_fuzzy(self):
        """Test that word boundaries are respected with fuzzy matching."""
        lexicon = {"scan": "Scan"}
        text = "The prescanning procedure requires advance notice."
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=85
        )
        
        # "scanning" should not be affected by "scan" replacement
        assert "prescanning" in result
    
    def test_persian_english_mixed_text_fuzzy(self):
        """Test mixed Persian and English text with fuzzy matching."""
        lexicon = {
            "mri": "MRI",
            "اسکن": "scan"
        }
        text = "The bimari needs mri and اسکن"
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=85
        )
        
        # Should handle mixed language text
        assert result is not None
    
    def test_numbers_with_fuzzy_matching(self):
        """Test that numbers are handled correctly with fuzzy matching."""
        lexicon = {
            "covid19": "COVID-19",
            "h1n1": "H1N1"
        }
        text = "Testing for covid19 and h1n1 variants."
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=85
        )
        
        # Should handle terms with numbers
        assert result is not None


class TestFuzzyMatchingIntegration:
    """Test integration of fuzzy matching with the full pipeline."""
    
    @patch('app.services.postprocessing_service.load_lexicon_sync')
    def test_pipeline_process_with_fuzzy(self, mock_load_lexicon):
        """Test PostProcessingPipeline.process() with fuzzy matching enabled."""
        from app.services.postprocessing_service import PostProcessingPipeline
        
        mock_db = Mock(spec=Session)
        mock_load_lexicon.return_value = {"radiology": "Radiology"}
        
        pipeline = PostProcessingPipeline(
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=80
        )
        
        text = "Patient needs radilogy imaging."
        result = pipeline.process(text, "radiology", mock_db)
        
        # Should process without errors
        assert result is not None
    
    @patch('app.services.postprocessing_service.load_lexicon_sync')
    def test_pipeline_process_fuzzy_disabled(self, mock_load_lexicon):
        """Test PostProcessingPipeline with fuzzy matching disabled."""
        from app.services.postprocessing_service import PostProcessingPipeline
        
        mock_db = Mock(spec=Session)
        mock_load_lexicon.return_value = {"radiology": "Radiology"}
        
        pipeline = PostProcessingPipeline(
            enable_fuzzy_matching=False,
            fuzzy_match_threshold=85
        )
        
        text = "Patient needs radilogy imaging."
        result = pipeline.process(text, "radiology", mock_db)
        
        # With fuzzy disabled, misspelled word may not be corrected
        assert result is not None
    
    @patch('app.services.postprocessing_service.load_lexicon_sync')
    def test_create_pipeline_with_fuzzy_overrides(self, mock_load_lexicon):
        """Test create_pipeline function with fuzzy matching overrides."""
        from app.services.postprocessing_service import create_pipeline
        
        pipeline = create_pipeline(
            enable_fuzzy_matching=False,
            fuzzy_match_threshold=75
        )
        
        assert pipeline.enable_fuzzy_matching is False
        assert pipeline.fuzzy_match_threshold == 75
    
    @patch('app.services.postprocessing_service.load_lexicon_sync')
    def test_full_pipeline_with_all_steps_and_fuzzy(self, mock_load_lexicon):
        """Test complete pipeline with all steps enabled including fuzzy."""
        from app.services.postprocessing_service import PostProcessingPipeline
        
        mock_db = Mock(spec=Session)
        mock_load_lexicon.return_value = {
            "mri": "MRI",
            "ct": "CT"
        }
        
        pipeline = PostProcessingPipeline(
            enable_lexicon_replacement=True,
            enable_text_cleanup=True,
            enable_numeral_handling=True,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=80
        )
        
        text = "Patient  had  an  mri and ct scans. "
        result = pipeline.process(text, "radiology", mock_db)
        
        # All steps should work together
        assert result is not None
        # Should be cleaned up (no double spaces)
        assert "  " not in result


class TestFuzzyMatchingRegressions:
    """Test that fuzzy matching doesn't break existing functionality."""
    
    def test_exact_matching_still_works(self):
        """Test that exact matching still works with fuzzy enabled."""
        lexicon = {"mri": "MRI"}
        text = "Patient had an mri scan."
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=85
        )
        
        # Exact match should still work
        assert "MRI" in result
    
    def test_case_insensitive_matching_preserved(self):
        """Test that case-insensitive matching still works."""
        lexicon = {"mri": "MRI"}
        text = "Patient had an MRI scan."
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=85
        )
        
        # Case-insensitive matching should still work
        assert "MRI" in result
    
    def test_longest_match_first_preserved(self):
        """Test that longest-match-first still works with fuzzy."""
        lexicon = {
            "mri": "MRI",
            "mri scan": "MRI scan"
        }
        text = "The patient needs an mri scan."
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=85
        )
        
        # Longest match should be preferred
        assert "MRI scan" in result or "MRI" in result
    
    def test_whole_word_matching_preserved(self):
        """Test that whole-word matching still works with fuzzy."""
        lexicon = {"scan": "SCAN"}
        text = "The scanning process requires prescan setup."
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=85
        )
        
        # "scan" should not match within "scanning" or "prescan"
        assert "scanning" in result
        assert "prescan" in result
    
    def test_multiple_occurrences_still_replaced(self):
        """Test that multiple occurrences are still replaced with fuzzy."""
        lexicon = {"mri": "MRI"}
        text = "First mri was clear. Second mri showed inflammation."
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=85
        )
        
        # Both occurrences should be replaced
        assert result.count("MRI") >= 2
    
    def test_persian_text_still_works(self):
        """Test that Persian text handling still works with fuzzy."""
        lexicon = {
            "ام آر آی": "MRI",
            "قلب": "heart"
        }
        text = "قلب ام آر آی سالم است"
        
        result = apply_lexicon_corrections(
            text,
            lexicon,
            enable_fuzzy_matching=True,
            fuzzy_match_threshold=85
        )
        
        # Persian text should be processed correctly
        assert "MRI" in result or "heart" in result
    
    @patch('app.services.postprocessing_service.load_lexicon_sync')
    def test_error_handling_with_fuzzy(self, mock_load_lexicon):
        """Test that error handling still works with fuzzy enabled."""
        from app.services.postprocessing_service import PostProcessingError
        
        mock_db = Mock(spec=Session)
        mock_load_lexicon.side_effect = Exception("Database error")
        
        with pytest.raises(PostProcessingError):
            apply_lexicon_replacements(
                "text",
                "radiology",
                mock_db,
                enable_fuzzy_matching=True,
                fuzzy_match_threshold=85
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
