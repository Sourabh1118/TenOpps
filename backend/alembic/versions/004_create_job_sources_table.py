"""Create job_sources table with indexes and constraints

Revision ID: 004_create_job_sources_table
Revises: 003_create_applications_table
Create Date: 2024-03-18 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_create_job_sources_table'
down_revision = '003_create_applications_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create job_sources table with all fields, constraints, and indexes."""
    
    # Create job_sources table
    op.create_table(
        'job_sources',
        # Primary key
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        
        # Foreign key to jobs
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # Source information
        sa.Column('source_platform', sa.String(length=50), nullable=False),
        sa.Column('source_url', sa.String(length=2048), nullable=False),
        sa.Column('source_job_id', sa.String(length=255), nullable=True),
        
        # Tracking timestamps
        sa.Column('scraped_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        
        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        
        # Foreign key constraint
        sa.ForeignKeyConstraint(
            ['job_id'],
            ['jobs.id'],
            name='fk_job_sources_job_id',
            ondelete='CASCADE'
        ),
    )
    
    # Create indexes for efficient querying
    op.create_index('idx_job_sources_id', 'job_sources', ['id'])
    
    # Index on job_id for source lookups (as specified in task requirements)
    op.create_index('idx_job_sources_job_id', 'job_sources', ['job_id'])
    
    # Composite index for platform-specific queries
    op.create_index(
        'idx_job_sources_platform_active',
        'job_sources',
        ['source_platform', 'is_active']
    )
    
    # Index for freshness tracking
    op.create_index(
        'idx_job_sources_last_verified',
        'job_sources',
        ['last_verified_at']
    )


def downgrade() -> None:
    """Drop job_sources table and related objects."""
    
    # Drop indexes first
    op.drop_index('idx_job_sources_last_verified', table_name='job_sources')
    op.drop_index('idx_job_sources_platform_active', table_name='job_sources')
    op.drop_index('idx_job_sources_job_id', table_name='job_sources')
    op.drop_index('idx_job_sources_id', table_name='job_sources')
    
    # Drop table
    op.drop_table('job_sources')
