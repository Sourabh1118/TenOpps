# Task 36.4: Deploy Celery Workers

**Requirement**: 16.7 - Celery workers with Beat scheduler for background tasks

## Overview

Deploy Celery workers and Beat scheduler for:
- Scheduled job scraping (LinkedIn, Indeed, Naukri, Monster)
- URL import processing
- Job expiration tasks
- Subscription management
- Email notifications

## Prerequisites

- [ ] Backend deployed (Task 36.3)
- [ ] Redis deployed (Task 36.2)
- [ ] PostgreSQL deployed (Task 36.1)
- [ ] Same Railway/Render account

---

## Option A: Railway

### Step 1: Add Celery Worker Service

1. **In Railway Project**:
   - Click "New"
   - Select "GitHub Repo"
   - Choose same repository
   - Name: `celery-worker`

2. **Configure Build**:
   - Go to **Settings** → **Build**
   - Set:
     - **Builder**: Dockerfile
     - **Dockerfile Path**: `backend/Dockerfile`
     - **Root Directory**: `backend`

3. **Configure Start Command**:
   - Go to **Settings** → **Deploy**
   - Set **Custom Start Command**:
     ```bash
     celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2
     ```
   - **Note**: Use `--concurrency=2` for free tier (limited CPU)

### Step 2: Configure Environment Variables

1. **Reference Backend Variables**:
   - Go to **Variables** tab
   - Click "Reference Variables"
   - Select backend service
   - This copies all environment variables

2. **Verify Required Variables**:
   ```bash
   DATABASE_URL=...
   REDIS_URL=${{Redis.REDIS_URL}}
   CELERY_BROKER_URL=${{Redis.REDIS_URL}}
   CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}
   SECRET_KEY=...
   JWT_SECRET_KEY=...
   INDEED_API_KEY=...
   LINKEDIN_RSS_URLS=...
   SCRAPING_USER_AGENT=...
   SENTRY_DSN=...
   ```

### Step 3: Deploy Worker

1. **Deploy**:
   - Railway automatically deploys
   - Monitor logs for:
     ```
     [INFO/MainProcess] Connected to redis://...
     [INFO/MainProcess] celery@hostname ready.
     ```

2. **Verify Worker is Running**:
   - Check logs for "ready" message
   - No error messages about Redis/DB connections

### Step 4: Add Celery Beat Service

1. **Create Beat Service**:
   - Click "New" → "GitHub Repo"
   - Choose same repository
   - Name: `celery-beat`

2. **Configure Build**:
   - Same as worker (Dockerfile, root directory)

3. **Configure Start Command**:
   ```bash
   celery -A app.tasks.celery_app beat --loglevel=info
   ```

4. **Reference Variables**:
   - Copy variables from backend service

5. **Deploy**:
   - Monitor logs for:
     ```
     [INFO/Beat] Scheduler: Sending due task...
     [INFO/Beat] beat: Starting...
     ```

### Step 5: Test Celery Tasks

1. **Trigger Test Task**:
   
   From backend shell or API:
   ```python
   from app.tasks.scraping_tasks import scrape_jobs_task
   
   # Queue a test task
   result = scrape_jobs_task.delay('linkedin')
   print(f"Task ID: {result.id}")
   
   # Check result
   print(f"Status: {result.status}")
   print(f"Result: {result.result}")
   ```

2. **Check Worker Logs**:
   - Go to celery-worker service
   - Check logs for task execution:
     ```
     [INFO/ForkPoolWorker-1] Task app.tasks.scraping_tasks.scrape_jobs_task[...] received
     [INFO/ForkPoolWorker-1] Task app.tasks.scraping_tasks.scrape_jobs_task[...] succeeded
     ```

3. **Verify Scheduled Tasks**:
   - Wait for Beat to trigger scheduled tasks
   - Check Beat logs for:
     ```
     [INFO/Beat] Scheduler: Sending due task scrape_all_sources
     ```

---

## Option B: Render

### Step 1: Create Celery Worker

1. **Create Background Worker**:
   - Go to Render dashboard
   - Click "New" → "Background Worker"
   - Connect repository

2. **Configure**:
   - **Name**: `celery-worker`
   - **Region**: Same as backend
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: Docker
   - **Plan**: Free

3. **Set Docker Command**:
   ```bash
   celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2
   ```

4. **Add Environment Variables**:
   - Copy all variables from backend service
   - Or use "Sync Environment Variables"

5. **Deploy**:
   - Click "Create Background Worker"
   - Monitor logs

### Step 2: Create Celery Beat

1. **Create Another Background Worker**:
   - Name: `celery-beat`
   - Same configuration as worker

2. **Set Docker Command**:
   ```bash
   celery -A app.tasks.celery_app beat --loglevel=info
   ```

3. **Deploy**:
   - Monitor logs for scheduler startup

---

## Celery Configuration

### Scheduled Tasks

Your `backend/app/tasks/celery_app.py` should define:

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    'scrape-linkedin-every-hour': {
        'task': 'app.tasks.scraping_tasks.scrape_jobs_task',
        'schedule': crontab(minute=0),  # Every hour
        'args': ('linkedin',)
    },
    'scrape-indeed-every-2-hours': {
        'task': 'app.tasks.scraping_tasks.scrape_jobs_task',
        'schedule': crontab(minute=0, hour='*/2'),  # Every 2 hours
        'args': ('indeed',)
    },
    'expire-old-jobs-daily': {
        'task': 'app.tasks.maintenance_tasks.expire_old_jobs',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'reset-monthly-quotas': {
        'task': 'app.tasks.subscription_tasks.reset_monthly_quotas',
        'schedule': crontab(day_of_month=1, hour=0, minute=0),  # 1st of month
    },
}
```

### Worker Configuration

```python
# Concurrency
CELERY_WORKER_CONCURRENCY=2  # Free tier

# Task settings
CELERY_TASK_ACKS_LATE=True
CELERY_TASK_REJECT_ON_WORKER_LOST=True
CELERY_TASK_TIME_LIMIT=300  # 5 minutes
CELERY_TASK_SOFT_TIME_LIMIT=240  # 4 minutes

# Result backend
CELERY_RESULT_EXPIRES=3600  # 1 hour

# Retry settings
CELERY_TASK_MAX_RETRIES=3
CELERY_TASK_DEFAULT_RETRY_DELAY=300  # 5 minutes
```

## Testing Checklist

- [ ] Worker service running
- [ ] Beat service running
- [ ] Worker connected to Redis
- [ ] Worker connected to PostgreSQL
- [ ] Can queue tasks manually
- [ ] Tasks execute successfully
- [ ] Beat triggers scheduled tasks
- [ ] Task results stored in Redis
- [ ] No connection errors in logs

## Monitoring Celery

### 1. Check Worker Status

```bash
# From backend shell
from app.tasks.celery_app import celery_app

# Inspect active workers
inspect = celery_app.control.inspect()
print(inspect.active())
print(inspect.registered())
print(inspect.stats())
```

### 2. Monitor Task Queue

```python
# Check queue length
from app.core.redis import get_redis_client

redis_client = get_redis_client()
queue_length = redis_client.llen('celery')
print(f"Tasks in queue: {queue_length}")
```

### 3. View Task History

```python
# Get task result
from celery.result import AsyncResult

result = AsyncResult(task_id)
print(f"Status: {result.status}")
print(f"Result: {result.result}")
print(f"Traceback: {result.traceback}")
```

### 4. Celery Flower (Optional)

For visual monitoring, deploy Flower:

1. **Add Flower Service** (Railway):
   - Create new service from same repo
   - Start command:
     ```bash
     celery -A app.tasks.celery_app flower --port=$PORT
     ```
   - Enable public networking
   - Access at: `https://flower-service.up.railway.app`

2. **Flower Dashboard**:
   - View active workers
   - Monitor task execution
   - See task history
   - Real-time graphs

## Troubleshooting

### Worker Won't Start

**Problem**: Worker crashes on startup

**Solutions**:
1. Check logs for specific error
2. Verify Redis connection:
   ```python
   from app.core.redis import get_redis_client
   print(get_redis_client().ping())
   ```
3. Verify database connection
4. Check environment variables are set

### Tasks Not Executing

**Problem**: Tasks queued but not running

**Solutions**:
1. Check worker is running
2. Verify worker logs show "ready"
3. Check task queue:
   ```python
   redis_client.llen('celery')
   ```
4. Restart worker service

### Beat Not Scheduling

**Problem**: Scheduled tasks not triggering

**Solutions**:
1. Check Beat service is running
2. Verify Beat logs show scheduler starting
3. Check Beat schedule configuration
4. Ensure only ONE Beat instance is running

### Tasks Failing

**Problem**: Tasks execute but fail

**Solutions**:
1. Check task logs for error
2. Test task logic manually
3. Verify external API keys (Indeed, LinkedIn)
4. Check rate limits
5. Review task retry configuration

### Memory Issues

**Problem**: Worker runs out of memory

**Solutions**:
1. Reduce concurrency: `--concurrency=1`
2. Implement task chunking
3. Clear result backend regularly
4. Optimize task code
5. Upgrade to paid tier

## Performance Optimization

### 1. Task Prioritization

```python
# High priority tasks
scrape_jobs_task.apply_async(args=['linkedin'], priority=9)

# Low priority tasks
cleanup_task.apply_async(priority=1)
```

### 2. Task Routing

```python
# Route heavy tasks to specific workers
app.conf.task_routes = {
    'app.tasks.scraping_tasks.*': {'queue': 'scraping'},
    'app.tasks.maintenance_tasks.*': {'queue': 'maintenance'},
}
```

### 3. Rate Limiting

```python
# Limit task execution rate
@app.task(rate_limit='10/m')  # 10 per minute
def scrape_jobs_task(source):
    pass
```

### 4. Task Chunking

```python
# Process large datasets in chunks
from celery import group

def process_large_dataset(items):
    chunk_size = 100
    chunks = [items[i:i+chunk_size] for i in range(0, len(items), chunk_size)]
    
    job = group(process_chunk.s(chunk) for chunk in chunks)
    result = job.apply_async()
    return result
```

## Free Tier Limits

### Railway

- **Memory**: 512MB per service
- **CPU**: Shared
- **Services**: Unlimited (within $5 credit)
- **Uptime**: 99.9% SLA

### Render

- **Memory**: 512MB per service
- **CPU**: 0.1 CPU
- **Services**: Unlimited
- **Spin Down**: After 15 min inactivity
- **Note**: Background workers don't spin down

## Next Steps

After completing Celery deployment:

1. ✅ Celery worker deployed
2. ✅ Celery Beat deployed
3. ✅ Scheduled tasks configured
4. ✅ Tasks executing successfully
5. ➡️ **Next**: Deploy Frontend (Task 36.5)
6. ➡️ Configure Sentry (Task 36.6)

## Support Resources

- **Celery Documentation**: https://docs.celeryq.dev
- **Railway Docs**: https://docs.railway.app
- **Render Docs**: https://render.com/docs
- **Celery Best Practices**: https://docs.celeryq.dev/en/stable/userguide/tasks.html

---

**Task 36.4 Complete!** ✅

Your Celery workers are now processing background tasks and scheduled jobs.
