"""Create applications table with indexes and constraints

Revision ID: 003_create_applications_table
Revises: 002_create_employers_table
Create Date: 2024-03-18 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_create_applications_table'
down_revision = '002_create_employers_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create applications table with all fields, constraints, and indexes."""
    
    # Create enum type for application status
    application_status_enum = postgresql.ENUM(
        'submitted', 'reviewed', 'shortlisted', 'rejected', 'accepted',
        name='applicationstatus',
        create_type=True
    )
    
    # Create applications table
    op.create_table(
        'applications',
        # Primary key
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        
        # Foreign keys
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_seeker_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # Application materials
        sa.Column('resume', sa.String(length=500), nullable=False),
        sa.Column('cover_letter', sa.Text(), nullable=True),
        
        # Status tracking
        sa.Column('status', application_status_enum, nullable=False, server_default='submitted'),
        
        # Employer notes
        sa.Column('employer_notes', sa.Text(), nullable=True),
        
        # Timestamps
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        
        # Foreign key constraint
        sa.ForeignKeyConstraint(
            ['job_id'],
            ['jobs.id'],
            name='fk_applications_job_id',
            ondelete='CASCADE'
        ),
    )
    
    # Create indexes for efficient querying
    op.create_index('idx_applications_id', 'applications', ['id'])
    op.create_index('idx_applications_job_id', 'applications', ['job_id'])
    op.create_index('idx_applications_job_seeker_id', 'applications', ['job_seeker_id'])
    op.create_index('idx_applications_status', 'applications', ['status'])
    
    # Composite index for employer queries (job_id, status)
    op.create_index(
        'idx_applications_job_status',
        'applications',
        ['job_id', 'status']
    )
    
    # Index for job seeker queries
    op.create_index(
        'idx_applications_job_seeker',
        'applications',
        ['job_seeker_id']
    )


def downgrade() -> None:
    """Drop applications table and related objects."""
    
    # Drop indexes first
    op.drop_index('idx_applications_job_seeker', table_name='applications')
    op.drop_index('idx_applications_job_status', table_name='applications')
    op.drop_index('idx_applications_status', table_name='applications')
    op.drop_index('idx_applications_job_seeker_id', table_name='applications')
    op.drop_index('idx_applications_job_id', table_name='applications')
    op.drop_index('idx_applications_id', table_name='applications')
    
    # Drop table
    op.drop_table('applications')
    
    # Drop enum type
    sa.Enum(name='applicationstatus').drop(op.get_bind(), checkfirst=True)
