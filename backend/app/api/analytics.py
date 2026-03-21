"""Analytics API endpoints."""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.dependencies import get_current_employer, get_current_admin
from app.services.analytics import get_analytics_service
from app.services.subscription import get_tier_limits
from app.models.employer import Employer, SubscriptionTier

router = APIRouter(tags=["analytics"])


@router.get("/analytics/scraping")
async def get_scraping_metrics(
    source_platform: Optional[str] = None,
    days: int = 7,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Get scraping metrics (admin only)."""
    analytics_service = get_analytics_service(db)
    metrics = analytics_service.get_scraping_metrics(
        source_platform=source_platform,
        days=days,
    )
    return metrics


@router.get("/analytics/searches/popular")
async def get_popular_searches(
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Get popular search terms."""
    analytics_service = get_analytics_service(db)
    searches = analytics_service.get_popular_searches(limit=limit)
    return {"popular_searches": searches}


@router.get("/analytics/jobs/{job_id}")
async def get_job_analytics(
    job_id: UUID,
    days: int = 30,
    db: Session = Depends(get_db),
    employer: Employer = Depends(get_current_employer),
):
    """Get analytics for a specific job (premium tier only)."""
    tier_limits = get_tier_limits(employer.subscription_tier)
    
    if not tier_limits.get("has_analytics", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analytics access requires premium subscription tier",
        )
    
    from app.models.job import Job
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    
    if job.employer_id != employer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view analytics for this job",
        )
    
    analytics_service = get_analytics_service(db)
    analytics = analytics_service.get_job_analytics(job_id=job_id, days=days)
    return analytics


@router.get("/analytics/employer/summary")
async def get_employer_analytics_summary(
    days: int = 30,
    db: Session = Depends(get_db),
    employer: Employer = Depends(get_current_employer),
):
    """Get aggregate analytics for all employer's jobs (premium tier only)."""
    tier_limits = get_tier_limits(employer.subscription_tier)
    
    if not tier_limits.get("has_analytics", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analytics access requires premium subscription tier",
        )
    
    analytics_service = get_analytics_service(db)
    analytics = analytics_service.get_employer_analytics(
        employer_id=employer.id,
        days=days,
    )
    return analytics


@router.get("/analytics/system/health")
async def get_system_health_metrics(
    metric_name: Optional[str] = None,
    hours: int = 24,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Get system health metrics (admin only)."""
    analytics_service = get_analytics_service(db)
    metrics = analytics_service.get_system_metrics(
        metric_name=metric_name,
        hours=hours,
    )
    return {"metrics": metrics}


@router.get("/analytics/api/slow-requests")
async def get_slow_api_requests(
    threshold_ms: float = 1000,
    hours: int = 24,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_current_admin),
):
    """Get slow API requests (admin only)."""
    analytics_service = get_analytics_service(db)
    requests = analytics_service.get_slow_requests(
        threshold_ms=threshold_ms,
        hours=hours,
        limit=limit,
    )
    return {"slow_requests": requests}
