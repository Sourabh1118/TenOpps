"""
Unit tests for the scraping service.

Tests cover:
- BaseScraper abstract class functionality
- Rate limiting with token bucket algorithm
- Retry logic with exponential backoff
- Job data normalization functions
- Scraping task management
- Redis-based rate limiter
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any, List

from app.services.scraping import (
    BaseScraper,
    RateLimiter,
    ScrapingError,
    RateLimitExceeded,
    normalize_job_type,
    normalize_experience_level,
    normalize_date_to_iso,
    extract_salary_info,
    create_scraping_task,
    update_scraping_task,
    LinkedInScraper,
    IndeedScraper,
    NaukriScraper,
    MonsterScraper,
)
from app.models.job import JobType, ExperienceLevel, SourceType
from app.models.scraping_task import TaskType, TaskStatus


# Concrete implementation of BaseScraper for testing
class TestScraper(BaseScraper):
    """Test implementation of BaseScraper."""
    
    def __init__(self, source_name: str, rate_limit: int, fail_count: int = 0):
        super().__init__(source_name, rate_limit)
        self.fail_count = fail_count
        self.attempt_count = 0
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """Mock scrape implementation."""
        self.attempt_count += 1
        
        if self.attempt_count <= self.fail_count:
            raise Exception(f"Scraping failed (attempt {self.attempt_count})")
        
        return [
            {
                "title": "Software Engineer",
                "company": "Tech Corp",
                "location": "San Francisco, CA",
                "description": "Build amazing software",
                "url": "https://example.com/job1"
            }
        ]
    
    def normalize_job(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock normalize implementation."""
        return {
            "title": raw_data["title"],
            "company": raw_data["company"],
            "location": raw_data["location"],
            "description": raw_data["description"],
            "source_url": raw_data["url"],
            "job_type": JobType.FULL_TIME,
            "experience_level": ExperienceLevel.MID,
        }


class TestBaseScraper:
    """Tests for BaseScraper abstract class."""
    
    @pytest.mark.asyncio
    async def test_scraper_initialization(self):
        """Test scraper initialization with rate limit."""
        scraper = TestScraper("test_source", rate_limit=10)
        
        assert scraper.source_name == "test_source"
        assert scraper.rate_limit == 10
        assert scraper.rate_limit_period == 60
        assert scraper.max_retries == 3
        assert scraper.base_backoff_delay == 5
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_check_rate_limit_first_request(self, mock_redis_client):
        """Test rate limit check on first request."""
        mock_redis = Mock()
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        mock_redis_client.get_cache_client.return_value = mock_redis
        
        scraper = TestScraper("test_source", rate_limit=10)
        result = await scraper.check_rate_limit()
        
        assert result is True
        mock_redis.setex.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_check_rate_limit_tokens_available(self, mock_redis_client):
        """Test rate limit check with tokens available."""
        mock_redis = Mock()
        mock_redis.get.return_value = "5"
        mock_redis.decr.return_value = 4
        mock_redis_client.get_cache_client.return_value = mock_redis
        
        scraper = TestScraper("test_source", rate_limit=10)
        result = await scraper.check_rate_limit()
        
        assert result is True
        mock_redis.decr.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_check_rate_limit_exceeded(self, mock_redis_client):
        """Test rate limit check when limit is exceeded."""
        mock_redis = Mock()
        mock_redis.get.return_value = "0"
        mock_redis.ttl.return_value = 30
        mock_redis_client.get_cache_client.return_value = mock_redis
        
        scraper = TestScraper("test_source", rate_limit=10)
        result = await scraper.check_rate_limit()
        
        assert result is False
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_scrape_with_retry_success_first_attempt(self, mock_redis_client):
        """Test successful scraping on first attempt."""
        mock_redis = Mock()
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        mock_redis_client.get_cache_client.return_value = mock_redis
        
        scraper = TestScraper("test_source", rate_limit=10, fail_count=0)
        jobs = await scraper.scrape_with_retry()
        
        assert len(jobs) == 1
        assert jobs[0]["title"] == "Software Engineer"
        assert scraper.attempt_count == 1
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_scrape_with_retry_success_after_failures(self, mock_redis_client):
        """Test successful scraping after 2 failures."""
        mock_redis = Mock()
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        mock_redis_client.get_cache_client.return_value = mock_redis
        
        scraper = TestScraper("test_source", rate_limit=10, fail_count=2)
        
        # Mock asyncio.sleep to avoid waiting
        with patch('asyncio.sleep', new_callable=AsyncMock):
            jobs = await scraper.scrape_with_retry()
        
        assert len(jobs) == 1
        assert scraper.attempt_count == 3  # Failed twice, succeeded on third
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_scrape_with_retry_all_attempts_fail(self, mock_redis_client):
        """Test scraping failure after all retry attempts."""
        mock_redis = Mock()
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        mock_redis_client.get_cache_client.return_value = mock_redis
        
        scraper = TestScraper("test_source", rate_limit=10, fail_count=5)
        
        # Mock asyncio.sleep to avoid waiting
        with patch('asyncio.sleep', new_callable=AsyncMock):
            with pytest.raises(ScrapingError) as exc_info:
                await scraper.scrape_with_retry()
        
        assert "All 3 scraping attempts failed" in str(exc_info.value)
        assert scraper.attempt_count == 3
    
    def test_log_metrics(self):
        """Test metrics logging."""
        scraper = TestScraper("test_source", rate_limit=10)
        
        # Should not raise any exceptions
        scraper.log_metrics(
            jobs_found=100,
            jobs_created=80,
            jobs_updated=20,
            duration=45.5
        )


class TestNormalizationFunctions:
    """Tests for job data normalization functions."""
    
    def test_normalize_job_type_full_time(self):
        """Test normalization of full-time job types."""
        assert normalize_job_type("Full-Time") == JobType.FULL_TIME
        assert normalize_job_type("full time") == JobType.FULL_TIME
        assert normalize_job_type("FULLTIME") == JobType.FULL_TIME
        assert normalize_job_type("Permanent") == JobType.FULL_TIME
    
    def test_normalize_job_type_part_time(self):
        """Test normalization of part-time job types."""
        assert normalize_job_type("Part-Time") == JobType.PART_TIME
        assert normalize_job_type("part time") == JobType.PART_TIME
        assert normalize_job_type("PARTTIME") == JobType.PART_TIME
    
    def test_normalize_job_type_contract(self):
        """Test normalization of contract job types."""
        assert normalize_job_type("Contract") == JobType.CONTRACT
        assert normalize_job_type("Contractor") == JobType.CONTRACT
        assert normalize_job_type("Temporary") == JobType.CONTRACT
        assert normalize_job_type("Temp") == JobType.CONTRACT
    
    def test_normalize_job_type_freelance(self):
        """Test normalization of freelance job types."""
        assert normalize_job_type("Freelance") == JobType.FREELANCE
        assert normalize_job_type("Freelancer") == JobType.FREELANCE
        assert normalize_job_type("Gig") == JobType.FREELANCE
    
    def test_normalize_job_type_internship(self):
        """Test normalization of internship job types."""
        assert normalize_job_type("Internship") == JobType.INTERNSHIP
        assert normalize_job_type("Intern") == JobType.INTERNSHIP
        assert normalize_job_type("Trainee") == JobType.INTERNSHIP
    
    def test_normalize_job_type_fellowship(self):
        """Test normalization of fellowship job types."""
        assert normalize_job_type("Fellowship") == JobType.FELLOWSHIP
        assert normalize_job_type("Fellow") == JobType.FELLOWSHIP
    
    def test_normalize_job_type_academic(self):
        """Test normalization of academic job types."""
        assert normalize_job_type("Academic") == JobType.ACADEMIC
        assert normalize_job_type("Faculty") == JobType.ACADEMIC
        assert normalize_job_type("Professor") == JobType.ACADEMIC
        assert normalize_job_type("Researcher") == JobType.ACADEMIC
    
    def test_normalize_job_type_unknown(self):
        """Test normalization of unknown job types defaults to FULL_TIME."""
        assert normalize_job_type("Unknown Type") == JobType.FULL_TIME
        assert normalize_job_type("") == JobType.FULL_TIME
        assert normalize_job_type(None) == JobType.FULL_TIME
    
    def test_normalize_experience_level_entry(self):
        """Test normalization of entry level."""
        assert normalize_experience_level("Entry Level") == ExperienceLevel.ENTRY
        assert normalize_experience_level("Junior") == ExperienceLevel.ENTRY
        assert normalize_experience_level("Jr") == ExperienceLevel.ENTRY
        assert normalize_experience_level("Graduate") == ExperienceLevel.ENTRY
        assert normalize_experience_level("Associate") == ExperienceLevel.ENTRY
    
    def test_normalize_experience_level_mid(self):
        """Test normalization of mid level."""
        assert normalize_experience_level("Mid Level") == ExperienceLevel.MID
        assert normalize_experience_level("Intermediate") == ExperienceLevel.MID
        assert normalize_experience_level("Experienced") == ExperienceLevel.MID
    
    def test_normalize_experience_level_senior(self):
        """Test normalization of senior level."""
        assert normalize_experience_level("Senior") == ExperienceLevel.SENIOR
        assert normalize_experience_level("Sr") == ExperienceLevel.SENIOR
        assert normalize_experience_level("Principal") == ExperienceLevel.SENIOR
        assert normalize_experience_level("Staff") == ExperienceLevel.SENIOR
    
    def test_normalize_experience_level_lead(self):
        """Test normalization of lead level."""
        assert normalize_experience_level("Lead") == ExperienceLevel.LEAD
        assert normalize_experience_level("Manager") == ExperienceLevel.LEAD
        assert normalize_experience_level("Head") == ExperienceLevel.LEAD
        assert normalize_experience_level("Director") == ExperienceLevel.LEAD
    
    def test_normalize_experience_level_executive(self):
        """Test normalization of executive level."""
        assert normalize_experience_level("Executive") == ExperienceLevel.EXECUTIVE
        assert normalize_experience_level("VP") == ExperienceLevel.EXECUTIVE
        assert normalize_experience_level("Vice President") == ExperienceLevel.EXECUTIVE
        assert normalize_experience_level("CTO") == ExperienceLevel.EXECUTIVE
        assert normalize_experience_level("CEO") == ExperienceLevel.EXECUTIVE
    
    def test_normalize_experience_level_unknown(self):
        """Test normalization of unknown experience level defaults to MID."""
        assert normalize_experience_level("Unknown") == ExperienceLevel.MID
        assert normalize_experience_level("") == ExperienceLevel.MID
        assert normalize_experience_level(None) == ExperienceLevel.MID
    
    def test_normalize_date_to_iso_datetime_object(self):
        """Test date normalization from datetime object."""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = normalize_date_to_iso(dt)
        assert result == "2024-01-15T10:30:00"
    
    def test_normalize_date_to_iso_string(self):
        """Test date normalization from ISO string."""
        result = normalize_date_to_iso("2024-01-15T10:30:00")
        assert "2024-01-15" in result
    
    def test_normalize_date_to_iso_common_formats(self):
        """Test date normalization from common date formats."""
        result1 = normalize_date_to_iso("2024-01-15")
        assert "2024-01-15" in result1
        
        result2 = normalize_date_to_iso("2024/01/15")
        assert "2024-01-15" in result2
    
    def test_normalize_date_to_iso_invalid(self):
        """Test date normalization with invalid input defaults to current time."""
        result = normalize_date_to_iso("invalid date")
        # Should return a valid ISO date string
        assert "T" in result
        assert len(result) > 10
    
    def test_extract_salary_info_range_with_commas(self):
        """Test salary extraction from range with commas."""
        result = extract_salary_info("$100,000 - $150,000")
        assert result['salary_min'] == 100000
        assert result['salary_max'] == 150000
    
    def test_extract_salary_info_range_with_k(self):
        """Test salary extraction from range with k notation."""
        result = extract_salary_info("$100k - $150k")
        assert result['salary_min'] == 100000
        assert result['salary_max'] == 150000
    
    def test_extract_salary_info_single_value(self):
        """Test salary extraction from single value."""
        result = extract_salary_info("$120,000")
        assert result['salary_min'] == 120000
        assert result['salary_max'] == 120000
    
    def test_extract_salary_info_single_value_k(self):
        """Test salary extraction from single value with k."""
        result = extract_salary_info("120k")
        assert result['salary_min'] == 120000
        assert result['salary_max'] == 120000
    
    def test_extract_salary_info_no_currency(self):
        """Test salary extraction without currency symbols."""
        result = extract_salary_info("100000-150000")
        assert result['salary_min'] == 100000
        assert result['salary_max'] == 150000
    
    def test_extract_salary_info_empty(self):
        """Test salary extraction from empty string."""
        result = extract_salary_info("")
        assert result['salary_min'] is None
        assert result['salary_max'] is None
    
    def test_extract_salary_info_none(self):
        """Test salary extraction from None."""
        result = extract_salary_info(None)
        assert result['salary_min'] is None
        assert result['salary_max'] is None


class TestScrapingTaskManagement:
    """Tests for scraping task management functions."""
    
    @pytest.mark.asyncio
    async def test_create_scraping_task_scheduled(self):
        """Test creating a scheduled scraping task."""
        mock_session = Mock()
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.refresh = Mock()
        
        task = await create_scraping_task(
            task_type=TaskType.SCHEDULED_SCRAPE,
            source_platform="linkedin",
            db_session=mock_session
        )
        
        assert task.task_type == TaskType.SCHEDULED_SCRAPE
        assert task.source_platform == "linkedin"
        assert task.status == TaskStatus.PENDING
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_scraping_task_url_import(self):
        """Test creating a URL import task."""
        mock_session = Mock()
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.refresh = Mock()
        
        task = await create_scraping_task(
            task_type=TaskType.URL_IMPORT,
            target_url="https://example.com/job/123",
            db_session=mock_session
        )
        
        assert task.task_type == TaskType.URL_IMPORT
        assert task.target_url == "https://example.com/job/123"
        assert task.status == TaskStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_update_scraping_task_success(self):
        """Test updating a scraping task with success metrics."""
        mock_task = Mock()
        mock_task.id = "test-task-id"
        mock_task.status = TaskStatus.PENDING
        mock_task.jobs_found = 0
        mock_task.jobs_created = 0
        mock_task.jobs_updated = 0
        
        mock_session = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_task
        mock_session.query.return_value = mock_query
        mock_session.commit = Mock()
        
        await update_scraping_task(
            task_id="test-task-id",
            updates={
                'status': TaskStatus.COMPLETED,
                'jobs_found': 100,
                'jobs_created': 80,
                'jobs_updated': 20,
            },
            db_session=mock_session
        )
        
        assert mock_task.status == TaskStatus.COMPLETED
        assert mock_task.jobs_found == 100
        assert mock_task.jobs_created == 80
        assert mock_task.jobs_updated == 20
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_scraping_task_failure(self):
        """Test updating a scraping task with failure."""
        mock_task = Mock()
        mock_task.id = "test-task-id"
        mock_task.status = TaskStatus.RUNNING
        mock_task.error_message = None
        
        mock_session = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_task
        mock_session.query.return_value = mock_query
        mock_session.commit = Mock()
        
        await update_scraping_task(
            task_id="test-task-id",
            updates={
                'status': TaskStatus.FAILED,
                'error_message': 'Connection timeout',
            },
            db_session=mock_session
        )
        
        assert mock_task.status == TaskStatus.FAILED
        assert mock_task.error_message == 'Connection timeout'


class TestRateLimiter:
    """Tests for Redis-based rate limiter."""
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_rate_limiter_initialization(self, mock_redis_client):
        """Test rate limiter initialization with default limits."""
        limiter = RateLimiter("linkedin")
        assert limiter.source == "linkedin"
        assert limiter.limit == 10
        assert limiter.period == 60
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_rate_limiter_custom_limit(self, mock_redis_client):
        """Test rate limiter with custom limit."""
        limiter = RateLimiter("custom_source", limit=50)
        assert limiter.source == "custom_source"
        assert limiter.limit == 50
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_rate_limiter_acquire_first_request(self, mock_redis_client):
        """Test acquiring token on first request."""
        mock_redis = Mock()
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        mock_redis_client.get_cache_client.return_value = mock_redis
        
        limiter = RateLimiter("linkedin")
        result = await limiter.acquire()
        
        assert result is True
        mock_redis.setex.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_rate_limiter_acquire_within_limit(self, mock_redis_client):
        """Test acquiring token within rate limit."""
        mock_redis = Mock()
        mock_redis.get.return_value = "5"
        mock_redis.incr.return_value = 6
        mock_redis_client.get_cache_client.return_value = mock_redis
        
        limiter = RateLimiter("linkedin", limit=10)
        result = await limiter.acquire()
        
        assert result is True
        mock_redis.incr.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_rate_limiter_acquire_limit_exceeded(self, mock_redis_client):
        """Test acquiring token when limit is exceeded."""
        mock_redis = Mock()
        mock_redis.get.return_value = "10"
        mock_redis_client.get_cache_client.return_value = mock_redis
        
        limiter = RateLimiter("linkedin", limit=10)
        result = await limiter.acquire()
        
        assert result is False
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_rate_limiter_get_remaining(self, mock_redis_client):
        """Test getting remaining requests."""
        mock_redis = Mock()
        mock_redis.get.return_value = "7"
        mock_redis_client.get_cache_client.return_value = mock_redis
        
        limiter = RateLimiter("linkedin", limit=10)
        remaining = limiter.get_remaining()
        
        assert remaining == 3
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_rate_limiter_get_remaining_no_usage(self, mock_redis_client):
        """Test getting remaining requests with no usage."""
        mock_redis = Mock()
        mock_redis.get.return_value = None
        mock_redis_client.get_cache_client.return_value = mock_redis
        
        limiter = RateLimiter("linkedin", limit=10)
        remaining = limiter.get_remaining()
        
        assert remaining == 10


class TestLinkedInScraper:
    """Tests for LinkedIn RSS scraper."""
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_linkedin_scraper_initialization(self, mock_redis_client):
        """Test LinkedIn scraper initialization."""
        scraper = LinkedInScraper(
            rss_feed_url="https://www.linkedin.com/jobs/feed",
            rate_limit=10
        )
        
        assert scraper.source_name == "linkedin"
        assert scraper.rss_feed_url == "https://www.linkedin.com/jobs/feed"
        assert scraper.rate_limit == 10
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    @patch('app.services.scraping.requests.get')
    async def test_linkedin_scraper_scrape_success(self, mock_get, mock_redis_client):
        """Test successful scraping of LinkedIn RSS feed."""
        # Mock RSS feed response
        mock_rss_content = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>LinkedIn Jobs</title>
                <item>
                    <title>Senior Software Engineer</title>
                    <author>Tech Corp</author>
                    <link>https://www.linkedin.com/jobs/view/123</link>
                    <description>Build amazing software products</description>
                    <pubDate>Mon, 15 Jan 2024 10:00:00 GMT</pubDate>
                </item>
                <item>
                    <title>Product Manager</title>
                    <author>Startup Inc</author>
                    <link>https://www.linkedin.com/jobs/view/456</link>
                    <description>Lead product development</description>
                    <pubDate>Tue, 16 Jan 2024 12:00:00 GMT</pubDate>
                </item>
            </channel>
        </rss>"""
        
        mock_response = Mock()
        mock_response.content = mock_rss_content.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        scraper = LinkedInScraper(
            rss_feed_url="https://www.linkedin.com/jobs/feed",
            rate_limit=10
        )
        
        jobs = await scraper.scrape()
        
        assert len(jobs) == 2
        assert jobs[0]['title'] == 'Senior Software Engineer'
        assert jobs[0]['company'] == 'Tech Corp'
        assert jobs[0]['link'] == 'https://www.linkedin.com/jobs/view/123'
        assert jobs[1]['title'] == 'Product Manager'
        assert jobs[1]['company'] == 'Startup Inc'
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    @patch('app.services.scraping.requests.get')
    async def test_linkedin_scraper_scrape_request_error(self, mock_get, mock_redis_client):
        """Test scraping failure due to request error."""
        mock_get.side_effect = Exception("Connection timeout")
        
        scraper = LinkedInScraper(
            rss_feed_url="https://www.linkedin.com/jobs/feed",
            rate_limit=10
        )
        
        with pytest.raises(ScrapingError) as exc_info:
            await scraper.scrape()
        
        assert "Failed to parse LinkedIn RSS feed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_linkedin_scraper_normalize_job(self, mock_redis_client):
        """Test normalization of LinkedIn RSS job data."""
        scraper = LinkedInScraper(
            rss_feed_url="https://www.linkedin.com/jobs/feed",
            rate_limit=10
        )
        
        raw_data = {
            'title': 'Senior Software Engineer',
            'company': 'Tech Corp',
            'location': 'San Francisco, CA',
            'link': 'https://www.linkedin.com/jobs/view/123',
            'description': 'Build amazing software products with cutting-edge technologies',
            'published': '2024-01-15T10:00:00',
            'job_type': 'Full-Time',
            'experience_level': 'Senior',
        }
        
        normalized = scraper.normalize_job(raw_data)
        
        assert normalized['title'] == 'Senior Software Engineer'
        assert normalized['company'] == 'Tech Corp'
        assert normalized['location'] == 'San Francisco, CA'
        assert normalized['source_url'] == 'https://www.linkedin.com/jobs/view/123'
        assert normalized['source_platform'] == 'linkedin'
        assert normalized['source_type'] == SourceType.AGGREGATED
        assert normalized['job_type'] == JobType.FULL_TIME
        assert normalized['experience_level'] == ExperienceLevel.SENIOR
        assert normalized['remote'] is False
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_linkedin_scraper_normalize_job_remote(self, mock_redis_client):
        """Test normalization of remote LinkedIn job."""
        scraper = LinkedInScraper(
            rss_feed_url="https://www.linkedin.com/jobs/feed",
            rate_limit=10
        )
        
        raw_data = {
            'title': 'Remote Software Engineer',
            'company': 'Remote Corp',
            'location': 'Remote',
            'link': 'https://www.linkedin.com/jobs/view/789',
            'description': 'Work from anywhere',
            'published': '2024-01-15T10:00:00',
            'job_type': 'Full-Time',
            'experience_level': 'Mid Level',
        }
        
        normalized = scraper.normalize_job(raw_data)
        
        assert normalized['remote'] is True
        assert normalized['location'] == 'Remote'
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_linkedin_scraper_normalize_job_with_salary(self, mock_redis_client):
        """Test normalization of LinkedIn job with salary in description."""
        scraper = LinkedInScraper(
            rss_feed_url="https://www.linkedin.com/jobs/feed",
            rate_limit=10
        )
        
        raw_data = {
            'title': 'Software Engineer',
            'company': 'Tech Corp',
            'location': 'New York, NY',
            'link': 'https://www.linkedin.com/jobs/view/999',
            'description': 'Great opportunity! Salary: $120k - $150k per year',
            'published': '2024-01-15T10:00:00',
            'job_type': 'Full-Time',
            'experience_level': 'Mid Level',
        }
        
        normalized = scraper.normalize_job(raw_data)
        
        assert normalized['salary_min'] == 120000
        assert normalized['salary_max'] == 150000
        assert normalized['salary_currency'] == 'USD'
    
    def test_linkedin_scraper_extract_location(self):
        """Test location extraction from RSS entry."""
        scraper = LinkedInScraper(
            rss_feed_url="https://www.linkedin.com/jobs/feed",
            rate_limit=10
        )
        
        # Test with explicit location
        entry = {'location': 'San Francisco, CA'}
        assert scraper._extract_location(entry) == 'San Francisco, CA'
        
        # Test with remote in summary
        entry = {'summary': 'This is a remote position'}
        assert scraper._extract_location(entry) == 'Remote'
        
        # Test with no location
        entry = {'summary': 'Some job description'}
        assert scraper._extract_location(entry) == 'Not specified'
    
    def test_linkedin_scraper_extract_job_type(self):
        """Test job type extraction from RSS entry."""
        scraper = LinkedInScraper(
            rss_feed_url="https://www.linkedin.com/jobs/feed",
            rate_limit=10
        )
        
        # Test with tags
        entry = {'tags': [{'term': 'Full-Time'}]}
        assert scraper._extract_job_type(entry) == 'Full-Time'
        
        # Test without tags
        entry = {}
        assert scraper._extract_job_type(entry) == 'Full-Time'
    
    def test_linkedin_scraper_extract_experience_level(self):
        """Test experience level extraction from RSS entry."""
        scraper = LinkedInScraper(
            rss_feed_url="https://www.linkedin.com/jobs/feed",
            rate_limit=10
        )
        
        # Test senior level
        entry = {'title': 'Senior Software Engineer', 'summary': ''}
        assert scraper._extract_experience_level(entry) == 'Senior'
        
        # Test entry level
        entry = {'title': 'Junior Developer', 'summary': ''}
        assert scraper._extract_experience_level(entry) == 'Entry Level'
        
        # Test lead level
        entry = {'title': 'Engineering Manager', 'summary': ''}
        assert scraper._extract_experience_level(entry) == 'Lead'
        
        # Test default
        entry = {'title': 'Software Engineer', 'summary': ''}
        assert scraper._extract_experience_level(entry) == 'Mid Level'


class TestIndeedScraper:
    """Tests for Indeed API scraper."""
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_indeed_scraper_initialization(self, mock_redis_client):
        """Test Indeed scraper initialization."""
        scraper = IndeedScraper(
            api_key="test_api_key",
            query="software engineer",
            location="San Francisco, CA",
            rate_limit=20
        )
        
        assert scraper.source_name == "indeed"
        assert scraper.api_key == "test_api_key"
        assert scraper.query == "software engineer"
        assert scraper.location == "San Francisco, CA"
        assert scraper.rate_limit == 20
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    @patch('app.services.scraping.requests.get')
    async def test_indeed_scraper_scrape_success(self, mock_get, mock_redis_client):
        """Test successful scraping from Indeed API."""
        # Mock Indeed API response
        mock_response_data = {
            'results': [
                {
                    'jobtitle': 'Senior Software Engineer',
                    'company': 'Tech Corp',
                    'city': 'San Francisco',
                    'state': 'CA',
                    'country': 'US',
                    'formattedLocation': 'San Francisco, CA',
                    'snippet': 'Build amazing software products. Full-time position. Senior level.',
                    'url': 'https://www.indeed.com/viewjob?jk=123',
                    'date': 'Mon, 15 Jan 2024 10:00:00 GMT',
                    'jobkey': '123',
                    'sponsored': False,
                    'expired': False,
                    'formattedRelativeTime': '2 days ago',
                },
                {
                    'jobtitle': 'Product Manager',
                    'company': 'Startup Inc',
                    'city': 'New York',
                    'state': 'NY',
                    'country': 'US',
                    'formattedLocation': 'New York, NY',
                    'snippet': 'Lead product development. Full-time role.',
                    'url': 'https://www.indeed.com/viewjob?jk=456',
                    'date': 'Tue, 16 Jan 2024 12:00:00 GMT',
                    'jobkey': '456',
                    'sponsored': False,
                    'expired': False,
                    'formattedRelativeTime': '1 day ago',
                },
            ],
            'totalResults': 2
        }
        
        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        scraper = IndeedScraper(
            api_key="test_api_key",
            query="software engineer",
            location="San Francisco, CA",
            rate_limit=20
        )
        
        jobs = await scraper.scrape()
        
        assert len(jobs) == 2
        assert jobs[0]['jobtitle'] == 'Senior Software Engineer'
        assert jobs[0]['company'] == 'Tech Corp'
        assert jobs[0]['formattedLocation'] == 'San Francisco, CA'
        assert jobs[1]['jobtitle'] == 'Product Manager'
        assert jobs[1]['company'] == 'Startup Inc'
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    @patch('app.services.scraping.requests.get')
    async def test_indeed_scraper_scrape_pagination(self, mock_get, mock_redis_client):
        """Test scraping with pagination."""
        # Mock first page
        mock_response_page1 = Mock()
        mock_response_page1.json.return_value = {
            'results': [
                {
                    'jobtitle': 'Job 1',
                    'company': 'Company 1',
                    'formattedLocation': 'Location 1',
                    'snippet': 'Description 1',
                    'url': 'https://www.indeed.com/viewjob?jk=1',
                    'date': 'Mon, 15 Jan 2024 10:00:00 GMT',
                    'jobkey': '1',
                }
            ] * 25,  # Full page
            'totalResults': 50
        }
        mock_response_page1.raise_for_status = Mock()
        
        # Mock second page
        mock_response_page2 = Mock()
        mock_response_page2.json.return_value = {
            'results': [
                {
                    'jobtitle': 'Job 26',
                    'company': 'Company 26',
                    'formattedLocation': 'Location 26',
                    'snippet': 'Description 26',
                    'url': 'https://www.indeed.com/viewjob?jk=26',
                    'date': 'Mon, 15 Jan 2024 10:00:00 GMT',
                    'jobkey': '26',
                }
            ] * 25,  # Full page
            'totalResults': 50
        }
        mock_response_page2.raise_for_status = Mock()
        
        mock_get.side_effect = [mock_response_page1, mock_response_page2]
        
        scraper = IndeedScraper(
            api_key="test_api_key",
            query="software engineer",
            location="San Francisco, CA",
            rate_limit=20
        )
        
        jobs = await scraper.scrape()
        
        assert len(jobs) == 50
        assert mock_get.call_count == 2
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    @patch('app.services.scraping.requests.get')
    async def test_indeed_scraper_scrape_request_error(self, mock_get, mock_redis_client):
        """Test scraping failure due to request error."""
        mock_get.side_effect = Exception("Connection timeout")
        
        scraper = IndeedScraper(
            api_key="test_api_key",
            query="software engineer",
            location="San Francisco, CA",
            rate_limit=20
        )
        
        with pytest.raises(ScrapingError) as exc_info:
            await scraper.scrape()
        
        assert "Failed to parse Indeed API response" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_indeed_scraper_normalize_job(self, mock_redis_client):
        """Test normalization of Indeed API job data."""
        scraper = IndeedScraper(
            api_key="test_api_key",
            query="software engineer",
            location="San Francisco, CA",
            rate_limit=20
        )
        
        raw_data = {
            'jobtitle': 'Senior Software Engineer',
            'company': 'Tech Corp',
            'city': 'San Francisco',
            'state': 'CA',
            'country': 'US',
            'formattedLocation': 'San Francisco, CA',
            'snippet': 'Build amazing software products with cutting-edge technologies. Full-time position. Senior level required.',
            'url': 'https://www.indeed.com/viewjob?jk=123',
            'date': 'Mon, 15 Jan 2024 10:00:00 GMT',
            'jobkey': '123',
            'formattedRelativeTime': '2 days ago',
        }
        
        normalized = scraper.normalize_job(raw_data)
        
        assert normalized['title'] == 'Senior Software Engineer'
        assert normalized['company'] == 'Tech Corp'
        assert normalized['location'] == 'San Francisco, CA'
        assert normalized['source_url'] == 'https://www.indeed.com/viewjob?jk=123'
        assert normalized['source_platform'] == 'indeed'
        assert normalized['source_type'] == SourceType.AGGREGATED
        assert normalized['job_type'] == JobType.FULL_TIME
        assert normalized['experience_level'] == ExperienceLevel.SENIOR
        assert normalized['remote'] is False
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_indeed_scraper_normalize_job_remote(self, mock_redis_client):
        """Test normalization of remote Indeed job."""
        scraper = IndeedScraper(
            api_key="test_api_key",
            query="software engineer",
            location="Remote",
            rate_limit=20
        )
        
        raw_data = {
            'jobtitle': 'Remote Software Engineer',
            'company': 'Remote Corp',
            'formattedLocation': 'Remote',
            'snippet': 'Work from anywhere. Remote position available.',
            'url': 'https://www.indeed.com/viewjob?jk=789',
            'date': 'Mon, 15 Jan 2024 10:00:00 GMT',
            'jobkey': '789',
            'formattedRelativeTime': 'Just posted',
        }
        
        normalized = scraper.normalize_job(raw_data)
        
        assert normalized['remote'] is True
        assert normalized['location'] == 'Remote'
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_indeed_scraper_normalize_job_with_salary(self, mock_redis_client):
        """Test normalization of Indeed job with salary in snippet."""
        scraper = IndeedScraper(
            api_key="test_api_key",
            query="software engineer",
            location="San Francisco, CA",
            rate_limit=20
        )
        
        raw_data = {
            'jobtitle': 'Software Engineer',
            'company': 'Tech Corp',
            'formattedLocation': 'New York, NY',
            'snippet': 'Great opportunity! Salary: $120k - $150k per year. Full-time position.',
            'url': 'https://www.indeed.com/viewjob?jk=999',
            'date': 'Mon, 15 Jan 2024 10:00:00 GMT',
            'jobkey': '999',
            'formattedRelativeTime': '1 day ago',
        }
        
        normalized = scraper.normalize_job(raw_data)
        
        assert normalized['salary_min'] == 120000
        assert normalized['salary_max'] == 150000
        assert normalized['salary_currency'] == 'USD'
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_indeed_scraper_normalize_job_part_time(self, mock_redis_client):
        """Test normalization of part-time Indeed job."""
        scraper = IndeedScraper(
            api_key="test_api_key",
            query="software engineer",
            location="San Francisco, CA",
            rate_limit=20
        )
        
        raw_data = {
            'jobtitle': 'Part-Time Developer',
            'company': 'Startup Inc',
            'formattedLocation': 'Boston, MA',
            'snippet': 'Part-time position available. Flexible hours.',
            'url': 'https://www.indeed.com/viewjob?jk=111',
            'date': 'Mon, 15 Jan 2024 10:00:00 GMT',
            'jobkey': '111',
            'formattedRelativeTime': '3 hours ago',
        }
        
        normalized = scraper.normalize_job(raw_data)
        
        assert normalized['job_type'] == JobType.PART_TIME
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_indeed_scraper_normalize_job_internship(self, mock_redis_client):
        """Test normalization of internship Indeed job."""
        scraper = IndeedScraper(
            api_key="test_api_key",
            query="software engineer",
            location="San Francisco, CA",
            rate_limit=20
        )
        
        raw_data = {
            'jobtitle': 'Software Engineering Intern',
            'company': 'Big Tech',
            'formattedLocation': 'Seattle, WA',
            'snippet': 'Summer internship program. Entry level position for students.',
            'url': 'https://www.indeed.com/viewjob?jk=222',
            'date': 'Mon, 15 Jan 2024 10:00:00 GMT',
            'jobkey': '222',
            'formattedRelativeTime': '5 days ago',
        }
        
        normalized = scraper.normalize_job(raw_data)
        
        assert normalized['job_type'] == JobType.INTERNSHIP
        assert normalized['experience_level'] == ExperienceLevel.ENTRY
    
    def test_indeed_scraper_parse_posted_date_rfc2822(self):
        """Test parsing posted date from RFC 2822 format."""
        scraper = IndeedScraper(
            api_key="test_api_key",
            query="software engineer",
            location="San Francisco, CA",
            rate_limit=20
        )
        
        date_str = "Mon, 15 Jan 2024 10:00:00 GMT"
        result = scraper._parse_posted_date(date_str, "")
        
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
    
    def test_indeed_scraper_parse_posted_date_relative_just_posted(self):
        """Test parsing posted date from 'just posted' relative time."""
        scraper = IndeedScraper(
            api_key="test_api_key",
            query="software engineer",
            location="San Francisco, CA",
            rate_limit=20
        )
        
        result = scraper._parse_posted_date("", "Just posted")
        
        # Should be very recent (within last minute)
        assert (datetime.utcnow() - result).total_seconds() < 60
    
    def test_indeed_scraper_parse_posted_date_relative_days(self):
        """Test parsing posted date from relative days."""
        scraper = IndeedScraper(
            api_key="test_api_key",
            query="software engineer",
            location="San Francisco, CA",
            rate_limit=20
        )
        
        result = scraper._parse_posted_date("", "3 days ago")
        
        # Should be approximately 3 days ago
        days_diff = (datetime.utcnow() - result).days
        assert days_diff == 3
    
    def test_indeed_scraper_parse_posted_date_relative_hours(self):
        """Test parsing posted date from relative hours."""
        scraper = IndeedScraper(
            api_key="test_api_key",
            query="software engineer",
            location="San Francisco, CA",
            rate_limit=20
        )
        
        result = scraper._parse_posted_date("", "5 hours ago")
        
        # Should be approximately 5 hours ago
        hours_diff = (datetime.utcnow() - result).total_seconds() / 3600
        assert 4.5 <= hours_diff <= 5.5
    
    def test_indeed_scraper_extract_job_type_full_time(self):
        """Test extracting full-time job type from snippet."""
        scraper = IndeedScraper(
            api_key="test_api_key",
            query="software engineer",
            location="San Francisco, CA",
            rate_limit=20
        )
        
        assert scraper._extract_job_type_from_snippet("Full-time position available") == "Full-Time"
        assert scraper._extract_job_type_from_snippet("Permanent role") == "Full-Time"
    
    def test_indeed_scraper_extract_job_type_part_time(self):
        """Test extracting part-time job type from snippet."""
        scraper = IndeedScraper(
            api_key="test_api_key",
            query="software engineer",
            location="San Francisco, CA",
            rate_limit=20
        )
        
        assert scraper._extract_job_type_from_snippet("Part-time position") == "Part-Time"
        assert scraper._extract_job_type_from_snippet("Looking for part time help") == "Part-Time"
    
    def test_indeed_scraper_extract_job_type_contract(self):
        """Test extracting contract job type from snippet."""
        scraper = IndeedScraper(
            api_key="test_api_key",
            query="software engineer",
            location="San Francisco, CA",
            rate_limit=20
        )
        
        assert scraper._extract_job_type_from_snippet("Contract position for 6 months") == "Contract"
        assert scraper._extract_job_type_from_snippet("Temporary role") == "Contract"
    
    def test_indeed_scraper_extract_job_type_internship(self):
        """Test extracting internship job type from snippet."""
        scraper = IndeedScraper(
            api_key="test_api_key",
            query="software engineer",
            location="San Francisco, CA",
            rate_limit=20
        )
        
        assert scraper._extract_job_type_from_snippet("Summer internship program") == "Internship"
        assert scraper._extract_job_type_from_snippet("Intern position available") == "Internship"
    
    def test_indeed_scraper_extract_experience_level_senior(self):
        """Test extracting senior experience level from snippet."""
        scraper = IndeedScraper(
            api_key="test_api_key",
            query="software engineer",
            location="San Francisco, CA",
            rate_limit=20
        )
        
        assert scraper._extract_experience_level_from_snippet("Senior engineer needed") == "Senior"
        assert scraper._extract_experience_level_from_snippet("Principal developer role") == "Senior"
    
    def test_indeed_scraper_extract_experience_level_entry(self):
        """Test extracting entry experience level from snippet."""
        scraper = IndeedScraper(
            api_key="test_api_key",
            query="software engineer",
            location="San Francisco, CA",
            rate_limit=20
        )
        
        assert scraper._extract_experience_level_from_snippet("Entry-level position") == "Entry Level"
        assert scraper._extract_experience_level_from_snippet("Junior developer wanted") == "Entry Level"
    
    def test_indeed_scraper_extract_experience_level_lead(self):
        """Test extracting lead experience level from snippet."""
        scraper = IndeedScraper(
            api_key="test_api_key",
            query="software engineer",
            location="San Francisco, CA",
            rate_limit=20
        )
        
        assert scraper._extract_experience_level_from_snippet("Lead engineer position") == "Lead"
        assert scraper._extract_experience_level_from_snippet("Engineering manager role") == "Lead"
    
    def test_indeed_scraper_extract_experience_level_default(self):
        """Test extracting default experience level from snippet."""
        scraper = IndeedScraper(
            api_key="test_api_key",
            query="software engineer",
            location="San Francisco, CA",
            rate_limit=20
        )
        
        assert scraper._extract_experience_level_from_snippet("Software engineer position") == "Mid Level"
        assert scraper._extract_experience_level_from_snippet("") == "Mid Level"


class TestNaukriScraper:
    """Tests for Naukri web scraper."""
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_naukri_scraper_initialization(self, mock_redis_client):
        """Test Naukri scraper initialization."""
        scraper = NaukriScraper(
            search_url="https://www.naukri.com/software-engineer-jobs",
            rate_limit=5
        )
        
        assert scraper.source_name == "naukri"
        assert scraper.search_url == "https://www.naukri.com/software-engineer-jobs"
        assert scraper.rate_limit == 5
        assert scraper.base_url == "https://www.naukri.com"
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    @patch('app.services.scraping.requests.get')
    async def test_naukri_scraper_scrape_success(self, mock_get, mock_redis_client):
        """Test successful scraping of Naukri search results."""
        # Mock search results page
        search_html = """
        <html>
            <body>
                <article class="jobTuple">
                    <a class="title" href="/job-listings-senior-software-engineer-tech-corp-123">Senior Software Engineer</a>
                </article>
                <article class="jobTuple">
                    <a class="title" href="/job-listings-product-manager-startup-inc-456">Product Manager</a>
                </article>
            </body>
        </html>
        """
        
        # Mock job page 1
        job_html_1 = """
        <html>
            <body>
                <h1 class="jd-header-title">Senior Software Engineer</h1>
                <a class="comp-name">Tech Corp</a>
                <span class="loc">Bangalore</span>
                <span class="exp">5-8 years</span>
                <span class="sal">15-20 Lacs PA</span>
                <div class="jd-desc">Build amazing software products</div>
                <div class="key-skill">
                    <a>Python</a>
                    <a>Django</a>
                </div>
                <span class="posted">Posted 2 days ago</span>
            </body>
        </html>
        """
        
        # Mock job page 2
        job_html_2 = """
        <html>
            <body>
                <h1 class="jd-header-title">Product Manager</h1>
                <a class="comp-name">Startup Inc</a>
                <span class="loc">Mumbai</span>
                <span class="exp">3-6 years</span>
                <span class="sal">12-18 Lacs PA</span>
                <div class="jd-desc">Lead product development</div>
                <span class="posted">Posted 1 day ago</span>
            </body>
        </html>
        """
        
        # Mock Redis for rate limiting
        mock_redis = Mock()
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        mock_redis_client.get_cache_client.return_value = mock_redis
        
        # Mock HTTP responses
        mock_search_response = Mock()
        mock_search_response.content = search_html.encode('utf-8')
        mock_search_response.raise_for_status = Mock()
        
        mock_job_response_1 = Mock()
        mock_job_response_1.content = job_html_1.encode('utf-8')
        mock_job_response_1.raise_for_status = Mock()
        
        mock_job_response_2 = Mock()
        mock_job_response_2.content = job_html_2.encode('utf-8')
        mock_job_response_2.raise_for_status = Mock()
        
        mock_get.side_effect = [mock_search_response, mock_job_response_1, mock_job_response_2]
        
        scraper = NaukriScraper(
            search_url="https://www.naukri.com/software-engineer-jobs",
            rate_limit=5
        )
        
        jobs = await scraper.scrape()
        
        assert len(jobs) == 2
        assert jobs[0]['title'] == 'Senior Software Engineer'
        assert jobs[0]['company'] == 'Tech Corp'
        assert jobs[0]['location'] == 'Bangalore'
        assert jobs[1]['title'] == 'Product Manager'
        assert jobs[1]['company'] == 'Startup Inc'
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    @patch('app.services.scraping.requests.get')
    async def test_naukri_scraper_scrape_no_jobs(self, mock_get, mock_redis_client):
        """Test scraping when no jobs are found."""
        # Mock empty search results
        search_html = """
        <html>
            <body>
                <div>No jobs found</div>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.content = search_html.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        scraper = NaukriScraper(
            search_url="https://www.naukri.com/software-engineer-jobs",
            rate_limit=5
        )
        
        jobs = await scraper.scrape()
        
        assert len(jobs) == 0
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    @patch('app.services.scraping.requests.get')
    async def test_naukri_scraper_scrape_request_error(self, mock_get, mock_redis_client):
        """Test scraping failure due to request error."""
        mock_get.side_effect = Exception("Connection timeout")
        
        scraper = NaukriScraper(
            search_url="https://www.naukri.com/software-engineer-jobs",
            rate_limit=5
        )
        
        with pytest.raises(ScrapingError) as exc_info:
            await scraper.scrape()
        
        assert "Failed to parse Naukri search results" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_naukri_scraper_normalize_job(self, mock_redis_client):
        """Test normalization of Naukri job data."""
        scraper = NaukriScraper(
            search_url="https://www.naukri.com/software-engineer-jobs",
            rate_limit=5
        )
        
        raw_data = {
            'title': 'Senior Software Engineer',
            'company': 'Tech Corp',
            'location': 'Bangalore',
            'experience': '5-8 years',
            'salary': '15-20 Lacs PA',
            'description': 'Build amazing software products with cutting-edge technologies',
            'skills': ['Python', 'Django', 'PostgreSQL'],
            'job_type': 'Full-Time',
            'posted': 'Posted 2 days ago',
            'url': 'https://www.naukri.com/job-listings-123',
        }
        
        normalized = scraper.normalize_job(raw_data)
        
        assert normalized['title'] == 'Senior Software Engineer'
        assert normalized['company'] == 'Tech Corp'
        assert normalized['location'] == 'Bangalore'
        assert normalized['source_url'] == 'https://www.naukri.com/job-listings-123'
        assert normalized['source_platform'] == 'naukri'
        assert normalized['source_type'] == SourceType.AGGREGATED
        assert normalized['job_type'] == JobType.FULL_TIME
        assert normalized['experience_level'] == ExperienceLevel.SENIOR
        assert normalized['salary_currency'] == 'INR'
        assert normalized['remote'] is False
        assert 'Python, Django, PostgreSQL' in normalized['requirements']
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_naukri_scraper_normalize_job_remote(self, mock_redis_client):
        """Test normalization of remote Naukri job."""
        scraper = NaukriScraper(
            search_url="https://www.naukri.com/software-engineer-jobs",
            rate_limit=5
        )
        
        raw_data = {
            'title': 'Remote Software Engineer',
            'company': 'Remote Corp',
            'location': 'Remote',
            'experience': '3-5 years',
            'salary': '10-15 Lacs PA',
            'description': 'Work from anywhere',
            'skills': [],
            'job_type': 'Full-Time',
            'posted': 'Just now',
            'url': 'https://www.naukri.com/job-listings-789',
        }
        
        normalized = scraper.normalize_job(raw_data)
        
        assert normalized['remote'] is True
        assert normalized['location'] == 'Remote'
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_naukri_scraper_normalize_job_entry_level(self, mock_redis_client):
        """Test normalization of entry level Naukri job."""
        scraper = NaukriScraper(
            search_url="https://www.naukri.com/software-engineer-jobs",
            rate_limit=5
        )
        
        raw_data = {
            'title': 'Junior Developer',
            'company': 'Startup Inc',
            'location': 'Pune',
            'experience': '0-2 years',
            'salary': '3-6 Lacs PA',
            'description': 'Entry level position for fresh graduates',
            'skills': ['Java', 'Spring'],
            'job_type': 'Full-Time',
            'posted': 'Posted 1 day ago',
            'url': 'https://www.naukri.com/job-listings-111',
        }
        
        normalized = scraper.normalize_job(raw_data)
        
        assert normalized['experience_level'] == ExperienceLevel.ENTRY
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_naukri_scraper_normalize_job_with_salary(self, mock_redis_client):
        """Test normalization of Naukri job with salary."""
        scraper = NaukriScraper(
            search_url="https://www.naukri.com/software-engineer-jobs",
            rate_limit=5
        )
        
        raw_data = {
            'title': 'Software Engineer',
            'company': 'Tech Corp',
            'location': 'Hyderabad',
            'experience': '3-5 years',
            'salary': '12-18 Lacs PA',
            'description': 'Great opportunity',
            'skills': [],
            'job_type': 'Full-Time',
            'posted': 'Posted 3 days ago',
            'url': 'https://www.naukri.com/job-listings-999',
        }
        
        normalized = scraper.normalize_job(raw_data)
        
        # Salary in Lacs (1 Lac = 100,000)
        assert normalized['salary_min'] == 12
        assert normalized['salary_max'] == 18
        assert normalized['salary_currency'] == 'INR'
    
    def test_naukri_scraper_extract_job_urls(self):
        """Test extracting job URLs from search results."""
        from bs4 import BeautifulSoup
        
        scraper = NaukriScraper(
            search_url="https://www.naukri.com/software-engineer-jobs",
            rate_limit=5
        )
        
        html = """
        <html>
            <body>
                <article class="jobTuple">
                    <a class="title" href="/job-listings-senior-software-engineer-123">Job 1</a>
                </article>
                <article class="jobTuple">
                    <a class="title" href="https://www.naukri.com/job-listings-product-manager-456">Job 2</a>
                </article>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        urls = scraper._extract_job_urls(soup)
        
        assert len(urls) == 2
        assert urls[0] == 'https://www.naukri.com/job-listings-senior-software-engineer-123'
        assert urls[1] == 'https://www.naukri.com/job-listings-product-manager-456'
    
    def test_naukri_scraper_parse_job_page(self):
        """Test parsing job details from job page."""
        from bs4 import BeautifulSoup
        
        scraper = NaukriScraper(
            search_url="https://www.naukri.com/software-engineer-jobs",
            rate_limit=5
        )
        
        html = """
        <html>
            <body>
                <h1 class="jd-header-title">Senior Software Engineer</h1>
                <a class="comp-name">Tech Corp</a>
                <span class="loc">Bangalore</span>
                <span class="exp">5-8 years</span>
                <span class="sal">15-20 Lacs PA</span>
                <div class="jd-desc">Build amazing software</div>
                <div class="key-skill">
                    <a>Python</a>
                    <a>Django</a>
                </div>
                <span class="posted">Posted 2 days ago</span>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        job_data = scraper._parse_job_page(soup, 'https://www.naukri.com/job-123')
        
        assert job_data is not None
        assert job_data['title'] == 'Senior Software Engineer'
        assert job_data['company'] == 'Tech Corp'
        assert job_data['location'] == 'Bangalore'
        assert job_data['experience'] == '5-8 years'
        assert job_data['salary'] == '15-20 Lacs PA'
        assert job_data['description'] == 'Build amazing software'
        assert job_data['skills'] == ['Python', 'Django']
        assert job_data['posted'] == 'Posted 2 days ago'
        assert job_data['url'] == 'https://www.naukri.com/job-123'
    
    def test_naukri_scraper_extract_experience_level_entry(self):
        """Test extracting entry level from experience text."""
        scraper = NaukriScraper(
            search_url="https://www.naukri.com/software-engineer-jobs",
            rate_limit=5
        )
        
        assert scraper._extract_experience_level_from_text('0-2 years') == 'Entry Level'
        assert scraper._extract_experience_level_from_text('Fresher') == 'Entry Level'
        assert scraper._extract_experience_level_from_text('1-3 years') == 'Entry Level'
    
    def test_naukri_scraper_extract_experience_level_mid(self):
        """Test extracting mid level from experience text."""
        scraper = NaukriScraper(
            search_url="https://www.naukri.com/software-engineer-jobs",
            rate_limit=5
        )
        
        assert scraper._extract_experience_level_from_text('3-5 years') == 'Mid Level'
        assert scraper._extract_experience_level_from_text('4-7 years') == 'Mid Level'
    
    def test_naukri_scraper_extract_experience_level_senior(self):
        """Test extracting senior level from experience text."""
        scraper = NaukriScraper(
            search_url="https://www.naukri.com/software-engineer-jobs",
            rate_limit=5
        )
        
        assert scraper._extract_experience_level_from_text('5-8 years') == 'Senior'
        assert scraper._extract_experience_level_from_text('6-10 years') == 'Senior'
        assert scraper._extract_experience_level_from_text('Senior level') == 'Senior'
    
    def test_naukri_scraper_extract_experience_level_lead(self):
        """Test extracting lead level from experience text."""
        scraper = NaukriScraper(
            search_url="https://www.naukri.com/software-engineer-jobs",
            rate_limit=5
        )
        
        assert scraper._extract_experience_level_from_text('8-12 years') == 'Lead'
        assert scraper._extract_experience_level_from_text('10+ years') == 'Lead'
        assert scraper._extract_experience_level_from_text('Manager level') == 'Lead'
    
    def test_naukri_scraper_parse_posted_date_just_now(self):
        """Test parsing 'just now' posted date."""
        scraper = NaukriScraper(
            search_url="https://www.naukri.com/software-engineer-jobs",
            rate_limit=5
        )
        
        result = scraper._parse_posted_date('Just now')
        
        # Should be very recent (within last minute)
        assert (datetime.utcnow() - result).total_seconds() < 60
    
    def test_naukri_scraper_parse_posted_date_days_ago(self):
        """Test parsing 'X days ago' posted date."""
        scraper = NaukriScraper(
            search_url="https://www.naukri.com/software-engineer-jobs",
            rate_limit=5
        )
        
        result = scraper._parse_posted_date('Posted 3 days ago')
        
        # Should be approximately 3 days ago
        days_diff = (datetime.utcnow() - result).days
        assert days_diff == 3
    
    def test_naukri_scraper_parse_posted_date_hours_ago(self):
        """Test parsing 'X hours ago' posted date."""
        scraper = NaukriScraper(
            search_url="https://www.naukri.com/software-engineer-jobs",
            rate_limit=5
        )
        
        result = scraper._parse_posted_date('Posted 5 hours ago')
        
        # Should be approximately 5 hours ago
        hours_diff = (datetime.utcnow() - result).total_seconds() / 3600
        assert 4.5 <= hours_diff <= 5.5
    
    def test_naukri_scraper_parse_posted_date_weeks_ago(self):
        """Test parsing 'X weeks ago' posted date."""
        scraper = NaukriScraper(
            search_url="https://www.naukri.com/software-engineer-jobs",
            rate_limit=5
        )
        
        result = scraper._parse_posted_date('Posted 2 weeks ago')
        
        # Should be approximately 14 days ago
        days_diff = (datetime.utcnow() - result).days
        assert 13 <= days_diff <= 15



class TestMonsterScraper:
    """Tests for Monster web scraper."""
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_monster_scraper_initialization(self, mock_redis_client):
        """Test Monster scraper initialization."""
        scraper = MonsterScraper(
            search_url="https://www.monster.com/jobs/search/?q=software-engineer",
            rate_limit=5
        )
        
        assert scraper.source_name == "monster"
        assert scraper.search_url == "https://www.monster.com/jobs/search/?q=software-engineer"
        assert scraper.rate_limit == 5
        assert scraper.base_url == "https://www.monster.com"
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    @patch('app.services.scraping.requests.get')
    async def test_monster_scraper_scrape_success(self, mock_get, mock_redis_client):
        """Test successful scraping of Monster search results."""
        # Mock search results page
        search_html = """
        <html>
            <body>
                <div class="job-card">
                    <h2 class="title"><a href="/job-openings/senior-software-engineer-123">Senior Software Engineer</a></h2>
                </div>
                <div class="job-card">
                    <h2 class="title"><a href="/job-openings/product-manager-456">Product Manager</a></h2>
                </div>
            </body>
        </html>
        """
        
        # Mock job page 1
        job_html_1 = """
        <html>
            <body>
                <h1 class="job-title">Senior Software Engineer</h1>
                <span class="company">Tech Corp</span>
                <span class="location">San Francisco, CA</span>
                <span class="job-type">Full-Time</span>
                <span class="salary">$120,000 - $150,000</span>
                <div class="job-description">Build amazing software products with cutting-edge technologies. 5+ years experience required.</div>
                <div class="requirements">Bachelor's degree in Computer Science. Strong Python skills.</div>
                <span class="posted-date">Posted 2 days ago</span>
            </body>
        </html>
        """
        
        # Mock job page 2
        job_html_2 = """
        <html>
            <body>
                <h1 class="job-title">Product Manager</h1>
                <span class="company">Startup Inc</span>
                <span class="location">New York, NY</span>
                <span class="job-type">Full-Time</span>
                <span class="salary">$100,000 - $130,000</span>
                <div class="job-description">Lead product development and strategy</div>
                <span class="posted-date">Posted 1 day ago</span>
            </body>
        </html>
        """
        
        # Mock Redis for rate limiting
        mock_redis = Mock()
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        mock_redis_client.get_cache_client.return_value = mock_redis
        
        # Mock HTTP responses
        mock_search_response = Mock()
        mock_search_response.content = search_html.encode('utf-8')
        mock_search_response.raise_for_status = Mock()
        
        mock_job_response_1 = Mock()
        mock_job_response_1.content = job_html_1.encode('utf-8')
        mock_job_response_1.raise_for_status = Mock()
        
        mock_job_response_2 = Mock()
        mock_job_response_2.content = job_html_2.encode('utf-8')
        mock_job_response_2.raise_for_status = Mock()
        
        mock_get.side_effect = [mock_search_response, mock_job_response_1, mock_job_response_2]
        
        scraper = MonsterScraper(
            search_url="https://www.monster.com/jobs/search/?q=software-engineer",
            rate_limit=5
        )
        
        jobs = await scraper.scrape()
        
        assert len(jobs) == 2
        assert jobs[0]['title'] == 'Senior Software Engineer'
        assert jobs[0]['company'] == 'Tech Corp'
        assert jobs[0]['location'] == 'San Francisco, CA'
        assert jobs[1]['title'] == 'Product Manager'
        assert jobs[1]['company'] == 'Startup Inc'
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    @patch('app.services.scraping.requests.get')
    async def test_monster_scraper_scrape_no_jobs(self, mock_get, mock_redis_client):
        """Test scraping when no jobs are found."""
        # Mock empty search results
        search_html = """
        <html>
            <body>
                <div>No jobs found</div>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.content = search_html.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        scraper = MonsterScraper(
            search_url="https://www.monster.com/jobs/search/?q=software-engineer",
            rate_limit=5
        )
        
        jobs = await scraper.scrape()
        
        assert len(jobs) == 0
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    @patch('app.services.scraping.requests.get')
    async def test_monster_scraper_scrape_request_error(self, mock_get, mock_redis_client):
        """Test scraping failure due to request error."""
        mock_get.side_effect = Exception("Connection timeout")
        
        scraper = MonsterScraper(
            search_url="https://www.monster.com/jobs/search/?q=software-engineer",
            rate_limit=5
        )
        
        with pytest.raises(ScrapingError) as exc_info:
            await scraper.scrape()
        
        assert "Failed to parse Monster search results" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_monster_scraper_normalize_job(self, mock_redis_client):
        """Test normalization of Monster job data."""
        scraper = MonsterScraper(
            search_url="https://www.monster.com/jobs/search/?q=software-engineer",
            rate_limit=5
        )
        
        raw_data = {
            'title': 'Senior Software Engineer',
            'company': 'Tech Corp',
            'location': 'San Francisco, CA',
            'job_type': 'Full-Time',
            'salary': '$120,000 - $150,000',
            'description': 'Build amazing software products with cutting-edge technologies. 5+ years experience required.',
            'requirements': 'Bachelor\'s degree in Computer Science. Strong Python skills.',
            'posted': 'Posted 2 days ago',
            'url': 'https://www.monster.com/job-openings/senior-software-engineer-123',
        }
        
        normalized = scraper.normalize_job(raw_data)
        
        assert normalized['title'] == 'Senior Software Engineer'
        assert normalized['company'] == 'Tech Corp'
        assert normalized['location'] == 'San Francisco, CA'
        assert normalized['source_url'] == 'https://www.monster.com/job-openings/senior-software-engineer-123'
        assert normalized['source_platform'] == 'monster'
        assert normalized['source_type'] == SourceType.AGGREGATED
        assert normalized['job_type'] == JobType.FULL_TIME
        assert normalized['experience_level'] == ExperienceLevel.SENIOR
        assert normalized['salary_min'] == 120000
        assert normalized['salary_max'] == 150000
        assert normalized['salary_currency'] == 'USD'
        assert normalized['remote'] is False
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_monster_scraper_normalize_job_remote(self, mock_redis_client):
        """Test normalization of remote Monster job."""
        scraper = MonsterScraper(
            search_url="https://www.monster.com/jobs/search/?q=software-engineer",
            rate_limit=5
        )
        
        raw_data = {
            'title': 'Remote Software Engineer',
            'company': 'Remote Corp',
            'location': 'Remote',
            'job_type': 'Full-Time',
            'salary': '$100,000 - $130,000',
            'description': 'Work from anywhere. Remote position available.',
            'requirements': '',
            'posted': 'Just posted',
            'url': 'https://www.monster.com/job-openings/remote-software-engineer-789',
        }
        
        normalized = scraper.normalize_job(raw_data)
        
        assert normalized['remote'] is True
        assert normalized['location'] == 'Remote'
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_monster_scraper_normalize_job_entry_level(self, mock_redis_client):
        """Test normalization of entry level Monster job."""
        scraper = MonsterScraper(
            search_url="https://www.monster.com/jobs/search/?q=software-engineer",
            rate_limit=5
        )
        
        raw_data = {
            'title': 'Junior Developer',
            'company': 'Startup Inc',
            'location': 'Boston, MA',
            'job_type': 'Full-Time',
            'salary': '$60,000 - $80,000',
            'description': 'Entry level position for fresh graduates. 0-2 years experience.',
            'requirements': 'Bachelor\'s degree required',
            'posted': 'Posted 1 day ago',
            'url': 'https://www.monster.com/job-openings/junior-developer-111',
        }
        
        normalized = scraper.normalize_job(raw_data)
        
        assert normalized['experience_level'] == ExperienceLevel.ENTRY
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_monster_scraper_normalize_job_part_time(self, mock_redis_client):
        """Test normalization of part-time Monster job."""
        scraper = MonsterScraper(
            search_url="https://www.monster.com/jobs/search/?q=software-engineer",
            rate_limit=5
        )
        
        raw_data = {
            'title': 'Part-Time Developer',
            'company': 'Tech Startup',
            'location': 'Seattle, WA',
            'job_type': 'Part-Time',
            'salary': '$40,000 - $60,000',
            'description': 'Part-time position available. Flexible hours.',
            'requirements': '',
            'posted': 'Posted 3 days ago',
            'url': 'https://www.monster.com/job-openings/part-time-developer-222',
        }
        
        normalized = scraper.normalize_job(raw_data)
        
        assert normalized['job_type'] == JobType.PART_TIME
    
    @pytest.mark.asyncio
    @patch('app.services.scraping.redis_client')
    async def test_monster_scraper_normalize_job_lead_level(self, mock_redis_client):
        """Test normalization of lead level Monster job."""
        scraper = MonsterScraper(
            search_url="https://www.monster.com/jobs/search/?q=software-engineer",
            rate_limit=5
        )
        
        raw_data = {
            'title': 'Engineering Manager',
            'company': 'Big Tech',
            'location': 'Austin, TX',
            'job_type': 'Full-Time',
            'salary': '$150,000 - $200,000',
            'description': 'Lead a team of engineers. 8+ years experience required.',
            'requirements': 'Strong leadership skills',
            'posted': 'Posted 5 days ago',
            'url': 'https://www.monster.com/job-openings/engineering-manager-333',
        }
        
        normalized = scraper.normalize_job(raw_data)
        
        assert normalized['experience_level'] == ExperienceLevel.LEAD
    
    def test_monster_scraper_extract_job_urls(self):
        """Test extracting job URLs from search results."""
        from bs4 import BeautifulSoup
        
        scraper = MonsterScraper(
            search_url="https://www.monster.com/jobs/search/?q=software-engineer",
            rate_limit=5
        )
        
        html = """
        <html>
            <body>
                <div class="job-card">
                    <h2 class="title"><a href="/job-openings/senior-software-engineer-123">Senior Software Engineer</a></h2>
                </div>
                <div class="job-card">
                    <h2 class="title"><a href="/job-openings/product-manager-456">Product Manager</a></h2>
                </div>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        job_urls = scraper._extract_job_urls(soup)
        
        assert len(job_urls) == 2
        assert job_urls[0] == 'https://www.monster.com/job-openings/senior-software-engineer-123'
        assert job_urls[1] == 'https://www.monster.com/job-openings/product-manager-456'
    
    def test_monster_scraper_extract_experience_level_from_text_senior(self):
        """Test extracting senior experience level from text."""
        scraper = MonsterScraper(
            search_url="https://www.monster.com/jobs/search/?q=software-engineer",
            rate_limit=5
        )
        
        text = "We are looking for a senior engineer with 5+ years of experience"
        assert scraper._extract_experience_level_from_text(text) == 'Senior'
        
        text = "Principal developer needed for this role"
        assert scraper._extract_experience_level_from_text(text) == 'Senior'
    
    def test_monster_scraper_extract_experience_level_from_text_entry(self):
        """Test extracting entry experience level from text."""
        scraper = MonsterScraper(
            search_url="https://www.monster.com/jobs/search/?q=software-engineer",
            rate_limit=5
        )
        
        text = "Entry-level position for fresh graduates"
        assert scraper._extract_experience_level_from_text(text) == 'Entry Level'
        
        text = "Junior developer with 0-2 years of experience"
        assert scraper._extract_experience_level_from_text(text) == 'Entry Level'
    
    def test_monster_scraper_extract_experience_level_from_text_lead(self):
        """Test extracting lead experience level from text."""
        scraper = MonsterScraper(
            search_url="https://www.monster.com/jobs/search/?q=software-engineer",
            rate_limit=5
        )
        
        text = "Lead engineer position with team management responsibilities"
        assert scraper._extract_experience_level_from_text(text) == 'Lead'
        
        text = "Engineering manager role with 8+ years experience"
        assert scraper._extract_experience_level_from_text(text) == 'Lead'
    
    def test_monster_scraper_extract_experience_level_from_text_years(self):
        """Test extracting experience level based on years."""
        scraper = MonsterScraper(
            search_url="https://www.monster.com/jobs/search/?q=software-engineer",
            rate_limit=5
        )
        
        text = "Looking for candidate with 1 year of experience"
        assert scraper._extract_experience_level_from_text(text) == 'Entry Level'
        
        text = "3 years of experience required"
        assert scraper._extract_experience_level_from_text(text) == 'Mid Level'
        
        text = "6 years experience in software development"
        assert scraper._extract_experience_level_from_text(text) == 'Senior'
        
        text = "10+ years of experience needed"
        assert scraper._extract_experience_level_from_text(text) == 'Lead'
    
    def test_monster_scraper_extract_experience_level_from_text_default(self):
        """Test extracting default experience level from text."""
        scraper = MonsterScraper(
            search_url="https://www.monster.com/jobs/search/?q=software-engineer",
            rate_limit=5
        )
        
        text = "Software engineer position available"
        assert scraper._extract_experience_level_from_text(text) == 'Mid Level'
        
        text = ""
        assert scraper._extract_experience_level_from_text(text) == 'Mid Level'
    
    def test_monster_scraper_parse_posted_date_just_posted(self):
        """Test parsing posted date from 'just posted' text."""
        scraper = MonsterScraper(
            search_url="https://www.monster.com/jobs/search/?q=software-engineer",
            rate_limit=5
        )
        
        result = scraper._parse_posted_date("Just posted")
        
        # Should be very recent (within last minute)
        assert (datetime.utcnow() - result).total_seconds() < 60
    
    def test_monster_scraper_parse_posted_date_days_ago(self):
        """Test parsing posted date from days ago text."""
        scraper = MonsterScraper(
            search_url="https://www.monster.com/jobs/search/?q=software-engineer",
            rate_limit=5
        )
        
        result = scraper._parse_posted_date("Posted 3 days ago")
        
        # Should be approximately 3 days ago
        days_diff = (datetime.utcnow() - result).days
        assert days_diff == 3
    
    def test_monster_scraper_parse_posted_date_hours_ago(self):
        """Test parsing posted date from hours ago text."""
        scraper = MonsterScraper(
            search_url="https://www.monster.com/jobs/search/?q=software-engineer",
            rate_limit=5
        )
        
        result = scraper._parse_posted_date("5 hours ago")
        
        # Should be approximately 5 hours ago
        hours_diff = (datetime.utcnow() - result).total_seconds() / 3600
        assert 4.5 <= hours_diff <= 5.5
    
    def test_monster_scraper_parse_posted_date_weeks_ago(self):
        """Test parsing posted date from weeks ago text."""
        scraper = MonsterScraper(
            search_url="https://www.monster.com/jobs/search/?q=software-engineer",
            rate_limit=5
        )
        
        result = scraper._parse_posted_date("2 weeks ago")
        
        # Should be approximately 14 days ago
        days_diff = (datetime.utcnow() - result).days
        assert 13 <= days_diff <= 15
    
    def test_monster_scraper_parse_posted_date_invalid(self):
        """Test parsing posted date with invalid input."""
        scraper = MonsterScraper(
            search_url="https://www.monster.com/jobs/search/?q=software-engineer",
            rate_limit=5
        )
        
        result = scraper._parse_posted_date("invalid date")
        
        # Should default to current time
        assert (datetime.utcnow() - result).total_seconds() < 60
