"""Create jobs table with indexes and constraints

Revision ID: 001_create_jobs_table
Revises: 
Create Date: 2024-03-18 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_create_jobs_table'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create jobs table with all fields, constraints, and indexes."""
    
    # Create enum types
    job_type_enum = postgresql.ENUM(
        'full_time', 'part_time', 'contract', 'freelance', 
        'internship', 'fellowship', 'academic',
        name='jobtype',
        create_type=True
    )
    
    experience_level_enum = postgresql.ENUM(
        'entry', 'mid', 'senior', 'lead', 'executive',
        name='experiencelevel',
        create_type=True
    )
    
    source_type_enum = postgresql.ENUM(
        'direct', 'url_import', 'aggregated',
        name='sourcetype',
        create_type=True
    )
    
    job_status_enum = postgresql.ENUM(
        'active', 'expired', 'filled', 'deleted',
        name='jobstatus',
        create_type=True
    )
    
    # Create jobs table
    op.create_table(
        'jobs',
        # Primary key
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        
        # Core job information
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('company', sa.String(length=100), nullable=False),
        sa.Column('location', sa.String(length=200), nullable=False),
        sa.Column('remote', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('job_type', job_type_enum, nullable=False),
        sa.Column('experience_level', experience_level_enum, nullable=False),
        
        # Detailed information
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('requirements', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('responsibilities', postgresql.ARRAY(sa.Text()), nullable=True),
        
        # Salary information
        sa.Column('salary_min', sa.Integer(), nullable=True),
        sa.Column('salary_max', sa.Integer(), nullable=True),
        sa.Column('salary_currency', sa.String(length=3), nullable=True, server_default='USD'),
        
        # Source information
        sa.Column('source_type', source_type_enum, nullable=False),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('source_platform', sa.String(length=50), nullable=True),
        sa.Column('employer_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Quality and status
        sa.Column('quality_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('status', job_status_enum, nullable=False, server_default='active'),
        
        # Dates
        sa.Column('posted_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        
        # Engagement metrics
        sa.Column('application_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('featured', sa.Boolean(), nullable=False, server_default='false'),
        
        # Tags
        sa.Column('tags', postgresql.ARRAY(sa.String(length=50)), nullable=True),
        
        # Check constraints for validation
        sa.CheckConstraint(
            "char_length(title) >= 10 AND char_length(title) <= 200",
            name='check_title_length'
        ),
        sa.CheckConstraint(
            "char_length(company) >= 2 AND char_length(company) <= 100",
            name='check_company_length'
        ),
        sa.CheckConstraint(
            "char_length(description) >= 50 AND char_length(description) <= 5000",
            name='check_description_length'
        ),
        sa.CheckConstraint(
            "salary_min IS NULL OR salary_max IS NULL OR salary_min < salary_max",
            name='check_salary_range'
        ),
        sa.CheckConstraint(
            "quality_score >= 0 AND quality_score <= 100",
            name='check_quality_score_bounds'
        ),
        sa.CheckConstraint(
            "application_count >= 0",
            name='check_application_count_positive'
        ),
        sa.CheckConstraint(
            "view_count >= 0",
            name='check_view_count_positive'
        ),
        sa.CheckConstraint(
            "expires_at > posted_at",
            name='check_expiration_after_posted'
        ),
        sa.CheckConstraint(
            "expires_at <= posted_at + INTERVAL '90 days'",
            name='check_expiration_within_90_days'
        ),
    )
    
    # Create indexes for efficient querying
    op.create_index('idx_jobs_id', 'jobs', ['id'])
    op.create_index('idx_jobs_title', 'jobs', ['title'])
    op.create_index('idx_jobs_company', 'jobs', ['company'])
    op.create_index('idx_jobs_status', 'jobs', ['status'])
    op.create_index('idx_jobs_quality_score', 'jobs', ['quality_score'])
    op.create_index('idx_jobs_posted_at', 'jobs', ['posted_at'])
    op.create_index('idx_jobs_source_type', 'jobs', ['source_type'])
    
    # Composite indexes for common query patterns
    op.create_index(
        'idx_jobs_search_ranking',
        'jobs',
        ['status', 'quality_score', 'posted_at']
    )
    op.create_index(
        'idx_jobs_employer_status',
        'jobs',
        ['employer_id', 'status']
    )
    
    # GIN indexes for full-text search
    # Note: These use PostgreSQL-specific syntax
    op.execute(
        """
        CREATE INDEX idx_jobs_title_fts ON jobs 
        USING gin(to_tsvector('english', title))
        """
    )
    op.execute(
        """
        CREATE INDEX idx_jobs_description_fts ON jobs 
        USING gin(to_tsvector('english', description))
        """
    )


def downgrade() -> None:
    """Drop jobs table and related objects."""
    
    # Drop indexes first
    op.drop_index('idx_jobs_description_fts', table_name='jobs')
    op.drop_index('idx_jobs_title_fts', table_name='jobs')
    op.drop_index('idx_jobs_employer_status', table_name='jobs')
    op.drop_index('idx_jobs_search_ranking', table_name='jobs')
    op.drop_index('idx_jobs_source_type', table_name='jobs')
    op.drop_index('idx_jobs_posted_at', table_name='jobs')
    op.drop_index('idx_jobs_quality_score', table_name='jobs')
    op.drop_index('idx_jobs_status', table_name='jobs')
    op.drop_index('idx_jobs_company', table_name='jobs')
    op.drop_index('idx_jobs_title', table_name='jobs')
    op.drop_index('idx_jobs_id', table_name='jobs')
    
    # Drop table
    op.drop_table('jobs')
    
    # Drop enum types
    sa.Enum(name='jobstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='sourcetype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='experiencelevel').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='jobtype').drop(op.get_bind(), checkfirst=True)
