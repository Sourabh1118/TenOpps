"""
ScrapingTask model and related enums for the job aggregation platform.

This module defines the ScrapingTask model that tracks scraping operations
for monitoring, debugging, and retry management.
"""
from datetime import datetime
import enum
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Text,
    Enum,
    CheckConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class TaskType(str, enum.Enum):
    """Type of scraping task."""
    SCHEDULED_SCRAPE = "scheduled_scrape"  # Automated scheduled scraping
    MANUAL_SCRAPE = "manual_scrape"  # Manually triggered scraping
    URL_IMPORT = "url_import"  # URL-based job import by employer


class TaskStatus(str, enum.Enum):
    """Status of a scraping task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScrapingTask(Base):
    """
    ScrapingTask model representing scraping operations.
    
    Tracks all scraping activities including scheduled scrapes,
    manual scrapes, and URL imports with metrics and error tracking.
    """
    __tablename__ = "scraping_tasks"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Task identification
    task_type = Column(Enum(TaskType, values_callable=lambda obj: [e.value for e in obj]), nullable=False, index=True)
    source_platform = Column(String(50), nullable=True)  # LinkedIn, Indeed, Naukri, Monster, etc.
    target_url = Column(Text, nullable=True)  # For URL imports

    # Status tracking
    status = Column(Enum(TaskStatus, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=TaskStatus.PENDING, index=True)

    # Execution timing
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Metrics
    jobs_found = Column(Integer, nullable=False, default=0)
    jobs_created = Column(Integer, nullable=False, default=0)
    jobs_updated = Column(Integer, nullable=False, default=0)

    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)

    # Check constraints for validation
    __table_args__ = (
        # Retry count bounds (0-3)
        CheckConstraint(
            "retry_count >= 0 AND retry_count <= 3",
            name="check_retry_count_bounds"
        ),
        # Jobs found must be >= jobs created + jobs updated
        CheckConstraint(
            "jobs_found >= jobs_created + jobs_updated",
            name="check_jobs_found_consistency"
        ),
        # Jobs metrics non-negative
        CheckConstraint(
            "jobs_found >= 0 AND jobs_created >= 0 AND jobs_updated >= 0",
            name="check_jobs_metrics_positive"
        ),
        # Completed at must be after started at if both present
        CheckConstraint(
            "started_at IS NULL OR completed_at IS NULL OR completed_at >= started_at",
            name="check_completion_after_start"
        ),
        # Indexes for efficient querying
        Index("idx_scraping_tasks_status", "status"),
        Index("idx_scraping_tasks_created_at", "created_at"),
        # Composite index for monitoring queries (status, created_at)
        Index("idx_scraping_tasks_status_created", "status", "created_at"),
        # Index for platform-specific queries
        Index("idx_scraping_tasks_platform", "source_platform"),
        # Index for task type queries
        Index("idx_scraping_tasks_type", "task_type"),
    )

    def __repr__(self) -> str:
        return f"<ScrapingTask(id={self.id}, type='{self.task_type}', status='{self.status}', platform='{self.source_platform}')>"

    def is_pending(self) -> bool:
        """Check if the task is pending execution."""
        return self.status == TaskStatus.PENDING

    def is_running(self) -> bool:
        """Check if the task is currently running."""
        return self.status == TaskStatus.RUNNING

    def is_completed(self) -> bool:
        """Check if the task completed successfully."""
        return self.status == TaskStatus.COMPLETED

    def is_failed(self) -> bool:
        """Check if the task failed."""
        return self.status == TaskStatus.FAILED

    def can_retry(self) -> bool:
        """Check if the task can be retried."""
        return self.is_failed() and self.retry_count < 3

    def get_duration_seconds(self) -> float:
        """Calculate task duration in seconds."""
        if not self.started_at or not self.completed_at:
            return 0.0
        delta = self.completed_at - self.started_at
        return delta.total_seconds()

    def get_success_rate(self) -> float:
        """Calculate success rate (jobs created/found)."""
        if self.jobs_found == 0:
            return 0.0
        return (self.jobs_created / self.jobs_found) * 100.0
