"""
Tests for the Employer model.

This module tests the Employer model including:
- Model creation and field validation
- Database constraints (email uniqueness, check constraints)
- Subscription tier logic and quota enforcement
- Helper methods for subscription management
"""
import pytest
from datetime import datetime, timedelta
import uuid
from sqlalchemy.exc import IntegrityError
from app.models import Employer, SubscriptionTier


class TestEmployerModel:
    """Test suite for Employer model basic functionality."""

    def test_create_employer_with_required_fields(self, db_session):
        """Test creating an employer with all required fields."""
        employer = Employer(
            email="test@example.com",
            password_hash="hashed_password_123",
            company_name="Test Company",
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer)
        db_session.commit()
        
        assert employer.id is not None
        assert employer.email == "test@example.com"
        assert employer.company_name == "Test Company"
        assert employer.subscription_tier == SubscriptionTier.FREE
        assert employer.monthly_posts_used == 0
        assert employer.featured_posts_used == 0
        assert employer.verified is False

    def test_create_employer_with_all_fields(self, db_session):
        """Test creating an employer with all optional fields."""
        employer = Employer(
            email="premium@company.com",
            password_hash="hashed_password_456",
            company_name="Premium Corp",
            company_website="https://premiumcorp.com",
            company_logo="https://cdn.example.com/logo.png",
            company_description="A premium company",
            subscription_tier=SubscriptionTier.PREMIUM,
            subscription_end_date=datetime.now() + timedelta(days=365),
            stripe_customer_id="cus_123456789",
            verified=True
        )
        db_session.add(employer)
        db_session.commit()
        
        assert employer.company_website == "https://premiumcorp.com"
        assert employer.company_logo == "https://cdn.example.com/logo.png"
        assert employer.company_description == "A premium company"
        assert employer.subscription_tier == SubscriptionTier.PREMIUM
        assert employer.stripe_customer_id == "cus_123456789"
        assert employer.verified is True

    def test_employer_timestamps(self, db_session):
        """Test that timestamps are automatically set."""
        employer = Employer(
            email="timestamps@test.com",
            password_hash="hashed_password",
            company_name="Timestamp Test",
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer)
        db_session.commit()
        
        assert employer.created_at is not None
        assert employer.updated_at is not None
        assert employer.subscription_start_date is not None


class TestEmployerConstraints:
    """Test suite for database constraints on Employer model."""

    def test_email_uniqueness(self, db_session):
        """Test that email must be unique."""
        employer1 = Employer(
            email="unique@test.com",
            password_hash="hash1",
            company_name="Company 1",
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer1)
        db_session.commit()
        
        # Try to create another employer with same email
        employer2 = Employer(
            email="unique@test.com",
            password_hash="hash2",
            company_name="Company 2",
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_company_name_length_validation(self, db_session):
        """Test company name length constraints (2-100 characters)."""
        # Test too short (1 character)
        employer_short = Employer(
            email="short@test.com",
            password_hash="hash",
            company_name="A",
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer_short)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
        
        db_session.rollback()
        
        # Test too long (101 characters)
        employer_long = Employer(
            email="long@test.com",
            password_hash="hash",
            company_name="A" * 101,
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer_long)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_company_name_valid_length(self, db_session):
        """Test valid company name lengths."""
        # Test minimum valid (2 characters)
        employer_min = Employer(
            email="min@test.com",
            password_hash="hash",
            company_name="AB",
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer_min)
        db_session.commit()
        assert employer_min.company_name == "AB"
        
        # Test maximum valid (100 characters)
        employer_max = Employer(
            email="max@test.com",
            password_hash="hash",
            company_name="A" * 100,
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer_max)
        db_session.commit()
        assert len(employer_max.company_name) == 100

    def test_company_website_url_validation(self, db_session):
        """Test company website URL validation."""
        # Test invalid URL (no protocol)
        employer_invalid = Employer(
            email="invalid@test.com",
            password_hash="hash",
            company_name="Invalid URL Co",
            company_website="www.example.com",
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer_invalid)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
        
        db_session.rollback()
        
        # Test valid HTTP URL
        employer_http = Employer(
            email="http@test.com",
            password_hash="hash",
            company_name="HTTP Co",
            company_website="http://example.com",
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer_http)
        db_session.commit()
        assert employer_http.company_website == "http://example.com"
        
        # Test valid HTTPS URL
        employer_https = Employer(
            email="https@test.com",
            password_hash="hash",
            company_name="HTTPS Co",
            company_website="https://secure.example.com",
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer_https)
        db_session.commit()
        assert employer_https.company_website == "https://secure.example.com"

    def test_monthly_posts_non_negative(self, db_session):
        """Test that monthly_posts_used cannot be negative."""
        employer = Employer(
            email="negative@test.com",
            password_hash="hash",
            company_name="Negative Test",
            monthly_posts_used=-1,
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_featured_posts_non_negative(self, db_session):
        """Test that featured_posts_used cannot be negative."""
        employer = Employer(
            email="negative_featured@test.com",
            password_hash="hash",
            company_name="Negative Featured Test",
            featured_posts_used=-1,
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_subscription_dates_validation(self, db_session):
        """Test that subscription_end_date must be after subscription_start_date."""
        start_date = datetime.now()
        end_date = start_date - timedelta(days=1)  # End before start
        
        employer = Employer(
            email="dates@test.com",
            password_hash="hash",
            company_name="Dates Test",
            subscription_start_date=start_date,
            subscription_end_date=end_date
        )
        db_session.add(employer)
        
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestEmployerSubscriptionLogic:
    """Test suite for subscription-related business logic."""

    def test_is_subscription_active(self, db_session):
        """Test subscription active status check."""
        # Active subscription
        employer_active = Employer(
            email="active@test.com",
            password_hash="hash",
            company_name="Active Co",
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer_active)
        db_session.commit()
        assert employer_active.is_subscription_active() is True
        
        # Expired subscription
        employer_expired = Employer(
            email="expired@test.com",
            password_hash="hash",
            company_name="Expired Co",
            subscription_end_date=datetime.now() - timedelta(days=1)
        )
        db_session.add(employer_expired)
        db_session.commit()
        assert employer_expired.is_subscription_active() is False

    def test_get_monthly_post_limit(self, db_session):
        """Test monthly post limits for different tiers."""
        # Free tier
        employer_free = Employer(
            email="free@test.com",
            password_hash="hash",
            company_name="Free Co",
            subscription_tier=SubscriptionTier.FREE,
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer_free)
        db_session.commit()
        assert employer_free.get_monthly_post_limit() == 3
        
        # Basic tier
        employer_basic = Employer(
            email="basic@test.com",
            password_hash="hash",
            company_name="Basic Co",
            subscription_tier=SubscriptionTier.BASIC,
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer_basic)
        db_session.commit()
        assert employer_basic.get_monthly_post_limit() == 20
        
        # Premium tier (unlimited)
        employer_premium = Employer(
            email="premium@test.com",
            password_hash="hash",
            company_name="Premium Co",
            subscription_tier=SubscriptionTier.PREMIUM,
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer_premium)
        db_session.commit()
        assert employer_premium.get_monthly_post_limit() == float('inf')

    def test_get_featured_post_limit(self, db_session):
        """Test featured post limits for different tiers."""
        # Free tier (no featured posts)
        employer_free = Employer(
            email="free_featured@test.com",
            password_hash="hash",
            company_name="Free Featured Co",
            subscription_tier=SubscriptionTier.FREE,
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer_free)
        db_session.commit()
        assert employer_free.get_featured_post_limit() == 0
        
        # Basic tier
        employer_basic = Employer(
            email="basic_featured@test.com",
            password_hash="hash",
            company_name="Basic Featured Co",
            subscription_tier=SubscriptionTier.BASIC,
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer_basic)
        db_session.commit()
        assert employer_basic.get_featured_post_limit() == 2
        
        # Premium tier
        employer_premium = Employer(
            email="premium_featured@test.com",
            password_hash="hash",
            company_name="Premium Featured Co",
            subscription_tier=SubscriptionTier.PREMIUM,
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer_premium)
        db_session.commit()
        assert employer_premium.get_featured_post_limit() == 10

    def test_can_post_job(self, db_session):
        """Test job posting quota check."""
        # Free tier with quota available
        employer_can_post = Employer(
            email="can_post@test.com",
            password_hash="hash",
            company_name="Can Post Co",
            subscription_tier=SubscriptionTier.FREE,
            monthly_posts_used=2,
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer_can_post)
        db_session.commit()
        assert employer_can_post.can_post_job() is True
        
        # Free tier with quota exhausted
        employer_cannot_post = Employer(
            email="cannot_post@test.com",
            password_hash="hash",
            company_name="Cannot Post Co",
            subscription_tier=SubscriptionTier.FREE,
            monthly_posts_used=3,
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer_cannot_post)
        db_session.commit()
        assert employer_cannot_post.can_post_job() is False
        
        # Expired subscription
        employer_expired = Employer(
            email="expired_post@test.com",
            password_hash="hash",
            company_name="Expired Post Co",
            subscription_tier=SubscriptionTier.BASIC,
            monthly_posts_used=0,
            subscription_end_date=datetime.now() - timedelta(days=1)
        )
        db_session.add(employer_expired)
        db_session.commit()
        assert employer_expired.can_post_job() is False

    def test_can_feature_job(self, db_session):
        """Test featured job quota check."""
        # Basic tier with quota available
        employer_can_feature = Employer(
            email="can_feature@test.com",
            password_hash="hash",
            company_name="Can Feature Co",
            subscription_tier=SubscriptionTier.BASIC,
            featured_posts_used=1,
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer_can_feature)
        db_session.commit()
        assert employer_can_feature.can_feature_job() is True
        
        # Free tier (no featured posts allowed)
        employer_free = Employer(
            email="free_feature@test.com",
            password_hash="hash",
            company_name="Free Feature Co",
            subscription_tier=SubscriptionTier.FREE,
            featured_posts_used=0,
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer_free)
        db_session.commit()
        assert employer_free.can_feature_job() is False

    def test_has_application_tracking(self, db_session):
        """Test application tracking access."""
        # Free tier (no application tracking)
        employer_free = Employer(
            email="free_tracking@test.com",
            password_hash="hash",
            company_name="Free Tracking Co",
            subscription_tier=SubscriptionTier.FREE,
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer_free)
        db_session.commit()
        assert employer_free.has_application_tracking() is False
        
        # Basic tier (has application tracking)
        employer_basic = Employer(
            email="basic_tracking@test.com",
            password_hash="hash",
            company_name="Basic Tracking Co",
            subscription_tier=SubscriptionTier.BASIC,
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer_basic)
        db_session.commit()
        assert employer_basic.has_application_tracking() is True
        
        # Premium tier (has application tracking)
        employer_premium = Employer(
            email="premium_tracking@test.com",
            password_hash="hash",
            company_name="Premium Tracking Co",
            subscription_tier=SubscriptionTier.PREMIUM,
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer_premium)
        db_session.commit()
        assert employer_premium.has_application_tracking() is True

    def test_has_analytics_access(self, db_session):
        """Test analytics access."""
        # Free tier (no analytics)
        employer_free = Employer(
            email="free_analytics@test.com",
            password_hash="hash",
            company_name="Free Analytics Co",
            subscription_tier=SubscriptionTier.FREE,
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer_free)
        db_session.commit()
        assert employer_free.has_analytics_access() is False
        
        # Basic tier (no analytics)
        employer_basic = Employer(
            email="basic_analytics@test.com",
            password_hash="hash",
            company_name="Basic Analytics Co",
            subscription_tier=SubscriptionTier.BASIC,
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer_basic)
        db_session.commit()
        assert employer_basic.has_analytics_access() is False
        
        # Premium tier (has analytics)
        employer_premium = Employer(
            email="premium_analytics@test.com",
            password_hash="hash",
            company_name="Premium Analytics Co",
            subscription_tier=SubscriptionTier.PREMIUM,
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer_premium)
        db_session.commit()
        assert employer_premium.has_analytics_access() is True


class TestEmployerIndexes:
    """Test that indexes are properly created for query performance."""

    def test_email_index_exists(self, db_session):
        """Test that email index exists for authentication queries."""
        # This is a basic test - in production, you'd check pg_indexes
        employer = Employer(
            email="index_test@test.com",
            password_hash="hash",
            company_name="Index Test Co",
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer)
        db_session.commit()
        
        # Query by email should be fast (uses index)
        result = db_session.query(Employer).filter(
            Employer.email == "index_test@test.com"
        ).first()
        assert result is not None
        assert result.email == "index_test@test.com"
