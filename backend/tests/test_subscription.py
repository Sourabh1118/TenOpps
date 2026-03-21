"""
Unit tests for subscription management service.

Tests cover:
- Subscription tier limits
- Quota checking with caching
- Quota consumption
- Subscription update endpoint
- Monthly quota reset task
- Edge cases and error handling
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.models.employer import Employer, SubscriptionTier
from app.services.subscription import (
    get_tier_limits,
    check_quota,
    consume_quota,
    _get_cache_key,
    _invalidate_subscription_cache,
)
from app.tasks.subscription_tasks import reset_monthly_quotas


class TestGetTierLimits:
    """Test subscription tier limit configuration."""
    
    def test_free_tier_limits(self):
        """Test free tier has correct limits."""
        limits = get_tier_limits(SubscriptionTier.FREE)
        
        assert limits["monthly_posts"] == 3
        assert limits["featured_posts"] == 0
        assert limits["has_application_tracking"] is False
        assert limits["has_analytics"] is False
    
    def test_basic_tier_limits(self):
        """Test basic tier has correct limits."""
        limits = get_tier_limits(SubscriptionTier.BASIC)
        
        assert limits["monthly_posts"] == 20
        assert limits["featured_posts"] == 2
        assert limits["has_application_tracking"] is True
        assert limits["has_analytics"] is False
    
    def test_premium_tier_limits(self):
        """Test premium tier has correct limits."""
        limits = get_tier_limits(SubscriptionTier.PREMIUM)
        
        assert limits["monthly_posts"] == float('inf')  # Unlimited
        assert limits["featured_posts"] == 10
        assert limits["has_application_tracking"] is True
        assert limits["has_analytics"] is True


class TestCheckQuota:
    """Test quota checking logic with caching."""
    
    def test_check_quota_with_available_quota(self, db_session: Session):
        """Test quota check returns True when quota is available."""
        # Create employer with free tier
        employer = Employer(
            id=uuid4(),
            email="test@example.com",
            password_hash="hashed",
            company_name="Test Corp",
            subscription_tier=SubscriptionTier.FREE,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=0,
            featured_posts_used=0,
        )
        db_session.add(employer)
        db_session.commit()
        
        # Mock Redis client
        redis_mock = Mock()
        redis_mock.get.return_value = None  # No cache
        
        # Check quota
        result = check_quota(db_session, redis_mock, employer.id, "monthly_posts")
        
        assert result is True
    
    def test_check_quota_with_exceeded_quota(self, db_session: Session):
        """Test quota check returns False when quota is exceeded."""
        # Create employer with free tier and quota exhausted
        employer = Employer(
            id=uuid4(),
            email="test@example.com",
            password_hash="hashed",
            company_name="Test Corp",
            subscription_tier=SubscriptionTier.FREE,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=3,  # Limit reached
            featured_posts_used=0,
        )
        db_session.add(employer)
        db_session.commit()
        
        # Mock Redis client
        redis_mock = Mock()
        redis_mock.get.return_value = None  # No cache
        
        # Check quota
        result = check_quota(db_session, redis_mock, employer.id, "monthly_posts")
        
        assert result is False
    
    def test_check_quota_with_premium_unlimited(self, db_session: Session):
        """Test premium tier has unlimited monthly posts."""
        # Create employer with premium tier
        employer = Employer(
            id=uuid4(),
            email="test@example.com",
            password_hash="hashed",
            company_name="Test Corp",
            subscription_tier=SubscriptionTier.PREMIUM,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=1000,  # High usage
            featured_posts_used=0,
        )
        db_session.add(employer)
        db_session.commit()
        
        # Mock Redis client
        redis_mock = Mock()
        redis_mock.get.return_value = None  # No cache
        
        # Check quota - should still be available
        result = check_quota(db_session, redis_mock, employer.id, "monthly_posts")
        
        assert result is True
    
    def test_check_quota_uses_cache(self, db_session: Session):
        """Test quota check uses cached data when available."""
        import json
        
        employer_id = uuid4()
        
        # Mock Redis client with cached data
        redis_mock = Mock()
        cache_data = {
            "tier": "basic",
            "usage": {
                "monthly_posts_used": 5,
                "featured_posts_used": 1,
            },
            "subscription_end_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        }
        redis_mock.get.return_value = json.dumps(cache_data)
        
        # Check quota - should use cache, not query database
        result = check_quota(db_session, redis_mock, employer_id, "monthly_posts")
        
        assert result is True
        redis_mock.get.assert_called_once()
    
    def test_check_quota_caches_result(self, db_session: Session):
        """Test quota check caches subscription data."""
        # Create employer
        employer = Employer(
            id=uuid4(),
            email="test@example.com",
            password_hash="hashed",
            company_name="Test Corp",
            subscription_tier=SubscriptionTier.BASIC,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=5,
            featured_posts_used=1,
        )
        db_session.add(employer)
        db_session.commit()
        
        # Mock Redis client
        redis_mock = Mock()
        redis_mock.get.return_value = None  # No cache initially
        
        # Check quota
        check_quota(db_session, redis_mock, employer.id, "monthly_posts")
        
        # Verify cache was set
        redis_mock.setex.assert_called_once()
        call_args = redis_mock.setex.call_args
        assert call_args[0][0] == f"subscription:{employer.id}"  # Cache key
        assert call_args[0][1] == 300  # TTL = 5 minutes
    
    def test_check_quota_with_inactive_subscription(self, db_session: Session):
        """Test quota check returns False for inactive subscription."""
        # Create employer with expired subscription
        employer = Employer(
            id=uuid4(),
            email="test@example.com",
            password_hash="hashed",
            company_name="Test Corp",
            subscription_tier=SubscriptionTier.FREE,
            subscription_start_date=datetime.utcnow() - timedelta(days=60),
            subscription_end_date=datetime.utcnow() - timedelta(days=30),  # Expired
            monthly_posts_used=0,
            featured_posts_used=0,
        )
        db_session.add(employer)
        db_session.commit()
        
        # Mock Redis client
        redis_mock = Mock()
        redis_mock.get.return_value = None
        
        # Check quota
        result = check_quota(db_session, redis_mock, employer.id, "monthly_posts")
        
        assert result is False
    
    def test_check_quota_with_missing_employer(self, db_session: Session):
        """Test quota check returns False for non-existent employer."""
        redis_mock = Mock()
        redis_mock.get.return_value = None
        
        # Check quota for non-existent employer
        result = check_quota(db_session, redis_mock, uuid4(), "monthly_posts")
        
        assert result is False
    
    def test_check_quota_with_invalid_quota_type(self, db_session: Session):
        """Test quota check raises ValueError for invalid quota type."""
        employer_id = uuid4()
        redis_mock = Mock()
        
        with pytest.raises(ValueError, match="Invalid quota_type"):
            check_quota(db_session, redis_mock, employer_id, "invalid_type")


class TestConsumeQuota:
    """Test quota consumption logic."""
    
    def test_consume_quota_increments_counter(self, db_session: Session):
        """Test consume_quota increments usage counter."""
        # Create employer
        employer = Employer(
            id=uuid4(),
            email="test@example.com",
            password_hash="hashed",
            company_name="Test Corp",
            subscription_tier=SubscriptionTier.BASIC,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=5,
            featured_posts_used=1,
        )
        db_session.add(employer)
        db_session.commit()
        
        initial_usage = employer.monthly_posts_used
        
        # Mock Redis client
        redis_mock = Mock()
        
        # Consume quota
        consume_quota(db_session, redis_mock, employer.id, "monthly_posts")
        
        # Refresh employer from database
        db_session.refresh(employer)
        
        assert employer.monthly_posts_used == initial_usage + 1
    
    def test_consume_quota_invalidates_cache(self, db_session: Session):
        """Test consume_quota invalidates subscription cache."""
        # Create employer
        employer = Employer(
            id=uuid4(),
            email="test@example.com",
            password_hash="hashed",
            company_name="Test Corp",
            subscription_tier=SubscriptionTier.BASIC,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=5,
            featured_posts_used=1,
        )
        db_session.add(employer)
        db_session.commit()
        
        # Mock Redis client
        redis_mock = Mock()
        
        # Consume quota
        consume_quota(db_session, redis_mock, employer.id, "monthly_posts")
        
        # Verify cache was invalidated
        redis_mock.delete.assert_called_once_with(f"subscription:{employer.id}")
    
    def test_consume_quota_raises_error_when_exceeded(self, db_session: Session):
        """Test consume_quota raises RuntimeError when quota is exceeded."""
        # Create employer with quota exhausted
        employer = Employer(
            id=uuid4(),
            email="test@example.com",
            password_hash="hashed",
            company_name="Test Corp",
            subscription_tier=SubscriptionTier.FREE,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=3,  # Limit reached
            featured_posts_used=0,
        )
        db_session.add(employer)
        db_session.commit()
        
        redis_mock = Mock()
        
        # Try to consume quota
        with pytest.raises(RuntimeError, match="quota exceeded"):
            consume_quota(db_session, redis_mock, employer.id, "monthly_posts")
    
    def test_consume_quota_with_missing_employer(self, db_session: Session):
        """Test consume_quota raises RuntimeError for non-existent employer."""
        redis_mock = Mock()
        
        with pytest.raises(RuntimeError, match="not found"):
            consume_quota(db_session, redis_mock, uuid4(), "monthly_posts")
    
    def test_consume_quota_with_invalid_quota_type(self, db_session: Session):
        """Test consume_quota raises ValueError for invalid quota type."""
        employer_id = uuid4()
        redis_mock = Mock()
        
        with pytest.raises(ValueError, match="Invalid quota_type"):
            consume_quota(db_session, redis_mock, employer_id, "invalid_type")
    
    def test_consume_featured_quota(self, db_session: Session):
        """Test consuming featured post quota."""
        # Create employer
        employer = Employer(
            id=uuid4(),
            email="test@example.com",
            password_hash="hashed",
            company_name="Test Corp",
            subscription_tier=SubscriptionTier.BASIC,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=5,
            featured_posts_used=0,
        )
        db_session.add(employer)
        db_session.commit()
        
        redis_mock = Mock()
        
        # Consume featured quota
        consume_quota(db_session, redis_mock, employer.id, "featured_posts")
        
        # Refresh employer
        db_session.refresh(employer)
        
        assert employer.featured_posts_used == 1


class TestSubscriptionUpdateEndpoint:
    """Test subscription update API endpoint."""
    
    def test_update_subscription_success(self, client, db_session: Session):
        """Test successful subscription update."""
        # Create and register employer
        from app.core.security import hash_password
        
        employer = Employer(
            id=uuid4(),
            email="employer@test.com",
            password_hash=hash_password("TestPass123!"),
            company_name="Test Corp",
            subscription_tier=SubscriptionTier.FREE,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=365),
            monthly_posts_used=2,
            featured_posts_used=0,
        )
        db_session.add(employer)
        db_session.commit()
        
        # Login to get token
        from app.core.security import create_access_token
        access_token = create_access_token({
            "sub": str(employer.id),
            "role": "employer"
        })
        
        # Update subscription
        response = client.post(
            "/api/subscription/update",
            json={"new_tier": "premium"},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["tier"] == "premium"
        assert data["monthly_posts_used"] == 0  # Reset
        assert data["featured_posts_used"] == 0  # Reset
        assert "message" in data
    
    def test_update_subscription_resets_counters(self, client, db_session: Session):
        """Test subscription update resets usage counters."""
        from app.core.security import hash_password, create_access_token
        
        employer = Employer(
            id=uuid4(),
            email="employer@test.com",
            password_hash=hash_password("TestPass123!"),
            company_name="Test Corp",
            subscription_tier=SubscriptionTier.BASIC,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=15,
            featured_posts_used=2,
        )
        db_session.add(employer)
        db_session.commit()
        
        access_token = create_access_token({
            "sub": str(employer.id),
            "role": "employer"
        })
        
        # Update subscription
        response = client.post(
            "/api/subscription/update",
            json={"new_tier": "premium"},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        
        # Verify counters were reset
        db_session.refresh(employer)
        assert employer.monthly_posts_used == 0
        assert employer.featured_posts_used == 0


class TestMonthlyQuotaReset:
    """Test monthly quota reset Celery task."""
    
    def test_reset_monthly_quotas_task(self, db_session: Session):
        """Test monthly quota reset task resets expired subscriptions."""
        # Create employers with expired billing cycles
        employer1 = Employer(
            id=uuid4(),
            email="employer1@test.com",
            password_hash="hashed",
            company_name="Corp 1",
            subscription_tier=SubscriptionTier.BASIC,
            subscription_start_date=datetime.utcnow() - timedelta(days=60),
            subscription_end_date=datetime.utcnow() - timedelta(days=1),  # Expired
            monthly_posts_used=15,
            featured_posts_used=2,
        )
        
        employer2 = Employer(
            id=uuid4(),
            email="employer2@test.com",
            password_hash="hashed",
            company_name="Corp 2",
            subscription_tier=SubscriptionTier.FREE,
            subscription_start_date=datetime.utcnow() - timedelta(days=35),
            subscription_end_date=datetime.utcnow() - timedelta(days=5),  # Expired
            monthly_posts_used=3,
            featured_posts_used=0,
        )
        
        # Employer with active subscription (should not be reset)
        employer3 = Employer(
            id=uuid4(),
            email="employer3@test.com",
            password_hash="hashed",
            company_name="Corp 3",
            subscription_tier=SubscriptionTier.PREMIUM,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=25),  # Active
            monthly_posts_used=50,
            featured_posts_used=5,
        )
        
        db_session.add_all([employer1, employer2, employer3])
        db_session.commit()
        
        # Mock the task's database session
        with patch('app.tasks.subscription_tasks.SessionLocal', return_value=db_session):
            # Run the task
            result = reset_monthly_quotas()
        
        assert result["status"] == "success"
        assert result["employers_reset"] == 2  # Only 2 expired
        
        # Verify counters were reset for expired employers
        db_session.refresh(employer1)
        db_session.refresh(employer2)
        db_session.refresh(employer3)
        
        assert employer1.monthly_posts_used == 0
        assert employer1.featured_posts_used == 0
        assert employer1.subscription_end_date > datetime.utcnow()
        
        assert employer2.monthly_posts_used == 0
        assert employer2.featured_posts_used == 0
        assert employer2.subscription_end_date > datetime.utcnow()
        
        # Active employer should not be reset
        assert employer3.monthly_posts_used == 50
        assert employer3.featured_posts_used == 5


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_cache_key_generation(self):
        """Test cache key format."""
        employer_id = uuid4()
        cache_key = _get_cache_key(employer_id)
        
        assert cache_key == f"subscription:{employer_id}"
    
    def test_invalidate_cache_handles_errors(self):
        """Test cache invalidation handles Redis errors gracefully."""
        redis_mock = Mock()
        redis_mock.delete.side_effect = Exception("Redis error")
        
        # Should not raise exception
        _invalidate_subscription_cache(redis_mock, uuid4())
    
    def test_check_quota_handles_cache_errors(self, db_session: Session):
        """Test quota check handles cache errors gracefully."""
        employer = Employer(
            id=uuid4(),
            email="test@example.com",
            password_hash="hashed",
            company_name="Test Corp",
            subscription_tier=SubscriptionTier.FREE,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=0,
            featured_posts_used=0,
        )
        db_session.add(employer)
        db_session.commit()
        
        # Mock Redis with error
        redis_mock = Mock()
        redis_mock.get.side_effect = Exception("Redis error")
        
        # Should fall back to database query
        result = check_quota(db_session, redis_mock, employer.id, "monthly_posts")
        
        assert result is True
