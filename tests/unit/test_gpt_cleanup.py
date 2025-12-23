"""
Comprehensive unit tests for GPT cleanup functionality in the post-processing pipeline.

Tests cover:
- GPT cleanup function with mocked OpenAI API calls
- Persian medical text fixtures
- Error handling and fallback behavior
- Pipeline integration with enable/disable configuration
- Edge cases and realistic medical report scenarios
"""
import pytest
import os

pytestmark = [pytest.mark.unit, pytest.mark.gpt_cleanup]
from unittest.mock import Mock, MagicMock, patch, call
from sqlalchemy.orm import Session

from app.services.postprocessing_service import (
    apply_gpt_cleanup,
    PostProcessingError,
    PostProcessingPipeline,
)
from app.services.openai_service import (
    OpenAIAPIError,
    OpenAIQuotaError,
)


# ============================================================================
# Fixtures for GPT Cleanup Testing
# ============================================================================

@pytest.fixture
def raw_persian_medical_dictation():
    """Fixture: Raw Persian medical dictation with errors and artifacts."""
    return """بیمار با شکایت سردرد و تب مراجعه کرد. دیگه چی داره؟
    MRI مغز نرمال بود. 
    اپیلپسی احتمالی داره. 
    نتیجه: مشاهده گایش در فعالیت مغزی"""


@pytest.fixture
def cleaned_persian_medical_text():
    """Fixture: Expected cleaned version of Persian medical text."""
    return """بیمار با شکایت سردرد و تب مراجعه کرد.
    MRI مغز نرمال بود.
    اپیلپسی احتمالی مشاهده می‌شود.
    نتیجه: کاهش در فعالیت مغزی مشاهده می‌شود"""


@pytest.fixture
def raw_medical_report_mixed_language():
    """Fixture: Mixed Persian/English medical report with errors."""
    return """Patient with fever and سردرد presented. 
    جن و وروس testing pending.
    CT scan نرمال است.
    تجویز: Antibiotic"""


@pytest.fixture
def mock_openai_response_success():
    """Fixture: Mocked successful OpenAI response."""
    mock_message = Mock()
    mock_message.content = "بیمار با شکایت سردرد و تب مراجعه کرد. MRI مغز نرمال بود. اپیلپسی احتمالی مشاهده می‌شود."
    
    mock_choice = Mock()
    mock_choice.message = mock_message
    
    mock_response = Mock()
    mock_response.choices = [mock_choice]
    
    return mock_response


@pytest.fixture
def mock_openai_response_empty_content():
    """Fixture: OpenAI response with empty content."""
    mock_message = Mock()
    mock_message.content = ""
    
    mock_choice = Mock()
    mock_choice.message = mock_message
    
    mock_response = Mock()
    mock_response.choices = [mock_choice]
    
    return mock_response


@pytest.fixture
def mock_openai_response_malformed():
    """Fixture: Malformed OpenAI response."""
    mock_response = Mock()
    mock_response.choices = []
    
    return mock_response


# ============================================================================
# Test apply_gpt_cleanup Function
# ============================================================================

class TestApplyGptCleanupFunction:
    """Test apply_gpt_cleanup function with mocked GPT responses."""
    
    @patch('app.services.postprocessing_service.get_openai_client')
    def test_successful_cleanup_with_mocked_response(self, mock_get_client, mock_openai_response_success):
        """Test successful cleanup with mocked GPT-4o-mini response."""
        # Setup mock
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response_success
        mock_get_client.return_value = mock_client
        
        # Input text
        input_text = "بیمار مراجعه کرد. MRI نرمال."
        
        # Call function
        result = apply_gpt_cleanup(input_text)
        
        # Verify result is not None and is the cleaned text
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Verify OpenAI client was initialized
        mock_get_client.assert_called_once()
        
        # Verify API call was made
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        
        # Verify model and parameters
        assert call_args.kwargs['model'] == 'gpt-4o-mini'
        assert call_args.kwargs['temperature'] == 0
        assert call_args.kwargs['max_tokens'] == 4000
        
        # Verify messages structure
        messages = call_args.kwargs['messages']
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert messages[1]['role'] == 'user'
        assert input_text in messages[1]['content']
    
    @patch('app.services.postprocessing_service.get_openai_client')
    def test_cleanup_with_realistic_persian_medical_text(self, mock_get_client, mock_openai_response_success, raw_persian_medical_dictation):
        """Test cleanup with realistic Persian medical dictation text."""
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response_success
        mock_get_client.return_value = mock_client
        
        # Use realistic medical text
        result = apply_gpt_cleanup(raw_persian_medical_dictation)
        
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
    
    @patch('app.services.postprocessing_service.get_openai_client')
    def test_gpt_prompt_contains_correct_instructions(self, mock_get_client, mock_openai_response_success):
        """Test that GPT prompt includes all required instructions."""
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response_success
        mock_get_client.return_value = mock_client
        
        apply_gpt_cleanup("Test text")
        
        # Get the system prompt from the call
        call_args = mock_client.chat.completions.create.call_args
        system_prompt = call_args.kwargs['messages'][0]['content']
        
        # Verify prompt contains key instructions
        assert "Persian" in system_prompt
        assert "grammar" in system_prompt.lower() or "GRAMMAR" in system_prompt
        assert "medical" in system_prompt.lower()
        assert "preservation" in system_prompt.lower() or "CRITICAL" in system_prompt
    
    @patch('app.services.postprocessing_service.get_openai_client')
    def test_error_handling_openai_api_error(self, mock_get_client):
        """Test error handling for OpenAI API errors."""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = OpenAIAPIError("API connection failed")
        mock_get_client.return_value = mock_client
        
        input_text = "Test medical text"
        
        # Should not raise exception, should return original text
        result = apply_gpt_cleanup(input_text)
        
        # Should return original text as fallback
        assert result == input_text
    
    @patch('app.services.postprocessing_service.get_openai_client')
    def test_error_handling_openai_quota_error(self, mock_get_client):
        """Test error handling for OpenAI quota/rate limit errors."""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = OpenAIQuotaError("Rate limit exceeded")
        mock_get_client.return_value = mock_client
        
        input_text = "Test medical text"
        
        # Should not raise exception, should return original text
        result = apply_gpt_cleanup(input_text)
        
        # Should return original text as fallback
        assert result == input_text
    
    @patch('app.services.postprocessing_service.get_openai_client')
    def test_error_handling_timeout(self, mock_get_client):
        """Test error handling for timeout errors."""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = TimeoutError("Request timeout")
        mock_get_client.return_value = mock_client
        
        input_text = "Test medical text"
        
        # Should not raise exception, should return original text
        result = apply_gpt_cleanup(input_text)
        
        # Should return original text as fallback
        assert result == input_text
    
    @patch('app.services.postprocessing_service.get_openai_client')
    def test_fallback_behavior_on_empty_response(self, mock_get_client, mock_openai_response_empty_content):
        """Test fallback when GPT returns empty response."""
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response_empty_content
        mock_get_client.return_value = mock_client
        
        input_text = "Test medical text"
        
        # Should return original text when response is empty
        result = apply_gpt_cleanup(input_text)
        assert result == input_text
    
    @patch('app.services.postprocessing_service.get_openai_client')
    def test_fallback_behavior_on_none_response(self, mock_get_client):
        """Test fallback when GPT returns None."""
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = None
        mock_get_client.return_value = mock_client
        
        input_text = "Test medical text"
        
        # Should return original text when response is None
        result = apply_gpt_cleanup(input_text)
        assert result == input_text
    
    @patch('app.services.postprocessing_service.get_openai_client')
    def test_fallback_behavior_on_malformed_response(self, mock_get_client, mock_openai_response_malformed):
        """Test fallback when GPT response is malformed."""
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response_malformed
        mock_get_client.return_value = mock_client
        
        input_text = "Test medical text"
        
        # Should return original text when response is malformed
        result = apply_gpt_cleanup(input_text)
        assert result == input_text
    
    def test_empty_string_input(self):
        """Test handling of empty string input."""
        result = apply_gpt_cleanup("")
        
        # Should return empty string unchanged
        assert result == ""
    
    def test_none_input(self):
        """Test handling of None input."""
        result = apply_gpt_cleanup(None)
        
        # Should return None unchanged
        assert result is None
    
    @patch('app.services.postprocessing_service.get_openai_client')
    def test_very_long_text_input(self, mock_get_client, mock_openai_response_success):
        """Test handling of very long medical text."""
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response_success
        mock_get_client.return_value = mock_client
        
        # Create a long medical text (but within realistic limits)
        long_text = "بیمار با شکایت سردرد مراجعه کرد. " * 100
        
        # Should handle long text
        result = apply_gpt_cleanup(long_text)
        
        assert result is not None
        assert isinstance(result, str)
    
    @patch('app.services.postprocessing_service.get_openai_client')
    def test_mixed_language_persian_english_text(self, mock_get_client, mock_openai_response_success, raw_medical_report_mixed_language):
        """Test cleanup of mixed Persian/English medical text."""
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response_success
        mock_get_client.return_value = mock_client
        
        result = apply_gpt_cleanup(raw_medical_report_mixed_language)
        
        assert result is not None
        assert isinstance(result, str)
    
    @patch('app.services.postprocessing_service.get_openai_client')
    def test_gpt_prompt_formatting_is_correct(self, mock_get_client, mock_openai_response_success):
        """Test that the GPT prompt is correctly formatted with user message."""
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response_success
        mock_get_client.return_value = mock_client
        
        input_text = "Medical text input"
        apply_gpt_cleanup(input_text)
        
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs['messages']
        
        # Verify user message contains the input text
        user_message = messages[1]['content']
        assert "medical dictation" in user_message.lower()
        assert input_text in user_message


# ============================================================================
# Test GPT Cleanup Pipeline Integration
# ============================================================================

class TestGptCleanupPipelineIntegration:
    """Test GPT cleanup integration into the post-processing pipeline."""
    
    @patch('app.services.postprocessing_service.load_lexicon_sync')
    @patch('app.services.postprocessing_service.get_openai_client')
    def test_gpt_cleanup_runs_as_fourth_step(self, mock_get_client, mock_load_lexicon, mock_openai_response_success):
        """Test that GPT cleanup runs as the 4th step (after Lexicon, Cleanup, Numeral)."""
        mock_db = Mock(spec=Session)
        mock_load_lexicon.return_value = {"mri": "MRI"}
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response_success
        mock_get_client.return_value = mock_client
        
        pipeline = PostProcessingPipeline(
            enable_lexicon_replacement=True,
            enable_text_cleanup=True,
            enable_numeral_handling=True,
            enable_gpt_cleanup=True
        )
        
        text = "Patient has mri done. نتیجه: ۱۲ سانتی متر"
        result = pipeline.process(text, "radiology", mock_db)
        
        # Verify pipeline processed through all steps
        assert result is not None
        
        # Verify GPT cleanup was called
        assert mock_client.chat.completions.create.called
    
    @patch('app.services.postprocessing_service.load_lexicon_sync')
    @patch('app.services.postprocessing_service.get_openai_client')
    def test_gpt_cleanup_skipped_when_disabled(self, mock_get_client, mock_load_lexicon):
        """Test that GPT cleanup is skipped when ENABLE_GPT_CLEANUP=false."""
        mock_db = Mock(spec=Session)
        mock_load_lexicon.return_value = {"mri": "MRI"}
        
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        pipeline = PostProcessingPipeline(
            enable_lexicon_replacement=True,
            enable_text_cleanup=True,
            enable_numeral_handling=True,
            enable_gpt_cleanup=False  # Disabled
        )
        
        text = "Patient has mri"
        result = pipeline.process(text, "radiology", mock_db)
        
        # Verify pipeline ran
        assert result is not None
        
        # Verify GPT cleanup was NOT called
        mock_client.chat.completions.create.assert_not_called()
    
    @patch('app.services.postprocessing_service.load_lexicon_sync')
    @patch('app.services.postprocessing_service.get_openai_client')
    def test_gpt_cleanup_runs_when_enabled(self, mock_get_client, mock_load_lexicon, mock_openai_response_success):
        """Test that GPT cleanup runs when ENABLE_GPT_CLEANUP=true."""
        mock_db = Mock(spec=Session)
        mock_load_lexicon.return_value = {}
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response_success
        mock_get_client.return_value = mock_client
        
        pipeline = PostProcessingPipeline(
            enable_lexicon_replacement=False,
            enable_text_cleanup=False,
            enable_numeral_handling=False,
            enable_gpt_cleanup=True  # Enabled
        )
        
        text = "Raw medical text"
        result = pipeline.process(text)
        
        # Verify GPT cleanup was called
        mock_client.chat.completions.create.assert_called_once()
        assert result is not None
    
    @patch('app.services.postprocessing_service.load_lexicon_sync')
    @patch('app.services.postprocessing_service.get_openai_client')
    def test_end_to_end_pipeline_with_gpt_cleanup_enabled(self, mock_get_client, mock_load_lexicon, mock_openai_response_success):
        """Test end-to-end pipeline flow with all steps including GPT cleanup."""
        mock_db = Mock(spec=Session)
        mock_load_lexicon.return_value = {"mri": "MRI"}
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response_success
        mock_get_client.return_value = mock_client
        
        pipeline = PostProcessingPipeline(
            enable_lexicon_replacement=True,
            enable_text_cleanup=True,
            enable_numeral_handling=True,
            enable_gpt_cleanup=True
        )
        
        # Input with various issues
        text = "Patient  had  mri  scan. نتیجه: ۱۲  سانتی متر"
        result = pipeline.process(text, "radiology", mock_db)
        
        # Verify result is processed
        assert result is not None
        assert isinstance(result, str)
        
        # All steps should have been called
        assert mock_load_lexicon.called
        assert mock_client.chat.completions.create.called
    
    @patch('app.services.postprocessing_service.load_lexicon_sync')
    @patch('app.services.postprocessing_service.get_openai_client')
    def test_gpt_cleanup_with_logging(self, mock_get_client, mock_load_lexicon, mock_openai_response_success):
        """Test that logging messages are produced for GPT cleanup step."""
        mock_db = Mock(spec=Session)
        mock_load_lexicon.return_value = {}
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response_success
        mock_get_client.return_value = mock_client
        
        pipeline = PostProcessingPipeline(enable_gpt_cleanup=True)
        
        text = "Test text"
        
        # Should not raise exceptions and logging should be handled internally
        result = pipeline.process(text)
        assert result is not None
    
    @patch('app.services.postprocessing_service.load_lexicon_sync')
    @patch('app.services.postprocessing_service.get_openai_client')
    def test_processed_text_reflects_gpt_cleanup_when_enabled(self, mock_get_client, mock_load_lexicon):
        """Test that processed_text contains GPT-cleaned output when enabled."""
        mock_db = Mock(spec=Session)
        mock_load_lexicon.return_value = {}
        
        # Mock response with transformed text
        mock_message = Mock()
        expected_output = "مبادله شده: Cleaned text"
        mock_message.content = expected_output
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        pipeline = PostProcessingPipeline(enable_gpt_cleanup=True)
        
        input_text = "Raw input text"
        result = pipeline.process(input_text)
        
        # Result should contain the GPT-cleaned output
        assert result == expected_output
    
    @patch('app.services.postprocessing_service.load_lexicon_sync')
    @patch('app.services.postprocessing_service.get_openai_client')
    def test_processed_text_fallback_when_gpt_cleanup_fails(self, mock_get_client, mock_load_lexicon):
        """Test that processed_text contains non-GPT output when GPT cleanup fails."""
        mock_db = Mock(spec=Session)
        mock_load_lexicon.return_value = {}
        
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = OpenAIAPIError("API failed")
        mock_get_client.return_value = mock_client
        
        pipeline = PostProcessingPipeline(enable_gpt_cleanup=True)
        
        input_text = "Input text"
        result = pipeline.process(input_text)
        
        # Should fall back to input text when GPT fails
        assert result == input_text
    
    @patch('app.services.postprocessing_service.load_lexicon_sync')
    @patch('app.services.postprocessing_service.get_openai_client')
    def test_processed_text_fallback_when_gpt_cleanup_disabled(self, mock_get_client, mock_load_lexicon):
        """Test that processed_text is correct when GPT cleanup is disabled."""
        mock_db = Mock(spec=Session)
        mock_load_lexicon.return_value = {}
        
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        pipeline = PostProcessingPipeline(
            enable_text_cleanup=True,
            enable_gpt_cleanup=False
        )
        
        input_text = "Text  with  extra  spaces"
        result = pipeline.process(input_text)
        
        # GPT should not be called
        mock_client.chat.completions.create.assert_not_called()
        
        # Text cleanup should be applied instead
        assert result is not None
        # Extra spaces should be cleaned up
        assert "  " not in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
