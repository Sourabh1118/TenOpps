"""
Unit tests for Celery configuration and tasks.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.tasks.celery_app import celery_app, debug_task, get_celery_app
from app.tasks.scraping_tasks import (
    scrape_linkedin_jobs,
    scrape_indeed_jobs,
    scrape_naukri_jobs,
    scrape_monster_jobs,
    import_job_from_url,
)
from app.tasks.maintenance_tasks import (
    expire_old_jobs,
    reset_monthly_quotas,
    remove_expired_featured_listings,
    update_quality_scores,
)


class TestCeleryConfiguration:
    """Test Celery app configuration."""
    
    def test_celery_app_exists(self):
        """Test that Celery app is initialized."""
        assert celery_app is not None
        assert celery_app.main == "job_aggregation_platform"
    
    def test_get_celery_app(self):
        """Test get_celery_app function."""
        app = get_celery_app()
        assert app is celery_app
    
    def test_broker_configured(self):
        """Test that broker URL is configured."""
        assert celery_app.conf.broker_url is not None
        assert "redis://" in celery_app.conf.broker_url
    
    def test_result_backend_configured(self):
        """Test that result backend is configured."""
        assert celery_app.conf.result_backend is not None
        assert "redis://" in celery_app.conf.result_backend
    
    def test_task_serializer(self):
        """Test that task serializer is JSON."""
        assert celery_app.conf.task_serializer == "json"
        assert "json" in celery_app.conf.accept_content
        assert celery_app.conf.result_serializer == "json"
    
    def test_timezone_configured(self):
        """Test that timezone is UTC."""
        assert celery_app.conf.timezone == "UTC"
        assert celery_app.conf.enable_utc is True
    
    def test_worker_settings(self):
        """Test worker configuration."""
        assert celery_app.conf.worker_prefetch_multiplier == 4
        assert celery_app.conf.worker_max_tasks_per_child == 1000
        assert celery_app.conf.worker_disable_rate_limits is False
    
    def test_task_queues_configured(self):
        """Test that task queues are configured."""
        queues = celery_app.conf.task_queues
        assert len(queues) == 3
        
        queue_names = [q.name for q in queues]
        assert "high_priority" in queue_names
        assert "default" in queue_names
        assert "low_priority" in queue_names
    
    def test_task_routes_configured(self):
        """Test that task routes are configured."""
        routes = celery_app.conf.task_routes
        assert len(routes) > 0
        
        # Check high priority routing
        assert "app.tasks.scraping_tasks.import_job_from_url" in routes
        assert routes["app.tasks.scraping_tasks.import_job_from_url"]["queue"] == "high_priority"
        assert routes["app.tasks.scraping_tasks.import_job_from_url"]["priority"] == 9
        
        # Check default priority routing
        assert "app.tasks.scraping_tasks.scrape_linkedin_jobs" in routes
        assert routes["app.tasks.scraping_tasks.scrape_linkedin_jobs"]["queue"] == "default"
        
        # Check low priority routing
        assert "app.tasks.maintenance_tasks.expire_old_jobs" in routes
        assert routes["app.tasks.maintenance_tasks.expire_old_jobs"]["queue"] == "low_priority"
    
    def test_beat_schedule_configured(self):
        """Test that Beat schedule is configured."""
        schedule = celery_app.conf.beat_schedule
        assert len(schedule) == 8
        
        # Check scraping tasks
        assert "scrape-linkedin-every-6-hours" in schedule
        assert "scrape-indeed-every-6-hours" in schedule
        assert "scrape-naukri-every-6-hours" in schedule
        assert "scrape-monster-every-6-hours" in schedule
        
        # Check maintenance tasks
        assert "expire-old-jobs-daily" in schedule
        assert "reset-monthly-quotas-daily" in schedule
        assert "remove-expired-featured-daily" in schedule
        assert "update-quality-scores-daily" in schedule
    
    def test_retry_configuration(self):
        """Test retry configuration."""
        assert celery_app.conf.task_acks_late is True
        assert celery_app.conf.task_reject_on_worker_lost is True
        assert celery_app.conf.task_track_started is True
        assert celery_app.conf.task_retry_backoff is True
        assert celery_app.conf.task_retry_backoff_max == 600
        assert celery_app.conf.task_retry_jitter is True


class TestDebugTask:
    """Test debug task."""
    
    def test_debug_task_registered(self):
        """Test that debug task is registered."""
        assert "app.tasks.celery_app.debug_task" in celery_app.tasks
    
    @patch('app.tasks.celery_app.logger')
    def test_debug_task_execution(self, mock_logger):
        """Test debug task execution."""
        # Create a mock request
        mock_request = MagicMock()
        debug_task.request = mock_request
        
        result = debug_task()
        
        assert result["status"] == "success"
        assert result["message"] == "Celery is working!"
        mock_logger.info.assert_called()


class TestScrapingTasks:
    """Test scraping tasks."""
    
    def test_scraping_tasks_registered(self):
        """Test that scraping tasks are registered."""
        assert "app.tasks.scraping_tasks.scrape_linkedin_jobs" in celery_app.tasks
        assert "app.tasks.scraping_tasks.scrape_indeed_jobs" in celery_app.tasks
        assert "app.tasks.scraping_tasks.scrape_naukri_jobs" in celery_app.tasks
        assert "app.tasks.scraping_tasks.scrape_monster_jobs" in celery_app.tasks
        assert "app.tasks.scraping_tasks.import_job_from_url" in celery_app.tasks
    
    @patch('app.tasks.scraping_tasks.logger')
    def test_scrape_linkedin_jobs(self, mock_logger):
        """Test LinkedIn scraping task."""
        result = scrape_linkedin_jobs()
        
        assert result["status"] == "success"
        assert result["source"] == "linkedin"
        assert "jobs_found" in result
        assert "jobs_created" in result
        assert "jobs_updated" in result
        mock_logger.info.assert_called()
    
    @patch('app.tasks.scraping_tasks.logger')
    def test_scrape_indeed_jobs(self, mock_logger):
        """Test Indeed scraping task."""
        result = scrape_indeed_jobs()
        
        assert result["status"] == "success"
        assert result["source"] == "indeed"
        mock_logger.info.assert_called()
    
    @patch('app.tasks.scraping_tasks.logger')
    def test_scrape_naukri_jobs(self, mock_logger):
        """Test Naukri scraping task."""
        result = scrape_naukri_jobs()
        
        assert result["status"] == "success"
        assert result["source"] == "naukri"
        mock_logger.info.assert_called()
    
    @patch('app.tasks.scraping_tasks.logger')
    def test_scrape_monster_jobs(self, mock_logger):
        """Test Monster scraping task."""
        result = scrape_monster_jobs()
        
        assert result["status"] == "success"
        assert result["source"] == "monster"
        mock_logger.info.assert_called()
    
    @patch('app.tasks.scraping_tasks.logger')
    def test_import_job_from_url(self, mock_logger):
        """Test URL import task."""
        employer_id = "test-employer-123"
        url = "https://example.com/job/123"
        
        result = import_job_from_url(employer_id, url)
        
        assert result["status"] == "success"
        assert result["employer_id"] == employer_id
        assert result["url"] == url
        mock_logger.info.assert_called()


class TestMaintenanceTasks:
    """Test maintenance tasks."""
    
    def test_maintenance_tasks_registered(self):
        """Test that maintenance tasks are registered."""
        assert "app.tasks.maintenance_tasks.expire_old_jobs" in celery_app.tasks
        assert "app.tasks.maintenance_tasks.reset_monthly_quotas" in celery_app.tasks
        assert "app.tasks.maintenance_tasks.remove_expired_featured_listings" in celery_app.tasks
        assert "app.tasks.maintenance_tasks.update_quality_scores" in celery_app.tasks
    
    @patch('app.tasks.maintenance_tasks.logger')
    def test_expire_old_jobs(self, mock_logger):
        """Test job expiration task."""
        result = expire_old_jobs()
        
        assert result["status"] == "success"
        assert "jobs_expired" in result
        mock_logger.info.assert_called()
    
    @patch('app.tasks.maintenance_tasks.logger')
    def test_reset_monthly_quotas(self, mock_logger):
        """Test quota reset task."""
        result = reset_monthly_quotas()
        
        assert result["status"] == "success"
        assert "quotas_reset" in result
        mock_logger.info.assert_called()
    
    @patch('app.tasks.maintenance_tasks.logger')
    def test_remove_expired_featured_listings(self, mock_logger):
        """Test featured listing expiration task."""
        result = remove_expired_featured_listings()
        
        assert result["status"] == "success"
        assert "featured_removed" in result
        mock_logger.info.assert_called()
    
    @patch('app.tasks.maintenance_tasks.logger')
    def test_update_quality_scores(self, mock_logger):
        """Test quality score update task."""
        result = update_quality_scores()
        
        assert result["status"] == "success"
        assert "scores_updated" in result
        mock_logger.info.assert_called()


class TestTaskRetry:
    """Test task retry behavior."""
    
    @patch('app.tasks.scraping_tasks.logger')
    def test_scraping_task_retry_on_exception(self, mock_logger):
        """Test that scraping tasks retry on exception."""
        # Get task instance
        task = scrape_linkedin_jobs
        
        # Check retry configuration
        assert task.autoretry_for == (Exception,)
        assert task.retry_kwargs["max_retries"] == 3
        assert task.retry_backoff is True
    
    @patch('app.tasks.maintenance_tasks.logger')
    def test_maintenance_task_retry_on_exception(self, mock_logger):
        """Test that maintenance tasks retry on exception."""
        # Get task instance
        task = expire_old_jobs
        
        # Check retry configuration
        assert task.autoretry_for == (Exception,)
        assert task.retry_kwargs["max_retries"] == 2
        assert task.retry_backoff is True


class TestTaskPriority:
    """Test task priority configuration."""
    
    def test_high_priority_tasks(self):
        """Test that URL import is high priority."""
        routes = celery_app.conf.task_routes
        url_import_route = routes["app.tasks.scraping_tasks.import_job_from_url"]
        
        assert url_import_route["queue"] == "high_priority"
        assert url_import_route["priority"] == 9
    
    def test_default_priority_tasks(self):
        """Test that scraping tasks are default priority."""
        routes = celery_app.conf.task_routes
        
        for task_name in [
            "app.tasks.scraping_tasks.scrape_linkedin_jobs",
            "app.tasks.scraping_tasks.scrape_indeed_jobs",
            "app.tasks.scraping_tasks.scrape_naukri_jobs",
            "app.tasks.scraping_tasks.scrape_monster_jobs",
        ]:
            assert routes[task_name]["queue"] == "default"
            assert routes[task_name]["priority"] == 5
    
    def test_low_priority_tasks(self):
        """Test that maintenance tasks are low priority."""
        routes = celery_app.conf.task_routes
        
        for task_name in [
            "app.tasks.maintenance_tasks.expire_old_jobs",
            "app.tasks.maintenance_tasks.reset_monthly_quotas",
            "app.tasks.maintenance_tasks.remove_expired_featured_listings",
            "app.tasks.maintenance_tasks.update_quality_scores",
        ]:
            assert routes[task_name]["queue"] == "low_priority"
            assert routes[task_name]["priority"] == 1
