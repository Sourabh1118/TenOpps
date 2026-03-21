"""
Subscription management service for the job aggregation platform.

This module provides functions for managing employer subscriptions, including:
- Subscription tier configuration and limits
- Quota checking and consumption
- Subscription caching in Redis
"""
from typing import Dict, Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from redis import Redis

from app.models.employer import Employer, SubscriptionTier
from app.core.logging import logger


# Subscription tier limits configuration
TIER_LIMITS = {
    SubscriptionTier.FREE: {
        "monthly_posts": 3,
        "featured_posts": 0,
        "url_imports": 5,  # Free tier gets 5 URL imports per month
        "has_application_tracking": False,
        "has_analytics": False,
    },
    SubscriptionTier.BASIC: {
        "monthly_posts": 20,
        "featured_posts": 2,
        "url_imports": 50,  # Basic tier gets 50 URL imports per month
        "has_application_tracking": True,
        "has_analytics": False,
    },
    SubscriptionTier.PREMIUM: {
        "monthly_posts": float('inf'),  # Unlimited
        "featured_posts": 10,
        "url_imports": float('inf'),  # Unlimited URL imports
        "has_application_tracking": True,
        "has_analytics": True,
    },
}


def get_tier_limits(tier: SubscriptionTier) -> Dict:
    """
    Get subscription tier limits and feature flags.
    
    This function implements Requirements 8.4, 8.5, and 8.6:
    - Free tier: 3 monthly posts, 0 featured posts
    - Basic tier: 20 monthly posts, 2 featured posts, application tracking
    - Premium tier: unlimited posts, 10 featured posts, application tracking, analytics
    
    Args:
        tier: Subscription tier enum value
        
    Returns:
        Dictionary with monthly_posts, featured_posts, has_application_tracking, has_analytics
        
    Example:
        >>> limits = get_tier_limits(SubscriptionTier.BASIC)
        >>> print(limits)
        {
            "monthly_posts": 20,
            "featured_posts": 2,
            "has_application_tracking": True,
            "has_analytics": False
        }
    """
    return TIER_LIMITS.get(tier, TIER_LIMITS[SubscriptionTier.FREE])


def _get_cache_key(employer_id: UUID) -> str:
    """
    Generate Redis cache key for subscription data.
    
    Args:
        employer_id: Employer UUID
        
    Returns:
        Cache key string in format "subscription:{employer_id}"
    """
    return f"subscription:{employer_id}"


def _get_cached_subscription(redis: Redis, employer_id: UUID) -> Optional[Dict]:
    """
    Retrieve cached subscription data from Redis.
    
    Args:
        redis: Redis client instance
        employer_id: Employer UUID
        
    Returns:
        Cached subscription data dict or None if not found
    """
    import json
    
    cache_key = _get_cache_key(employer_id)
    
    try:
        cached_data = redis.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
    except Exception as e:
        logger.error(f"Error retrieving cached subscription for {employer_id}: {e}")
    
    return None


def _cache_subscription(redis: Redis, employer_id: UUID, subscription_data: Dict, ttl: int = 300):
    """
    Cache subscription data in Redis with TTL.
    
    Args:
        redis: Redis client instance
        employer_id: Employer UUID
        subscription_data: Subscription data to cache
        ttl: Time to live in seconds (default: 300 = 5 minutes)
    """
    import json
    
    cache_key = _get_cache_key(employer_id)
    
    try:
        redis.setex(cache_key, ttl, json.dumps(subscription_data))
    except Exception as e:
        logger.error(f"Error caching subscription for {employer_id}: {e}")


def _invalidate_subscription_cache(redis: Redis, employer_id: UUID):
    """
    Invalidate cached subscription data.
    
    Args:
        redis: Redis client instance
        employer_id: Employer UUID
    """
    cache_key = _get_cache_key(employer_id)
    
    try:
        redis.delete(cache_key)
        logger.info(f"Invalidated subscription cache for employer {employer_id}")
    except Exception as e:
        logger.error(f"Error invalidating subscription cache for {employer_id}: {e}")


def check_quota(db: Session, redis: Redis, employer_id: UUID, quota_type: str) -> bool:
    """
    Check if employer has available quota for the specified action.
    
    This function implements Requirements 4.2, 5.5, 8.2, and 8.3:
    - Queries employer subscription and usage from database
    - Compares usage against tier limits
    - Caches subscription data in Redis for 5 minutes
    
    Args:
        db: Database session
        redis: Redis client instance
        employer_id: Employer UUID
        quota_type: Type of quota to check ("monthly_posts", "featured_posts", or "url_import")
        
    Returns:
        True if quota is available, False otherwise
        
    Raises:
        ValueError: If quota_type is invalid
        
    Example:
        >>> can_post = check_quota(db, redis, employer_id, "monthly_posts")
        >>> if can_post:
        ...     # Create job post
    """
    if quota_type not in ["monthly_posts", "featured_posts", "url_import"]:
        raise ValueError(f"Invalid quota_type: {quota_type}. Must be 'monthly_posts', 'featured_posts', or 'url_import'")
    
    # Try to get cached subscription data
    cached_data = _get_cached_subscription(redis, employer_id)
    
    if cached_data:
        logger.debug(f"Using cached subscription data for employer {employer_id}")
        tier = SubscriptionTier(cached_data["tier"])
        usage = cached_data["usage"]
        subscription_end_date = datetime.fromisoformat(cached_data["subscription_end_date"])
    else:
        # Query employer from database
        employer = db.query(Employer).filter(Employer.id == employer_id).first()
        
        if not employer:
            logger.warning(f"Employer {employer_id} not found")
            return False
        
        # Check if subscription is active
        if not employer.is_subscription_active():
            logger.warning(f"Employer {employer_id} subscription is inactive")
            return False
        
        tier = employer.subscription_tier
        usage = {
            "monthly_posts_used": employer.monthly_posts_used,
            "featured_posts_used": employer.featured_posts_used,
            "url_imports_used": employer.url_imports_used,
        }
        subscription_end_date = employer.subscription_end_date
        
        # Cache subscription data
        cache_data = {
            "tier": tier.value,
            "usage": usage,
            "subscription_end_date": subscription_end_date.isoformat(),
        }
        _cache_subscription(redis, employer_id, cache_data)
    
    # Get tier limits
    limits = get_tier_limits(tier)
    
    # Check quota based on type
    if quota_type == "monthly_posts":
        limit = limits["monthly_posts"]
        used = usage["monthly_posts_used"]
        
        # Handle unlimited (infinity)
        if limit == float('inf'):
            return True
        
        available = used < limit
        logger.info(f"Employer {employer_id} monthly posts: {used}/{limit}, available: {available}")
        return available
    
    elif quota_type == "featured_posts":
        limit = limits["featured_posts"]
        used = usage["featured_posts_used"]
        
        available = used < limit
        logger.info(f"Employer {employer_id} featured posts: {used}/{limit}, available: {available}")
        return available
    
    elif quota_type == "url_import":
        limit = limits["url_imports"]
        used = usage["url_imports_used"]
        
        # Handle unlimited (infinity)
        if limit == float('inf'):
            return True
        
        available = used < limit
        logger.info(f"Employer {employer_id} URL imports: {used}/{limit}, available: {available}")
        return available
    
    return False


def consume_quota(db: Session, redis: Redis, employer_id: UUID, quota_type: str) -> None:
    """
    Consume one unit of quota for the specified action.
    
    This function implements Requirements 4.9, 5.14, 8.10, and 11.4:
    - Increments monthly_posts_used, featured_posts_used, or url_imports_used in database
    - Invalidates subscription cache after update
    - Raises exception if quota is exceeded
    
    Args:
        db: Database session
        redis: Redis client instance
        employer_id: Employer UUID
        quota_type: Type of quota to consume ("monthly_posts", "featured_posts", or "url_import")
        
    Raises:
        ValueError: If quota_type is invalid
        RuntimeError: If quota is exceeded or employer not found
        
    Example:
        >>> try:
        ...     consume_quota(db, redis, employer_id, "monthly_posts")
        ...     # Quota consumed successfully
        ... except RuntimeError as e:
        ...     # Handle quota exceeded
    """
    if quota_type not in ["monthly_posts", "featured_posts", "url_import"]:
        raise ValueError(f"Invalid quota_type: {quota_type}. Must be 'monthly_posts', 'featured_posts', or 'url_import'")
    
    # Query employer from database
    employer = db.query(Employer).filter(Employer.id == employer_id).first()
    
    if not employer:
        raise RuntimeError(f"Employer {employer_id} not found")
    
    # Check if subscription is active
    if not employer.is_subscription_active():
        raise RuntimeError(f"Employer {employer_id} subscription is inactive")
    
    # Get tier limits
    limits = get_tier_limits(employer.subscription_tier)
    
    # Check and consume quota based on type
    if quota_type == "monthly_posts":
        limit = limits["monthly_posts"]
        
        # Handle unlimited (infinity)
        if limit != float('inf') and employer.monthly_posts_used >= limit:
            raise RuntimeError(f"Monthly post quota exceeded for employer {employer_id}")
        
        employer.monthly_posts_used += 1
        logger.info(f"Consumed monthly post quota for employer {employer_id}: {employer.monthly_posts_used}/{limit}")
    
    elif quota_type == "featured_posts":
        limit = limits["featured_posts"]
        
        if employer.featured_posts_used >= limit:
            raise RuntimeError(f"Featured post quota exceeded for employer {employer_id}")
        
        employer.featured_posts_used += 1
        logger.info(f"Consumed featured post quota for employer {employer_id}: {employer.featured_posts_used}/{limit}")
    
    elif quota_type == "url_import":
        limit = limits["url_imports"]
        
        # Handle unlimited (infinity)
        if limit != float('inf') and employer.url_imports_used >= limit:
            raise RuntimeError(f"URL import quota exceeded for employer {employer_id}")
        
        employer.url_imports_used += 1
        logger.info(f"Consumed URL import quota for employer {employer_id}: {employer.url_imports_used}/{limit}")
    
    # Commit changes to database
    try:
        db.commit()
        db.refresh(employer)
    except Exception as e:
        db.rollback()
        logger.error(f"Error consuming quota for employer {employer_id}: {e}")
        raise RuntimeError(f"Failed to consume quota: {e}")
    
    # Invalidate cache after update
    _invalidate_subscription_cache(redis, employer_id)
