"""Create scraping_tasks table with indexes and constraints

Revision ID: 005_create_scraping_tasks_table
Revises: 004_create_job_sources_table
Create Date: 2024-03-18 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_create_scraping_tasks_table'
down_revision = '004_create_job_sources_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create scraping_tasks table with all fields, constraints, and indexes."""
    
    # Create task_type enum
    task_type_enum = postgresql.ENUM(
        'scheduled_scrape',
        'manual_scrape',
        'url_import',
        name='tasktype',
        create_type=True
    )
    
    # Create task_status enum
    task_status_enum = postgresql.ENUM(
        'pending',
        'running',
        'completed',
        'failed',
        name='taskstatus',
        create_type=True
    )
    
    # Create scraping_tasks table
    op.create_table(
        'scraping_tasks',
        # Primary key
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        
        # Task identification
        sa.Column('task_type', task_type_enum, nullable=False),
        sa.Column('source_platform', sa.String(length=50), nullable=True),
        sa.Column('target_url', sa.Text(), nullable=True),
        
        # Status tracking
        sa.Column('status', task_status_enum, nullable=False, server_default='pending'),
        
        # Execution timing
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        
        # Metrics
        sa.Column('jobs_found', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('jobs_created', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('jobs_updated', sa.Integer(), nullable=False, server_default='0'),
        
        # Error handling
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        
        # Check constraints for validation
        sa.CheckConstraint(
            'retry_count >= 0 AND retry_count <= 3',
            name='check_retry_count_bounds'
        ),
        sa.CheckConstraint(
            'jobs_found >= jobs_created + jobs_updated',
            name='check_jobs_found_consistency'
        ),
        sa.CheckConstraint(
            'jobs_found >= 0 AND jobs_created >= 0 AND jobs_updated >= 0',
            name='check_jobs_metrics_positive'
        ),
        sa.CheckConstraint(
            'started_at IS NULL OR completed_at IS NULL OR completed_at >= started_at',
            name='check_completion_after_start'
        ),
    )
    
    # Create indexes for efficient querying
    op.create_index('idx_scraping_tasks_id', 'scraping_tasks', ['id'])
    op.create_index('idx_scraping_tasks_status', 'scraping_tasks', ['status'])
    op.create_index('idx_scraping_tasks_created_at', 'scraping_tasks', ['created_at'])
    
    # Composite index for monitoring queries (status, created_at) - as specified in task requirements
    op.create_index(
        'idx_scraping_tasks_status_created',
        'scraping_tasks',
        ['status', 'created_at']
    )
    
    # Index for platform-specific queries
    op.create_index('idx_scraping_tasks_platform', 'scraping_tasks', ['source_platform'])
    
    # Index for task type queries
    op.create_index('idx_scraping_tasks_type', 'scraping_tasks', ['task_type'])


def downgrade() -> None:
    """Drop scraping_tasks table and related objects."""
    
    # Drop indexes first
    op.drop_index('idx_scraping_tasks_type', table_name='scraping_tasks')
    op.drop_index('idx_scraping_tasks_platform', table_name='scraping_tasks')
    op.drop_index('idx_scraping_tasks_status_created', table_name='scraping_tasks')
    op.drop_index('idx_scraping_tasks_created_at', table_name='scraping_tasks')
    op.drop_index('idx_scraping_tasks_status', table_name='scraping_tasks')
    op.drop_index('idx_scraping_tasks_id', table_name='scraping_tasks')
    
    # Drop table
    op.drop_table('scraping_tasks')
    
    # Drop enums
    task_status_enum = postgresql.ENUM(name='taskstatus')
    task_status_enum.drop(op.get_bind())
    
    task_type_enum = postgresql.ENUM(name='tasktype')
    task_type_enum.drop(op.get_bind())
