# Celery Setup and Configuration

This document provides comprehensive information about the Celery configuration for background task processing in the Job Aggregation Platform.

## Overview

Celery is configured with:
- **Broker**: Redis (database 0)
- **Result Backend**: Redis (database 0)
- **Worker Concurrency**: 4 processes with 2 threads each (configurable)
- **Task Queues**: 3 priority queues (high, default, low)
- **Scheduled Tasks**: 8 periodic tasks via Celery Beat

## Architecture

```
┌─────────────────┐
│   FastAPI App   │
│                 │
│  Enqueues Tasks │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Redis Broker   │
│   (Database 0)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│ Celery Workers  │────▶│ Result Backend   │
│  (4 processes)  │     │  (Redis DB 0)    │
└────────┬────────┘     └──────────────────┘
         │
         ▼
┌─────────────────┐
│  Celery Beat    │
│   (Scheduler)   │
└─────────────────┘
```

## Task Queues

### 1. High Priority Queue
- **Purpose**: User-initiated tasks that need immediate processing
- **Priority**: 10 (highest)
- **Tasks**:
  - URL job imports
  - User-triggered operations

### 2. Default Queue
- **Purpose**: Scheduled scraping tasks
- **Priority**: 5 (medium)
- **Tasks**:
  - LinkedIn job scraping
  - Indeed job scraping
  - Naukri job scraping
  - Monster job scraping

### 3. Low Priority Queue
- **Purpose**: Maintenance and cleanup tasks
- **Priority**: 1 (lowest)
- **Tasks**:
  - Job expiration
  - Quota resets
  - Featured listing expiration
  - Quality score updates

## Task Routing

Tasks are automatically routed to appropriate queues based on their name:

```python
# High priority
"app.tasks.scraping_tasks.import_job_from_url" → high_priority queue

# Default priority
"app.tasks.scraping_tasks.scrape_*_jobs" → default queue

# Low priority
"app.tasks.maintenance_tasks.*" → low_priority queue
```

## Scheduled Tasks (Celery Beat)

### Scraping Tasks (Every 6 hours, staggered)
- **LinkedIn**: 00:00, 06:00, 12:00, 18:00
- **Indeed**: 01:00, 07:00, 13:00, 19:00
- **Naukri**: 02:00, 08:00, 14:00, 20:00
- **Monster**: 03:00, 09:00, 15:00, 21:00

### Maintenance Tasks (Daily)
- **Job Expiration**: 02:00 AM
- **Quota Reset**: 03:00 AM
- **Featured Listing Expiration**: 04:00 AM
- **Quality Score Update**: 05:00 AM

## Worker Configuration

### Default Configuration
- **Processes**: 4 (prefork pool)
- **Threads per process**: 2
- **Max tasks per child**: 1000 (prevents memory leaks)
- **Task time limit**: 300 seconds (5 minutes)
- **Soft time limit**: 270 seconds (4.5 minutes)

### Environment Variables
```bash
# Worker settings
CELERY_WORKER_NAME=worker1
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_POOL=prefork
CELERY_WORKER_LOGLEVEL=info

# Beat settings
CELERY_BEAT_LOGLEVEL=info
CELERY_BEAT_SCHEDULE=celerybeat-schedule

# Flower settings
CELERY_FLOWER_PORT=5555
CELERY_FLOWER_LOGLEVEL=info
```

## Running Celery

### 1. Start a Worker

```bash
# Using the provided script
./scripts/run_celery_worker.sh

# Or manually
celery -A app.tasks.celery_app worker \
    -n worker1@%h \
    -c 4 \
    -P prefork \
    -l info \
    -Q high_priority,default,low_priority \
    --max-tasks-per-child=1000
```

### 2. Start Beat Scheduler

```bash
# Using the provided script
./scripts/run_celery_beat.sh

# Or manually
celery -A app.tasks.celery_app beat \
    -l info \
    -s celerybeat-schedule
```

### 3. Start Flower (Optional Monitoring)

```bash
# Using the provided script
./scripts/run_celery_flower.sh

# Or manually
celery -A app.tasks.celery_app flower --port=5555
```

Access Flower at: http://localhost:5555

## Testing Celery

### Test Configuration

```bash
python scripts/test_celery.py
```

This will verify:
- Celery app initialization
- Redis broker connection
- Task queues configuration
- Task routing
- Beat schedule
- Registered tasks

### Test Task Execution

1. Start a worker:
   ```bash
   ./scripts/run_celery_worker.sh
   ```

2. In another terminal, run:
   ```bash
   python -c "from app.tasks.celery_app import debug_task; result = debug_task.delay(); print(result.get())"
   ```

## Task Retry Configuration

All tasks are configured with automatic retry:
- **Max retries**: 3
- **Backoff**: Exponential (2^retry_count seconds)
- **Max backoff**: 600 seconds (10 minutes)
- **Jitter**: Random jitter added to prevent thundering herd

Example retry delays:
- 1st retry: ~2 seconds
- 2nd retry: ~4 seconds
- 3rd retry: ~8 seconds

## Rate Limiting

External scraping tasks are rate-limited:
- **LinkedIn**: 10 requests/minute
- **Indeed**: 20 requests/minute
- **Naukri**: 5 requests/minute
- **Monster**: 5 requests/minute

## Monitoring

### Using Flower

Flower provides a web-based UI for monitoring:
- Active workers and their status
- Task execution history
- Task success/failure rates
- Queue lengths
- Worker resource usage

### Using Celery CLI

```bash
# Inspect active tasks
celery -A app.tasks.celery_app inspect active

# Inspect scheduled tasks
celery -A app.tasks.celery_app inspect scheduled

# Inspect registered tasks
celery -A app.tasks.celery_app inspect registered

# Get worker statistics
celery -A app.tasks.celery_app inspect stats

# Ping workers
celery -A app.tasks.celery_app inspect ping
```

## Production Deployment

### Using Supervisor

Create `/etc/supervisor/conf.d/celery.conf`:

```ini
[program:celery-worker]
command=/path/to/venv/bin/celery -A app.tasks.celery_app worker -n worker1@%%h -c 4 -l info
directory=/path/to/backend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery/worker.log

[program:celery-beat]
command=/path/to/venv/bin/celery -A app.tasks.celery_app beat -l info
directory=/path/to/backend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery/beat.log
```

### Using systemd

Create `/etc/systemd/system/celery-worker.service`:

```ini
[Unit]
Description=Celery Worker
After=network.target redis.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/celery -A app.tasks.celery_app worker -n worker1@%%h -c 4 -l info
Restart=always

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/celery-beat.service`:

```ini
[Unit]
Description=Celery Beat
After=network.target redis.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/path/to/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/celery -A app.tasks.celery_app beat -l info
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable celery-worker celery-beat
sudo systemctl start celery-worker celery-beat
```

### Using Docker

See `docker-compose.yml` for containerized deployment.

## Scaling Workers

### Horizontal Scaling
Run multiple worker instances on different machines:

```bash
# Machine 1
celery -A app.tasks.celery_app worker -n worker1@machine1 -c 4

# Machine 2
celery -A app.tasks.celery_app worker -n worker2@machine2 -c 4
```

### Vertical Scaling
Increase concurrency on a single machine:

```bash
# 8 processes instead of 4
celery -A app.tasks.celery_app worker -n worker1@%h -c 8
```

### Queue-Specific Workers
Run dedicated workers for specific queues:

```bash
# High priority worker
celery -A app.tasks.celery_app worker -n high_worker@%h -c 2 -Q high_priority

# Default priority worker
celery -A app.tasks.celery_app worker -n default_worker@%h -c 4 -Q default

# Low priority worker
celery -A app.tasks.celery_app worker -n low_worker@%h -c 2 -Q low_priority
```

## Troubleshooting

### Worker Not Starting
1. Check Redis connection:
   ```bash
   redis-cli ping
   ```

2. Verify environment variables:
   ```bash
   echo $CELERY_BROKER_URL
   echo $CELERY_RESULT_BACKEND
   ```

3. Check logs for errors:
   ```bash
   celery -A app.tasks.celery_app worker -l debug
   ```

### Tasks Not Executing
1. Verify worker is running and consuming from correct queues
2. Check task routing configuration
3. Inspect active tasks:
   ```bash
   celery -A app.tasks.celery_app inspect active
   ```

### Beat Not Scheduling Tasks
1. Ensure only one Beat instance is running
2. Check Beat schedule file permissions
3. Verify Beat schedule configuration:
   ```python
   from app.tasks.celery_app import celery_app
   print(celery_app.conf.beat_schedule)
   ```

### High Memory Usage
1. Reduce `worker_max_tasks_per_child` to restart workers more frequently
2. Reduce concurrency (`-c` parameter)
3. Use `solo` pool instead of `prefork` for memory-constrained environments

## Best Practices

1. **Always use task queues**: Don't run all tasks in the default queue
2. **Set task time limits**: Prevent tasks from running indefinitely
3. **Use task retries**: Handle transient failures automatically
4. **Monitor task execution**: Use Flower or logging to track task performance
5. **Scale appropriately**: Add workers based on queue length and task execution time
6. **Use result expiration**: Don't store task results indefinitely
7. **Implement idempotency**: Tasks should be safe to retry
8. **Log task progress**: Use structured logging for debugging

## References

- [Celery Documentation](https://docs.celeryproject.org/)
- [Celery Best Practices](https://docs.celeryproject.org/en/stable/userguide/tasks.html#tips-and-best-practices)
- [Flower Documentation](https://flower.readthedocs.io/)
