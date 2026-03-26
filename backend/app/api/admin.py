"""
Admin API endpoints for system monitoring and management.

This module provides admin-only endpoints for:
- Rate limit violation monitoring
- System health checks
- User management
- Platform statistics
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.dependencies import get_current_admin
from app.schemas.auth import TokenData
from app.core.redis import redis_client
from app.core.rate_limiting import (
    get_rate_limit_violations,
    get_all_violators,
)
from app.core.logging import logger
from app.db.session import get_db
from app.models.admin import Admin
from app.models.employer import Employer
from app.models.job_seeker import JobSeeker
from app.models.job import Job
from app.models.application import Application


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



class PlatformStatsResponse(BaseModel):
    """Response for platform statistics."""
    total_users: int
    total_employers: int
    total_job_seekers: int
    total_jobs: int
    total_applications: int
    active_jobs: int
    jobs_posted_today: int
    applications_today: int


class UserListItem(BaseModel):
    """User list item."""
    id: str
    email: str
    role: str
    created_at: datetime
    full_name: Optional[str] = None
    company_name: Optional[str] = None


class UsersListResponse(BaseModel):
    """Response for users list."""
    users: List[UserListItem]
    total: int
    page: int
    limit: int


@router.get(
    "/stats",
    response_model=PlatformStatsResponse,
    summary="Get platform statistics"
)
async def get_platform_stats(
    admin: TokenData = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get platform-wide statistics.
    
    Returns aggregate statistics about users, jobs, and applications
    across the entire platform.
    
    Args:
        admin: Admin user from authentication
        db: Database session
        
    Returns:
        Platform statistics including user counts, job counts, and activity metrics
    """
    try:
        # Count users
        total_employers = db.query(func.count(Employer.id)).scalar() or 0
        total_job_seekers = db.query(func.count(JobSeeker.id)).scalar() or 0
        total_admins = db.query(func.count(Admin.id)).scalar() or 0
        total_users = total_employers + total_job_seekers + total_admins
        
        # Count jobs
        total_jobs = db.query(func.count(Job.id)).scalar() or 0
        active_jobs = db.query(func.count(Job.id)).filter(
            Job.status == 'active'
        ).scalar() or 0
        
        # Count jobs posted today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        jobs_posted_today = db.query(func.count(Job.id)).filter(
            Job.created_at >= today_start
        ).scalar() or 0
        
        # Count applications
        total_applications = db.query(func.count(Application.id)).scalar() or 0
        applications_today = db.query(func.count(Application.id)).filter(
            Application.created_at >= today_start
        ).scalar() or 0
        
        logger.info(f"Admin {admin.user_id} retrieved platform statistics")
        
        return PlatformStatsResponse(
            total_users=total_users,
            total_employers=total_employers,
            total_job_seekers=total_job_seekers,
            total_jobs=total_jobs,
            total_applications=total_applications,
            active_jobs=active_jobs,
            jobs_posted_today=jobs_posted_today,
            applications_today=applications_today
        )
        
    except Exception as e:
        logger.error(f"Error retrieving platform stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve platform statistics"
        )


@router.get(
    "/users",
    response_model=UsersListResponse,
    summary="Get all users"
)
async def get_users(
    role: Optional[str] = Query(None, description="Filter by role: admin, employer, job_seeker"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    admin: TokenData = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get list of all users with pagination and filtering.
    
    Args:
        role: Optional role filter (admin, employer, job_seeker)
        page: Page number (default: 1)
        limit: Items per page (default: 50, max: 100)
        admin: Admin user from authentication
        db: Database session
        
    Returns:
        Paginated list of users with their basic information
    """
    try:
        users = []
        offset = (page - 1) * limit
        
        # Get admins
        if not role or role == 'admin':
            admins = db.query(Admin).offset(offset if not role else 0).limit(limit if not role else None).all()
            for a in admins:
                users.append(UserListItem(
                    id=str(a.id),
                    email=a.email,
                    role='admin',
                    created_at=a.created_at,
                    full_name=a.full_name
                ))
        
        # Get employers
        if not role or role == 'employer':
            employers = db.query(Employer).offset(offset if not role else 0).limit(limit if not role else None).all()
            for e in employers:
                users.append(UserListItem(
                    id=str(e.id),
                    email=e.email,
                    role='employer',
                    created_at=e.created_at,
                    company_name=e.company_name
                ))
        
        # Get job seekers
        if not role or role == 'job_seeker':
            job_seekers = db.query(JobSeeker).offset(offset if not role else 0).limit(limit if not role else None).all()
            for js in job_seekers:
                users.append(UserListItem(
                    id=str(js.id),
                    email=js.email,
                    role='job_seeker',
                    created_at=js.created_at,
                    full_name=js.full_name
                ))
        
        # Sort by created_at descending
        users.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination if no role filter
        if not role:
            users = users[offset:offset + limit]
        
        # Count total
        total = 0
        if not role:
            total = (db.query(func.count(Admin.id)).scalar() or 0) + \
                    (db.query(func.count(Employer.id)).scalar() or 0) + \
                    (db.query(func.count(JobSeeker.id)).scalar() or 0)
        elif role == 'admin':
            total = db.query(func.count(Admin.id)).scalar() or 0
        elif role == 'employer':
            total = db.query(func.count(Employer.id)).scalar() or 0
        elif role == 'job_seeker':
            total = db.query(func.count(JobSeeker.id)).scalar() or 0
        
        logger.info(f"Admin {admin.user_id} retrieved users list (role={role}, page={page})")
        
        return UsersListResponse(
            users=users,
            total=total,
            page=page,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error retrieving users list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users list"
        )


# ──────────────────────────────────────────────────────────────
# Jobs Management
# ──────────────────────────────────────────────────────────────

class JobListItem(BaseModel):
    id: str
    title: str
    company: str
    location: str
    status: str
    source_platform: Optional[str] = None
    source_type: str
    posted_at: Optional[datetime] = None
    created_at: datetime
    application_count: int = 0
    view_count: int = 0


class JobsListResponse(BaseModel):
    jobs: List[JobListItem]
    total: int
    page: int
    limit: int


@router.get("/jobs", response_model=JobsListResponse, summary="Get all jobs (admin)")
async def get_admin_jobs(
    search: Optional[str] = Query(None, description="Search by title or company"),
    status_filter: Optional[str] = Query(None, alias="status", description="active, expired, all"),
    source: Optional[str] = Query(None, description="Filter by source platform"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    admin: TokenData = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get paginated list of all jobs for admin management."""
    try:
        query = db.query(Job)
        if search:
            query = query.filter(
                (Job.title.ilike(f"%{search}%")) | (Job.company.ilike(f"%{search}%"))
            )
        if status_filter and status_filter != "all":
            query = query.filter(Job.status == status_filter)
        if source:
            query = query.filter(Job.source_platform == source)

        total = query.count()
        offset = (page - 1) * limit
        jobs = query.order_by(Job.created_at.desc()).offset(offset).limit(limit).all()

        return JobsListResponse(
            jobs=[
                JobListItem(
                    id=str(j.id),
                    title=j.title,
                    company=j.company,
                    location=j.location,
                    status=j.status,
                    source_platform=j.source_platform,
                    source_type=j.source_type.value if hasattr(j.source_type, "value") else str(j.source_type),
                    posted_at=j.posted_at,
                    created_at=j.created_at,
                    application_count=j.application_count or 0,
                    view_count=j.view_count or 0,
                )
                for j in jobs
            ],
            total=total,
            page=page,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error retrieving jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve jobs")


@router.patch("/jobs/{job_id}/status", summary="Update job status (activate/deactivate)")
async def update_job_status(
    job_id: str,
    body: dict,
    admin: TokenData = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Activate or deactivate a job posting."""
    from uuid import UUID
    job = db.query(Job).filter(Job.id == UUID(job_id)).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    new_status = body.get("status", "active")
    job.status = new_status
    db.commit()
    logger.info(f"Admin {admin.user_id} set job {job_id} status to {new_status}")
    return {"message": f"Job status updated to {new_status}", "job_id": job_id}


# ──────────────────────────────────────────────────────────────
# Scraping Monitor
# ──────────────────────────────────────────────────────────────

SCRAPING_SOURCES = ["linkedin", "indeed", "naukri", "monster"]


class ScrapingSourceStatus(BaseModel):
    source: str
    circuit_open: bool
    failure_count: int
    cooldown_seconds: Optional[int] = None


class ScrapingStatusResponse(BaseModel):
    sources: List[ScrapingSourceStatus]
    recent_tasks: List[dict]


@router.get("/scraping/status", response_model=ScrapingStatusResponse, summary="Get scraping system status")
async def get_scraping_status(
    admin: TokenData = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get circuit breaker status and recent task history for all scraping sources."""
    try:
        redis = redis_client.get_cache_client()
        sources = []
        for source in SCRAPING_SOURCES:
            circuit_key = f"circuit_breaker:{source}:open"
            failure_key = f"circuit_breaker:{source}:failures"
            circuit_open = redis.exists(circuit_key) > 0
            failure_count = int(redis.get(failure_key) or 0)
            cooldown = redis.ttl(circuit_key) if circuit_open else None
            sources.append(ScrapingSourceStatus(
                source=source,
                circuit_open=circuit_open,
                failure_count=failure_count,
                cooldown_seconds=cooldown if cooldown and cooldown > 0 else None
            ))

        from app.models.scraping_task import ScrapingTask as ScrapingTaskModel
        recent = db.query(ScrapingTaskModel).order_by(
            ScrapingTaskModel.created_at.desc()
        ).limit(20).all()

        recent_tasks = [
            {
                "id": str(t.id),
                "task_type": t.task_type.value if hasattr(t.task_type, "value") else str(t.task_type),
                "source_platform": t.source_platform,
                "status": t.status.value if hasattr(t.status, "value") else str(t.status),
                "jobs_found": t.jobs_found or 0,
                "jobs_created": t.jobs_created or 0,
                "jobs_updated": t.jobs_updated or 0,
                "error_message": t.error_message,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            }
            for t in recent
        ]

        return ScrapingStatusResponse(sources=sources, recent_tasks=recent_tasks)
    except Exception as e:
        logger.error(f"Error retrieving scraping status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve scraping status")


@router.post("/scraping/trigger/{source}", summary="Manually trigger a scraping job")
async def trigger_scraping(
    source: str,
    admin: TokenData = Depends(get_current_admin)
):
    """Manually trigger a Celery scraping task for a given source."""
    if source not in SCRAPING_SOURCES:
        raise HTTPException(status_code=400, detail=f"Unknown source '{source}'. Valid: {SCRAPING_SOURCES}")
    try:
        from app.tasks.scraping_tasks import (
            scrape_linkedin_jobs, scrape_indeed_jobs, scrape_naukri_jobs, scrape_monster_jobs
        )
        task_map = {
            "linkedin": scrape_linkedin_jobs,
            "indeed": scrape_indeed_jobs,
            "naukri": scrape_naukri_jobs,
            "monster": scrape_monster_jobs,
        }
        task = task_map[source].delay()
        logger.info(f"Admin {admin.user_id} triggered manual scrape for {source}, task_id={task.id}")
        return {"message": f"Scraping task for '{source}' queued", "task_id": task.id}
    except Exception as e:
        logger.error(f"Error triggering scrape for {source}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger scraping: {str(e)}")
