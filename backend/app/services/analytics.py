"""
Analytics service for tracking metrics and monitoring.

This module provides functions for:
- Tracking API response times
- Recording scraping metrics
- Tracking search analytics
- Recording job analytics
- Monitoring system health
"""
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from app.models.analytics import (
    APIMetric,
    ScrapingMetric,
    SearchAnalytic,
    JobAnalytic,
    SystemHealthMetric,
)
from app.core.redis import redis_client, CacheManager
from app.core.logging import logger


class AnalyticsService:
    """Service for tracking and retrieving analytics data."""
    
    def __init__(self, db: Session):
        """Initialize analytics service."""
        self.db = db
        self.cache = CacheManager()
    
    # ===== API Response Time Tracking (Requirement 19.2) =====
    
    def track_api_response(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        user_id: Optional[UUID] = None,
        user_role: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Track API response time.
        
        Implements Requirement 19.2:
        - Store response time metrics in database
        - Log slow requests (>1 second)
        
        Args:
            endpoint: API endpoint path
            method: HTTP method
            status_code: HTTP status code
            response_time_ms: Response time in milliseconds
            user_id: Optional user ID
            user_role: Optional user role
            error_message: Optional error message for failed requests
        """
        try:
            # Create metric record
            metric = APIMetric(
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time_ms=response_time_ms,
                user_id=user_id,
                user_role=user_role,
                error_message=error_message,
            )
            self.db.add(metric)
            self.db.commit()
            
            # Log slow requests (>1 second)
            if response_time_ms > 1000:
                logger.warning(
                    f"Slow API request detected",
                    extra={
                        "endpoint": endpoint,
                        "method": method,
                        "response_time_ms": response_time_ms,
                        "status_code": status_code,
                    }
                )
            
            # Store in Redis for real-time monitoring
            redis = redis_client.get_cache_client()
            key = f"api_metrics:recent:{endpoint}:{method}"
            redis.lpush(key, response_time_ms)
            redis.ltrim(key, 0, 99)  # Keep last 100 measurements
            redis.expire(key, 3600)  # 1 hour TTL
            
        except Exception as e:
            logger.error(f"Error tracking API response: {e}")
            # Don't raise - analytics tracking should not break the request
    
    def get_slow_requests(
        self,
        threshold_ms: float = 1000,
        hours: int = 24,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get slow API requests.
        
        Args:
            threshold_ms: Response time threshold in milliseconds
            hours: Number of hours to look back
            limit: Maximum number of results
            
        Returns:
            List of slow request records
        """
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            
            results = (
                self.db.query(APIMetric)
                .filter(
                    and_(
                        APIMetric.response_time_ms > threshold_ms,
                        APIMetric.timestamp >= since,
                    )
                )
                .order_by(desc(APIMetric.response_time_ms))
                .limit(limit)
                .all()
            )
            
            return [
                {
                    "endpoint": r.endpoint,
                    "method": r.method,
                    "response_time_ms": r.response_time_ms,
                    "status_code": r.status_code,
                    "timestamp": r.timestamp.isoformat(),
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Error getting slow requests: {e}")
            return []
    
    # ===== Scraping Metrics (Requirement 19.3) =====
    
    def track_scraping_result(
        self,
        source_platform: str,
        success: bool,
        duration_seconds: float,
        jobs_found: int = 0,
        jobs_created: int = 0,
        jobs_updated: int = 0,
        task_id: Optional[UUID] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Track scraping task result.
        
        Implements Requirement 19.3:
        - Track scraping success rate and duration per source
        - Store metrics in database
        
        Args:
            source_platform: Source platform name
            success: Whether scraping succeeded
            duration_seconds: Duration in seconds
            jobs_found: Number of jobs found
            jobs_created: Number of jobs created
            jobs_updated: Number of jobs updated
            task_id: Optional Celery task ID
            error_message: Optional error message for failures
        """
        try:
            metric = ScrapingMetric(
                source_platform=source_platform,
                task_id=task_id,
                success=1 if success else 0,
                jobs_found=jobs_found,
                jobs_created=jobs_created,
                jobs_updated=jobs_updated,
                duration_seconds=duration_seconds,
                error_message=error_message,
            )
            self.db.add(metric)
            self.db.commit()
            
            # Update Redis counters for real-time monitoring
            redis = redis_client.get_cache_client()
            date_key = datetime.utcnow().strftime("%Y-%m-%d")
            
            if success:
                redis.incr(f"scraping:success:{source_platform}:{date_key}")
                redis.incrby(f"scraping:jobs_created:{source_platform}:{date_key}", jobs_created)
            else:
                redis.incr(f"scraping:failure:{source_platform}:{date_key}")
            
            # Set expiration for daily keys (7 days)
            redis.expire(f"scraping:success:{source_platform}:{date_key}", 604800)
            redis.expire(f"scraping:failure:{source_platform}:{date_key}", 604800)
            redis.expire(f"scraping:jobs_created:{source_platform}:{date_key}", 604800)
            
        except Exception as e:
            logger.error(f"Error tracking scraping result: {e}")
    
    def get_scraping_metrics(
        self,
        source_platform: Optional[str] = None,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Get scraping metrics summary.
        
        Args:
            source_platform: Optional platform filter
            days: Number of days to look back
            
        Returns:
            Dictionary with success rate, average duration, and job counts
        """
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            query = self.db.query(ScrapingMetric).filter(
                ScrapingMetric.timestamp >= since
            )
            
            if source_platform:
                query = query.filter(ScrapingMetric.source_platform == source_platform)
            
            metrics = query.all()
            
            if not metrics:
                return {
                    "total_runs": 0,
                    "success_rate": 0.0,
                    "average_duration_seconds": 0.0,
                    "total_jobs_found": 0,
                    "total_jobs_created": 0,
                    "total_jobs_updated": 0,
                }
            
            total_runs = len(metrics)
            successful_runs = sum(1 for m in metrics if m.success)
            success_rate = (successful_runs / total_runs) * 100
            
            avg_duration = sum(m.duration_seconds for m in metrics) / total_runs
            total_jobs_found = sum(m.jobs_found for m in metrics)
            total_jobs_created = sum(m.jobs_created for m in metrics)
            total_jobs_updated = sum(m.jobs_updated for m in metrics)
            
            return {
                "total_runs": total_runs,
                "success_rate": round(success_rate, 2),
                "average_duration_seconds": round(avg_duration, 2),
                "total_jobs_found": total_jobs_found,
                "total_jobs_created": total_jobs_created,
                "total_jobs_updated": total_jobs_updated,
            }
        except Exception as e:
            logger.error(f"Error getting scraping metrics: {e}")
            return {}
    
    # ===== Search Analytics (Requirement 19.5) =====
    
    def track_search(
        self,
        query_text: Optional[str],
        result_count: int,
        location: Optional[str] = None,
        filters_applied: Optional[Dict] = None,
        user_id: Optional[UUID] = None,
    ) -> None:
        """
        Track search query.
        
        Implements Requirement 19.5:
        - Track popular search terms
        - Store search queries and result counts
        
        Args:
            query_text: Search query text
            result_count: Number of results returned
            location: Optional location filter
            filters_applied: Optional dictionary of filters
            user_id: Optional user ID
        """
        try:
            analytic = SearchAnalytic(
                query_text=query_text,
                location=location,
                filters_applied=json.dumps(filters_applied) if filters_applied else None,
                result_count=result_count,
                user_id=user_id,
            )
            self.db.add(analytic)
            self.db.commit()
            
            # Track popular searches in Redis
            if query_text:
                redis = redis_client.get_cache_client()
                redis.zincrby("search:popular", 1, query_text.lower())
                # Keep top 1000 searches
                redis.zremrangebyrank("search:popular", 0, -1001)
            
        except Exception as e:
            logger.error(f"Error tracking search: {e}")
    
    def get_popular_searches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get popular search terms.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of popular search terms with counts
        """
        try:
            # Try Redis first for real-time data
            redis = redis_client.get_cache_client()
            popular = redis.zrevrange("search:popular", 0, limit - 1, withscores=True)
            
            if popular:
                return [
                    {"query": query, "count": int(score)}
                    for query, score in popular
                ]
            
            # Fallback to database
            since = datetime.utcnow() - timedelta(days=7)
            
            results = (
                self.db.query(
                    SearchAnalytic.query_text,
                    func.count(SearchAnalytic.id).label("count")
                )
                .filter(
                    and_(
                        SearchAnalytic.query_text.isnot(None),
                        SearchAnalytic.timestamp >= since,
                    )
                )
                .group_by(SearchAnalytic.query_text)
                .order_by(desc("count"))
                .limit(limit)
                .all()
            )
            
            return [
                {"query": r.query_text, "count": r.count}
                for r in results
            ]
        except Exception as e:
            logger.error(f"Error getting popular searches: {e}")
            return []
    
    # ===== Job Analytics (Requirements 19.6, 9.10) =====
    
    def track_job_event(
        self,
        job_id: UUID,
        employer_id: UUID,
        event_type: str,
        user_id: Optional[UUID] = None,
        referrer: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        Track job event (view, application, click).
        
        Implements Requirements 19.6 and 9.10:
        - Track views, applications, and conversion rates per job
        
        Args:
            job_id: Job ID
            employer_id: Employer ID
            event_type: Event type ('view', 'application', 'click')
            user_id: Optional user ID
            referrer: Optional referrer URL
            user_agent: Optional user agent string
        """
        try:
            analytic = JobAnalytic(
                job_id=job_id,
                employer_id=employer_id,
                event_type=event_type,
                user_id=user_id,
                referrer=referrer,
                user_agent=user_agent,
            )
            self.db.add(analytic)
            self.db.commit()
            
            # Update Redis counters for real-time stats
            redis = redis_client.get_cache_client()
            redis.incr(f"job:analytics:{job_id}:{event_type}")
            redis.expire(f"job:analytics:{job_id}:{event_type}", 2592000)  # 30 days
            
        except Exception as e:
            logger.error(f"Error tracking job event: {e}")
    
    def get_job_analytics(
        self,
        job_id: UUID,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get analytics for a specific job.
        
        Args:
            job_id: Job ID
            days: Number of days to look back
            
        Returns:
            Dictionary with views, applications, and conversion rate
        """
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            # Get event counts
            results = (
                self.db.query(
                    JobAnalytic.event_type,
                    func.count(JobAnalytic.id).label("count")
                )
                .filter(
                    and_(
                        JobAnalytic.job_id == job_id,
                        JobAnalytic.timestamp >= since,
                    )
                )
                .group_by(JobAnalytic.event_type)
                .all()
            )
            
            counts = {r.event_type: r.count for r in results}
            views = counts.get("view", 0)
            applications = counts.get("application", 0)
            
            conversion_rate = (applications / views * 100) if views > 0 else 0.0
            
            return {
                "views": views,
                "applications": applications,
                "clicks": counts.get("click", 0),
                "conversion_rate": round(conversion_rate, 2),
                "period_days": days,
            }
        except Exception as e:
            logger.error(f"Error getting job analytics: {e}")
            return {}
    
    def get_employer_analytics(
        self,
        employer_id: UUID,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get analytics for all jobs by an employer.
        
        Args:
            employer_id: Employer ID
            days: Number of days to look back
            
        Returns:
            Dictionary with aggregate analytics
        """
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            results = (
                self.db.query(
                    JobAnalytic.event_type,
                    func.count(JobAnalytic.id).label("count")
                )
                .filter(
                    and_(
                        JobAnalytic.employer_id == employer_id,
                        JobAnalytic.timestamp >= since,
                    )
                )
                .group_by(JobAnalytic.event_type)
                .all()
            )
            
            counts = {r.event_type: r.count for r in results}
            views = counts.get("view", 0)
            applications = counts.get("application", 0)
            
            conversion_rate = (applications / views * 100) if views > 0 else 0.0
            
            return {
                "total_views": views,
                "total_applications": applications,
                "total_clicks": counts.get("click", 0),
                "conversion_rate": round(conversion_rate, 2),
                "period_days": days,
            }
        except Exception as e:
            logger.error(f"Error getting employer analytics: {e}")
            return {}
    
    # ===== System Health Monitoring (Requirements 19.7, 19.8) =====
    
    def track_system_metric(
        self,
        metric_name: str,
        metric_value: float,
        metric_unit: Optional[str] = None,
        extra_data: Optional[Dict] = None,
    ) -> None:
        """
        Track system health metric.
        
        Implements Requirements 19.7 and 19.8:
        - Track daily active users and job posting volume
        - Monitor database and Redis usage
        
        Args:
            metric_name: Metric name
            metric_value: Metric value
            metric_unit: Optional unit (e.g., 'users', 'jobs', 'MB')
            extra_data: Optional extra data dictionary
        """
        try:
            metric = SystemHealthMetric(
                metric_name=metric_name,
                metric_value=metric_value,
                metric_unit=metric_unit,
                extra_data=json.dumps(extra_data) if extra_data else None,
            )
            self.db.add(metric)
            self.db.commit()
            
            # Store in Redis for real-time monitoring
            redis = redis_client.get_cache_client()
            redis.set(f"system:metric:{metric_name}", metric_value, ex=3600)
            
        except Exception as e:
            logger.error(f"Error tracking system metric: {e}")
    
    def get_system_metrics(
        self,
        metric_name: Optional[str] = None,
        hours: int = 24,
    ) -> List[Dict[str, Any]]:
        """
        Get system health metrics.
        
        Args:
            metric_name: Optional metric name filter
            hours: Number of hours to look back
            
        Returns:
            List of metric records
        """
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            
            query = self.db.query(SystemHealthMetric).filter(
                SystemHealthMetric.timestamp >= since
            )
            
            if metric_name:
                query = query.filter(SystemHealthMetric.metric_name == metric_name)
            
            results = query.order_by(desc(SystemHealthMetric.timestamp)).all()
            
            return [
                {
                    "metric_name": r.metric_name,
                    "metric_value": r.metric_value,
                    "metric_unit": r.metric_unit,
                    "timestamp": r.timestamp.isoformat(),
                    "extra_data": json.loads(r.extra_data) if r.extra_data else None,
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return []


def get_analytics_service(db: Session) -> AnalyticsService:
    """Get analytics service instance."""
    return AnalyticsService(db)
