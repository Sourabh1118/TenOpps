"""
Unit tests for search service.

Tests the full-text search functionality using PostgreSQL's tsvector and tsquery,
as well as all filter combinations, ranking, pagination, and caching.

**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 6.11, 6.12, 6.13, 6.14, 11.5, 16.1, 16.3**

Note: These tests require PostgreSQL. Set TEST_DATABASE_URL environment variable
to run these tests. Example:
    export TEST_DATABASE_URL="postgresql://user:pass@localhost/test_db"
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.job import Job, JobType, ExperienceLevel, SourceType, JobStatus
from app.schemas.search import SearchFilters
from app.services.search import SearchService
from app.core.redis import cache


pytestmark = pytest.mark.integration


@pytest.fixture
def search_service(pg_db_session: Session):
    """Create search service instance."""
    return SearchService(pg_db_session)


@pytest.fixture
def sample_jobs(pg_db_session: Session):
    """Create sample jobs for testing."""
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
            expires_at=datetime.utcnow() + timedelta(days=30),
            featured=False
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
            salary_max=80000,
            featured=False
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
            salary_max=150000,
            featured=False
        ),
        Job(
            title="Frontend Developer",
            company="WebAgency",
            location="Austin",
            remote=False,
            job_type=JobType.PART_TIME,
            experience_level=ExperienceLevel.MID,
            description="Part-time frontend developer needed for React projects",
            source_type=SourceType.DIRECT,
            quality_score=75.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.utcnow() - timedelta(days=10),
            expires_at=datetime.utcnow() + timedelta(days=20),
            featured=False
        ),
        Job(
            title="DevOps Engineer",
            company="CloudTech",
            location="Seattle",
            remote=True,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.SENIOR,
            description="Senior DevOps engineer for cloud infrastructure management",
            source_type=SourceType.DIRECT,
            quality_score=90.0,
            status=JobStatus.EXPIRED,  # Expired job - should not appear in results
            posted_at=datetime.utcnow() - timedelta(days=60),
            expires_at=datetime.utcnow() - timedelta(days=1),
            featured=False
        ),
        Job(
            title="Featured Full Stack Developer",
            company="PremiumCorp",
            location="San Francisco",
            remote=True,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.SENIOR,
            description="Featured position for full stack developer with React and Node.js",
            source_type=SourceType.DIRECT,
            quality_score=80.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.utcnow() - timedelta(days=1),
            expires_at=datetime.utcnow() + timedelta(days=29),
            featured=True  # Featured job - should appear at top
        )
    ]
    
    for job in jobs:
        pg_db_session.add(job)
    pg_db_session.commit()
    
    # Clear cache before tests
    cache.clear_pattern("search:*")
    
    return jobs


class TestSearchService:
    """Test cases for SearchService."""

    def test_search_no_filters_returns_all_active_jobs(self, search_service, sample_jobs, pg_db_session):
        """Test that search with no filters returns all active jobs."""
        filters = SearchFilters()
        result = search_service.search_jobs(filters, page=1, page_size=20)
        
        # Should return 5 active jobs (excluding expired one)
        assert result["total"] == 5
        assert len(result["jobs"]) == 5
        assert result["page"] == 1
        assert result["total_pages"] == 1

    def test_full_text_search_on_title(self, search_service, sample_jobs, pg_db_session):
        """Test full-text search matches job titles."""
        filters = SearchFilters(query="Python")
        result = search_service.search_jobs(filters, page=1, page_size=20)
        
        # Should find "Junior Python Developer"
        assert result["total"] == 1
        assert "Python" in result["jobs"][0].title

    def test_full_text_search_on_description(self, search_service, sample_jobs, pg_db_session):
        """Test full-text search matches job descriptions."""
        filters = SearchFilters(query="machine learning")
        result = search_service.search_jobs(filters, page=1, page_size=20)
        
        # Should find "Data Scientist" job
        assert result["total"] == 1
        assert "machine learning" in result["jobs"][0].description.lower()

    def test_full_text_search_title_or_description(self, search_service, sample_jobs, pg_db_session):
        """Test full-text search matches either title or description."""
        filters = SearchFilters(query="engineer")
        result = search_service.search_jobs(filters, page=1, page_size=20)
        
        # Should find "Senior Software Engineer" and "DevOps Engineer" (but DevOps is expired)
        # So only 1 active job
        assert result["total"] >= 1
        assert any("Engineer" in job.title for job in result["jobs"])

    def test_location_filter_exact_match(self, search_service, sample_jobs, pg_db_session):
        """Test location filter returns exact matches only."""
        filters = SearchFilters(location="San Francisco")
        result = search_service.search_jobs(filters, page=1, page_size=20)
        
        # Should find 3 jobs in San Francisco (including featured)
        assert result["total"] == 3
        assert all(job.location == "San Francisco" for job in result["jobs"])

    def test_job_type_filter(self, search_service, sample_jobs, pg_db_session):
        """Test job type filter."""
        filters = SearchFilters(jobType=[JobType.FULL_TIME])
        result = search_service.search_jobs(filters, page=1, page_size=20)
        
        # Should find 3 active full-time jobs (including featured)
        assert result["total"] == 3
        assert all(job.job_type == JobType.FULL_TIME for job in result["jobs"])

    def test_experience_level_filter(self, search_service, sample_jobs, pg_db_session):
        """Test experience level filter."""
        filters = SearchFilters(experienceLevel=[ExperienceLevel.SENIOR])
        result = search_service.search_jobs(filters, page=1, page_size=20)
        
        # Should find 2 active senior jobs (including featured, DevOps is expired)
        assert result["total"] == 2
        assert all(job.experience_level == ExperienceLevel.SENIOR for job in result["jobs"])

    def test_remote_filter(self, search_service, sample_jobs, pg_db_session):
        """Test remote filter."""
        filters = SearchFilters(remote=True)
        result = search_service.search_jobs(filters, page=1, page_size=20)
        
        # Should find 3 active remote jobs (including featured)
        assert result["total"] == 3
        assert all(job.remote is True for job in result["jobs"])

    def test_salary_min_filter(self, search_service, sample_jobs, pg_db_session):
        """Test minimum salary filter."""
        filters = SearchFilters(salaryMin=90000)
        result = search_service.search_jobs(filters, page=1, page_size=20)
        
        # Should find jobs with salary_max >= 90000 or no salary info
        assert result["total"] >= 1
        for job in result["jobs"]:
            if job.salary_max is not None:
                assert job.salary_max >= 90000

    def test_salary_max_filter(self, search_service, sample_jobs, pg_db_session):
        """Test maximum salary filter."""
        filters = SearchFilters(salaryMax=100000)
        result = search_service.search_jobs(filters, page=1, page_size=20)
        
        # Should find jobs with salary_min <= 100000 or no salary info
        assert result["total"] >= 1
        for job in result["jobs"]:
            if job.salary_min is not None:
                assert job.salary_min <= 100000

    def test_posted_within_filter(self, search_service, sample_jobs, pg_db_session):
        """Test posted within filter."""
        filters = SearchFilters(postedWithin=7)
        result = search_service.search_jobs(filters, page=1, page_size=20)
        
        # Should find jobs posted within last 7 days
        cutoff = datetime.utcnow() - timedelta(days=7)
        assert result["total"] >= 1
        assert all(job.posted_at >= cutoff for job in result["jobs"])

    def test_source_type_filter(self, search_service, sample_jobs, pg_db_session):
        """Test source type filter."""
        filters = SearchFilters(sourceType=[SourceType.DIRECT])
        result = search_service.search_jobs(filters, page=1, page_size=20)
        
        # Should find 3 active direct posts (including featured)
        assert result["total"] == 3
        assert all(job.source_type == SourceType.DIRECT for job in result["jobs"])

    def test_multiple_filters_combined(self, search_service, sample_jobs, pg_db_session):
        """Test that multiple filters are combined with AND logic."""
        filters = SearchFilters(
            location="San Francisco",
            remote=True,
            jobType=[JobType.FULL_TIME, JobType.CONTRACT]
        )
        result = search_service.search_jobs(filters, page=1, page_size=20)
        
        # Should find jobs matching ALL criteria
        assert result["total"] >= 1
        for job in result["jobs"]:
            assert job.location == "San Francisco"
            assert job.remote is True
            assert job.job_type in [JobType.FULL_TIME, JobType.CONTRACT]

    def test_results_sorted_by_quality_and_date(self, search_service, sample_jobs, pg_db_session):
        """
        Test that results are sorted by featured first, then quality score desc, then posted date desc.
        
        **Validates: Requirements 6.11, 11.5**
        """
        filters = SearchFilters()
        result = search_service.search_jobs(filters, page=1, page_size=20)
        
        jobs = result["jobs"]
        
        # First job should be featured
        assert jobs[0].featured is True
        
        # Check sorting: featured first, then quality score desc, then posted_at desc
        for i in range(len(jobs) - 1):
            # Featured jobs should come before non-featured
            if jobs[i].featured and not jobs[i + 1].featured:
                continue
            elif not jobs[i].featured and jobs[i + 1].featured:
                assert False, "Non-featured job before featured job"
            # Within same featured status, check quality score
            elif jobs[i].quality_score == jobs[i + 1].quality_score:
                # If quality scores equal, check posted_at is descending
                assert jobs[i].posted_at >= jobs[i + 1].posted_at
            else:
                assert jobs[i].quality_score >= jobs[i + 1].quality_score

    def test_pagination_first_page(self, search_service, sample_jobs, pg_db_session):
        """
        Test pagination returns correct first page.
        
        **Validates: Requirements 6.12, 6.13, 16.3**
        """
        filters = SearchFilters()
        result = search_service.search_jobs(filters, page=1, page_size=2)
        
        assert result["page"] == 1
        assert result["page_size"] == 2
        assert len(result["jobs"]) == 2
        assert result["total"] == 5
        assert result["total_pages"] == 3

    def test_pagination_second_page(self, search_service, sample_jobs, pg_db_session):
        """Test pagination returns correct second page."""
        filters = SearchFilters()
        result = search_service.search_jobs(filters, page=2, page_size=2)
        
        assert result["page"] == 2
        assert len(result["jobs"]) == 2
        assert result["total"] == 5

    def test_pagination_last_page_partial(self, search_service, sample_jobs, pg_db_session):
        """Test pagination handles partial last page."""
        filters = SearchFilters()
        result = search_service.search_jobs(filters, page=2, page_size=3)
        
        assert result["page"] == 2
        assert len(result["jobs"]) == 2  # Only 2 jobs on last page (5 total, 3 per page)
        assert result["total"] == 5

    def test_pagination_invalid_page_raises_error(self, search_service, sample_jobs, pg_db_session):
        """Test that invalid page number raises error."""
        filters = SearchFilters()
        
        with pytest.raises(ValueError, match="Page must be >= 1"):
            search_service.search_jobs(filters, page=0, page_size=20)

    def test_pagination_invalid_page_size_raises_error(self, search_service, sample_jobs, pg_db_session):
        """Test that invalid page size raises error."""
        filters = SearchFilters()
        
        with pytest.raises(ValueError, match="Page size must be between 1 and 100"):
            search_service.search_jobs(filters, page=1, page_size=0)
        
        with pytest.raises(ValueError, match="Page size must be between 1 and 100"):
            search_service.search_jobs(filters, page=1, page_size=101)

    def test_no_results_returns_empty_list(self, search_service, sample_jobs, pg_db_session):
        """Test that search with no matches returns empty results."""
        filters = SearchFilters(query="nonexistent technology xyz")
        result = search_service.search_jobs(filters, page=1, page_size=20)
        
        assert result["total"] == 0
        assert len(result["jobs"]) == 0
        assert result["total_pages"] == 0

    def test_expired_jobs_excluded_from_results(self, search_service, sample_jobs, pg_db_session):
        """Test that expired jobs are not included in search results."""
        filters = SearchFilters(query="DevOps")
        result = search_service.search_jobs(filters, page=1, page_size=20)
        
        # DevOps job is expired, should not appear
        assert result["total"] == 0

    def test_featured_jobs_appear_first(self, search_service, sample_jobs, pg_db_session):
        """
        Test that featured jobs appear at the top of search results.
        
        **Validates: Requirements 11.5**
        """
        filters = SearchFilters(location="San Francisco")
        result = search_service.search_jobs(filters, page=1, page_size=20)
        
        # First job should be the featured one
        assert result["jobs"][0].featured is True
        assert result["jobs"][0].title == "Featured Full Stack Developer"
        
        # Other jobs should not be featured
        for job in result["jobs"][1:]:
            assert job.featured is False

    def test_search_results_cached(self, search_service, sample_jobs, pg_db_session):
        """
        Test that search results are cached in Redis.
        
        **Validates: Requirements 6.14, 16.1**
        """
        filters = SearchFilters(query="Python")
        
        # Clear cache first
        cache.clear_pattern("search:*")
        
        # First search - should hit database
        result1 = search_service.search_jobs(filters, page=1, page_size=20)
        
        # Generate cache key
        cache_key = search_service._generate_cache_key(filters, 1, 20)
        
        # Check that result is cached
        cached_data = cache.get(cache_key)
        assert cached_data is not None
        assert "job_ids" in cached_data
        assert cached_data["total"] == result1["total"]
        
        # Second search - should hit cache
        result2 = search_service.search_jobs(filters, page=1, page_size=20)
        
        # Results should be identical
        assert result2["total"] == result1["total"]
        assert len(result2["jobs"]) == len(result1["jobs"])

    def test_cache_key_generation_consistent(self, search_service, sample_jobs, pg_db_session):
        """
        Test that cache key generation is consistent for same filters.
        
        **Validates: Requirements 6.14**
        """
        filters1 = SearchFilters(query="Python", location="San Francisco", remote=True)
        filters2 = SearchFilters(query="Python", location="San Francisco", remote=True)
        
        key1 = search_service._generate_cache_key(filters1, 1, 20)
        key2 = search_service._generate_cache_key(filters2, 1, 20)
        
        # Same filters should generate same key
        assert key1 == key2

    def test_cache_key_different_for_different_filters(self, search_service, sample_jobs, pg_db_session):
        """
        Test that different filters generate different cache keys.
        
        **Validates: Requirements 6.14**
        """
        filters1 = SearchFilters(query="Python")
        filters2 = SearchFilters(query="Java")
        
        key1 = search_service._generate_cache_key(filters1, 1, 20)
        key2 = search_service._generate_cache_key(filters2, 1, 20)
        
        # Different filters should generate different keys
        assert key1 != key2

    def test_cache_ttl_is_5_minutes(self, search_service, sample_jobs, pg_db_session):
        """
        Test that cached results have 5-minute TTL.
        
        **Validates: Requirements 6.14, 16.1**
        """
        filters = SearchFilters(query="engineer")
        
        # Clear cache first
        cache.clear_pattern("search:*")
        
        # Execute search to populate cache
        search_service.search_jobs(filters, page=1, page_size=20)
        
        # Get cache key and check TTL
        cache_key = search_service._generate_cache_key(filters, 1, 20)
        ttl = cache.get_ttl(cache_key)
        
        # TTL should be around 300 seconds (5 minutes)
        assert ttl is not None
        assert 290 <= ttl <= 300  # Allow small variance

    def test_pagination_limit_enforced(self, search_service, sample_jobs, pg_db_session):
        """
        Test that page size is limited to maximum 100.
        
        **Validates: Requirements 6.13, 16.3**
        """
        filters = SearchFilters()
        
        # Should raise error for page_size > 100
        with pytest.raises(ValueError, match="Page size must be between 1 and 100"):
            search_service.search_jobs(filters, page=1, page_size=101)

    def test_multiple_job_types_filter(self, search_service, sample_jobs, pg_db_session):
        """
        Test filtering by multiple job types.
        
        **Validates: Requirements 6.3**
        """
        filters = SearchFilters(jobType=[JobType.FULL_TIME, JobType.CONTRACT])
        result = search_service.search_jobs(filters, page=1, page_size=20)
        
        # Should find jobs matching either type
        assert result["total"] >= 2
        for job in result["jobs"]:
            assert job.job_type in [JobType.FULL_TIME, JobType.CONTRACT]

    def test_multiple_experience_levels_filter(self, search_service, sample_jobs, pg_db_session):
        """
        Test filtering by multiple experience levels.
        
        **Validates: Requirements 6.4**
        """
        filters = SearchFilters(experienceLevel=[ExperienceLevel.SENIOR, ExperienceLevel.MID])
        result = search_service.search_jobs(filters, page=1, page_size=20)
        
        # Should find jobs matching either level
        assert result["total"] >= 2
        for job in result["jobs"]:
            assert job.experience_level in [ExperienceLevel.SENIOR, ExperienceLevel.MID]

    def test_salary_range_filter_combination(self, search_service, sample_jobs, pg_db_session):
        """
        Test filtering by both minimum and maximum salary.
        
        **Validates: Requirements 6.5, 6.6**
        """
        filters = SearchFilters(salaryMin=70000, salaryMax=120000)
        result = search_service.search_jobs(filters, page=1, page_size=20)
        
        # Should find jobs within salary range
        assert result["total"] >= 1
        for job in result["jobs"]:
            if job.salary_min is not None and job.salary_max is not None:
                # Job salary range should overlap with filter range
                assert job.salary_max >= 70000
                assert job.salary_min <= 120000

    def test_complex_filter_combination(self, search_service, sample_jobs, pg_db_session):
        """
        Test complex combination of multiple filters.
        
        **Validates: Requirements 6.10**
        """
        filters = SearchFilters(
            location="San Francisco",
            remote=True,
            jobType=[JobType.FULL_TIME],
            experienceLevel=[ExperienceLevel.SENIOR]
        )
        result = search_service.search_jobs(filters, page=1, page_size=20)
        
        # All results should match ALL filters
        for job in result["jobs"]:
            assert job.location == "San Francisco"
            assert job.remote is True
            assert job.job_type == JobType.FULL_TIME
            assert job.experience_level == ExperienceLevel.SENIOR
