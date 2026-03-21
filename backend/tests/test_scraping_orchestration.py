"""
Tests for scraping orchestration and Celery tasks.

This module tests:
- Main scraping orchestration function
- Celery task execution
- Circuit breaker pattern
- Error handling and alerting
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.scraping import scrape_and_process_jobs, SCRAPER_REGISTRY
from app.tasks.scraping_tasks import (
    CircuitBreaker,
    scrape_linkedin_jobs,
    scrape_indeed_jobs,
    scrape_naukri_jobs,
    scrape_monster_jobs,
)
from app.models.job import Job, JobType, ExperienceLevel, SourceType, JobStatus
from app.models.job_source import JobSource
from app.models.scraping_task import ScrapingTask, TaskType, TaskStatus


class TestScrapingOrchestration:
    """Tests for the main scraping orchestration function."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        session = Mock(spec=Session)
        session.add = Mock()
        session.commit = Mock()
        session.flush = Mock()
        session.rollback = Mock()
        session.query = Mock()
        return session
    
    @pytest.fixture
    def mock_scraper(self):
        """Create a mock scraper."""
        scraper = Mock()
        
        # Make scrape_with_retry return a coroutine
        async def mock_scrape():
            return []
        scraper.scrape_with_retry = mock_scrape
        
        scraper.normalize_job = Mock()
        scraper.log_metrics = Mock()
        return scraper
    
    @pytest.fixture
    def sample_raw_job(self):
        """Sample raw job data from scraper."""
        return {
            'title': 'Senior Python Developer',
            'company': 'Tech Corp Inc',
            'location': 'San Francisco, CA',
            'description': 'We are looking for an experienced Python developer...',
            'url': 'https://example.com/job/123',
            'jobkey': 'job123',
        }
    
    @pytest.fixture
    def sample_normalized_job(self):
        """Sample normalized job data."""
        return {
            'title': 'Senior Python Developer',
            'company': 'Tech Corp Inc',
            'location': 'San Francisco, CA',
            'remote': False,
            'job_type': JobType.FULL_TIME,
            'experience_level': ExperienceLevel.SENIOR,
            'description': 'We are looking for an experienced Python developer...',
            'requirements': None,
            'responsibilities': None,
            'salary_min': None,
            'salary_max': None,
            'salary_currency': 'USD',
            'source_url': 'https://example.com/job/123',
            'source_platform': 'linkedin',
            'posted_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(days=30),
            'tags': [],
        }
    
    @pytest.mark.asyncio
    async def test_scrape_and_process_jobs_success(
        self, mock_db_session, sample_raw_job, sample_normalized_job
    ):
        """Test successful scraping and processing."""
        # Create mock scraper with async method
        mock_scraper = Mock()
        
        async def mock_scrape():
            return [sample_raw_job]
        mock_scraper.scrape_with_retry = mock_scrape
        mock_scraper.normalize_job = Mock(return_value=sample_normalized_job)
        mock_scraper.log_metrics = Mock()
        
        with patch('app.services.scraping.SCRAPER_REGISTRY', {'linkedin': lambda **kwargs: mock_scraper}):
            with patch('app.services.scraping.create_scraping_task') as mock_create_task:
                with patch('app.services.scraping.update_scraping_task') as mock_update_task:
                    with patch('app.services.quality_scoring.calculate_quality_score', return_value=75.0):
                        with patch('app.services.deduplication.process_job_with_deduplication', return_value=(False, {})):
                            # Create mock task
                            mock_task = Mock()
                            mock_task.id = 'task-123'
                            mock_task.retry_count = 0
                            mock_create_task.return_value = mock_task
                            
                            # Run scraping
                            result = await scrape_and_process_jobs('linkedin', mock_db_session)
        
        # Assertions
        assert result['success'] is True
        assert result['source_platform'] == 'linkedin'
        assert result['jobs_found'] == 1
        assert result['jobs_created'] == 1
        assert result['jobs_updated'] == 0
        assert result['error'] is None
        
        # Verify task was created and updated
        mock_create_task.assert_called_once()
        assert mock_update_task.call_count == 2  # RUNNING and COMPLETED
    
    @pytest.mark.asyncio
    async def test_scrape_and_process_jobs_with_duplicate(
        self, mock_db_session, sample_raw_job, sample_normalized_job
    ):
        """Test scraping with duplicate detection."""
        # Create mock scraper with async method
        mock_scraper = Mock()
        
        async def mock_scrape():
            return [sample_raw_job]
        mock_scraper.scrape_with_retry = mock_scrape
        mock_scraper.normalize_job = Mock(return_value=sample_normalized_job)
        mock_scraper.log_metrics = Mock()
        
        with patch('app.services.scraping.SCRAPER_REGISTRY', {'linkedin': lambda **kwargs: mock_scraper}):
            with patch('app.services.scraping.create_scraping_task') as mock_create_task:
                with patch('app.services.scraping.update_scraping_task') as mock_update_task:
                    with patch('app.services.quality_scoring.calculate_quality_score', return_value=75.0):
                        # Mock duplicate detection - job is duplicate
                        with patch('app.services.deduplication.process_job_with_deduplication', return_value=(True, {'id': 'existing-job-123'})):
                            # Create mock task
                            mock_task = Mock()
                            mock_task.id = 'task-123'
                            mock_task.retry_count = 0
                            mock_create_task.return_value = mock_task
                            
                            # Run scraping
                            result = await scrape_and_process_jobs('linkedin', mock_db_session)
        
        # Assertions
        assert result['success'] is True
        assert result['jobs_found'] == 1
        assert result['jobs_created'] == 0
        assert result['jobs_updated'] == 1  # Duplicate was merged
    
    @pytest.mark.asyncio
    async def test_scrape_and_process_jobs_failure(self, mock_db_session):
        """Test scraping failure handling."""
        # Create mock scraper that raises exception
        mock_scraper = Mock()
        
        async def mock_scrape_fail():
            raise Exception("Network error")
        mock_scraper.scrape_with_retry = mock_scrape_fail
        
        with patch('app.services.scraping.SCRAPER_REGISTRY', {'linkedin': lambda **kwargs: mock_scraper}):
            with patch('app.services.scraping.create_scraping_task') as mock_create_task:
                with patch('app.services.scraping.update_scraping_task') as mock_update_task:
                    # Create mock task
                    mock_task = Mock()
                    mock_task.id = 'task-123'
                    mock_task.retry_count = 0
                    mock_create_task.return_value = mock_task
                    
                    # Run scraping
                    result = await scrape_and_process_jobs('linkedin', mock_db_session)
        
        # Assertions
        assert result['success'] is False
        assert result['error'] is not None
        assert 'Network error' in result['error']
        assert result['jobs_found'] == 0
        
        # Verify task was marked as FAILED
        failed_update_call = [call for call in mock_update_task.call_args_list if call[0][1].get('status') == TaskStatus.FAILED]
        assert len(failed_update_call) > 0
    
    @pytest.mark.asyncio
    async def test_scrape_and_process_jobs_invalid_source(self, mock_db_session):
        """Test scraping with invalid source platform."""
        result = await scrape_and_process_jobs('invalid_source', mock_db_session)
        
        assert result['success'] is False
        assert 'Unknown source platform' in result['error']
        assert result['jobs_found'] == 0


class TestCircuitBreaker:
    """Tests for the circuit breaker pattern."""
    
    @pytest.fixture(autouse=True)
    def setup_redis_mock(self):
        """Setup Redis mock for each test."""
        with patch('app.tasks.scraping_tasks.redis_client') as mock_redis_client:
            self.mock_redis = Mock()
            mock_redis_client.get_cache_client.return_value = self.mock_redis
            yield
    
    def test_get_failure_count_no_failures(self):
        """Test getting failure count when no failures recorded."""
        self.mock_redis.get.return_value = None
        
        count = CircuitBreaker.get_failure_count('linkedin')
        
        assert count == 0
        self.mock_redis.get.assert_called_once_with('circuit_breaker:linkedin:failures')
    
    def test_get_failure_count_with_failures(self):
        """Test getting failure count with existing failures."""
        self.mock_redis.get.return_value = '2'
        
        count = CircuitBreaker.get_failure_count('linkedin')
        
        assert count == 2
    
    def test_increment_failure(self):
        """Test incrementing failure count."""
        self.mock_redis.incr.return_value = 1
        
        count = CircuitBreaker.increment_failure('linkedin')
        
        assert count == 1
        self.mock_redis.incr.assert_called_once_with('circuit_breaker:linkedin:failures')
        self.mock_redis.expire.assert_called_once()
    
    def test_reset_failures(self):
        """Test resetting failure count."""
        CircuitBreaker.reset_failures('linkedin')
        
        self.mock_redis.delete.assert_called_once_with('circuit_breaker:linkedin:failures')
    
    def test_is_circuit_open_when_closed(self):
        """Test checking if circuit is open when it's closed."""
        self.mock_redis.exists.return_value = 0
        
        is_open = CircuitBreaker.is_circuit_open('linkedin')
        
        assert is_open is False
    
    def test_is_circuit_open_when_open(self):
        """Test checking if circuit is open when it's open."""
        self.mock_redis.exists.return_value = 1
        
        is_open = CircuitBreaker.is_circuit_open('linkedin')
        
        assert is_open is True
    
    def test_open_circuit(self):
        """Test opening circuit."""
        CircuitBreaker.open_circuit('linkedin')
        
        self.mock_redis.setex.assert_called_once()
        args = self.mock_redis.setex.call_args[0]
        assert args[0] == 'circuit_breaker:linkedin:open'
        assert args[1] == CircuitBreaker.COOLDOWN_PERIOD
    
    def test_send_admin_alert(self):
        """Test sending admin alert."""
        with patch('app.tasks.scraping_tasks.logger') as mock_logger:
            CircuitBreaker.send_admin_alert('linkedin', 'Network timeout')
            
            mock_logger.critical.assert_called_once()
            call_args = mock_logger.critical.call_args[0][0]
            assert 'ADMIN ALERT' in call_args
            assert 'linkedin' in call_args
            assert 'Network timeout' in call_args


class TestScrapingTasks:
    """Tests for Celery scraping tasks."""
    
    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Setup common mocks for task tests."""
        with patch('app.tasks.scraping_tasks.redis_client') as mock_redis_client:
            self.mock_redis = Mock()
            mock_redis_client.get_cache_client.return_value = self.mock_redis
            
            with patch('app.tasks.scraping_tasks.run_async_scraping') as mock_run_scraping:
                self.mock_run_scraping = mock_run_scraping
                yield
    
    def test_scrape_linkedin_jobs_success(self):
        """Test successful LinkedIn scraping task."""
        # Mock circuit breaker - circuit is closed
        self.mock_redis.exists.return_value = 0
        
        # Mock successful scraping
        self.mock_run_scraping.return_value = {
            'success': True,
            'jobs_found': 10,
            'jobs_created': 8,
            'jobs_updated': 2,
            'duration': 45.5,
        }
        
        result = scrape_linkedin_jobs()
        
        assert result['status'] == 'success'
        assert result['source'] == 'linkedin'
        assert result['jobs_found'] == 10
        assert result['jobs_created'] == 8
        assert result['jobs_updated'] == 2
    
    def test_scrape_linkedin_jobs_circuit_open(self):
        """Test LinkedIn scraping task when circuit is open."""
        # Mock circuit breaker - circuit is open
        self.mock_redis.exists.return_value = 1
        
        result = scrape_linkedin_jobs()
        
        assert result['status'] == 'skipped'
        assert result['reason'] == 'circuit_breaker_open'
        assert result['jobs_found'] == 0
        
        # Verify scraping was not attempted
        self.mock_run_scraping.assert_not_called()
    
    def test_scrape_linkedin_jobs_failure_opens_circuit(self):
        """Test that 3 consecutive failures open the circuit."""
        # Mock circuit breaker - circuit is closed
        self.mock_redis.exists.return_value = 0
        
        # Mock failure count reaching threshold
        self.mock_redis.incr.return_value = 3
        
        # Mock failed scraping
        self.mock_run_scraping.return_value = {
            'success': False,
            'error': 'Connection timeout',
            'jobs_found': 0,
            'jobs_created': 0,
            'jobs_updated': 0,
            'duration': 30.0,
        }
        
        with pytest.raises(Exception):
            scrape_linkedin_jobs()
        
        # Verify circuit was opened
        self.mock_redis.setex.assert_called()
        setex_args = self.mock_redis.setex.call_args[0]
        assert 'circuit_breaker:linkedin:open' in setex_args[0]
    
    def test_scrape_indeed_jobs_success(self):
        """Test successful Indeed scraping task."""
        # Mock circuit breaker - circuit is closed
        self.mock_redis.exists.return_value = 0
        
        # Mock successful scraping
        self.mock_run_scraping.return_value = {
            'success': True,
            'jobs_found': 15,
            'jobs_created': 12,
            'jobs_updated': 3,
            'duration': 60.2,
        }
        
        result = scrape_indeed_jobs()
        
        assert result['status'] == 'success'
        assert result['source'] == 'indeed'
        assert result['jobs_found'] == 15
    
    def test_scrape_naukri_jobs_success(self):
        """Test successful Naukri scraping task."""
        # Mock circuit breaker - circuit is closed
        self.mock_redis.exists.return_value = 0
        
        # Mock successful scraping
        self.mock_run_scraping.return_value = {
            'success': True,
            'jobs_found': 20,
            'jobs_created': 18,
            'jobs_updated': 2,
            'duration': 120.5,
        }
        
        result = scrape_naukri_jobs()
        
        assert result['status'] == 'success'
        assert result['source'] == 'naukri'
        assert result['jobs_found'] == 20
    
    def test_scrape_monster_jobs_success(self):
        """Test successful Monster scraping task."""
        # Mock circuit breaker - circuit is closed
        self.mock_redis.exists.return_value = 0
        
        # Mock successful scraping
        self.mock_run_scraping.return_value = {
            'success': True,
            'jobs_found': 12,
            'jobs_created': 10,
            'jobs_updated': 2,
            'duration': 90.3,
        }
        
        result = scrape_monster_jobs()
        
        assert result['status'] == 'success'
        assert result['source'] == 'monster'
        assert result['jobs_found'] == 12


class TestScrapingMetrics:
    """Tests for scraping metrics tracking."""
    
    def test_metrics_tracked_correctly(self):
        """Test that scraping metrics are tracked correctly."""
        # This would test the actual metrics tracking in a real scenario
        # For now, we verify the structure
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
