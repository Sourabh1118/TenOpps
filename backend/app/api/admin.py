"""
Admin API endpoints for system monitoring and management.

This module provides admin-only endpoints for:
- Rate limit violation monitoring
- System health checks
- User management
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime

from app.api.dependencies import get_current_admin
from app.schemas.auth import TokenData
from app.core.redis import redis_client
from app.core.rate_limiting import (
    get_rate_limit_violations,
    get_all_violators,
)
from app.core.logging import logger


router = APIRouter(prefix="/admin", tags=["admin"])


class RateLimitViolation(BaseModel):
    """Rate limit violation record."""
    timestamp: str
    user_id: str
    path: str
    count: int
    limit: int


class RateLimitViolationsResponse(BaseModel):
    """Response for rate limit violations query."""
    user_id: str
    violations: List[RateLimitViolation]
    total_count: int


class ViolatorsResponse(BaseModel):
    """Response for violators list."""
    violators: List[str]
    total_count: int
    time_window_hours: int


class RateLimitStatsResponse(BaseModel):
    """Response for rate limit statistics."""
    total_violators: int
    time_window_hours: int
    top_violators: List[dict]


@router.get(
    "/rate-limit/violations/{user_id}",
    response_model=RateLimitViolationsResponse,
    summary="Get rate limit violations for a user"
)
async def get_user_violations(
    user_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of violations to return"),
    admin: TokenData = Depends(get_current_admin)
):
    """
    Get rate limit violations for a specific user.
    
    Implements Requirement 14.6: Log rate limit violations for admin review
    
    This endpoint allows administrators to review rate limit violations
    for a specific user to identify abuse patterns.
    
    Args:
        user_id: User identifier (UUID or IP address)
        limit: Maximum number of violations to return (default: 100)
        admin: Admin user from authentication
        
    Returns:
        List of rate limit violations with timestamps and details
    """
    try:
        redis = redis_client.get_cache_client()
        violations = await get_rate_limit_violations(redis, user_id, limit)
        
        logger.info(
            f"Admin {admin.user_id} retrieved {len(violations)} violations for user {user_id}"
        )
        
        return RateLimitViolationsResponse(
            user_id=user_id,
            violations=[RateLimitViolation(**v) for v in violations],
            total_count=len(violations)
        )
        
    except Exception as e:
        logger.error(f"Error retrieving violations for {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve rate limit violations"
        )


@router.get(
    "/rate-limit/violators",
    response_model=ViolatorsResponse,
    summary="Get list of users with rate limit violations"
)
async def get_violators(
    hours: int = Query(24, ge=1, le=168, description="Time window in hours"),
    admin: TokenData = Depends(get_current_admin)
):
    """
    Get list of users with rate limit violations in the specified time window.
    
    Implements Requirement 14.6: Alert admins for repeated violations
    
    This endpoint allows administrators to identify users who have
    violated rate limits recently, enabling proactive abuse prevention.
    
    Args:
        hours: Time window in hours (default: 24, max: 168 = 1 week)
        admin: Admin user from authentication
        
    Returns:
        List of user IDs with violations in the time window
    """
    try:
        redis = redis_client.get_cache_client()
        violators = await get_all_violators(redis, hours)
        
        logger.info(
            f"Admin {admin.user_id} retrieved {len(violators)} violators "
            f"in last {hours} hours"
        )
        
        return ViolatorsResponse(
            violators=violators,
            total_count=len(violators),
            time_window_hours=hours
        )
        
    except Exception as e:
        logger.error(f"Error retrieving violators: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve violators list"
        )


@router.get(
    "/rate-limit/stats",
    response_model=RateLimitStatsResponse,
    summary="Get rate limit statistics"
)
async def get_rate_limit_stats(
    hours: int = Query(24, ge=1, le=168, description="Time window in hours"),
    top_n: int = Query(10, ge=1, le=100, description="Number of top violators to return"),
    admin: TokenData = Depends(get_current_admin)
):
    """
    Get rate limit statistics including top violators.
    
    Implements Requirement 14.6: Alert admins for repeated violations
    
    This endpoint provides aggregate statistics about rate limit violations,
    helping administrators identify patterns and potential abuse.
    
    Args:
        hours: Time window in hours (default: 24)
        top_n: Number of top violators to return (default: 10)
        admin: Admin user from authentication
        
    Returns:
        Statistics including total violators and top violators with counts
    """
    try:
        redis = redis_client.get_cache_client()
        
        # Get all violators
        violators = await get_all_violators(redis, hours)
        
        # Get violation counts for each violator
        violator_counts = []
        cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)
        
        for user_id in violators:
            violation_key = f"rate_limit_violations:{user_id}"
            count = redis.zcount(violation_key, cutoff_time, "+inf")
            violator_counts.append({
                "user_id": user_id,
                "violation_count": count
            })
        
        # Sort by violation count and get top N
        violator_counts.sort(key=lambda x: x["violation_count"], reverse=True)
        top_violators = violator_counts[:top_n]
        
        logger.info(
            f"Admin {admin.user_id} retrieved rate limit stats: "
            f"{len(violators)} violators in last {hours} hours"
        )
        
        return RateLimitStatsResponse(
            total_violators=len(violators),
            time_window_hours=hours,
            top_violators=top_violators
        )
        
    except Exception as e:
        logger.error(f"Error retrieving rate limit stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve rate limit statistics"
        )


@router.delete(
    "/rate-limit/violations/{user_id}",
    summary="Clear rate limit violations for a user"
)
async def clear_user_violations(
    user_id: str,
    admin: TokenData = Depends(get_current_admin)
):
    """
    Clear rate limit violation history for a user.
    
    This endpoint allows administrators to clear violation history
    for users after reviewing and addressing the issue.
    
    Args:
        user_id: User identifier (UUID or IP address)
        admin: Admin user from authentication
        
    Returns:
        Success message
    """
    try:
        redis = redis_client.get_cache_client()
        violation_key = f"rate_limit_violations:{user_id}"
        
        # Delete violation history
        redis.delete(violation_key)
        
        logger.info(
            f"Admin {admin.user_id} cleared rate limit violations for user {user_id}"
        )
        
        return {
            "message": f"Rate limit violations cleared for user {user_id}",
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"Error clearing violations for {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear rate limit violations"
        )
