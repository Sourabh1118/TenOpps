"""
Tests for robots.txt compliance checking.

This module tests:
- Robots.txt fetching and parsing
- URL permission checking
- Crawl delay extraction
- Caching behavior
"""
import pytest
from unittest.mock import Mock, patch
from app.services.robots_compliance import RobotsChecker, check_robots_compliance, get_crawl_delay


@pytest.fixture
def robots_checker():
    """Create a RobotsChecker instance."""
    return RobotsChecker()


def test_get_robots_url(robots_checker):
    """Test extracting robots.txt URL from a page URL."""
    url = "https://example.com/jobs/software-engineer"
    robots_url = robots_checker._get_robots_url(url)
    
    assert robots_url == "https://example.com/robots.txt"


def test_get_robots_url_with_port(robots_checker):
    """Test extracting robots.txt URL with port number."""
    url = "https://example.com:8080/jobs/software-engineer"
    robots_url = robots_checker._get_robots_url(url)
    
    assert robots_url == "https://example.com:8080/robots.txt"


@patch('app.services.robots_compliance.requests.get')
def test_can_fetch_allowed(mock_get, robots_checker):
    """Test checking if URL is allowed by robots.txt."""
    # Mock robots.txt response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = """
User-agent: *
Disallow: /admin/
Allow: /jobs/
"""
    mock_get.return_value = mock_response
    
    # Test allowed URL
    url = "https://example.com/jobs/software-engineer"
    can_fetch = robots_checker.can_fetch(url)
    
    assert can_fetch == True


@patch('app.services.robots_compliance.requests.get')
def test_can_fetch_disallowed(mock_get, robots_checker):
    """Test checking if URL is disallowed by robots.txt."""
    # Mock robots.txt response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = """
User-agent: *
Disallow: /admin/
Disallow: /private/
"""
    mock_get.return_value = mock_response
    
    # Test disallowed URL
    url = "https://example.com/admin/users"
    can_fetch = robots_checker.can_fetch(url)
    
    assert can_fetch == False


@patch('app.services.robots_compliance.requests.get')
def test_can_fetch_no_robots_txt(mock_get, robots_checker):
    """Test checking URL when no robots.txt exists."""
    # Mock 404 response
    mock_response = Mock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response
    
    # Should allow all when no robots.txt
    url = "https://example.com/jobs/software-engineer"
    can_fetch = robots_checker.can_fetch(url)
    
    assert can_fetch == True


@patch('app.services.robots_compliance.requests.get')
def test_get_crawl_delay(mock_get, robots_checker):
    """Test extracting crawl delay from robots.txt."""
    # Mock robots.txt response with crawl delay
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = """
User-agent: *
Crawl-delay: 5
Disallow: /admin/
"""
    mock_get.return_value = mock_response
    
    url = "https://example.com/jobs/software-engineer"
    crawl_delay = robots_checker.get_crawl_delay(url)
    
    assert crawl_delay == 5.0


@patch('app.services.robots_compliance.requests.get')
def test_get_crawl_delay_none(mock_get, robots_checker):
    """Test when no crawl delay is specified."""
    # Mock robots.txt response without crawl delay
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = """
User-agent: *
Disallow: /admin/
"""
    mock_get.return_value = mock_response
    
    url = "https://example.com/jobs/software-engineer"
    crawl_delay = robots_checker.get_crawl_delay(url)
    
    assert crawl_delay is None


@patch('app.services.robots_compliance.requests.get')
def test_can_fetch_with_custom_user_agent(mock_get, robots_checker):
    """Test checking URL with custom user agent."""
    # Mock robots.txt response with specific user agent rules
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = """
User-agent: BadBot
Disallow: /

User-agent: *
Allow: /
"""
    mock_get.return_value = mock_response
    
    url = "https://example.com/jobs/software-engineer"
    
    # Should be allowed for default user agent
    can_fetch = robots_checker.can_fetch(url)
    assert can_fetch == True
    
    # Should be disallowed for BadBot
    can_fetch = robots_checker.can_fetch(url, user_agent="BadBot")
    assert can_fetch == False


@patch('app.services.robots_compliance.requests.get')
def test_error_handling_allows_fetch(mock_get, robots_checker):
    """Test that errors result in allowing the fetch (fail open)."""
    # Mock request exception
    mock_get.side_effect = Exception("Network error")
    
    url = "https://example.com/jobs/software-engineer"
    can_fetch = robots_checker.can_fetch(url)
    
    # Should allow on error (fail open)
    assert can_fetch == True


def test_convenience_functions():
    """Test convenience functions."""
    with patch('app.services.robots_compliance.robots_checker.can_fetch') as mock_can_fetch:
        mock_can_fetch.return_value = True
        
        result = check_robots_compliance("https://example.com/jobs")
        assert result == True
        mock_can_fetch.assert_called_once()
    
    with patch('app.services.robots_compliance.robots_checker.get_crawl_delay') as mock_get_delay:
        mock_get_delay.return_value = 5.0
        
        result = get_crawl_delay("https://example.com/jobs")
        assert result == 5.0
        mock_get_delay.assert_called_once()
