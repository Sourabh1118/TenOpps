"""
Analytics models for tracking metrics and monitoring.

This module defines models for:
- API response time tracking
- Scraping metrics
- Search analytics
- Job posting analytics
- System health metrics
"""
from datetime import datetime
from typing import Optional
import enum
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    Text,
    Enum,
    Index,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.base import Base, GUID


class MetricType(str, enum.Enum):
    """Types of metrics tracked."""
    API_RESPONSE_TIME = "api_response_time"
    SCRAPING_SUCCESS = "scraping_success"
    SCRAPING_FAILURE = "scraping_failure"
    SEARCH_QUERY = "search_query"
    JOB_VIEW = "job_view"
    JOB_APPLICATION = "job_application"
    SYSTEM_HEALTH = "system_health"


class APIMetric(Base):
    """
    API response time metrics.
    
    Tracks response times for API endpoints to identify slow requests.
    Implements Requirement 19.2.
    """
    __tablename__ = "api_metrics"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Request information
    endpoint = Column(String(500), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False)
    
    # Timing
    response_time_ms = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    
    # User context (optional)
    user_id = Column(GUID(), nullable=True)
    user_role = Column(String(50), nullable=True)
    
    # Additional context
    error_message = Column(Text, nullable=True)
    
    __table_args__ = (
        CheckConstraint("response_time_ms >= 0", name="check_response_time_positive"),
        Index("idx_api_metrics_endpoint_timestamp", "endpoint", "timestamp"),
        Index("idx_api_metrics_slow_requests", "response_time_ms", postgresql_where="response_time_ms > 1000"),
    )

    def __repr__(self) -> str:
        return f"<APIMetric(endpoint='{self.endpoint}', response_time={self.response_time_ms}ms)>"


class ScrapingMetric(Base):
    """
    Scraping task metrics.
    
    Tracks success rate and duration for each scraping source.
    Implements Requirement 19.3.
    """
    __tablename__ = "scraping_metrics"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Source information
    source_platform = Column(String(50), nullable=False, index=True)
    task_id = Column(GUID(), nullable=True)
    
    # Results
    success = Column(Integer, nullable=False)  # Boolean as int: 1 = success, 0 = failure
    jobs_found = Column(Integer, default=0, nullable=False)
    jobs_created = Column(Integer, default=0, nullable=False)
    jobs_updated = Column(Integer, default=0, nullable=False)
    
    # Timing
    duration_seconds = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    
    # Error information
    error_message = Column(Text, nullable=True)
    
    __table_args__ = (
        CheckConstraint("success IN (0, 1)", name="check_success_boolean"),
        CheckConstraint("duration_seconds >= 0", name="check_duration_positive"),
        CheckConstraint("jobs_found >= 0", name="check_jobs_found_positive"),
        CheckConstraint("jobs_created >= 0", name="check_jobs_created_positive"),
        CheckConstraint("jobs_updated >= 0", name="check_jobs_updated_positive"),
        Index("idx_scraping_metrics_platform_timestamp", "source_platform", "timestamp"),
        Index("idx_scraping_metrics_failures", "success", postgresql_where="success = 0"),
    )

    def __repr__(self) -> str:
        status = "success" if self.success else "failure"
        return f"<ScrapingMetric(platform='{self.source_platform}', status='{status}')>"


class SearchAnalytic(Base):
    """
    Search query analytics.
    
    Tracks search queries and result counts for analytics.
    Implements Requirement 19.5.
    """
    __tablename__ = "search_analytics"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Query information
    query_text = Column(String(500), nullable=True, index=True)
    location = Column(String(200), nullable=True)
    filters_applied = Column(Text, nullable=True)  # JSON string of filters
    
    # Results
    result_count = Column(Integer, nullable=False)
    
    # Timing
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    
    # User context (optional)
    user_id = Column(GUID(), nullable=True)
    
    __table_args__ = (
        CheckConstraint("result_count >= 0", name="check_result_count_positive"),
        Index("idx_search_analytics_query_timestamp", "query_text", "timestamp"),
        Index("idx_search_analytics_timestamp", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<SearchAnalytic(query='{self.query_text}', results={self.result_count})>"


class JobAnalytic(Base):
    """
    Job posting analytics for employers.
    
    Tracks views, applications, and conversion rates per job.
    Implements Requirements 19.6 and 9.10.
    """
    __tablename__ = "job_analytics"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Job reference
    job_id = Column(GUID(), nullable=False, index=True)
    employer_id = Column(GUID(), nullable=False, index=True)
    
    # Event type
    event_type = Column(String(50), nullable=False)  # 'view', 'application', 'click'
    
    # Timing
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    
    # User context (optional)
    user_id = Column(GUID(), nullable=True)
    
    # Additional context
    referrer = Column(String(500), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    __table_args__ = (
        Index("idx_job_analytics_job_timestamp", "job_id", "timestamp"),
        Index("idx_job_analytics_employer_timestamp", "employer_id", "timestamp"),
        Index("idx_job_analytics_event_type", "event_type"),
    )

    def __repr__(self) -> str:
        return f"<JobAnalytic(job_id={self.job_id}, event='{self.event_type}')>"


class SystemHealthMetric(Base):
    """
    System health monitoring metrics.
    
    Tracks system-wide metrics like DAU, job volume, resource usage.
    Implements Requirements 19.7 and 19.8.
    """
    __tablename__ = "system_health_metrics"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Metric information
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(50), nullable=True)
    
    # Timing
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    
    # Additional context
    extra_data = Column(Text, nullable=True)  # JSON string for additional data
    
    __table_args__ = (
        Index("idx_system_health_name_timestamp", "metric_name", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<SystemHealthMetric(name='{self.metric_name}', value={self.metric_value})>"
