# Task 39.3: Monitoring and Alerting Setup Guide

## Overview

This document provides a comprehensive guide for setting up monitoring and alerting for the Job Aggregation Platform in production. It covers Sentry configuration, uptime monitoring, scraping failure alerts, and error rate monitoring.

## Setup Date

March 21, 2026

---

## 1. Sentry Error Monitoring

### 1.1 Sentry Project Setup

**Status**: ✅ CONFIGURED

Sentry is already integrated in the codebase. Follow these steps to configure for production:

#### Backend Sentry Configuration

**File**: `backend/app/main.py`

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENVIRONMENT,  # "production"
    traces_sample_rate=0.1,  # 10% of transactions
    profiles_sample_rate=0.1,  # 10% of profiles
    integrations=[
        FastApiIntegration(),
        SqlalchemyIntegration(),
        RedisIntegration(),
    ],
    before_send=sanitize_sentry_event,  # Remove sensitive data
)
```

#### Frontend Sentry Configuration

**File**: `frontend/app/providers.tsx`

```typescript
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NEXT_PUBLIC_ENVIRONMENT,
  tracesSampleRate: 0.1,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
});
```

---

### 1.2 Sentry Alert Configuration

#### Critical Error Alerts

Configure alerts in Sentry dashboard for:

1. **High Error Rate Alert**
   - Condition: Error rate > 10 errors/minute
   - Action: Email + Slack notification
   - Priority: Critical

2. **New Error Type Alert**
   - Condition: New error fingerprint detected
   - Action: Email notification
   - Priority: High

3. **Database Connection Errors**
   - Condition: Error contains "database" or "connection"
   - Action: Email + Slack + PagerDuty
   - Priority: Critical

4. **Authentication Failures Spike**
   - Condition: Auth errors > 50/minute
   - Action: Email + Slack
   - Priority: High

#### Sentry Alert Rules (JSON Configuration)

```json
{
  "alerts": [
    {
      "name": "High Error Rate",
      "conditions": [
        {
          "id": "sentry.rules.conditions.event_frequency.EventFrequencyCondition",
          "value": 10,
          "interval": "1m"
        }
      ],
      "actions": [
        {
          "id": "sentry.mail.actions.NotifyEmailAction",
          "targetType": "Team",
          "targetIdentifier": "engineering"
        },
        {
          "id": "sentry.integrations.slack.notify_action.SlackNotifyServiceAction",
          "workspace": "your-workspace",
          "channel": "#alerts-critical"
        }
      ]
    },
    {
      "name": "Database Connection Errors",
      "conditions": [
        {
          "id": "sentry.rules.conditions.tagged_event.TaggedEventCondition",
          "key": "error.type",
          "match": "co",
          "value": "database"
        }
      ],
      "actions": [
        {
          "id": "sentry.mail.actions.NotifyEmailAction",
          "targetType": "Team",
          "targetIdentifier": "engineering"
        }
      ]
    }
  ]
}
```

---

### 1.3 Sentry Environment Variables

Add to production environment:

```bash
# Backend (.env.production)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# Frontend (.env.production)
NEXT_PUBLIC_SENTRY_DSN=https://your-frontend-sentry-dsn@sentry.io/project-id
NEXT_PUBLIC_ENVIRONMENT=production
```

---

## 2. Uptime Monitoring

### 2.1 UptimeRobot Setup

**Service**: UptimeRobot (Free tier: 50 monitors, 5-minute intervals)

#### Monitors to Create

1. **Backend API Health Check**
   - URL: `https://api.yourplatform.com/health`
   - Type: HTTP(s)
   - Interval: 5 minutes
   - Alert: Email + SMS when down

2. **Frontend Homepage**
   - URL: `https://yourplatform.com`
   - Type: HTTP(s)
   - Interval: 5 minutes
   - Alert: Email when down

3. **Database Connectivity**
   - URL: `https://api.yourplatform.com/health/db`
   - Type: HTTP(s)
   - Interval: 5 minutes
   - Alert: Email + SMS when down

4. **Redis Connectivity**
   - URL: `https://api.yourplatform.com/health/redis`
   - Type: HTTP(s)
   - Interval: 5 minutes
   - Alert: Email when down

5. **Celery Workers**
   - URL: `https://api.yourplatform.com/health/celery`
   - Type: HTTP(s)
   - Interval: 10 minutes
   - Alert: Email when down

#### UptimeRobot Configuration Steps

1. Sign up at https://uptimerobot.com
2. Create new monitor for each endpoint
3. Configure alert contacts (email, SMS, Slack)
4. Set up status page (optional, public)

#### Health Check Endpoints

**File**: `backend/app/api/health.py`

```python
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.db.session import SessionLocal
from app.core.redis import redis_client
from app.tasks.celery_app import celery_app

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@router.get("/health/db")
async def database_health():
    """Check database connectivity"""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "healthy", "service": "database"}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database unhealthy")

@router.get("/health/redis")
async def redis_health():
    """Check Redis connectivity"""
    try:
        redis_client.ping()
        return {"status": "healthy", "service": "redis"}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Redis unhealthy")

@router.get("/health/celery")
async def celery_health():
    """Check Celery workers"""
    try:
        stats = celery_app.control.inspect().stats()
        if not stats:
            raise Exception("No workers available")
        return {"status": "healthy", "service": "celery", "workers": len(stats)}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Celery unhealthy")
```

---

### 2.2 Alternative: Better Uptime

**Service**: Better Uptime (More features, paid)

If you prefer Better Uptime:
- 30-second check intervals
- Incident management
- Status pages
- On-call scheduling

Configuration similar to UptimeRobot.

---

## 3. Scraping Failure Alerts

### 3.1 Scraping Monitoring Service

**File**: `backend/app/services/alerting.py`

Already implemented. Configuration:

```python
class AlertingService:
    def __init__(self):
        self.failure_counts = {}  # Track consecutive failures
        self.alert_threshold = 3  # Alert after 3 failures
        
    async def check_scraping_failures(self, source: str, task_status: str):
        """Monitor scraping task failures"""
        if task_status == "FAILED":
            self.failure_counts[source] = self.failure_counts.get(source, 0) + 1
            
            if self.failure_counts[source] >= self.alert_threshold:
                await self.send_alert(
                    level="critical",
                    title=f"Scraping Failures: {source}",
                    message=f"{source} has failed {self.failure_counts[source]} times consecutively",
                    tags=["scraping", source]
                )
        else:
            # Reset counter on success
            self.failure_counts[source] = 0
```

---

### 3.2 Scraping Alert Configuration

#### Email Alerts

**File**: `backend/app/core/config.py`

```python
# Alert email configuration
ALERT_EMAIL_FROM = "alerts@yourplatform.com"
ALERT_EMAIL_TO = ["admin@yourplatform.com", "devops@yourplatform.com"]
SMTP_HOST = "smtp.sendgrid.net"
SMTP_PORT = 587
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
```

#### Slack Alerts

**File**: `backend/app/services/alerting.py`

```python
import httpx

async def send_slack_alert(message: str, channel: str = "#alerts-scraping"):
    """Send alert to Slack"""
    webhook_url = settings.SLACK_WEBHOOK_URL
    
    payload = {
        "channel": channel,
        "username": "Scraping Monitor",
        "icon_emoji": ":warning:",
        "text": message,
        "attachments": [{
            "color": "danger",
            "fields": [
                {"title": "Environment", "value": settings.ENVIRONMENT, "short": True},
                {"title": "Timestamp", "value": datetime.utcnow().isoformat(), "short": True}
            ]
        }]
    }
    
    async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json=payload)
```

#### Environment Variables

```bash
# Slack webhook for alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Email alerts
SMTP_USER=your-smtp-user
SMTP_PASSWORD=your-smtp-password
ALERT_EMAIL_TO=admin@yourplatform.com,devops@yourplatform.com
```

---

### 3.3 Scraping Dashboard

**File**: `backend/app/api/admin.py`

```python
@router.get("/admin/scraping/status")
async def get_scraping_status(current_user: User = Depends(require_admin)):
    """Get scraping status for all sources"""
    db = SessionLocal()
    
    # Get recent scraping tasks
    recent_tasks = db.query(ScrapingTask)\
        .filter(ScrapingTask.created_at >= datetime.utcnow() - timedelta(hours=24))\
        .order_by(ScrapingTask.created_at.desc())\
        .all()
    
    # Calculate success rates per source
    status_by_source = {}
    for task in recent_tasks:
        source = task.source_platform
        if source not in status_by_source:
            status_by_source[source] = {"total": 0, "success": 0, "failed": 0}
        
        status_by_source[source]["total"] += 1
        if task.status == "COMPLETED":
            status_by_source[source]["success"] += 1
        elif task.status == "FAILED":
            status_by_source[source]["failed"] += 1
    
    return {
        "sources": status_by_source,
        "last_24_hours": len(recent_tasks)
    }
```

---

## 4. High Error Rate Monitoring

### 4.1 Error Rate Tracking

**File**: `backend/app/core/middleware.py`

```python
from collections import defaultdict
from datetime import datetime, timedelta

class ErrorRateMonitor:
    def __init__(self):
        self.error_counts = defaultdict(list)
        self.alert_threshold = 50  # errors per minute
        
    def record_error(self, error_type: str):
        """Record an error occurrence"""
        now = datetime.utcnow()
        self.error_counts[error_type].append(now)
        
        # Clean old entries (older than 1 minute)
        cutoff = now - timedelta(minutes=1)
        self.error_counts[error_type] = [
            ts for ts in self.error_counts[error_type] if ts > cutoff
        ]
        
        # Check if threshold exceeded
        if len(self.error_counts[error_type]) > self.alert_threshold:
            self.send_high_error_rate_alert(error_type)
    
    async def send_high_error_rate_alert(self, error_type: str):
        """Send alert for high error rate"""
        count = len(self.error_counts[error_type])
        
        await alerting_service.send_alert(
            level="critical",
            title="High Error Rate Detected",
            message=f"{error_type} errors: {count} in the last minute",
            tags=["error-rate", error_type]
        )
```

---

### 4.2 Error Rate Dashboard

Create a monitoring dashboard endpoint:

**File**: `backend/app/api/admin.py`

```python
@router.get("/admin/metrics/errors")
async def get_error_metrics(
    hours: int = 24,
    current_user: User = Depends(require_admin)
):
    """Get error metrics for the specified time period"""
    
    # Query error logs from database or Sentry API
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # This would integrate with your logging system
    error_stats = {
        "total_errors": 0,
        "errors_by_type": {},
        "errors_by_hour": [],
        "top_errors": []
    }
    
    return error_stats
```

---

## 5. Performance Monitoring

### 5.1 Response Time Monitoring

**File**: `backend/app/core/middleware.py`

```python
from prometheus_client import Histogram, Counter

# Metrics
request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'status']
)

request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    # Record metrics
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).observe(duration)
    
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    # Alert on slow requests
    if duration > 5.0:  # 5 seconds
        logger.warning(f"Slow request: {request.url.path} took {duration:.2f}s")
    
    return response
```

---

### 5.2 Database Query Monitoring

**File**: `backend/app/db/session.py`

```python
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    
    # Alert on slow queries
    if total > 1.0:  # 1 second
        logger.warning(f"Slow query ({total:.2f}s): {statement[:100]}")
```

---

## 6. Alert Channels Configuration

### 6.1 Email Alerts

**Setup**: Configure SMTP in environment variables

```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
ALERT_EMAIL_FROM=alerts@yourplatform.com
ALERT_EMAIL_TO=admin@yourplatform.com,devops@yourplatform.com
```

---

### 6.2 Slack Alerts

**Setup**: Create Slack webhook

1. Go to https://api.slack.com/apps
2. Create new app
3. Enable Incoming Webhooks
4. Create webhook for #alerts channel
5. Add webhook URL to environment:

```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_ALERTS_CHANNEL=#alerts
SLACK_CRITICAL_CHANNEL=#alerts-critical
```

---

### 6.3 PagerDuty (Optional)

For critical alerts that require immediate response:

```bash
PAGERDUTY_API_KEY=your-pagerduty-api-key
PAGERDUTY_SERVICE_ID=your-service-id
```

**File**: `backend/app/services/alerting.py`

```python
async def send_pagerduty_alert(title: str, description: str, severity: str = "critical"):
    """Send alert to PagerDuty"""
    url = "https://api.pagerduty.com/incidents"
    
    headers = {
        "Authorization": f"Token token={settings.PAGERDUTY_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.pagerduty+json;version=2"
    }
    
    payload = {
        "incident": {
            "type": "incident",
            "title": title,
            "service": {
                "id": settings.PAGERDUTY_SERVICE_ID,
                "type": "service_reference"
            },
            "urgency": severity,
            "body": {
                "type": "incident_body",
                "details": description
            }
        }
    }
    
    async with httpx.AsyncClient() as client:
        await client.post(url, headers=headers, json=payload)
```

---

## 7. Monitoring Checklist

### Pre-Launch Checklist

- [ ] Sentry DSN configured for backend
- [ ] Sentry DSN configured for frontend
- [ ] Sentry alerts configured (high error rate, new errors, database errors)
- [ ] UptimeRobot monitors created (API, frontend, database, Redis, Celery)
- [ ] Health check endpoints tested
- [ ] Scraping failure alerts configured
- [ ] Email alerts configured (SMTP settings)
- [ ] Slack webhook configured
- [ ] Alert thresholds tuned appropriately
- [ ] Test alerts sent and received
- [ ] Monitoring dashboard accessible
- [ ] On-call rotation defined (if using PagerDuty)

---

## 8. Testing Monitoring Setup

### 8.1 Test Sentry Integration

```bash
# Backend - trigger test error
curl -X POST http://localhost:8000/api/test/sentry-error

# Frontend - trigger test error
# Visit: http://localhost:3000/test-error
```

---

### 8.2 Test Health Checks

```bash
# Test all health endpoints
curl https://api.yourplatform.com/health
curl https://api.yourplatform.com/health/db
curl https://api.yourplatform.com/health/redis
curl https://api.yourplatform.com/health/celery
```

---

### 8.3 Test Alert Delivery

```python
# Test email alert
from app.services.alerting import alerting_service

await alerting_service.send_alert(
    level="info",
    title="Test Alert",
    message="This is a test alert to verify email delivery",
    tags=["test"]
)

# Test Slack alert
await alerting_service.send_slack_alert(
    "Test alert from monitoring system",
    channel="#alerts"
)
```

---

## 9. Monitoring Dashboard

### 9.1 Admin Dashboard

Access monitoring dashboard at:
- URL: `https://yourplatform.com/admin/monitoring`
- Authentication: Admin role required

**Features**:
- Real-time error rate
- Scraping status by source
- API response times
- Database query performance
- Celery task queue status
- Recent alerts

---

### 9.2 External Dashboards

- **Sentry**: https://sentry.io/organizations/your-org/issues/
- **UptimeRobot**: https://uptimerobot.com/dashboard
- **Vercel Analytics**: https://vercel.com/your-project/analytics

---

## 10. Alert Response Procedures

### 10.1 High Error Rate Alert

**Response Steps**:
1. Check Sentry for error details
2. Identify affected endpoints
3. Check recent deployments
4. Review error logs
5. Rollback if necessary
6. Fix and redeploy

---

### 10.2 Scraping Failure Alert

**Response Steps**:
1. Check scraping dashboard
2. Identify failing source
3. Check external source availability
4. Review rate limits
5. Check robots.txt compliance
6. Restart scraping task if needed

---

### 10.3 Database Connection Alert

**Response Steps**:
1. Check database health endpoint
2. Verify database service is running
3. Check connection pool status
4. Review database logs
5. Restart database if necessary
6. Scale up if resource constrained

---

### 10.4 Service Down Alert

**Response Steps**:
1. Check service health endpoints
2. Review deployment logs
3. Check resource usage (CPU, memory)
4. Restart service if needed
5. Scale up if necessary
6. Investigate root cause

---

## 11. Monitoring Best Practices

### 11.1 Alert Fatigue Prevention

- Set appropriate thresholds (not too sensitive)
- Use alert aggregation (don't spam)
- Implement alert cooldown periods
- Prioritize alerts (critical vs warning)
- Regular alert review and tuning

---

### 11.2 Incident Response

- Document all incidents
- Conduct post-mortems
- Update runbooks
- Improve monitoring based on incidents
- Share learnings with team

---

### 11.3 Regular Maintenance

- Weekly: Review alert thresholds
- Monthly: Analyze error trends
- Quarterly: Update monitoring strategy
- Annually: Comprehensive monitoring audit

---

## 12. Monitoring Setup Summary

### ✅ Completed

- [x] Sentry integration (backend and frontend)
- [x] Health check endpoints
- [x] Scraping failure monitoring
- [x] Error rate tracking
- [x] Alerting service implementation
- [x] Logging infrastructure

### ⚠️ To Configure (Production)

- [ ] Set Sentry DSN in production environment
- [ ] Create UptimeRobot monitors
- [ ] Configure Slack webhook
- [ ] Set up email alerts (SMTP)
- [ ] Configure Sentry alert rules
- [ ] Test all alert channels
- [ ] Document on-call procedures

---

## 13. Quick Start Guide

### Step 1: Configure Sentry

```bash
# Set environment variables
export SENTRY_DSN="https://your-dsn@sentry.io/project"
export NEXT_PUBLIC_SENTRY_DSN="https://your-frontend-dsn@sentry.io/project"
```

### Step 2: Set Up UptimeRobot

1. Sign up at uptimerobot.com
2. Add monitors for all health endpoints
3. Configure alert contacts

### Step 3: Configure Slack

```bash
# Set Slack webhook
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK"
```

### Step 4: Test Alerts

```bash
# Test Sentry
python backend/scripts/test_sentry.py

# Test health checks
./backend/scripts/test_health_checks.sh

# Test alerts
python backend/scripts/test_alerts.py
```

### Step 5: Monitor

- Check Sentry dashboard daily
- Review UptimeRobot status
- Monitor Slack alerts channel
- Review weekly metrics

---

## Conclusion

Monitoring and alerting infrastructure is **ready for production** with the following components:

✅ **Error Tracking**: Sentry configured  
✅ **Uptime Monitoring**: Health endpoints ready  
✅ **Scraping Alerts**: Failure detection implemented  
✅ **Error Rate Monitoring**: Thresholds configured  
✅ **Alert Channels**: Email and Slack ready  

**Action Required**: Configure production environment variables and create external monitoring accounts (Sentry, UptimeRobot).
