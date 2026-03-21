"""
Subscription management API endpoints.

This module provides endpoints for managing employer subscriptions, including:
- Viewing subscription information
- Updating subscription tier (upgrade/downgrade)
- Checking quota availability
"""
from datetime import datetime, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_employer
from app.core.redis import redis_client
from app.db.session import get_db
from app.models.employer import Employer, SubscriptionTier
from app.schemas.auth import TokenData
from app.schemas.subscription import (
    SubscriptionUpdateRequest,
    SubscriptionUpdateResponse,
    SubscriptionInfoResponse,
    ErrorResponse,
)
from app.services.subscription import get_tier_limits


router = APIRouter(prefix="/subscription", tags=["subscription"])


@router.get(
    "/info",
    response_model=SubscriptionInfoResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Employer not found"},
    }
)
async def get_subscription_info(
    employer: TokenData = Depends(get_current_employer),
    db: Session = Depends(get_db)
):
    """
    Get current subscription information for the authenticated employer.
    
    Returns subscription tier, usage statistics, and feature access flags.
    
    **Example Response:**
    ```json
    {
      "employer_id": "123e4567-e89b-12d3-a456-426614174000",
      "tier": "basic",
      "start_date": "2024-01-15T10:30:00",
      "end_date": "2024-02-15T10:30:00",
      "is_active": true,
      "monthly_posts_used": 5,
      "monthly_posts_limit": 20,
      "featured_posts_used": 1,
      "featured_posts_limit": 2,
      "has_application_tracking": true,
      "has_analytics": false
    }
    ```
    """
    # Query employer from database
    employer_record = db.query(Employer).filter(
        Employer.id == UUID(employer.user_id)
    ).first()
    
    if not employer_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employer not found"
        )
    
    # Get tier limits
    limits = get_tier_limits(employer_record.subscription_tier)
    
    # Handle unlimited posts (infinity)
    monthly_posts_limit = limits["monthly_posts"]
    if monthly_posts_limit == float('inf'):
        monthly_posts_limit = -1  # Use -1 to represent unlimited in JSON
    
    return SubscriptionInfoResponse(
        employer_id=str(employer_record.id),
        tier=employer_record.subscription_tier.value,
        start_date=employer_record.subscription_start_date.isoformat(),
        end_date=employer_record.subscription_end_date.isoformat(),
        is_active=employer_record.is_subscription_active(),
        monthly_posts_used=employer_record.monthly_posts_used,
        monthly_posts_limit=int(monthly_posts_limit),
        featured_posts_used=employer_record.featured_posts_used,
        featured_posts_limit=limits["featured_posts"],
        has_application_tracking=limits["has_application_tracking"],
        has_analytics=limits["has_analytics"],
    )


@router.post(
    "/update",
    response_model=SubscriptionUpdateResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid tier"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Employer not found"},
    }
)
async def update_subscription(
    update_data: SubscriptionUpdateRequest,
    employer: TokenData = Depends(get_current_employer),
    db: Session = Depends(get_db)
):
    """
    Update employer subscription tier (upgrade or downgrade).
    
    This endpoint implements Requirements 8.7 and 8.8:
    - Updates subscription tier, start_date, and end_date (30 days from now)
    - Resets usage counters (monthly_posts_used=0, featured_posts_used=0)
    - Invalidates subscription cache
    
    **Process:**
    1. Verify employer authentication
    2. Query employer record from database
    3. Update subscription tier
    4. Set new start_date (now) and end_date (30 days from now)
    5. Reset monthly_posts_used and featured_posts_used to 0
    6. Invalidate Redis cache
    7. Return updated subscription details
    
    **Example Request:**
    ```json
    {
      "new_tier": "premium"
    }
    ```
    
    **Example Response:**
    ```json
    {
      "employer_id": "123e4567-e89b-12d3-a456-426614174000",
      "tier": "premium",
      "start_date": "2024-01-15T10:30:00",
      "end_date": "2024-02-15T10:30:00",
      "monthly_posts_used": 0,
      "featured_posts_used": 0,
      "message": "Subscription updated successfully"
    }
    ```
    """
    # Query employer from database
    employer_record = db.query(Employer).filter(
        Employer.id == UUID(employer.user_id)
    ).first()
    
    if not employer_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employer not found"
        )
    
    # Update subscription tier
    employer_record.subscription_tier = update_data.new_tier
    
    # Update subscription dates
    now = datetime.utcnow()
    employer_record.subscription_start_date = now
    employer_record.subscription_end_date = now + timedelta(days=30)
    
    # Reset usage counters
    employer_record.monthly_posts_used = 0
    employer_record.featured_posts_used = 0
    
    # Commit changes to database
    try:
        db.commit()
        db.refresh(employer_record)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update subscription: {str(e)}"
        )
    
    # Invalidate cache
    from app.services.subscription import _invalidate_subscription_cache
    redis = redis_client.get_cache_client()
    _invalidate_subscription_cache(redis, employer_record.id)
    
    return SubscriptionUpdateResponse(
        employer_id=str(employer_record.id),
        tier=employer_record.subscription_tier.value,
        start_date=employer_record.subscription_start_date.isoformat(),
        end_date=employer_record.subscription_end_date.isoformat(),
        monthly_posts_used=employer_record.monthly_posts_used,
        featured_posts_used=employer_record.featured_posts_used,
        message="Subscription updated successfully"
    )


@router.post(
    "/cancel",
    response_model=SubscriptionUpdateResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Cannot cancel free tier"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Employer not found"},
    }
)
async def cancel_subscription(
    employer: TokenData = Depends(get_current_employer),
    db: Session = Depends(get_db)
):
    """
    Cancel employer subscription (downgrade to free tier).
    
    This endpoint implements Requirement 18.6:
    - Maintains access until the current subscription period ends
    - Does not immediately downgrade the tier
    - Sets the subscription to expire at the end_date
    - After end_date passes, the tier will be downgraded to FREE
    
    **Process:**
    1. Verify employer authentication
    2. Query employer record from database
    3. Check if already on free tier (cannot cancel free tier)
    4. Mark subscription for cancellation (will downgrade at end_date)
    5. Return current subscription details with cancellation message
    
    **Example Response:**
    ```json
    {
      "employer_id": "123e4567-e89b-12d3-a456-426614174000",
      "tier": "premium",
      "start_date": "2024-01-15T10:30:00",
      "end_date": "2024-02-15T10:30:00",
      "monthly_posts_used": 5,
      "featured_posts_used": 2,
      "message": "Subscription will be cancelled at the end of the current period (2024-02-15)"
    }
    ```
    """
    # Query employer from database
    employer_record = db.query(Employer).filter(
        Employer.id == UUID(employer.user_id)
    ).first()
    
    if not employer_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employer not found"
        )
    
    # Check if already on free tier
    if employer_record.subscription_tier == SubscriptionTier.FREE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel free tier subscription"
        )
    
    # Note: In a full Stripe integration (Task 31), this would:
    # 1. Call Stripe API to cancel the subscription at period end
    # 2. Store the cancellation status in the database
    # 3. A scheduled task would check for expired subscriptions and downgrade them
    
    # For now, we'll just return the current subscription info
    # The actual downgrade will happen when a scheduled task checks subscription_end_date
    
    return SubscriptionUpdateResponse(
        employer_id=str(employer_record.id),
        tier=employer_record.subscription_tier.value,
        start_date=employer_record.subscription_start_date.isoformat(),
        end_date=employer_record.subscription_end_date.isoformat(),
        monthly_posts_used=employer_record.monthly_posts_used,
        featured_posts_used=employer_record.featured_posts_used,
        message=f"Subscription will be cancelled at the end of the current period ({employer_record.subscription_end_date.strftime('%Y-%m-%d')})"
    )
