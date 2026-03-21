"""
JobSeeker model for the job aggregation platform.

This module defines the JobSeeker model that stores job seeker accounts
with authentication, profile information, and application tracking.
"""
from datetime import datetime
import enum
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text,
    Index,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class JobSeeker(Base):
    """
    JobSeeker model representing users who search for and apply to jobs.
    
    Supports authentication, profile management, and application tracking.
    """
    __tablename__ = "job_seekers"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Authentication
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)

    # Profile information
    full_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    resume_url = Column(String(500), nullable=True)  # Default resume
    profile_summary = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # Check constraints for validation
    __table_args__ = (
        # Email format validation (basic check)
        CheckConstraint(
            "email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'",
            name="check_job_seeker_email_format"
        ),
        # Full name length validation (2-100 characters)
        CheckConstraint(
            "char_length(full_name) >= 2 AND char_length(full_name) <= 100",
            name="check_full_name_length"
        ),
        # Phone format validation (optional, but if provided must be valid)
        CheckConstraint(
            "phone IS NULL OR phone ~* '^[+]?[0-9\\s\\-\\(\\)]{7,20}$'",
            name="check_phone_format"
        ),
        # Resume URL validation (must be valid URL if provided)
        CheckConstraint(
            "resume_url IS NULL OR resume_url ~* '^https?://.+'",
            name="check_resume_url_format"
        ),
        # Indexes for efficient querying
        Index("idx_job_seekers_email", "email"),
    )

    def __repr__(self) -> str:
        return f"<JobSeeker(id={self.id}, email='{self.email}', name='{self.full_name}')>"

    def has_complete_profile(self) -> bool:
        """Check if the job seeker has completed their profile."""
        return all([
            self.full_name,
            self.phone,
            self.resume_url,
            self.profile_summary
        ])

    def can_apply(self) -> bool:
        """Check if job seeker can apply to jobs (requires at least a resume)."""
        return self.resume_url is not None
