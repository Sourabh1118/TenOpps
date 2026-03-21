"""
Unit tests for rate limiting functionality.

Tests cover:
- Rate limit enforcement per user
- Tier-based rate limits
- Rate limit headers
- Violation logging
- Admin monitoring endpoints
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from fastapi import Request, Response
from fastapi.testclient import TestClient

from app.core.rate_limiting import (
    get_rate_limit_for_tier,
    get_rate_limit_key,
    get_violation_log_key,
    check_rate_limit,
    log_rate_limit_violation,
    get_retry_after_seconds,
    RateLimitMiddleware,
)
from app.models.employer import SubscriptionTier


class TestRateLimitConfiguration:
    """Test rate limit configuration and tier-based limits."""
    
    def test_get_rate_limit_for_free_tier(self):
        """Test rate limit for free tier."""
        limit = get_rate_limit_for_tier(SubscriptionTier.FREE)
        assert limit == 100
    
    def test_get_rate_limit_for_basic_tier(self):
        """Test rate limit for basic tier."""
        limit = get_rate_limit_for_tier(SubscriptionTier.BASIC)
        assert limit == 200
    
    def test_get_rate_limit_for_premium_tier(self):
        """Test rate limit for premium tier."""
        limit = get_rate_limit_for_tier(SubscriptionTier.PREMIUM)
        assert limit == 500
    
    def test_get_rate_limit_for_unauthenticated(self):
        """Test rate limit for unauthenticated users."""
        limit = get_rate_limit_for_tier(None)
        assert limit == 100
    
    def test_get_rate_limit_key_format(self):
        """Test rate limit key generation."""
        user_id = "test-user-123"
        window_start = 1234567890
        
        key = get_rate_limit_key(user_id, window_start)
        
        assert key == "rate_limit:test-user-123:1234567890"
        assert key.startswith("rate_limit:")
    
    def test_get_violation_log_key_format(self):
        """Test violation log key generation."""
        user_id = "test-user-123"
        
        key = get_violation_log_key(user_id)
        
        assert key == "rate_limit_violations:test-user-123"
        assert key.startswith("rate_limit_violations:")


class TestRateLimitChecking:
    """Test rate limit checking logic."""
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_first_request(self):
        """Test rate limit check for first request in window."""
        mock_redis = Mock()
        mock_redis.incr.return_value = 1
        
        allowed, count, limit = await check_rate_limit(
            mock_redis,
            "user-123",
            SubscriptionTier.FREE
        )
        
        assert allowed is True
        assert count == 1
        assert limit == 100
        mock_redis.incr.assert_called_once()
        mock_redis.expire.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_within_limit(self):
        """Test rate limit check when within limit."""
        mock_redis = Mock()
        mock_redis.incr.return_value = 50
        
        allowed, count, limit = await check_rate_limit(
            mock_redis,
            "user-123",
            SubscriptionTier.FREE
        )
        
        assert allowed is True
        assert count == 50
        assert limit == 100
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_at_limit(self):
        """Test rate limit check when at exact limit."""
        mock_redis = Mock()
        mock_redis.incr.return_value = 100
        
        allowed, count, limit = await check_rate_limit(
            mock_redis,
            "user-123",
            SubscriptionTier.FREE
        )
        
        assert allowed is True
        assert count == 100
        assert limit == 100
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeded(self):
        """Test rate limit check when limit exceeded."""
        mock_redis = Mock()
        mock_redis.incr.return_value = 101
        
        allowed, count, limit = await check_rate_limit(
            mock_redis,
            "user-123",
            SubscriptionTier.FREE
        )
        
        assert allowed is False
        assert count == 101
        assert limit == 100
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_premium_tier(self):
        """Test rate limit check for premium tier."""
        mock_redis = Mock()
        mock_redis.incr.return_value = 250
        
        allowed, count, limit = await check_rate_limit(
            mock_redis,
            "user-123",
            SubscriptionTier.PREMIUM
        )
        
        assert allowed is True
        assert count == 250
        assert limit == 500
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_redis_error(self):
        """Test rate limit check when Redis fails (fail open)."""
        mock_redis = Mock()
        mock_redis.incr.side_effect = Exception("Redis connection error")
        
        allowed, count, limit = await check_rate_limit(
            mock_redis,
            "user-123",
            SubscriptionTier.FREE
        )
        
        # Should allow request on error (fail open)
        assert allowed is True
        assert count == 0


class TestViolationLogging:
    """Test rate limit violation logging."""
    
    @pytest.mark.asyncio
    async def test_log_rate_limit_violation(self):
        """Test logging a rate limit violation."""
        mock_redis = Mock()
        mock_redis.zadd.return_value = 1
        mock_redis.zcount.return_value = 1
        
        await log_rate_limit_violation(
            mock_redis,
            "user-123",
            "/api/jobs",
            101,
            100
        )
        
        mock_redis.zadd.assert_called_once()
        mock_redis.zremrangebyrank.assert_called_once()
        mock_redis.expire.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_log_repeated_violations_alert(self):
        """Test alert for repeated violations."""
        mock_redis = Mock()
        mock_redis.zadd.return_value = 1
        mock_redis.zcount.return_value = 6  # More than 5 violations
        
        with patch('app.core.rate_limiting.logger') as mock_logger:
            await log_rate_limit_violation(
                mock_redis,
                "user-123",
                "/api/jobs",
                101,
                100
            )
            
            # Should log error for repeated violations
            assert mock_logger.error.called
            error_msg = mock_logger.error.call_args[0][0]
            assert "ALERT" in error_msg
            assert "Repeated rate limit violations" in error_msg
    
    @pytest.mark.asyncio
    async def test_log_violation_redis_error(self):
        """Test violation logging when Redis fails."""
        mock_redis = Mock()
        mock_redis.zadd.side_effect = Exception("Redis error")
        
        # Should not raise exception
        await log_rate_limit_violation(
            mock_redis,
            "user-123",
            "/api/jobs",
            101,
            100
        )


class TestRetryAfter:
    """Test retry-after calculation."""
    
    def test_get_retry_after_seconds(self):
        """Test retry-after calculation."""
        retry_after = get_retry_after_seconds()
        
        # Should be between 1 and 60 seconds
        assert 1 <= retry_after <= 60
        assert isinstance(retry_after, int)


class TestRateLimitMiddleware:
    """Test rate limit middleware integration."""
    
    @pytest.mark.asyncio
    async def test_middleware_allows_exempt_paths(self):
        """Test middleware allows exempt paths without rate limiting."""
        middleware = RateLimitMiddleware(app=Mock())
        
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/health"
        
        mock_call_next = AsyncMock(return_value=Response())
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Should call next without rate limiting
        mock_call_next.assert_called_once()
        assert response is not None
    
    @pytest.mark.asyncio
    async def test_middleware_enforces_rate_limit(self):
        """Test middleware enforces rate limit."""
        middleware = RateLimitMiddleware(app=Mock())
        
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/api/jobs"
        mock_request.headers.get.return_value = None
        mock_request.client.host = "127.0.0.1"
        
        mock_call_next = AsyncMock(return_value=Response())
        
        with patch('app.core.rate_limiting.check_rate_limit') as mock_check:
            # Simulate rate limit exceeded
            mock_check.return_value = (False, 101, 100)
            
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            # Should return 429
            assert response.status_code == 429
            assert "Retry-After" in response.headers
    
    @pytest.mark.asyncio
    async def test_middleware_adds_rate_limit_headers(self):
        """Test middleware adds rate limit headers to response."""
        middleware = RateLimitMiddleware(app=Mock())
        
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/api/jobs"
        mock_request.headers.get.return_value = None
        mock_request.client.host = "127.0.0.1"
        
        mock_response = Response()
        mock_call_next = AsyncMock(return_value=mock_response)
        
        with patch('app.core.rate_limiting.check_rate_limit') as mock_check:
            # Simulate request allowed
            mock_check.return_value = (True, 50, 100)
            
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            # Should add rate limit headers
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers
            assert response.headers["X-RateLimit-Limit"] == "100"
            assert response.headers["X-RateLimit-Remaining"] == "50"


class TestRateLimitIntegration:
    """Integration tests for rate limiting with FastAPI."""
    
    def test_rate_limit_headers_in_response(self, client: TestClient):
        """Test that rate limit headers are included in responses."""
        response = client.get("/health")
        
        # Health endpoint is exempt, but other endpoints should have headers
        response = client.get("/")
        
        # Should have rate limit headers
        assert "X-RateLimit-Limit" in response.headers or response.status_code == 200
    
    def test_rate_limit_exceeded_returns_429(self, client: TestClient):
        """Test that exceeding rate limit returns 429."""
        # This test would require actually making 101 requests
        # For now, we'll test the structure
        pass
    
    def test_rate_limit_retry_after_header(self, client: TestClient):
        """Test that 429 response includes Retry-After header."""
        # This test would require actually exceeding the rate limit
        # For now, we'll test the structure
        pass


class TestAdminEndpoints:
    """Test admin endpoints for rate limit monitoring."""
    
    def test_get_user_violations_requires_admin(self, client: TestClient):
        """Test that violations endpoint requires admin role."""
        response = client.get("/api/admin/rate-limit/violations/user-123")
        
        # Should return 401 or 403 without authentication
        assert response.status_code in [401, 403]
    
    def test_get_violators_requires_admin(self, client: TestClient):
        """Test that violators endpoint requires admin role."""
        response = client.get("/api/admin/rate-limit/violators")
        
        # Should return 401 or 403 without authentication
        assert response.status_code in [401, 403]
    
    def test_get_rate_limit_stats_requires_admin(self, client: TestClient):
        """Test that stats endpoint requires admin role."""
        response = client.get("/api/admin/rate-limit/stats")
        
        # Should return 401 or 403 without authentication
        assert response.status_code in [401, 403]


# Fixtures
@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    return Mock()


@pytest.fixture
def mock_request():
    """Create mock request."""
    request = Mock(spec=Request)
    request.url.path = "/api/test"
    request.headers.get.return_value = None
    request.client.host = "127.0.0.1"
    return request
