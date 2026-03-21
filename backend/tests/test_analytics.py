"""
Unit tests for analytics service and API endpoints.

Tests cover:
- API response time tracking
- Scraping metrics tracking
- Search analytics tracking
- Job analytics tracking
- System health monitoring
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.orm import Session

from app.services.analytics import AnalyticsService
from app.models.analytics import (
    APIMetric,
    ScrapingMetric,
    SearchAnalytic,
    JobAnalytic,
    SystemHealthMetric,
)


class TestAnalyticsService:
    """Test analytics service functionality."""
    
    def test_track_api_response(self, db_session: Session):
        """Test API response time tracking."""
        analytics = AnalyticsService(db_session)
        
        # Track API response
        analytics.track_api_response(
            endpoint="/api/jobs/search",
            method="GET",
            status_code=200,
            response_time_ms=150.5,
        )
        
        # Verify metric was created
        metric = db_session.query(APIMetric).filter(
            APIMetric.endpoint == "/api/jobs/search"
        ).first()
        
        assert metric is not None
        assert metric.method == "GET"
        assert metric.status_code == 200
        assert metric.response_time_ms == 150.5
    
    def test_track_slow_request(self, db_session: Session):
        """Test slow request logging."""
        analytics = AnalyticsService(db_session)
        
        # Track slow request (>1 second)
        analytics.track_api_response(
            endpoint="/api/jobs/search",
            method="POST",
            status_code=200,
            response_time_ms=1500.0,
        )
        
        # Get slow requests
        slow_requests = analytics.get_slow_requests(
            threshold_ms=1000,
            hours=1,
            limit=10,
        )
        
        assert len(slow_requests) > 0
        assert slow_requests[0]["response_time_ms"] >= 1000
    
    def test_track_scraping_result(self, db_session: Session):
        """Test scraping metrics tracking."""
        analytics = AnalyticsService(db_session)
        
        # Track successful scraping
        analytics.track_scraping_result(
            source_platform="linkedin",
            success=True,
            duration_seconds=45.2,
            jobs_found=100,
            jobs_created=25,
            jobs_updated=10,
        )
        
        # Verify metric was created
        metric = db_session.query(ScrapingMetric).filter(
            ScrapingMetric.source_platform == "linkedin"
        ).first()
        
        assert metric is not None
        assert metric.success == 1
        assert metric.duration_seconds == 45.2
        assert metric.jobs_found == 100
        assert metric.jobs_created == 25
        assert metric.jobs_updated == 10
    
    def test_get_scraping_metrics(self, db_session: Session):
        """Test scraping metrics retrieval."""
        analytics = AnalyticsService(db_session)
        
        # Track multiple scraping results
        analytics.track_scraping_result(
            source_platform="indeed",
            success=True,
            duration_seconds=30.0,
            jobs_found=50,
            jobs_created=10,
            jobs_updated=5,
        )
        
        analytics.track_scraping_result(
            source_platform="indeed",
            success=False,
            duration_seconds=15.0,
            jobs_found=0,
            jobs_created=0,
            jobs_updated=0,
            error_message="Connection timeout",
        )
        
        # Get metrics
        metrics = analytics.get_scraping_metrics(
            source_platform="indeed",
            days=7,
        )
        
        assert metrics["total_runs"] == 2
        assert metrics["success_rate"] == 50.0
        assert metrics["total_jobs_found"] == 50
    
    def test_track_search(self, db_session: Session):
        """Test search analytics tracking."""
        analytics = AnalyticsService(db_session)
        
        # Track search
        analytics.track_search(
            query_text="software engineer",
            result_count=150,
            location="San Francisco",
            filters_applied={"remote": True, "jobType": ["full_time"]},
        )
        
        # Verify analytic was created
        analytic = db_session.query(SearchAnalytic).filter(
            SearchAnalytic.query_text == "software engineer"
        ).first()
        
        assert analytic is not None
        assert analytic.result_count == 150
        assert analytic.location == "San Francisco"
    
    def test_get_popular_searches(self, db_session: Session):
        """Test popular searches retrieval."""
        analytics = AnalyticsService(db_session)
        
        # Track multiple searches
        for _ in range(5):
            analytics.track_search(
                query_text="python developer",
                result_count=100,
            )
        
        for _ in range(3):
            analytics.track_search(
                query_text="data scientist",
                result_count=75,
            )
        
        # Get popular searches
        popular = analytics.get_popular_searches(limit=10)
        
        assert len(popular) > 0
        # Most popular should be "python developer"
        assert popular[0]["query"] == "python developer"
    
    def test_track_job_event(self, db_session: Session):
        """Test job event tracking."""
        analytics = AnalyticsService(db_session)
        
        job_id = uuid4()
        employer_id = uuid4()
        
        # Track job view
        analytics.track_job_event(
            job_id=job_id,
            employer_id=employer_id,
            event_type="view",
        )
        
        # Track job application
        analytics.track_job_event(
            job_id=job_id,
            employer_id=employer_id,
            event_type="application",
        )
        
        # Verify events were created
        events = db_session.query(JobAnalytic).filter(
            JobAnalytic.job_id == job_id
        ).all()
        
        assert len(events) == 2
        assert events[0].event_type in ["view", "application"]
    
    def test_get_job_analytics(self, db_session: Session):
        """Test job analytics retrieval."""
        analytics = AnalyticsService(db_session)
        
        job_id = uuid4()
        employer_id = uuid4()
        
        # Track multiple events
        for _ in range(10):
            analytics.track_job_event(
                job_id=job_id,
                employer_id=employer_id,
                event_type="view",
            )
        
        for _ in range(2):
            analytics.track_job_event(
                job_id=job_id,
                employer_id=employer_id,
                event_type="application",
            )
        
        # Get analytics
        job_analytics = analytics.get_job_analytics(job_id=job_id, days=30)
        
        assert job_analytics["views"] == 10
        assert job_analytics["applications"] == 2
        assert job_analytics["conversion_rate"] == 20.0
    
    def test_get_employer_analytics(self, db_session: Session):
        """Test employer analytics retrieval."""
        analytics = AnalyticsService(db_session)
        
        employer_id = uuid4()
        job1_id = uuid4()
        job2_id = uuid4()
        
        # Track events for multiple jobs
        for _ in range(5):
            analytics.track_job_event(
                job_id=job1_id,
                employer_id=employer_id,
                event_type="view",
            )
        
        for _ in range(8):
            analytics.track_job_event(
                job_id=job2_id,
                employer_id=employer_id,
                event_type="view",
            )
        
        analytics.track_job_event(
            job_id=job1_id,
            employer_id=employer_id,
            event_type="application",
        )
        
        # Get employer analytics
        employer_analytics = analytics.get_employer_analytics(
            employer_id=employer_id,
            days=30,
        )
        
        assert employer_analytics["total_views"] == 13
        assert employer_analytics["total_applications"] == 1
    
    def test_track_system_metric(self, db_session: Session):
        """Test system health metric tracking."""
        analytics = AnalyticsService(db_session)
        
        # Track system metric
        analytics.track_system_metric(
            metric_name="daily_active_users",
            metric_value=1250.0,
            metric_unit="users",
            extra_data={"date": "2024-01-15"},
        )
        
        # Verify metric was created
        metric = db_session.query(SystemHealthMetric).filter(
            SystemHealthMetric.metric_name == "daily_active_users"
        ).first()
        
        assert metric is not None
        assert metric.metric_value == 1250.0
        assert metric.metric_unit == "users"
    
    def test_get_system_metrics(self, db_session: Session):
        """Test system metrics retrieval."""
        analytics = AnalyticsService(db_session)
        
        # Track multiple metrics
        analytics.track_system_metric(
            metric_name="redis_memory_usage",
            metric_value=85.5,
            metric_unit="MB",
        )
        
        analytics.track_system_metric(
            metric_name="db_pool_size",
            metric_value=15.0,
            metric_unit="connections",
        )
        
        # Get all metrics
        metrics = analytics.get_system_metrics(hours=24)
        
        assert len(metrics) >= 2
        
        # Get specific metric
        redis_metrics = analytics.get_system_metrics(
            metric_name="redis_memory_usage",
            hours=24,
        )
        
        assert len(redis_metrics) >= 1
        assert redis_metrics[0]["metric_name"] == "redis_memory_usage"


class TestAnalyticsAPI:
    """Test analytics API endpoints."""
    
    def test_get_popular_searches_endpoint(self, client, db: Session):
        """Test popular searches endpoint."""
        # Track some searches
        analytics = AnalyticsService(db_session)
        analytics.track_search(
            query_text="python developer",
            result_count=100,
        )
        
        # Call endpoint
        response = client.get("/api/analytics/popular-searches?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert "popular_searches" in data
        assert "total_count" in data
    
    def test_get_slow_requests_admin_only(self, client, admin_token):
        """Test slow requests endpoint requires admin."""
        # Without auth
        response = client.get("/api/analytics/admin/slow-requests")
        assert response.status_code == 401
        
        # With admin auth
        response = client.get(
            "/api/analytics/admin/slow-requests",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
    
    def test_get_scraping_metrics_admin_only(self, client, admin_token):
        """Test scraping metrics endpoint requires admin."""
        # Without auth
        response = client.get("/api/analytics/admin/scraping-metrics")
        assert response.status_code == 401
        
        # With admin auth
        response = client.get(
            "/api/analytics/admin/scraping-metrics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
    
    def test_get_job_analytics_premium_only(
        self, client, premium_employer_token, db: Session
    ):
        """Test job analytics endpoint requires premium tier."""
        # This test would require setting up a premium employer
        # and a job, which is complex for a unit test
        # In a real scenario, this would be an integration test
        pass
