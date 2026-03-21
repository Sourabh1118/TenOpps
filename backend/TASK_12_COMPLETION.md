# Task 12 Completion: Naukri Web Scraper

## Summary

Successfully implemented the Naukri web scraper with full functionality including HTML parsing with BeautifulSoup4, job URL extraction, individual job page scraping, job normalization, and comprehensive test coverage.

## Implementation Details

### 12.1 Naukri Web Scraper Implementation

**File**: `backend/app/services/scraping.py`

Created `NaukriScraper` class that extends `BaseScraper` with the following features:

1. **Web Scraping with BeautifulSoup4**:
   - Uses BeautifulSoup4 to parse HTML content from Naukri.com
   - Fetches search results page and extracts job URLs
   - Fetches individual job pages for detailed information
   - Implements proper error handling and logging

2. **Job URL Extraction**:
   - Parses search results page to find job listings
   - Extracts job URLs from article tags with class 'jobTuple'
   - Handles both relative and absolute URLs
   - Converts relative URLs to absolute using base URL

3. **Individual Job Page Parsing**:
   - Fetches up to 20 jobs per scrape to respect rate limits
   - Parses job title, company, location, experience, salary
   - Extracts job description and key skills
   - Handles missing or malformed data gracefully
   - Logs errors for individual job parsing failures without stopping the entire scrape

4. **Rate Limiting**:
   - Default rate limit: 5 requests per minute (as specified in requirements)
   - Inherits rate limiting infrastructure from `BaseScraper`
   - Uses Redis-based token bucket algorithm
   - Waits for rate limit before fetching each job page

5. **User-Agent Header**:
   - Uses realistic User-Agent header to avoid being blocked
   - Mimics Chrome browser on Windows

### 12.2 Naukri Job Normalization Implementation

**File**: `backend/app/services/scraping.py`

Implemented comprehensive job normalization with the following features:

1. **Field Mapping**:
   - Maps `title` → `title`
   - Maps `company` → `company`
   - Maps `location` → `location`
   - Maps `description` → `description`
   - Maps `skills` → `requirements` (comma-separated)
   - Maps `url` → `source_url`
   - Sets `source_platform` to 'naukri'
   - Sets `source_type` to `SourceType.AGGREGATED`

2. **Experience Level Extraction**:
   - Analyzes experience text for year ranges (e.g., "5-8 years")
   - Maps years to experience levels:
     - 0-2 years → Entry Level
     - 3-4 years → Mid Level
     - 5-7 years → Senior
     - 8+ years → Lead
   - Detects keywords: fresher, entry, junior, senior, lead, manager
   - Uses `normalize_experience_level()` helper for standardization
   - Defaults to Mid Level if not detected

3. **Job Type Extraction**:
   - Uses `normalize_job_type()` helper for standardization
   - Defaults to Full-Time if not specified

4. **Date Parsing**:
   - Parses relative time strings (e.g., "Just now", "Posted 2 days ago", "Posted 5 hours ago", "Posted 2 weeks ago")
   - Handles various formats: days, hours, weeks
   - Falls back to current time if parsing fails

5. **Salary Extraction**:
   - Uses existing `extract_salary_info()` helper
   - Extracts salary ranges from text (e.g., "15-20 Lacs PA")
   - Sets currency to INR (Indian Rupees) as Naukri is primarily an Indian job site

6. **Remote Detection**:
   - Checks location and description for "remote" keyword
   - Sets `remote` flag accordingly

7. **Skills Extraction**:
   - Extracts key skills from job page
   - Stores as comma-separated string in requirements field

8. **Expiration Date**:
   - Calculates expiration as 30 days from posting date
   - Follows same pattern as LinkedInScraper and IndeedScraper

## Test Coverage

**File**: `backend/tests/test_scraping.py`

Added comprehensive test suite with 18 tests covering:

### Initialization Tests
- ✅ Scraper initialization with search URL and rate limit

### Scraping Tests
- ✅ Successful scraping with mock HTML responses
- ✅ Handling empty search results (no jobs found)
- ✅ Request error handling

### Normalization Tests
- ✅ Basic job normalization with all fields
- ✅ Remote job detection
- ✅ Entry level job detection
- ✅ Salary extraction

### HTML Parsing Tests
- ✅ Job URL extraction from search results
- ✅ Job page parsing with all fields

### Experience Level Extraction Tests
- ✅ Entry level detection (0-2 years)
- ✅ Mid level detection (3-4 years)
- ✅ Senior level detection (5-7 years)
- ✅ Lead level detection (8+ years)

### Date Parsing Tests
- ✅ "Just now" parsing
- ✅ "X days ago" parsing
- ✅ "X hours ago" parsing
- ✅ "X weeks ago" parsing

## Test Results

```
================================== 92 passed, 24 warnings in 1.23s ==================================
```

All 92 tests pass, including:
- 18 new Naukri scraper tests
- 74 existing scraping service tests

No diagnostics errors or warnings in the implementation.

## Requirements Validation

### Requirement 1.3: Naukri Web Scraping ✅
- ✅ Fetches jobs from Naukri.com via web scraping
- ✅ Uses BeautifulSoup4 to parse HTML
- ✅ Extracts job URLs from search results
- ✅ Fetches individual job pages and parses details

### Requirement 1.5: Job Normalization ✅
- ✅ Maps Naukri HTML fields to standard schema
- ✅ Extracts job title, company, location, description
- ✅ Parses experience level from experience field
- ✅ Extracts salary information
- ✅ Extracts key skills as requirements
- ✅ Sets source_platform to 'naukri'
- ✅ Sets source_type to AGGREGATED

### Requirement 1.8: Retry Logic ✅
- ✅ Inherits retry logic from BaseScraper
- ✅ Exponential backoff up to 3 attempts

### Requirement 1.9: Rate Limiting ✅
- ✅ Rate limit: 5 requests per minute
- ✅ Uses Redis-based token bucket algorithm
- ✅ Inherits from BaseScraper infrastructure

## Usage Example

```python
from app.services.scraping import NaukriScraper

# Initialize scraper
scraper = NaukriScraper(
    search_url="https://www.naukri.com/software-engineer-jobs",
    rate_limit=5
)

# Scrape jobs with retry logic
jobs = await scraper.scrape_with_retry()

# Normalize each job
normalized_jobs = [scraper.normalize_job(job) for job in jobs]
```

## HTML Structure Parsed

The scraper handles the following Naukri HTML structure:

### Search Results Page
- `<article class="jobTuple">` - Job listing container
- `<a class="title">` - Job title link with URL

### Job Detail Page
- `<h1 class="jd-header-title">` - Job title
- `<a class="comp-name">` or `<div class="comp-name">` - Company name
- `<span class="loc">` or `<a class="loc">` - Location
- `<span class="exp">` - Experience requirement
- `<span class="sal">` or `<div class="salary">` - Salary information
- `<div class="jd-desc">` or `<div class="job-desc">` - Job description
- `<div class="key-skill">` - Skills section with `<a>` tags for each skill
- `<span class="posted">` or `<div class="posted">` - Posted date

## Integration Points

The NaukriScraper integrates seamlessly with existing infrastructure:

1. **BaseScraper**: Inherits rate limiting, retry logic, and error handling
2. **Normalization Helpers**: Uses `normalize_job_type()`, `normalize_experience_level()`, `extract_salary_info()`
3. **Rate Limiter**: Uses default rate limit of 5 requests/minute from `RateLimiter.DEFAULT_LIMITS`
4. **Job Model**: Normalizes to standard `Job` model schema
5. **Scraping Tasks**: Compatible with `create_scraping_task()` and `update_scraping_task()`

## Key Features

1. **Production-Ready**: Comprehensive error handling, logging, and retry logic
2. **Two-Stage Scraping**: Extracts URLs from search results, then fetches individual job pages
3. **Smart Parsing**: Extracts experience level from year ranges and keywords
4. **Flexible Date Parsing**: Handles relative time formats (days, hours, weeks)
5. **Rate Limited**: Respects Naukri rate limits with 5 requests/minute
6. **Skills Extraction**: Parses key skills from job pages
7. **Well Tested**: 18 comprehensive tests with 100% pass rate
8. **Consistent**: Follows same patterns as LinkedInScraper and IndeedScraper
9. **User-Agent Spoofing**: Uses realistic browser User-Agent to avoid blocking
10. **Graceful Degradation**: Continues scraping even if individual jobs fail to parse

## Files Modified

1. `backend/app/services/scraping.py` - Added NaukriScraper class
2. `backend/tests/test_scraping.py` - Added 18 comprehensive tests

## Next Steps

The Naukri scraper is ready for integration with:
- Celery scraping tasks (for scheduled scraping)
- Job deduplication service (already implemented)
- Quality scoring service (already implemented)
- Database persistence (already implemented)

## Notes

- Naukri.com is primarily an Indian job site, so salary currency is set to INR
- The scraper limits to 20 jobs per scrape to respect rate limits and avoid overloading
- HTML structure may change over time - the scraper uses multiple fallback selectors for robustness
- The implementation follows the same patterns as LinkedInScraper and IndeedScraper for consistency
- All normalization helpers are reused from existing infrastructure
- BeautifulSoup4 was already installed in requirements.txt

## Comparison with Other Scrapers

| Feature | LinkedIn (RSS) | Indeed (API) | Naukri (Web) |
|---------|---------------|--------------|--------------|
| Method | RSS Feed | REST API | HTML Scraping |
| Rate Limit | 10/min | 20/min | 5/min |
| Pagination | No | Yes | Limited (20 jobs) |
| Data Quality | Medium | High | Medium |
| Reliability | High | High | Medium |
| Skills Extraction | No | No | Yes |
| Experience Format | Text | Text | Year Range |
| Currency | USD | USD | INR |

## Technical Challenges Solved

1. **HTML Parsing**: Implemented robust parsing with multiple fallback selectors
2. **Experience Level Mapping**: Created intelligent year-to-level mapping
3. **Relative Date Parsing**: Handles multiple relative time formats
4. **Rate Limiting**: Waits for rate limit before each job page fetch
5. **URL Handling**: Converts relative URLs to absolute URLs
6. **Skills Extraction**: Parses skills from HTML and formats as comma-separated string
7. **Error Resilience**: Continues scraping even if individual jobs fail
