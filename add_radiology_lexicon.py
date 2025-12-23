"""
Add comprehensive radiology lexicon terms to the database.
Covers: DX/X-ray, CT, MRI, Ultrasound, Mammography
"""

import requests
import json

API_URL = "http://127.0.0.1:8080"
API_KEY = "1CBAJxlf5-b_s6-d9a5lwQ2zSUtamVFI5RHHCm8Bp4I"

# Comprehensive radiology lexicon organized by category
RADIOLOGY_TERMS = [
    # ===== ANATOMY - General (50 terms) =====
    ("ریحه", "ریه"),  # lung
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
    ("مهره", "مهره"),  # vertebra
    ("فقارت", "فقرات"),  # vertebrae
    ("استخوان", "استخوان"),  # bone (correct spelling reference)
    ("عروف", "عروق"),  # vessels
    ("شریان", "شریان"),  # artery
    ("ورید", "ورید"),  # vein
    ("غدد", "غدد"),  # glands
    ("لنفاوی", "لنفاوی"),  # lymphatic
    ("عصف", "عصب"),  # nerve
    ("عزله", "عضله"),  # muscle
    ("پوست", "پوست"),  # skin
    ("بافد", "بافت"),  # tissue
    ("مخ", "مغز"),  # brain
    ("نخاغ", "نخاع"),  # spinal cord
    ("جمجمه", "جمجمه"),  # skull
    ("دنده", "دنده"),  # rib
    ("جناق", "جناق"),  # sternum
    ("لگن", "لگن"),  # pelvis
    ("ران", "ران"),  # femur
    ("زانو", "زانو"),  # knee
    ("ساف", "ساق"),  # tibia
    ("فیبولا", "فیبولا"),  # fibula
    ("قوز", "قوزک"),  # ankle
    ("کتف", "کتف"),  # scapula
    ("ترفیغه", "ترقوه"),  # clavicle
    ("بازو", "بازو"),  # arm
    ("آرنج", "آرنج"),  # elbow
    ("ساغد", "ساعد"),  # forearm
    ("مچ", "مچ"),  # wrist
    ("پاتلا", "پاتلا"),  # patella
    ("فک", "فک"),  # jaw
    ("سیموس", "سینوس"),  # sinus
    ("حفره", "حفره"),  # cavity
    ("کانان", "کانال"),  # canal

    # ===== PATHOLOGY & FINDINGS (60 terms) =====
    ("افصایی", "فضایی"),  # spatial
    ("سخامت", "ضخامت"),  # thickness
    ("آنحراف", "انحراف"),  # deviation
    ("شواد", "قدرت"),  # power (in context)
    ("گایش", "کاهش"),  # decrease
    ("افصایش", "افزایش"),  # increase
    ("وسیف", "وسیع"),  # wide/extensive
    ("لزیون", "ضایعه"),  # lesion
    ("توده", "توده"),  # mass
    ("ندول", "ندول"),  # nodule
    ("کیسد", "کیست"),  # cyst
    ("کلسیفیکاسیون", "کلسیفیکاسیون"),  # calcification
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
    ("هرنی", "فتق"),  # hernia
    ("دیسپلاسی", "دیسپلازی"),  # dysplasia
    ("استنوس", "استنوز"),  # stenosis
    ("دیلاتاسیون", "دیلاتاسیون"),  # dilatation
    ("آنوریسم", "آنوریسم"),  # aneurysm
    ("اوبستراکسیون", "انسداد"),  # obstruction
    ("پرفراسیون", "سوراخ شدگی"),  # perforation
    ("فراکچر", "شکستگی"),  # fracture
    ("دیسلوکاسیون", "دررفتگی"),  # dislocation
    ("اسپرین", "رگ به رگ شدگی"),  # sprain
    ("استیوفیت", "استئوفیت"),  # osteophyte
    ("استئوآرتریت", "استئوآرتریت"),  # osteoarthritis
    ("استیوپروز", "استئوپروز"),  # osteoporosis
    ("استیوپنی", "استئوپنی"),  # osteopenia
    ("لنفادنوپاتی", "لنفادنوپاتی"),  # lymphadenopathy
    ("اسپلنومگالی", "بزرگی طحال"),  # splenomegaly
    ("هپاتومگالی", "بزرگی کبد"),  # hepatomegaly
    ("کاردیومگالی", "بزرگی قلب"),  # cardiomegaly
    ("هماتوم", "کبودی"),  # hematoma
    ("آبسه", "آبسه"),  # abscess
    ("تومور", "تومور"),  # tumor
    ("نیوپلاسم", "نئوپلاسم"),  # neoplasm
    ("متاستاس", "متاستاز"),  # metastasis
    ("بدخیم", "بدخیم"),  # malignant
    ("خوش خیم", "خوش‌خیم"),  # benign
    ("دسانسیون", "آسانسیون"),  # ascension
    ("پلورال", "پلورال"),  # pleural
    ("پریکاردیال", "پریکاردیال"),  # pericardial
    ("سوبکوتانه", "زیرجلدی"),  # subcutaneous
    ("اینتراموسکولار", "داخل عضلانی"),  # intramuscular
    ("اینتراآرتیکولار", "داخل مفصلی"),  # intra-articular
    ("پاراورتبرال", "کنار مهره"),  # paravertebral
    ("پارااورتیک", "کنار آئورت"),  # para-aortic
    ("مدیاستینال", "مدیاستن"),  # mediastinal
    ("رتروپریتونال", "پشت صفاقی"),  # retroperitoneal
    ("لیپوماتوس", "چربی"),  # lipomatous
    ("وسکولار", "عروقی"),  # vascular
    ("نورولوژیک", "عصبی"),  # neurologic

    # ===== MODALITY-SPECIFIC TERMS (40 terms) =====
    # CT
    ("سی تی", "سی‌تی"),  # CT
    ("اسکن", "اسکن"),  # scan
    ("کنتراست", "کنتراست"),  # contrast
    ("نان کنتراست", "بدون کنتراست"),  # non-contrast
    ("ویندو", "پنجره"),  # window
    ("HU", "واحد هانسفیلد"),  # Hounsfield unit

    # MRI
    ("ام آر آی", "ام‌آر‌آی"),  # MRI
    ("تی وان", "T1"),  # T1
    ("تی تو", "T2"),  # T2
    ("فلر", "FLAIR"),  # FLAIR
    ("دیفیوژن", "دیفیوژن"),  # diffusion
    ("سیگنال", "سیگنال"),  # signal
    ("هایپرانتنس", "فوق شدید"),  # hyperintense
    ("هایپوانتنس", "کم شدت"),  # hypointense
    ("آیزوانتنس", "هم شدت"),  # isointense
    ("گادولینیوم", "گادولینیوم"),  # gadolinium

    # Ultrasound
    ("سونوگراضی", "سونوگرافی"),  # sonography
    ("اکو", "اکو"),  # echo
    ("اکوژنیسیته", "اکوژنیسیته"),  # echogenicity
    ("هایپراکویک", "پراکو"),  # hyperechoic
    ("هایپواکویک", "کم‌اکو"),  # hypoechoic
    ("آناکویک", "بی‌اکو"),  # anechoic
    ("داپلر", "داپلر"),  # Doppler
    ("فلو", "جریان"),  # flow

    # X-ray
    ("رادیوگراضی", "رادیوگرافی"),  # radiography
    ("رادیولوسنت", "رادیولوسنت"),  # radiolucent
    ("رادیواوپاک", "رادیواوپک"),  # radiopaque
    ("دانسیته", "دانسیته"),  # density

    # Mammography
    ("ماموگراضی", "ماموگرافی"),  # mammography
    ("میکروکلسیفیکاسیون", "میکروکلسیفیکاسیون"),  # microcalcification
    ("بی راد", "BI-RADS"),  # BI-RADS
    ("فیبروآدنوم", "فیبروآدنوم"),  # fibroadenoma

    # ===== MEASUREMENTS & DESCRIPTORS (30 terms) =====
    ("میلیمتر", "میلی‌متر"),  # millimeter
    ("سانتیمتر", "سانتی‌متر"),  # centimeter
    ("اندازه", "اندازه"),  # size
    ("ابعاد", "ابعاد"),  # dimensions
    ("قطر", "قطر"),  # diameter
    ("طول", "طول"),  # length
    ("عرض", "عرض"),  # width
    ("ارتفاع", "ارتفاع"),  # height
    ("حجم", "حجم"),  # volume
    ("فاصله", "فاصله"),  # distance
    ("جزیی", "جزئی"),  # mild/minor
    ("خفیض", "خفیف"),  # slight
    ("متوسط", "متوسط"),  # moderate
    ("شدید", "شدید"),  # severe
    ("ماکزیمال", "حداکثر"),  # maximal
    ("مینیمال", "حداقل"),  # minimal
    ("نرمال", "نرمال"),  # normal
    ("طبیعی", "طبیعی"),  # normal
    ("غیر طبیعی", "غیرطبیعی"),  # abnormal
    ("متقارن", "متقارن"),  # symmetric
    ("نامتقارن", "نامتقارن"),  # asymmetric
    ("همگن", "هموژن"),  # homogeneous
    ("ناهمگن", "ناهموژن"),  # heterogeneous
    ("منتشر", "منتشر"),  # diffuse
    ("موضعی", "موضعی"),  # focal
    ("چند کانونی", "چندکانونی"),  # multifocal
    ("دو طرفه", "دوطرفه"),  # bilateral
    ("یک طرفه", "یک‌طرفه"),  # unilateral
    ("مرکسی", "مرکزی"),  # central
    ("محیطی", "محیطی"),  # peripheral

    # ===== POSITIONS & DIRECTIONS (20 terms) =====
    ("راست", "راست"),  # right
    ("چب", "چپ"),  # left
    ("فوقانی", "فوقانی"),  # superior
    ("تحتانی", "تحتانی"),  # inferior
    ("قدامی", "قدامی"),  # anterior
    ("خلفی", "خلفی"),  # posterior
    ("داخلی", "داخلی"),  # medial
    ("خارجی", "خارجی"),  # lateral
    ("پروگزیمال", "نزدیک"),  # proximal
    ("دیستال", "دور"),  # distal
    ("سوپریور", "بالایی"),  # superior
    ("اینفریور", "پایینی"),  # inferior
    ("مدیال", "میانی"),  # medial
    ("لترال", "جانبی"),  # lateral
    ("ونترال", "شکمی"),  # ventral
    ("دورسال", "پشتی"),  # dorsal
    ("کرانیال", "سری"),  # cranial
    ("کادال", "دمی"),  # caudal
    ("آکسیال", "محوری"),  # axial
    ("ساجیتال", "کناری"),  # sagittal
]

def add_terms_to_lexicon():
    """Add all radiology terms to the general lexicon via API."""

    # Prepare the data for CSV import
    csv_content = "term,replacement\n"
    for term, replacement in RADIOLOGY_TERMS:
        csv_content += f'"{term}","{replacement}"\n'

    # Save to temporary CSV file
    csv_path = "radiology_lexicon.csv"
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write(csv_content)

    print(f"Created CSV with {len(RADIOLOGY_TERMS)} terms")

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
            print(f"✅ Success!")
            print(f"   - Imported: {result.get('imported_count', 0)} terms")
            print(f"   - Skipped: {result.get('skipped_count', 0)} terms (duplicates)")
            print(f"   - Total active terms: {result.get('total_terms', 0)}")

            if result.get('skipped_terms'):
                print(f"\nSkipped terms (first 5):")
                for skipped in result.get('skipped_terms', [])[:5]:
                    print(f"   - {skipped.get('term')}: {skipped.get('reason')}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")

    except Exception as e:
        print(f"❌ Error uploading: {str(e)}")

if __name__ == "__main__":
    print("=" * 60)
    print("Adding Comprehensive Radiology Lexicon")
    print("=" * 60)
    print(f"\nCategories:")
    print(f"  - Anatomy (General): 50 terms")
    print(f"  - Pathology & Findings: 60 terms")
    print(f"  - Modality-Specific: 40 terms")
    print(f"  - Measurements & Descriptors: 30 terms")
    print(f"  - Positions & Directions: 20 terms")
    print(f"\nTotal: {len(RADIOLOGY_TERMS)} new terms")
    print(f"\nModalities covered:")
    print(f"  - DX / X-ray")
    print(f"  - CT")
    print(f"  - MRI")
    print(f"  - Ultrasound")
    print(f"  - Mammography")
    print("=" * 60)
    print()

    add_terms_to_lexicon()
