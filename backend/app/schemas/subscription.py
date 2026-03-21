"""
Subscription management schemas for the job aggregation platform.

This module defines Pydantic models for subscription-related requests and responses.
"""
from typing import Optional
from pydantic import BaseModel, Field
from app.models.employer import SubscriptionTier


class SubscriptionUpdateRequest(BaseModel):
    """
    Request schema for updating employer subscription tier.
    
    Used for subscription upgrade/downgrade operations.
    """
    new_tier: SubscriptionTier = Field(..., description="New subscription tier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "new_tier": "premium"
            }
        }


class SubscriptionUpdateResponse(BaseModel):
    """
    Response schema for successful subscription update.
    
    Returns updated subscription details.
    """
    employer_id: str = Field(..., description="Employer UUID")
    tier: str = Field(..., description="New subscription tier")
    start_date: str = Field(..., description="Subscription start date (ISO format)")
    end_date: str = Field(..., description="Subscription end date (ISO format)")
    monthly_posts_used: int = Field(..., description="Monthly posts used (reset to 0)")
    featured_posts_used: int = Field(..., description="Featured posts used (reset to 0)")
    message: str = Field(..., description="Success message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "employer_id": "123e4567-e89b-12d3-a456-426614174000",
                "tier": "premium",
                "start_date": "2024-01-15T10:30:00",
                "end_date": "2024-02-15T10:30:00",
                "monthly_posts_used": 0,
                "featured_posts_used": 0,
                "message": "Subscription updated successfully"
            }
        }


class SubscriptionInfoResponse(BaseModel):
    """
    Response schema for subscription information.
    
    Returns current subscription details and usage.
    """
    employer_id: str = Field(..., description="Employer UUID")
    tier: str = Field(..., description="Current subscription tier")
    start_date: str = Field(..., description="Subscription start date (ISO format)")
    end_date: str = Field(..., description="Subscription end date (ISO format)")
    is_active: bool = Field(..., description="Whether subscription is currently active")
    monthly_posts_used: int = Field(..., description="Monthly posts used")
    monthly_posts_limit: int = Field(..., description="Monthly posts limit")
    featured_posts_used: int = Field(..., description="Featured posts used")
    featured_posts_limit: int = Field(..., description="Featured posts limit")
    has_application_tracking: bool = Field(..., description="Application tracking feature access")
    has_analytics: bool = Field(..., description="Analytics feature access")
    
    class Config:
        json_schema_extra = {
            "example": {
                "employer_id": "123e4567-e89b-12d3-a456-426614174000",
                "tier": "basic",
                "start_date": "2024-01-15T10:30:00",
                "end_date": "2024-02-15T10:30:00",
                "is_active": True,
                "monthly_posts_used": 5,
                "monthly_posts_limit": 20,
                "featured_posts_used": 1,
                "featured_posts_limit": 2,
                "has_application_tracking": True,
                "has_analytics": False
            }
        }


class ErrorResponse(BaseModel):
    """
    Error response schema for subscription endpoints.
    """
    detail: str = Field(..., description="Error message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Subscription quota exceeded"
            }
        }
