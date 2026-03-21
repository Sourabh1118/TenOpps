"""
Manual test script for search service.

This script tests the search service with a real PostgreSQL database.
Run this after setting up the database and running migrations.

Usage:
    python test_search_manual.py
"""
import sys
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.job import Job, JobType, ExperienceLevel, SourceType, JobStatus
from app.schemas.search import SearchFilters
from app.services.search import SearchService


def create_test_jobs(db: Session):
    """Create test jobs in the database."""
    print("Creating test jobs...")
    
    jobs = [
        Job(
            title="Senior Software Engineer",
            company="TechCorp",
            location="San Francisco",
            remote=True,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.SENIOR,
            description="We are looking for a senior software engineer with Python experience",
            source_type=SourceType.DIRECT,
            quality_score=85.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30)
        ),
        Job(
            title="Junior Python Developer",
            company="StartupXYZ",
            location="New York",
            remote=False,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.ENTRY,
            description="Entry level position for Python developer with Django knowledge",
            source_type=SourceType.AGGREGATED,
            quality_score=45.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.utcnow() - timedelta(days=5),
            expires_at=datetime.utcnow() + timedelta(days=25),
            salary_min=60000,
            salary_max=80000
        ),
        Job(
            title="Data Scientist",
            company="DataCo",
            location="San Francisco",
            remote=True,
            job_type=JobType.CONTRACT,
            experience_level=ExperienceLevel.MID,
            description="Looking for data scientist with machine learning expertise",
            source_type=SourceType.URL_IMPORT,
            quality_score=65.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.utcnow() - timedelta(days=2),
            expires_at=datetime.utcnow() + timedelta(days=28),
            salary_min=100000,
            salary_max=150000
        ),
    ]
    
    for job in jobs:
        db.add(job)
    db.commit()
    
    print(f"✓ Created {len(jobs)} test jobs")
    return jobs


def test_search_no_filters(search_service: SearchService):
    """Test search with no filters."""
    print("\n1. Testing search with no filters...")
    filters = SearchFilters()
    result = search_service.search_jobs(filters, page=1, page_size=20)
    
    print(f"   Found {result['total']} jobs")
    assert result['total'] >= 3, "Should find at least 3 active jobs"
    print("   ✓ PASSED")


def test_full_text_search(search_service: SearchService):
    """Test full-text search."""
    print("\n2. Testing full-text search on 'Python'...")
    filters = SearchFilters(query="Python")
    result = search_service.search_jobs(filters, page=1, page_size=20)
    
    print(f"   Found {result['total']} jobs")
    assert result['total'] >= 1, "Should find at least 1 job with 'Python'"
    print("   ✓ PASSED")


def test_location_filter(search_service: SearchService):
    """Test location filter."""
    print("\n3. Testing location filter for 'San Francisco'...")
    filters = SearchFilters(location="San Francisco")
    result = search_service.search_jobs(filters, page=1, page_size=20)
    
    print(f"   Found {result['total']} jobs")
    assert result['total'] >= 2, "Should find at least 2 jobs in San Francisco"
    for job in result['jobs']:
        assert job.location == "San Francisco"
    print("   ✓ PASSED")


def test_remote_filter(search_service: SearchService):
    """Test remote filter."""
    print("\n4. Testing remote filter...")
    filters = SearchFilters(remote=True)
    result = search_service.search_jobs(filters, page=1, page_size=20)
    
    print(f"   Found {result['total']} remote jobs")
    assert result['total'] >= 2, "Should find at least 2 remote jobs"
    for job in result['jobs']:
        assert job.remote is True
    print("   ✓ PASSED")


def test_job_type_filter(search_service: SearchService):
    """Test job type filter."""
    print("\n5. Testing job type filter for FULL_TIME...")
    filters = SearchFilters(jobType=[JobType.FULL_TIME])
    result = search_service.search_jobs(filters, page=1, page_size=20)
    
    print(f"   Found {result['total']} full-time jobs")
    assert result['total'] >= 2, "Should find at least 2 full-time jobs"
    for job in result['jobs']:
        assert job.job_type == JobType.FULL_TIME
    print("   ✓ PASSED")


def test_salary_filter(search_service: SearchService):
    """Test salary filter."""
    print("\n6. Testing salary filter (min: 90000)...")
    filters = SearchFilters(salaryMin=90000)
    result = search_service.search_jobs(filters, page=1, page_size=20)
    
    print(f"   Found {result['total']} jobs with salary >= 90000")
    assert result['total'] >= 1, "Should find at least 1 job with salary >= 90000"
    print("   ✓ PASSED")


def test_combined_filters(search_service: SearchService):
    """Test combined filters."""
    print("\n7. Testing combined filters (San Francisco + remote)...")
    filters = SearchFilters(location="San Francisco", remote=True)
    result = search_service.search_jobs(filters, page=1, page_size=20)
    
    print(f"   Found {result['total']} jobs")
    assert result['total'] >= 1, "Should find at least 1 remote job in San Francisco"
    for job in result['jobs']:
        assert job.location == "San Francisco"
        assert job.remote is True
    print("   ✓ PASSED")


def test_pagination(search_service: SearchService):
    """Test pagination."""
    print("\n8. Testing pagination...")
    filters = SearchFilters()
    result = search_service.search_jobs(filters, page=1, page_size=2)
    
    print(f"   Page 1: {len(result['jobs'])} jobs (total: {result['total']})")
    assert len(result['jobs']) <= 2, "Should return at most 2 jobs per page"
    assert result['page'] == 1
    assert result['page_size'] == 2
    print("   ✓ PASSED")


def cleanup_test_jobs(db: Session):
    """Clean up test jobs."""
    print("\nCleaning up test jobs...")
    # Delete test jobs created by this script
    db.query(Job).filter(Job.company.in_(["TechCorp", "StartupXYZ", "DataCo"])).delete()
    db.commit()
    print("✓ Cleanup complete")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Search Service Manual Tests")
    print("=" * 60)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create test data
        create_test_jobs(db)
        
        # Create search service
        search_service = SearchService(db)
        
        # Run tests
        test_search_no_filters(search_service)
        test_full_text_search(search_service)
        test_location_filter(search_service)
        test_remote_filter(search_service)
        test_job_type_filter(search_service)
        test_salary_filter(search_service)
        test_combined_filters(search_service)
        test_pagination(search_service)
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Cleanup
        cleanup_test_jobs(db)
        db.close()


if __name__ == "__main__":
    main()
