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
import os
import requests
import feedparser
import urllib.parse
import random
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
import re
from datetime import datetime, timedelta

# Selenium for JavaScript-rendered sites (Requirement 1.3)
try:
    import undetected_chromedriver as uc
    from selenium import webdriver
    HAS_UC = True
except ImportError:
    from selenium import webdriver
    HAS_UC = False

from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from enum import Enum

from app.core.logging import logger
from app.core.redis import redis_client
from app.models.job import Job, JobType, ExperienceLevel, SourceType
from app.models.scraping_task import TaskType, TaskStatus
from app.services.robots_compliance import check_robots_compliance, get_crawl_delay
from app.core.config import settings

class ScrapingProvider(str, Enum):
    SCRAPE_DO = "scrape_do"
    SCRAPER_API = "scraper_api"
    SCRAPING_BEE = "scraping_bee"
    DECODO = "decodo"
    BRIGHT_DATA = "bright_data"
    DIFFBOT = "diffbot"
    PARSEHUB = "parsehub"
    BROWSE_AI = "browse_ai"
    SCRAPE_STORM = "scrape_storm"
    DATABAR = "databar"
    SELENIUM = "selenium"  # Fallback
    DIRECT = "direct"      # Standard requests

class ProviderTransport:
    """Unified handler for various scraping providers."""
    
    @staticmethod
    async def fetch(url: str, provider: ScrapingProvider, render: bool = False, super_proxy: bool = False, source_name: str = "", api_key: Optional[str] = None) -> str:
        """Fetch content using the specified provider."""
        logger.info(f"Fetching {url} via {provider} (render={render}, super={super_proxy})")
        
        try:
            if provider == ScrapingProvider.SCRAPE_DO:
                token = api_key or settings.SCRAPE_DO_TOKEN
                if not token: return ""
                render_param = "&render=true" if render else ""
                super_param = "&super=true" if super_proxy else ""
                proxy_url = f"https://api.scrape.do?token={token}&url={urllib.parse.quote(url)}{render_param}{super_param}"
                response = requests.get(proxy_url, timeout=60 if render else 30)
                return response.text if response.status_code == 200 else ""
                
            elif provider == ScrapingProvider.SCRAPER_API:
                key = api_key or settings.SCRAPER_API_KEY
                if not key: return ""
                payload = {'api_key': key, 'url': url, 'render': str(render).lower()}
                response = requests.get('http://api.scraperapi.com/', params=payload, timeout=60)
                return response.text if response.status_code == 200 else ""
                
            elif provider == ScrapingProvider.SCRAPING_BEE:
                key = settings.SCRAPING_BEE_KEY
                if not key: return ""
                payload = {'api_key': key, 'url': url, 'render_js': str(render).lower()}
                response = requests.get('https://app.scrapingbee.com/api/v1/', params=payload, timeout=60)
                return response.text if response.status_code == 200 else ""

            elif provider == ScrapingProvider.DIFFBOT:
                token = settings.DIFFBOT_TOKEN
                if not token: return ""
                # Diffbot Job API is specialized; for now we return raw HTML via their Extract API
                proxy_url = f"https://api.diffbot.com/v3/analyze?token={token}&url={urllib.parse.quote(url)}"
                response = requests.get(proxy_url, timeout=60)
                return response.text if response.status_code == 200 else ""
                
            elif provider == ScrapingProvider.DECODO:
                token = settings.DECODO_API_TOKEN
                if not token: return ""
                payload = {'token': token, 'url': url, 'render': str(render).lower()}
                response = requests.get('https://api.decodo.com/v1/scraper', params=payload, timeout=60)
                return response.text if response.status_code == 200 else ""
                
            elif provider == ScrapingProvider.BRIGHT_DATA:
                key = settings.BRIGHT_DATA_API_KEY
                zone = settings.BRIGHT_DATA_ZONE
                if not key or not zone: return ""
                headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
                payload = {"url": url, "zone": zone, "format": "raw"}
                response = requests.post("https://api.brightdata.com/request", headers=headers, json=payload, timeout=60)
                return response.text if response.status_code == 200 else ""

            elif provider == ScrapingProvider.DATABAR:
                key = settings.DATABAR_API_KEY
                if not key: return ""
                # Databar usually enrichment-based, but handles direct extraction via API
                headers = {"x-apikey": key}
                response = requests.get(url, headers=headers, timeout=30)
                return response.text if response.status_code == 200 else ""
                
            # Async / Task-based providers (ParseHub, Browse AI) require polling
            if provider in [ScrapingProvider.PARSEHUB, ScrapingProvider.BROWSE_AI]:
                # We use a helper method for these to keep fetch() cleaner
                # Note: This is an async call to a potentially long-running process.
                return await ProviderTransport._fetch_async_task(url, provider, api_key)
            
            return ""
        except Exception as e:
            logger.error(f"Provider {provider} error: {e}")
            return ""

    @staticmethod
    async def _fetch_async_task(url: str, provider: ScrapingProvider, api_key: Optional[str] = None) -> str:
        """Handle providers that require a task trigger and polling (ParseHub, Browse AI)."""
        try:
            if provider == ScrapingProvider.PARSEHUB:
                key = api_key or settings.PARSEHUB_API_KEY
                project_id = settings.PARSEHUB_PROJECT_ID
                if not key or not project_id: return ""
                # Trigger a new run
                params = {"api_key": key, "start_url": url}
                response = requests.post(f"https://www.parsehub.com/api/v2/projects/{project_id}/run", data=params, timeout=30)
                if response.status_code != 200: return ""
                run_token = response.json().get("run_token")
                
                # Poll for completion (Wait up to 2 mins)
                # In a real production scenario, we might use webhooks instead of polling here.
                import time
                for _ in range(24): # 24 * 5s = 120s
                    time.sleep(5)
                    status_resp = requests.get(f"https://www.parsehub.com/api/v2/runs/{run_token}", params={"api_key": key})
                    if status_resp.json().get("status") == "complete":
                        data_resp = requests.get(f"https://www.parsehub.com/api/v2/runs/{run_token}/data", params={"api_key": key})
                        return data_resp.text
                return ""

            elif provider == ScrapingProvider.BROWSE_AI:
                key = api_key or settings.BROWSE_AI_API_KEY
                robot_id = settings.BROWSE_AI_ROBOT_ID
                if not key or not robot_id: return ""
                headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
                payload = {"inputParameters": {"originUrl": url}}
                response = requests.post(f"https://api.browse.ai/v2/robots/{robot_id}/tasks", headers=headers, json=payload, timeout=30)
                if response.status_code != 201: return ""
                task_id = response.json().get("result", {}).get("id")
                
                # Poll for completion
                import time
                for _ in range(24):
                    time.sleep(5)
                    status_resp = requests.get(f"https://api.browse.ai/v2/robots/{robot_id}/tasks/{task_id}", headers=headers)
                    task_status = status_resp.json().get("result", {}).get("status")
                    if task_status == "successful":
                        # In Browse AI, result is often in the task status response or a separate captures endpoint
                        return str(status_resp.json().get("result", {}).get("capturedLists", {}))
                return ""
            
            elif provider == ScrapingProvider.SCRAPE_STORM:
                key = api_key or settings.SCRAPE_STORM_API_KEY
                if not key: return ""
                # ScrapeStorm often uses a task-based approach via their API
                # Triggering a task usually requires a taskId
                return ""

            return ""
        except Exception as e:
            logger.error(f"Async provider {provider} error: {e}")
            return ""


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
        rate_limit_period: int = 60,
        provider: ScrapingProvider = ScrapingProvider.SCRAPE_DO,
        api_key: Optional[str] = None
    ):
        """
        Initialize the base scraper.
        
        Args:
            source_name: Name of the job source (e.g., "linkedin", "indeed")
            rate_limit: Maximum number of requests per period
            rate_limit_period: Time period in seconds (default: 60)
            provider: Preferred scraping provider
            api_key: Optional API key to override settings
        """
        self.source_name = source_name
        self.rate_limit = rate_limit
        self.rate_limit_period = rate_limit_period
        self.preferred_provider = provider
        self.provider_api_key = api_key
        self.max_retries = 3
        self.base_backoff_delay = 5  # seconds
        self.session = requests.Session()
        self.driver: Optional[webdriver.Chrome] = None
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]
        
        # Validation constants matching DB constraints in app/models/job.py
        self.MIN_TITLE_LENGTH = 10
        self.MIN_DESCRIPTION_LENGTH = 50
        self.MAX_TITLE_LENGTH = 200
        self.MAX_DESCRIPTION_LENGTH = 5000
        
        logger.info(
            f"Initialized {self.source_name} scraper with "
            f"rate limit: {rate_limit}/{rate_limit_period}s"
        )
    
    def _validate_job_data(self, job_data: Dict[str, Any]) -> bool:
        """
        Validate job data against database constraints.
        
        Returns True if valid, False otherwise.
        """
        title = job_data.get('title', '')
        description = job_data.get('description', '')
        company = job_data.get('company', '')
        
        if len(title) < self.MIN_TITLE_LENGTH:
            logger.warning(f"Job from {self.source_name} skipped: Title too short ({len(title)} < {self.MIN_TITLE_LENGTH})")
            return False
            
        if len(description) < self.MIN_DESCRIPTION_LENGTH:
            logger.warning(f"Job from {self.source_name} skipped: Description too short ({len(description)} < {self.MIN_DESCRIPTION_LENGTH})")
            return False
            
        if len(company) < 2:
            logger.warning(f"Job from {self.source_name} skipped: Company name too short ({len(company)} < 2)")
            return False
            
        return True
    
    def get_browser_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        """
        Get randomized browser-like headers to avoid bot detection.
        """
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        if referer:
            headers['Referer'] = referer
        return headers
    
    def _save_debug_html(self, html: str, name: str):
        """
        Save diagnostic HTML to a persistent directory for debugging.
        """
        log_dir = "/home/jobplatform/job-platform/backend/logs"
        os.makedirs(log_dir, exist_ok=True)
        filename = f"{name}.html"
        filepath = os.path.join(log_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)
            logger.info(f"Debug HTML saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save debug HTML to {filepath}: {str(e)}")

    def _init_driver(self, stealth: bool = False) -> webdriver.Chrome:
        """
        Initialize a headless Chrome driver (stealthy if requested).
        """
        if stealth and HAS_UC:
            logger.info(f"Initializing UNDETECTED chrome driver for {self.source_name}")
            options = uc.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            
            # Use Xvfb windowed mode if DISPLAY is available
            use_headless = not os.environ.get('DISPLAY')
            
            try:
                # Force version 146 to match server's Chrome
                driver = uc.Chrome(options=options, headless=use_headless, version_main=146)
                return driver
            except Exception as e:
                logger.error(f"Failed to init UC driver, falling back to standard: {e}")
        
        # Standard Selenium fallback
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")  # Use the newer headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-setuid-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--proxy-server='direct://'")
        chrome_options.add_argument("--proxy-bypass-list=*")
        # Generate a unique profile directory for this specific run
        # to prevent cross-talk between concurrent scraper tasks
        timestamp = int(time.time() * 1000)
        profile_dir = f"/tmp/chrome_profile_{self.source_name}_{timestamp}"
        os.makedirs(profile_dir, exist_ok=True)
        
        chrome_options.add_argument(f"--user-data-dir={profile_dir}")
        chrome_options.add_argument(f"user-agent={random.choice(self.user_agents)}")
        
        # Remove hardcoded port to allow OS to assign dynamic ports for concurrency
        # chrome_options.add_argument("--remote-debugging-port=9222")
        
        # Redirect Selenium Manager cache to a writable directory (/tmp)
        # to bypass systemd ProtectHome=read-only restrictions
        os.environ['SE_CACHE_PATH'] = '/tmp/selenium-manager-cache'
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e:
            logger.error(f"Failed to initialize Selenium driver: {e}")
            raise ScrapingError(f"Selenium initialization failed: {e}")

    async def _get_page_content(self, url: str, render: bool = False, super_proxy: bool = False, provider: Optional[ScrapingProvider] = None) -> str:
        """
        Fetch page content using a specific provider or the default system choice.
        """
        # Determine provider: argument > constructor > default
        selected_provider = provider or self.preferred_provider
        
        # 1. Try specified provider
        html = await ProviderTransport.fetch(
            url=url, 
            provider=selected_provider, 
            render=render, 
            super_proxy=super_proxy,
            source_name=self.source_name,
            api_key=self.provider_api_key
        )
        
        if html:
            return html
            
        # 2. Fallback to Scrape.do if not already tried
        if selected_provider != ScrapingProvider.SCRAPE_DO:
            logger.info(f"Falling back to Scrape.do for {url}")
            html = await ProviderTransport.fetch(
                url=url,
                provider=ScrapingProvider.SCRAPE_DO,
                render=render,
                super_proxy=super_proxy,
                source_name=self.source_name,
                api_key=self.provider_api_key if selected_provider == ScrapingProvider.SCRAPE_DO else None
            )
            if html: return html

        # 3. Last resort: Selenium fallback
        if not self.driver:
            self.driver = self._init_driver(stealth=True)
            
        if self.driver:
            logger.info(f"Fetching {url} via Selenium fallback")
            try:
                self.driver.get(url)
                # Wait for specific content based on source
                wait_time = 15 if render else 5
                await asyncio.sleep(wait_time)
                return self.driver.page_source
            except Exception as e:
                logger.error(f"Selenium fallback failed: {e}")
                
        return ""

    def _close_driver(self):
        """
        Safely close the Selenium driver.
        """
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
            except Exception as e:
                logger.warning(f"Error closing Selenium driver: {e}")

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
        raise NotImplementedError
    
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
        raise NotImplementedError
    
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
    if any(term in raw_level_lower for term in ['lead', 'manager', 'head', 'director']):
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
        except ValueError:
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
        f"Created scraping task: id={task.id}, type={task_type}, "
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
        f"status={task.status}, "
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
    
    def __init__(self, rss_feed_url: str, provider: ScrapingProvider = ScrapingProvider.DIRECT, api_key: Optional[str] = None, rate_limit: int = 10):
        """
        Initialize LinkedIn scraper.
        
        Args:
            rss_feed_url: LinkedIn search results URL (legacy parameter name kept for compatibility)
            provider: Preferred scraping provider (default: direct for RSS)
            api_key: Optional API key override
            rate_limit: Maximum requests per minute (default: 10)
        """
        super().__init__(source_name="linkedin", rate_limit=rate_limit, provider=provider, api_key=api_key)
        self.search_url = rss_feed_url
        self.base_url = "https://www.linkedin.com"
        logger.info(f"Initialized LinkedIn HTML scraper for URL: {self.search_url}")
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape jobs from LinkedIn public job search page.
        
        Implements Requirement 1.1:
        - Fetches jobs from LinkedIn HTML guest page
        - Parses HTML using BeautifulSoup4
        - Extracts job data from search results
        
        Returns:
            List of raw job dictionaries from LinkedIn
            
        Raises:
            ScrapingError: If fetching or parsing fails
        """
        from bs4 import BeautifulSoup
        
        try:
            logger.info(f"Fetching LinkedIn jobs from: {self.search_url}")
            
            # Fetch HTML using proxy provider
            logger.info(f"Fetching LinkedIn search results via {self.preferred_provider}: {self.search_url}")
            html = await self._get_page_content(self.search_url, render=True, super_proxy=True)
            
            if not html:
                logger.error(f"Failed to fetch LinkedIn search page via {self.preferred_provider}")
                return []
                
            # Parse HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract job listings
            # Public guest page uses <li> inside <ul> with specific classes
            job_cards = soup.find_all('div', class_='base-card') or \
                        soup.find_all('li', class_='jobs-search-results__list-item') or \
                        soup.find_all('div', class_='base-search-card')
            
            if not job_cards:
                # Try finding all <li> if specific classes aren't present
                results_list = soup.find('ul', class_='jobs-search__results-list')
                if results_list:
                    job_cards = results_list.find_all('li', recursive=False)
            
            if not job_cards:
                logger.warning("No job cards found on LinkedIn search page. Structure might have changed or we are blocked.")
                return []
            
            logger.info(f"Found {len(job_cards)} potential job cards on LinkedIn")
            
            jobs = []
            for card in job_cards:
                try:
                    # Extract title
                    title_elem = card.find('h3', class_='base-search-card__title') or \
                                card.find('span', class_='screen-reader-text') or \
                                card.find('h3')
                    title = title_elem.get_text(strip=True) if title_elem else ''
                    
                    # Extract company
                    company_elem = card.find('a', class_='hidden-nested-link') or \
                                  card.find('h4', class_='base-search-card__subtitle') or \
                                  card.find('div', class_='base-search-card__subtitle')
                    company = company_elem.get_text(strip=True) if company_elem else ''
                    
                    # Extract link
                    link_elem = card.find('a', class_='base-card__full-link') or \
                               card.find('a', class_='base-search-card__title-link') or \
                               card.find('a')
                    link = link_elem.get('href', '') if link_elem else ''
                    
                    # Extract location
                    location_elem = card.find('span', class_='job-search-card__location')
                    location = location_elem.get_text(strip=True) if location_elem else ''
                    
                    # Extract date
                    date_elem = card.find('time', class_='job-search-card__listdate') or \
                               card.find('time', class_='job-search-card__listdate--new')
                    published = date_elem.get('datetime', '') if date_elem else ''
                    posted_text = date_elem.get_text(strip=True) if date_elem else ''
                    
                    if title and link:
                        jobs.append({
                            'title': title,
                            'company': company,
                            'link': link,
                            'location': location,
                            'published': published,
                            'posted_text': posted_text,
                            'description': '', # LinkedIn guest page doesn't show description in list
                        })
                except Exception as e:
                    logger.debug(f"Error parsing individual LinkedIn job card: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(jobs)} jobs from LinkedIn HTML. Fetching descriptions for the first 15.")
            
            # Fetch full descriptions for discovered jobs (Limit to 15 for performance)
            detailed_jobs = []
            for job in jobs[:15]:
                try:
                    await self.wait_for_rate_limit()
                    description = await self._parse_job_page(job['link'])
                    if description:
                        job['description'] = description
                    detailed_jobs.append(job)
                except Exception as e:
                    logger.warning(f"Failed to fetch description for LinkedIn job {job['link']}: {e}")
                    detailed_jobs.append(job)
            
            return detailed_jobs
            
        except requests.RequestException as e:
            error_msg = f"Failed to fetch LinkedIn search page: {e}"
            logger.error(error_msg)
            raise ScrapingError(error_msg)
        except Exception as e:
            error_msg = f"Failed to parse LinkedIn search page: {e}"
            logger.error(error_msg)
            raise ScrapingError(error_msg)
    
    def _extract_location(self, entry: Dict[str, Any]) -> str:
        """
        Extract location from HTML entry.
        
        Args:
            entry: Raw job dictionary from HTML scraping
            
        Returns:
            Location string or 'Remote' if applicable
        """
        location = entry.get('location', 'Not specified')
        
        # Standardize "Remote"
        if any(term in location.lower() for term in ['remote', 'work from home', 'anywhere']):
            return 'Remote'
        
        return location
    
    def _extract_job_type(self, entry: Dict[str, Any]) -> str:
        """
        Extract job type from HTML entry.
        
        Args:
            entry: Raw job dictionary from HTML scraping
            
        Returns:
            Job type string
        """
        # LinkedIn guest list rarely has job type, but we can look for keywords in title
        title = entry.get('title', '').lower()
        
        if 'contract' in title:
            return 'Contract'
        elif 'intern' in title:
            return 'Internship'
        elif 'part-time' in title or 'part time' in title:
            return 'Part-Time'
        
        return 'Full-Time'
    
    def _extract_experience_level(self, entry: Dict[str, Any]) -> str:
        """
        Extract experience level from HTML entry.
        
        Args:
            entry: Raw job dictionary from HTML scraping
            
        Returns:
            Experience level string
        """
        title = entry.get('title', '').lower()
        
        if any(term in title for term in ['senior', 'sr', 'principal', 'staff', 'ii', 'iii']):
            return 'Senior'
        elif any(term in title for term in ['junior', 'jr', 'entry', 'graduate', 'intern']):
            return 'Entry Level'
        elif any(term in title for term in ['lead', 'manager', 'director', 'vp', 'head']):
            return 'Lead'
        
        return 'Mid Level'
    
    async def _parse_job_page(self, url: str) -> Optional[str]:
        """
        Fetch and parse a LinkedIn job detail page to extract the full description.
        
        Args:
            url: LinkedIn job detail URL
            
        Returns:
            Full job description in HTML format, or None if extraction fails
        """
        try:
            # Use preferred provider with rendering for best reliability on LinkedIn detail pages
            logger.info(f"Fetching LinkedIn detail page via {self.preferred_provider}: {url}")
            html = await self._get_page_content(url, render=True, super_proxy=True)
            
            if not html:
                logger.warning(f"Could not fetch content for LinkedIn job detail: {url}")
                return None
                
            soup = BeautifulSoup(html, 'html.parser')
            
            # 1. Try LD+JSON (Most reliable for full content)
            import json
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    data = json.loads(script.string)
                    # LinkedIn guest view often has an array or a single object
                    ld = data if isinstance(data, dict) else (data[0] if isinstance(data, list) and data else {})
                    
                    if ld.get('@type') == 'JobPosting' and ld.get('description'):
                        desc = ld.get('description')
                        # Sometimes it's a list or needs cleanup
                        if isinstance(desc, list): desc = " ".join(desc)
                        logger.info(f"Extracted LinkedIn description via LD+JSON for {url}")
                        return desc
                except Exception as e:
                    logger.debug(f"Error parsing LD+JSON on LinkedIn page {url}: {e}")
                    continue
            
            # 2. Fallback: CSS Selector
            # div.show-more-less-html__markup is the standard for LinkedIn guest view
            desc_elem = soup.select_one('div.show-more-less-html__markup') or \
                        soup.select_one('div.description__text') or \
                        soup.select_one('section.show-more-less-html')
            
            if desc_elem:
                logger.info(f"Extracted LinkedIn description via CSS selector for {url}")
                # Clean up the output to be decent HTML
                return str(desc_elem)
                
            logger.warning(f"No description found on LinkedIn job page: {url}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to parse LinkedIn job page {url}: {e}")
            return None

    def normalize_job(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert LinkedIn HTML format to standard schema.
        
        Implements Requirement 1.5:
        - Maps LinkedIn HTML fields to standard schema
        - Extracts job title, company, location
        - Parses posted date from relative text ('2 days ago')
        - Sets source_platform to 'linkedin'
        
        Args:
            raw_data: Raw job data from LinkedIn HTML scraping
            
        Returns:
            Normalized job dictionary conforming to Job model schema
        """
        from datetime import datetime, timedelta
        import re
        
        # Parse published date from relative text or machine date
        published = raw_data.get('published', '')
        posted_text = raw_data.get('posted_text', '').lower()
        posted_at = datetime.utcnow()
        
        if published:
             try:
                 posted_at = datetime.fromisoformat(published.replace('Z', '+00:00'))
             except Exception:
                 pass
        elif posted_text:
             # Try to parse "2 days ago", "1 week ago", etc.
             num_match = re.search(r'(\d+)', posted_text)
             if num_match:
                 num = int(num_match.group(1))
                 if 'hour' in posted_text:
                     posted_at = datetime.utcnow() - timedelta(hours=num)
                 elif 'day' in posted_text:
                     posted_at = datetime.utcnow() - timedelta(days=num)
                 elif 'week' in posted_text:
                     posted_at = datetime.utcnow() - timedelta(weeks=num)
                 elif 'month' in posted_text:
                     posted_at = datetime.utcnow() - timedelta(days=num*30)
        
        # Calculate expiration date (30 days from posting)
        expires_at = posted_at + timedelta(days=30)
        
        # Check if remote
        location = self._extract_location(raw_data)
        remote = location == 'Remote' or 'remote' in raw_data.get('title', '').lower()
        
        # Build normalized job dictionary
        normalized = {
            'title': raw_data.get('title', 'Untitled Position'),
            'company': raw_data.get('company', 'Unknown Company'),
            'location': location,
            'remote': remote,
            'job_type': normalize_job_type(self._extract_job_type(raw_data)),
            'experience_level': normalize_experience_level(self._extract_experience_level(raw_data)),
            'description': raw_data.get('description') or 'Description not available in summary view. Visit source page for details.',
            'requirements': None,
            'responsibilities': None,
            'salary_min': None,
            'salary_max': None,
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
    """Indeed web scraper using BeautifulSoup4 and Scrape.do API."""
    def __init__(self, query: str, location: str = "", provider: ScrapingProvider = ScrapingProvider.SCRAPE_DO, api_key: Optional[str] = None, rate_limit: int = 15):
        super().__init__(source_name="indeed", rate_limit=rate_limit, provider=provider, api_key=api_key)
        self.query = query
        self.location = location
        self.base_url = "https://www.indeed.com/jobs"
        self.base_host = "https://www.indeed.com"
        logger.info(f"Initialized Indeed scraper with {self.preferred_provider} provider")

    async def scrape(self) -> List[Dict[str, Any]]:
        try:
            params = {'q': self.query, 'l': self.location, 'fromage': '1'}
            search_url = f"{self.base_url}?{urllib.parse.urlencode(params)}"
            html = await self._get_page_content(search_url, render=True, super_proxy=True)
            if not html: return []
            soup = BeautifulSoup(html, 'html.parser')
            
            # Selectors for job links on Indeed search page
            selectors = [
                'a[data-jk]',
                'a.jcs-JobTitle',
                'a[class*="jcs-JobTitle"]',
                'h2.jobTitle a',
                'div.job_seen_beacon a[data-jk]'
            ]
            
            job_links = []
            for selector in selectors:
                found = soup.select(selector)
                if found:
                    job_links.extend(found)
            
            # Remove duplicates while preserving order
            unique_links = []
            seen_jks = set()
            for link in job_links:
                jk = link.get('data-jk')
                if not jk:
                    href = link.get('href', '')
                    match = re.search(r'jk=([a-f0-9]+)', href)
                    if match: jk = match.group(1)
                if jk and jk not in seen_jks:
                    unique_links.append(link)
                    seen_jks.add(jk)
            
            logger.info(f"Indeed found {len(unique_links)} unique job links using selectors. Soup length: {len(str(soup))}")
            if not unique_links:
                logger.debug(f"Indeed soup snippet: {str(soup)[:1000]}")
            
            job_urls = []
            for link in unique_links[:15]:
                jk = link.get("data-jk")
                if not jk:
                    href = link.get("href", "")
                    match = re.search(r"jk=([a-f0-9]+)", href)
                    if match: jk = match.group(1)
                if jk:
                    url = f"{self.base_host}/viewjob?jk={jk}"
                    if url not in job_urls: job_urls.append(url)

            logger.info(f"Found {len(job_urls)} Indeed job URLs")
            all_jobs = []
            for job_url in job_urls:
                data = await self._parse_job_page(job_url)
                if data: all_jobs.append(data)
                await asyncio.sleep(1)
            return all_jobs
            return all_jobs
        except Exception as e:
            logger.error(f"Indeed scraping failed: {e}")
            return []
        finally: self._close_driver()

    async def _parse_job_page(self, url: str) -> Optional[Dict[str, Any]]:
        html = await self._get_page_content(url)
        if not html: return None
        soup = BeautifulSoup(html, 'html.parser')
        job_data = {'link': url}
        import json
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                ld = data if isinstance(data, dict) else (data[0] if isinstance(data, list) and data else {})
                if ld.get('@type') == 'JobPosting':
                    desc = ld.get('description', '')
                    if not isinstance(desc, str):
                        try: desc = BeautifulSoup(str(desc), 'html.parser').get_text('\n', strip=True)
                        except: desc = str(desc)
                    job_data.update({
                        'title': ld.get('title'),
                        'company': ld.get('hiringOrganization', {}).get('name'),
                        'location': ld.get('jobLocation', {}).get('address', {}).get('addressLocality'),
                        'description': desc,
                        'published': ld.get('datePosted'),
                    })
                    break
            except: continue
        if not job_data.get('title'):
            title_elem = soup.select_one('h1')
            if title_elem: job_data['title'] = title_elem.get_text(strip=True)
        return job_data if job_data.get('title') else None

    def normalize_job(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        desc = raw_data.get('description', '')
        if not isinstance(desc, str): desc = str(desc)
        loc = raw_data.get('location', 'Remote')
        posted = datetime.utcnow()
        try: posted = datetime.fromisoformat(raw_data.get('published', '').split('T')[0])
        except: pass
        return {
            'title': raw_data.get('title', 'Unknown'),
            'company': raw_data.get('company', 'Unknown'),
            'location': str(loc),
            'remote': 'remote' in str(loc).lower() or 'remote' in raw_data.get('title', '').lower(),
            'job_type': JobType.FULL_TIME,
            'experience_level': ExperienceLevel.MID,
            'description': desc,
            'source_platform': 'indeed',
            'source_url': raw_data.get('link', ''),
            'posted_at': posted,
            'expires_at': posted + timedelta(days=30),
            'source_type': SourceType.AGGREGATED,
            'salary_currency': 'USD',
        }


class NaukriScraper(BaseScraper):
    """Naukri web scraper using BeautifulSoup4 and Stealth Selenium."""
    def __init__(self, search_url: str, provider: ScrapingProvider = ScrapingProvider.SELENIUM, api_key: Optional[str] = None, rate_limit: int = 5):
        super().__init__(source_name="naukri", rate_limit=rate_limit, provider=provider, api_key=api_key)
        self.search_url = search_url
        self.base_url = "https://www.naukri.com"
        logger.info(f"Initialized Naukri scraper for {search_url}")

    async def scrape(self) -> List[Dict[str, Any]]:
        try:
            self.driver = self._init_driver(stealth=True)
            if not self.driver: raise ScrapingError("Failed to init driver")
            self.driver.get(self.search_url)
            try:
                wait = WebDriverWait(self.driver, 20)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.srp-jobtuple-wrapper, article.jobTuple")))
                time.sleep(2)
            except TimeoutException: return []
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            job_urls = []
            for card in soup.select('div.srp-jobtuple-wrapper, article.jobTuple'):
                a = card.select_one('a.title, a.job-title')
                if a and a.get('href'):
                    url = a['href']
                    if not url.startswith('http'): url = self.base_url + url
                    job_urls.append(url)
            
            jobs = []
            for url in job_urls[:15]:
                try:
                    await self.wait_for_rate_limit()
                    time.sleep(random.uniform(2, 4))
                    self.driver.get(url)
                    # Simple wait for content
                    time.sleep(2)
                    job_data = self._parse_job_page(BeautifulSoup(self.driver.page_source, 'html.parser'), url)
                    if job_data: jobs.append(job_data)
                except Exception as e:
                    logger.debug(f"Failed to parse Naukri job page {url}: {e}")
                    continue
            return jobs
        except Exception as e:
            logger.error(f"Naukri scraping failed: {e}")
            return []
        finally: self._close_driver()

    def _parse_job_page(self, soup, url: str) -> Optional[Dict[str, Any]]:
        import json
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                ld = data if isinstance(data, dict) else (data[0] if isinstance(data, list) and data else {})
                if ld.get('@type') == 'JobPosting':
                    return {
                        'title': ld.get('title'),
                        'company': ld.get('hiringOrganization', {}).get('name'),
                        'location': ld.get('jobLocation', {}).get('address', {}).get('addressLocality'),
                        'description': ld.get('description'),
                        'posted': ld.get('datePosted'),
                        'url': url
                    }
            except: continue
        return None

    def normalize_job(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        dt = datetime.utcnow()
        try: dt = datetime.fromisoformat(raw_data.get('posted', '').split('T')[0])
        except: pass
        return {
            'title': raw_data.get('title', 'Unknown'),
            'company': raw_data.get('company', 'Unknown'),
            'location': str(raw_data.get('location', 'India')),
            'remote': 'remote' in str(raw_data.get('description', '')).lower(),
            'job_type': JobType.FULL_TIME,
            'experience_level': ExperienceLevel.MID,
            'description': str(raw_data.get('description', '')).replace('\n', ' ')[:5000],
            'source_platform': 'naukri',
            'source_url': raw_data.get('url', ''),
            'posted_at': dt,
            'expires_at': dt + timedelta(days=30),
            'source_type': SourceType.AGGREGATED,
            'salary_currency': 'INR',
        }


class MonsterScraper(BaseScraper):
    """Monster web scraper using Scrape.do API."""
    def __init__(self, query: str = "", location: str = "", provider: ScrapingProvider = ScrapingProvider.SCRAPE_DO, api_key: Optional[str] = None, rate_limit: int = 5):
        super().__init__(source_name="monster", rate_limit=rate_limit, provider=provider, api_key=api_key)
        self.query = query
        self.location = location
        self.search_url = f"https://www.monster.com/jobs/search?q={urllib.parse.quote(query or '')}&where={urllib.parse.quote(location or '')}"
        logger.info(f"Initialized Monster scraper with {self.preferred_provider} provider")

    async def scrape(self) -> List[Dict[str, Any]]:
        try:
            html = await self._get_page_content(self.search_url, render=True, super_proxy=True)
            if not html: return []
            soup = BeautifulSoup(html, 'html.parser')
            
            # Refined Monster selectors
            selectors = [
                'a.title-link',
                'a[class*="title-link"]',
                'a[href*="/job-openings/"]',
                'a[data-testid="job-card-link"]',
                '[data-testid="jobcard-container"] a',
                'div[class*="JobCard-sc"] a',
                'a[class*="job-name"]',
                'h2 a',
                'div[class*="job-card"] a'
            ]
            
            job_links = []
            for selector in selectors:
                found = soup.select(selector)
                if found: job_links.extend(found)
            
            # Remove duplicates and get URLs only
            urls = []
            for link in job_links:
                href = link.get('href', '')
                if href:
                    if not href.startswith('http'): 
                        path = href if href.startswith('/') else '/' + href
                        href = f'https://www.monster.com{path}'
                    if href not in urls: urls.append(href)
            
            logger.info(f'Monster found {len(urls)} unique job links. Soup length: {len(str(soup))}')
            if not urls:
                logger.info(f'Monster soup snippet: {str(soup)[:3000]}')
            jobs = []
            for job_url in urls[:15]:
                try:
                    h = await self._get_page_content(job_url)
                    if h:
                        data = self._parse_job_page(BeautifulSoup(h, 'html.parser'), job_url)
                        if data: jobs.append(data)
                    await asyncio.sleep(1)
                except: continue
            return jobs
        except Exception as e:
            logger.error(f"Monster scrape failed: {e}")
            return []
        finally: self._close_driver()

    def _parse_job_page(self, soup, url: str) -> Optional[Dict[str, Any]]:
        import json
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                ld = data if isinstance(data, dict) else (data[0] if isinstance(data, list) and data else {})
                if ld.get("@type") == "JobPosting":
                    desc = ld.get("description", "")
                    if not isinstance(desc, str):
                        try: desc = BeautifulSoup(str(desc), "html.parser").get_text("\n", strip=True)
                        except: desc = str(desc)
                    return {
                        "title": ld.get("title"),
                        "company": ld.get("hiringOrganization", {}).get("name"),
                        "location": ld.get("jobLocation", {}).get("address", {}).get("addressLocality"),
                        "description": desc,
                        "posted": ld.get("datePosted"),
                        "url": url
                    }
            except: continue
        return None

    def normalize_job(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        dt = datetime.utcnow()
        try: dt = datetime.fromisoformat(raw_data.get('posted', '').split('T')[0])
        except: pass
        return {
            'title': raw_data.get('title', 'Unknown'),
            'company': raw_data.get('company', 'Unknown'),
            'location': str(raw_data.get('location', 'USA')),
            'remote': 'remote' in str(raw_data.get('description', '')).lower(),
            'job_type': JobType.FULL_TIME,
            'experience_level': ExperienceLevel.MID,
            'description': str(raw_data.get('description', '')).replace('\n', ' ')[:5000],
            'source_platform': 'monster',
            'source_url': raw_data.get('url', ''),
            'posted_at': dt,
            'expires_at': dt + timedelta(days=30),
            'source_type': SourceType.AGGREGATED,
            'salary_currency': 'USD',
        }


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
    """
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
    
    jobs_found: int = 0
    jobs_created: int = 0
    jobs_updated: int = 0
    
    try:
        # Initialize scraper with configuration
        scraper_class = SCRAPER_REGISTRY[source_platform.lower()]
        
        if scraper_config is None:
            scraper_config = {}
        
        # Get scraper-specific configuration from settings
        raw_jobs: List[Dict[str, Any]] = []
        scraper: Optional[BaseScraper] = None
        if source_platform.lower() == 'linkedin':
            # Use plural LINKEDIN_RSS_URLS as defined in config.py
            rss_urls = scraper_config.get('rss_urls') or getattr(settings, 'LINKEDIN_RSS_URLS', [])
            if not rss_urls:
                # Fallback to single URL or default
                rss_urls = [scraper_config.get('rss_url', 'https://www.linkedin.com/jobs/search/?f_TPR=r86400&format=rss')]
            
            if isinstance(rss_urls, str):
                rss_urls = [rss_urls]
            
            for url in rss_urls:
                try:
                    logger.info(f"Scraping LinkedIn feed: {url}")
                    provider = scraper_config.get('provider', ScrapingProvider.DIRECT)
                    api_key = scraper_config.get('api_key')
                    scraper = scraper_class(rss_feed_url=url, provider=provider, api_key=api_key)
                    # Use scrape_with_retry for individual feeds
                    feed_jobs = await scraper.scrape_with_retry()
                    raw_jobs.extend(feed_jobs)
                except Exception as e:
                    logger.error(f"Error scraping LinkedIn feed {url}: {e}")
            
            # Ensure we have a scraper instance for normalization later
            if not scraper and rss_urls:
                scraper = scraper_class(rss_feed_url=rss_urls[0])
            elif not scraper:
                scraper = scraper_class(rss_feed_url='https://www.linkedin.com/jobs/search/')
        elif source_platform.lower() == 'indeed':
            provider = scraper_config.get('provider', ScrapingProvider.SCRAPE_DO)
            api_key = scraper_config.get('api_key')
            query = scraper_config.get('query', getattr(settings, 'INDEED_SEARCH_QUERY', 'software engineer'))
            location = scraper_config.get('location', getattr(settings, 'INDEED_SEARCH_LOCATION', 'New York'))
            scraper = IndeedScraper(query=query, location=location, provider=provider, api_key=api_key)
            raw_jobs = await scraper.scrape_with_retry()
        elif source_platform.lower() == 'naukri':
            search_url = scraper_config.get('search_url', getattr(settings, 'NAUKRI_SEARCH_URL', ''))
            provider = scraper_config.get('provider', ScrapingProvider.SELENIUM)
            api_key = scraper_config.get('api_key')
            scraper = NaukriScraper(search_url=search_url, provider=provider, api_key=api_key)
            raw_jobs = await scraper.scrape_with_retry()
        elif source_platform.lower() == 'monster':
            provider = scraper_config.get('provider', ScrapingProvider.SCRAPE_DO)
            api_key = scraper_config.get('api_key')
            query = scraper_config.get('query', 'software engineer')
            location = scraper_config.get('location', 'New York')
            scraper = MonsterScraper(query=query, location=location, provider=provider, api_key=api_key)
            raw_jobs = await scraper.scrape_with_retry()
        else:
            raise ValueError(f"Unsupported source platform: {source_platform}")
            
        if not scraper:
            logger.error(f"Failed to initialize scraper for {source_platform}")
            result['error'] = f"Scraper not initialized for {source_platform}"
            return result
        
        logger.info(f"Starting scraping for {source_platform}")
        
        # raw_jobs is now already populated for the specific platform logic above
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
        
        # Capture a more descriptive error message
        error_msg = f"Scraping failed for {source_platform}: {str(e)}"
        if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
             error_msg = f"{source_platform.capitalize()} returned HTTP {e.response.status_code}: {str(e)}"
        
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
