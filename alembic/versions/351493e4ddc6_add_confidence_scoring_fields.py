"""add_confidence_scoring_fields

Revision ID: 351493e4ddc6
Revises: 004
Create Date: 2025-12-23 17:34:22.477227

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '351493e4ddc6'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add confidence scoring fields to jobs table
    op.add_column('jobs', sa.Column('confidence_score', sa.Float(), nullable=True, comment='Overall confidence score (0.0-1.0)'))
    op.add_column('jobs', sa.Column('correction_count', sa.Integer(), nullable=True, comment='Number of corrections applied'))
    op.add_column('jobs', sa.Column('fuzzy_match_count', sa.Integer(), nullable=True, comment='Number of fuzzy matches used'))
    op.add_column('jobs', sa.Column('confidence_metrics', sa.JSON(), nullable=True, comment='Detailed confidence breakdown'))


def downgrade() -> None:
    # Remove confidence scoring fields
    op.drop_column('jobs', 'confidence_metrics')
    op.drop_column('jobs', 'fuzzy_match_count')
    op.drop_column('jobs', 'correction_count')
    op.drop_column('jobs', 'confidence_score')
