"""
Rate limiting middleware and utilities for API protection.

This module implements rate limiting using Redis to track request counts
per user per minute. Supports tier-based rate limits and provides
monitoring capabilities.

Implements Requirements 14.1, 14.2, 14.4, 14.5, 14.6
"""
from typing import Optional, Callable
from datetime import datetime
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from redis import Redis

from app.core.config import settings
from app.core.redis import redis_client
from app.core.logging import logger
from app.models.employer import SubscriptionTier


# Rate limit configuration by subscription tier
RATE_LIMITS = {
    "standard": 100,  # Free tier and unauthenticated users
    SubscriptionTier.FREE: 100,
    SubscriptionTier.BASIC: 200,
    SubscriptionTier.PREMIUM: 500,
}


def get_rate_limit_for_tier(tier: Optional[SubscriptionTier]) -> int:
    """
    Get rate limit for subscription tier.
    
    Implements Requirement 14.5: Premium tier gets higher rate limits
    
    Args:
        tier: Subscription tier or None for unauthenticated users
        
    Returns:
        Rate limit (requests per minute)
    """
    if tier is None:
        return RATE_LIMITS["standard"]
    return RATE_LIMITS.get(tier, RATE_LIMITS["standard"])


def get_rate_limit_key(user_id: str, window_start: int) -> str:
    """
    Generate Redis key for rate limiting.
    
    Args:
        user_id: User identifier (or IP address for unauthenticated)
        window_start: Unix timestamp of window start (minute precision)
        
    Returns:
        Redis key in format "rate_limit:{user_id}:{window_start}"
    """
    return f"rate_limit:{user_id}:{window_start}"


def get_violation_log_key(user_id: str) -> str:
    """
    Generate Redis key for rate limit violation logging.
    
    Args:
        user_id: User identifier
        
    Returns:
        Redis key in format "rate_limit_violations:{user_id}"
    """
    return f"rate_limit_violations:{user_id}"


async def check_rate_limit(
    redis: Redis,
    user_id: str,
    tier: Optional[SubscriptionTier] = None
) -> tuple[bool, int, int]:
    """
    Check if user has exceeded rate limit.
    
    Implements Requirements 14.1 and 14.2:
    - Track request count per user per minute
    - Reject requests exceeding limit with HTTP 429
    
    Args:
        redis: Redis client instance
        user_id: User identifier (user ID or IP address)
        tier: Subscription tier for tier-based limits
        
    Returns:
        Tuple of (allowed, current_count, limit)
        - allowed: True if request is allowed, False if rate limit exceeded
        - current_count: Current request count in this window
        - limit: Rate limit for this user
    """
    # Get rate limit for tier
    limit = get_rate_limit_for_tier(tier)
    
    # Get current minute window (Unix timestamp truncated to minute)
    now = datetime.utcnow()
    window_start = int(now.timestamp() // 60 * 60)
    
    # Generate Redis key
    key = get_rate_limit_key(user_id, window_start)
    
    try:
        # Increment counter and get current value
        current_count = redis.incr(key)
        
        # Set expiration on first request in window (2 minutes to be safe)
        if current_count == 1:
            redis.expire(key, 120)
        
        # Check if limit exceeded
        allowed = current_count <= limit
        
        logger.debug(
            f"Rate limit check for {user_id}: {current_count}/{limit} (tier: {tier})"
        )
        
        return allowed, current_count, limit
        
    except Exception as e:
        logger.error(f"Rate limit check error for {user_id}: {e}")
        # On error, allow request (fail open)
        return True, 0, limit


async def log_rate_limit_violation(
    redis: Redis,
    user_id: str,
    request_path: str,
    current_count: int,
    limit: int
) -> None:
    """
    Log rate limit violation for monitoring.
    
    Implements Requirement 14.6: Log rate limit violations for admin review
    
    Args:
        redis: Redis client instance
        user_id: User identifier
        request_path: Request path that was rate limited
        current_count: Current request count
        limit: Rate limit that was exceeded
    """
    try:
        # Create violation log entry
        violation_key = get_violation_log_key(user_id)
        timestamp = datetime.utcnow().isoformat()
        
        violation_data = {
            "timestamp": timestamp,
            "user_id": user_id,
            "path": request_path,
            "count": current_count,
            "limit": limit,
        }
        
        # Add to sorted set with timestamp as score
        redis.zadd(
            violation_key,
            {str(violation_data): datetime.utcnow().timestamp()}
        )
        
        # Keep only last 100 violations per user
        redis.zremrangebyrank(violation_key, 0, -101)
        
        # Set expiration (7 days)
        redis.expire(violation_key, 604800)
        
        # Log for immediate monitoring
        logger.warning(
            f"Rate limit violation: user={user_id}, path={request_path}, "
            f"count={current_count}, limit={limit}"
        )
        
        # Check for repeated violations (more than 5 in last hour)
        one_hour_ago = datetime.utcnow().timestamp() - 3600
        recent_violations = redis.zcount(violation_key, one_hour_ago, "+inf")
        
        if recent_violations >= 5:
            logger.error(
                f"ALERT: Repeated rate limit violations detected for user {user_id}: "
                f"{recent_violations} violations in last hour"
            )
        
    except Exception as e:
        logger.error(f"Error logging rate limit violation for {user_id}: {e}")


def get_retry_after_seconds() -> int:
    """
    Calculate retry-after value in seconds.
    
    Implements Requirement 14.4: Include retry-after header in response
    
    Returns:
        Seconds until next minute window (1-60 seconds)
    """
    now = datetime.utcnow()
    seconds_into_minute = now.second
    return 60 - seconds_into_minute


async def extract_user_identifier(request: Request) -> tuple[str, Optional[SubscriptionTier]]:
    """
    Extract user identifier and subscription tier from request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Tuple of (user_id, tier)
        - user_id: User ID from JWT or IP address for unauthenticated
        - tier: Subscription tier or None
    """
    # Try to get user from JWT token
    auth_header = request.headers.get("Authorization")
    
    if auth_header and auth_header.startswith("Bearer "):
        try:
            from jose import jwt
            from app.core.security import decode_token
            
            token = auth_header.split(" ")[1]
            payload = decode_token(token)
            
            user_id = payload.get("sub")
            role = payload.get("role")
            
            # Get subscription tier for employers
            tier = None
            if role == "employer" and user_id:
                # Try to get tier from cache or database
                tier = await get_user_subscription_tier(user_id)
            
            return user_id or request.client.host, tier
            
        except Exception as e:
            logger.debug(f"Could not extract user from token: {e}")
            # Fall through to IP-based identification
    
    # Use IP address for unauthenticated users
    return request.client.host, None


async def get_user_subscription_tier(user_id: str) -> Optional[SubscriptionTier]:
    """
    Get user's subscription tier from cache or database.
    
    Args:
        user_id: User UUID
        
    Returns:
        SubscriptionTier or None if not found
    """
    try:
        from app.core.redis import cache
        
        # Try cache first
        cache_key = f"subscription:{user_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data and isinstance(cached_data, dict):
            tier_value = cached_data.get("tier")
            if tier_value:
                return SubscriptionTier(tier_value)
        
        # If not in cache, return None (will use standard rate limit)
        # The subscription service will populate cache on next quota check
        return None
        
    except Exception as e:
        logger.debug(f"Could not get subscription tier for {user_id}: {e}")
        return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce API rate limiting.
    
    Implements Requirements 14.1, 14.2, 14.4, 14.5, 14.6:
    - Track request count per user per minute
    - Reject requests exceeding limit with HTTP 429
    - Include Retry-After header in response
    - Apply higher rate limits for premium tier employers
    - Log rate limit violations for admin review
    """
    
    # Paths exempt from rate limiting
    EXEMPT_PATHS = {
        "/health",
        "/",
        "/docs",
        "/openapi.json",
        "/redoc",
    }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting to requests."""
        # Skip rate limiting for exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)
        
        # Get Redis client
        redis = redis_client.get_cache_client()
        
        # Extract user identifier and tier
        user_id, tier = await extract_user_identifier(request)
        
        # Check rate limit
        allowed, current_count, limit = await check_rate_limit(redis, user_id, tier)
        
        if not allowed:
            # Rate limit exceeded
            retry_after = get_retry_after_seconds()
            
            # Log violation
            await log_rate_limit_violation(
                redis,
                user_id,
                request.url.path,
                current_count,
                limit
            )
            
            # Return 429 with Retry-After header
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "limit": limit,
                    "current": current_count,
                    "retry_after": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(retry_after),
                }
            )
        
        # Request allowed - add rate limit headers to response
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = max(0, limit - current_count)
        retry_after = get_retry_after_seconds()
        
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(retry_after)
        
        return response


async def get_rate_limit_violations(
    redis: Redis,
    user_id: str,
    limit: int = 100
) -> list[dict]:
    """
    Get recent rate limit violations for a user.
    
    Args:
        redis: Redis client instance
        user_id: User identifier
        limit: Maximum number of violations to return
        
    Returns:
        List of violation records
    """
    try:
        violation_key = get_violation_log_key(user_id)
        
        # Get recent violations (newest first)
        violations = redis.zrevrange(violation_key, 0, limit - 1, withscores=True)
        
        result = []
        for violation_str, timestamp in violations:
            try:
                import json
                violation_data = json.loads(violation_str)
                result.append(violation_data)
            except Exception:
                continue
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting rate limit violations for {user_id}: {e}")
        return []


async def get_all_violators(redis: Redis, hours: int = 24) -> list[str]:
    """
    Get list of users with rate limit violations in the last N hours.
    
    Args:
        redis: Redis client instance
        hours: Number of hours to look back
        
    Returns:
        List of user IDs with violations
    """
    try:
        # Scan for all violation keys
        pattern = "rate_limit_violations:*"
        violators = []
        
        for key in redis.scan_iter(match=pattern):
            # Extract user_id from key
            user_id = key.split(":")[-1]
            
            # Check if user has violations in time window
            cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)
            recent_count = redis.zcount(key, cutoff_time, "+inf")
            
            if recent_count > 0:
                violators.append(user_id)
        
        return violators
        
    except Exception as e:
        logger.error(f"Error getting all violators: {e}")
        return []
