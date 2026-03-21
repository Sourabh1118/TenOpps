"""Create job_seekers table with indexes and constraints

Revision ID: 006_create_job_seekers_table
Revises: 005_create_scraping_tasks_table
Create Date: 2024-03-18 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_create_job_seekers_table'
down_revision = '005_create_scraping_tasks_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create job_seekers table with all fields, constraints, and indexes."""
    
    # Create job_seekers table
    op.create_table(
        'job_seekers',
        # Primary key
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        
        # Authentication
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        
        # Profile information
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('resume_url', sa.String(length=500), nullable=True),
        sa.Column('profile_summary', sa.Text(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        
        # Check constraints for validation
        sa.CheckConstraint(
            "email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'",
            name='check_job_seeker_email_format'
        ),
        sa.CheckConstraint(
            "char_length(full_name) >= 2 AND char_length(full_name) <= 100",
            name='check_full_name_length'
        ),
        sa.CheckConstraint(
            "phone IS NULL OR phone ~* '^[+]?[0-9\\s\\-\\(\\)]{7,20}$'",
            name='check_phone_format'
        ),
        sa.CheckConstraint(
            "resume_url IS NULL OR resume_url ~* '^https?://.+'",
            name='check_resume_url_format'
        ),
    )
    
    # Create indexes for efficient querying
    op.create_index('idx_job_seekers_id', 'job_seekers', ['id'])
    op.create_index('idx_job_seekers_email', 'job_seekers', ['email'], unique=True)


def downgrade() -> None:
    """Drop job_seekers table and related objects."""
    
    # Drop indexes first
    op.drop_index('idx_job_seekers_email', table_name='job_seekers')
    op.drop_index('idx_job_seekers_id', table_name='job_seekers')
    
    # Drop table
    op.drop_table('job_seekers')
