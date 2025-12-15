"""
Unit tests for text cleanup and normalization utilities.

Tests cover all cleanup operations including:
- Whitespace normalization
- Persian character normalization
- Punctuation consistency
- Transcription artifact removal
- Configuration toggles
- Edge cases
"""
import pytest

pytestmark = [pytest.mark.unit, pytest.mark.text_processing]

from app.services.text_cleanup import (
    cleanup_text,
    normalize_whitespace,
    normalize_persian_characters,
    normalize_punctuation,
    remove_transcription_artifacts,
    apply_unicode_normalization,
)


class TestWhitespaceNormalization:
    """Tests for whitespace normalization."""
    
    def test_trim_leading_trailing_spaces(self):
        """Test removal of leading and trailing whitespace."""
        text = "   Hello World   "
        result = cleanup_text(text)
        assert result == "Hello World"
    
    def test_collapse_multiple_spaces(self):
        """Test collapsing multiple consecutive spaces."""
        text = "Hello    World"
        result = cleanup_text(text)
        assert result == "Hello World"
    
    def test_normalize_line_breaks(self):
        """Test normalization of different line break styles."""
        text = "Line1\r\nLine2\rLine3\nLine4"
        result = cleanup_text(text)
        assert "\r" not in result
        assert result == "Line1\nLine2\nLine3\nLine4"
    
    def test_collapse_excessive_line_breaks(self):
        """Test collapsing excessive line breaks."""
        text = "Paragraph1\n\n\n\n\nParagraph2"
        result = cleanup_text(text)
        assert result == "Paragraph1\n\nParagraph2"
    
    def test_remove_spaces_at_line_boundaries(self):
        """Test removal of spaces at start/end of lines."""
        text = "  Line1  \n  Line2  \n  Line3  "
        result = cleanup_text(text)
        assert result == "Line1\nLine2\nLine3"
    
    def test_mixed_whitespace_issues(self):
        """Test handling of multiple whitespace issues together."""
        text = "   Hello    World  \n\n\n  Next  Line   "
        result = cleanup_text(text)
        assert result == "Hello World\n\nNext Line"
    
    def test_whitespace_with_persian_text(self):
        """Test whitespace normalization with Persian text."""
        text = "   سلام    دنیا   "
        result = cleanup_text(text)
        assert result == "سلام دنیا"
    
    def test_disable_whitespace_normalization(self):
        """Test disabling whitespace normalization."""
        text = "  Hello    World  "
        config = {"normalize_whitespace": False}
        result = cleanup_text(text, config)
        assert result == text


class TestPersianCharacterNormalization:
    """Tests for Persian character normalization."""
    
    def test_normalize_arabic_yeh_to_persian(self):
        """Test normalization of Arabic ي to Persian ی."""
        # Arabic Yeh (U+064A) -> Persian Yeh (U+06CC)
        text = "سلام دنيا"  # With Arabic ي
        result = cleanup_text(text)
        assert result == "سلام دنیا"  # With Persian ی
    
    def test_normalize_arabic_kaf_to_persian(self):
        """Test normalization of Arabic ك to Persian ک."""
        # Arabic Kaf (U+0643) -> Persian Kaf (U+06A9)
        text = "كتاب"  # With Arabic ك
        result = cleanup_text(text)
        assert result == "کتاب"  # With Persian ک
    
    def test_normalize_alef_maksura_to_persian_yeh(self):
        """Test normalization of Arabic Alef Maksura to Persian Yeh."""
        # Arabic Alef Maksura (U+0649) -> Persian Yeh (U+06CC)
        text = "مصطفى"  # With Alef Maksura
        result = cleanup_text(text)
        assert result == "مصطفی"  # With Persian Yeh
    
    def test_multiple_persian_normalizations(self):
        """Test text with multiple Persian character variants."""
        text = "كتاب خوبي است"  # Mix of Arabic ك and ي
        result = cleanup_text(text)
        assert result == "کتاب خوبی است"  # All Persian forms
    
    def test_persian_text_with_english_mixed(self):
        """Test Persian normalization with mixed English text."""
        text = "Hello سلام دنيا World"
        result = cleanup_text(text)
        assert result == "Hello سلام دنیا World"
    
    def test_disable_persian_normalization(self):
        """Test disabling Persian character normalization."""
        text = "سلام دنيا"  # With Arabic ي
        config = {"normalize_persian_chars": False}
        result = cleanup_text(text, config)
        assert "ي" in result  # Arabic Yeh preserved


class TestPunctuationNormalization:
    """Tests for punctuation normalization."""
    
    def test_normalize_ellipsis_character(self):
        """Test normalization of ellipsis character to three periods."""
        text = "Wait… what"
        result = cleanup_text(text)
        assert result == "Wait... what"
    
    def test_remove_excessive_periods(self):
        """Test removal of excessive periods."""
        text = "Hello....... World"
        result = cleanup_text(text)
        assert result == "Hello... World"
    
    def test_remove_multiple_ellipsis(self):
        """Test collapsing multiple ellipsis."""
        text = "Hello... ... ... World"
        result = cleanup_text(text)
        assert result == "Hello... World"
    
    def test_normalize_en_dash_to_hyphen(self):
        """Test normalization of en-dash to hyphen."""
        text = "Hello–World"  # en-dash
        result = cleanup_text(text)
        assert result == "Hello-World"  # hyphen
    
    def test_preserve_em_dash(self):
        """Test that em-dash is preserved."""
        text = "Hello—World"  # em-dash
        result = cleanup_text(text)
        assert "—" in result
    
    def test_remove_excessive_question_marks(self):
        """Test normalization of excessive question marks."""
        text = "What???? Really????"
        result = cleanup_text(text)
        assert result == "What?? Really??"
    
    def test_remove_excessive_exclamation_marks(self):
        """Test normalization of excessive exclamation marks."""
        text = "Wow!!!! Amazing!!!!"
        result = cleanup_text(text)
        assert result == "Wow!! Amazing!!"
    
    def test_punctuation_with_persian_text(self):
        """Test punctuation normalization with Persian text."""
        text = "سلام… چطوری؟؟؟"
        result = cleanup_text(text)
        assert result == "سلام... چطوری??"
    
    def test_disable_punctuation_normalization(self):
        """Test disabling punctuation normalization."""
        text = "Wait… What????"
        config = {"normalize_punctuation": False}
        result = cleanup_text(text, config)
        assert "…" in result
        assert "????" in result


class TestTranscriptionArtifactRemoval:
    """Tests for transcription artifact removal."""
    
    def test_remove_timestamp_brackets(self):
        """Test removal of timestamp markers in brackets."""
        text = "[00:00:15] Hello world [00:01:30] Next part"
        result = cleanup_text(text)
        assert result == "Hello world Next part"
    
    def test_remove_timestamp_short_format(self):
        """Test removal of short timestamp markers."""
        text = "[01:30] Hello [12:45] World"
        result = cleanup_text(text)
        assert result == "Hello World"
    
    def test_remove_music_marker(self):
        """Test removal of [Music] marker."""
        text = "[Music] Hello World [Music]"
        result = cleanup_text(text)
        assert result == "Hello World"
    
    def test_remove_applause_marker(self):
        """Test removal of [Applause] marker."""
        text = "Great speech [Applause] Thank you"
        result = cleanup_text(text)
        assert result == "Great speech Thank you"
    
    def test_remove_laughter_marker(self):
        """Test removal of [Laughter] marker."""
        text = "That's funny [Laughter] Indeed"
        result = cleanup_text(text)
        assert result == "That's funny Indeed"
    
    def test_remove_inaudible_marker(self):
        """Test removal of [Inaudible] marker."""
        text = "I think [Inaudible] that's good"
        result = cleanup_text(text)
        assert result == "I think that's good"
    
    def test_remove_multiple_artifacts(self):
        """Test removal of multiple different artifacts."""
        text = "[00:00:00] [Music] Hello [Applause] World [Laughter]"
        result = cleanup_text(text)
        assert result == "Hello World"
    
    def test_remove_musical_notes(self):
        """Test removal of musical note markers."""
        text = "♪ La la la ♪ Hello World"
        result = cleanup_text(text)
        assert result == "Hello World"
    
    def test_artifacts_case_insensitive(self):
        """Test that artifact removal is case-insensitive."""
        text = "[MUSIC] Hello [music] World [Music]"
        result = cleanup_text(text)
        assert result == "Hello World"
    
    def test_artifacts_with_persian_text(self):
        """Test artifact removal with Persian text."""
        text = "[Music] سلام دنیا [Applause]"
        result = cleanup_text(text)
        assert result == "سلام دنیا"
    
    def test_disable_artifact_removal(self):
        """Test disabling artifact removal."""
        text = "[Music] Hello [00:01:30] World"
        config = {"remove_artifacts": False}
        result = cleanup_text(text, config)
        assert "[Music]" in result
        assert "[00:01:30]" in result


class TestUnicodeNormalization:
    """Tests for Unicode normalization."""
    
    def test_nfc_normalization(self):
        """Test NFC Unicode normalization."""
        # Decomposed form to composed form
        text = "café"  # é as e + combining accent
        config = {"unicode_normalization": "NFC"}
        result = cleanup_text(text, config)
        # NFC should produce composed characters
        assert result == "café"
    
    def test_nfkc_normalization(self):
        """Test NFKC Unicode normalization."""
        text = "ﬁle"  # Contains ligature fi (U+FB01)
        config = {"unicode_normalization": "NFKC"}
        result = cleanup_text(text, config)
        # NFKC should decompose ligatures
        assert result == "file"
    
    def test_disable_unicode_normalization(self):
        """Test disabling Unicode normalization."""
        text = "café"
        config = {"unicode_normalization": None}
        result = cleanup_text(text, config)
        # Should preserve original form
        assert "café" in result or "café" in result
    
    def test_invalid_normalization_form(self):
        """Test handling of invalid normalization form."""
        text = "Hello World"
        config = {"unicode_normalization": "INVALID"}
        # Should fallback to NFC without error
        result = cleanup_text(text, config)
        assert result == "Hello World"


class TestComprehensiveCleanup:
    """Tests for comprehensive cleanup with multiple operations."""
    
    def test_full_cleanup_english(self):
        """Test full cleanup pipeline with English text."""
        text = "  [Music]   Hello....    World  [00:01:30]  "
        result = cleanup_text(text)
        assert result == "Hello... World"
    
    def test_full_cleanup_persian(self):
        """Test full cleanup pipeline with Persian text."""
        text = "  [Music]  سلام   دنيا…  [Applause]  "
        result = cleanup_text(text)
        assert result == "سلام دنیا..."
    
    def test_full_cleanup_mixed_languages(self):
        """Test full cleanup with mixed Persian and English."""
        text = "  Hello  سلام  دنيا   World   "
        result = cleanup_text(text)
        assert result == "Hello سلام دنیا World"
    
    def test_complex_transcription_cleanup(self):
        """Test cleanup of complex transcription with multiple issues."""
        text = """
        [00:00:00] [Music]
        Hello    World....
        
        
        This is   a test.
        سلام   دنيا… 
        [Applause] [00:01:30]
        """
        result = cleanup_text(text)
        # Should remove artifacts, normalize whitespace and Persian chars
        assert "[Music]" not in result
        assert "[00:00:00]" not in result
        assert "[Applause]" not in result
        assert "دنیا" in result  # Persian ی not Arabic ي
        assert "    " not in result  # No multiple spaces
    
    def test_preserve_language_no_translation(self):
        """Test that original languages are preserved."""
        text = "Hello سلام مرحبا 你好 Bonjour"
        result = cleanup_text(text)
        # All languages should be preserved
        assert "Hello" in result
        assert "سلام" in result
        assert "مرحبا" in result
        assert "你好" in result
        assert "Bonjour" in result
    
    def test_preserve_meaning_minimal_changes(self):
        """Test that meaning is preserved with minimal changes."""
        text = "This is important. Really important!"
        result = cleanup_text(text)
        # Content should be fully preserved
        assert "important" in result
        assert "Really" in result
        assert result == "This is important. Really important!"


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""
    
    def test_empty_string(self):
        """Test handling of empty string."""
        result = cleanup_text("")
        assert result == ""
    
    def test_whitespace_only(self):
        """Test handling of whitespace-only string."""
        result = cleanup_text("     ")
        assert result == ""
    
    def test_artifacts_only(self):
        """Test handling of string with only artifacts."""
        text = "[Music] [Applause] [00:00:00]"
        result = cleanup_text(text)
        assert result == ""
    
    def test_single_word(self):
        """Test handling of single word."""
        result = cleanup_text("Hello")
        assert result == "Hello"
    
    def test_special_characters_preserved(self):
        """Test that special characters are preserved."""
        text = "Price: $100.50 (50% off)"
        result = cleanup_text(text)
        assert result == "Price: $100.50 (50% off)"
    
    def test_numbers_preserved(self):
        """Test that numbers are preserved."""
        text = "The year 2024 has 365 days"
        result = cleanup_text(text)
        assert result == "The year 2024 has 365 days"
    
    def test_urls_preserved(self):
        """Test that URLs are preserved."""
        text = "Visit https://example.com for more"
        result = cleanup_text(text)
        assert "https://example.com" in result
    
    def test_email_addresses_preserved(self):
        """Test that email addresses are preserved."""
        text = "Contact us at test@example.com"
        result = cleanup_text(text)
        assert "test@example.com" in result


class TestConfigurationOptions:
    """Tests for configuration options and toggles."""
    
    def test_all_operations_disabled(self):
        """Test with all cleanup operations disabled."""
        text = "  [Music] سلام دنيا… World....  "
        config = {
            "normalize_whitespace": False,
            "normalize_persian_chars": False,
            "normalize_punctuation": False,
            "remove_artifacts": False,
            "unicode_normalization": None,
        }
        result = cleanup_text(text, config)
        # Nothing should change except final strip
        assert "[Music]" in result
        assert "…" in result
        assert "...." in result
    
    def test_selective_operations(self):
        """Test enabling only specific operations."""
        text = "  [Music] Hello.... World  "
        config = {
            "normalize_whitespace": True,
            "normalize_persian_chars": False,
            "normalize_punctuation": False,
            "remove_artifacts": False,
        }
        result = cleanup_text(text, config)
        # Only whitespace should be cleaned
        assert "[Music]" in result
        assert "...." in result
        assert "  " not in result  # Multiple spaces removed
    
    def test_custom_config_merges_with_defaults(self):
        """Test that custom config merges with defaults."""
        text = "  Hello  World  "
        config = {"normalize_whitespace": True}
        result = cleanup_text(text, config)
        # Should still apply other default operations
        assert result == "Hello World"
    
    def test_none_config_uses_defaults(self):
        """Test that None config uses all defaults."""
        text = "  [Music] Hello... World  "
        result = cleanup_text(text, config=None)
        # Should apply all default operations
        assert result == "Hello... World"


class TestFunctionIndependence:
    """Tests for individual cleanup functions."""
    
    def test_normalize_whitespace_function(self):
        """Test normalize_whitespace function directly."""
        text = "  Hello    World  "
        config = {"normalize_whitespace": True}
        result = normalize_whitespace(text, config)
        assert result == "Hello World"
    
    def test_normalize_persian_characters_function(self):
        """Test normalize_persian_characters function directly."""
        text = "سلام دنيا"
        config = {"normalize_persian_chars": True}
        result = normalize_persian_characters(text, config)
        assert result == "سلام دنیا"
    
    def test_normalize_punctuation_function(self):
        """Test normalize_punctuation function directly."""
        text = "Hello… World????"
        config = {"normalize_punctuation": True}
        result = normalize_punctuation(text, config)
        assert result == "Hello... World??"
    
    def test_remove_transcription_artifacts_function(self):
        """Test remove_transcription_artifacts function directly."""
        text = "[Music] Hello [00:01:30] World"
        config = {"remove_artifacts": True}
        result = remove_transcription_artifacts(text, config)
        assert "[Music]" not in result
        assert "[00:01:30]" not in result
    
    def test_apply_unicode_normalization_function(self):
        """Test apply_unicode_normalization function directly."""
        text = "café"
        config = {"unicode_normalization": "NFC"}
        result = apply_unicode_normalization(text, config)
        # Should normalize to composed form
        assert "café" in result or "café" in result
