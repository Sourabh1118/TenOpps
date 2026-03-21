# Error Handling and Logging - Quick Reference

## Overview
Comprehensive error handling and logging system with structured JSON logging, admin alerting, and Sentry integration.

## Structured Logging

### Basic Usage
```python
from app.core.logging import get_logger

logger = get_logger(__name__)

# Simple logging
logger.info("Operation completed")
logger.warning("Rate limit approaching")
logger.error("Operation failed")
```

### Logging with Context
```python
from app.core.logging import log_error_with_context

try:
    # Some operation
    result = perform_operation()
except Exception as e:
    log_error_with_context(
        logger,
        "Operation failed",
        error=e,
        context={
            'user_id': '123',
            'action': 'create_job',
            'input_data': sanitize_log_data(input_data)
        }
    )
```

### Sanitizing Sensitive Data
```python
from app.core.logging import sanitize_log_data

# Automatically removes passwords, tokens, API keys
data = {
    'username': 'john',
    'password': 'secret123',
    'api_key': 'sk_test_123'
}

safe_data = sanitize_log_data(data)
# Result: {'username': 'john', 'password': '***REDACTED***', 'api_key': '***REDACTED***'}

logger.info("User data", extra={'context': safe_data})
```

## Admin Alerting

### Critical Error Alerts
```python
from app.services.alerting import alerting_service

# Send critical error alert
await alerting_service.send_critical_error_alert(
    error_message="Database connection lost",
    error_type="DatabaseError",
    context={
        'database': 'postgresql',
        'host': 'db.example.com',
        'error_code': 'CONNECTION_FAILED'
    }
)
```

### Scraping Failure Tracking
```python
from app.services.alerting import track_scraping_failures, reset_scraping_failures

# Track failure (automatically sends alert on 3rd consecutive failure)
await track_scraping_failures("linkedin", "Connection timeout")

# Reset on success
await reset_scraping_failures("linkedin")
```

### Circuit Breaker Alerts
```python
from app.services.alerting import alerting_service

# Alert when circuit breaker trips
await alerting_service.send_circuit_breaker_alert(
    service_name="payment_service",
    reason="Too many failures (5 in 60 seconds)"
)
```

## Database Error Logging

Database errors are automatically logged via SQLAlchemy event listener. No code changes needed!

```python
# All database operations are automatically monitored
from app.db.session import get_db

db = next(get_db())
try:
    job = db.query(Job).filter(Job.id == job_id).first()
except Exception as e:
    # Error is automatically logged with:
    # - Query statement (sanitized)
    # - Query parameters (sanitized)
    # - Error type
    # - Connection status
    pass
```

## Sentry Integration

Sentry is automatically configured and captures:
- All unhandled exceptions
- User context (ID, role) from JWT tokens
- Request context (method, URL, path)
- Sanitized request data

### Manual Sentry Reporting
```python
import sentry_sdk

# Add custom context
sentry_sdk.set_context("business_logic", {
    "operation": "job_creation",
    "employer_id": "123",
    "job_count": 5
})

# Capture exception
try:
    risky_operation()
except Exception as e:
    sentry_sdk.capture_exception(e)
```

## Configuration

### Environment Variables

```env
# Logging
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json             # json or text

# Email Alerting
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=alerts@example.com
SMTP_PASSWORD=your-password
ADMIN_EMAIL=admin@example.com
FROM_EMAIL=noreply@jobplatform.com

# Slack Alerting
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Sentry
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

### Enable/Disable Features

```python
# Email alerts enabled if SMTP_HOST and ADMIN_EMAIL are set
# Slack alerts enabled if SLACK_WEBHOOK_URL is set
# Sentry enabled if SENTRY_DSN is set

# Check alerting status
from app.services.alerting import alerting_service

if alerting_service.email_enabled:
    print("Email alerting is enabled")

if alerting_service.slack_enabled:
    print("Slack alerting is enabled")
```

## Log Format

### JSON Format (Production)
```json
{
  "timestamp": "2024-01-15T10:30:45Z",
  "level": "ERROR",
  "app": "Job Aggregation Platform",
  "env": "production",
  "logger": "app.services.scraping",
  "message": "Scraping failed for linkedin",
  "context": {
    "source": "linkedin",
    "error_message": "Connection timeout",
    "retry_count": 3
  },
  "stack_trace": "Traceback (most recent call last):\n  File..."
}
```

### Text Format (Development)
```
2024-01-15 10:30:45 - app.services.scraping - ERROR - Scraping failed for linkedin
```

## Alert Examples

### Email Alert
```
Subject: [CRITICAL] DatabaseError: Database connection lost

Critical Error Alert

Time: 2024-01-15T10:30:45Z
Environment: production
Error Type: DatabaseError
Message: Database connection lost

Context:
  database: postgresql
  host: db.example.com
  error_code: CONNECTION_FAILED

Please investigate immediately.
```

### Slack Alert
```
[CRITICAL] DatabaseError: Database connection lost

Critical Error Alert

Time: 2024-01-15T10:30:45Z
Environment: production
Error Type: DatabaseError
Message: Database connection lost

Context:
  database: postgresql
  host: db.example.com
  error_code: CONNECTION_FAILED

Please investigate immediately.
```

## Best Practices

### 1. Always Use Context
```python
# ❌ Bad
logger.error("Job creation failed")

# ✅ Good
log_error_with_context(
    logger,
    "Job creation failed",
    error=e,
    context={
        'employer_id': employer_id,
        'job_title': job_data.get('title'),
        'validation_errors': errors
    }
)
```

### 2. Sanitize Before Logging
```python
# ❌ Bad - May log passwords
logger.info("User data", extra={'data': user_data})

# ✅ Good - Sanitized
logger.info("User data", extra={'data': sanitize_log_data(user_data)})
```

### 3. Use Appropriate Log Levels
```python
logger.debug("Detailed debugging info")      # Development only
logger.info("Normal operation")               # General info
logger.warning("Something unusual")           # Potential issues
logger.error("Operation failed")              # Errors that need attention
logger.critical("System failure")             # Critical system issues
```

### 4. Track Failures Properly
```python
# In scraping service
try:
    jobs = await scraper.scrape()
    await reset_scraping_failures(source)  # Reset on success
except Exception as e:
    await track_scraping_failures(source, str(e))  # Track failure
    raise
```

### 5. Add Business Context to Sentry
```python
import sentry_sdk

# Add tags for filtering
sentry_sdk.set_tag("feature", "job_posting")
sentry_sdk.set_tag("subscription_tier", "premium")

# Add context for debugging
sentry_sdk.set_context("job_data", {
    "job_id": job_id,
    "employer_id": employer_id,
    "source_type": "direct"
})
```

## Monitoring and Debugging

### View Logs in Production
```bash
# JSON logs can be piped to jq for pretty printing
docker logs backend | jq '.'

# Filter by level
docker logs backend | jq 'select(.level == "ERROR")'

# Filter by logger
docker logs backend | jq 'select(.logger == "app.services.scraping")'

# View last 100 errors
docker logs backend | jq 'select(.level == "ERROR")' | tail -100
```

### Check Alert Status
```python
from app.services.alerting import alerting_service

# Test email alerting
result = await alerting_service.send_critical_error_alert(
    error_message="Test alert",
    error_type="TestError",
    context={}
)
print(f"Email alert sent: {result}")

# Test Slack alerting
result = await alerting_service.send_critical_error_alert(
    error_message="Test alert",
    error_type="TestError",
    context={}
)
print(f"Slack alert sent: {result}")
```

### View Scraping Failure Count
```python
from app.core.redis import redis_client

redis = redis_client.get_cache_client()
failures = redis.get("scraping_failures:linkedin")
print(f"LinkedIn failures: {failures or 0}")
```

## Troubleshooting

### Alerts Not Sending

1. **Check Configuration**
   ```python
   from app.services.alerting import alerting_service
   print(f"Email enabled: {alerting_service.email_enabled}")
   print(f"Slack enabled: {alerting_service.slack_enabled}")
   ```

2. **Check Environment Variables**
   ```bash
   echo $SMTP_HOST
   echo $ADMIN_EMAIL
   echo $SLACK_WEBHOOK_URL
   ```

3. **Test SMTP Connection**
   ```python
   import smtplib
   from app.core.config import settings
   
   with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
       server.starttls()
       server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
       print("SMTP connection successful")
   ```

### Logs Not Appearing

1. **Check Log Level**
   ```env
   LOG_LEVEL=DEBUG  # Set to DEBUG for verbose logging
   ```

2. **Check Log Format**
   ```env
   LOG_FORMAT=text  # Use text format for easier reading in development
   ```

3. **Verify Logger Name**
   ```python
   # Use module name for logger
   logger = get_logger(__name__)  # ✅ Good
   logger = get_logger("mylogger")  # ❌ May not work with filters
   ```

### Sentry Not Capturing Errors

1. **Check DSN**
   ```bash
   echo $SENTRY_DSN
   ```

2. **Verify Initialization**
   ```python
   import sentry_sdk
   print(f"Sentry initialized: {sentry_sdk.Hub.current.client is not None}")
   ```

3. **Test Manually**
   ```python
   import sentry_sdk
   sentry_sdk.capture_message("Test message")
   ```

## Performance Considerations

- **JSON Logging**: Minimal overhead (~1-2ms per log entry)
- **Email Alerts**: Async, non-blocking (~100-500ms)
- **Slack Alerts**: Async, non-blocking (~50-200ms)
- **Sentry**: Async, non-blocking (~10-50ms)
- **Database Error Logging**: Event-based, minimal overhead

## Security

- ✅ Passwords automatically sanitized
- ✅ Tokens automatically sanitized
- ✅ API keys automatically sanitized
- ✅ Database queries sanitized
- ✅ Sentry reports sanitized
- ✅ No PII sent to external services by default

## Support

For issues or questions:
1. Check logs: `docker logs backend | jq 'select(.level == "ERROR")'`
2. Check Sentry dashboard for error trends
3. Review alert emails/Slack messages
4. Check Redis for failure counts: `redis-cli get "scraping_failures:linkedin"`
