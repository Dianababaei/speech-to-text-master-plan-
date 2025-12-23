# Radiology Lexicon Cleanup Summary

## Changes Made

### Problem Identified
The original lexicon contained **translations** instead of **spelling corrections**:
- ❌ BAD: `("دیستال", "دور")` - This translates "distal" to Persian "door/far"
- ❌ BAD: `("پروگزیمال", "نزدیک")` - This translates "proximal" to Persian "near"
- ❌ BAD: `("لترال", "جانبی")` - This translates "lateral" to Persian

### Corrected Approach
The lexicon should ONLY contain:
1. **Misspelling corrections** (Persian → Correct Persian)
2. **Persian phonetic → English medical term** (where English is standard)
3. **Spacing and formatting fixes**

### Examples of CORRECT Entries

#### Persian Spelling Corrections
```
("گبد", "کبد")           # liver - misspelling
("فلب", "قلب")           # heart - misspelling
("ریحه", "ریه")          # lung - misspelling
("سخامت", "ضخامت")      # thickness - misspelling
```

#### Persian Phonetic → English Medical Terms
```
("سی تی", "CT")
("ام آر آی", "MRI")
("تی وان", "T1")
("فلر", "FLAIR")
("داپلر", "Doppler")
("کنتراست", "contrast")
```

#### Anatomical Position Terms (Keep English)
```
("پروگزیمال", "proximal")   # Standard medical English
("دیستال", "distal")
("مدیال", "medial")
("لترال", "lateral")
("آنتریور", "anterior")
("پوستریور", "posterior")
```

#### Imaging Descriptors (Keep English)
```
("هایپرانتنس", "hyperintense")
("هایپوانتنس", "hypointense")
("هایپراکویک", "hyperechoic")
("هایپواکویک", "hypoechoic")
```

## Current Status

- **Total active terms**: ~188
- **Persian corrections**: ~120 terms
- **English medical terms**: ~68 terms

## Removed Translations

The following translation-style entries were REMOVED:

```python
# ❌ REMOVED - These translate to Persian instead of correcting
("دیستال", "دور"),              # distal → far
("پروگزیمال", "نزدیک"),          # proximal → near
("لترال", "جانبی"),              # lateral → lateral (Persian)
("ونترال", "شکمی"),              # ventral → belly
("دورسال", "پشتی"),              # dorsal → back
("کرانیال", "سری"),              # cranial → head
("کادال", "دمی"),                # caudal → tail
("سوپریور", "بالایی"),          # superior → upper
("اینفریور", "پایینی"),          # inferior → lower
("مدیال", "میانی"),              # medial → middle
("آکسیال", "محوری"),            # axial → axial (Persian)
("ساجیتال", "کناری"),           # sagittal → side

# Medical findings - use English terms
("هرنی", "فتق"),                 # hernia
("اوبستراکسیون", "انسداد"),     # obstruction
("پرفراسیون", "سوراخ شدگی"),   # perforation
("فراکچر", "شکستگی"),           # fracture
("دیسلوکاسیون", "دررفتگی"),     # dislocation
("اسپرین", "رگ به رگ شدگی"),   # sprain

# Medical conditions - use English
("اسپلنومگالی", "بزرگی طحال"),  # splenomegaly
("هپاتومگالی", "بزرگی کبد"),    # hepatomegaly
("کاردیومگالی", "بزرگی قلب"),  # cardiomegaly
("هماتوم", "کبودی"),             # hematoma
("لیپوماتوس", "چربی"),          # lipomatous
("وسکولار", "عروقی"),            # vascular
("نورولوژیک", "عصبی"),          # neurologic

# Anatomical locations
("سوبکوتانه", "زیرجلدی"),                # subcutaneous
("اینتراموسکولار", "داخل عضلانی"),      # intramuscular
("اینتراآرتیکولار", "داخل مفصلی"),      # intra-articular
("پاراورتبرال", "کنار مهره"),           # paravertebral
("پارااورتیک", "کنار آئورت"),           # para-aortic
("مدیاستینال", "مدیاستن"),              # mediastinal
("رتروپریتونال", "پشت صفاقی"),         # retroperitoneal

# Measurement descriptors
("ماکزیمال", "حداکثر"),         # maximal
("مینیمال", "حداقل"),            # minimal

# Imaging descriptors
("کم‌اکو", "hypoechoic"),       # Keep English
("پراکو", "hyperechoic"),       # Keep English
("بی‌اکو", "anechoic"),          # Keep English
("فوق شدید", "hyperintense"),   # Keep English
("کم شدت", "hypointense"),      # Keep English
("هم شدت", "isointense"),        # Keep English

# Flow/window terms
("فلو", "جریان"),                # flow
("ویندو", "پنجره"),              # window
("HU", "واحد هانسفیلد"),         # Hounsfield unit
```

## Recommendations

### 1. Use English Medical Terminology
International medical reports use standardized English terms for:
- Anatomical positions: proximal, distal, medial, lateral, etc.
- Pathology: lesion, mass, nodule, cyst, etc.
- Imaging: hyperintense, hypoechoic, artifact, etc.

### 2. Persian for General Description
Use Persian for:
- Patient information
- General observations
- Connecting phrases
- Non-technical descriptors

### 3. Example of Good Mixed Report
```
بیمار: فاطمه رشیدی ۶۲۲۶۸
Modality: CT abdomen with contrast

یافته‌ها:
- Liver: homogeneous, normal size
- Spleen: mild splenomegaly
- Kidneys: bilateral cortical cysts
- Pancreas: normal
- Lymph nodes: no lymphadenopathy

نتیجه: Mild splenomegaly. Bilateral renal cysts. Otherwise unremarkable.
```

## Updated Whisper Prompt

The example-based prompt already demonstrates good mixed usage:

```persian
بیمار: فاطمه رشیدی ۶۲۲۶۸
یافته‌ها: کاهش فاصله مفصلی در زانوی راست. ضخامت جزئی مخاطی در سینوس اتموئید.
تغییرات دژنراتیو در ستون فقرات کمری. کبد و طحال در اندازه طبیعی.
ریه‌ها عاری از کانسولیدیشن و آتلکتازی.
```

This shows Whisper:
- Patient info format
- Persian sentence structure
- Mix of Persian and medical terminology
- Proper spacing and punctuation

## Files Created

1. **radiology_lexicon_corrected.py** - New lexicon with only corrections (168 terms)
2. **radiology_lexicon_corrected.csv** - CSV export
3. **lexicon_backup.json** - Backup of previous lexicon
4. **LEXICON_CLEANUP_SUMMARY.md** - This document

## Next Steps

### Option 1: Keep Current Mixed Lexicon
- 188 terms total
- Includes some translations
- Works but not ideal

### Option 2: Clean Database and Re-import
```sql
-- Clean all lexicon terms
DELETE FROM lexicon_terms WHERE lexicon_id = 'general';

-- Import only radiology_lexicon_corrected.csv
-- This gives pure corrections without translations
```

### Option 3: Selective Removal
Remove only the translation entries while keeping corrections:
- Delete entries where replacement is multi-word Persian
- Keep entries where replacement is English medical term
- Keep entries where it's simple Persian spelling correction

## Testing

After lexicon update, test with:
```bash
python TRANSCRIBE_AUDIO.bat
```

Check that corrections work properly in transcription output.
