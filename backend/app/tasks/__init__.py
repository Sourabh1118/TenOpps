"""
Background task processing with Celery.

This package contains the Celery application configuration and task definitions
for job scraping, maintenance, and monitoring operations.
"""
from app.tasks.celery_app import celery_app, get_celery_app

__all__ = ["celery_app", "get_celery_app"]
