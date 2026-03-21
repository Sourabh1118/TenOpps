"""
URL import API endpoints.

This module provides endpoints for importing jobs from URLs:
- POST /api/jobs/import-url: Queue URL import task
- GET /api/jobs/import-status/:taskId: Poll import task status
"""
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_employer
from app.core.redis import redis_client
from app.db.session import get_db
from app.models.scraping_task import ScrapingTask, TaskStatus, TaskType
from app.schemas.auth import TokenData
from app.schemas.url_import import (
    URLImportRequest,
    URLImportResponse,
    ImportStatusResponse,
    ErrorResponse,
)
from app.services.url_import import validate_import_url
from app.services.subscription import check_quota
from app.tasks.scraping_tasks import import_job_from_url


router = APIRouter(prefix="/jobs", tags=["url_import"])


@router.post(
    "/import-url",
    response_model=URLImportResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid URL or unsupported domain"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Import quota exceeded"},
    }
)
async def import_job_url(
    import_request: URLImportRequest,
    employer: TokenData = Depends(get_current_employer),
    db: Session = Depends(get_db)
):
    """
    Import a job by providing a URL from a supported platform.
    
    This endpoint implements Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8:
    - Validates URL format
    - Extracts and checks domain against whitelist
    - Checks employer's import quota
    - Queues import task in Celery
    - Returns task ID for polling
    
    **Supported Domains:**
    - LinkedIn (linkedin.com)
    - Indeed (indeed.com)
    - Naukri (naukri.com)
    - Monster (monster.com)
    - Glassdoor (glassdoor.com)
    
    **Process:**
    1. Validate URL format and domain
    2. Check subscription quota for URL imports
    3. Queue import task in Celery (high priority)
    4. Return task ID for status polling
    
    **Example Request:**
    ```json
    {
      "url": "https://www.linkedin.com/jobs/view/123456789"
    }
    ```
    
    **Example Response:**
    ```json
    {
      "task_id": "123e4567-e89b-12d3-a456-426614174000",
      "message": "Import task queued successfully. Use task_id to poll for status."
    }
    ```
    """
    # Get Redis client for quota checking
    redis = redis_client.get_cache_client()
    employer_id = UUID(employer.user_id)
    
    # Validate URL and check domain whitelist
    is_valid, domain, error = validate_import_url(import_request.url)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    # Check import quota
    has_quota = check_quota(db, redis, employer_id, "url_import")
    if not has_quota:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="URL import quota exceeded. Please upgrade your subscription or wait for quota reset."
        )
    
    # Queue import task in Celery (high priority queue)
    task = import_job_from_url.apply_async(
        args=[str(employer_id), import_request.url],
        queue='high_priority',
        priority=9
    )
    
    return URLImportResponse(
        task_id=UUID(task.id),
        message="Import task queued successfully. Use task_id to poll for status."
    )


@router.get(
    "/import-status/{task_id}",
    response_model=ImportStatusResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Task not found"},
    }
)
async def get_import_status(
    task_id: UUID,
    employer: TokenData = Depends(get_current_employer),
    db: Session = Depends(get_db)
):
    """
    Get the status of a URL import task.
    
    This endpoint implements Requirement 5.15:
    - Returns task status (PENDING, RUNNING, COMPLETED, FAILED)
    - Returns job ID on completion
    - Returns error message on failure
    
    **Task Statuses:**
    - PENDING: Task is queued but not yet started
    - RUNNING: Task is currently executing
    - COMPLETED: Task completed successfully (job created or duplicate found)
    - FAILED: Task failed with error
    
    **Example Response (Completed):**
    ```json
    {
      "task_id": "123e4567-e89b-12d3-a456-426614174000",
      "status": "COMPLETED",
      "job_id": "987e6543-e21b-12d3-a456-426614174000",
      "error_message": null,
      "created_at": "2024-01-15T10:00:00Z",
      "completed_at": "2024-01-15T10:00:15Z"
    }
    ```
    
    **Example Response (Failed):**
    ```json
    {
      "task_id": "123e4567-e89b-12d3-a456-426614174000",
      "status": "FAILED",
      "job_id": null,
      "error_message": "Failed to extract job details from URL",
      "created_at": "2024-01-15T10:00:00Z",
      "completed_at": "2024-01-15T10:00:10Z"
    }
    ```
    """
    # Query scraping task from database
    task = db.query(ScrapingTask).filter(
        ScrapingTask.id == task_id,
        ScrapingTask.task_type == TaskType.URL_IMPORT
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import task not found"
        )
    
    # Get job ID if task completed successfully
    job_id = None
    if task.status == TaskStatus.COMPLETED and task.jobs_created > 0:
        # Find the job created by this import
        from app.models.job import Job
        from app.models.job_source import JobSource
        
        # Query job source to find job created from this URL
        job_source = db.query(JobSource).filter(
            JobSource.source_url == task.target_url,
            JobSource.scraped_at >= task.created_at
        ).order_by(JobSource.scraped_at.desc()).first()
        
        if job_source:
            job_id = job_source.job_id
    
    return ImportStatusResponse(
        task_id=task.id,
        status=task.status.value.upper(),
        job_id=job_id,
        error_message=task.error_message,
        created_at=task.created_at.isoformat(),
        completed_at=task.completed_at.isoformat() if task.completed_at else None
    )
