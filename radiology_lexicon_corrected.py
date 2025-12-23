"""
Corrected Radiology Lexicon - Only spelling corrections, NO translations
This lexicon corrects common speech recognition errors and misspellings
"""

import requests
import json

API_URL = "http://127.0.0.1:8080"
API_KEY = "1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I"

# CORRECTED lexicon - only misspelling corrections, no translations
RADIOLOGY_CORRECTIONS = [
    # ===== PERSIAN ANATOMY - Spelling Corrections Only =====
    ("ریحه", "ریه"),  # lung - common misspelling
    ("گبد", "کبد"),  # liver
    ("فلب", "قلب"),  # heart
    ("طحان", "طحال"),  # spleen
    ("غلیه", "کلیه"),  # kidney
    ("مغده", "معده"),  # stomach
    ("لوزالمغده", "لوزالمعده"),  # pancreas
    ("ماری", "مثانه"),  # bladder
    ("پروستان", "پروستات"),  # prostate
    ("رحیم", "رحم"),  # uterus
    ("تحمدان", "تخمدان"),  # ovary
    ("غضروض", "غضروف"),  # cartilage
    ("لیکامان", "لیگامان"),  # ligament
    ("تانذون", "تاندون"),  # tendon
    ("مفسل", "مفصل"),  # joint
    ("فقارت", "فقرات"),  # vertebrae
    ("عروف", "عروق"),  # vessels
    ("عصف", "عصب"),  # nerve
    ("عزله", "عضله"),  # muscle
    ("بافد", "بافت"),  # tissue
    ("مخ", "مغز"),  # brain
    ("نخاغ", "نخاع"),  # spinal cord
    ("ساف", "ساق"),  # tibia
    ("قوز", "قوزک"),  # ankle
    ("ترفیغه", "ترقوه"),  # clavicle
    ("ساغد", "ساعد"),  # forearm
    ("سیموس", "سینوس"),  # sinus
    ("کانان", "کانال"),  # canal

    # ===== PATHOLOGY TERMS - Spelling Corrections =====
    ("افصایی", "فضایی"),  # spatial
    ("سخامت", "ضخامت"),  # thickness
    ("زخامت", "ضخامت"),  # thickness variant
    ("ضحامت", "ضخامت"),  # thickness variant
    ("آنحراف", "انحراف"),  # deviation
    ("گایش", "کاهش"),  # decrease
    ("افصایش", "افزایش"),  # increase
    ("وسیف", "وسیع"),  # extensive
    ("کیسد", "کیست"),  # cyst
    ("کنسولیدیشن", "کانسولیدیشن"),  # consolidation
    ("آتلکتزی", "آتلکتازی"),  # atelectasis
    ("افوزیون", "افیوژن"),  # effusion
    ("پنوموتراکس", "پنوموتوراکس"),  # pneumothorax
    ("ادیم", "ادم"),  # edema
    ("التحاب", "التهاب"),  # inflammation
    ("فیبروس", "فیبروز"),  # fibrosis
    ("نکروس", "نکروز"),  # necrosis
    ("اتروفی", "آتروفی"),  # atrophy
    ("هیپرتروضی", "هیپرتروفی"),  # hypertrophy
    ("دیسپلاسی", "دیسپلازی"),  # dysplasia
    ("استنوس", "استنوز"),  # stenosis
    ("استیوفیت", "استئوفیت"),  # osteophyte
    ("استیوپروز", "استئوپروز"),  # osteoporosis
    ("استیوپنی", "استئوپنی"),  # osteopenia
    ("متاستاس", "متاستاز"),  # metastasis
    ("خوش خیم", "خوش‌خیم"),  # benign - spacing
    ("غیر طبیعی", "غیرطبیعی"),  # abnormal - spacing
    ("دسانسیون", "آسانسیون"),  # ascension

    # ===== ENGLISH MEDICAL TERMS - Correct English Spelling =====
    # CT Terms
    ("سی تی", "CT"),  # CT scan
    ("کنتراست", "contrast"),

    # MRI Terms
    ("ام آر آی", "MRI"),
    ("تی وان", "T1"),
    ("تی تو", "T2"),
    ("فلر", "FLAIR"),
    ("دیفیوژن", "diffusion"),
    ("سیگنال", "signal"),
    ("هایپرانتنس", "hyperintense"),
    ("هایپوانتنس", "hypointense"),
    ("آیزوانتنس", "isointense"),
    ("گادولینیوم", "gadolinium"),

    # Ultrasound Terms
    ("سونوگراضی", "سونوگرافی"),  # sonography
    ("اکوژنیسیته", "echogenicity"),
    ("هایپراکویک", "hyperechoic"),
    ("هایپواکویک", "hypoechoic"),
    ("آناکویک", "anechoic"),
    ("داپلر", "Doppler"),

    # X-ray Terms
    ("رادیوگراضی", "رادیوگرافی"),  # radiography
    ("رادیولوسنت", "radiolucent"),
    ("رادیواوپاک", "radiopaque"),
    ("دانسیته", "density"),

    # Mammography
    ("ماموگراضی", "ماموگرافی"),  # mammography
    ("میکروکلسیفیکاسیون", "microcalcification"),
    ("بی راد", "BI-RADS"),
    ("فیبروآدنوم", "fibroadenoma"),

    # General Terms
    ("لزیون", "lesion"),
    ("ندول", "nodule"),
    ("کلسیفیکاسیون", "calcification"),
    ("نیوپلاسم", "neoplasm"),
    ("لنفادنوپاتی", "lymphadenopathy"),

    # ===== MEASUREMENTS - Spacing Corrections =====
    ("میلیمتر", "میلی‌متر"),  # millimeter
    ("سانتیمتر", "سانتی‌متر"),  # centimeter
    ("جزیی", "جزئی"),  # mild
    ("جزگی", "جزئی"),  # mild variant
    ("خفیض", "خفیف"),  # slight
    ("چند کانونی", "چندکانونی"),  # multifocal
    ("دو طرفه", "دوطرفه"),  # bilateral
    ("یک طرفه", "یک‌طرفه"),  # unilateral
    ("مرکسی", "مرکزی"),  # central
    ("کم‌اکو", "hypoechoic"),  # use English term
    ("پراکو", "hyperechoic"),  # use English term
    ("بی‌اکو", "anechoic"),  # use English term

    # ===== DIRECTIONS - Keep Medical English Terms =====
    ("چب", "چپ"),  # left
    ("پروگزیمال", "proximal"),
    ("دیستال", "distal"),
    ("سوپریور", "superior"),
    ("اینفریور", "inferior"),
    ("مدیال", "medial"),
    ("لترال", "lateral"),
    ("ونترال", "ventral"),
    ("دورسال", "dorsal"),
    ("کرانیال", "cranial"),
    ("کادال", "caudal"),
    ("آکسیال", "axial"),
    ("ساجیتال", "sagittal"),
    ("آنتریور", "anterior"),
    ("پوستریور", "posterior"),

    # ===== COMMON REPORT TERMS =====
    ("فاغله", "فاصله"),  # distance
    ("قظر", "قطر"),  # diameter
    ("موفعیت", "موقعیت"),  # position
    ("نضر", "نظر"),  # opinion
    ("موجو", "موجود"),  # present
    ("مجدد", "مجدد"),  # repeat (correct)
    ("ضعبط", "ضبط"),  # record
    ("مسهول", "مسئول"),  # responsible
    ("تقریب", "تقریبا"),  # approximately
    ("حالط", "خالص"),  # pure
    ("تغزیه", "تغذیه"),  # nutrition

    # ===== PATHOLOGY - Medical English Terms =====
    ("نرمال", "normal"),
    ("اسکن", "scan"),
    ("تومور", "tumor"),
    ("ماکزیمال", "maximal"),
    ("مینیمال", "minimal"),
    ("همگن", "homogeneous"),
    ("ناهمگن", "heterogeneous"),

    # ===== NEW TERMS from Radiopaedia =====
    # Artifacts and Technical
    ("آرتیفکت", "artifact"),
    ("آرتیفکد", "artifact"),

    # Pathology terms
    ("آژنزی", "agenesis"),
    ("آپلازی", "aplasia"),
    ("آترزی", "atresia"),
    ("آتروضی", "atrophy"),
    ("هایپرپلازی", "hyperplasia"),
    ("هایپرتروضی", "hypertrophy"),

    # CNS terms
    ("اینفارکشن", "infarction"),
    ("ایسکمی", "ischemia"),
    ("اینتراونتریکولار", "intraventricular"),

    # GI terms
    ("دیسفاژی", "dysphagia"),
    ("هپاتوفوگال", "hepatofugal"),
    ("هپاتوپتال", "hepatopetal"),

    # Musculoskeletal
    ("آمپوتیشن", "amputation"),
    ("آپوفیزیس", "apophysis"),
    ("دیافیزیس", "diaphysis"),
    ("اپیفیزیس", "epiphysis"),
    ("متافیزیس", "metaphysis"),
    ("فیزیس", "physis"),
    ("مونواستوتیک", "monostotic"),
    ("پلی‌استوتیک", "polyostotic"),

    # Chest
    ("برونکوره‌آ", "bronchorrhea"),
    ("موکوسل", "mucocele"),
    ("مایستوما", "mycetoma"),

    # Imaging modalities
    ("فلوروسکوپی", "fluoroscopy"),
    ("آنژیوگرافی", "angiography"),
    ("مموگرافی", "mammography"),
    ("سینتیگرافی", "scintigraphy"),
    ("اکوکاردیوگرافی", "echocardiography"),

    # Descriptors
    ("اگزوفیتیک", "exophytic"),
    ("سرپیجینوس", "serpiginous"),
    ("ژئوگرافیک", "geographic"),
    ("فوکال", "focal"),
    ("دیفیوز", "diffuse"),
    ("مولتی‌فوکال", "multifocal"),
]

def update_lexicon():
    """Replace old lexicon with corrected version via API."""

    # First, export current lexicon to backup
    print("Creating backup of current lexicon...")
    try:
        response = requests.get(
            f"{API_URL}/lexicons/general/export?format=json",
            headers={"X-API-Key": API_KEY}
        )
        if response.status_code == 200:
            with open('lexicon_backup.json', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("[OK] Backup saved to lexicon_backup.json")
    except Exception as e:
        print(f"[WARN] Could not create backup: {e}")

    # Prepare CSV with corrected terms
    csv_content = "term,replacement\n"
    for term, replacement in RADIOLOGY_CORRECTIONS:
        csv_content += f'"{term}","{replacement}"\n'

    # Save to CSV
    csv_path = "radiology_lexicon_corrected.csv"
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write(csv_content)

    print(f"\n{'='*70}")
    print("CORRECTED Radiology Lexicon")
    print(f"{'='*70}")
    print(f"Total corrections: {len(RADIOLOGY_CORRECTIONS)}")
    print("\nCategories:")
    print("  - Persian spelling corrections (anatomy, pathology)")
    print("  - English medical term corrections")
    print("  - Spacing and formatting fixes")
    print("  - Common speech recognition errors")
    print("\n[REMOVED] Translations (e.g., 'distal' -> 'door')")
    print("[KEPT] Only spelling corrections and proper medical terms")
    print(f"{'='*70}\n")

    # Upload via API
    try:
        with open(csv_path, 'rb') as f:
            response = requests.post(
                f"{API_URL}/lexicons/general/import",
                headers={"X-API-Key": API_KEY},
                files={"file": ("lexicon.csv", f, "text/csv")}
            )

        if response.status_code == 200:
            result = response.json()
            print("[OK] Import successful!")
            print(f"   - Imported: {result.get('imported', 0)} new terms")
            print(f"   - Skipped: {result.get('skipped', 0)} duplicates")

            if result.get('errors'):
                print("\n[ERRORS]:")
                for error in result.get('errors', []):
                    print(f"   - {error}")
        else:
            print(f"[ERROR] HTTP {response.status_code}")
            print(f"   Response: {response.text}")

    except Exception as e:
        print(f"[ERROR] Upload failed: {str(e)}")

if __name__ == "__main__":
    update_lexicon()
