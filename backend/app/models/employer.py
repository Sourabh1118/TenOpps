"""
Employer model and related enums for the job aggregation platform.

This module defines the Employer model that stores employer accounts
with authentication, company information, and subscription management.
"""
from datetime import datetime
import enum
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    Text,
    Enum,
    CheckConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.base import Base, GUID


class SubscriptionTier(str, enum.Enum):
    """Subscription tier levels for employers."""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"


class Employer(Base):
    """
    Employer model representing registered employers who can post jobs.
    
    Supports authentication, company information, and subscription management
    with usage tracking for quota enforcement.
    """
    __tablename__ = "employers"

    # Primary key
    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)

    # Authentication
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)

    # Company information
    company_name = Column(String(100), nullable=False)
    company_website = Column(String(500), nullable=True)
    company_logo = Column(String(500), nullable=True)
    company_description = Column(Text, nullable=True)

    # Subscription management
    subscription_tier = Column(
        Enum(SubscriptionTier),
        nullable=False,
        default=SubscriptionTier.FREE,
        index=True
    )
    subscription_start_date = Column(DateTime(timezone=True), nullable=False, default=func.now())
    subscription_end_date = Column(DateTime(timezone=True), nullable=False)
    
    # Usage tracking for quota enforcement
    monthly_posts_used = Column(Integer, nullable=False, default=0)
    featured_posts_used = Column(Integer, nullable=False, default=0)
    url_imports_used = Column(Integer, nullable=False, default=0)

    # Payment integration
    stripe_customer_id = Column(String(255), nullable=True, unique=True)

    # Account status
    verified = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # Check constraints for validation
    __table_args__ = (
        # Email format validation (basic check)
        CheckConstraint(
            "email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'",
            name="check_email_format"
        ),
        # Company name length validation (2-100 characters)
        CheckConstraint(
            "char_length(company_name) >= 2 AND char_length(company_name) <= 100",
            name="check_company_name_length"
        ),
        # Company website URL validation (must start with http:// or https://)
        CheckConstraint(
            "company_website IS NULL OR company_website ~* '^https?://.+'",
            name="check_company_website_url"
        ),
        # Monthly posts used non-negative
        CheckConstraint(
            "monthly_posts_used >= 0",
            name="check_monthly_posts_positive"
        ),
        # Featured posts used non-negative
        CheckConstraint(
            "featured_posts_used >= 0",
            name="check_featured_posts_positive"
        ),
        # URL imports used non-negative
        CheckConstraint(
            "url_imports_used >= 0",
            name="check_url_imports_positive"
        ),
        # Subscription end date must be after start date
        CheckConstraint(
            "subscription_end_date > subscription_start_date",
            name="check_subscription_dates"
        ),
        # Indexes for efficient querying
        Index("idx_employers_email", "email"),
        Index("idx_employers_subscription_tier", "subscription_tier"),
        Index("idx_employers_verified", "verified"),
        # Composite index for subscription management queries
        Index("idx_employers_subscription_status", "subscription_tier", "subscription_end_date"),
    )

    def __repr__(self) -> str:
        return f"<Employer(id={self.id}, email='{self.email}', company='{self.company_name}', tier='{self.subscription_tier}')>"

    def is_subscription_active(self) -> bool:
        """Check if the employer's subscription is currently active."""
        return self.subscription_end_date > datetime.now()

    def get_monthly_post_limit(self) -> int:
        """Get the monthly post limit based on subscription tier."""
        limits = {
            SubscriptionTier.FREE: 3,
            SubscriptionTier.BASIC: 20,
            SubscriptionTier.PREMIUM: float('inf')  # Unlimited
        }
        return limits.get(self.subscription_tier, 0)

    def get_featured_post_limit(self) -> int:
        """Get the featured post limit based on subscription tier."""
        limits = {
            SubscriptionTier.FREE: 0,
            SubscriptionTier.BASIC: 2,
            SubscriptionTier.PREMIUM: 10
        }
        return limits.get(self.subscription_tier, 0)

    def can_post_job(self) -> bool:
        """Check if employer can post a new job based on quota."""
        if not self.is_subscription_active():
            return False
        limit = self.get_monthly_post_limit()
        return self.monthly_posts_used < limit

    def can_feature_job(self) -> bool:
        """Check if employer can feature a job based on quota."""
        if not self.is_subscription_active():
            return False
        limit = self.get_featured_post_limit()
        return self.featured_posts_used < limit

    def has_application_tracking(self) -> bool:
        """Check if employer has access to application tracking."""
        return self.subscription_tier in [SubscriptionTier.BASIC, SubscriptionTier.PREMIUM]

    def has_analytics_access(self) -> bool:
        """Check if employer has access to analytics."""
        return self.subscription_tier == SubscriptionTier.PREMIUM
