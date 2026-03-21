"""
Script to verify database indexes using EXPLAIN ANALYZE.

This script tests common query patterns to ensure indexes are being used effectively.
Implements Task 33.1 verification requirement.
"""
import asyncio
from sqlalchemy import text
from app.db.session import SessionLocal
from app.core.logging import get_logger

logger = get_logger(__name__)


async def verify_indexes():
    """Verify that indexes are being used for common queries."""
    
    db = SessionLocal()
    
    try:
        logger.info("Verifying database indexes with EXPLAIN ANALYZE...")
        
        # Test 1: Company lookup for deduplication (should use idx_jobs_company)
        logger.info("\n=== Test 1: Company lookup for deduplication ===")
        result = db.execute(text("""
            EXPLAIN ANALYZE
            SELECT id, title, company, location, description
            FROM jobs
            WHERE company = 'Google Inc'
            LIMIT 10
        """))
        for row in result:
            logger.info(row[0])
        
        # Test 2: Full-text search on title (should use idx_jobs_title_fts)
        logger.info("\n=== Test 2: Full-text search on title ===")
        result = db.execute(text("""
            EXPLAIN ANALYZE
            SELECT id, title, company, quality_score
            FROM jobs
            WHERE to_tsvector('english', title) @@ plainto_tsquery('english', 'software engineer')
            LIMIT 20
        """))
        for row in result:
            logger.info(row[0])
        
        # Test 3: Full-text search on description (should use idx_jobs_description_fts)
        logger.info("\n=== Test 3: Full-text search on description ===")
        result = db.execute(text("""
            EXPLAIN ANALYZE
            SELECT id, title, company, quality_score
            FROM jobs
            WHERE to_tsvector('english', description) @@ plainto_tsquery('english', 'python django')
            LIMIT 20
        """))
        for row in result:
            logger.info(row[0])
        
        # Test 4: Search ranking query (should use idx_jobs_search_ranking or idx_jobs_active_featured_quality)
        logger.info("\n=== Test 4: Search ranking query ===")
        result = db.execute(text("""
            EXPLAIN ANALYZE
            SELECT id, title, company, quality_score, posted_at, featured
            FROM jobs
            WHERE status = 'active'
            ORDER BY featured DESC, quality_score DESC, posted_at DESC
            LIMIT 20
        """))
        for row in result:
            logger.info(row[0])
        
        # Test 5: Employer dashboard query (should use idx_jobs_employer_id)
        logger.info("\n=== Test 5: Employer dashboard query ===")
        result = db.execute(text("""
            EXPLAIN ANALYZE
            SELECT id, title, status, application_count, view_count, posted_at
            FROM jobs
            WHERE employer_id = '00000000-0000-0000-0000-000000000001'::uuid
            ORDER BY posted_at DESC
        """))
        for row in result:
            logger.info(row[0])
        
        # Test 6: Location-based filtering (should use idx_jobs_location)
        logger.info("\n=== Test 6: Location-based filtering ===")
        result = db.execute(text("""
            EXPLAIN ANALYZE
            SELECT id, title, company, location
            FROM jobs
            WHERE location = 'San Francisco, CA' AND status = 'active'
            LIMIT 20
        """))
        for row in result:
            logger.info(row[0])
        
        # Test 7: Remote job filtering (should use idx_jobs_remote)
        logger.info("\n=== Test 7: Remote job filtering ===")
        result = db.execute(text("""
            EXPLAIN ANALYZE
            SELECT id, title, company, remote
            FROM jobs
            WHERE remote = true AND status = 'active'
            LIMIT 20
        """))
        for row in result:
            logger.info(row[0])
        
        # Test 8: Featured jobs query (should use idx_jobs_featured)
        logger.info("\n=== Test 8: Featured jobs query ===")
        result = db.execute(text("""
            EXPLAIN ANALYZE
            SELECT id, title, company, featured, quality_score
            FROM jobs
            WHERE featured = true AND status = 'active'
            ORDER BY quality_score DESC, posted_at DESC
            LIMIT 10
        """))
        for row in result:
            logger.info(row[0])
        
        # Summary: List all indexes on jobs table
        logger.info("\n=== Current indexes on jobs table ===")
        result = db.execute(text("""
            SELECT
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename = 'jobs'
            ORDER BY indexname
        """))
        for row in result:
            logger.info(f"{row[0]}: {row[1]}")
        
        logger.info("\n✓ Index verification complete!")
        
    except Exception as e:
        logger.error(f"Error verifying indexes: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(verify_indexes())
