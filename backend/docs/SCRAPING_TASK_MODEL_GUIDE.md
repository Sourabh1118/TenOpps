# ScrapingTask Model Guide

## Overview

The ScrapingTask model tracks all scraping operations in the platform, including scheduled scrapes, manual scrapes, and URL imports. It provides comprehensive monitoring, debugging, and retry management capabilities for the job aggregation system. Each scraping operation creates a task record that tracks execution status, metrics, timing, and errors.

## Model Structure

### Fields

#### Primary Key
- **id** (UUID): Unique identifier for the scraping task

#### Task Identification
- **task_type** (TaskType enum): Type of scraping operation
  - `SCHEDULED_SCRAPE`: Automated scheduled scraping (cron jobs)
  - `MANUAL_SCRAPE`: Manually triggered scraping by admin
  - `URL_IMPORT`: URL-based job import by employer
  - Required field, indexed
- **source_platform** (String, max 50 chars): Platform being scraped
  - Examples: "LinkedIn", "Indeed", "Naukri", "Monster"
  - Optional (null for URL imports without platform identification)
  - Indexed for platform-specific queries
- **target_url** (Text): Specific URL for URL import tasks
  - Optional (used only for URL_IMPORT task type)
  - Stores the employer-provided job URL

#### Status Tracking
- **status** (TaskStatus enum): Current task status
  - `PENDING`: Task queued but not started
  - `RUNNING`: Task currently executing
  - `COMPLETED`: Task finished successfully
  - `FAILED`: Task failed with error
  - Required field, indexed, default: PENDING

#### Execution Timing
- **started_at** (DateTime with timezone): When task execution began
  - Optional (null until task starts)
  - Set when status changes to RUNNING
- **completed_at** (DateTime with timezone): When task execution finished
  - Optional (null until task completes or fails)
  - Set when status changes to COMPLETED or FAILED

#### Metrics
- **jobs_found** (Integer): Total jobs discovered during scraping
  - Default: 0
  - Non-negative constraint
- **jobs_created** (Integer): New jobs created in database
  - Default: 0
  - Non-negative constraint
- **jobs_updated** (Integer): Existing jobs updated (duplicates)
  - Default: 0
  - Non-negative constraint
- **Constraint**: jobs_found >= jobs_created + jobs_updated

#### Error Handling
- **error_message** (Text): Error details if task failed
  - Optional (null for successful tasks)
  - Stores exception message and stack trace
- **retry_count** (Integer): Number of retry attempts
  - Default: 0
  - Range: 0-3 (enforced by check constraint)
  - Incremented on each retry

#### Timestamps
- **created_at** (DateTime with timezone): When task was created
  - Default: current timestamp
  - Indexed for monitoring queries

### Enums

#### TaskType
```python
class TaskType(str, enum.Enum):
    SCHEDULED_SCRAPE = "scheduled_scrape"
    MANUAL_SCRAPE = "manual_scrape"
    URL_IMPORT = "url_import"
```

#### TaskStatus
```python
class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
```

### Indexes

1. **idx_scraping_tasks_id**: Primary key index
2. **idx_scraping_tasks_status**: Status index for filtering
3. **idx_scraping_tasks_created_at**: Timestamp index for time-based queries
4. **idx_scraping_tasks_status_created**: Composite index on (status, created_at)
   - **Required by task specification**
   - Optimizes monitoring queries (e.g., recent failed tasks)
5. **idx_scraping_tasks_platform**: Platform index for platform-specific queries
6. **idx_scraping_tasks_type**: Task type index for filtering by operation type

### Check Constraints

1. **check_retry_count_bounds**: retry_count >= 0 AND retry_count <= 3
2. **check_jobs_found_consistency**: jobs_found >= jobs_created + jobs_updated
3. **check_jobs_metrics_positive**: All job metrics >= 0
4. **check_completion_after_start**: completed_at >= started_at (when both present)

## Use Cases

### 1. Scheduled Scraping Monitoring
Track automated scraping operations across all platforms:

```
Daily LinkedIn Scrape
├── Status: COMPLETED
├── Jobs Found: 150
├── Jobs Created: 45
├── Jobs Updated: 105
└── Duration: 5m 30s
```

### 2. URL Import Tracking
Monitor employer-initiated URL imports:

```
URL Import: https://linkedin.com/jobs/view/123
├── Status: COMPLETED
├── Jobs Found: 1
├── Jobs Created: 1
└── Employer: employer_id_123
```

### 3. Error Tracking and Retry Management
Track failures and retry attempts:

```
Failed Scrape: Naukri
├── Status: FAILED
├── Error: Connection timeout
├── Retry Count: 2
└── Next Retry: In 20 minutes
```

## Helper Methods

### is_pending()
Returns `True` if the task is pending execution.

```python
if task.is_pending():
    print("Task is queued for execution")
```

### is_running()
Returns `True` if the task is currently running.

```python
if task.is_running():
    print("Task is in progress")
```

### is_completed()
Returns `True` if the task completed successfully.

```python
if task.is_completed():
    print(f"Task completed: {task.jobs_created} jobs created")
```

### is_failed()
Returns `True` if the task failed.

```python
if task.is_failed():
    print(f"Task failed: {task.error_message}")
```

### can_retry()
Returns `True` if the task can be retried (failed and retry_count < 3).

```python
if task.can_retry():
    # Schedule retry with exponential backoff
    delay = 300 * (2 ** task.retry_count)
    schedule_retry(task.id, delay)
```

### get_duration_seconds()
Calculates task duration in seconds.

```python
duration = task.get_duration_seconds()
print(f"Task took {duration:.2f} seconds")
```

### get_success_rate()
Calculates success rate (jobs_created / jobs_found * 100).

```python
success_rate = task.get_success_rate()
print(f"Success rate: {success_rate:.1f}%")
```

## Usage Examples

### Creating a Scheduled Scrape Task

```python
from app.models.scraping_task import ScrapingTask, TaskType, TaskStatus
import uuid

# Create task for scheduled scraping
task = ScrapingTask(
    id=uuid.uuid4(),
    task_type=TaskType.SCHEDULED_SCRAPE,
    source_platform="LinkedIn",
    status=TaskStatus.PENDING
)

db.add(task)
db.commit()
```

### Creating a URL Import Task

```python
# Create task for URL import
task = ScrapingTask(
    id=uuid.uuid4(),
    task_type=TaskType.URL_IMPORT,
    target_url="https://www.linkedin.com/jobs/view/123456789",
    status=TaskStatus.PENDING
)

db.add(task)
db.commit()
```

### Updating Task Status During Execution

```python
from datetime import datetime

# Start task execution
task.status = TaskStatus.RUNNING
task.started_at = datetime.now()
db.commit()

try:
    # Perform scraping
    jobs = scraper.scrape_platform(task.source_platform)
    
    # Update metrics
    task.jobs_found = len(jobs)
    task.jobs_created = count_new_jobs
    task.jobs_updated = count_updated_jobs
    
    # Mark as completed
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now()
    db.commit()
    
except Exception as e:
    # Mark as failed
    task.status = TaskStatus.FAILED
    task.error_message = str(e)
    task.completed_at = datetime.now()
    task.retry_count += 1
    db.commit()
```

### Querying Tasks for Monitoring

```python
from sqlalchemy import and_, desc
from datetime import datetime, timedelta

# Get recent failed tasks
recent_failures = db.query(ScrapingTask).filter(
    and_(
        ScrapingTask.status == TaskStatus.FAILED,
        ScrapingTask.created_at >= datetime.now() - timedelta(hours=24)
    )
).order_by(desc(ScrapingTask.created_at)).all()

# Get running tasks
running_tasks = db.query(ScrapingTask).filter(
    ScrapingTask.status == TaskStatus.RUNNING
).all()

# Get tasks by platform
linkedin_tasks = db.query(ScrapingTask).filter(
    ScrapingTask.source_platform == "LinkedIn"
).order_by(desc(ScrapingTask.created_at)).limit(10).all()

# Get tasks needing retry
retry_candidates = db.query(ScrapingTask).filter(
    and_(
        ScrapingTask.status == TaskStatus.FAILED,
        ScrapingTask.retry_count < 3
    )
).all()
```

### Monitoring Dashboard Queries

```python
# Get task statistics for last 24 hours
from sqlalchemy import func

stats = db.query(
    ScrapingTask.status,
    func.count(ScrapingTask.id).label('count'),
    func.sum(ScrapingTask.jobs_found).label('total_found'),
    func.sum(ScrapingTask.jobs_created).label('total_created'),
    func.avg(ScrapingTask.jobs_created * 100.0 / ScrapingTask.jobs_found).label('avg_success_rate')
).filter(
    ScrapingTask.created_at >= datetime.now() - timedelta(hours=24)
).group_by(ScrapingTask.status).all()

# Get platform performance
platform_stats = db.query(
    ScrapingTask.source_platform,
    func.count(ScrapingTask.id).label('total_tasks'),
    func.sum(case((ScrapingTask.status == TaskStatus.COMPLETED, 1), else_=0)).label('successful'),
    func.avg(ScrapingTask.jobs_created).label('avg_jobs_created')
).filter(
    ScrapingTask.created_at >= datetime.now() - timedelta(days=7)
).group_by(ScrapingTask.source_platform).all()
```

## Integration with Scraping System

### Celery Task Integration

```python
from celery import Task
from app.models.scraping_task import ScrapingTask, TaskType, TaskStatus

@celery_app.task(bind=True, max_retries=3)
def scrape_platform(self, platform: str):
    # Create task record
    task = ScrapingTask(
        task_type=TaskType.SCHEDULED_SCRAPE,
        source_platform=platform,
        status=TaskStatus.PENDING
    )
    db.add(task)
    db.commit()
    
    try:
        # Start execution
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        db.commit()
        
        # Perform scraping
        scraper = get_scraper(platform)
        jobs = scraper.scrape()
        
        # Process jobs
        jobs_created = 0
        jobs_updated = 0
        
        for job_data in jobs:
            if is_duplicate(job_data):
                update_job(job_data)
                jobs_updated += 1
            else:
                create_job(job_data)
                jobs_created += 1
        
        # Update task with results
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        task.jobs_found = len(jobs)
        task.jobs_created = jobs_created
        task.jobs_updated = jobs_updated
        db.commit()
        
    except Exception as e:
        # Handle failure
        task.status = TaskStatus.FAILED
        task.error_message = str(e)
        task.completed_at = datetime.now()
        task.retry_count += 1
        db.commit()
        
        # Retry with exponential backoff
        if task.can_retry():
            delay = 300 * (2 ** task.retry_count)
            raise self.retry(exc=e, countdown=delay)
```

### URL Import Workflow

```python
async def import_job_from_url(employer_id: str, url: str):
    # Create import task
    task = ScrapingTask(
        task_type=TaskType.URL_IMPORT,
        target_url=url,
        status=TaskStatus.PENDING
    )
    db.add(task)
    db.commit()
    
    try:
        # Start import
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        db.commit()
        
        # Scrape URL
        job_data = await scraper.scrape_url(url)
        
        # Check for duplicates
        if not is_duplicate(job_data):
            create_job(job_data, employer_id=employer_id)
            task.jobs_found = 1
            task.jobs_created = 1
        else:
            task.jobs_found = 1
            task.jobs_updated = 1
        
        # Mark as completed
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        db.commit()
        
        return {"success": True, "task_id": task.id}
        
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.error_message = str(e)
        task.completed_at = datetime.now()
        db.commit()
        
        return {"success": False, "error": str(e)}
```

## Monitoring and Alerting

### Alert on Consecutive Failures

```python
def check_consecutive_failures(platform: str, threshold: int = 3):
    """Alert if platform has consecutive failures."""
    recent_tasks = db.query(ScrapingTask).filter(
        ScrapingTask.source_platform == platform
    ).order_by(desc(ScrapingTask.created_at)).limit(threshold).all()
    
    if len(recent_tasks) == threshold:
        if all(task.status == TaskStatus.FAILED for task in recent_tasks):
            send_alert(f"Platform {platform} has {threshold} consecutive failures")
```

### Performance Monitoring

```python
def get_platform_health(platform: str, hours: int = 24):
    """Get platform health metrics."""
    cutoff = datetime.now() - timedelta(hours=hours)
    
    tasks = db.query(ScrapingTask).filter(
        and_(
            ScrapingTask.source_platform == platform,
            ScrapingTask.created_at >= cutoff
        )
    ).all()
    
    total = len(tasks)
    completed = sum(1 for t in tasks if t.is_completed())
    failed = sum(1 for t in tasks if t.is_failed())
    avg_duration = sum(t.get_duration_seconds() for t in tasks if t.completed_at) / total
    avg_success_rate = sum(t.get_success_rate() for t in tasks if t.is_completed()) / completed
    
    return {
        'platform': platform,
        'total_tasks': total,
        'success_rate': (completed / total * 100) if total > 0 else 0,
        'failure_rate': (failed / total * 100) if total > 0 else 0,
        'avg_duration_seconds': avg_duration,
        'avg_job_success_rate': avg_success_rate
    }
```

## Validation Rules

### Database Constraints

1. **Retry Count**: Must be between 0 and 3
2. **Jobs Consistency**: jobs_found >= jobs_created + jobs_updated
3. **Jobs Metrics**: All job metrics must be non-negative
4. **Timing**: completed_at must be >= started_at when both present
5. **Required Fields**: task_type and status are required

### Application Logic Validation

1. **Task Type**: Must be valid TaskType enum value
2. **Status Transitions**: Follow valid state machine (PENDING → RUNNING → COMPLETED/FAILED)
3. **Platform Required**: source_platform required for SCHEDULED_SCRAPE and MANUAL_SCRAPE
4. **URL Required**: target_url required for URL_IMPORT
5. **Metrics Update**: Only update metrics when task completes

## Performance Considerations

### Indexing Strategy
- Composite index on (status, created_at) optimizes monitoring queries
- Platform index enables efficient platform-specific queries
- Task type index supports filtering by operation type

### Query Optimization
- Use composite index for monitoring: `WHERE status = ? AND created_at >= ?`
- Use platform index for platform queries: `WHERE source_platform = ?`
- Limit result sets for dashboard queries

### Data Retention
- Archive completed tasks older than 90 days
- Keep failed tasks for 180 days for debugging
- Maintain recent task history for monitoring

## Testing

### Unit Tests
See `tests/test_scraping_task_model.py` for comprehensive test coverage:
- Model creation with required fields
- Task type and status enums
- Check constraints (retry_count, jobs metrics, timing)
- Helper methods (is_pending, can_retry, get_duration_seconds, etc.)
- Monitoring query indexes
- Edge cases and validation

### Integration Tests
- Celery task integration
- URL import workflow
- Retry mechanism
- Monitoring queries
- Alert triggers

## Migration

The ScrapingTask model is created by migration `005_create_scraping_tasks_table.py`.

### Running the Migration

```bash
# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Migration Details
- Creates `scraping_tasks` table with all fields and constraints
- Creates TaskType and TaskStatus enums
- Creates all indexes including:
  - Primary key index
  - Status and created_at indexes
  - Composite (status, created_at) index (required by task)
  - Platform and task type indexes
- Creates check constraints for validation

## Best Practices

1. **Task Creation**: Always create a task record before starting scraping
2. **Status Updates**: Update status atomically with metrics
3. **Error Handling**: Store detailed error messages for debugging
4. **Retry Logic**: Use exponential backoff for retries
5. **Monitoring**: Regularly query recent tasks for health checks
6. **Alerting**: Set up alerts for consecutive failures
7. **Metrics**: Always update job metrics when task completes
8. **Cleanup**: Archive old tasks to maintain performance

## Related Documentation

- [Job Model Guide](./JOB_MODEL_GUIDE.md)
- [JobSource Model Guide](./JOB_SOURCE_MODEL_GUIDE.md)
- [Celery Setup](./CELERY_SETUP.md)
- [Database Setup](./DATABASE_SETUP.md)
- Requirements 1.7, 1.8, 15.2 (Job Aggregation, Error Handling, Logging)

## Requirements Validation

This model satisfies the following requirements:

### Requirement 1.7 (Automated Job Aggregation)
- Tracks scraping task execution and results
- Records jobs found, created, and updated
- Supports scheduled scraping operations

### Requirement 1.8 (Scraping Task Logging)
- Logs scraping task status and metrics
- Records error messages for failed tasks
- Tracks retry attempts

### Requirement 15.2 (Error Handling and Logging)
- Comprehensive error logging with stack traces
- Retry count tracking for failure management
- Task status tracking for monitoring
