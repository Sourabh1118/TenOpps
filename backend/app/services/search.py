"""
Search service for job search with full-text search and filtering.

This module provides the search service that implements PostgreSQL full-text
search using tsvector and tsquery for efficient searching on job titles and
descriptions.

**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 6.11, 6.12, 6.13, 6.14, 16.1, 16.3**
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import hashlib
import json
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session

from app.models.job import Job, JobStatus
from app.schemas.search import SearchFilters
from app.core.redis import cache
from app.core.logging import get_logger

logger = get_logger(__name__)


class SearchService:
    """Service for searching jobs with filters and full-text search."""

    def __init__(self, db: Session):
        """
        Initialize search service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.cache_ttl = 300  # 5 minutes in seconds

    def _generate_cache_key(
        self,
        filters: SearchFilters,
        page: int,
        page_size: int
    ) -> str:
        """
        Generate cache key from filters and pagination params.
        
        **Validates: Requirements 6.14**
        
        Args:
            filters: Search filters
            page: Page number
            page_size: Results per page
            
        Returns:
            Cache key string
        """
        # Convert filters to dict and sort for consistent key generation
        filter_dict = filters.model_dump(exclude_none=True)
        
        # Create a stable string representation
        key_data = {
            "filters": filter_dict,
            "page": page,
            "page_size": page_size
        }
        
        # Generate hash for compact key
        key_str = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        
        return f"search:{key_hash}"

    def search_jobs(
        self,
        filters: SearchFilters,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Search jobs with filters and pagination.
        
        Implements full-text search on title and description using PostgreSQL's
        tsvector and tsquery. Applies all provided filters with AND logic.
        Caches popular searches in Redis with 5-minute TTL.
        
        **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 6.11, 6.12, 6.13, 6.14, 16.1, 16.3**
        
        Args:
            filters: Search filters including query, location, job type, etc.
            page: Page number (1-indexed)
            page_size: Number of results per page (max 100)
            
        Returns:
            Dictionary with:
                - jobs: List of matching jobs
                - total: Total count of matching jobs
                - page: Current page number
                - page_size: Results per page
                - total_pages: Total number of pages
                
        Raises:
            ValueError: If page < 1 or page_size < 1 or page_size > 100
        """
        # Validate pagination parameters (Requirement 6.13, 16.3)
        if page < 1:
            raise ValueError("Page must be >= 1")
        if page_size < 1 or page_size > 100:
            raise ValueError("Page size must be between 1 and 100")

        # Check cache for popular searches (Requirement 6.14, 16.1)
        cache_key = self._generate_cache_key(filters, page, page_size)
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            # Return cached results (convert job IDs back to Job objects)
            return self._deserialize_cached_result(cached_result)

        # Build base query - only active jobs (Requirement 10.5)
        query = select(Job).where(Job.status == JobStatus.ACTIVE)

        # Apply full-text search on title and description if query provided (Requirement 6.1)
        if filters.query:
            # Create tsquery from search query
            # Use plainto_tsquery for simple query parsing (handles spaces, special chars)
            search_query = func.plainto_tsquery('english', filters.query)
            
            # Search in both title and description using tsvector
            # The GIN indexes on title and description will be used automatically
            title_match = func.to_tsvector('english', Job.title).op('@@')(search_query)
            description_match = func.to_tsvector('english', Job.description).op('@@')(search_query)
            
            # Match if query appears in either title or description
            query = query.where(or_(title_match, description_match))

        # Apply location filter (exact match) (Requirement 6.2)
        if filters.location:
            query = query.where(Job.location == filters.location)

        # Apply job type filter (IN clause) (Requirement 6.3)
        if filters.jobType:
            query = query.where(Job.job_type.in_(filters.jobType))

        # Apply experience level filter (IN clause) (Requirement 6.4)
        if filters.experienceLevel:
            query = query.where(Job.experience_level.in_(filters.experienceLevel))

        # Apply salary range filters (Requirement 6.5, 6.6)
        if filters.salaryMin is not None:
            # Job's max salary should be >= minimum requested
            query = query.where(
                or_(
                    Job.salary_max >= filters.salaryMin,
                    Job.salary_max.is_(None)  # Include jobs without salary info
                )
            )

        if filters.salaryMax is not None:
            # Job's min salary should be <= maximum requested
            query = query.where(
                or_(
                    Job.salary_min <= filters.salaryMax,
                    Job.salary_min.is_(None)  # Include jobs without salary info
                )
            )

        # Apply remote filter (boolean match) (Requirement 6.7)
        if filters.remote is True:
            query = query.where(Job.remote == True)

        # Apply posted within filter (date comparison) (Requirement 6.8)
        if filters.postedWithin:
            cutoff_date = datetime.utcnow() - timedelta(days=filters.postedWithin)
            query = query.where(Job.posted_at >= cutoff_date)

        # Apply source type filter (IN clause) (Requirement 6.9)
        if filters.sourceType:
            query = query.where(Job.source_type.in_(filters.sourceType))

        # All filters combined with AND logic (Requirement 6.10)

        # Get total count before pagination (Requirement 6.12)
        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_query).scalar()

        # Apply sorting: featured jobs first, then quality_score DESC, then posted_at DESC
        # (Requirement 6.11, 11.5)
        query = query.order_by(
            Job.featured.desc(),  # Featured jobs at top
            Job.quality_score.desc(),
            Job.posted_at.desc()
        )

        # Apply pagination (Requirement 6.12, 6.13, 16.3)
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Execute query
        result = self.db.execute(query)
        jobs = result.scalars().all()

        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        search_result = {
            "jobs": jobs,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }

        # Cache results for 5 minutes (Requirement 6.14, 16.1)
        self._cache_search_result(cache_key, search_result)
        
        # Track search analytics (Requirement 19.5)
        try:
            from app.services.analytics import AnalyticsService
            analytics = AnalyticsService(self.db)
            
            # Build filters dict for tracking
            filters_dict = {}
            if filters.location:
                filters_dict['location'] = filters.location
            if filters.jobType:
                filters_dict['jobType'] = [jt.value for jt in filters.jobType]
            if filters.experienceLevel:
                filters_dict['experienceLevel'] = [el.value for el in filters.experienceLevel]
            if filters.salaryMin is not None:
                filters_dict['salaryMin'] = filters.salaryMin
            if filters.salaryMax is not None:
                filters_dict['salaryMax'] = filters.salaryMax
            if filters.remote is not None:
                filters_dict['remote'] = filters.remote
            if filters.postedWithin is not None:
                filters_dict['postedWithin'] = filters.postedWithin
            if filters.sourceType:
                filters_dict['sourceType'] = [st.value for st in filters.sourceType]
            
            analytics.track_search(
                query_text=filters.query,
                result_count=total,
                location=filters.location,
                filters_applied=filters_dict if filters_dict else None,
            )
        except Exception as e:
            # Don't let analytics tracking break search
            logger.error(f"Error tracking search analytics: {e}")

        return search_result

    def _cache_search_result(self, cache_key: str, result: Dict[str, Any]) -> None:
        """
        Store search results in cache.
        
        **Validates: Requirements 6.14, 16.1**
        
        Args:
            cache_key: Cache key
            result: Search result to cache
        """
        try:
            # Serialize result for caching (store job IDs instead of full objects)
            cacheable_result = {
                "job_ids": [str(job.id) for job in result["jobs"]],
                "total": result["total"],
                "page": result["page"],
                "page_size": result["page_size"],
                "total_pages": result["total_pages"]
            }
            
            # Store in cache with 5-minute TTL
            cache.set(cache_key, cacheable_result, ttl=self.cache_ttl)
        except Exception as e:
            # Log error but don't fail the request
            from app.core.logging import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to cache search results: {e}")

    def _deserialize_cached_result(self, cached_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert cached result back to full result with Job objects.
        
        Args:
            cached_data: Cached search result
            
        Returns:
            Full search result with Job objects
        """
        # Fetch jobs by IDs
        from uuid import UUID
        job_ids = [UUID(job_id) for job_id in cached_data["job_ids"]]
        
        if not job_ids:
            jobs = []
        else:
            query = select(Job).where(Job.id.in_(job_ids))
            result = self.db.execute(query)
            jobs_dict = {job.id: job for job in result.scalars().all()}
            
            # Maintain original order
            jobs = [jobs_dict[job_id] for job_id in job_ids if job_id in jobs_dict]
        
        return {
            "jobs": jobs,
            "total": cached_data["total"],
            "page": cached_data["page"],
            "page_size": cached_data["page_size"],
            "total_pages": cached_data["total_pages"]
        }


def get_search_service(db: Session) -> SearchService:
    """
    Factory function to create search service instance.
    
    Args:
        db: Database session
        
    Returns:
        SearchService instance
    """
    return SearchService(db)


def invalidate_search_cache() -> int:
    """
    Invalidate all search result caches.
    
    This should be called when jobs are updated to ensure search results
    reflect the latest data.
    
    **Validates: Requirements 6.14, 16.1**
    
    Returns:
        Number of cache keys invalidated
    """
    try:
        # Clear all search cache keys
        count = cache.clear_pattern("search:*")
        logger.info(f"Invalidated {count} search cache entries")
        return count
    except Exception as e:
        logger.error(f"Failed to invalidate search cache: {e}")
        return 0
