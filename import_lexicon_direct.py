"""
Direct database import of radiology lexicon terms.
Bypasses API to avoid auth issues.
"""

import csv
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from app.database import SessionLocal
from app.models.lexicon import LexiconTerm

def import_terms():
    """Import lexicon terms directly to database."""

    csv_path = r"c:\Users\digi kaj\Desktop\speech-to-text\speech-to-text-master-plan-\radiology_lexicon.csv"

    # Read CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        terms = list(reader)

    print(f"Read {len(terms)} terms from CSV")

    # Connect to database
    db = SessionLocal()

    try:
        # Get existing terms for deduplication
        existing = db.query(LexiconTerm).filter(
            LexiconTerm.lexicon_id == 'general',
            LexiconTerm.is_active == True
        ).all()

        existing_terms = {t.term.lower() for t in existing}
        print(f"Found {len(existing_terms)} existing terms in database")

        # Add new terms
        added = 0
        skipped = 0
        current_time = datetime.utcnow()

        for row in terms:
            term = row['term']
            replacement = row['replacement']

            if term.lower() in existing_terms:
                skipped += 1
                continue

            new_term = LexiconTerm(
                lexicon_id='general',
                term=term,
                replacement=replacement,
                is_active=True,
                created_at=current_time,
                updated_at=current_time
            )

            db.add(new_term)
            added += 1

        # Commit transaction
        db.commit()

        print(f"\n✓ Success!")
        print(f"  - Added: {added} new terms")
        print(f"  - Skipped: {skipped} duplicates")
        print(f"  - Total active terms: {len(existing_terms) + added}")

    except Exception as e:
        db.rollback()
        print(f"\n✗ Error: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Direct Database Import - Radiology Lexicon")
    print("=" * 60)
    print()
    import_terms()
