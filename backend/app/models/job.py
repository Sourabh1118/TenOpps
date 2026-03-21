"""
Job model and related enums for the job aggregation platform.

This module defines the core Job model that stores all job postings
(aggregated, direct, and URL imported) with comprehensive fields,
validation constraints, and indexes for efficient querying.
"""
from datetime import datetime, timedelta
from typing import Optional
import enum
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    Enum,
    CheckConstraint,
    Index,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
import uuid

from app.db.base import Base, GUID


# Enums for Job model
class JobType(str, enum.Enum):
    """Types of employment."""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"
    FELLOWSHIP = "fellowship"
    ACADEMIC = "academic"


class ExperienceLevel(str, enum.Enum):
    """Experience levels for job positions."""
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"


class SourceType(str, enum.Enum):
    """Source type of the job posting."""
    DIRECT = "direct"  # Posted directly by employer
    URL_IMPORT = "url_import"  # Imported via URL by employer
    AGGREGATED = "aggregated"  # Automatically scraped from external sources


class JobStatus(str, enum.Enum):
    """Status of the job posting."""
    ACTIVE = "active"
    EXPIRED = "expired"
    FILLED = "filled"
    DELETED = "deleted"


class Job(Base):
    """
    Job model representing all job postings in the platform.
    
    Supports three source types:
    - DIRECT: Posted directly by employers with application tracking
    - URL_IMPORT: Imported by employers via URL scraping
    - AGGREGATED: Automatically scraped from external job platforms
    
    Includes quality scoring, deduplication support, and full-text search indexes.
    """
    __tablename__ = "jobs"

    # Primary key
    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)

    # Core job information
    title = Column(String(200), nullable=False, index=True)
    company = Column(String(100), nullable=False, index=True)
    location = Column(String(200), nullable=False)
    remote = Column(Boolean, default=False, nullable=False)
    job_type = Column(Enum(JobType), nullable=False)
    experience_level = Column(Enum(ExperienceLevel), nullable=False)

    # Detailed information
    description = Column(Text, nullable=False)
    requirements = Column(ARRAY(Text), nullable=True)
    responsibilities = Column(ARRAY(Text), nullable=True)

    # Salary information
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    salary_currency = Column(String(3), default="USD", nullable=True)

    # Source information
    source_type = Column(Enum(SourceType), nullable=False, index=True)
    source_url = Column(Text, nullable=True)  # Original job URL
    source_platform = Column(String(50), nullable=True)  # LinkedIn, Indeed, etc.
    employer_id = Column(GUID(), nullable=True)  # For direct posts

    # Quality and status
    quality_score = Column(Float, nullable=False, default=0.0, index=True)
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.ACTIVE, index=True)

    # Dates
    posted_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # Engagement metrics
    application_count = Column(Integer, default=0, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    featured = Column(Boolean, default=False, nullable=False)

    # Tags for categorization
    tags = Column(ARRAY(String(50)), nullable=True)

    # Check constraints for validation
    __table_args__ = (
        # Title length validation (10-200 characters)
        CheckConstraint(
            "char_length(title) >= 10 AND char_length(title) <= 200",
            name="check_title_length"
        ),
        # Company name length validation (2-100 characters)
        CheckConstraint(
            "char_length(company) >= 2 AND char_length(company) <= 100",
            name="check_company_length"
        ),
        # Description length validation (50-5000 characters)
        CheckConstraint(
            "char_length(description) >= 50 AND char_length(description) <= 5000",
            name="check_description_length"
        ),
        # Salary validation: min < max if both provided
        CheckConstraint(
            "salary_min IS NULL OR salary_max IS NULL OR salary_min < salary_max",
            name="check_salary_range"
        ),
        # Quality score bounds (0-100)
        CheckConstraint(
            "quality_score >= 0 AND quality_score <= 100",
            name="check_quality_score_bounds"
        ),
        # Application count non-negative
        CheckConstraint(
            "application_count >= 0",
            name="check_application_count_positive"
        ),
        # View count non-negative
        CheckConstraint(
            "view_count >= 0",
            name="check_view_count_positive"
        ),
        # Expiration date must be after posted date
        CheckConstraint(
            "expires_at > posted_at",
            name="check_expiration_after_posted"
        ),
        # Expiration date within 90 days of posting
        CheckConstraint(
            "expires_at <= posted_at + INTERVAL '90 days'",
            name="check_expiration_within_90_days"
        ),
        # Indexes for efficient querying
        Index("idx_jobs_company", "company"),
        Index("idx_jobs_status", "status"),
        Index("idx_jobs_quality_score", "quality_score"),
        Index("idx_jobs_posted_at", "posted_at"),
        Index("idx_jobs_source_type", "source_type"),
        # Composite index for search ranking
        Index("idx_jobs_search_ranking", "status", "quality_score", "posted_at"),
        # Composite index for employer dashboard
        Index("idx_jobs_employer_status", "employer_id", "status"),
        # GIN indexes for full-text search on title and description
        Index(
            "idx_jobs_title_fts",
            func.to_tsvector("english", "title"),
            postgresql_using="gin"
        ),
        Index(
            "idx_jobs_description_fts",
            func.to_tsvector("english", "description"),
            postgresql_using="gin"
        ),
    )

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, title='{self.title}', company='{self.company}', status='{self.status}')>"

    def is_active(self) -> bool:
        """Check if the job is currently active."""
        return self.status == JobStatus.ACTIVE and self.expires_at > datetime.now()

    def is_expired(self) -> bool:
        """Check if the job has expired."""
        return datetime.now() > self.expires_at

    def days_until_expiration(self) -> int:
        """Calculate days until job expires."""
        if self.is_expired():
            return 0
        delta = self.expires_at - datetime.now()
        return delta.days

    def is_direct_post(self) -> bool:
        """Check if this is a direct employer post."""
        return self.source_type == SourceType.DIRECT

    def can_receive_applications(self) -> bool:
        """Check if this job can receive applications."""
        return self.is_direct_post() and self.is_active()
