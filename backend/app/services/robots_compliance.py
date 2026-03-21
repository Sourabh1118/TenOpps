"""
Robots.txt compliance utilities for web scraping.

This module provides functionality to check and respect robots.txt
directives before scraping external sources.

Implements Requirement 17.5: System shall respect robots.txt directives
"""
import requests
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from typing import Optional, Dict
from datetime import datetime, timedelta

from app.core.logging import logger
from app.core.redis import redis_client


class RobotsChecker:
    """
    Checker for robots.txt compliance.
    
    Caches robots.txt files in Redis for 24 hours to avoid
    repeated fetches.
    """
    
    def __init__(self):
        """Initialize the robots checker."""
        self.cache_ttl = 86400  # 24 hours
        self.user_agent = "JobAggregationBot/1.0"
    
    def _get_robots_url(self, url: str) -> str:
        """
        Get the robots.txt URL for a given URL.
        
        Args:
            url: The URL to check
            
        Returns:
            The robots.txt URL for the domain
        """
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        return robots_url
    
    def _get_cached_robots(self, robots_url: str) -> Optional[str]:
        """
        Get cached robots.txt content from Redis.
        
        Args:
            robots_url: The robots.txt URL
            
        Returns:
            Cached robots.txt content or None if not cached
        """
        try:
            redis = redis_client.get_cache_client()
            cache_key = f"robots:{robots_url}"
            cached = redis.get(cache_key)
            
            if cached:
                logger.debug(f"Using cached robots.txt for {robots_url}")
                return cached.decode('utf-8') if isinstance(cached, bytes) else cached
            
            return None
        except Exception as e:
            logger.error(f"Error getting cached robots.txt: {e}")
            return None
    
    def _cache_robots(self, robots_url: str, content: str) -> None:
        """
        Cache robots.txt content in Redis.
        
        Args:
            robots_url: The robots.txt URL
            content: The robots.txt content
        """
        try:
            redis = redis_client.get_cache_client()
            cache_key = f"robots:{robots_url}"
            redis.setex(cache_key, self.cache_ttl, content)
            logger.debug(f"Cached robots.txt for {robots_url}")
        except Exception as e:
            logger.error(f"Error caching robots.txt: {e}")
    
    def _fetch_robots(self, robots_url: str) -> Optional[str]:
        """
        Fetch robots.txt from URL.
        
        Args:
            robots_url: The robots.txt URL
            
        Returns:
            robots.txt content or None if not found
        """
        try:
            response = requests.get(robots_url, timeout=10)
            
            if response.status_code == 200:
                content = response.text
                self._cache_robots(robots_url, content)
                return content
            elif response.status_code == 404:
                # No robots.txt - allow all
                logger.info(f"No robots.txt found at {robots_url}, allowing all")
                return None
            else:
                logger.warning(
                    f"Unexpected status code {response.status_code} "
                    f"for robots.txt at {robots_url}"
                )
                return None
        except Exception as e:
            logger.error(f"Error fetching robots.txt from {robots_url}: {e}")
            return None
    
    def can_fetch(self, url: str, user_agent: Optional[str] = None) -> bool:
        """
        Check if URL can be fetched according to robots.txt.
        
        Implements Requirement 17.5:
        - Checks robots.txt before scraping
        - Respects disallow directives
        
        Args:
            url: The URL to check
            user_agent: User agent string (defaults to JobAggregationBot)
            
        Returns:
            True if URL can be fetched, False otherwise
        """
        if user_agent is None:
            user_agent = self.user_agent
        
        try:
            robots_url = self._get_robots_url(url)
            
            # Try to get cached robots.txt
            robots_content = self._get_cached_robots(robots_url)
            
            # If not cached, fetch it
            if robots_content is None:
                robots_content = self._fetch_robots(robots_url)
            
            # If no robots.txt, allow all
            if robots_content is None:
                return True
            
            # Parse robots.txt
            parser = RobotFileParser()
            parser.parse(robots_content.splitlines())
            
            # Check if URL can be fetched
            can_fetch = parser.can_fetch(user_agent, url)
            
            if not can_fetch:
                logger.warning(
                    f"URL {url} is disallowed by robots.txt for user agent {user_agent}"
                )
            
            return can_fetch
            
        except Exception as e:
            logger.error(f"Error checking robots.txt for {url}: {e}")
            # On error, allow the request (fail open)
            return True
    
    def get_crawl_delay(self, url: str, user_agent: Optional[str] = None) -> Optional[float]:
        """
        Get crawl delay from robots.txt.
        
        Implements Requirement 17.5:
        - Respects crawl-delay directive
        
        Args:
            url: The URL to check
            user_agent: User agent string (defaults to JobAggregationBot)
            
        Returns:
            Crawl delay in seconds or None if not specified
        """
        if user_agent is None:
            user_agent = self.user_agent
        
        try:
            robots_url = self._get_robots_url(url)
            
            # Try to get cached robots.txt
            robots_content = self._get_cached_robots(robots_url)
            
            # If not cached, fetch it
            if robots_content is None:
                robots_content = self._fetch_robots(robots_url)
            
            # If no robots.txt, no delay
            if robots_content is None:
                return None
            
            # Parse robots.txt
            parser = RobotFileParser()
            parser.parse(robots_content.splitlines())
            
            # Get crawl delay
            crawl_delay = parser.crawl_delay(user_agent)
            
            if crawl_delay:
                logger.info(
                    f"Crawl delay for {url} with user agent {user_agent}: "
                    f"{crawl_delay} seconds"
                )
            
            return crawl_delay
            
        except Exception as e:
            logger.error(f"Error getting crawl delay for {url}: {e}")
            return None


# Global instance
robots_checker = RobotsChecker()


def check_robots_compliance(url: str, user_agent: Optional[str] = None) -> bool:
    """
    Check if URL can be scraped according to robots.txt.
    
    Convenience function that uses the global robots checker.
    
    Args:
        url: The URL to check
        user_agent: User agent string (optional)
        
    Returns:
        True if URL can be scraped, False otherwise
    """
    return robots_checker.can_fetch(url, user_agent)


def get_crawl_delay(url: str, user_agent: Optional[str] = None) -> Optional[float]:
    """
    Get crawl delay for URL from robots.txt.
    
    Convenience function that uses the global robots checker.
    
    Args:
        url: The URL to check
        user_agent: User agent string (optional)
        
    Returns:
        Crawl delay in seconds or None if not specified
    """
    return robots_checker.get_crawl_delay(url, user_agent)
