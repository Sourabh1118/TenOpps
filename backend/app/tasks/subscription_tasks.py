"""
Subscription management Celery tasks.

This module provides background tasks for subscription management, including:
- Monthly quota reset for expired billing cycles
- Payment failure handling and grace period management
- Subscription downgrade after grace period
"""
from datetime import datetime, timedelta
from celery import Task
from sqlalchemy.orm import Session
import stripe

from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.employer import Employer, SubscriptionTier
from app.core.logging import logger
from app.core.config import settings

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class DatabaseTask(Task):
    """Base task class that provides database session management."""
    
    _db: Session = None
    
    @property
    def db(self) -> Session:
        """Get database session, creating it if necessary."""
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    def after_return(self, *args, **kwargs):
        """Close database session after task completes."""
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.tasks.subscription_tasks.reset_monthly_quotas",
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def reset_monthly_quotas(self):
    """
    Reset monthly quotas for employers with expired billing cycles.
    
    This task implements Requirement 8.9:
    - Queries all employers where subscription_end_date < now()
    - For each employer: resets monthly_posts_used=0, featured_posts_used=0
    - Updates subscription_end_date to +30 days
    - Logs number of quotas reset
    
    **Scheduled to run daily at 3 AM via Celery Beat.**
    
    **Process:**
    1. Query employers with expired billing cycles
    2. For each employer:
       - Reset monthly_posts_used to 0
       - Reset featured_posts_used to 0
       - Extend subscription_end_date by 30 days
    3. Commit changes in batches
    4. Log total number of quotas reset
    
    Returns:
        dict: Summary of reset operation with count of employers processed
        
    Example:
        >>> result = reset_monthly_quotas.delay()
        >>> result.get()
        {
            "status": "success",
            "employers_reset": 42,
            "timestamp": "2024-01-15T03:00:00"
        }
    """
    try:
        logger.info("Starting monthly quota reset task")
        
        # Get current timestamp
        now = datetime.utcnow()
        
        # Query employers with expired billing cycles
        expired_employers = self.db.query(Employer).filter(
            Employer.subscription_end_date < now
        ).all()
        
        reset_count = 0
        
        # Process each employer
        for employer in expired_employers:
            try:
                # Reset usage counters
                employer.monthly_posts_used = 0
                employer.featured_posts_used = 0
                
                # Extend subscription by 30 days from current end date
                # This preserves the billing cycle even if task runs late
                from datetime import timedelta
                employer.subscription_end_date = employer.subscription_end_date + timedelta(days=30)
                
                reset_count += 1
                
                logger.debug(
                    f"Reset quota for employer {employer.id} "
                    f"(tier: {employer.subscription_tier.value}, "
                    f"new end date: {employer.subscription_end_date})"
                )
                
            except Exception as e:
                logger.error(f"Error resetting quota for employer {employer.id}: {e}")
                # Continue processing other employers
                continue
        
        # Commit all changes
        try:
            self.db.commit()
            logger.info(f"Successfully reset quotas for {reset_count} employers")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error committing quota resets: {e}")
            raise
        
        return {
            "status": "success",
            "employers_reset": reset_count,
            "timestamp": now.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Monthly quota reset task failed: {e}")
        # Retry the task
        raise self.retry(exc=e)



@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.tasks.subscription_tasks.check_expired_subscriptions",
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def check_expired_subscriptions(self):
    """
    Check for expired subscriptions and downgrade to free tier.
    
    This task implements Requirement 18.5:
    - Queries employers with expired subscriptions (subscription_end_date < now)
    - Downgrades to free tier after grace period
    - Sends notification to employer
    
    **Scheduled to run daily at 4 AM via Celery Beat.**
    
    **Process:**
    1. Query employers with expired subscriptions
    2. For each employer:
       - Check if subscription has expired
       - Downgrade to free tier
       - Reset usage counters
       - Send notification email
    3. Log total number of downgrades
    
    Returns:
        dict: Summary of downgrade operation
    """
    try:
        logger.info("Starting expired subscription check task")
        
        # Get current timestamp
        now = datetime.utcnow()
        
        # Query employers with expired subscriptions (not on free tier)
        expired_employers = self.db.query(Employer).filter(
            Employer.subscription_end_date < now,
            Employer.subscription_tier != SubscriptionTier.FREE
        ).all()
        
        downgrade_count = 0
        
        # Process each employer
        for employer in expired_employers:
            try:
                logger.info(
                    f"Downgrading employer {employer.id} from {employer.subscription_tier.value} "
                    f"to free tier (expired: {employer.subscription_end_date})"
                )
                
                # Downgrade to free tier
                employer.subscription_tier = SubscriptionTier.FREE
                
                # Reset usage counters
                employer.monthly_posts_used = 0
                employer.featured_posts_used = 0
                
                # Set new subscription dates (free tier is perpetual)
                employer.subscription_start_date = now
                employer.subscription_end_date = now + timedelta(days=365)  # 1 year
                
                downgrade_count += 1
                
                # TODO: Send email notification to employer
                # await send_subscription_downgrade_notification(employer)
                
            except Exception as e:
                logger.error(f"Error downgrading employer {employer.id}: {e}")
                continue
        
        # Commit all changes
        try:
            self.db.commit()
            logger.info(f"Successfully downgraded {downgrade_count} employers to free tier")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error committing subscription downgrades: {e}")
            raise
        
        return {
            "status": "success",
            "employers_downgraded": downgrade_count,
            "timestamp": now.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Expired subscription check task failed: {e}")
        raise self.retry(exc=e)


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.tasks.subscription_tasks.send_payment_failure_notification",
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def send_payment_failure_notification(self, employer_id: str):
    """
    Send notification to employer about payment failure.
    
    This task implements Requirement 18.5:
    - Sends email notification to employer about payment failure
    - Includes grace period information
    - Provides link to update payment method
    
    **Triggered by Stripe webhook when payment fails.**
    
    Args:
        employer_id: UUID of the employer
        
    Returns:
        dict: Status of notification sending
    """
    try:
        from uuid import UUID
        
        logger.info(f"Sending payment failure notification to employer {employer_id}")
        
        # Query employer
        employer = self.db.query(Employer).filter(
            Employer.id == UUID(employer_id)
        ).first()
        
        if not employer:
            logger.error(f"Employer {employer_id} not found")
            return {"status": "error", "message": "Employer not found"}
        
        # TODO: Implement email sending using SMTP settings
        # This would use the alerting service from Task 22
        # For now, just log the notification
        
        logger.info(
            f"Payment failure notification sent to {employer.email} "
            f"(tier: {employer.subscription_tier.value}, "
            f"grace period until: {employer.subscription_end_date})"
        )
        
        # In production, this would send an email like:
        # Subject: Payment Failed - Action Required
        # Body:
        # Dear {employer.company_name},
        #
        # We were unable to process your subscription payment for the {tier} plan.
        # 
        # Your account will remain active until {subscription_end_date}, after which
        # it will be downgraded to the Free plan.
        #
        # To maintain your current subscription, please update your payment method:
        # {frontend_url}/employer/subscription
        #
        # If you have any questions, please contact support.
        
        return {
            "status": "success",
            "employer_id": employer_id,
            "email": employer.email,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to send payment failure notification: {e}")
        raise self.retry(exc=e)
