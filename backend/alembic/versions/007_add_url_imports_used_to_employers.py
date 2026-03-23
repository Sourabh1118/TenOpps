"""add url_imports_used to employers

Revision ID: 007
Revises: 006
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    """Add url_imports_used column to employers table."""
    # Add url_imports_used column with default value 0
    op.add_column(
        'employers',
        sa.Column('url_imports_used', sa.Integer(), nullable=False, server_default='0')
    )
    
    # Add check constraint for url_imports_used non-negative
    op.create_check_constraint(
        'check_url_imports_positive',
        'employers',
        'url_imports_used >= 0'
    )


def downgrade():
    """Remove url_imports_used column from employers table."""
    # Drop check constraint
    op.drop_constraint('check_url_imports_positive', 'employers', type_='check')
    
    # Drop column
    op.drop_column('employers', 'url_imports_used')
