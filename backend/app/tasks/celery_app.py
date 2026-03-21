"""
Celery application configuration for background task processing.

This module configures Celery with Redis as the broker and result backend,
sets up task routing, priority queues, and worker configuration.
"""
from celery import Celery
from celery.schedules import crontab
from kombu import Queue, Exchange
from app.core.config import settings
from app.core.logging import logger


# Create Celery app instance
celery_app = Celery(
    "job_aggregation_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.scraping_tasks",
        "app.tasks.maintenance_tasks",
        "app.tasks.monitoring_tasks",
        "app.tasks.subscription_tasks",
    ]
)


# Celery configuration
celery_app.conf.update(
    # Task execution settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task result settings (Requirement 16.7)
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "retry_on_timeout": True,
    },
    
    # Worker settings (Requirement 16.6)
    # Configure 4 workers with 2 threads each for optimal concurrency
    worker_concurrency=4,  # Number of worker processes
    worker_prefetch_multiplier=2,  # Number of tasks to prefetch per worker (2 threads)
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks to prevent memory leaks
    worker_disable_rate_limits=False,
    
    # Task routing and priority queues
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
    
    # Define task queues with priorities
    task_queues=(
        # High priority queue for URL imports and user-initiated tasks
        Queue(
            "high_priority",
            Exchange("high_priority"),
            routing_key="high_priority",
            queue_arguments={"x-max-priority": 10},
        ),
        # Default queue for scheduled scraping tasks
        Queue(
            "default",
            Exchange("default"),
            routing_key="default",
            queue_arguments={"x-max-priority": 5},
        ),
        # Low priority queue for maintenance and cleanup tasks
        Queue(
            "low_priority",
            Exchange("low_priority"),
            routing_key="low_priority",
            queue_arguments={"x-max-priority": 1},
        ),
    ),
    
    # Task routing rules
    task_routes={
        # URL import tasks go to high priority queue
        "app.tasks.scraping_tasks.import_job_from_url": {
            "queue": "high_priority",
            "routing_key": "high_priority",
            "priority": 9,
        },
        # Scheduled scraping tasks go to default queue
        "app.tasks.scraping_tasks.scrape_linkedin_jobs": {
            "queue": "default",
            "routing_key": "default",
            "priority": 5,
        },
        "app.tasks.scraping_tasks.scrape_indeed_jobs": {
            "queue": "default",
            "routing_key": "default",
            "priority": 5,
        },
        "app.tasks.scraping_tasks.scrape_naukri_jobs": {
            "queue": "default",
            "routing_key": "default",
            "priority": 5,
        },
        "app.tasks.scraping_tasks.scrape_monster_jobs": {
            "queue": "default",
            "routing_key": "default",
            "priority": 5,
        },
        # Maintenance tasks go to low priority queue
        "app.tasks.maintenance_tasks.expire_old_jobs": {
            "queue": "low_priority",
            "routing_key": "low_priority",
            "priority": 1,
        },
        "app.tasks.maintenance_tasks.reset_monthly_quotas": {
            "queue": "low_priority",
            "routing_key": "low_priority",
            "priority": 1,
        },
        "app.tasks.maintenance_tasks.remove_expired_featured_listings": {
            "queue": "low_priority",
            "routing_key": "low_priority",
            "priority": 1,
        },
        "app.tasks.maintenance_tasks.update_quality_scores": {
            "queue": "low_priority",
            "routing_key": "low_priority",
            "priority": 1,
        },
    },
    
    # Task execution options
    task_acks_late=True,  # Acknowledge tasks after execution
    task_reject_on_worker_lost=True,  # Reject tasks if worker crashes
    task_track_started=True,  # Track when tasks start
    
    # Retry settings
    task_autoretry_for=(Exception,),
    task_retry_kwargs={"max_retries": 3},
    task_retry_backoff=True,  # Exponential backoff
    task_retry_backoff_max=600,  # Max 10 minutes between retries
    task_retry_jitter=True,  # Add random jitter to retries
    
    # Rate limiting
    task_annotations={
        "app.tasks.scraping_tasks.scrape_linkedin_jobs": {
            "rate_limit": "10/m"  # 10 per minute
        },
        "app.tasks.scraping_tasks.scrape_indeed_jobs": {
            "rate_limit": "20/m"  # 20 per minute
        },
        "app.tasks.scraping_tasks.scrape_naukri_jobs": {
            "rate_limit": "5/m"  # 5 per minute
        },
        "app.tasks.scraping_tasks.scrape_monster_jobs": {
            "rate_limit": "5/m"  # 5 per minute
        },
    },
    
    # Beat schedule for periodic tasks
    beat_schedule={
        # Scrape LinkedIn jobs every 6 hours
        "scrape-linkedin-every-6-hours": {
            "task": "app.tasks.scraping_tasks.scrape_linkedin_jobs",
            "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
            "options": {"queue": "default", "priority": 5},
        },
        # Scrape Indeed jobs every 6 hours (offset by 1 hour)
        "scrape-indeed-every-6-hours": {
            "task": "app.tasks.scraping_tasks.scrape_indeed_jobs",
            "schedule": crontab(minute=0, hour="1,7,13,19"),  # Every 6 hours, offset
            "options": {"queue": "default", "priority": 5},
        },
        # Scrape Naukri jobs every 6 hours (offset by 2 hours)
        "scrape-naukri-every-6-hours": {
            "task": "app.tasks.scraping_tasks.scrape_naukri_jobs",
            "schedule": crontab(minute=0, hour="2,8,14,20"),  # Every 6 hours, offset
            "options": {"queue": "default", "priority": 5},
        },
        # Scrape Monster jobs every 6 hours (offset by 3 hours)
        "scrape-monster-every-6-hours": {
            "task": "app.tasks.scraping_tasks.scrape_monster_jobs",
            "schedule": crontab(minute=0, hour="3,9,15,21"),  # Every 6 hours, offset
            "options": {"queue": "default", "priority": 5},
        },
        # Expire old jobs daily at 2 AM
        "expire-old-jobs-daily": {
            "task": "app.tasks.maintenance_tasks.expire_old_jobs",
            "schedule": crontab(minute=0, hour=2),  # Daily at 2 AM
            "options": {"queue": "low_priority", "priority": 1},
        },
        # Reset monthly quotas daily at midnight
        "reset-monthly-quotas-daily": {
            "task": "app.tasks.subscription_tasks.reset_monthly_quotas",
            "schedule": crontab(minute=0, hour=0),  # Daily at midnight
            "options": {"queue": "low_priority", "priority": 1},
        },
        # Check expired subscriptions daily at 1 AM
        "check-expired-subscriptions-daily": {
            "task": "app.tasks.subscription_tasks.check_expired_subscriptions",
            "schedule": crontab(minute=0, hour=1),  # Daily at 1 AM
            "options": {"queue": "low_priority", "priority": 1},
        },
        # Remove expired featured listings daily at 4 AM
        "remove-expired-featured-daily": {
            "task": "app.tasks.maintenance_tasks.remove_expired_featured_listings",
            "schedule": crontab(minute=0, hour=4),  # Daily at 4 AM
            "options": {"queue": "low_priority", "priority": 1},
        },
        # Update quality scores for aging jobs daily at 5 AM
        "update-quality-scores-daily": {
            "task": "app.tasks.maintenance_tasks.update_quality_scores",
            "schedule": crontab(minute=0, hour=5),  # Daily at 5 AM
            "options": {"queue": "low_priority", "priority": 1},
        },
        # Archive jobs older than 180 days weekly on Sunday at 3 AM
        "archive-old-jobs-weekly": {
            "task": "app.tasks.maintenance_tasks.archive_old_jobs",
            "schedule": crontab(minute=0, hour=3, day_of_week=0),  # Weekly on Sunday at 3 AM
            "options": {"queue": "low_priority", "priority": 1},
        },
        # Collect system metrics every hour (Requirement 19.7, 19.8)
        "collect-system-metrics-hourly": {
            "task": "app.tasks.monitoring_tasks.collect_system_metrics",
            "schedule": crontab(minute=0),  # Every hour
            "options": {"queue": "low_priority", "priority": 1},
        },
        # Check metric thresholds every 15 minutes (Requirement 19.8)
        "check-metric-thresholds-15min": {
            "task": "app.tasks.monitoring_tasks.check_metric_thresholds",
            "schedule": crontab(minute="*/15"),  # Every 15 minutes
            "options": {"queue": "low_priority", "priority": 1},
        },
    },
)


# Task event monitoring
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Set up periodic tasks after Celery is configured."""
    logger.info("Celery periodic tasks configured")


@celery_app.on_after_finalize.connect
def setup_task_monitoring(sender, **kwargs):
    """Set up task monitoring after Celery is finalized."""
    logger.info("Celery task monitoring configured")


# Task event handlers
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery configuration."""
    logger.info(f"Request: {self.request!r}")
    return {"status": "success", "message": "Celery is working!"}


def get_celery_app() -> Celery:
    """
    Get the Celery app instance.
    
    Returns:
        Configured Celery app instance
    """
    return celery_app
