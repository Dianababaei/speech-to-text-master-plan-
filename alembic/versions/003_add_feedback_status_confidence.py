"""Add status and confidence fields to feedback table

Revision ID: 003
Revises: 002
Create Date: 2024-01-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add status and confidence columns to feedback table."""
    
    # Add status column with default 'pending'
    op.add_column(
        'feedback',
        sa.Column(
            'status',
            sa.String(length=50),
            nullable=False,
            server_default='pending',
            comment='Feedback status: pending, approved, rejected, auto-approved'
        )
    )
    
    # Add confidence column (optional field for future use)
    op.add_column(
        'feedback',
        sa.Column(
            'confidence',
            sa.Float(),
            nullable=True,
            comment='Confidence score for the feedback (0.0-1.0)'
        )
    )
    
    # Create index on status for filtering queries
    op.create_index('ix_feedback_status', 'feedback', ['status'])


def downgrade() -> None:
    """Remove status and confidence columns from feedback table."""
    
    # Drop index first
    op.drop_index('ix_feedback_status', table_name='feedback')
    
    # Drop columns
    op.drop_column('feedback', 'confidence')
    op.drop_column('feedback', 'status')
