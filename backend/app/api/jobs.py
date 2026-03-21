"""
Job API endpoints.

This module provides endpoints for job management including:
- Direct job posting by employers
- Job retrieval (single and by employer)
- Job updates
- Job deletion and status management
- View counter increment
"""
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.api.dependencies import get_current_employer
from app.core.redis import redis_client
from app.db.session import get_db
from app.models.job import Job, JobStatus, SourceType
from app.models.employer import Employer
from app.schemas.auth import TokenData
from app.schemas.job import (
    JobCreateRequest,
    JobUpdateRequest,
    JobResponse,
    JobListResponse,
    JobCreateResponse,
    JobReactivateRequest,
    ErrorResponse,
)
from app.services.subscription import check_quota, consume_quota
from app.services.quality_scoring import calculate_quality_score
from app.services.analytics import AnalyticsService
from app.core.logging import logger


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post(
    "/direct",
    response_model=JobCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Quota exceeded"},
    }
)
async def create_direct_job(
    job_data: JobCreateRequest,
    employer: TokenData = Depends(get_current_employer),
    db: Session = Depends(get_db)
):
    """
    Create a direct job posting.
    
    This endpoint implements Requirements 4.1-4.10:
    - Validates employer authentication token
    - Checks employer's posting quota
    - Creates job record with source_type='direct'
    - Calculates and assigns quality score
    - Consumes employer quota
    - Returns job ID on success
    
    **Process:**
    1. Validate employer authentication
    2. Check subscription quota for monthly posts
    3. Check featured post quota if featured=true
    4. Calculate quality score
    5. Create job record
    6. Consume quota
    7. Return job ID
    
    **Example Request:**
    ```json
    {
      "title": "Senior Python Developer",
      "company": "Tech Corp",
      "location": "San Francisco, CA",
      "remote": true,
      "job_type": "full_time",
      "experience_level": "senior",
      "description": "We are looking for an experienced Python developer...",
      "requirements": ["5+ years Python", "Django/FastAPI experience"],
      "responsibilities": ["Build APIs", "Mentor junior developers"],
      "salary_min": 120000,
      "salary_max": 180000,
      "salary_currency": "USD",
      "expires_at": "2024-03-15T00:00:00Z",
      "featured": false,
      "tags": ["python", "backend", "api"]
    }
    ```
    
    **Example Response:**
    ```json
    {
      "job_id": "123e4567-e89b-12d3-a456-426614174000",
      "message": "Job posted successfully"
    }
    ```
    """
    # Get Redis client for quota checking
    redis = redis_client.get_cache_client()
    employer_id = UUID(employer.user_id)
    
    # Check monthly posting quota
    has_quota = check_quota(db, redis, employer_id, "monthly_posts")
    if not has_quota:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Monthly posting quota exceeded. Please upgrade your subscription."
        )
    
    # Check featured post quota if featured
    if job_data.featured:
        has_featured_quota = check_quota(db, redis, employer_id, "featured_posts")
        if not has_featured_quota:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Featured post quota exceeded. Please upgrade your subscription."
            )
    
    # Prepare job data for quality scoring
    job_dict = {
        "title": job_data.title,
        "company": job_data.company,
        "description": job_data.description,
        "requirements": job_data.requirements or [],
        "responsibilities": job_data.responsibilities or [],
        "salary_min": job_data.salary_min,
        "salary_max": job_data.salary_max,
        "tags": job_data.tags or [],
    }
    
    # Calculate quality score
    quality_score = calculate_quality_score(
        source_type=SourceType.DIRECT,
        job_data=job_dict,
        posted_at=datetime.utcnow()
    )
    
    # Create job record
    new_job = Job(
        title=job_data.title,
        company=job_data.company,
        location=job_data.location,
        remote=job_data.remote,
        job_type=job_data.job_type,
        experience_level=job_data.experience_level,
        description=job_data.description,
        requirements=job_data.requirements,
        responsibilities=job_data.responsibilities,
        salary_min=job_data.salary_min,
        salary_max=job_data.salary_max,
        salary_currency=job_data.salary_currency,
        source_type=SourceType.DIRECT,
        employer_id=employer_id,
        quality_score=quality_score,
        status=JobStatus.ACTIVE,
        posted_at=datetime.utcnow(),
        expires_at=job_data.expires_at,
        featured=job_data.featured,
        tags=job_data.tags,
        application_count=0,
        view_count=0,
    )
    
    try:
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}"
        )
    
    # Consume quota
    try:
        consume_quota(db, redis, employer_id, "monthly_posts")
        if job_data.featured:
            consume_quota(db, redis, employer_id, "featured_posts")
    except RuntimeError as e:
        # Rollback job creation if quota consumption fails
        db.delete(new_job)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to consume quota: {str(e)}"
        )
    
    return JobCreateResponse(
        job_id=new_job.id,
        message="Job posted successfully"
    )


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Job not found"},
    }
)
async def get_job(
    job_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a single job by ID.
    
    This endpoint implements Requirement 9.1:
    - Fetches single job by ID
    - Includes application count and view count
    
    **Example Response:**
    ```json
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "Senior Python Developer",
      "company": "Tech Corp",
      "location": "San Francisco, CA",
      "remote": true,
      "job_type": "full_time",
      "experience_level": "senior",
      "description": "We are looking for...",
      "quality_score": 95.0,
      "status": "active",
      "application_count": 15,
      "view_count": 234,
      ...
    }
    ```
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Track job view (Requirement 19.4, 19.6)
    if job.employer_id:
        try:
            analytics = AnalyticsService(db)
            analytics.track_job_event(
                job_id=job.id,
                employer_id=job.employer_id,
                event_type="view",
            )
        except Exception as e:
            # Don't fail the request if analytics tracking fails
            logger.error(f"Error tracking job view: {e}")
    
    return JobResponse.model_validate(job)


@router.get(
    "/employer/{employer_id}",
    response_model=JobListResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    }
)
async def get_employer_jobs(
    employer_id: UUID,
    status_filter: Optional[JobStatus] = Query(None, description="Filter by job status"),
    employer: TokenData = Depends(get_current_employer),
    db: Session = Depends(get_db)
):
    """
    Get all jobs for a specific employer.
    
    This endpoint implements Requirements 9.2 and 9.3:
    - Fetches all jobs for employer
    - Includes application count and view count
    - Filters by status (active, expired, filled, deleted)
    
    **Query Parameters:**
    - status_filter: Optional filter by job status
    
    **Example Response:**
    ```json
    {
      "jobs": [...],
      "total": 25,
      "page": 1,
      "page_size": 25
    }
    ```
    """
    # Verify employer owns these jobs
    if str(employer_id) != employer.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own jobs"
        )
    
    # Build query
    query = db.query(Job).filter(Job.employer_id == employer_id)
    
    # Apply status filter if provided
    if status_filter:
        query = query.filter(Job.status == status_filter)
    
    # Execute query
    jobs = query.order_by(Job.posted_at.desc()).all()
    
    return JobListResponse(
        jobs=[JobResponse.model_validate(job) for job in jobs],
        total=len(jobs),
        page=1,
        page_size=len(jobs)
    )


@router.patch(
    "/{job_id}",
    response_model=JobResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Job not found"},
    }
)
async def update_job(
    job_id: UUID,
    update_data: JobUpdateRequest,
    employer: TokenData = Depends(get_current_employer),
    db: Session = Depends(get_db)
):
    """
    Update a job posting.
    
    This endpoint implements Requirement 9.6:
    - Verifies employer owns the job
    - Validates update data
    - Updates job record and recalculates quality score if needed
    
    **Example Request:**
    ```json
    {
      "description": "Updated job description...",
      "salary_min": 130000,
      "salary_max": 190000
    }
    ```
    """
    # Fetch job
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Verify employer owns the job
    if str(job.employer_id) != employer.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own jobs"
        )
    
    # Track if we need to recalculate quality score
    recalculate_score = False
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        if hasattr(job, field):
            setattr(job, field, value)
            # Fields that affect quality score
            if field in ['description', 'requirements', 'responsibilities', 'salary_min', 'salary_max', 'tags']:
                recalculate_score = True
    
    # Recalculate quality score if needed
    if recalculate_score:
        job_dict = {
            "title": job.title,
            "company": job.company,
            "description": job.description,
            "requirements": job.requirements or [],
            "responsibilities": job.responsibilities or [],
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "tags": job.tags or [],
        }
        job.quality_score = calculate_quality_score(
            source_type=job.source_type,
            job_data=job_dict,
            posted_at=job.posted_at
        )
    
    try:
        db.commit()
        db.refresh(job)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update job: {str(e)}"
        )
    
    return JobResponse.model_validate(job)


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Job not found"},
    }
)
async def delete_job(
    job_id: UUID,
    employer: TokenData = Depends(get_current_employer),
    db: Session = Depends(get_db)
):
    """
    Mark a job as deleted.
    
    This endpoint implements Requirement 9.7:
    - Verifies employer owns the job
    - Updates job status to 'deleted'
    
    **Example Response:**
    ```json
    {
      "message": "Job deleted successfully"
    }
    ```
    """
    # Fetch job
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Verify employer owns the job
    if str(job.employer_id) != employer.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own jobs"
        )
    
    # Update status to deleted
    job.status = JobStatus.DELETED
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete job: {str(e)}"
        )
    
    return {"message": "Job deleted successfully"}


@router.post(
    "/{job_id}/mark-filled",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Job not found"},
    }
)
async def mark_job_filled(
    job_id: UUID,
    employer: TokenData = Depends(get_current_employer),
    db: Session = Depends(get_db)
):
    """
    Mark a job as filled.
    
    This endpoint implements Requirement 9.8:
    - Verifies employer owns the job
    - Updates job status to 'filled'
    
    **Example Response:**
    ```json
    {
      "message": "Job marked as filled"
    }
    ```
    """
    # Fetch job
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Verify employer owns the job
    if str(job.employer_id) != employer.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own jobs"
        )
    
    # Update status to filled
    job.status = JobStatus.FILLED
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark job as filled: {str(e)}"
        )
    
    return {"message": "Job marked as filled"}


@router.post(
    "/{job_id}/increment-view",
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "Job not found"},
    }
)
async def increment_view_count(
    job_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Increment view count for a job.
    
    This endpoint implements Requirement 19.4:
    - Increments view count when job is viewed
    - Uses Redis to batch updates (increment every 10 views)
    
    **Process:**
    1. Increment counter in Redis
    2. Every 10 views, flush to database
    3. Return success
    
    **Example Response:**
    ```json
    {
      "message": "View count incremented"
    }
    ```
    """
    # Check if job exists
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Get Redis client
    redis = redis_client.get_cache_client()
    
    # Increment view counter in Redis
    cache_key = f"job_views:{job_id}"
    view_count = redis.incr(cache_key)
    
    # Batch update: flush to database every 10 views
    if view_count % 10 == 0:
        job.view_count += 10
        try:
            db.commit()
            # Reset Redis counter after flushing
            redis.delete(cache_key)
        except Exception as e:
            db.rollback()
            # Don't fail the request if database update fails
            # The counter will be flushed on next batch
            pass
    
    return {"message": "View count incremented"}


@router.post(
    "/{job_id}/feature",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - quota exceeded or not job owner"},
        404: {"model": ErrorResponse, "description": "Job not found"},
    }
)
async def feature_job(
    job_id: UUID,
    employer: TokenData = Depends(get_current_employer),
    db: Session = Depends(get_db)
):
    """
    Feature a job posting to give it enhanced visibility.
    
    This endpoint implements Requirements 11.1, 11.2, 11.3, and 11.4:
    - Verifies employer owns the job
    - Checks employer's featured post quota
    - Sets featured flag to true
    - Consumes featured quota
    
    **Process:**
    1. Verify employer owns the job
    2. Check featured post quota
    3. Set featured flag to true
    4. Consume featured quota
    5. Return success
    
    **Example Response:**
    ```json
    {
      "message": "Job featured successfully"
    }
    ```
    """
    # Fetch job
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Verify employer owns the job (Requirement 11.1)
    if str(job.employer_id) != employer.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only feature your own jobs"
        )
    
    # Check if job is already featured
    if job.featured:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job is already featured"
        )
    
    # Get Redis client for quota checking
    redis = redis_client.get_cache_client()
    employer_id = UUID(employer.user_id)
    
    # Check featured post quota (Requirement 11.2)
    has_featured_quota = check_quota(db, redis, employer_id, "featured_posts")
    if not has_featured_quota:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Featured post quota exceeded. Please upgrade your subscription."
        )
    
    # Set featured flag to true (Requirement 11.3)
    job.featured = True
    
    try:
        db.commit()
        db.refresh(job)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to feature job: {str(e)}"
        )
    
    # Consume featured quota (Requirement 11.4)
    try:
        consume_quota(db, redis, employer_id, "featured_posts")
    except RuntimeError as e:
        # Rollback featured flag if quota consumption fails
        job.featured = False
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to consume quota: {str(e)}"
        )
    
    return {"message": "Job featured successfully"}



@router.post(
    "/{job_id}/reactivate",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - not job owner"},
        404: {"model": ErrorResponse, "description": "Job not found"},
        400: {"model": ErrorResponse, "description": "Job is not expired"},
    }
)
async def reactivate_job(
    job_id: UUID,
    reactivate_data: JobReactivateRequest,
    employer: TokenData = Depends(get_current_employer),
    db: Session = Depends(get_db)
):
    """
    Reactivate an expired job with a new expiration date.
    
    This endpoint implements Requirement 10.7:
    - Verifies employer owns the job
    - Updates expiration date to new date (within 90 days)
    - Sets status back to 'active'
    
    **Process:**
    1. Verify employer owns the job
    2. Verify job is expired
    3. Update expiration date
    4. Set status to 'active'
    5. Return updated job
    
    **Example Request:**
    ```json
    {
      "expires_at": "2024-06-15T00:00:00Z"
    }
    ```
    
    **Example Response:**
    ```json
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "Senior Python Developer",
      "status": "active",
      "expires_at": "2024-06-15T00:00:00Z",
      ...
    }
    ```
    """
    # Fetch job
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Verify employer owns the job
    if str(job.employer_id) != employer.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only reactivate your own jobs"
        )
    
    # Verify job is expired
    if job.status != JobStatus.EXPIRED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job is not expired. Only expired jobs can be reactivated."
        )
    
    # Update expiration date and status
    job.expires_at = reactivate_data.expires_at
    job.status = JobStatus.ACTIVE
    
    try:
        db.commit()
        db.refresh(job)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reactivate job: {str(e)}"
        )
    
    return JobResponse.model_validate(job)
