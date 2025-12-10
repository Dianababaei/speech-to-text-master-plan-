"""Add is_admin field to api_keys table

Revision ID: 004
Revises: 003
Create Date: 2024-01-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_admin field for admin-level authentication."""
    
    # Add is_admin column
    op.add_column('api_keys', 
        sa.Column('is_admin', sa.Boolean(), nullable=True, 
                  server_default='false',
                  comment='Whether this key has admin privileges')
    )
    
    # Set default value for existing rows
    op.execute("UPDATE api_keys SET is_admin = false WHERE is_admin IS NULL")
    
    # Make column non-nullable after setting defaults
    op.alter_column('api_keys', 'is_admin', nullable=False)
    
    # Create index for faster admin checks
    op.create_index('ix_api_keys_is_admin', 'api_keys', ['is_admin'])


def downgrade() -> None:
    """Remove is_admin field from api_keys table."""
    
    # Drop index
    op.drop_index('ix_api_keys_is_admin', table_name='api_keys')
    
    # Drop column
    op.drop_column('api_keys', 'is_admin')
