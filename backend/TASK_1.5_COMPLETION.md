# Task 1.5 Completion: Configure Celery for Background Tasks

## Summary

Successfully configured Celery for background task processing with Redis broker and result backend. The implementation includes:

1. ✅ Celery app configuration with Redis broker and result backend
2. ✅ Worker configuration (4 processes, 2 threads each)
3. ✅ Task routing with 3 priority queues (high, default, low)
4. ✅ Celery Beat configuration for 8 scheduled tasks
5. ✅ Task modules for scraping, maintenance, and monitoring
6. ✅ Shell scripts to run workers, beat, and flower
7. ✅ Comprehensive documentation and quick start guide
8. ✅ Unit tests for Celery configuration

## Files Created

### Core Configuration
- `app/tasks/celery_app.py` - Main Celery app configuration with queues, routing, and Beat schedule
- `app/tasks/__init__.py` - Package initialization with exports

### Task Modules
- `app/tasks/scraping_tasks.py` - Scraping tasks (LinkedIn, Indeed, Naukri, Monster, URL import)
- `app/tasks/maintenance_tasks.py` - Maintenance tasks (expiration, quotas, featured listings, quality scores)
- `app/tasks/monitoring_tasks.py` - Monitoring tasks (health checks, metrics)

### Scripts
- `scripts/run_celery_worker.sh` - Start Celery worker with configured concurrency
- `scripts/run_celery_beat.sh` - Start Celery Beat scheduler
- `scripts/run_celery_flower.sh` - Start Flower monitoring UI
- `scripts/test_celery.py` - Test Celery configuration and connectivity

### Documentation
- `docs/CELERY_SETUP.md` - Comprehensive setup and configuration guide
- `docs/CELERY_QUICK_START.md` - Quick start guide for getting Celery running
- `TASK_1.5_COMPLETION.md` - This completion summary

### Tests
- `tests/test_celery.py` - Unit tests for Celery configuration and tasks

### Dependencies
- Updated `requirements.txt` to include `flower==2.0.1`

## Configuration Details

### Task Queues

1. **High Priority Queue** (priority: 10)
   - URL job imports
   - User-initiated tasks
   - Immediate processing required

2. **Default Queue** (priority: 5)
   - Scheduled scraping tasks
   - LinkedIn, Indeed, Naukri, Monster scraping
   - Regular background processing

3. **Low Priority Queue** (priority: 1)
   - Maintenance tasks
   - Job expiration, quota resets
   - Non-urgent operations

### Worker Configuration

- **Concurrency**: 4 processes (prefork pool)
- **Max tasks per child**: 1000 (prevents memory leaks)
- **Task time limit**: 300 seconds (5 minutes)
- **Soft time limit**: 270 seconds (4.5 minutes)
- **Prefetch multiplier**: 4 tasks per worker
- **Retry configuration**: 3 retries with exponential backoff

### Scheduled Tasks (Celery Beat)

#### Scraping Tasks (Every 6 hours, staggered)
- **LinkedIn**: 00:00, 06:00, 12:00, 18:00
- **Indeed**: 01:00, 07:00, 13:00, 19:00
- **Naukri**: 02:00, 08:00, 14:00, 20:00
- **Monster**: 03:00, 09:00, 15:00, 21:00

#### Maintenance Tasks (Daily)
- **Job Expiration**: 02:00 AM
- **Quota Reset**: 03:00 AM
- **Featured Listing Expiration**: 04:00 AM
- **Quality Score Update**: 05:00 AM

### Rate Limiting

External scraping tasks are rate-limited:
- **LinkedIn**: 10 requests/minute
- **Indeed**: 20 requests/minute
- **Naukri**: 5 requests/minute
- **Monster**: 5 requests/minute

## Task Routing

Tasks are automatically routed based on their name:

```python
# High priority
"app.tasks.scraping_tasks.import_job_from_url" → high_priority queue (priority 9)

# Default priority
"app.tasks.scraping_tasks.scrape_*_jobs" → default queue (priority 5)

# Low priority
"app.tasks.maintenance_tasks.*" → low_priority queue (priority 1)
```

## Getting Started

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Add to `.env`:
```bash
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 3. Test Configuration

```bash
python scripts/test_celery.py
```

### 4. Start Worker

```bash
./scripts/run_celery_worker.sh
```

### 5. Start Beat (for scheduled tasks)

```bash
./scripts/run_celery_beat.sh
```

### 6. Start Flower (optional monitoring)

```bash
./scripts/run_celery_flower.sh
```

Access at: http://localhost:5555

## Task Implementation Status

### Scraping Tasks (Placeholder)
- ✅ `scrape_linkedin_jobs` - Configured, implementation pending
- ✅ `scrape_indeed_jobs` - Configured, implementation pending
- ✅ `scrape_naukri_jobs` - Configured, implementation pending
- ✅ `scrape_monster_jobs` - Configured, implementation pending
- ✅ `import_job_from_url` - Configured, implementation pending

### Maintenance Tasks (Placeholder)
- ✅ `expire_old_jobs` - Configured, implementation pending
- ✅ `reset_monthly_quotas` - Configured, implementation pending
- ✅ `remove_expired_featured_listings` - Configured, implementation pending
- ✅ `update_quality_scores` - Configured, implementation pending

### Monitoring Tasks (Placeholder)
- ✅ `health_check` - Configured, implementation pending
- ✅ `collect_metrics` - Configured, implementation pending

**Note**: Task implementations are placeholders that return success status. Actual scraping and maintenance logic will be implemented in later tasks (Tasks 9-20).

## Testing

### Unit Tests

Run tests with:
```bash
pytest tests/test_celery.py -v
```

Tests cover:
- ✅ Celery app configuration
- ✅ Broker and result backend setup
- ✅ Task queue configuration
- ✅ Task routing rules
- ✅ Beat schedule configuration
- ✅ Task registration
- ✅ Retry configuration
- ✅ Priority configuration
- ✅ Task execution (placeholder)

### Manual Testing

1. **Test Configuration**:
   ```bash
   python scripts/test_celery.py
   ```

2. **Test Task Execution** (requires running worker):
   ```bash
   python -c "from app.tasks.celery_app import debug_task; result = debug_task.delay(); print(result.get())"
   ```

3. **Inspect Workers**:
   ```bash
   celery -A app.tasks.celery_app inspect active
   celery -A app.tasks.celery_app inspect registered
   celery -A app.tasks.celery_app inspect ping
   ```

## Production Deployment

### Using Supervisor

See `docs/CELERY_SETUP.md` for Supervisor configuration.

### Using systemd

See `docs/CELERY_SETUP.md` for systemd service files.

### Using Docker

Add to `docker-compose.yml`:

```yaml
celery-worker:
  build: .
  command: celery -A app.tasks.celery_app worker -c 4 -l info
  depends_on:
    - redis
    - postgres
  environment:
    - CELERY_BROKER_URL=redis://redis:6379/0
    - CELERY_RESULT_BACKEND=redis://redis:6379/0

celery-beat:
  build: .
  command: celery -A app.tasks.celery_app beat -l info
  depends_on:
    - redis
    - postgres
  environment:
    - CELERY_BROKER_URL=redis://redis:6379/0
    - CELERY_RESULT_BACKEND=redis://redis:6379/0
```

## Monitoring

### Flower Web UI

Access at http://localhost:5555 when running:
```bash
./scripts/run_celery_flower.sh
```

Features:
- Real-time task monitoring
- Worker status and statistics
- Task history and results
- Queue lengths and throughput
- Worker resource usage

### CLI Monitoring

```bash
# Active tasks
celery -A app.tasks.celery_app inspect active

# Worker stats
celery -A app.tasks.celery_app inspect stats

# Scheduled tasks
celery -A app.tasks.celery_app inspect scheduled

# Ping workers
celery -A app.tasks.celery_app inspect ping
```

## Scaling

### Horizontal Scaling
Run multiple workers on different machines:
```bash
# Machine 1
celery -A app.tasks.celery_app worker -n worker1@machine1 -c 4

# Machine 2
celery -A app.tasks.celery_app worker -n worker2@machine2 -c 4
```

### Vertical Scaling
Increase concurrency:
```bash
# 8 processes instead of 4
CELERY_WORKER_CONCURRENCY=8 ./scripts/run_celery_worker.sh
```

### Queue-Specific Workers
Run dedicated workers for specific queues:
```bash
# High priority worker
celery -A app.tasks.celery_app worker -n high_worker -c 2 -Q high_priority

# Default priority worker
celery -A app.tasks.celery_app worker -n default_worker -c 4 -Q default

# Low priority worker
celery -A app.tasks.celery_app worker -n low_worker -c 2 -Q low_priority
```

## Requirements Validation

### Requirement 1.7: Scraping Task Records
✅ Configured scraping tasks with proper logging and result tracking
- Task records will be created when scraping logic is implemented
- Task status tracking (PENDING, RUNNING, COMPLETED, FAILED)
- Results tracking (jobs_found, jobs_created, jobs_updated)

### Requirement 1.8: Retry with Exponential Backoff
✅ Implemented retry configuration for all tasks
- Max retries: 3 attempts
- Exponential backoff enabled
- Max backoff: 600 seconds (10 minutes)
- Random jitter to prevent thundering herd
- Automatic retry on exceptions

## Next Steps

1. **Task 2.x**: Implement database models for Job, ScrapingTask, etc.
2. **Task 9.x**: Implement actual scraping logic in task modules
3. **Task 14.x**: Implement scraping orchestration and deduplication
4. **Task 15.x**: Implement URL import logic
5. **Task 20.x**: Implement job expiration logic
6. **Task 4.x**: Implement quota reset logic

## Notes

- All task implementations are currently placeholders that return success status
- Actual business logic will be implemented in later tasks
- Celery configuration is production-ready and follows best practices
- Task routing and priority queues are configured for optimal performance
- Monitoring and scaling capabilities are built-in

## References

- [Celery Setup Guide](docs/CELERY_SETUP.md)
- [Celery Quick Start](docs/CELERY_QUICK_START.md)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Documentation](https://redis.io/documentation)
- [Flower Documentation](https://flower.readthedocs.io/)
