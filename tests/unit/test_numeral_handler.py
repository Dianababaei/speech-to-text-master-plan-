"""
Unit tests for numeral_handler service.

Tests cover:
- Simple numeral conversion (Persian ↔ English)
- Medical term preservation (vertebral levels, measurements)
- Mixed text with Persian and English content
- Edge cases (decimals, ranges, mixed numerals)
- All strategy options (english/persian/preserve/context_aware)
"""

import pytest
from app.services.numeral_handler import (
    persian_to_english,
    english_to_persian,
    detect_medical_terms,
    is_position_in_medical_term,
    process_numerals,
    apply_english_strategy,
    apply_persian_strategy,
    apply_context_aware_strategy,
)


class TestBasicNumeralConversion:
    """Test basic Persian ↔ English numeral conversion."""
    
    def test_persian_to_english_simple(self):
        """Test converting Persian numerals to English."""
        text = "۱۲۳۴۵۶۷۸۹۰"
        expected = "1234567890"
        assert persian_to_english(text) == expected
    
    def test_english_to_persian_simple(self):
        """Test converting English numerals to Persian."""
        text = "1234567890"
        expected = "۱۲۳۴۵۶۷۸۹۰"
        assert english_to_persian(text) == expected
    
    def test_persian_to_english_mixed_text(self):
        """Test converting Persian numerals in mixed text."""
        text = "بیمار ۳۵ ساله"
        expected = "بیمار 35 ساله"
        assert persian_to_english(text) == expected
    
    def test_english_to_persian_mixed_text(self):
        """Test converting English numerals in mixed text."""
        text = "بیمار 35 ساله"
        expected = "بیمار ۳۵ ساله"
        assert english_to_persian(text) == expected
    
    def test_no_numerals(self):
        """Test text without numerals remains unchanged."""
        text = "این متن بدون عدد است"
        assert persian_to_english(text) == text
        assert english_to_persian(text) == text
    
    def test_decimal_numbers(self):
        """Test handling decimal numbers."""
        persian_text = "۳.۵ میلیمتر"
        expected = "3.5 میلیمتر"
        assert persian_to_english(persian_text) == expected
        
        english_text = "3.5 میلیمتر"
        expected_persian = "۳.۵ میلیمتر"
        assert english_to_persian(english_text) == expected_persian


class TestMedicalTermDetection:
    """Test detection of medical terms with numerals."""
    
    def test_detect_vertebral_levels(self):
        """Test detecting vertebral level codes."""
        text = "مشکل در L4 و T12 مشاهده شد"
        medical_terms = detect_medical_terms(text)
        assert len(medical_terms) == 2
        assert any("L4" in term[2] for term in medical_terms)
        assert any("T12" in term[2] for term in medical_terms)
    
    def test_detect_vertebral_ranges(self):
        """Test detecting vertebral level ranges."""
        text = "ناحیه L4-L5 تحت فشار است"
        medical_terms = detect_medical_terms(text)
        assert len(medical_terms) == 1
        assert "L4-L5" in medical_terms[0][2]
    
    def test_detect_measurements(self):
        """Test detecting measurements with units."""
        text = "دوز 10mg با اندازه 5cm و عمق 3.5mm"
        medical_terms = detect_medical_terms(text)
        assert len(medical_terms) == 3
        # Check that measurements are detected
        detected_texts = [term[2] for term in medical_terms]
        assert "10mg" in detected_texts
        assert "5cm" in detected_texts
        assert "3.5mm" in detected_texts
    
    def test_detect_medical_codes(self):
        """Test detecting medical codes with numbers."""
        text = "تشخیص با کد T1 و C3-C4"
        medical_terms = detect_medical_terms(text)
        assert len(medical_terms) == 2
    
    def test_no_medical_terms(self):
        """Test text without medical terms."""
        text = "بیمار 35 ساله با درد مزمن"
        medical_terms = detect_medical_terms(text)
        assert len(medical_terms) == 0
    
    def test_is_position_in_medical_term(self):
        """Test checking if position is within medical term."""
        text = "مشکل در L4 مشاهده شد"
        medical_terms = detect_medical_terms(text)
        
        # Position within "L4"
        l4_start = text.index("L4")
        assert is_position_in_medical_term(l4_start, medical_terms)
        assert is_position_in_medical_term(l4_start + 1, medical_terms)
        
        # Position outside medical term
        assert not is_position_in_medical_term(0, medical_terms)
        assert not is_position_in_medical_term(len(text) - 1, medical_terms)


class TestEnglishStrategy:
    """Test English numeral strategy."""
    
    def test_convert_persian_to_english(self):
        """Test converting Persian numerals to English."""
        text = "بیمار ۳۵ ساله با فشار خون ۱۲۰/۸۰"
        result, count = apply_english_strategy(text)
        assert result == "بیمار 35 ساله با فشار خون 120/80"
        assert count == 5  # ۳۵۱۲۰۸۰
    
    def test_already_english(self):
        """Test text with already English numerals."""
        text = "بیمار 35 ساله"
        result, count = apply_english_strategy(text)
        assert result == text
        assert count == 0
    
    def test_mixed_numerals(self):
        """Test text with mixed Persian and English numerals."""
        text = "بیمار ۳۵ ساله با وزن 70 کیلوگرم"
        result, count = apply_english_strategy(text)
        assert result == "بیمار 35 ساله با وزن 70 کیلوگرم"
        assert count == 2  # ۳۵


class TestPersianStrategy:
    """Test Persian numeral strategy."""
    
    def test_convert_english_to_persian(self):
        """Test converting English numerals to Persian."""
        text = "بیمار 35 ساله با فشار خون 120/80"
        result, count = apply_persian_strategy(text)
        assert result == "بیمار ۳۵ ساله با فشار خون ۱۲۰/۸۰"
        assert count == 5  # 35120/80
    
    def test_already_persian(self):
        """Test text with already Persian numerals."""
        text = "بیمار ۳۵ ساله"
        result, count = apply_persian_strategy(text)
        assert result == text
        assert count == 0
    
    def test_mixed_numerals(self):
        """Test text with mixed Persian and English numerals."""
        text = "بیمار ۳۵ ساله با وزن 70 کیلوگرم"
        result, count = apply_persian_strategy(text)
        assert result == "بیمار ۳۵ ساله با وزن ۷۰ کیلوگرم"
        assert count == 2  # 70


class TestContextAwareStrategy:
    """Test context-aware numeral strategy."""
    
    def test_preserves_medical_codes(self):
        """Test that medical codes keep English numerals."""
        text = "مشکل در L4-L5 مشاهده شد"
        result, _ = apply_context_aware_strategy(text)
        # L4-L5 should remain in English
        assert "L4-L5" in result
    
    def test_converts_standalone_numbers(self):
        """Test that standalone numbers convert to Persian."""
        text = "بیمار 35 ساله"
        result, _ = apply_context_aware_strategy(text)
        # 35 should convert to Persian
        assert "۳۵" in result
    
    def test_mixed_medical_and_standalone(self):
        """Test mixed medical codes and standalone numbers."""
        text = "بیمار 35 ساله با مشکل در L4-L5"
        result, _ = apply_context_aware_strategy(text)
        # L4-L5 stays English, 35 converts to Persian
        assert "۳۵" in result
        assert "L4-L5" in result
    
    def test_measurements_stay_english(self):
        """Test that measurements keep English numerals."""
        text = "دوز 10mg با طول 5cm"
        result, _ = apply_context_aware_strategy(text)
        # Measurements should stay in English
        assert "10mg" in result
        assert "5cm" in result
    
    def test_complex_medical_text(self):
        """Test complex text with multiple medical terms."""
        text = "بیمار 45 ساله با آسیب L4-L5 و دوز 10mg در ناحیه C3-C4"
        result, _ = apply_context_aware_strategy(text)
        # Medical codes and measurements stay English
        assert "L4-L5" in result
        assert "10mg" in result
        assert "C3-C4" in result
        # Standalone age converts to Persian
        assert "۴۵" in result
    
    def test_persian_numerals_in_medical_terms(self):
        """Test that Persian numerals in medical terms convert to English."""
        text = "مشکل در L۴-L۵ مشاهده شد"
        result, _ = apply_context_aware_strategy(text)
        # L۴-L۵ should convert to L4-L5
        assert "L4-L5" in result or ("L4" in result and "L5" in result)


class TestProcessNumeralsMainFunction:
    """Test the main process_numerals function."""
    
    def test_english_strategy(self):
        """Test process_numerals with english strategy."""
        text = "بیمار ۳۵ ساله"
        result = process_numerals(text, strategy="english")
        assert result == "بیمار 35 ساله"
    
    def test_persian_strategy(self):
        """Test process_numerals with persian strategy."""
        text = "بیمار 35 ساله"
        result = process_numerals(text, strategy="persian")
        assert result == "بیمار ۳۵ ساله"
    
    def test_preserve_strategy(self):
        """Test process_numerals with preserve strategy."""
        text = "بیمار ۳۵ ساله with 120 BP"
        result = process_numerals(text, strategy="preserve")
        assert result == text  # Should remain unchanged
    
    def test_context_aware_strategy(self):
        """Test process_numerals with context_aware strategy."""
        text = "بیمار 35 ساله با مشکل در L4-L5"
        result = process_numerals(text, strategy="context_aware")
        # L4-L5 stays English, 35 converts to Persian
        assert "۳۵" in result
        assert "L4-L5" in result
    
    def test_invalid_strategy(self):
        """Test process_numerals with invalid strategy raises error."""
        text = "بیمار 35 ساله"
        with pytest.raises(ValueError, match="Invalid numeral strategy"):
            process_numerals(text, strategy="invalid_strategy")
    
    def test_empty_text(self):
        """Test process_numerals with empty text."""
        result = process_numerals("", strategy="english")
        assert result == ""
    
    def test_none_text(self):
        """Test process_numerals with None text."""
        result = process_numerals(None, strategy="english")
        assert result is None


class TestEdgeCases:
    """Test edge cases and complex scenarios."""
    
    def test_multiple_decimal_points(self):
        """Test numbers with decimal points."""
        text = "قند خون 3.5 و 10.25 و 100.5"
        result = process_numerals(text, strategy="persian")
        assert "۳.۵" in result
        assert "۱۰.۲۵" in result
        assert "۱۰۰.۵" in result
    
    def test_ranges_with_dash(self):
        """Test ranges like L4-L5."""
        text = "L4-L5 و T11-T12"
        result = process_numerals(text, strategy="context_aware")
        # Should preserve medical ranges
        assert "L4-L5" in result or ("L4" in result and "L5" in result)
        assert "T11-T12" in result or ("T11" in result and "T12" in result)
    
    def test_mixed_persian_english_in_same_number(self):
        """Test handling mixed numerals in same number sequence."""
        text = "عدد ۱۲3۴۵"
        result = process_numerals(text, strategy="english")
        assert "12345" in result
    
    def test_measurements_with_decimal(self):
        """Test measurements with decimal values."""
        text = "دوز 3.5mg و طول 10.2cm"
        result = process_numerals(text, strategy="context_aware")
        # Measurements should stay in English
        assert "3.5mg" in result
        assert "10.2cm" in result
    
    def test_blood_pressure_format(self):
        """Test blood pressure format (120/80)."""
        text = "فشار خون 120/80"
        result = process_numerals(text, strategy="persian")
        assert "۱۲۰/۸۰" in result
    
    def test_vertebral_levels_all_types(self):
        """Test all types of vertebral levels."""
        text = "بررسی T1, L5, C7, S2"
        result = process_numerals(text, strategy="context_aware")
        # All should be preserved in English
        assert "T1" in result
        assert "L5" in result
        assert "C7" in result
        assert "S2" in result
    
    def test_long_text_with_multiple_patterns(self):
        """Test longer text with multiple numeral patterns."""
        text = """
        بیمار 45 ساله با شکایت از درد در ناحیه L4-L5.
        فشار خون 120/80 و قند خون 95.
        دوز تجویزی: 10mg روزانه.
        MRI نشان از آسیب در C3-C4 و T11-T12 می‌دهد.
        وزن بیمار 70 کیلوگرم و قد 175 سانتیمتر.
        """
        result = process_numerals(text, strategy="context_aware")
        
        # Medical codes should stay English
        assert "L4-L5" in result
        assert "10mg" in result
        assert "C3-C4" in result
        assert "T11-T12" in result
        
        # Standalone numbers should be Persian
        assert "۴۵" in result  # age
        assert "۱۲۰" in result or "۸۰" in result  # blood pressure
        assert "۹۵" in result  # blood sugar
        assert "۷۰" in result  # weight
        assert "۱۷۵" in result  # height
    
    def test_text_with_no_spaces(self):
        """Test text with numerals without spaces."""
        text = "L4مهره"
        result = process_numerals(text, strategy="context_aware")
        # L4 should be preserved
        assert "L4" in result
    
    def test_case_insensitive_medical_codes(self):
        """Test that medical code detection is case-insensitive."""
        text = "مشکل در l4-l5 و T12"
        medical_terms = detect_medical_terms(text)
        # Should detect both lowercase and uppercase
        assert len(medical_terms) >= 2


class TestRealWorldScenarios:
    """Test real-world medical transcription scenarios."""
    
    def test_radiology_report(self):
        """Test a typical radiology report."""
        text = """
        MRI ستون فقرات کمری:
        بیمار 52 ساله با شکایت از کمردرد.
        مشاهدات: 
        - هرنی دیسک L4-L5 به اندازه 5mm
        - تنگی کانال نخاعی در سطح L5-S1
        - ارتفاع دیسک‌ها در حد طبیعی
        نتیجه: هرنی دیسک درجه 2 در L4-L5
        """
        result = process_numerals(text, strategy="context_aware")
        
        # Medical codes stay English
        assert "L4-L5" in result
        assert "L5-S1" in result
        assert "5mm" in result
        
        # Age converts to Persian
        assert "۵۲" in result
        
        # Grade number converts to Persian (standalone)
        assert "۲" in result
    
    def test_prescription_text(self):
        """Test a prescription text."""
        text = """
        نسخه برای بیمار 35 ساله:
        1. قرص A 10mg - روزی 2 عدد
        2. کپسول B 500mg - روزی 3 عدد
        مدت درمان: 14 روز
        """
        result = process_numerals(text, strategy="context_aware")
        
        # Medications with dosages stay English
        assert "10mg" in result
        assert "500mg" in result
        
        # Other numbers convert to Persian
        assert "۳۵" in result  # age
        assert "۲" in result  # quantity per day
        assert "۳" in result  # quantity per day
        assert "۱۴" in result  # duration
    
    def test_lab_results(self):
        """Test laboratory results."""
        text = """
        نتایج آزمایش بیمار 28 ساله:
        - قند خون ناشتا: 95 mg/dl
        - کلسترول: 180 mg/dl
        - تری‌گلیسرید: 150 mg/dl
        - HbA1c: 5.6%
        """
        result = process_numerals(text, strategy="context_aware")
        
        # Age converts to Persian
        assert "۲۸" in result
        
        # Lab values with units might vary based on implementation
        # but medical codes should be preserved
        assert "HbA1c" in result
