"""
URL import service for the job aggregation platform.

This module provides functions for importing jobs from URLs:
- URL validation and domain whitelisting
- Domain extraction
- URL format validation
"""
from typing import Optional, Tuple
from urllib.parse import urlparse
import re

from app.core.logging import logger


# Whitelisted domains for URL imports (Requirement 5.3, 5.4)
WHITELISTED_DOMAINS = {
    'linkedin.com',
    'www.linkedin.com',
    'indeed.com',
    'www.indeed.com',
    'naukri.com',
    'www.naukri.com',
    'monster.com',
    'www.monster.com',
    'glassdoor.com',
    'www.glassdoor.com',
}


def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL.
    
    This function implements Requirement 5.2:
    - Parses URL and extracts domain
    - Returns None if URL is invalid
    
    Args:
        url: URL string to extract domain from
        
    Returns:
        Domain string (e.g., "linkedin.com") or None if invalid
        
    Example:
        >>> extract_domain("https://www.linkedin.com/jobs/view/123")
        'www.linkedin.com'
        >>> extract_domain("invalid-url")
        None
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        if not domain:
            logger.warning(f"Could not extract domain from URL: {url}")
            return None
        
        logger.debug(f"Extracted domain '{domain}' from URL: {url}")
        return domain
        
    except Exception as e:
        logger.error(f"Error extracting domain from URL '{url}': {e}")
        return None


def is_valid_url(url: str) -> bool:
    """
    Validate URL format.
    
    This function implements Requirement 5.1:
    - Checks if URL has valid format
    - Validates protocol (http/https)
    - Validates domain structure
    
    Args:
        url: URL string to validate
        
    Returns:
        True if URL is valid, False otherwise
        
    Example:
        >>> is_valid_url("https://www.linkedin.com/jobs/view/123")
        True
        >>> is_valid_url("not-a-url")
        False
        >>> is_valid_url("ftp://example.com")
        False
    """
    if not url or not isinstance(url, str):
        return False
    
    try:
        # Parse URL
        parsed = urlparse(url)
        
        # Check protocol (must be http or https)
        if parsed.scheme not in ['http', 'https']:
            logger.debug(f"Invalid URL protocol: {parsed.scheme}")
            return False
        
        # Check domain exists
        if not parsed.netloc:
            logger.debug(f"URL missing domain: {url}")
            return False
        
        # Basic domain format validation (contains at least one dot)
        if '.' not in parsed.netloc:
            logger.debug(f"Invalid domain format: {parsed.netloc}")
            return False
        
        logger.debug(f"URL validation passed: {url}")
        return True
        
    except Exception as e:
        logger.error(f"Error validating URL '{url}': {e}")
        return False


def is_whitelisted_domain(domain: str) -> bool:
    """
    Check if domain is in whitelist.
    
    This function implements Requirements 5.3, 5.4:
    - Checks domain against whitelist
    - Supports LinkedIn, Indeed, Naukri, Monster, Glassdoor
    - Returns True if domain is whitelisted
    
    Args:
        domain: Domain string to check
        
    Returns:
        True if domain is whitelisted, False otherwise
        
    Example:
        >>> is_whitelisted_domain("www.linkedin.com")
        True
        >>> is_whitelisted_domain("example.com")
        False
    """
    if not domain:
        return False
    
    domain_lower = domain.lower()
    is_whitelisted = domain_lower in WHITELISTED_DOMAINS
    
    logger.debug(
        f"Domain whitelist check: '{domain}' -> {is_whitelisted}"
    )
    
    return is_whitelisted


def validate_import_url(url: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate URL for import and check domain whitelist.
    
    This function implements Requirements 5.1, 5.2, 5.3, 5.4:
    - Validates URL format
    - Extracts domain
    - Checks domain against whitelist
    - Returns validation result with error message if invalid
    
    Args:
        url: URL string to validate
        
    Returns:
        Tuple of (is_valid: bool, domain: Optional[str], error: Optional[str])
        - is_valid: True if URL is valid and domain is whitelisted
        - domain: Extracted domain if valid, None otherwise
        - error: Error message if invalid, None if valid
        
    Example:
        >>> validate_import_url("https://www.linkedin.com/jobs/view/123")
        (True, 'www.linkedin.com', None)
        >>> validate_import_url("https://example.com/job")
        (False, 'example.com', 'Domain example.com is not supported for import')
        >>> validate_import_url("invalid-url")
        (False, None, 'Invalid URL format')
    """
    # Validate URL format
    if not is_valid_url(url):
        error = "Invalid URL format. URL must start with http:// or https://"
        logger.warning(f"URL validation failed: {error} - {url}")
        return False, None, error
    
    # Extract domain
    domain = extract_domain(url)
    if not domain:
        error = "Could not extract domain from URL"
        logger.warning(f"Domain extraction failed: {url}")
        return False, None, error
    
    # Check whitelist
    if not is_whitelisted_domain(domain):
        error = (
            f"Domain {domain} is not supported for import. "
            f"Supported domains: LinkedIn, Indeed, Naukri, Monster, Glassdoor"
        )
        logger.warning(f"Domain not whitelisted: {domain}")
        return False, domain, error
    
    logger.info(f"URL validation passed: {url} (domain: {domain})")
    return True, domain, None


def get_platform_from_domain(domain: str) -> Optional[str]:
    """
    Get platform name from domain.
    
    Args:
        domain: Domain string
        
    Returns:
        Platform name (linkedin, indeed, naukri, monster, glassdoor) or None
        
    Example:
        >>> get_platform_from_domain("www.linkedin.com")
        'linkedin'
        >>> get_platform_from_domain("indeed.com")
        'indeed'
    """
    if not domain:
        return None
    
    domain_lower = domain.lower()
    
    if 'linkedin' in domain_lower:
        return 'linkedin'
    elif 'indeed' in domain_lower:
        return 'indeed'
    elif 'naukri' in domain_lower:
        return 'naukri'
    elif 'monster' in domain_lower:
        return 'monster'
    elif 'glassdoor' in domain_lower:
        return 'glassdoor'
    
    return None
