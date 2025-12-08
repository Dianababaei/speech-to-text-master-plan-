"""Add lexicon_id and replacement fields to lexicon_terms

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add lexicon_id and replacement fields to lexicon_terms table."""
    
    # Add lexicon_id column
    op.add_column('lexicon_terms', 
        sa.Column('lexicon_id', sa.String(length=100), nullable=True, 
                  comment='Identifier for the lexicon (e.g., radiology, cardiology)')
    )
    
    # Add replacement column
    op.add_column('lexicon_terms',
        sa.Column('replacement', sa.String(length=255), nullable=True,
                  comment='The corrected/replacement term')
    )
    
    # Set default lexicon_id for existing rows
    op.execute("UPDATE lexicon_terms SET lexicon_id = 'general' WHERE lexicon_id IS NULL")
    
    # Set default replacement for existing rows (use term itself)
    op.execute("UPDATE lexicon_terms SET replacement = term WHERE replacement IS NULL")
    
    # Make columns non-nullable after setting defaults
    op.alter_column('lexicon_terms', 'lexicon_id', nullable=False)
    op.alter_column('lexicon_terms', 'replacement', nullable=False)
    
    # Drop old unique constraint on term
    op.drop_constraint('uq_lexicon_terms_term', 'lexicon_terms', type_='unique')
    
    # Create new unique constraint on (lexicon_id, normalized_term)
    op.create_unique_constraint(
        'uq_lexicon_terms_lexicon_normalized', 
        'lexicon_terms', 
        ['lexicon_id', 'normalized_term']
    )
    
    # Create index on lexicon_id for faster queries
    op.create_index('ix_lexicon_terms_lexicon_id', 'lexicon_terms', ['lexicon_id'])


def downgrade() -> None:
    """Remove lexicon_id and replacement fields from lexicon_terms table."""
    
    # Drop index
    op.drop_index('ix_lexicon_terms_lexicon_id', table_name='lexicon_terms')
    
    # Drop new unique constraint
    op.drop_constraint('uq_lexicon_terms_lexicon_normalized', 'lexicon_terms', type_='unique')
    
    # Recreate old unique constraint on term
    op.create_unique_constraint('uq_lexicon_terms_term', 'lexicon_terms', ['term'])
    
    # Drop columns
    op.drop_column('lexicon_terms', 'replacement')
    op.drop_column('lexicon_terms', 'lexicon_id')
