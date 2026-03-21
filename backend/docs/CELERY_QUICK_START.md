# Celery Quick Start Guide

Get Celery up and running in 5 minutes.

## Prerequisites

- Redis running on localhost:6379 (or configured in `.env`)
- Python virtual environment activated
- Dependencies installed (`pip install -r requirements.txt`)

## Quick Setup

### 1. Verify Configuration

```bash
python scripts/test_celery.py
```

This will check:
- ✓ Celery app initialization
- ✓ Redis broker connection
- ✓ Task queues configuration
- ✓ Task routing
- ✓ Beat schedule

### 2. Start a Worker

Open a terminal and run:

```bash
./scripts/run_celery_worker.sh
```

You should see:
```
Starting Celery worker: worker1
Concurrency: 4 processes
Pool: prefork
Log level: info

 -------------- celery@worker1 v5.3.4
---- **** ----- 
--- * ***  * -- Linux-... 
-- * - **** --- 
- ** ---------- [config]
- ** ---------- .> app:         job_aggregation_platform
- ** ---------- .> transport:   redis://localhost:6379/0
- ** ---------- .> results:     redis://localhost:6379/0
- *** --- * --- .> concurrency: 4 (prefork)
-- ******* ---- .> task events: OFF
--- ***** ----- 
 -------------- [queues]
                .> high_priority    exchange=high_priority(direct) key=high_priority
                .> default          exchange=default(direct) key=default
                .> low_priority     exchange=low_priority(direct) key=low_priority

[tasks]
  . app.tasks.celery_app.debug_task
  . app.tasks.scraping_tasks.import_job_from_url
  . app.tasks.scraping_tasks.scrape_indeed_jobs
  . app.tasks.scraping_tasks.scrape_linkedin_jobs
  . app.tasks.scraping_tasks.scrape_monster_jobs
  . app.tasks.scraping_tasks.scrape_naukri_jobs
  . app.tasks.maintenance_tasks.expire_old_jobs
  . app.tasks.maintenance_tasks.remove_expired_featured_listings
  . app.tasks.maintenance_tasks.reset_monthly_quotas
  . app.tasks.maintenance_tasks.update_quality_scores
  . app.tasks.monitoring_tasks.collect_metrics
  . app.tasks.monitoring_tasks.health_check

[... ready.]
```

### 3. Test Task Execution

Open another terminal and run:

```bash
python -c "from app.tasks.celery_app import debug_task; result = debug_task.delay(); print('Task ID:', result.id); print('Result:', result.get(timeout=10))"
```

Expected output:
```
Task ID: 12345678-1234-1234-1234-123456789012
Result: {'status': 'success', 'message': 'Celery is working!'}
```

### 4. Start Beat Scheduler (Optional)

For scheduled tasks, open another terminal:

```bash
./scripts/run_celery_beat.sh
```

You should see:
```
Starting Celery Beat scheduler
Log level: info
Schedule file: celerybeat-schedule

celery beat v5.3.4 is starting.
LocalTime -> 2024-01-15 10:00:00
Configuration ->
    . broker -> redis://localhost:6379/0
    . loader -> celery.loaders.app.AppLoader
    . scheduler -> celery.beat.PersistentScheduler
    . db -> celerybeat-schedule
    . logfile -> [stderr]@%INFO
    . maxinterval -> 5.00 minutes (300s)
```

### 5. Start Flower Monitoring (Optional)

For a web-based monitoring UI:

```bash
./scripts/run_celery_flower.sh
```

Then open http://localhost:5555 in your browser.

## Common Tasks

### Execute a Task Manually

```python
from app.tasks.scraping_tasks import scrape_linkedin_jobs

# Execute asynchronously
result = scrape_linkedin_jobs.delay()
print(f"Task ID: {result.id}")

# Wait for result
task_result = result.get(timeout=60)
print(f"Result: {task_result}")
```

### Check Task Status

```python
from celery.result import AsyncResult
from app.tasks.celery_app import celery_app

# Get task by ID
result = AsyncResult('task-id-here', app=celery_app)
print(f"Status: {result.state}")
print(f"Result: {result.result}")
```

### Inspect Workers

```bash
# Check active tasks
celery -A app.tasks.celery_app inspect active

# Check registered tasks
celery -A app.tasks.celery_app inspect registered

# Ping workers
celery -A app.tasks.celery_app inspect ping
```

## Environment Variables

Add these to your `.env` file:

```bash
# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Worker Configuration (optional)
CELERY_WORKER_NAME=worker1
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_POOL=prefork
CELERY_WORKER_LOGLEVEL=info

# Beat Configuration (optional)
CELERY_BEAT_LOGLEVEL=info
CELERY_BEAT_SCHEDULE=celerybeat-schedule

# Flower Configuration (optional)
CELERY_FLOWER_PORT=5555
CELERY_FLOWER_LOGLEVEL=info
```

## Task Queues

Tasks are automatically routed to appropriate queues:

- **high_priority**: URL imports, user-initiated tasks (priority 9-10)
- **default**: Scheduled scraping tasks (priority 5)
- **low_priority**: Maintenance tasks (priority 1)

## Scheduled Tasks

Celery Beat runs these tasks automatically:

| Task | Schedule | Description |
|------|----------|-------------|
| scrape_linkedin_jobs | Every 6 hours (0, 6, 12, 18) | Scrape LinkedIn jobs |
| scrape_indeed_jobs | Every 6 hours (1, 7, 13, 19) | Scrape Indeed jobs |
| scrape_naukri_jobs | Every 6 hours (2, 8, 14, 20) | Scrape Naukri jobs |
| scrape_monster_jobs | Every 6 hours (3, 9, 15, 21) | Scrape Monster jobs |
| expire_old_jobs | Daily at 2 AM | Mark expired jobs |
| reset_monthly_quotas | Daily at 3 AM | Reset employer quotas |
| remove_expired_featured_listings | Daily at 4 AM | Remove expired featured flags |
| update_quality_scores | Daily at 5 AM | Update job quality scores |

## Troubleshooting

### "Connection refused" error
- Make sure Redis is running: `redis-cli ping`
- Check CELERY_BROKER_URL in `.env`

### Worker not starting
- Check for syntax errors: `python -c "from app.tasks.celery_app import celery_app"`
- Verify Redis connection: `python scripts/test_celery.py`

### Tasks not executing
- Verify worker is running and consuming from correct queues
- Check worker logs for errors
- Inspect active tasks: `celery -A app.tasks.celery_app inspect active`

### Beat not scheduling tasks
- Ensure only ONE Beat instance is running
- Check Beat logs for errors
- Verify schedule file permissions

## Next Steps

1. Read the full [Celery Setup Guide](CELERY_SETUP.md)
2. Implement scraping logic in task modules
3. Add custom tasks for your use case
4. Set up monitoring with Flower
5. Configure production deployment

## Useful Commands

```bash
# Start worker
./scripts/run_celery_worker.sh

# Start beat
./scripts/run_celery_beat.sh

# Start flower
./scripts/run_celery_flower.sh

# Test configuration
python scripts/test_celery.py

# Inspect workers
celery -A app.tasks.celery_app inspect active
celery -A app.tasks.celery_app inspect stats
celery -A app.tasks.celery_app inspect ping

# Purge all tasks
celery -A app.tasks.celery_app purge

# Control workers
celery -A app.tasks.celery_app control shutdown
celery -A app.tasks.celery_app control pool_restart
```

## Support

For more information, see:
- [Celery Setup Guide](CELERY_SETUP.md)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Documentation](https://redis.io/documentation)
