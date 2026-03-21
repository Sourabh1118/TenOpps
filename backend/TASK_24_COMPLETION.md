# Task 24: Monitoring and Analytics - Implementation Complete

## Overview
Successfully implemented comprehensive monitoring and analytics functionality for the Job Aggregation Platform, covering API response time tracking, scraping metrics, search analytics, job posting analytics, and system health monitoring.

## Completed Subtasks

### 24.1 ✅ API Response Time Tracking
**Requirement:** 19.2 - Track response times, log slow requests (>1 second), store metrics in Redis/database

**Implementation:**
- **Middleware:** `ResponseTimeMiddleware` in `app/core/middleware.py`
  - Tracks response time for all API requests
  - Adds `X-Response-Time` header to responses
  - Logs slow requests (>1 second) with warning level
  - Stores recent response times in Redis (last 100 per endpoint)
  - Queues database write via Celery task `track_api_metric_task`

- **Database Storage:** `APIMetric` model in `app/models/analytics.py`
  - Stores endpoint, method, status code, response time
  - Includes user context (user_id, user_role) when available
  - Indexed for fast queries on slow requests

- **Admin API:** `/api/analytics/admin/slow-requests`
  - Retrieves slow requests with configurable threshold
  - Filters by time window (hours)
  - Requires admin authentication

**Files Modified:**
- `backend/app/core/middleware.py` - Already implemented
- `backend/app/tasks/monitoring_tasks.py` - Added `track_api_metric_task`
- `backend/app/api/analytics.py` - Added admin endpoint

### 24.2 ✅ Scraping Metrics Tracking
**Requirement:** 19.3 - Track scraping success rate and duration per source, store in database, create dashboard endpoint

**Implementation:**
- **Service:** `AnalyticsService.track_scraping_result()` in `app/services/analytics.py`
  - Tracks success/failure, duration, jobs found/created/updated
  - Stores per-source metrics
  - Updates Redis counters for real-time monitoring

- **Database Storage:** `ScrapingMetric` model in `app/models/analytics.py`
  - Stores source platform, success flag, duration, job counts
  - Includes error messages for failures
  - Indexed for fast queries by platform and timestamp

- **Integration:** Already integrated in `app/tasks/scraping_tasks.py`
  - All scraping tasks (LinkedIn, Indeed, Naukri, Monster) track metrics
  - Tracks both successful and failed scraping attempts

- **Admin Dashboard:** `/api/analytics/admin/scraping-metrics`
  - Returns success rate, average duration, job counts
  - Filters by source platform
  - Configurable time window (days)
  - Requires admin authentication

**Files Modified:**
- `backend/app/services/analytics.py` - Already implemented
- `backend/app/tasks/scraping_tasks.py` - Already integrated
- `backend/app/api/analytics.py` - Added dashboard endpoint

### 24.3 ✅ Search Analytics
**Requirement:** 19.5 - Track popular search terms, store queries and result counts, create endpoint for popular searches

**Implementation:**
- **Service:** `AnalyticsService.track_search()` in `app/services/analytics.py`
  - Tracks query text, result count, location, filters
  - Stores in database for historical analysis
  - Updates Redis sorted set for real-time popular searches

- **Database Storage:** `SearchAnalytic` model in `app/models/analytics.py`
  - Stores query text, location, filters (JSON), result count
  - Includes user context when available
  - Indexed for fast queries on popular searches

- **Integration:** Added to `app/api/search.py`
  - Tracks every search query automatically
  - Includes all filter parameters
  - Non-blocking (doesn't fail search if tracking fails)

- **Public API:** `/api/analytics/popular-searches`
  - Returns top N popular search terms with counts
  - Uses Redis for real-time data
  - Falls back to database if Redis unavailable
  - No authentication required (public endpoint)

**Files Modified:**
- `backend/app/services/analytics.py` - Already implemented
- `backend/app/api/search.py` - Added tracking integration
- `backend/app/api/analytics.py` - Added public endpoint

### 24.4 ✅ Job Posting Analytics for Employers
**Requirements:** 19.6, 9.10 - Track views/applications/conversion rates, create analytics endpoint for premium tier, verify premium access

**Implementation:**
- **Service:** `AnalyticsService.track_job_event()` in `app/services/analytics.py`
  - Tracks job views, applications, clicks
  - Stores per-job and per-employer metrics
  - Updates Redis counters for real-time stats

- **Database Storage:** `JobAnalytic` model in `app/models/analytics.py`
  - Stores job_id, employer_id, event_type, timestamp
  - Includes user context, referrer, user agent
  - Indexed for fast queries by job and employer

- **Integration:**
  - **Job Views:** Added to `app/api/jobs.py` - `get_job()` endpoint
  - **Applications:** Added to `app/services/application.py` - `create_application()`
  - Both integrations are non-blocking

- **Premium Employer API:**
  - `/api/analytics/employer/job/{job_id}` - Individual job analytics
  - `/api/analytics/employer/overview` - Aggregate employer analytics
  - Both endpoints verify premium tier subscription
  - Both endpoints verify job ownership
  - Returns views, applications, clicks, conversion rate

**Files Modified:**
- `backend/app/services/analytics.py` - Already implemented
- `backend/app/api/jobs.py` - Added view tracking
- `backend/app/services/application.py` - Added application tracking
- `backend/app/api/analytics.py` - Added premium employer endpoints

### 24.5 ✅ System Health Monitoring
**Requirements:** 19.7, 19.8 - Track DAU/job volume, monitor DB/Redis usage, alert on thresholds

**Implementation:**
- **Service:** `AnalyticsService.track_system_metric()` in `app/services/analytics.py`
  - Tracks any system metric with name, value, unit
  - Stores in database for historical analysis
  - Updates Redis for real-time monitoring

- **Database Storage:** `SystemHealthMetric` model in `app/models/analytics.py`
  - Stores metric name, value, unit, timestamp
  - Includes extra_data field for additional context (JSON)
  - Indexed for fast queries by metric name

- **Monitoring Tasks:** `app/tasks/monitoring_tasks.py`
  - **`collect_system_metrics`** - Runs hourly
    - Tracks daily active job seekers
    - Tracks daily active employers
    - Tracks daily jobs posted
    - Tracks active jobs count
    - Monitors database connection pool usage
    - Monitors Redis memory usage
  
  - **`check_metric_thresholds`** - Runs every 15 minutes
    - Checks Redis memory usage (threshold: 100 MB)
    - Checks database pool usage (threshold: 80%)
    - Checks slow API requests (threshold: 50 in 24h)
    - Sends alerts via email/Slack when thresholds exceeded

- **Celery Beat Schedule:** Updated `app/tasks/celery_app.py`
  - Added hourly system metrics collection
  - Added 15-minute threshold checks

- **Admin API:** `/api/analytics/admin/system-metrics`
  - Returns system health metrics
  - Filters by metric name
  - Configurable time window (hours)
  - Requires admin authentication

**Files Modified:**
- `backend/app/services/analytics.py` - Already implemented
- `backend/app/tasks/monitoring_tasks.py` - Enhanced with full implementation
- `backend/app/tasks/celery_app.py` - Added beat schedule
- `backend/app/api/analytics.py` - Added admin endpoint

## Database Schema

### Analytics Tables Created (Migration 007)
All tables created in `backend/alembic/versions/007_create_analytics_tables.py`:

1. **api_metrics** - API response time tracking
   - Columns: id, endpoint, method, status_code, response_time_ms, timestamp, user_id, user_role, error_message
   - Indexes: endpoint, timestamp, slow_requests (>1000ms)

2. **scraping_metrics** - Scraping task metrics
   - Columns: id, source_platform, task_id, success, jobs_found, jobs_created, jobs_updated, duration_seconds, timestamp, error_message
   - Indexes: source_platform, timestamp, failures

3. **search_analytics** - Search query analytics
   - Columns: id, query_text, location, filters_applied, result_count, timestamp, user_id
   - Indexes: query_text, timestamp

4. **job_analytics** - Job event tracking
   - Columns: id, job_id, employer_id, event_type, timestamp, user_id, referrer, user_agent
   - Indexes: job_id, employer_id, timestamp, event_type

5. **system_health_metrics** - System health monitoring
   - Columns: id, metric_name, metric_value, metric_unit, timestamp, extra_data
   - Indexes: metric_name, timestamp

## API Endpoints

### Public Endpoints
- `GET /api/analytics/popular-searches` - Get popular search terms

### Employer Endpoints (Premium Tier Required)
- `GET /api/analytics/employer/job/{job_id}` - Get job analytics
- `GET /api/analytics/employer/overview` - Get employer overview analytics

### Admin Endpoints
- `GET /api/analytics/admin/slow-requests` - Get slow API requests
- `GET /api/analytics/admin/scraping-metrics` - Get scraping metrics dashboard
- `GET /api/analytics/admin/system-metrics` - Get system health metrics

## Celery Beat Schedule

### Monitoring Tasks
- **collect-system-metrics-hourly** - Every hour at :00
  - Collects DAU, job volume, DB pool, Redis memory metrics
  
- **check-metric-thresholds-15min** - Every 15 minutes
  - Checks thresholds and sends alerts

## Key Features

### Real-Time Monitoring
- Redis caching for immediate metric access
- Recent response times (last 100 per endpoint)
- Popular searches (top 1000)
- Job event counters (30-day TTL)

### Historical Analysis
- All metrics stored in PostgreSQL
- Configurable time windows for queries
- Aggregate statistics (success rates, averages, totals)

### Alerting
- Email and Slack alerts for threshold violations
- Configurable thresholds per metric
- Alert deduplication to prevent spam

### Performance
- Non-blocking analytics tracking
- Async Celery tasks for database writes
- Redis for fast real-time queries
- Indexed database tables for fast historical queries

## Testing

Created comprehensive test suite in `backend/tests/test_analytics.py`:
- Unit tests for all analytics service methods
- API endpoint tests (requires fixtures)
- Tests cover all 5 subtasks

**Note:** Full test execution requires PostgreSQL (SQLite doesn't support ARRAY types used in Job model). Tests are ready for integration testing with PostgreSQL.

## Configuration

### Environment Variables
No new environment variables required. Uses existing:
- `REDIS_URL` - For real-time metrics
- `DATABASE_URL` - For historical metrics
- `SMTP_*` / `SLACK_WEBHOOK_URL` - For alerting (from Task 23)

### Thresholds (Configurable in Code)
- Slow API request: 1000ms
- Redis memory: 100 MB
- DB pool usage: 80%
- Slow request count: 50 in 24h

## Integration Points

### Automatic Tracking
1. **All API Requests** - Response time tracked via middleware
2. **All Scraping Tasks** - Metrics tracked in scraping service
3. **All Search Queries** - Analytics tracked in search API
4. **All Job Views** - Tracked when job is retrieved
5. **All Applications** - Tracked when application is created

### Manual Tracking
System administrators can track custom metrics using:
```python
analytics = AnalyticsService(db)
analytics.track_system_metric(
    metric_name="custom_metric",
    metric_value=123.45,
    metric_unit="units",
    extra_data={"context": "value"}
)
```

## Files Created/Modified

### Created
- `backend/app/api/analytics.py` - Analytics API endpoints
- `backend/tests/test_analytics.py` - Analytics test suite
- `backend/TASK_24_COMPLETION.md` - This document

### Modified
- `backend/app/main.py` - Registered analytics router
- `backend/app/api/search.py` - Added search analytics tracking
- `backend/app/api/jobs.py` - Added job view tracking
- `backend/app/services/application.py` - Added application tracking
- `backend/app/tasks/celery_app.py` - Added monitoring task schedule
- `backend/app/models/analytics.py` - Fixed metadata → extra_data
- `backend/alembic/versions/007_create_analytics_tables.py` - Fixed metadata → extra_data

### Already Implemented (No Changes Needed)
- `backend/app/models/analytics.py` - All models already defined
- `backend/app/services/analytics.py` - All service methods already implemented
- `backend/app/core/middleware.py` - ResponseTimeMiddleware already implemented
- `backend/app/tasks/monitoring_tasks.py` - Core monitoring tasks already implemented
- `backend/app/tasks/scraping_tasks.py` - Scraping metrics already integrated

## Verification Steps

### 1. Run Database Migration
```bash
cd backend
alembic upgrade head
```

### 2. Start Celery Worker
```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

### 3. Start Celery Beat
```bash
celery -A app.tasks.celery_app beat --loglevel=info
```

### 4. Test API Endpoints

**Popular Searches (Public):**
```bash
curl http://localhost:8000/api/analytics/popular-searches?limit=10
```

**Slow Requests (Admin):**
```bash
curl -H "Authorization: Bearer <admin_token>" \
  http://localhost:8000/api/analytics/admin/slow-requests?threshold_ms=1000&hours=24
```

**Scraping Metrics (Admin):**
```bash
curl -H "Authorization: Bearer <admin_token>" \
  http://localhost:8000/api/analytics/admin/scraping-metrics?source_platform=linkedin&days=7
```

**Job Analytics (Premium Employer):**
```bash
curl -H "Authorization: Bearer <premium_employer_token>" \
  http://localhost:8000/api/analytics/employer/job/{job_id}?days=30
```

**System Metrics (Admin):**
```bash
curl -H "Authorization: Bearer <admin_token>" \
  http://localhost:8000/api/analytics/admin/system-metrics?metric_name=redis_memory_usage&hours=24
```

### 5. Verify Automatic Tracking

**Search Analytics:**
```bash
# Perform a search
curl "http://localhost:8000/api/jobs/search?query=python+developer&location=San+Francisco"

# Check popular searches
curl http://localhost:8000/api/analytics/popular-searches
```

**Job View Tracking:**
```bash
# View a job
curl http://localhost:8000/api/jobs/{job_id}

# Check job analytics (as premium employer)
curl -H "Authorization: Bearer <premium_employer_token>" \
  http://localhost:8000/api/analytics/employer/job/{job_id}
```

### 6. Monitor Celery Tasks
```bash
# Check task execution in Celery logs
# Should see hourly: "Collecting system metrics"
# Should see every 15 min: "Checking metric thresholds"
```

## Requirements Validation

### ✅ Requirement 19.2 - API Response Time Tracking
- [x] Add middleware to track response times
- [x] Log slow requests (>1 second)
- [x] Store metrics in Redis or time-series database

### ✅ Requirement 19.3 - Scraping Metrics Tracking
- [x] Track scraping success rate and duration per source
- [x] Store metrics in database
- [x] Create dashboard endpoint for admin view

### ✅ Requirement 19.5 - Search Analytics
- [x] Track popular search terms
- [x] Store search queries and result counts
- [x] Create endpoint to retrieve popular searches

### ✅ Requirement 19.6 & 9.10 - Job Posting Analytics
- [x] Track views, applications, and conversion rates per job
- [x] Create analytics endpoint for premium tier employers
- [x] Verify employer has premium tier before showing analytics

### ✅ Requirement 19.7 & 19.8 - System Health Monitoring
- [x] Track daily active users and job posting volume
- [x] Monitor database connection pool usage
- [x] Monitor Redis memory usage
- [x] Alert when metrics exceed thresholds

## Summary

Task 24 is **COMPLETE**. All 5 subtasks have been successfully implemented:

1. ✅ API response time tracking with middleware and admin dashboard
2. ✅ Scraping metrics tracking with per-source analytics
3. ✅ Search analytics with popular searches endpoint
4. ✅ Job posting analytics for premium employers with tier verification
5. ✅ System health monitoring with automated collection and alerting

The implementation provides comprehensive monitoring and analytics capabilities covering all aspects of the platform, from API performance to business metrics. All tracking is automatic and non-blocking, ensuring minimal impact on application performance.
