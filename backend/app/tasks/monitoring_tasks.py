"""
Celery tasks for monitoring and health checks.

This module contains tasks for system health monitoring,
metrics collection, and alerting.
"""
from typing import Optional
from datetime import datetime, timedelta
from uuid import UUID
from celery import Task
from sqlalchemy import func

from app.tasks.celery_app import celery_app
from app.core.logging import logger
from app.db.session import SessionLocal
from app.services.analytics import AnalyticsService
from app.services.alerting import send_alert
from app.core.redis import redis_client
from app.models.job import Job, JobStatus
from app.models.employer import Employer
from app.models.job_seeker import JobSeeker


class MonitoringTask(Task):
    """Base class for monitoring tasks."""
    
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 1}


@celery_app.task(name="app.tasks.monitoring_tasks.track_api_metric_task")
def track_api_metric_task(
    endpoint: str,
    method: str,
    status_code: int,
    response_time_ms: float,
    user_id: Optional[str] = None,
    user_role: Optional[str] = None,
    error_message: Optional[str] = None,
):
    """
    Background task to track API metrics in database.
    
    Implements Requirement 19.2:
    - Store API response time metrics in database
    
    Args:
        endpoint: API endpoint path
        method: HTTP method
        status_code: HTTP status code
        response_time_ms: Response time in milliseconds
        user_id: Optional user ID
        user_role: Optional user role
        error_message: Optional error message
    """
    db = SessionLocal()
    try:
        analytics = AnalyticsService(db)
        analytics.track_api_response(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            user_id=UUID(user_id) if user_id else None,
            user_role=user_role,
            error_message=error_message,
        )
    except Exception as e:
        logger.error(f"Error tracking API metric: {e}")
    finally:
        db.close()


@celery_app.task(base=MonitoringTask, bind=True, name="app.tasks.monitoring_tasks.health_check")
def health_check(self):
    """
    Perform system health check.
    
    This task can be used to verify Celery workers are functioning.
    """
    logger.info("Performing health check")
    
    try:
        # TODO: Implement health check logic
        # Check database connection
        # Check Redis connection
        # Check external API availability
        logger.info("Health check completed (placeholder)")
        return {
            "status": "healthy",
            "timestamp": None,
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise


@celery_app.task(base=MonitoringTask, bind=True, name="app.tasks.monitoring_tasks.collect_system_metrics")
def collect_system_metrics(self):
    """
    Collect system metrics for monitoring.
    
    Implements Requirements 19.7 and 19.8:
    - Track daily active users and job posting volume
    - Monitor database connection pool usage
    - Monitor Redis memory usage
    """
    logger.info("Collecting system metrics")
    
    db = SessionLocal()
    try:
        analytics = AnalyticsService(db)
        
        # Track daily active users (Requirement 19.7)
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        
        # Count unique job seekers who searched or applied yesterday
        from app.models.application import Application
        from app.models.search_analytics import SearchAnalytic
        
        active_job_seekers = db.query(func.count(func.distinct(Application.job_seeker_id))).filter(
            func.date(Application.applied_at) == yesterday
        ).scalar() or 0
        
        analytics.track_system_metric(
            metric_name="daily_active_job_seekers",
            metric_value=float(active_job_seekers),
            metric_unit="users",
        )
        
        # Count unique employers who posted or viewed analytics yesterday
        active_employers = db.query(func.count(func.distinct(Job.employer_id))).filter(
            func.date(Job.created_at) == yesterday,
            Job.employer_id.isnot(None),
        ).scalar() or 0
        
        analytics.track_system_metric(
            metric_name="daily_active_employers",
            metric_value=float(active_employers),
            metric_unit="users",
        )
        
        # Track job posting volume (Requirement 19.7)
        jobs_posted_yesterday = db.query(func.count(Job.id)).filter(
            func.date(Job.created_at) == yesterday
        ).scalar() or 0
        
        analytics.track_system_metric(
            metric_name="daily_jobs_posted",
            metric_value=float(jobs_posted_yesterday),
            metric_unit="jobs",
        )
        
        # Track active jobs
        active_jobs = db.query(func.count(Job.id)).filter(
            Job.status == JobStatus.ACTIVE
        ).scalar() or 0
        
        analytics.track_system_metric(
            metric_name="active_jobs_count",
            metric_value=float(active_jobs),
            metric_unit="jobs",
        )
        
        # Monitor database connection pool (Requirement 19.8)
        from app.db.session import engine
        pool = engine.pool
        
        analytics.track_system_metric(
            metric_name="db_pool_size",
            metric_value=float(pool.size()),
            metric_unit="connections",
            extra_data={
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
            }
        )
        
        # Monitor Redis memory usage (Requirement 19.8)
        redis = redis_client.get_cache_client()
        redis_info = redis.info("memory")
        
        used_memory_mb = redis_info.get("used_memory", 0) / (1024 * 1024)
        
        analytics.track_system_metric(
            metric_name="redis_memory_usage",
            metric_value=used_memory_mb,
            metric_unit="MB",
            extra_data={
                "peak_memory_mb": redis_info.get("used_memory_peak", 0) / (1024 * 1024),
                "fragmentation_ratio": redis_info.get("mem_fragmentation_ratio", 0),
            }
        )
        
        logger.info("System metrics collection completed")
        
        return {
            "status": "success",
            "metrics": {
                "daily_active_job_seekers": active_job_seekers,
                "daily_active_employers": active_employers,
                "daily_jobs_posted": jobs_posted_yesterday,
                "active_jobs_count": active_jobs,
                "db_pool_size": pool.size(),
                "redis_memory_mb": round(used_memory_mb, 2),
            }
        }
        
    except Exception as e:
        logger.error(f"System metrics collection failed: {e}")
        raise
    finally:
        db.close()


@celery_app.task(base=MonitoringTask, bind=True, name="app.tasks.monitoring_tasks.check_metric_thresholds")
def check_metric_thresholds(self):
    """
    Check if system metrics exceed thresholds and send alerts.
    
    Implements Requirement 19.8:
    - Alert when metrics exceed thresholds
    """
    logger.info("Checking metric thresholds")
    
    db = SessionLocal()
    try:
        analytics = AnalyticsService(db)
        redis = redis_client.get_cache_client()
        
        alerts = []
        
        # Check Redis memory usage
        redis_memory = redis.get("system:metric:redis_memory_usage")
        if redis_memory and float(redis_memory) > 100:  # 100 MB threshold
            alerts.append({
                "metric": "redis_memory_usage",
                "value": float(redis_memory),
                "threshold": 100,
                "unit": "MB",
            })
        
        # Check database pool usage
        from app.db.session import engine
        pool = engine.pool
        pool_usage_percent = (pool.checkedout() / pool.size()) * 100 if pool.size() > 0 else 0
        
        if pool_usage_percent > 80:  # 80% threshold
            alerts.append({
                "metric": "db_pool_usage",
                "value": pool_usage_percent,
                "threshold": 80,
                "unit": "%",
            })
        
        # Check slow API requests
        slow_requests = redis.llen("api:slow_requests")
        if slow_requests > 50:  # More than 50 slow requests in last 24h
            alerts.append({
                "metric": "slow_api_requests",
                "value": slow_requests,
                "threshold": 50,
                "unit": "requests",
            })
        
        # Send alerts if any thresholds exceeded
        if alerts:
            alert_message = "System metrics exceeded thresholds:\n"
            for alert in alerts:
                alert_message += f"- {alert['metric']}: {alert['value']}{alert['unit']} (threshold: {alert['threshold']}{alert['unit']})\n"
            
            send_alert(
                subject="System Metrics Alert",
                message=alert_message,
                severity="warning",
            )
            
            logger.warning(f"Metric thresholds exceeded: {alerts}")
        
        return {
            "status": "success",
            "alerts": alerts,
        }
        
    except Exception as e:
        logger.error(f"Threshold check failed: {e}")
        raise
    finally:
        db.close()


@celery_app.task(base=MonitoringTask, bind=True, name="app.tasks.monitoring_tasks.collect_metrics")
def collect_metrics(self):
    """
    Collect system metrics for monitoring.
    
    This task can be scheduled to collect metrics periodically.
    """
    logger.info("Collecting system metrics")
    
    try:
        # TODO: Implement metrics collection logic
        # Collect task execution metrics
        # Collect scraping success rates
        # Collect API response times
        logger.info("Metrics collection completed (placeholder)")
        return {
            "status": "success",
            "metrics": {},
        }
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        raise
