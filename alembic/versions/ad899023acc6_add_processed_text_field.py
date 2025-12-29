"""add_processed_text_field

Revision ID: ad899023acc6
Revises: 351493e4ddc6
Create Date: 2025-12-23 20:44:42.521580

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ad899023acc6'
down_revision: Union[str, None] = '351493e4ddc6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add processed_text field to jobs table
    op.add_column('jobs', sa.Column('processed_text', sa.Text(), nullable=True, comment='Post-processed transcription output'))


def downgrade() -> None:
    # Remove processed_text field
    op.drop_column('jobs', 'processed_text')
