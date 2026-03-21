"""
JobSource model for tracking job origins in the job aggregation platform.

This module defines the JobSource model that tracks the origin of each job,
supporting multiple sources per job for deduplication tracking.
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class JobSource(Base):
    """
    JobSource model representing the origin of a job posting.
    
    Tracks multiple sources per job to support deduplication and
    freshness tracking across different platforms.
    """
    __tablename__ = "job_sources"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Foreign key to Job
    job_id = Column(
        UUID(as_uuid=True),
        ForeignKey('jobs.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Source information
    source_platform = Column(String(50), nullable=False)  # LinkedIn, Indeed, Naukri, Monster, etc.
    source_url = Column(String(2048), nullable=False)  # Original job URL
    source_job_id = Column(String(255), nullable=True)  # External platform's job ID

    # Tracking timestamps
    scraped_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    last_verified_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    # Status
    is_active = Column(Boolean, default=True, nullable=False)  # Still available on source

    # Indexes for efficient querying
    __table_args__ = (
        # Index on job_id for source lookups (as specified in task)
        Index("idx_job_sources_job_id", "job_id"),
        # Composite index for platform-specific queries
        Index("idx_job_sources_platform_active", "source_platform", "is_active"),
        # Index for freshness tracking
        Index("idx_job_sources_last_verified", "last_verified_at"),
    )

    def __repr__(self) -> str:
        return f"<JobSource(id={self.id}, job_id={self.job_id}, platform='{self.source_platform}')>"

    def is_stale(self, days: int = 7) -> bool:
        """Check if the source hasn't been verified recently."""
        if not self.last_verified_at:
            return True
        delta = datetime.now() - self.last_verified_at
        return delta.days > days

    def mark_verified(self) -> None:
        """Update the last verified timestamp to now."""
        self.last_verified_at = datetime.now()

    def mark_inactive(self) -> None:
        """Mark this source as no longer active."""
        self.is_active = False
