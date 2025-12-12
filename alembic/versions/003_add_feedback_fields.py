"""Add status, lexicon_id, confidence, frequency, and created_by fields to feedback table

Revision ID: 003
Revises: 002
Create Date: 2024-01-03 00:00:00.000000

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
    """Add fields for admin review workflow and filtering."""
    
    # Add status column for admin review workflow
    op.add_column('feedback', 
        sa.Column('status', sa.String(length=50), nullable=True, 
                  server_default='pending',
                  comment='Status: pending, approved, rejected')
    )
    
    # Add lexicon_id for filtering
    op.add_column('feedback',
        sa.Column('lexicon_id', sa.String(length=100), nullable=True,
                  comment='Lexicon used for this transcription')
    )
    
    # Add confidence score
    op.add_column('feedback',
        sa.Column('confidence', sa.Float(), nullable=True,
                  comment='Confidence score for the correction')
    )
    
    # Add frequency counter
    op.add_column('feedback',
        sa.Column('frequency', sa.Integer(), nullable=True,
                  server_default='1',
                  comment='Number of times this correction was submitted')
    )
    
    # Add created_by field (in addition to reviewer)
    op.add_column('feedback',
        sa.Column('created_by', sa.String(length=100), nullable=True,
                  comment='User who submitted the feedback')
    )
    
    # Set default status for existing rows
    op.execute("UPDATE feedback SET status = 'pending' WHERE status IS NULL")
    
    # Set default frequency for existing rows
    op.execute("UPDATE feedback SET frequency = 1 WHERE frequency IS NULL")
    
    # Make status and frequency non-nullable after setting defaults
    op.alter_column('feedback', 'status', nullable=False)
    op.alter_column('feedback', 'frequency', nullable=False)
    
    # Create indexes for filtering
    op.create_index('ix_feedback_status', 'feedback', ['status'])
    op.create_index('ix_feedback_lexicon_id', 'feedback', ['lexicon_id'])
    op.create_index('ix_feedback_created_by', 'feedback', ['created_by'])


def downgrade() -> None:
    """Remove added fields from feedback table."""
    
    # Drop indexes
    op.drop_index('ix_feedback_created_by', table_name='feedback')
    op.drop_index('ix_feedback_lexicon_id', table_name='feedback')
    op.drop_index('ix_feedback_status', table_name='feedback')
    
    # Drop columns
    op.drop_column('feedback', 'created_by')
    op.drop_column('feedback', 'frequency')
    op.drop_column('feedback', 'confidence')
    op.drop_column('feedback', 'lexicon_id')
    op.drop_column('feedback', 'status')
