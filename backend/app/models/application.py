"""
Application model and related enums for the job aggregation platform.

This module defines the Application model that tracks job applications
from job seekers to direct-posted jobs with status tracking and employer notes.
"""
from datetime import datetime
import enum
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text,
    Enum,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class ApplicationStatus(str, enum.Enum):
    """Status of a job application."""
    SUBMITTED = "submitted"
    REVIEWED = "reviewed"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    ACCEPTED = "accepted"


class Application(Base):
    """
    Application model representing job applications from job seekers.
    
    Tracks applications to direct-posted jobs with status management,
    resume/cover letter storage, and employer notes.
    """
    __tablename__ = "applications"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Foreign keys
    job_id = Column(
        UUID(as_uuid=True),
        ForeignKey('jobs.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    job_seeker_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Application materials
    resume = Column(String(500), nullable=False)  # File URL
    cover_letter = Column(Text, nullable=True)

    # Status tracking
    status = Column(
        Enum(ApplicationStatus),
        nullable=False,
        default=ApplicationStatus.SUBMITTED,
        index=True
    )

    # Employer notes
    employer_notes = Column(Text, nullable=True)

    # Timestamps
    applied_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # Indexes for efficient querying
    __table_args__ = (
        # Composite index for employer queries (job_id, status)
        Index("idx_applications_job_status", "job_id", "status"),
        # Index for job seeker queries
        Index("idx_applications_job_seeker", "job_seeker_id"),
    )

    def __repr__(self) -> str:
        return f"<Application(id={self.id}, job_id={self.job_id}, status='{self.status}')>"

    def is_pending(self) -> bool:
        """Check if the application is still pending review."""
        return self.status == ApplicationStatus.SUBMITTED

    def is_active(self) -> bool:
        """Check if the application is in an active state (not rejected or accepted)."""
        return self.status in [
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.REVIEWED,
            ApplicationStatus.SHORTLISTED
        ]

    def is_final(self) -> bool:
        """Check if the application has reached a final state."""
        return self.status in [ApplicationStatus.REJECTED, ApplicationStatus.ACCEPTED]
