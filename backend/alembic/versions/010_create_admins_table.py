"""Create admins table for system administrators

Revision ID: 010_create_admins_table
Revises: 009_add_performance_indexes
Create Date: 2024-03-23 20:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010_create_admins_table'
down_revision = '009_add_performance_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create admins table with authentication and profile fields."""
    
    # Create admins table
    op.create_table(
        'admins',
        # Primary key
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        
        # Authentication
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        
        # Profile information
        sa.Column('full_name', sa.String(length=100), nullable=False),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        
        # Check constraints for validation
        sa.CheckConstraint(
            "email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'",
            name='check_admin_email_format'
        ),
        sa.CheckConstraint(
            "char_length(full_name) >= 2 AND char_length(full_name) <= 100",
            name='check_admin_full_name_length'
        ),
    )
    
    # Create indexes for efficient querying
    op.create_index('idx_admins_id', 'admins', ['id'])
    op.create_index('idx_admins_email', 'admins', ['email'], unique=True)


def downgrade() -> None:
    """Drop admins table and related objects."""
    
    # Drop indexes
    op.drop_index('idx_admins_email', table_name='admins')
    op.drop_index('idx_admins_id', table_name='admins')
    
    # Drop table
    op.drop_table('admins')
