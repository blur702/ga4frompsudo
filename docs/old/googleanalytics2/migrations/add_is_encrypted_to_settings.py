"""
Migration script to add is_encrypted column to the Setting model.
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    """
    Add is_encrypted column to the setting table.
    """
    op.add_column('setting', sa.Column('is_encrypted', sa.Boolean(), nullable=False, server_default='0'))

def downgrade():
    """
    Remove is_encrypted column from the setting table.
    """
    op.drop_column('setting', 'is_encrypted')