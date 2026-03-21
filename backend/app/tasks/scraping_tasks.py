"""
Celery tasks for job scraping operations.

This module contains tasks for scraping jobs from external sources
(LinkedIn, Indeed, Naukri, Monster) and importing jobs from URLs.

Implements Requirements 1.8, 15.2, 15.3:
- Scheduled scraping tasks for each source
- Error handling with retries and circuit breaker
- Admin alerts after consecutive failures
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
from celery import Task
from app.tasks.celery_app import celery_app
from app.core.logging import logger
from app.core.redis import redis_client
from app.db.session import SessionLocal


class ScrapingTask(Task):
    """Base class for scraping tasks with error handling."""
    
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True


class CircuitBreaker:
    """
    Circuit breaker pattern for failing sources.
    
    Implements Requirement 15.3:
    - Tracks consecutive failures per source
    - Opens circuit after 3 consecutive failures
    - Prevents further attempts until cooldown period
    - Sends admin alerts when circuit opens
    """
    
    FAILURE_THRESHOLD = 3
    COOLDOWN_PERIOD = 3600  # 1 hour in seconds
    
    @staticmethod
    def get_failure_count(source: str) -> int:
        """Get consecutive failure count for source."""
        redis = redis_client.get_cache_client()
        key = f"circuit_breaker:{source}:failures"
        count = redis.get(key)
        return int(count) if count else 0
    
    @staticmethod
    def increment_failure(source: str) -> int:
        """Increment failure count for source."""
        redis = redis_client.get_cache_client()
        key = f"circuit_breaker:{source}:failures"
        count = redis.incr(key)
        redis.expire(key, CircuitBreaker.COOLDOWN_PERIOD)
        return count
    
    @staticmethod
    def reset_failures(source: str) -> None:
        """Reset failure count for source."""
        redis = redis_client.get_cache_client()
        key = f"circuit_breaker:{source}:failures"
        redis.delete(key)
    
    @staticmethod
    def is_circuit_open(source: str) -> bool:
        """Check if circuit is open for source."""
        redis = redis_client.get_cache_client()
        key = f"circuit_breaker:{source}:open"
        return redis.exists(key) > 0
    
    @staticmethod
    def open_circuit(source: str) -> None:
        """Open circuit for source."""
        redis = redis_client.get_cache_client()
        key = f"circuit_breaker:{source}:open"
        redis.setex(key, CircuitBreaker.COOLDOWN_PERIOD, "1")
        logger.warning(
            f"Circuit breaker OPENED for {source}. "
            f"Cooldown period: {CircuitBreaker.COOLDOWN_PERIOD}s"
        )
    
    @staticmethod
    def send_admin_alert(source: str, error_message: str) -> None:
        """
        Send alert to administrators about scraping failures.
        
        Implements Requirement 15.7:
        - Logs critical error for admin monitoring
        - In production, this would integrate with alerting service (email, Slack, PagerDuty)
        """
        logger.critical(
            f"ADMIN ALERT: Scraping source '{source}' has failed {CircuitBreaker.FAILURE_THRESHOLD} "
            f"consecutive times. Circuit breaker activated. Last error: {error_message}"
        )
        
        # TODO: In production, integrate with alerting service
        # - Send email to admins
        # - Post to Slack channel
        # - Create PagerDuty incident
        # Example:
        # send_email(
        #     to=settings.ADMIN_EMAILS,
        #     subject=f"Scraping Alert: {source} circuit breaker activated",
        #     body=f"Source {source} has failed {CircuitBreaker.FAILURE_THRESHOLD} times. Error: {error_message}"
        # )


def run_async_scraping(source_platform: str, scraper_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Helper function to run async scraping in sync Celery task.
    
    Args:
        source_platform: Platform to scrape
        scraper_config: Optional scraper configuration
        
    Returns:
        Scraping result dictionary
    """
    import time
    from app.services.scraping import scrape_and_process_jobs
    from app.services.analytics import AnalyticsService
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Track start time
        start_time = time.time()
        
        # Run async scraping function
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            scrape_and_process_jobs(source_platform, db, scraper_config)
        )
        
        # Calculate duration
        duration_seconds = time.time() - start_time
        result['duration'] = duration_seconds
        
        # Track scraping metrics (Requirement 19.3)
        analytics = AnalyticsService(db)
        analytics.track_scraping_result(
            source_platform=source_platform,
            success=result.get('success', False),
            duration_seconds=duration_seconds,
            jobs_found=result.get('jobs_found', 0),
            jobs_created=result.get('jobs_created', 0),
            jobs_updated=result.get('jobs_updated', 0),
            error_message=result.get('error') if not result.get('success') else None,
        )
        
        return result
    except Exception as e:
        # Track failure
        duration_seconds = time.time() - start_time if 'start_time' in locals() else 0
        try:
            analytics = AnalyticsService(db)
            analytics.track_scraping_result(
                source_platform=source_platform,
                success=False,
                duration_seconds=duration_seconds,
                error_message=str(e),
            )
        except Exception:
            pass  # Don't let metrics tracking break the error handling
        raise
    finally:
        db.close()


@celery_app.task(base=ScrapingTask, bind=True, name="app.tasks.scraping_tasks.scrape_linkedin_jobs")
def scrape_linkedin_jobs(self):
    """
    Scrape jobs from LinkedIn RSS feeds.
    
    Implements Requirements 1.1, 1.8, 15.2, 15.3:
    - Scheduled to run every 6 hours via Celery Beat
    - Handles task failures with retries
    - Implements circuit breaker pattern
    - Sends admin alerts after 3 consecutive failures
    
    Returns:
        Dictionary with scraping results
    """
    source = "linkedin"
    
    # Check circuit breaker
    if CircuitBreaker.is_circuit_open(source):
        logger.warning(f"Circuit breaker is OPEN for {source}. Skipping scraping.")
        return {
            "status": "skipped",
            "source": source,
            "reason": "circuit_breaker_open",
            "jobs_found": 0,
            "jobs_created": 0,
            "jobs_updated": 0,
        }
    
    logger.info(f"Starting {source} job scraping task")
    
    try:
        # Run scraping
        result = run_async_scraping(source)
        
        if result['success']:
            # Reset failure count on success
            CircuitBreaker.reset_failures(source)
            
            logger.info(
                f"{source} scraping completed successfully: "
                f"found={result['jobs_found']}, created={result['jobs_created']}, "
                f"updated={result['jobs_updated']}"
            )
            
            return {
                "status": "success",
                "source": source,
                "jobs_found": result['jobs_found'],
                "jobs_created": result['jobs_created'],
                "jobs_updated": result['jobs_updated'],
                "duration": result['duration'],
            }
        else:
            # Handle failure
            failure_count = CircuitBreaker.increment_failure(source)
            
            logger.error(
                f"{source} scraping failed (failure {failure_count}/{CircuitBreaker.FAILURE_THRESHOLD}): "
                f"{result.get('error', 'Unknown error')}"
            )
            
            # Check if threshold reached
            if failure_count >= CircuitBreaker.FAILURE_THRESHOLD:
                CircuitBreaker.open_circuit(source)
                CircuitBreaker.send_admin_alert(source, result.get('error', 'Unknown error'))
            
            # Raise exception to trigger Celery retry
            raise Exception(result.get('error', 'Scraping failed'))
            
    except Exception as e:
        logger.error(f"{source} scraping task failed: {e}", exc_info=True)
        
        # Increment failure count
        failure_count = CircuitBreaker.increment_failure(source)
        
        # Check if threshold reached
        if failure_count >= CircuitBreaker.FAILURE_THRESHOLD:
            CircuitBreaker.open_circuit(source)
            CircuitBreaker.send_admin_alert(source, str(e))
        
        raise


@celery_app.task(base=ScrapingTask, bind=True, name="app.tasks.scraping_tasks.scrape_indeed_jobs")
def scrape_indeed_jobs(self):
    """
    Scrape jobs from Indeed API.
    
    Implements Requirements 1.2, 1.8, 15.2, 15.3:
    - Scheduled to run every 6 hours via Celery Beat
    - Handles task failures with retries
    - Implements circuit breaker pattern
    - Sends admin alerts after 3 consecutive failures
    
    Returns:
        Dictionary with scraping results
    """
    source = "indeed"
    
    # Check circuit breaker
    if CircuitBreaker.is_circuit_open(source):
        logger.warning(f"Circuit breaker is OPEN for {source}. Skipping scraping.")
        return {
            "status": "skipped",
            "source": source,
            "reason": "circuit_breaker_open",
            "jobs_found": 0,
            "jobs_created": 0,
            "jobs_updated": 0,
        }
    
    logger.info(f"Starting {source} job scraping task")
    
    try:
        # Run scraping
        result = run_async_scraping(source)
        
        if result['success']:
            # Reset failure count on success
            CircuitBreaker.reset_failures(source)
            
            logger.info(
                f"{source} scraping completed successfully: "
                f"found={result['jobs_found']}, created={result['jobs_created']}, "
                f"updated={result['jobs_updated']}"
            )
            
            return {
                "status": "success",
                "source": source,
                "jobs_found": result['jobs_found'],
                "jobs_created": result['jobs_created'],
                "jobs_updated": result['jobs_updated'],
                "duration": result['duration'],
            }
        else:
            # Handle failure
            failure_count = CircuitBreaker.increment_failure(source)
            
            logger.error(
                f"{source} scraping failed (failure {failure_count}/{CircuitBreaker.FAILURE_THRESHOLD}): "
                f"{result.get('error', 'Unknown error')}"
            )
            
            # Check if threshold reached
            if failure_count >= CircuitBreaker.FAILURE_THRESHOLD:
                CircuitBreaker.open_circuit(source)
                CircuitBreaker.send_admin_alert(source, result.get('error', 'Unknown error'))
            
            # Raise exception to trigger Celery retry
            raise Exception(result.get('error', 'Scraping failed'))
            
    except Exception as e:
        logger.error(f"{source} scraping task failed: {e}", exc_info=True)
        
        # Increment failure count
        failure_count = CircuitBreaker.increment_failure(source)
        
        # Check if threshold reached
        if failure_count >= CircuitBreaker.FAILURE_THRESHOLD:
            CircuitBreaker.open_circuit(source)
            CircuitBreaker.send_admin_alert(source, str(e))
        
        raise


@celery_app.task(base=ScrapingTask, bind=True, name="app.tasks.scraping_tasks.scrape_naukri_jobs")
def scrape_naukri_jobs(self):
    """
    Scrape jobs from Naukri via web scraping.
    
    Implements Requirements 1.3, 1.8, 15.2, 15.3:
    - Scheduled to run every 6 hours via Celery Beat
    - Handles task failures with retries
    - Implements circuit breaker pattern
    - Sends admin alerts after 3 consecutive failures
    
    Returns:
        Dictionary with scraping results
    """
    source = "naukri"
    
    # Check circuit breaker
    if CircuitBreaker.is_circuit_open(source):
        logger.warning(f"Circuit breaker is OPEN for {source}. Skipping scraping.")
        return {
            "status": "skipped",
            "source": source,
            "reason": "circuit_breaker_open",
            "jobs_found": 0,
            "jobs_created": 0,
            "jobs_updated": 0,
        }
    
    logger.info(f"Starting {source} job scraping task")
    
    try:
        # Run scraping
        result = run_async_scraping(source)
        
        if result['success']:
            # Reset failure count on success
            CircuitBreaker.reset_failures(source)
            
            logger.info(
                f"{source} scraping completed successfully: "
                f"found={result['jobs_found']}, created={result['jobs_created']}, "
                f"updated={result['jobs_updated']}"
            )
            
            return {
                "status": "success",
                "source": source,
                "jobs_found": result['jobs_found'],
                "jobs_created": result['jobs_created'],
                "jobs_updated": result['jobs_updated'],
                "duration": result['duration'],
            }
        else:
            # Handle failure
            failure_count = CircuitBreaker.increment_failure(source)
            
            logger.error(
                f"{source} scraping failed (failure {failure_count}/{CircuitBreaker.FAILURE_THRESHOLD}): "
                f"{result.get('error', 'Unknown error')}"
            )
            
            # Check if threshold reached
            if failure_count >= CircuitBreaker.FAILURE_THRESHOLD:
                CircuitBreaker.open_circuit(source)
                CircuitBreaker.send_admin_alert(source, result.get('error', 'Unknown error'))
            
            # Raise exception to trigger Celery retry
            raise Exception(result.get('error', 'Scraping failed'))
            
    except Exception as e:
        logger.error(f"{source} scraping task failed: {e}", exc_info=True)
        
        # Increment failure count
        failure_count = CircuitBreaker.increment_failure(source)
        
        # Check if threshold reached
        if failure_count >= CircuitBreaker.FAILURE_THRESHOLD:
            CircuitBreaker.open_circuit(source)
            CircuitBreaker.send_admin_alert(source, str(e))
        
        raise


@celery_app.task(base=ScrapingTask, bind=True, name="app.tasks.scraping_tasks.scrape_monster_jobs")
def scrape_monster_jobs(self):
    """
    Scrape jobs from Monster via web scraping.
    
    Implements Requirements 1.4, 1.8, 15.2, 15.3:
    - Scheduled to run every 6 hours via Celery Beat
    - Handles task failures with retries
    - Implements circuit breaker pattern
    - Sends admin alerts after 3 consecutive failures
    
    Returns:
        Dictionary with scraping results
    """
    source = "monster"
    
    # Check circuit breaker
    if CircuitBreaker.is_circuit_open(source):
        logger.warning(f"Circuit breaker is OPEN for {source}. Skipping scraping.")
        return {
            "status": "skipped",
            "source": source,
            "reason": "circuit_breaker_open",
            "jobs_found": 0,
            "jobs_created": 0,
            "jobs_updated": 0,
        }
    
    logger.info(f"Starting {source} job scraping task")
    
    try:
        # Run scraping
        result = run_async_scraping(source)
        
        if result['success']:
            # Reset failure count on success
            CircuitBreaker.reset_failures(source)
            
            logger.info(
                f"{source} scraping completed successfully: "
                f"found={result['jobs_found']}, created={result['jobs_created']}, "
                f"updated={result['jobs_updated']}"
            )
            
            return {
                "status": "success",
                "source": source,
                "jobs_found": result['jobs_found'],
                "jobs_created": result['jobs_created'],
                "jobs_updated": result['jobs_updated'],
                "duration": result['duration'],
            }
        else:
            # Handle failure
            failure_count = CircuitBreaker.increment_failure(source)
            
            logger.error(
                f"{source} scraping failed (failure {failure_count}/{CircuitBreaker.FAILURE_THRESHOLD}): "
                f"{result.get('error', 'Unknown error')}"
            )
            
            # Check if threshold reached
            if failure_count >= CircuitBreaker.FAILURE_THRESHOLD:
                CircuitBreaker.open_circuit(source)
                CircuitBreaker.send_admin_alert(source, result.get('error', 'Unknown error'))
            
            # Raise exception to trigger Celery retry
            raise Exception(result.get('error', 'Scraping failed'))
            
    except Exception as e:
        logger.error(f"{source} scraping task failed: {e}", exc_info=True)
        
        # Increment failure count
        failure_count = CircuitBreaker.increment_failure(source)
        
        # Check if threshold reached
        if failure_count >= CircuitBreaker.FAILURE_THRESHOLD:
            CircuitBreaker.open_circuit(source)
            CircuitBreaker.send_admin_alert(source, str(e))
        
        raise


@celery_app.task(base=ScrapingTask, bind=True, name="app.tasks.scraping_tasks.import_job_from_url")
def import_job_from_url(self, employer_id: str, url: str):
    """
    Import a job by scraping from a provided URL.
    
    Implements Requirements 5.9, 5.10, 5.11, 5.12, 5.13, 5.14:
    - Fetches job page HTML from URL
    - Extracts job details using domain-specific parser
    - Checks for duplicates
    - Creates job with source_type='url_import'
    - Consumes employer's import quota on success
    
    This is a high-priority task triggered by employer actions.
    
    Args:
        employer_id: ID of the employer importing the job
        url: URL of the job to import
        
    Returns:
        Dictionary with import result
    """
    from uuid import UUID
    from app.services.url_import import validate_import_url, get_platform_from_domain
    from app.services.scraping import (
        LinkedInScraper, IndeedScraper, NaukriScraper, MonsterScraper,
        create_scraping_task, update_scraping_task
    )
    from app.models.scraping_task import TaskType, TaskStatus
    from app.models.job import Job, SourceType
    from app.models.job_source import JobSource
    from app.services.deduplication import find_duplicates
    from app.services.quality_scoring import calculate_quality_score
    from app.services.subscription import consume_quota
    from app.core.redis import redis_client
    from app.core.config import settings
    import requests
    from bs4 import BeautifulSoup
    
    logger.info(f"Starting URL import task for employer {employer_id}: {url}")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Validate URL and extract domain
        is_valid, domain, error = validate_import_url(url)
        if not is_valid:
            logger.error(f"URL validation failed: {error}")
            return {
                "status": "failed",
                "employer_id": employer_id,
                "url": url,
                "job_id": None,
                "error": error,
            }
        
        # Get platform from domain
        platform = get_platform_from_domain(domain)
        if not platform:
            error = f"Could not determine platform from domain: {domain}"
            logger.error(error)
            return {
                "status": "failed",
                "employer_id": employer_id,
                "url": url,
                "job_id": None,
                "error": error,
            }
        
        # Create scraping task record
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        task = loop.run_until_complete(
            create_scraping_task(
                task_type=TaskType.URL_IMPORT,
                source_platform=platform,
                target_url=url,
                db_session=db
            )
        )
        
        # Update task status to RUNNING
        loop.run_until_complete(
            update_scraping_task(
                task.id,
                {
                    'status': TaskStatus.RUNNING,
                    'started_at': datetime.utcnow()
                },
                db_session=db
            )
        )
        
        # Fetch job page HTML
        logger.info(f"Fetching job page from {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Select appropriate scraper based on platform
        scraper = None
        if platform == 'linkedin':
            scraper = LinkedInScraper(rss_feed_url="", rate_limit=10)
        elif platform == 'indeed':
            scraper = IndeedScraper(api_key=settings.INDEED_API_KEY or "", query="", rate_limit=20)
        elif platform == 'naukri':
            scraper = NaukriScraper(search_url="", rate_limit=5)
        elif platform == 'monster':
            scraper = MonsterScraper(search_url="", rate_limit=5)
        
        if not scraper:
            error = f"No scraper available for platform: {platform}"
            logger.error(error)
            
            # Update task status to FAILED
            loop.run_until_complete(
                update_scraping_task(
                    task.id,
                    {
                        'status': TaskStatus.FAILED,
                        'error_message': error,
                        'completed_at': datetime.utcnow()
                    },
                    db_session=db
                )
            )
            
            return {
                "status": "failed",
                "employer_id": employer_id,
                "url": url,
                "job_id": None,
                "error": error,
            }
        
        # Extract job details using platform-specific parser
        logger.info(f"Extracting job details from {platform} page")
        job_data = scraper._parse_job_page(soup, url)
        
        if not job_data:
            error = f"Failed to extract job details from {url}"
            logger.error(error)
            
            # Update task status to FAILED
            loop.run_until_complete(
                update_scraping_task(
                    task.id,
                    {
                        'status': TaskStatus.FAILED,
                        'error_message': error,
                        'completed_at': datetime.utcnow()
                    },
                    db_session=db
                )
            )
            
            return {
                "status": "failed",
                "employer_id": employer_id,
                "url": url,
                "job_id": None,
                "error": error,
            }
        
        # Normalize job data
        normalized_job = scraper.normalize_job(job_data)
        
        # Check for duplicates
        logger.info(f"Checking for duplicates")
        job_dict = {
            "company": normalized_job['company'],
            "title": normalized_job['title'],
            "location": normalized_job['location'],
            "description": normalized_job['description']
        }
        
        duplicates = find_duplicates(job_dict, [
            {
                "id": job.id,
                "company": job.company,
                "title": job.title,
                "location": job.location,
                "description": job.description
            }
            for job in db.query(Job).filter(Job.status == "active").all()
        ])
        
        if duplicates:
            # Duplicate found - return existing job ID
            duplicate_job, match_details = duplicates[0]
            existing_job_id = duplicate_job["id"]
            
            logger.info(f"Duplicate job found: {existing_job_id}")
            
            # Update task status to COMPLETED (but no new job created)
            loop.run_until_complete(
                update_scraping_task(
                    task.id,
                    {
                        'status': TaskStatus.COMPLETED,
                        'jobs_found': 1,
                        'jobs_created': 0,
                        'jobs_updated': 0,
                        'completed_at': datetime.utcnow()
                    },
                    db_session=db
                )
            )
            
            return {
                "status": "duplicate",
                "employer_id": employer_id,
                "url": url,
                "job_id": str(existing_job_id),
                "message": "This job already exists in the database",
            }
        
        # Calculate quality score (URL imports get higher score than aggregated)
        quality_score = calculate_quality_score(
            source_type=SourceType.URL_IMPORT,
            job_data={
                "title": normalized_job['title'],
                "company": normalized_job['company'],
                "description": normalized_job['description'],
                "requirements": normalized_job.get('requirements'),
                "responsibilities": normalized_job.get('responsibilities'),
                "salary_min": normalized_job.get('salary_min'),
                "salary_max": normalized_job.get('salary_max'),
                "tags": normalized_job.get('tags', []),
            },
            posted_at=normalized_job['posted_at']
        )
        
        # Create job record with source_type='url_import'
        logger.info(f"Creating new job from URL import")
        new_job = Job(
            title=normalized_job['title'],
            company=normalized_job['company'],
            location=normalized_job['location'],
            remote=normalized_job['remote'],
            job_type=normalized_job['job_type'],
            experience_level=normalized_job['experience_level'],
            description=normalized_job['description'],
            requirements=normalized_job.get('requirements'),
            responsibilities=normalized_job.get('responsibilities'),
            salary_min=normalized_job.get('salary_min'),
            salary_max=normalized_job.get('salary_max'),
            salary_currency=normalized_job.get('salary_currency', 'USD'),
            source_type=SourceType.URL_IMPORT,
            source_url=url,
            source_platform=platform,
            employer_id=UUID(employer_id),
            quality_score=quality_score,
            status="active",
            posted_at=normalized_job['posted_at'],
            expires_at=normalized_job['expires_at'],
            featured=False,
            tags=normalized_job.get('tags'),
            application_count=0,
            view_count=0,
        )
        
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        
        # Create job source record
        job_source = JobSource(
            job_id=new_job.id,
            source_platform=platform,
            source_url=url,
            scraped_at=datetime.utcnow(),
            last_verified_at=datetime.utcnow(),
            is_active=True
        )
        db.add(job_source)
        db.commit()
        
        # Consume employer's import quota
        logger.info(f"Consuming import quota for employer {employer_id}")
        redis = redis_client.get_cache_client()
        consume_quota(db, redis, UUID(employer_id), "url_import")
        
        # Update task status to COMPLETED
        loop.run_until_complete(
            update_scraping_task(
                task.id,
                {
                    'status': TaskStatus.COMPLETED,
                    'jobs_found': 1,
                    'jobs_created': 1,
                    'jobs_updated': 0,
                    'completed_at': datetime.utcnow()
                },
                db_session=db
            )
        )
        
        logger.info(f"URL import completed successfully: job_id={new_job.id}")
        
        return {
            "status": "success",
            "employer_id": employer_id,
            "url": url,
            "job_id": str(new_job.id),
            "message": "Job imported successfully",
        }
        
    except Exception as e:
        logger.error(f"URL import task failed for {url}: {e}", exc_info=True)
        
        # Update task status to FAILED if task was created
        try:
            if 'task' in locals():
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                loop.run_until_complete(
                    update_scraping_task(
                        task.id,
                        {
                            'status': TaskStatus.FAILED,
                            'error_message': str(e),
                            'completed_at': datetime.utcnow()
                        },
                        db_session=db
                    )
                )
        except:
            pass
        
        return {
            "status": "failed",
            "employer_id": employer_id,
            "url": url,
            "job_id": None,
            "error": str(e),
        }
    finally:
        db.close()
