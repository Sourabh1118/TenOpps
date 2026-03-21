"""
Manual test script for URL import functionality.

This script tests the URL import service without requiring a running database.
It verifies the core logic of URL validation, domain whitelisting, and scraper selection.
"""
from app.services.url_import import (
    validate_import_url,
    extract_domain,
    is_valid_url,
    is_whitelisted_domain,
    get_platform_from_domain,
)


def test_url_validation():
    """Test URL validation logic."""
    print("\n=== Testing URL Validation ===")
    
    # Test valid URLs
    valid_urls = [
        "https://www.linkedin.com/jobs/view/123456789",
        "https://www.indeed.com/viewjob?jk=abc123",
        "https://www.naukri.com/job-listings-123",
        "https://www.monster.com/job-openings/123",
        "https://www.glassdoor.com/job/123",
    ]
    
    for url in valid_urls:
        is_valid, domain, error = validate_import_url(url)
        print(f"✓ {url}")
        print(f"  Valid: {is_valid}, Domain: {domain}, Error: {error}")
        assert is_valid, f"Expected {url} to be valid"
        assert domain is not None, f"Expected domain to be extracted from {url}"
        assert error is None, f"Expected no error for {url}"
    
    # Test invalid URLs
    invalid_urls = [
        ("not-a-url", "Invalid URL format"),
        ("ftp://example.com", "Invalid URL format"),
        ("https://example.com/job", "Domain example.com is not supported"),
        ("https://twitter.com/job/123", "Domain twitter.com is not supported"),
    ]
    
    for url, expected_error_substring in invalid_urls:
        is_valid, domain, error = validate_import_url(url)
        print(f"✗ {url}")
        print(f"  Valid: {is_valid}, Domain: {domain}, Error: {error}")
        assert not is_valid, f"Expected {url} to be invalid"
        assert error is not None, f"Expected error for {url}"
        assert expected_error_substring.lower() in error.lower(), \
            f"Expected error to contain '{expected_error_substring}' for {url}"
    
    print("\n✅ All URL validation tests passed!")


def test_domain_extraction():
    """Test domain extraction logic."""
    print("\n=== Testing Domain Extraction ===")
    
    test_cases = [
        ("https://www.linkedin.com/jobs/view/123", "www.linkedin.com"),
        ("https://indeed.com/viewjob?jk=abc", "indeed.com"),
        ("https://www.naukri.com/job-listings-123", "www.naukri.com"),
        ("http://monster.com/job/123", "monster.com"),
        ("https://glassdoor.com/job/123", "glassdoor.com"),
    ]
    
    for url, expected_domain in test_cases:
        domain = extract_domain(url)
        print(f"URL: {url}")
        print(f"  Extracted: {domain}, Expected: {expected_domain}")
        assert domain == expected_domain, \
            f"Expected domain '{expected_domain}' but got '{domain}'"
    
    print("\n✅ All domain extraction tests passed!")


def test_domain_whitelisting():
    """Test domain whitelisting logic."""
    print("\n=== Testing Domain Whitelisting ===")
    
    whitelisted = [
        "linkedin.com",
        "www.linkedin.com",
        "indeed.com",
        "www.indeed.com",
        "naukri.com",
        "www.naukri.com",
        "monster.com",
        "www.monster.com",
        "glassdoor.com",
        "www.glassdoor.com",
    ]
    
    for domain in whitelisted:
        result = is_whitelisted_domain(domain)
        print(f"✓ {domain}: {result}")
        assert result, f"Expected {domain} to be whitelisted"
    
    not_whitelisted = [
        "example.com",
        "twitter.com",
        "facebook.com",
        "google.com",
    ]
    
    for domain in not_whitelisted:
        result = is_whitelisted_domain(domain)
        print(f"✗ {domain}: {result}")
        assert not result, f"Expected {domain} to NOT be whitelisted"
    
    print("\n✅ All domain whitelisting tests passed!")


def test_platform_detection():
    """Test platform detection from domain."""
    print("\n=== Testing Platform Detection ===")
    
    test_cases = [
        ("www.linkedin.com", "linkedin"),
        ("linkedin.com", "linkedin"),
        ("www.indeed.com", "indeed"),
        ("indeed.com", "indeed"),
        ("www.naukri.com", "naukri"),
        ("naukri.com", "naukri"),
        ("www.monster.com", "monster"),
        ("monster.com", "monster"),
        ("www.glassdoor.com", "glassdoor"),
        ("glassdoor.com", "glassdoor"),
        ("example.com", None),
    ]
    
    for domain, expected_platform in test_cases:
        platform = get_platform_from_domain(domain)
        print(f"Domain: {domain} → Platform: {platform} (expected: {expected_platform})")
        assert platform == expected_platform, \
            f"Expected platform '{expected_platform}' but got '{platform}'"
    
    print("\n✅ All platform detection tests passed!")


def test_url_format_validation():
    """Test URL format validation."""
    print("\n=== Testing URL Format Validation ===")
    
    valid_formats = [
        "https://example.com",
        "http://example.com",
        "https://www.example.com/path",
        "https://example.com/path?query=value",
        "https://example.com:8080/path",
    ]
    
    for url in valid_formats:
        result = is_valid_url(url)
        print(f"✓ {url}: {result}")
        assert result, f"Expected {url} to be valid format"
    
    invalid_formats = [
        "not-a-url",
        "ftp://example.com",
        "example.com",
        "//example.com",
        "https://",
        "",
        None,
    ]
    
    for url in invalid_formats:
        result = is_valid_url(url)
        print(f"✗ {url}: {result}")
        assert not result, f"Expected {url} to be invalid format"
    
    print("\n✅ All URL format validation tests passed!")


def main():
    """Run all tests."""
    print("=" * 60)
    print("URL Import Service - Manual Test Suite")
    print("=" * 60)
    
    try:
        test_url_validation()
        test_domain_extraction()
        test_domain_whitelisting()
        test_platform_detection()
        test_url_format_validation()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nURL import service is working correctly!")
        print("\nNext steps:")
        print("1. Set up .env file with required environment variables")
        print("2. Run database migrations: alembic upgrade head")
        print("3. Start Celery worker: celery -A app.tasks.celery_app worker")
        print("4. Start FastAPI server: uvicorn app.main:app --reload")
        print("5. Test API endpoints with curl or Postman")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
