"""
Unit tests for ScrapingTask model.

Tests cover:
- Model creation and field validation
- Enum constraints (TaskType, TaskStatus)
- Check constraints (retry_count, jobs metrics)
- Timestamp tracking
- Helper methods
- Index creation for monitoring queries
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
import uuid

from app.models.scraping_task import ScrapingTask, TaskType, TaskStatus


class TestScrapingTaskModel:
    """Test suite for ScrapingTask model."""

    def test_create_scraping_task_with_required_fields(self, db_session):
        """Test creating a scraping task with all required fields."""
        task = ScrapingTask(
            task_type=TaskType.SCHEDULED_SCRAPE,
            source_platform="LinkedIn",
            status=TaskStatus.PENDING
        )
        db_session.add(task)
        db_session.commit()

        # Verify
        assert task.id is not None
        assert task.task_type == TaskType.SCHEDULED_SCRAPE
        assert task.source_platform == "LinkedIn"
        assert task.status == TaskStatus.PENDING
        assert task.jobs_found == 0
        assert task.jobs_created == 0
        assert task.jobs_updated == 0
        assert task.retry_count == 0
        assert task.created_at is not None

    def test_create_url_import_task(self, db_session):
        """Test creating a URL import task."""
        task = ScrapingTask(
            task_type=TaskType.URL_IMPORT,
            target_url="https://www.linkedin.com/jobs/view/123456",
            status=TaskStatus.PENDING
        )
        db_session.add(task)
        db_session.commit()

        # Verify
        assert task.task_type == TaskType.URL_IMPORT
        assert task.target_url == "https://www.linkedin.com/jobs/view/123456"
        assert task.source_platform is None

    def test_create_manual_scrape_task(self, db_session):
        """Test creating a manual scrape task."""
        task = ScrapingTask(
            task_type=TaskType.MANUAL_SCRAPE,
            source_platform="Indeed",
            status=TaskStatus.RUNNING,
            started_at=datetime.now()
        )
        db_session.add(task)
        db_session.commit()

        # Verify
        assert task.task_type == TaskType.MANUAL_SCRAPE
        assert task.status == TaskStatus.RUNNING
        assert task.started_at is not None

    def test_completed_task_with_metrics(self, db_session):
        """Test creating a completed task with job metrics."""
        started = datetime.now() - timedelta(minutes=5)
        completed = datetime.now()

        task = ScrapingTask(
            task_type=TaskType.SCHEDULED_SCRAPE,
            source_platform="Naukri",
            status=TaskStatus.COMPLETED,
            started_at=started,
            completed_at=completed,
            jobs_found=50,
            jobs_created=30,
            jobs_updated=20
        )
        db_session.add(task)
        db_session.commit()

        # Verify
        assert task.status == TaskStatus.COMPLETED
        assert task.jobs_found == 50
        assert task.jobs_created == 30
        assert task.jobs_updated == 20
        assert task.started_at == started
        assert task.completed_at == completed

    def test_failed_task_with_error_message(self, db_session):
        """Test creating a failed task with error message."""
        task = ScrapingTask(
            task_type=TaskType.SCHEDULED_SCRAPE,
            source_platform="Monster",
            status=TaskStatus.FAILED,
            started_at=datetime.now() - timedelta(minutes=2),
            completed_at=datetime.now(),
            error_message="Connection timeout after 30 seconds",
            retry_count=1
        )
        db_session.add(task)
        db_session.commit()

        # Verify
        assert task.status == TaskStatus.FAILED
        assert task.error_message == "Connection timeout after 30 seconds"
        assert task.retry_count == 1

    def test_retry_count_constraint_valid(self, db_session):
        """Test that retry_count within bounds (0-3) is accepted."""
        for retry_count in [0, 1, 2, 3]:
            task = ScrapingTask(
                task_type=TaskType.SCHEDULED_SCRAPE,
                source_platform="LinkedIn",
                status=TaskStatus.FAILED,
                retry_count=retry_count
            )
            db_session.add(task)
            db_session.commit()
            assert task.retry_count == retry_count

    def test_retry_count_constraint_invalid(self, db_session):
        """Test that retry_count outside bounds (0-3) is rejected."""
        task = ScrapingTask(
            task_type=TaskType.SCHEDULED_SCRAPE,
            source_platform="Indeed",
            status=TaskStatus.FAILED,
            retry_count=4  # Invalid: exceeds max of 3
        )
        db_session.add(task)

        with pytest.raises(IntegrityError) as exc_info:
            db_session.commit()
        assert "check_retry_count_bounds" in str(exc_info.value)

    def test_jobs_found_consistency_constraint_valid(self, db_session):
        """Test that jobs_found >= jobs_created + jobs_updated is enforced."""
        task = ScrapingTask(
            task_type=TaskType.SCHEDULED_SCRAPE,
            source_platform="LinkedIn",
            status=TaskStatus.COMPLETED,
            jobs_found=100,
            jobs_created=60,
            jobs_updated=40
        )
        db_session.add(task)
        db_session.commit()

        # Verify
        assert task.jobs_found == 100
        assert task.jobs_created == 60
        assert task.jobs_updated == 40

    def test_jobs_found_consistency_constraint_invalid(self, db_session):
        """Test that jobs_found < jobs_created + jobs_updated is rejected."""
        task = ScrapingTask(
            task_type=TaskType.SCHEDULED_SCRAPE,
            source_platform="Indeed",
            status=TaskStatus.COMPLETED,
            jobs_found=50,
            jobs_created=40,
            jobs_updated=20  # Invalid: 40 + 20 > 50
        )
        db_session.add(task)

        with pytest.raises(IntegrityError) as exc_info:
            db_session.commit()
        assert "check_jobs_found_consistency" in str(exc_info.value)

    def test_jobs_metrics_positive_constraint(self, db_session):
        """Test that job metrics must be non-negative."""
        # Valid: all non-negative
        task = ScrapingTask(
            task_type=TaskType.SCHEDULED_SCRAPE,
            source_platform="Naukri",
            status=TaskStatus.COMPLETED,
            jobs_found=0,
            jobs_created=0,
            jobs_updated=0
        )
        db_session.add(task)
        db_session.commit()
        assert task.jobs_found == 0

    def test_jobs_metrics_negative_invalid(self, db_session):
        """Test that negative job metrics are rejected."""
        task = ScrapingTask(
            task_type=TaskType.SCHEDULED_SCRAPE,
            source_platform="Monster",
            status=TaskStatus.COMPLETED,
            jobs_found=-1  # Invalid: negative
        )
        db_session.add(task)

        with pytest.raises(IntegrityError) as exc_info:
            db_session.commit()
        assert "check_jobs_metrics_positive" in str(exc_info.value)

    def test_completion_after_start_constraint_valid(self, db_session):
        """Test that completed_at >= started_at is enforced."""
        started = datetime.now() - timedelta(minutes=10)
        completed = datetime.now()

        task = ScrapingTask(
            task_type=TaskType.SCHEDULED_SCRAPE,
            source_platform="LinkedIn",
            status=TaskStatus.COMPLETED,
            started_at=started,
            completed_at=completed
        )
        db_session.add(task)
        db_session.commit()

        # Verify
        assert task.completed_at >= task.started_at

    def test_completion_after_start_constraint_invalid(self, db_session):
        """Test that completed_at < started_at is rejected."""
        started = datetime.now()
        completed = started - timedelta(minutes=5)  # Invalid: before start

        task = ScrapingTask(
            task_type=TaskType.SCHEDULED_SCRAPE,
            source_platform="Indeed",
            status=TaskStatus.COMPLETED,
            started_at=started,
            completed_at=completed
        )
        db_session.add(task)

        with pytest.raises(IntegrityError) as exc_info:
            db_session.commit()
        assert "check_completion_after_start" in str(exc_info.value)

    def test_is_pending_method(self, db_session):
        """Test the is_pending helper method."""
        task = ScrapingTask(
            task_type=TaskType.SCHEDULED_SCRAPE,
            source_platform="LinkedIn",
            status=TaskStatus.PENDING
        )
        db_session.add(task)
        db_session.commit()

        assert task.is_pending() is True
        assert task.is_running() is False
        assert task.is_completed() is False
        assert task.is_failed() is False

    def test_is_running_method(self, db_session):
        """Test the is_running helper method."""
        task = ScrapingTask(
            task_type=TaskType.SCHEDULED_SCRAPE,
            source_platform="Indeed",
            status=TaskStatus.RUNNING,
            started_at=datetime.now()
        )
        db_session.add(task)
        db_session.commit()

        assert task.is_pending() is False
        assert task.is_running() is True
        assert task.is_completed() is False
        assert task.is_failed() is False

    def test_is_completed_method(self, db_session):
        """Test the is_completed helper method."""
        task = ScrapingTask(
            task_type=TaskType.SCHEDULED_SCRAPE,
            source_platform="Naukri",
            status=TaskStatus.COMPLETED,
            started_at=datetime.now() - timedelta(minutes=5),
            completed_at=datetime.now(),
            jobs_found=10,
            jobs_created=10
        )
        db_session.add(task)
        db_session.commit()

        assert task.is_pending() is False
        assert task.is_running() is False
        assert task.is_completed() is True
        assert task.is_failed() is False

    def test_is_failed_method(self, db_session):
        """Test the is_failed helper method."""
        task = ScrapingTask(
            task_type=TaskType.SCHEDULED_SCRAPE,
            source_platform="Monster",
            status=TaskStatus.FAILED,
            started_at=datetime.now() - timedelta(minutes=2),
            completed_at=datetime.now(),
            error_message="Network error"
        )
        db_session.add(task)
        db_session.commit()

        assert task.is_pending() is False
        assert task.is_running() is False
        assert task.is_completed() is False
        assert task.is_failed() is True

    def test_can_retry_method(self, db_session):
        """Test the can_retry helper method."""
        # Failed task with retry_count < 3 can retry
        task1 = ScrapingTask(
            task_type=TaskType.SCHEDULED_SCRAPE,
            source_platform="LinkedIn",
            status=TaskStatus.FAILED,
            retry_count=2
        )
        db_session.add(task1)
        db_session.commit()
        assert task1.can_retry() is True

        # Failed task with retry_count = 3 cannot retry
        task2 = ScrapingTask(
            task_type=TaskType.SCHEDULED_SCRAPE,
            source_platform="Indeed",
            status=TaskStatus.FAILED,
            retry_count=3
        )
        db_session.add(task2)
        db_session.commit()
        assert task2.can_retry() is False

        # Completed task cannot retry
        task3 = ScrapingTask(
            task_type=TaskType.SCHEDULED_SCRAPE,
            source_platform="Naukri",
            status=TaskStatus.COMPLETED,
            retry_count=0,
            jobs_found=5,
            jobs_created=5
        )
        db_session.add(task3)
        db_session.commit()
        assert task3.can_retry() is False

    def test_get_duration_seconds_method(self, db_session):
        """Test the get_duration_seconds helper method."""
        started = datetime.now() - timedelta(minutes=5, seconds=30)
        completed = datetime.now()

        task = ScrapingTask(
            task_type=TaskType.SCHEDULED_SCRAPE,
            source_platform="LinkedIn",
            status=TaskStatus.COMPLETED,
            started_at=started,
            completed_at=completed,
            jobs_found=20,
            jobs_created=20
        )
        db_session.add(task)
        db_session.commit()

        duration = task.get_duration_seconds()
        assert duration > 0
        assert 320 <= duration <= 340  # Approximately 5.5 minutes (330 seconds)

    def test_get_duration_seconds_no_timestamps(self, db_session):
        """Test get_duration_seconds when timestamps are missing."""
        task = ScrapingTask(
            task_type=TaskType.SCHEDULED_SCRAPE,
            source_platform="Indeed",
            status=TaskStatus.PENDING
        )
        db_session.add(task)
        db_session.commit()

        assert task.get_duration_seconds() == 0.0

    def test_get_success_rate_method(self, db_session):
        """Test the get_success_rate helper method."""
        task = ScrapingTask(
            task_type=TaskType.SCHEDULED_SCRAPE,
            source_platform="Naukri",
            status=TaskStatus.COMPLETED,
            jobs_found=100,
            jobs_created=75,
            jobs_updated=20
        )
        db_session.add(task)
        db_session.commit()

        success_rate = task.get_success_rate()
        assert success_rate == 75.0  # 75 created out of 100 found

    def test_get_success_rate_zero_found(self, db_session):
        """Test get_success_rate when no jobs were found."""
        task = ScrapingTask(
            task_type=TaskType.SCHEDULED_SCRAPE,
            source_platform="Monster",
            status=TaskStatus.COMPLETED,
            jobs_found=0,
            jobs_created=0
        )
        db_session.add(task)
        db_session.commit()

        assert task.get_success_rate() == 0.0

    def test_scraping_task_repr(self, db_session):
        """Test the string representation of ScrapingTask."""
        task = ScrapingTask(
            task_type=TaskType.SCHEDULED_SCRAPE,
            source_platform="LinkedIn",
            status=TaskStatus.RUNNING
        )
        db_session.add(task)
        db_session.commit()

        repr_str = repr(task)
        assert "ScrapingTask" in repr_str
        assert str(task.id) in repr_str
        assert "scheduled_scrape" in repr_str
        assert "running" in repr_str
        assert "LinkedIn" in repr_str

    def test_task_type_enum_values(self, db_session):
        """Test all TaskType enum values."""
        task_types = [
            TaskType.SCHEDULED_SCRAPE,
            TaskType.MANUAL_SCRAPE,
            TaskType.URL_IMPORT
        ]

        for task_type in task_types:
            task = ScrapingTask(
                task_type=task_type,
                source_platform="TestPlatform",
                status=TaskStatus.PENDING
            )
            db_session.add(task)
            db_session.commit()
            assert task.task_type == task_type

    def test_task_status_enum_values(self, db_session):
        """Test all TaskStatus enum values."""
        statuses = [
            TaskStatus.PENDING,
            TaskStatus.RUNNING,
            TaskStatus.COMPLETED,
            TaskStatus.FAILED
        ]

        for status in statuses:
            task = ScrapingTask(
                task_type=TaskType.SCHEDULED_SCRAPE,
                source_platform="TestPlatform",
                status=status
            )
            db_session.add(task)
            db_session.commit()
            assert task.status == status

    def test_monitoring_query_index(self, db_session):
        """Test that status and created_at index supports monitoring queries."""
        # Create multiple tasks with different statuses and timestamps
        base_time = datetime.now() - timedelta(hours=24)

        tasks = [
            ScrapingTask(
                task_type=TaskType.SCHEDULED_SCRAPE,
                source_platform="LinkedIn",
                status=TaskStatus.COMPLETED,
                created_at=base_time + timedelta(hours=i),
                jobs_found=10,
                jobs_created=10
            )
            for i in range(5)
        ]

        tasks.extend([
            ScrapingTask(
                task_type=TaskType.SCHEDULED_SCRAPE,
                source_platform="Indeed",
                status=TaskStatus.FAILED,
                created_at=base_time + timedelta(hours=i + 5),
                error_message="Test error"
            )
            for i in range(3)
        ])

        db_session.add_all(tasks)
        db_session.commit()

        # Query using the composite index (status, created_at)
        recent_failed = db_session.query(ScrapingTask).filter(
            ScrapingTask.status == TaskStatus.FAILED,
            ScrapingTask.created_at >= base_time
        ).order_by(ScrapingTask.created_at.desc()).all()

        assert len(recent_failed) == 3
        assert all(task.status == TaskStatus.FAILED for task in recent_failed)

    def test_platform_specific_queries(self, db_session):
        """Test querying tasks by source platform."""
        platforms = ["LinkedIn", "Indeed", "Naukri", "Monster"]

        for platform in platforms:
            task = ScrapingTask(
                task_type=TaskType.SCHEDULED_SCRAPE,
                source_platform=platform,
                status=TaskStatus.COMPLETED,
                jobs_found=10,
                jobs_created=10
            )
            db_session.add(task)
        db_session.commit()

        # Query by platform
        linkedin_tasks = db_session.query(ScrapingTask).filter_by(
            source_platform="LinkedIn"
        ).all()

        assert len(linkedin_tasks) == 1
        assert linkedin_tasks[0].source_platform == "LinkedIn"

    def test_url_import_without_platform(self, db_session):
        """Test URL import task without source_platform."""
        task = ScrapingTask(
            task_type=TaskType.URL_IMPORT,
            target_url="https://example.com/job/12345",
            status=TaskStatus.PENDING
        )
        db_session.add(task)
        db_session.commit()

        assert task.source_platform is None
        assert task.target_url is not None
        assert task.task_type == TaskType.URL_IMPORT
