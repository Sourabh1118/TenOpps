"""Add performance optimization indexes

Revision ID: 009_add_performance_indexes
Revises: 008_create_consents_table
Create Date: 2024-03-20 10:00:00.000000

Implements Task 33.1: Database indexing strategy for performance optimization
- B-tree index on jobs.company for deduplication (Requirement 16.2)
- GIN indexes on jobs.title and jobs.description for full-text search (already exist)
- Composite index on (status, quality_score, posted_at) for search ranking (already exists)
- Index on jobs.employer_id for employer dashboard queries (Requirement 16.2)
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add performance optimization indexes."""
    
    # Note: Most indexes already exist from 001_create_jobs_table.py
    # We'll verify and add any missing ones
    
    # Add B-tree index on employer_id if not exists (for employer dashboard queries)
    # This is critical for Requirement 16.2 - employer dashboard performance
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_jobs_employer_id 
        ON jobs (employer_id)
        WHERE employer_id IS NOT NULL
    """)
    
    # Verify existing indexes are optimal
    # The following indexes should already exist from migration 001:
    # - idx_jobs_company (B-tree on company for deduplication)
    # - idx_jobs_title_fts (GIN on title for full-text search)
    # - idx_jobs_description_fts (GIN on description for full-text search)
    # - idx_jobs_search_ranking (composite on status, quality_score, posted_at)
    
    # Add index on location for location-based filtering
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_jobs_location 
        ON jobs (location)
    """)
    
    # Add index on remote flag for remote job filtering
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_jobs_remote 
        ON jobs (remote)
        WHERE remote = true
    """)
    
    # Add index on featured flag for featured job queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_jobs_featured 
        ON jobs (featured)
        WHERE featured = true
    """)
    
    # Add composite index for common search patterns
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_jobs_active_featured_quality 
        ON jobs (status, featured, quality_score DESC, posted_at DESC)
        WHERE status = 'active'
    """)


def downgrade() -> None:
    """Remove performance optimization indexes."""
    
    op.drop_index('idx_jobs_active_featured_quality', table_name='jobs', if_exists=True)
    op.drop_index('idx_jobs_featured', table_name='jobs', if_exists=True)
    op.drop_index('idx_jobs_remote', table_name='jobs', if_exists=True)
    op.drop_index('idx_jobs_location', table_name='jobs', if_exists=True)
    op.drop_index('idx_jobs_employer_id', table_name='jobs', if_exists=True)
