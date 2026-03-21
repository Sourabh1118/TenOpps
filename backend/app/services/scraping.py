"""
Scraping service for the job aggregation platform.

This module provides the base infrastructure for web scraping operations:
- BaseScraper abstract class with rate limiting and retry logic
- Job data normalization functions
- Scraping task management
- Redis-based rate limiting for external sources
- Robots.txt compliance checking
"""
import time
import asyncio
import requests
import feedparser
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum

from app.core.logging import logger
from app.core.redis import redis_client
from app.models.job import JobType, ExperienceLevel, SourceType
from app.models.scraping_task import TaskType, TaskStatus
from app.services.robots_compliance import check_robots_compliance, get_crawl_delay


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    pass


class ScrapingError(Exception):
    """Exception raised when scraping fails."""
    pass


class BaseScraper(ABC):
    """
    Abstract base class for all job scrapers.
    
    Provides common functionality:
    - Rate limiting using token bucket algorithm
    - Retry logic with exponential backoff (max 3 attempts)
    - Error logging and metrics tracking
    - Abstract methods for scraping and normalization
    
    Implements Requirements 1.8, 1.9, 14.3
    """
    
    def __init__(
        self,
        source_name: str,
        rate_limit: int,
        rate_limit_period: int = 60
    ):
        """
        Initialize the base scraper.
        
        Args:
            source_name: Name of the job source (e.g., "linkedin", "indeed")
            rate_limit: Maximum number of requests per period
            rate_limit_period: Time period in seconds (default: 60)
        """
        self.source_name = source_name
        self.rate_limit = rate_limit
        self.rate_limit_period = rate_limit_period
        self.max_retries = 3
        self.base_backoff_delay = 5  # seconds
        
        logger.info(
            f"Initialized {self.source_name} scraper with "
            f"rate limit: {rate_limit}/{rate_limit_period}s"
        )
    
    @abstractmethod
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape jobs from the source and return raw data.
        
        This method must be implemented by subclasses.
        
        Returns:
            List of raw job dictionaries from the source
            
        Raises:
            ScrapingError: If scraping fails
        """
        pass
    
    @abstractmethod
    def normalize_job(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert source-specific format to standard schema.
        
        This method must be implemented by subclasses.
        
        Args:
            raw_data: Raw job data from the source
            
        Returns:
            Normalized job dictionary conforming to Job model schema
        """
        pass
    
    async def check_rate_limit(self) -> bool:
        """
        Check if rate limit allows a new request using token bucket algorithm.
        
        Implements Requirement 1.9 and 14.3:
        - Uses Redis to track request counts per source
        - Token bucket algorithm for smooth rate limiting
        - Returns True if request is allowed, False otherwise
        
        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        redis = redis_client.get_cache_client()
        key = f"rate_limit:{self.source_name}"
        
        try:
            # Get current token count
            current_tokens = redis.get(key)
            
            if current_tokens is None:
                # First request - initialize bucket with full tokens
                redis.setex(
                    key,
                    self.rate_limit_period,
                    self.rate_limit - 1
                )
                logger.debug(
                    f"Rate limit initialized for {self.source_name}: "
                    f"{self.rate_limit - 1} tokens remaining"
                )
                return True
            
            current_tokens = int(current_tokens)
            
            if current_tokens > 0:
                # Tokens available - decrement and allow request
                redis.decr(key)
                logger.debug(
                    f"Rate limit check passed for {self.source_name}: "
                    f"{current_tokens - 1} tokens remaining"
                )
                return True
            else:
                # No tokens available - rate limit exceeded
                ttl = redis.ttl(key)
                logger.warning(
                    f"Rate limit exceeded for {self.source_name}. "
                    f"Retry after {ttl} seconds"
                )
                return False
                
        except Exception as e:
            logger.error(f"Rate limit check error for {self.source_name}: {e}")
            # On error, allow the request (fail open)
            return True
    
    async def wait_for_rate_limit(self) -> None:
        """
        Wait until rate limit allows a new request.
        
        Blocks until a token is available in the bucket.
        """
        redis = redis_client.get_cache_client()
        key = f"rate_limit:{self.source_name}"
        
        while not await self.check_rate_limit():
            # Get TTL and wait
            ttl = redis.ttl(key)
            wait_time = max(1, ttl)
            logger.info(
                f"Rate limit exceeded for {self.source_name}. "
                f"Waiting {wait_time} seconds..."
            )
            await asyncio.sleep(wait_time)
    
    async def scrape_with_retry(self) -> List[Dict[str, Any]]:
        """
        Scrape with retry logic and exponential backoff.
        
        Implements Requirements 1.8, 15.2:
        - Retries up to 3 times on failure
        - Exponential backoff: 5s, 10s, 20s
        - Logs all attempts and errors with source, error message, and retry count
        
        Returns:
            List of raw job dictionaries
            
        Raises:
            ScrapingError: If all retry attempts fail
        """
        from app.core.logging import log_error_with_context
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                logger.info(
                    f"Scraping attempt {attempt + 1}/{self.max_retries} "
                    f"for {self.source_name}"
                )
                
                # Check rate limit before scraping
                await self.wait_for_rate_limit()
                
                # Perform scraping
                jobs = await self.scrape()
                
                logger.info(
                    f"Successfully scraped {len(jobs)} jobs from {self.source_name} "
                    f"on attempt {attempt + 1}"
                )
                
                # Reset failure tracking on success
                from app.services.alerting import reset_scraping_failures
                await reset_scraping_failures(self.source_name)
                
                return jobs
                
            except Exception as e:
                last_error = e
                
                # Log scraping error with source, error message, and retry count (Requirement 15.2)
                log_error_with_context(
                    logger,
                    f"Scraping attempt {attempt + 1} failed for {self.source_name}",
                    error=e,
                    context={
                        'source': self.source_name,
                        'error_message': str(e),
                        'retry_count': attempt + 1,
                        'max_retries': self.max_retries
                    }
                )
                
                # Calculate backoff delay
                if attempt < self.max_retries - 1:
                    delay = self.base_backoff_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
        
        # All retries failed - track failures and potentially send alert
        from app.services.alerting import track_scraping_failures
        await track_scraping_failures(self.source_name, str(last_error))
        
        error_msg = (
            f"All {self.max_retries} scraping attempts failed for {self.source_name}. "
            f"Last error: {last_error}"
        )
        logger.error(error_msg)
        raise ScrapingError(error_msg)
    
    def log_metrics(
        self,
        jobs_found: int,
        jobs_created: int,
        jobs_updated: int,
        duration: float
    ) -> None:
        """
        Log scraping metrics for monitoring.
        
        Args:
            jobs_found: Number of jobs scraped from source
            jobs_created: Number of new jobs created in database
            jobs_updated: Number of existing jobs updated
            duration: Scraping duration in seconds
        """
        logger.info(
            f"Scraping metrics for {self.source_name}: "
            f"found={jobs_found}, created={jobs_created}, updated={jobs_updated}, "
            f"duration={duration:.2f}s"
        )


def normalize_job_type(raw_type: str) -> JobType:
    """
    Normalize job type string to standard enum.
    
    Implements Requirement 1.5:
    - Maps various job type formats to standard JobType enum
    - Handles common variations and abbreviations
    
    Args:
        raw_type: Raw job type string from source
        
    Returns:
        JobType enum value
        
    Example:
        >>> normalize_job_type("Full-Time")
        JobType.FULL_TIME
        >>> normalize_job_type("contract")
        JobType.CONTRACT
    """
    if not raw_type:
        return JobType.FULL_TIME  # Default
    
    raw_type_lower = raw_type.lower().strip()
    
    # Full-time variations
    if any(term in raw_type_lower for term in ["full", "fulltime", "full-time", "permanent"]):
        return JobType.FULL_TIME
    
    # Part-time variations
    if any(term in raw_type_lower for term in ["part", "parttime", "part-time"]):
        return JobType.PART_TIME
    
    # Contract variations
    if any(term in raw_type_lower for term in ["contract", "contractor", "temporary", "temp"]):
        return JobType.CONTRACT
    
    # Freelance variations
    if any(term in raw_type_lower for term in ["freelance", "freelancer", "gig"]):
        return JobType.FREELANCE
    
    # Internship variations
    if any(term in raw_type_lower for term in ["intern", "internship", "trainee"]):
        return JobType.INTERNSHIP
    
    # Fellowship variations
    if any(term in raw_type_lower for term in ["fellow", "fellowship"]):
        return JobType.FELLOWSHIP
    
    # Academic variations
    if any(term in raw_type_lower for term in ["academic", "faculty", "professor", "researcher"]):
        return JobType.ACADEMIC
    
    logger.warning(f"Unknown job type '{raw_type}', defaulting to FULL_TIME")
    return JobType.FULL_TIME


def normalize_experience_level(raw_level: str) -> ExperienceLevel:
    """
    Normalize experience level string to standard enum.
    
    Args:
        raw_level: Raw experience level string from source
        
    Returns:
        ExperienceLevel enum value
        
    Example:
        >>> normalize_experience_level("Senior")
        ExperienceLevel.SENIOR
        >>> normalize_experience_level("Entry Level")
        ExperienceLevel.ENTRY
    """
    if not raw_level:
        return ExperienceLevel.MID  # Default
    
    raw_level_lower = raw_level.lower().strip()
    
    # Entry level variations
    if any(term in raw_level_lower for term in ["entry", "junior", "jr", "graduate", "associate"]):
        return ExperienceLevel.ENTRY
    
    # Mid level variations
    if any(term in raw_level_lower for term in ["mid", "intermediate", "experienced"]):
        return ExperienceLevel.MID
    
    # Senior level variations
    if any(term in raw_level_lower for term in ["senior", "sr", "principal", "staff"]):
        return ExperienceLevel.SENIOR
    
    # Lead level variations
    if any(term in raw_level_lower for term in ["lead", "manager", "head", "director"]):
        return ExperienceLevel.LEAD
    
    # Executive level variations
    if any(term in raw_level_lower for term in ["executive", "vp", "vice president", "cto", "ceo", "cfo"]):
        return ExperienceLevel.EXECUTIVE
    
    logger.warning(f"Unknown experience level '{raw_level}', defaulting to MID")
    return ExperienceLevel.MID


def normalize_date_to_iso(raw_date: Any) -> str:
    """
    Normalize date to ISO format string.
    
    Implements Requirement 1.5:
    - Converts various date formats to ISO 8601
    - Handles datetime objects, timestamps, and date strings
    
    Args:
        raw_date: Raw date in various formats
        
    Returns:
        ISO format date string (YYYY-MM-DDTHH:MM:SS)
        
    Example:
        >>> normalize_date_to_iso(datetime(2024, 1, 15))
        '2024-01-15T00:00:00'
    """
    if isinstance(raw_date, datetime):
        return raw_date.isoformat()
    
    if isinstance(raw_date, str):
        # Try to parse common date formats
        try:
            # ISO format
            dt = datetime.fromisoformat(raw_date.replace('Z', '+00:00'))
            return dt.isoformat()
        except:
            pass
        
        try:
            # Common formats
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"]:
                try:
                    dt = datetime.strptime(raw_date, fmt)
                    return dt.isoformat()
                except:
                    continue
        except:
            pass
    
    # Default to current time if parsing fails
    logger.warning(f"Could not parse date '{raw_date}', using current time")
    return datetime.utcnow().isoformat()


def extract_salary_info(raw_salary: str) -> Dict[str, Optional[int]]:
    """
    Extract and normalize salary information from text.
    
    Implements Requirement 1.5:
    - Extracts min and max salary from various formats
    - Handles ranges, single values, and currency symbols
    - Normalizes to integer values
    
    Args:
        raw_salary: Raw salary string (e.g., "$100k-$150k", "100000-150000")
        
    Returns:
        Dictionary with 'salary_min' and 'salary_max' keys
        
    Example:
        >>> extract_salary_info("$100,000 - $150,000")
        {'salary_min': 100000, 'salary_max': 150000}
        >>> extract_salary_info("$120k")
        {'salary_min': 120000, 'salary_max': 120000}
    """
    import re
    
    if not raw_salary:
        return {'salary_min': None, 'salary_max': None}
    
    # Remove currency symbols and commas
    cleaned = re.sub(r'[$,£€]', '', raw_salary)
    
    # Find all numbers (including k/K for thousands)
    numbers = re.findall(r'(\d+(?:\.\d+)?)\s*([kK])?', cleaned)
    
    if not numbers:
        return {'salary_min': None, 'salary_max': None}
    
    # Convert to integers
    values = []
    for num, multiplier in numbers:
        value = float(num)
        if multiplier and multiplier.lower() == 'k':
            value *= 1000
        values.append(int(value))
    
    if len(values) == 1:
        # Single value - use as both min and max
        return {'salary_min': values[0], 'salary_max': values[0]}
    elif len(values) >= 2:
        # Range - use first two values
        return {'salary_min': min(values[0], values[1]), 'salary_max': max(values[0], values[1])}
    
    return {'salary_min': None, 'salary_max': None}


async def create_scraping_task(
    task_type: TaskType,
    source_platform: Optional[str] = None,
    target_url: Optional[str] = None,
    db_session = None
) -> Any:
    """
    Create a scraping task record in the database.
    
    Implements Requirement 1.7:
    - Creates task record with PENDING status
    - Logs task creation
    - Returns task object
    
    Args:
        task_type: Type of scraping task
        source_platform: Source platform name (for scheduled scrapes)
        target_url: Target URL (for URL imports)
        db_session: SQLAlchemy database session
        
    Returns:
        ScrapingTask object
    """
    from app.models.scraping_task import ScrapingTask
    
    task = ScrapingTask(
        task_type=task_type,
        source_platform=source_platform,
        target_url=target_url,
        status=TaskStatus.PENDING
    )
    
    if db_session:
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
    
    logger.info(
        f"Created scraping task: id={task.id}, type={task_type.value}, "
        f"platform={source_platform}, url={target_url}"
    )
    
    return task


async def update_scraping_task(
    task_id: str,
    updates: Dict[str, Any],
    db_session = None
) -> None:
    """
    Update scraping task status and metrics.
    
    Implements Requirements 1.7, 1.10, 15.2:
    - Updates task status (PENDING, RUNNING, COMPLETED, FAILED)
    - Logs jobs found, created, and updated counts
    - Records error messages and timestamps
    
    Args:
        task_id: Task UUID
        updates: Dictionary of fields to update
        db_session: SQLAlchemy database session
    """
    from app.models.scraping_task import ScrapingTask
    
    if not db_session:
        logger.error("Database session required for task update")
        return
    
    task = db_session.query(ScrapingTask).filter(ScrapingTask.id == task_id).first()
    
    if not task:
        logger.error(f"Scraping task {task_id} not found")
        return
    
    # Update fields
    for key, value in updates.items():
        if hasattr(task, key):
            setattr(task, key, value)
    
    db_session.commit()
    
    logger.info(
        f"Updated scraping task {task_id}: "
        f"status={task.status.value}, "
        f"jobs_found={task.jobs_found}, "
        f"jobs_created={task.jobs_created}, "
        f"jobs_updated={task.jobs_updated}"
    )


class LinkedInScraper(BaseScraper):
    """
    LinkedIn RSS feed scraper.
    
    Implements Requirements 1.1, 1.5:
    - Fetches jobs from LinkedIn RSS feeds using feedparser
    - Parses RSS feed items and extracts job data
    - Normalizes LinkedIn data to standard schema
    - Handles pagination if available
    """
    
    def __init__(self, rss_feed_url: str, rate_limit: int = 10):
        """
        Initialize LinkedIn RSS scraper.
        
        Args:
            rss_feed_url: LinkedIn RSS feed URL
            rate_limit: Maximum requests per minute (default: 10)
        """
        super().__init__(source_name="linkedin", rate_limit=rate_limit)
        self.rss_feed_url = rss_feed_url
        logger.info(f"Initialized LinkedIn RSS scraper for feed: {rss_feed_url}")
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape jobs from LinkedIn RSS feed.
        
        Implements Requirement 1.1:
        - Fetches jobs from LinkedIn RSS feeds
        - Parses RSS feed items
        - Extracts job data from feed entries
        
        Returns:
            List of raw job dictionaries from LinkedIn RSS
            
        Raises:
            ScrapingError: If fetching or parsing fails
        """
        try:
            logger.info(f"Fetching LinkedIn RSS feed: {self.rss_feed_url}")
            
            # Fetch RSS feed with timeout
            response = requests.get(self.rss_feed_url, timeout=30)
            response.raise_for_status()
            
            # Parse RSS feed
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                # Feed has parsing errors
                logger.warning(f"RSS feed parsing warning: {feed.bozo_exception}")
            
            jobs = []
            
            # Extract job data from feed entries
            for entry in feed.entries:
                try:
                    job_data = {
                        'title': entry.get('title', ''),
                        'company': entry.get('author', ''),
                        'link': entry.get('link', ''),
                        'description': entry.get('summary', ''),
                        'published': entry.get('published', ''),
                        'published_parsed': entry.get('published_parsed', None),
                        'location': self._extract_location(entry),
                        'job_type': self._extract_job_type(entry),
                        'experience_level': self._extract_experience_level(entry),
                    }
                    
                    jobs.append(job_data)
                    
                except Exception as e:
                    logger.error(f"Error parsing RSS entry: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(jobs)} jobs from LinkedIn RSS feed")
            return jobs
            
        except requests.RequestException as e:
            error_msg = f"Failed to fetch LinkedIn RSS feed: {e}"
            logger.error(error_msg)
            raise ScrapingError(error_msg)
        except Exception as e:
            error_msg = f"Failed to parse LinkedIn RSS feed: {e}"
            logger.error(error_msg)
            raise ScrapingError(error_msg)
    
    def _extract_location(self, entry: Dict[str, Any]) -> str:
        """
        Extract location from RSS entry.
        
        Args:
            entry: RSS feed entry
            
        Returns:
            Location string or 'Remote' as default
        """
        # Try to extract location from various fields
        location = entry.get('location', '')
        
        if not location:
            # Try to extract from summary/description
            summary = entry.get('summary', '')
            # Simple heuristic: look for common location patterns
            # This is a basic implementation - can be enhanced
            if 'Remote' in summary or 'remote' in summary:
                location = 'Remote'
            else:
                location = 'Not specified'
        
        return location
    
    def _extract_job_type(self, entry: Dict[str, Any]) -> str:
        """
        Extract job type from RSS entry.
        
        Args:
            entry: RSS feed entry
            
        Returns:
            Job type string
        """
        # Try to extract job type from tags or summary
        tags = entry.get('tags', [])
        for tag in tags:
            tag_term = tag.get('term', '').lower()
            if any(t in tag_term for t in ['full-time', 'part-time', 'contract', 'freelance', 'internship']):
                return tag.get('term', '')
        
        # Default to full-time
        return 'Full-Time'
    
    def _extract_experience_level(self, entry: Dict[str, Any]) -> str:
        """
        Extract experience level from RSS entry.
        
        Args:
            entry: RSS feed entry
            
        Returns:
            Experience level string
        """
        # Try to extract from title or summary
        title = entry.get('title', '').lower()
        summary = entry.get('summary', '').lower()
        
        combined = f"{title} {summary}"
        
        if any(term in combined for term in ['senior', 'sr', 'principal', 'staff']):
            return 'Senior'
        elif any(term in combined for term in ['junior', 'jr', 'entry', 'graduate']):
            return 'Entry Level'
        elif any(term in combined for term in ['lead', 'manager', 'director']):
            return 'Lead'
        
        return 'Mid Level'
    
    def normalize_job(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert LinkedIn RSS format to standard schema.
        
        Implements Requirement 1.5:
        - Maps LinkedIn RSS fields to standard schema
        - Extracts job title, company, location, description
        - Parses posted date from RSS pubDate
        - Sets source_platform to 'linkedin'
        
        Args:
            raw_data: Raw job data from LinkedIn RSS
            
        Returns:
            Normalized job dictionary conforming to Job model schema
        """
        from datetime import datetime, timedelta
        
        # Parse published date
        if raw_data.get('published_parsed'):
            import time
            posted_at = datetime(*raw_data['published_parsed'][:6])
        elif raw_data.get('published'):
            posted_at = normalize_date_to_iso(raw_data['published'])
            posted_at = datetime.fromisoformat(posted_at)
        else:
            posted_at = datetime.utcnow()
        
        # Calculate expiration date (30 days from posting)
        expires_at = posted_at + timedelta(days=30)
        
        # Normalize job type and experience level
        job_type = normalize_job_type(raw_data.get('job_type', 'Full-Time'))
        experience_level = normalize_experience_level(raw_data.get('experience_level', 'Mid Level'))
        
        # Extract salary info if present in description
        description = raw_data.get('description', '')
        salary_info = extract_salary_info(description)
        
        # Build normalized job dictionary
        normalized = {
            'title': raw_data.get('title', 'Untitled Position'),
            'company': raw_data.get('company', 'Unknown Company'),
            'location': raw_data.get('location', 'Not specified'),
            'remote': 'remote' in raw_data.get('location', '').lower(),
            'job_type': job_type,
            'experience_level': experience_level,
            'description': description[:5000] if description else 'No description available',
            'requirements': None,
            'responsibilities': None,
            'salary_min': salary_info.get('salary_min'),
            'salary_max': salary_info.get('salary_max'),
            'salary_currency': 'USD',
            'source_type': SourceType.AGGREGATED,
            'source_url': raw_data.get('link', ''),
            'source_platform': 'linkedin',
            'posted_at': posted_at,
            'expires_at': expires_at,
        }
        
        logger.debug(f"Normalized LinkedIn job: {normalized['title']} at {normalized['company']}")
        return normalized


class IndeedScraper(BaseScraper):
    """
    Indeed API scraper.
    
    Implements Requirements 1.2, 1.5:
    - Fetches jobs from Indeed Publisher API
    - Handles API authentication and pagination
    - Normalizes Indeed data to standard schema
    """
    
    def __init__(self, api_key: str, query: str = "", location: str = "", rate_limit: int = 20):
        """
        Initialize Indeed API scraper.
        
        Args:
            api_key: Indeed Publisher API key
            query: Job search query (keywords)
            location: Job location filter
            rate_limit: Maximum requests per minute (default: 20)
        """
        super().__init__(source_name="indeed", rate_limit=rate_limit)
        self.api_key = api_key
        self.query = query
        self.location = location
        self.base_url = "http://api.indeed.com/ads/apisearch"
        logger.info(f"Initialized Indeed API scraper with query='{query}', location='{location}'")
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape jobs from Indeed Publisher API.
        
        Implements Requirement 1.2:
        - Fetches jobs from Indeed API
        - Handles pagination to fetch all results
        - Extracts job data from API response
        
        Returns:
            List of raw job dictionaries from Indeed API
            
        Raises:
            ScrapingError: If fetching or parsing fails
        """
        try:
            all_jobs = []
            start = 0
            limit = 25  # Indeed API default page size
            
            while True:
                logger.info(f"Fetching Indeed jobs: start={start}, query='{self.query}', location='{self.location}'")
                
                # Build API request parameters
                params = {
                    'publisher': self.api_key,
                    'q': self.query,
                    'l': self.location,
                    'format': 'json',
                    'v': '2',
                    'start': start,
                    'limit': limit,
                }
                
                # Fetch from Indeed API with timeout
                response = requests.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                
                # Parse JSON response
                data = response.json()
                
                # Extract results
                results = data.get('results', [])
                
                if not results:
                    # No more results
                    break
                
                # Process each job result
                for result in results:
                    try:
                        job_data = {
                            'jobtitle': result.get('jobtitle', ''),
                            'company': result.get('company', ''),
                            'city': result.get('city', ''),
                            'state': result.get('state', ''),
                            'country': result.get('country', ''),
                            'formattedLocation': result.get('formattedLocation', ''),
                            'snippet': result.get('snippet', ''),
                            'url': result.get('url', ''),
                            'date': result.get('date', ''),
                            'jobkey': result.get('jobkey', ''),
                            'sponsored': result.get('sponsored', False),
                            'expired': result.get('expired', False),
                            'formattedLocationFull': result.get('formattedLocationFull', ''),
                            'formattedRelativeTime': result.get('formattedRelativeTime', ''),
                        }
                        
                        all_jobs.append(job_data)
                        
                    except Exception as e:
                        logger.error(f"Error parsing Indeed job result: {e}")
                        continue
                
                # Check if there are more results
                total_results = data.get('totalResults', 0)
                if start + limit >= total_results:
                    # Fetched all results
                    break
                
                # Move to next page
                start += limit
            
            logger.info(f"Successfully fetched {len(all_jobs)} jobs from Indeed API")
            return all_jobs
            
        except requests.RequestException as e:
            error_msg = f"Failed to fetch from Indeed API: {e}"
            logger.error(error_msg)
            raise ScrapingError(error_msg)
        except Exception as e:
            error_msg = f"Failed to parse Indeed API response: {e}"
            logger.error(error_msg)
            raise ScrapingError(error_msg)
    
    def normalize_job(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Indeed API format to standard schema.
        
        Implements Requirement 1.5:
        - Maps Indeed API fields to standard schema
        - Extracts job title, company, location, description
        - Parses job type and experience level from snippet
        - Sets source_platform to 'indeed'
        
        Args:
            raw_data: Raw job data from Indeed API
            
        Returns:
            Normalized job dictionary conforming to Job model schema
        """
        from datetime import datetime, timedelta
        
        # Build location string
        location = raw_data.get('formattedLocation') or raw_data.get('formattedLocationFull', '')
        if not location:
            city = raw_data.get('city', '')
            state = raw_data.get('state', '')
            country = raw_data.get('country', '')
            location = ', '.join(filter(None, [city, state, country]))
        
        if not location:
            location = 'Not specified'
        
        # Parse posted date from relative time or date field
        posted_at = self._parse_posted_date(raw_data.get('date', ''), raw_data.get('formattedRelativeTime', ''))
        
        # Calculate expiration date (30 days from posting)
        expires_at = posted_at + timedelta(days=30)
        
        # Extract job type and experience level from snippet
        snippet = raw_data.get('snippet', '')
        job_type = self._extract_job_type_from_snippet(snippet)
        experience_level = self._extract_experience_level_from_snippet(snippet)
        
        # Normalize job type and experience level
        job_type = normalize_job_type(job_type)
        experience_level = normalize_experience_level(experience_level)
        
        # Extract salary info from snippet
        salary_info = extract_salary_info(snippet)
        
        # Build normalized job dictionary
        normalized = {
            'title': raw_data.get('jobtitle', 'Untitled Position'),
            'company': raw_data.get('company', 'Unknown Company'),
            'location': location,
            'remote': 'remote' in location.lower() or 'remote' in snippet.lower(),
            'job_type': job_type,
            'experience_level': experience_level,
            'description': snippet[:5000] if snippet else 'No description available',
            'requirements': None,
            'responsibilities': None,
            'salary_min': salary_info.get('salary_min'),
            'salary_max': salary_info.get('salary_max'),
            'salary_currency': 'USD',
            'source_type': SourceType.AGGREGATED,
            'source_url': raw_data.get('url', ''),
            'source_platform': 'indeed',
            'posted_at': posted_at,
            'expires_at': expires_at,
        }
        
        logger.debug(f"Normalized Indeed job: {normalized['title']} at {normalized['company']}")
        return normalized
    
    def _parse_posted_date(self, date_str: str, relative_time_str: str) -> datetime:
        """
        Parse posted date from Indeed API date or relative time string.
        
        Args:
            date_str: Date string from API (e.g., "Mon, 15 Jan 2024 10:00:00 GMT")
            relative_time_str: Relative time string (e.g., "2 days ago", "Just posted")
            
        Returns:
            datetime object representing posted date
        """
        # Try parsing date_str first
        if date_str:
            try:
                # Try RFC 2822 format
                from email.utils import parsedate_to_datetime
                return parsedate_to_datetime(date_str)
            except:
                pass
            
            try:
                # Try ISO format
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                pass
        
        # Try parsing relative time
        if relative_time_str:
            try:
                relative_lower = relative_time_str.lower()
                
                if 'just posted' in relative_lower or 'today' in relative_lower:
                    return datetime.utcnow()
                
                # Extract number of days/hours
                import re
                match = re.search(r'(\d+)\s*(day|hour|minute)', relative_lower)
                if match:
                    value = int(match.group(1))
                    unit = match.group(2)
                    
                    if 'day' in unit:
                        return datetime.utcnow() - timedelta(days=value)
                    elif 'hour' in unit:
                        return datetime.utcnow() - timedelta(hours=value)
                    elif 'minute' in unit:
                        return datetime.utcnow() - timedelta(minutes=value)
            except:
                pass
        
        # Default to current time if parsing fails
        logger.warning(f"Could not parse Indeed date '{date_str}' or '{relative_time_str}', using current time")
        return datetime.utcnow()
    
    def _extract_job_type_from_snippet(self, snippet: str) -> str:
        """
        Extract job type from Indeed snippet text.
        
        Args:
            snippet: Job description snippet
            
        Returns:
            Job type string
        """
        if not snippet:
            return 'Full-Time'
        
        snippet_lower = snippet.lower()
        
        # Check for job type keywords
        if any(term in snippet_lower for term in ['part-time', 'part time', 'parttime']):
            return 'Part-Time'
        elif any(term in snippet_lower for term in ['contract', 'contractor', 'temporary']):
            return 'Contract'
        elif any(term in snippet_lower for term in ['freelance', 'freelancer']):
            return 'Freelance'
        elif any(term in snippet_lower for term in ['intern', 'internship']):
            return 'Internship'
        elif any(term in snippet_lower for term in ['full-time', 'full time', 'fulltime', 'permanent']):
            return 'Full-Time'
        
        # Default to full-time
        return 'Full-Time'
    
    def _extract_experience_level_from_snippet(self, snippet: str) -> str:
        """
        Extract experience level from Indeed snippet text.
        
        Args:
            snippet: Job description snippet
            
        Returns:
            Experience level string
        """
        if not snippet:
            return 'Mid Level'
        
        snippet_lower = snippet.lower()
        
        # Check for experience level keywords
        if any(term in snippet_lower for term in ['senior', 'sr.', 'principal', 'staff']):
            return 'Senior'
        elif any(term in snippet_lower for term in ['junior', 'jr.', 'entry', 'entry-level', 'graduate']):
            return 'Entry Level'
        elif any(term in snippet_lower for term in ['lead', 'manager', 'director']):
            return 'Lead'
        elif any(term in snippet_lower for term in ['executive', 'vp', 'vice president', 'cto', 'ceo']):
            return 'Executive'
        
        # Default to mid level
        return 'Mid Level'


class NaukriScraper(BaseScraper):
    """
    Naukri web scraper using BeautifulSoup4.
    
    Implements Requirements 1.3, 1.5:
    - Fetches jobs from Naukri.com via web scraping
    - Parses HTML using BeautifulSoup4
    - Extracts job URLs from search results
    - Fetches individual job pages and parses details
    - Normalizes Naukri data to standard schema
    """
    
    def __init__(self, search_url: str, rate_limit: int = 5):
        """
        Initialize Naukri web scraper.
        
        Args:
            search_url: Naukri search results URL
            rate_limit: Maximum requests per minute (default: 5)
        """
        super().__init__(source_name="naukri", rate_limit=rate_limit)
        self.search_url = search_url
        self.base_url = "https://www.naukri.com"
        logger.info(f"Initialized Naukri scraper for URL: {search_url}")
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape jobs from Naukri search results.
        
        Implements Requirement 1.3:
        - Fetches Naukri search results page
        - Extracts job URLs from search results
        - Fetches individual job pages
        - Parses job details from HTML
        
        Returns:
            List of raw job dictionaries from Naukri
            
        Raises:
            ScrapingError: If fetching or parsing fails
        """
        from bs4 import BeautifulSoup
        
        try:
            logger.info(f"Fetching Naukri search results: {self.search_url}")
            
            # Fetch search results page with timeout
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(self.search_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse search results HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract job URLs from search results
            job_urls = self._extract_job_urls(soup)
            
            if not job_urls:
                logger.warning("No job URLs found in Naukri search results")
                return []
            
            logger.info(f"Found {len(job_urls)} job URLs in Naukri search results")
            
            # Fetch and parse individual job pages
            jobs = []
            for job_url in job_urls[:20]:  # Limit to 20 jobs per scrape to respect rate limits
                try:
                    # Wait for rate limit before fetching job page
                    await self.wait_for_rate_limit()
                    
                    logger.debug(f"Fetching Naukri job page: {job_url}")
                    job_response = requests.get(job_url, headers=headers, timeout=30)
                    job_response.raise_for_status()
                    
                    # Parse job page HTML
                    job_soup = BeautifulSoup(job_response.content, 'html.parser')
                    
                    # Extract job details
                    job_data = self._parse_job_page(job_soup, job_url)
                    
                    if job_data:
                        jobs.append(job_data)
                    
                except Exception as e:
                    logger.error(f"Error fetching Naukri job page {job_url}: {e}")
                    continue
            
            logger.info(f"Successfully scraped {len(jobs)} jobs from Naukri")
            return jobs
            
        except requests.RequestException as e:
            error_msg = f"Failed to fetch Naukri search results: {e}"
            logger.error(error_msg)
            raise ScrapingError(error_msg)
        except Exception as e:
            error_msg = f"Failed to parse Naukri search results: {e}"
            logger.error(error_msg)
            raise ScrapingError(error_msg)
    
    def _extract_job_urls(self, soup) -> List[str]:
        """
        Extract job URLs from Naukri search results page.
        
        Args:
            soup: BeautifulSoup object of search results page
            
        Returns:
            List of job URLs
        """
        job_urls = []
        
        # Naukri uses article tags with class 'jobTuple' for job listings
        job_cards = soup.find_all('article', class_='jobTuple')
        
        for card in job_cards:
            try:
                # Find the job title link
                title_link = card.find('a', class_='title')
                if title_link and title_link.get('href'):
                    job_url = title_link['href']
                    
                    # Make absolute URL if relative
                    if not job_url.startswith('http'):
                        job_url = self.base_url + job_url
                    
                    job_urls.append(job_url)
            except Exception as e:
                logger.error(f"Error extracting job URL from card: {e}")
                continue
        
        return job_urls
    
    def _parse_job_page(self, soup, job_url: str) -> Optional[Dict[str, Any]]:
        """
        Parse job details from Naukri job page.
        
        Args:
            soup: BeautifulSoup object of job page
            job_url: URL of the job page
            
        Returns:
            Dictionary with job data or None if parsing fails
        """
        try:
            # Extract job title
            title_elem = soup.find('h1', class_='jd-header-title') or soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else 'Untitled Position'
            
            # Extract company name
            company_elem = soup.find('a', class_='comp-name') or soup.find('div', class_='comp-name')
            company = company_elem.get_text(strip=True) if company_elem else 'Unknown Company'
            
            # Extract location
            location_elem = soup.find('span', class_='loc') or soup.find('a', class_='loc')
            location = location_elem.get_text(strip=True) if location_elem else 'Not specified'
            
            # Extract experience
            experience_elem = soup.find('span', class_='exp')
            experience = experience_elem.get_text(strip=True) if experience_elem else ''
            
            # Extract salary
            salary_elem = soup.find('span', class_='sal') or soup.find('div', class_='salary')
            salary = salary_elem.get_text(strip=True) if salary_elem else ''
            
            # Extract job description
            desc_elem = soup.find('div', class_='jd-desc') or soup.find('div', class_='job-desc')
            description = desc_elem.get_text(strip=True) if desc_elem else ''
            
            # Extract key skills
            skills_section = soup.find('div', class_='key-skill')
            skills = []
            if skills_section:
                skill_tags = skills_section.find_all('a')
                skills = [tag.get_text(strip=True) for tag in skill_tags]
            
            # Extract job type (if available)
            job_type_elem = soup.find('span', class_='job-type')
            job_type = job_type_elem.get_text(strip=True) if job_type_elem else 'Full-Time'
            
            # Extract posted date
            posted_elem = soup.find('span', class_='posted') or soup.find('div', class_='posted')
            posted = posted_elem.get_text(strip=True) if posted_elem else ''
            
            job_data = {
                'title': title,
                'company': company,
                'location': location,
                'experience': experience,
                'salary': salary,
                'description': description,
                'skills': skills,
                'job_type': job_type,
                'posted': posted,
                'url': job_url,
            }
            
            logger.debug(f"Parsed Naukri job: {title} at {company}")
            return job_data
            
        except Exception as e:
            logger.error(f"Error parsing Naukri job page: {e}")
            return None
    
    def normalize_job(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Naukri format to standard schema.
        
        Implements Requirement 1.5:
        - Maps Naukri HTML fields to standard schema
        - Extracts job title, company, location, description
        - Parses salary information
        - Extracts experience level from experience field
        - Sets source_platform to 'naukri'
        
        Args:
            raw_data: Raw job data from Naukri
            
        Returns:
            Normalized job dictionary conforming to Job model schema
        """
        from datetime import datetime, timedelta
        
        # Parse experience level from experience field
        experience = raw_data.get('experience', '')
        experience_level = self._extract_experience_level_from_text(experience)
        
        # Normalize experience level
        experience_level = normalize_experience_level(experience_level)
        
        # Parse job type
        job_type = normalize_job_type(raw_data.get('job_type', 'Full-Time'))
        
        # Extract salary info
        salary_info = extract_salary_info(raw_data.get('salary', ''))
        
        # Parse posted date from posted text
        posted_at = self._parse_posted_date(raw_data.get('posted', ''))
        
        # Calculate expiration date (30 days from posting)
        expires_at = posted_at + timedelta(days=30)
        
        # Check if remote
        location = raw_data.get('location', 'Not specified')
        description = raw_data.get('description', '')
        remote = 'remote' in location.lower() or 'remote' in description.lower()
        
        # Build normalized job dictionary
        normalized = {
            'title': raw_data.get('title', 'Untitled Position'),
            'company': raw_data.get('company', 'Unknown Company'),
            'location': location,
            'remote': remote,
            'job_type': job_type,
            'experience_level': experience_level,
            'description': description[:5000] if description else 'No description available',
            'requirements': ', '.join(raw_data.get('skills', [])) if raw_data.get('skills') else None,
            'responsibilities': None,
            'salary_min': salary_info.get('salary_min'),
            'salary_max': salary_info.get('salary_max'),
            'salary_currency': 'INR',  # Naukri is primarily Indian job site
            'source_type': SourceType.AGGREGATED,
            'source_url': raw_data.get('url', ''),
            'source_platform': 'naukri',
            'posted_at': posted_at,
            'expires_at': expires_at,
        }
        
        logger.debug(f"Normalized Naukri job: {normalized['title']} at {normalized['company']}")
        return normalized
    
    def _extract_experience_level_from_text(self, experience_text: str) -> str:
        """
        Extract experience level from Naukri experience text.
        
        Args:
            experience_text: Experience text (e.g., "2-5 years", "0-2 years")
            
        Returns:
            Experience level string
        """
        if not experience_text:
            return 'Mid Level'
        
        experience_lower = experience_text.lower()
        
        # Extract years from text
        import re
        years_match = re.search(r'(\d+)', experience_lower)
        
        if years_match:
            min_years = int(years_match.group(1))
            
            if min_years == 0 or 'fresher' in experience_lower:
                return 'Entry Level'
            elif min_years <= 2:
                return 'Entry Level'
            elif min_years <= 4:
                return 'Mid Level'
            elif min_years <= 7:
                return 'Senior'
            else:
                return 'Lead'
        
        # Check for keywords
        if any(term in experience_lower for term in ['fresher', 'entry', 'junior']):
            return 'Entry Level'
        elif any(term in experience_lower for term in ['senior', 'sr']):
            return 'Senior'
        elif any(term in experience_lower for term in ['lead', 'manager', 'director']):
            return 'Lead'
        
        return 'Mid Level'
    
    def _parse_posted_date(self, posted_text: str) -> datetime:
        """
        Parse posted date from Naukri posted text.
        
        Args:
            posted_text: Posted text (e.g., "Posted 2 days ago", "Just now")
            
        Returns:
            datetime object representing posted date
        """
        if not posted_text:
            return datetime.utcnow()
        
        posted_lower = posted_text.lower()
        
        # Check for "just now" or "today"
        if 'just' in posted_lower or 'today' in posted_lower:
            return datetime.utcnow()
        
        # Extract number of days/hours
        import re
        
        # Try to match "X days ago"
        days_match = re.search(r'(\d+)\s*day', posted_lower)
        if days_match:
            days = int(days_match.group(1))
            return datetime.utcnow() - timedelta(days=days)
        
        # Try to match "X hours ago"
        hours_match = re.search(r'(\d+)\s*hour', posted_lower)
        if hours_match:
            hours = int(hours_match.group(1))
            return datetime.utcnow() - timedelta(hours=hours)
        
        # Try to match "X weeks ago"
        weeks_match = re.search(r'(\d+)\s*week', posted_lower)
        if weeks_match:
            weeks = int(weeks_match.group(1))
            return datetime.utcnow() - timedelta(weeks=weeks)
        
        # Default to current time if parsing fails
        logger.warning(f"Could not parse Naukri posted date '{posted_text}', using current time")
        return datetime.utcnow()


class MonsterScraper(BaseScraper):
    """
    Monster web scraper using BeautifulSoup4.
    
    Implements Requirements 1.4, 1.5:
    - Fetches jobs from Monster.com via web scraping
    - Parses HTML using BeautifulSoup4
    - Extracts job URLs from search results
    - Fetches individual job pages and parses details
    - Normalizes Monster data to standard schema
    """
    
    def __init__(self, search_url: str, rate_limit: int = 5):
        """
        Initialize Monster web scraper.
        
        Args:
            search_url: Monster search results URL
            rate_limit: Maximum requests per minute (default: 5)
        """
        super().__init__(source_name="monster", rate_limit=rate_limit)
        self.search_url = search_url
        self.base_url = "https://www.monster.com"
        logger.info(f"Initialized Monster scraper for URL: {search_url}")
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape jobs from Monster search results.
        
        Implements Requirement 1.4:
        - Fetches Monster search results page
        - Extracts job URLs from search results
        - Fetches individual job pages
        - Parses job details from HTML
        
        Returns:
            List of raw job dictionaries from Monster
            
        Raises:
            ScrapingError: If fetching or parsing fails
        """
        from bs4 import BeautifulSoup
        
        try:
            logger.info(f"Fetching Monster search results: {self.search_url}")
            
            # Fetch search results page with timeout
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(self.search_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse search results HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract job URLs from search results
            job_urls = self._extract_job_urls(soup)
            
            if not job_urls:
                logger.warning("No job URLs found in Monster search results")
                return []
            
            logger.info(f"Found {len(job_urls)} job URLs in Monster search results")
            
            # Fetch and parse individual job pages
            jobs = []
            for job_url in job_urls[:20]:  # Limit to 20 jobs per scrape to respect rate limits
                try:
                    # Wait for rate limit before fetching job page
                    await self.wait_for_rate_limit()
                    
                    logger.debug(f"Fetching Monster job page: {job_url}")
                    job_response = requests.get(job_url, headers=headers, timeout=30)
                    job_response.raise_for_status()
                    
                    # Parse job page HTML
                    job_soup = BeautifulSoup(job_response.content, 'html.parser')
                    
                    # Extract job details
                    job_data = self._parse_job_page(job_soup, job_url)
                    
                    if job_data:
                        jobs.append(job_data)
                    
                except Exception as e:
                    logger.error(f"Error fetching Monster job page {job_url}: {e}")
                    continue
            
            logger.info(f"Successfully scraped {len(jobs)} jobs from Monster")
            return jobs
            
        except requests.RequestException as e:
            error_msg = f"Failed to fetch Monster search results: {e}"
            logger.error(error_msg)
            raise ScrapingError(error_msg)
        except Exception as e:
            error_msg = f"Failed to parse Monster search results: {e}"
            logger.error(error_msg)
            raise ScrapingError(error_msg)
    
    def _extract_job_urls(self, soup) -> List[str]:
        """
        Extract job URLs from Monster search results page.
        
        Args:
            soup: BeautifulSoup object of search results page
            
        Returns:
            List of job URLs
        """
        job_urls = []
        
        # Monster uses various selectors for job listings
        # Try multiple selectors to handle different page layouts
        job_cards = (
            soup.find_all('div', class_='job-card') or
            soup.find_all('section', class_='card-content') or
            soup.find_all('div', class_='job-cardstyle__JobCardComponent')
        )
        
        for card in job_cards:
            try:
                # Find the job title link
                title_link = (
                    card.find('a', class_='job-title') or
                    card.find('a', class_='title') or
                    card.find('h2', class_='title').find('a') if card.find('h2', class_='title') else None
                )
                
                if title_link and title_link.get('href'):
                    job_url = title_link['href']
                    
                    # Make absolute URL if relative
                    if not job_url.startswith('http'):
                        job_url = self.base_url + job_url
                    
                    job_urls.append(job_url)
            except Exception as e:
                logger.error(f"Error extracting job URL from card: {e}")
                continue
        
        return job_urls
    
    def _parse_job_page(self, soup, job_url: str) -> Optional[Dict[str, Any]]:
        """
        Parse job details from Monster job page.
        
        Args:
            soup: BeautifulSoup object of job page
            job_url: URL of the job page
            
        Returns:
            Dictionary with job data or None if parsing fails
        """
        try:
            # Extract job title
            title_elem = (
                soup.find('h1', class_='job-title') or
                soup.find('h1', class_='title') or
                soup.find('h1')
            )
            title = title_elem.get_text(strip=True) if title_elem else 'Untitled Position'
            
            # Extract company name
            company_elem = (
                soup.find('span', class_='company') or
                soup.find('div', class_='company') or
                soup.find('a', class_='company-name')
            )
            company = company_elem.get_text(strip=True) if company_elem else 'Unknown Company'
            
            # Extract location
            location_elem = (
                soup.find('span', class_='location') or
                soup.find('div', class_='location') or
                soup.find('span', {'itemprop': 'jobLocation'})
            )
            location = location_elem.get_text(strip=True) if location_elem else 'Not specified'
            
            # Extract job type
            job_type_elem = (
                soup.find('span', class_='job-type') or
                soup.find('div', class_='employment-type')
            )
            job_type = job_type_elem.get_text(strip=True) if job_type_elem else 'Full-Time'
            
            # Extract salary
            salary_elem = (
                soup.find('span', class_='salary') or
                soup.find('div', class_='salary-range') or
                soup.find('span', {'itemprop': 'baseSalary'})
            )
            salary = salary_elem.get_text(strip=True) if salary_elem else ''
            
            # Extract job description
            desc_elem = (
                soup.find('div', class_='job-description') or
                soup.find('div', {'id': 'JobDescription'}) or
                soup.find('div', class_='description')
            )
            description = desc_elem.get_text(strip=True) if desc_elem else ''
            
            # Extract requirements (if available)
            requirements_elem = (
                soup.find('div', class_='requirements') or
                soup.find('div', class_='qualifications')
            )
            requirements = requirements_elem.get_text(strip=True) if requirements_elem else ''
            
            # Extract posted date
            posted_elem = (
                soup.find('span', class_='posted-date') or
                soup.find('time', class_='posted') or
                soup.find('span', class_='date')
            )
            posted = posted_elem.get_text(strip=True) if posted_elem else ''
            
            job_data = {
                'title': title,
                'company': company,
                'location': location,
                'job_type': job_type,
                'salary': salary,
                'description': description,
                'requirements': requirements,
                'posted': posted,
                'url': job_url,
            }
            
            logger.debug(f"Parsed Monster job: {title} at {company}")
            return job_data
            
        except Exception as e:
            logger.error(f"Error parsing Monster job page: {e}")
            return None
    
    def normalize_job(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Monster format to standard schema.
        
        Implements Requirement 1.5:
        - Maps Monster HTML fields to standard schema
        - Extracts job title, company, location, description
        - Parses salary information
        - Extracts job type information
        - Sets source_platform to 'monster'
        
        Args:
            raw_data: Raw job data from Monster
            
        Returns:
            Normalized job dictionary conforming to Job model schema
        """
        from datetime import datetime, timedelta
        
        # Parse job type
        job_type = normalize_job_type(raw_data.get('job_type', 'Full-Time'))
        
        # Extract experience level from description and requirements
        description = raw_data.get('description', '')
        requirements = raw_data.get('requirements', '')
        combined_text = f"{description} {requirements}"
        experience_level = self._extract_experience_level_from_text(combined_text)
        experience_level = normalize_experience_level(experience_level)
        
        # Extract salary info
        salary_info = extract_salary_info(raw_data.get('salary', ''))
        
        # Parse posted date from posted text
        posted_at = self._parse_posted_date(raw_data.get('posted', ''))
        
        # Calculate expiration date (30 days from posting)
        expires_at = posted_at + timedelta(days=30)
        
        # Check if remote
        location = raw_data.get('location', 'Not specified')
        remote = 'remote' in location.lower() or 'remote' in description.lower()
        
        # Build normalized job dictionary
        normalized = {
            'title': raw_data.get('title', 'Untitled Position'),
            'company': raw_data.get('company', 'Unknown Company'),
            'location': location,
            'remote': remote,
            'job_type': job_type,
            'experience_level': experience_level,
            'description': description[:5000] if description else 'No description available',
            'requirements': requirements[:2000] if requirements else None,
            'responsibilities': None,
            'salary_min': salary_info.get('salary_min'),
            'salary_max': salary_info.get('salary_max'),
            'salary_currency': 'USD',
            'source_type': SourceType.AGGREGATED,
            'source_url': raw_data.get('url', ''),
            'source_platform': 'monster',
            'posted_at': posted_at,
            'expires_at': expires_at,
        }
        
        logger.debug(f"Normalized Monster job: {normalized['title']} at {normalized['company']}")
        return normalized
    
    def _extract_experience_level_from_text(self, text: str) -> str:
        """
        Extract experience level from Monster job text.
        
        Args:
            text: Job description or requirements text
            
        Returns:
            Experience level string
        """
        if not text:
            return 'Mid Level'
        
        text_lower = text.lower()
        
        # Check for experience level keywords
        if any(term in text_lower for term in ['senior', 'sr.', 'sr ', 'principal', 'staff']):
            return 'Senior'
        elif any(term in text_lower for term in ['junior', 'jr.', 'jr ', 'entry', 'entry-level', 'entry level', 'graduate']):
            return 'Entry Level'
        elif any(term in text_lower for term in ['lead', 'manager', 'director', 'head of']):
            return 'Lead'
        elif any(term in text_lower for term in ['executive', 'vp', 'vice president', 'cto', 'ceo', 'cfo']):
            return 'Executive'
        
        # Check for years of experience
        import re
        years_match = re.search(r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)', text_lower)
        
        if years_match:
            years = int(years_match.group(1))
            
            if years == 0 or years <= 2:
                return 'Entry Level'
            elif years <= 4:
                return 'Mid Level'
            elif years <= 7:
                return 'Senior'
            else:
                return 'Lead'
        
        return 'Mid Level'
    
    def _parse_posted_date(self, posted_text: str) -> datetime:
        """
        Parse posted date from Monster posted text.
        
        Args:
            posted_text: Posted text (e.g., "Posted 2 days ago", "Just posted")
            
        Returns:
            datetime object representing posted date
        """
        if not posted_text:
            return datetime.utcnow()
        
        posted_lower = posted_text.lower()
        
        # Check for "just posted" or "today"
        if 'just' in posted_lower or 'today' in posted_lower:
            return datetime.utcnow()
        
        # Extract number of days/hours
        import re
        
        # Try to match "X days ago"
        days_match = re.search(r'(\d+)\s*day', posted_lower)
        if days_match:
            days = int(days_match.group(1))
            return datetime.utcnow() - timedelta(days=days)
        
        # Try to match "X hours ago"
        hours_match = re.search(r'(\d+)\s*hour', posted_lower)
        if hours_match:
            hours = int(hours_match.group(1))
            return datetime.utcnow() - timedelta(hours=hours)
        
        # Try to match "X weeks ago"
        weeks_match = re.search(r'(\d+)\s*week', posted_lower)
        if weeks_match:
            weeks = int(weeks_match.group(1))
            return datetime.utcnow() - timedelta(weeks=weeks)
        
        # Default to current time if parsing fails
        logger.warning(f"Could not parse Monster posted date '{posted_text}', using current time")
        return datetime.utcnow()


class RateLimiter:
    """
    Redis-based rate limiter for external sources.
    
    Implements Requirements 1.9, 14.3:
    - Token bucket algorithm using Redis
    - Configurable limits per source
    - Blocks requests when limit exceeded
    """
    
    # Default rate limits per source (requests per minute)
    DEFAULT_LIMITS = {
        'linkedin': 10,
        'indeed': 20,
        'naukri': 5,
        'monster': 5,
    }
    
    def __init__(self, source: str, limit: Optional[int] = None):
        """
        Initialize rate limiter for a source.
        
        Args:
            source: Source name (linkedin, indeed, naukri, monster)
            limit: Custom rate limit (requests per minute), uses default if None
        """
        self.source = source.lower()
        self.limit = limit or self.DEFAULT_LIMITS.get(self.source, 10)
        self.period = 60  # seconds
        
        logger.info(
            f"Initialized rate limiter for {self.source}: "
            f"{self.limit} requests per {self.period}s"
        )
    
    async def acquire(self) -> bool:
        """
        Acquire a token from the rate limiter.
        
        Returns:
            True if token acquired, False if rate limit exceeded
        """
        redis = redis_client.get_cache_client()
        key = f"rate_limit:{self.source}"
        
        try:
            # Get current count
            current = redis.get(key)
            
            if current is None:
                # Initialize counter
                redis.setex(key, self.period, 1)
                return True
            
            current = int(current)
            
            if current < self.limit:
                # Increment counter
                redis.incr(key)
                return True
            else:
                # Rate limit exceeded
                return False
                
        except Exception as e:
            logger.error(f"Rate limiter error for {self.source}: {e}")
            # Fail open on error
            return True
    
    async def wait_and_acquire(self) -> None:
        """
        Wait until a token is available and acquire it.
        
        Blocks until rate limit allows a request.
        """
        redis = redis_client.get_cache_client()
        key = f"rate_limit:{self.source}"
        
        while not await self.acquire():
            ttl = redis.ttl(key)
            wait_time = max(1, ttl)
            logger.info(
                f"Rate limit exceeded for {self.source}. "
                f"Waiting {wait_time} seconds..."
            )
            await asyncio.sleep(wait_time)
    
    def get_remaining(self) -> int:
        """
        Get remaining requests in current period.
        
        Returns:
            Number of remaining requests
        """
        redis = redis_client.get_cache_client()
        key = f"rate_limit:{self.source}"
        
        try:
            current = redis.get(key)
            if current is None:
                return self.limit
            return max(0, self.limit - int(current))
        except Exception as e:
            logger.error(f"Error getting remaining requests for {self.source}: {e}")
            return self.limit


# Scraper registry for source platform mapping
SCRAPER_REGISTRY: Dict[str, type] = {
    'linkedin': LinkedInScraper,
    'indeed': IndeedScraper,
    'naukri': NaukriScraper,
    'monster': MonsterScraper,
}


async def scrape_and_process_jobs(
    source_platform: str,
    db_session,
    scraper_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Main orchestration function for scraping and processing jobs.
    
    Implements Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.10:
    - Fetches raw jobs from scraper
    - Normalizes each job
    - Checks for duplicates using deduplication service
    - Creates new jobs or updates existing ones
    - Tracks metrics (jobs found, created, updated)
    
    Args:
        source_platform: Platform to scrape (linkedin, indeed, naukri, monster)
        db_session: SQLAlchemy database session
        scraper_config: Optional configuration for scraper initialization
        
    Returns:
        Dictionary with scraping results:
        - success: bool
        - source_platform: str
        - jobs_found: int
        - jobs_created: int
        - jobs_updated: int
        - duration: float (seconds)
        - error: Optional[str]
    """
    from app.models.job import Job
    from app.models.job_source import JobSource
    from app.services.deduplication import process_job_with_deduplication
    from app.services.quality_scoring import calculate_quality_score
    from app.core.config import settings
    
    start_time = time.time()
    
    # Validate source platform
    if source_platform.lower() not in SCRAPER_REGISTRY:
        error_msg = f"Unknown source platform: {source_platform}"
        logger.error(error_msg)
        return {
            'success': False,
            'source_platform': source_platform,
            'jobs_found': 0,
            'jobs_created': 0,
            'jobs_updated': 0,
            'duration': 0.0,
            'error': error_msg
        }
    
    # Create scraping task record
    task = await create_scraping_task(
        task_type=TaskType.SCHEDULED_SCRAPE,
        source_platform=source_platform,
        db_session=db_session
    )
    
    # Update task status to RUNNING
    await update_scraping_task(
        task.id,
        {
            'status': TaskStatus.RUNNING,
            'started_at': datetime.utcnow()
        },
        db_session
    )
    
    jobs_found = 0
    jobs_created = 0
    jobs_updated = 0
    
    try:
        # Initialize scraper with configuration
        scraper_class = SCRAPER_REGISTRY[source_platform.lower()]
        
        if scraper_config is None:
            scraper_config = {}
        
        # Get scraper-specific configuration from settings
        if source_platform.lower() == 'linkedin':
            rss_url = scraper_config.get('rss_url', getattr(settings, 'LINKEDIN_RSS_URL', 'https://www.linkedin.com/jobs/search/?f_TPR=r86400&format=rss'))
            scraper = scraper_class(rss_feed_url=rss_url)
        elif source_platform.lower() == 'indeed':
            api_key = scraper_config.get('api_key', getattr(settings, 'INDEED_API_KEY', ''))
            query = scraper_config.get('query', 'software engineer')
            location = scraper_config.get('location', '')
            scraper = scraper_class(api_key=api_key, query=query, location=location)
        elif source_platform.lower() == 'naukri':
            search_url = scraper_config.get('search_url', getattr(settings, 'NAUKRI_SEARCH_URL', 'https://www.naukri.com/software-engineer-jobs'))
            scraper = scraper_class(search_url=search_url)
        elif source_platform.lower() == 'monster':
            search_url = scraper_config.get('search_url', getattr(settings, 'MONSTER_SEARCH_URL', 'https://www.monster.com/jobs/search/?q=software-engineer'))
            scraper = scraper_class(search_url=search_url)
        else:
            raise ValueError(f"Unsupported source platform: {source_platform}")
        
        logger.info(f"Starting scraping for {source_platform}")
        
        # Fetch raw jobs from source with retry logic
        raw_jobs = await scraper.scrape_with_retry()
        jobs_found = len(raw_jobs)
        
        logger.info(f"Found {jobs_found} jobs from {source_platform}")
        
        # Process each job
        for raw_job in raw_jobs:
            try:
                # Normalize job data to standard schema
                normalized_job = scraper.normalize_job(raw_job)
                
                # Calculate quality score
                quality_score = calculate_quality_score(
                    source_type=SourceType.AGGREGATED,
                    job_data=normalized_job,
                    posted_at=normalized_job.get('posted_at')
                )
                normalized_job['quality_score'] = quality_score
                
                # Prepare source information
                source_info = {
                    'platform': source_platform,
                    'url': normalized_job.get('source_url', ''),
                    'job_id': raw_job.get('jobkey') or raw_job.get('id')
                }
                
                # Check for duplicates and process
                is_duplicate, result = process_job_with_deduplication(
                    job_data=normalized_job,
                    source_info=source_info,
                    db_session=db_session
                )
                
                if is_duplicate:
                    # Job was merged with existing record
                    jobs_updated += 1
                    logger.debug(
                        f"Updated existing job: {normalized_job['title']} at "
                        f"{normalized_job['company']} (merged with job_id={result['id']})"
                    )
                else:
                    # Create new job record
                    new_job = Job(
                        title=normalized_job['title'],
                        company=normalized_job['company'],
                        location=normalized_job['location'],
                        remote=normalized_job.get('remote', False),
                        job_type=normalized_job['job_type'],
                        experience_level=normalized_job['experience_level'],
                        description=normalized_job['description'],
                        requirements=normalized_job.get('requirements'),
                        responsibilities=normalized_job.get('responsibilities'),
                        salary_min=normalized_job.get('salary_min'),
                        salary_max=normalized_job.get('salary_max'),
                        salary_currency=normalized_job.get('salary_currency', 'USD'),
                        source_type=SourceType.AGGREGATED,
                        source_url=normalized_job.get('source_url'),
                        source_platform=source_platform,
                        quality_score=quality_score,
                        status='active',
                        posted_at=normalized_job['posted_at'],
                        expires_at=normalized_job['expires_at'],
                        tags=normalized_job.get('tags', [])
                    )
                    
                    db_session.add(new_job)
                    db_session.flush()  # Get the job ID
                    
                    # Create job source record
                    job_source = JobSource(
                        job_id=new_job.id,
                        source_platform=source_platform,
                        source_url=source_info['url'],
                        source_job_id=source_info.get('job_id'),
                        scraped_at=datetime.utcnow()
                    )
                    db_session.add(job_source)
                    
                    jobs_created += 1
                    logger.debug(
                        f"Created new job: {normalized_job['title']} at "
                        f"{normalized_job['company']} (job_id={new_job.id})"
                    )
                
                # Commit after each job to avoid losing progress on errors
                db_session.commit()
                
            except Exception as e:
                logger.error(
                    f"Error processing job from {source_platform}: {e}",
                    exc_info=True
                )
                db_session.rollback()
                continue
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Update task status to COMPLETED
        await update_scraping_task(
            task.id,
            {
                'status': TaskStatus.COMPLETED,
                'completed_at': datetime.utcnow(),
                'jobs_found': jobs_found,
                'jobs_created': jobs_created,
                'jobs_updated': jobs_updated
            },
            db_session
        )
        
        # Log metrics
        scraper.log_metrics(jobs_found, jobs_created, jobs_updated, duration)
        
        logger.info(
            f"Scraping completed for {source_platform}: "
            f"found={jobs_found}, created={jobs_created}, updated={jobs_updated}, "
            f"duration={duration:.2f}s"
        )
        
        return {
            'success': True,
            'source_platform': source_platform,
            'jobs_found': jobs_found,
            'jobs_created': jobs_created,
            'jobs_updated': jobs_updated,
            'duration': duration,
            'error': None
        }
        
    except Exception as e:
        # Calculate duration
        duration = time.time() - start_time
        
        error_msg = f"Scraping failed for {source_platform}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Update task status to FAILED
        await update_scraping_task(
            task.id,
            {
                'status': TaskStatus.FAILED,
                'completed_at': datetime.utcnow(),
                'error_message': str(e),
                'jobs_found': jobs_found,
                'jobs_created': jobs_created,
                'jobs_updated': jobs_updated,
                'retry_count': task.retry_count + 1
            },
            db_session
        )
        
        return {
            'success': False,
            'source_platform': source_platform,
            'jobs_found': jobs_found,
            'jobs_created': jobs_created,
            'jobs_updated': jobs_updated,
            'duration': duration,
            'error': error_msg
        }
