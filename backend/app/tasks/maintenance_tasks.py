"""
Celery tasks for system maintenance operations.

This module contains tasks for job expiration, quota resets,
featured listing management, and quality score updates.
"""
from celery import Task
from app.tasks.celery_app import celery_app
from app.core.logging import logger


class MaintenanceTask(Task):
    """Base class for maintenance tasks."""
    
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 2}
    retry_backoff = True


@celery_app.task(base=MaintenanceTask, bind=True, name="app.tasks.maintenance_tasks.expire_old_jobs")
def expire_old_jobs(self):
    """
    Mark jobs as expired if they are past their expiration date.
    
    This task runs daily at 2 AM to identify and expire old jobs.
    Implements Requirements 10.3 and 10.4:
    - Identifies jobs past their expiration date
    - Updates their status to 'expired'
    
    Returns:
        Dictionary with status and count of jobs expired
    """
    logger.info("Starting job expiration task")
    
    try:
        from datetime import datetime
        from app.db.session import SessionLocal
        from app.models.job import Job, JobStatus
        
        # Create database session
        db = SessionLocal()
        
        try:
            # Query jobs where expires_at < current_date and status='active'
            # Implements Requirement 10.3
            current_time = datetime.utcnow()
            expired_jobs = db.query(Job).filter(
                Job.expires_at < current_time,
                Job.status == JobStatus.ACTIVE
            ).all()
            
            jobs_expired = 0
            
            # Update status to 'expired'
            # Implements Requirement 10.4
            for job in expired_jobs:
                job.status = JobStatus.EXPIRED
                jobs_expired += 1
                logger.info(f"Expired job {job.id}: {job.title} at {job.company}")
            
            # Commit changes
            db.commit()
            
            logger.info(f"Job expiration task completed: {jobs_expired} jobs expired")
            
            return {
                "status": "success",
                "jobs_expired": jobs_expired,
            }
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Job expiration task failed: {e}")
        raise


@celery_app.task(base=MaintenanceTask, bind=True, name="app.tasks.maintenance_tasks.reset_monthly_quotas")
def reset_monthly_quotas(self):
    """
    Reset monthly usage quotas for employers at billing cycle end.
    
    This task runs daily at 3 AM to check for expired billing cycles
    and reset usage counters.
    """
    logger.info("Starting monthly quota reset task")
    
    try:
        # TODO: Implement quota reset logic
        # Query employers where subscription_end_date < current_date
        # Reset monthly_posts_used and featured_posts_used to 0
        logger.info("Monthly quota reset task completed (placeholder)")
        return {
            "status": "success",
            "quotas_reset": 0,
        }
    except Exception as e:
        logger.error(f"Monthly quota reset task failed: {e}")
        raise


@celery_app.task(base=MaintenanceTask, bind=True, name="app.tasks.maintenance_tasks.remove_expired_featured_listings")
def remove_expired_featured_listings(self):
    """
    Remove featured flag from expired featured listings.
    
    This task runs daily at 4 AM to check for expired featured listings.
    Implements Requirement 11.7: Featured listings should expire and have
    the featured flag removed.
    
    Returns:
        Dictionary with status and count of featured flags removed
    """
    logger.info("Starting featured listing expiration task")
    
    try:
        from datetime import datetime
        from app.db.session import SessionLocal
        from app.models.job import Job
        
        # Create database session
        db = SessionLocal()
        
        try:
            # Query jobs where featured=true and expires_at < current_date
            current_time = datetime.utcnow()
            expired_featured_jobs = db.query(Job).filter(
                Job.featured == True,
                Job.expires_at < current_time
            ).all()
            
            featured_removed = 0
            
            # Remove featured flag from expired jobs
            for job in expired_featured_jobs:
                job.featured = False
                featured_removed += 1
                logger.info(f"Removed featured flag from expired job {job.id}")
            
            # Commit changes
            db.commit()
            
            logger.info(f"Featured listing expiration task completed: {featured_removed} featured flags removed")
            
            return {
                "status": "success",
                "featured_removed": featured_removed,
            }
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Featured listing expiration task failed: {e}")
        raise


@celery_app.task(base=MaintenanceTask, bind=True, name="app.tasks.maintenance_tasks.update_quality_scores")
def update_quality_scores(self):
    """
    Update quality scores for aging jobs.
    
    This task runs daily at 5 AM to recalculate quality scores
    based on job freshness.
    """
    logger.info("Starting quality score update task")
    
    try:
        # TODO: Implement quality score update logic
        # Query active jobs and recalculate quality scores
        # Update quality_score field based on age
        logger.info("Quality score update task completed (placeholder)")
        return {
            "status": "success",
            "scores_updated": 0,
        }
    except Exception as e:
        logger.error(f"Quality score update task failed: {e}")
        raise


@celery_app.task(base=MaintenanceTask, bind=True, name="app.tasks.maintenance_tasks.archive_old_jobs")
def archive_old_jobs(self):
    """
    Archive jobs older than 180 days to cold storage.
    
    This task runs weekly to identify and archive old jobs.
    Implements Requirement 17.4:
    - Archives jobs older than 180 days
    - Moves archived jobs to separate table or marks them
    - Runs weekly
    
    Returns:
        Dictionary with status and count of jobs archived
    """
    logger.info("Starting job archival task")
    
    try:
        from datetime import datetime, timedelta
        from app.db.session import SessionLocal
        from app.models.job import Job, JobStatus
        
        # Create database session
        db = SessionLocal()
        
        try:
            # Calculate cutoff date (180 days ago)
            cutoff_date = datetime.utcnow() - timedelta(days=180)
            
            # Query jobs older than 180 days
            # For now, we'll mark them as archived by setting status to DELETED
            # In a production system, you might move them to a separate table
            old_jobs = db.query(Job).filter(
                Job.posted_at < cutoff_date,
                Job.status.in_([JobStatus.ACTIVE, JobStatus.EXPIRED, JobStatus.FILLED])
            ).all()
            
            jobs_archived = 0
            
            # Archive jobs (mark as deleted for now)
            for job in old_jobs:
                job.status = JobStatus.DELETED
                jobs_archived += 1
                logger.info(
                    f"Archived job {job.id}: {job.title} at {job.company} "
                    f"(posted {job.posted_at})"
                )
            
            # Commit changes
            db.commit()
            
            logger.info(
                f"Job archival task completed: {jobs_archived} jobs archived "
                f"(older than {cutoff_date})"
            )
            
            return {
                "status": "success",
                "jobs_archived": jobs_archived,
                "cutoff_date": cutoff_date.isoformat(),
            }
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Job archival task failed: {e}")
        raise
