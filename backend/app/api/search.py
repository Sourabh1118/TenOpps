"""
Search API endpoints for job search with filtering.

This module provides the REST API endpoints for searching jobs with
various filters, pagination, and caching.

**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 6.11, 6.12, 6.13, 10.5**
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.job import JobType, ExperienceLevel, SourceType
from app.schemas.search import SearchFilters
from app.services.search import SearchService
from app.services.analytics import AnalyticsService
from app.core.logging import logger


router = APIRouter(prefix="/jobs", tags=["search"])


@router.get("/search")
async def search_jobs(
    query: Optional[str] = Query(None, max_length=200, description="Full-text search query"),
    location: Optional[str] = Query(None, max_length=200, description="Job location filter"),
    jobType: Optional[List[JobType]] = Query(None, description="Job type filters"),
    experienceLevel: Optional[List[ExperienceLevel]] = Query(None, description="Experience level filters"),
    salaryMin: Optional[int] = Query(None, ge=0, description="Minimum salary filter"),
    salaryMax: Optional[int] = Query(None, ge=0, description="Maximum salary filter"),
    remote: Optional[bool] = Query(None, description="Remote jobs only"),
    postedWithin: Optional[int] = Query(None, ge=1, le=365, description="Posted within days"),
    sourceType: Optional[List[SourceType]] = Query(None, description="Source type filters"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    db: Session = Depends(get_db)
):
    """
    Search jobs with filters and pagination.
    
    Supports full-text search on job titles and descriptions, along with
    multiple filters that can be combined. Results are sorted by featured
    status, quality score, and posting date. Popular searches are cached
    for 5 minutes.
    
    **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 6.11, 6.12, 6.13, 10.5**
    
    Args:
        query: Full-text search query for job title and description
        location: Job location filter (exact match)
        jobType: Filter by job types (can specify multiple)
        experienceLevel: Filter by experience levels (can specify multiple)
        salaryMin: Minimum salary filter (jobs with salary >= this value)
        salaryMax: Maximum salary filter (jobs with salary <= this value)
        remote: Filter for remote jobs only
        postedWithin: Filter jobs posted within this many days
        sourceType: Filter by source types (can specify multiple)
        page: Page number (1-indexed)
        page_size: Number of results per page (max 100)
        db: Database session
        
    Returns:
        Paginated search results with:
            - jobs: List of matching jobs
            - total: Total count of matching jobs
            - page: Current page number
            - page_size: Results per page
            - total_pages: Total number of pages
            
    Example:
        GET /api/jobs/search?query=software+engineer&location=San+Francisco&remote=true&page=1&page_size=20
    """
    # Create search filters from query parameters
    filters = SearchFilters(
        query=query,
        location=location,
        jobType=jobType,
        experienceLevel=experienceLevel,
        salaryMin=salaryMin,
        salaryMax=salaryMax,
        remote=remote,
        postedWithin=postedWithin,
        sourceType=sourceType
    )
    
    # Execute search
    search_service = SearchService(db)
    results = search_service.search_jobs(filters, page=page, page_size=page_size)
    
    # Track search analytics (Requirement 19.5)
    try:
        analytics = AnalyticsService(db)
        analytics.track_search(
            query_text=query,
            result_count=results["total"],
            location=location,
            filters_applied={
                "jobType": [jt.value for jt in jobType] if jobType else None,
                "experienceLevel": [el.value for el in experienceLevel] if experienceLevel else None,
                "salaryMin": salaryMin,
                "salaryMax": salaryMax,
                "remote": remote,
                "postedWithin": postedWithin,
                "sourceType": [st.value for st in sourceType] if sourceType else None,
            },
        )
    except Exception as e:
        # Don't fail the search if analytics tracking fails
        logger.error(f"Error tracking search analytics: {e}")
    
    # Convert Job objects to dictionaries for JSON response
    return {
        "jobs": [
            {
                "id": str(job.id),
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "remote": job.remote,
                "jobType": job.job_type.value,
                "experienceLevel": job.experience_level.value,
                "description": job.description,
                "salaryMin": job.salary_min,
                "salaryMax": job.salary_max,
                "salaryCurrency": job.salary_currency,
                "sourceType": job.source_type.value,
                "sourceUrl": job.source_url,
                "qualityScore": job.quality_score,
                "postedAt": job.posted_at.isoformat() + "Z",
                "expiresAt": job.expires_at.isoformat() + "Z",
                "featured": job.featured,
                "tags": job.tags
            }
            for job in results["jobs"]
        ],
        "total": results["total"],
        "page": results["page"],
        "pageSize": results["page_size"],
        "totalPages": results["total_pages"]
    }
