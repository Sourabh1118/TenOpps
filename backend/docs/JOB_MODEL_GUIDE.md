# Job Model Quick Reference Guide

## Overview

The Job model is the core entity for storing all job postings in the platform. It supports three source types: direct employer posts, URL imports, and aggregated jobs from external platforms.

## Model Location

```python
from app.models import Job, JobType, ExperienceLevel, SourceType, JobStatus
```

## Enums

### JobType
```python
JobType.FULL_TIME      # "full_time"
JobType.PART_TIME      # "part_time"
JobType.CONTRACT       # "contract"
JobType.FREELANCE      # "freelance"
JobType.INTERNSHIP     # "internship"
JobType.FELLOWSHIP     # "fellowship"
JobType.ACADEMIC       # "academic"
```

### ExperienceLevel
```python
ExperienceLevel.ENTRY      # "entry"
ExperienceLevel.MID        # "mid"
ExperienceLevel.SENIOR     # "senior"
ExperienceLevel.LEAD       # "lead"
ExperienceLevel.EXECUTIVE  # "executive"
```

### SourceType
```python
SourceType.DIRECT       # "direct" - Posted by employer
SourceType.URL_IMPORT   # "url_import" - Imported via URL
SourceType.AGGREGATED   # "aggregated" - Scraped from external sources
```

### JobStatus
```python
JobStatus.ACTIVE    # "active"
JobStatus.EXPIRED   # "expired"
JobStatus.FILLED    # "filled"
JobStatus.DELETED   # "deleted"
```

## Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | UUID | Yes | Primary key |
| title | String(200) | Yes | Job title (10-200 chars) |
| company | String(100) | Yes | Company name (2-100 chars) |
| location | String(200) | Yes | Job location |
| remote | Boolean | Yes | Remote work flag |
| job_type | JobType | Yes | Type of employment |
| experience_level | ExperienceLevel | Yes | Required experience level |
| description | Text | Yes | Job description (50-5000 chars) |
| requirements | Array[Text] | No | List of requirements |
| responsibilities | Array[Text] | No | List of responsibilities |
| salary_min | Integer | No | Minimum salary |
| salary_max | Integer | No | Maximum salary |
| salary_currency | String(3) | No | Currency code (default: USD) |
| source_type | SourceType | Yes | Source of the job |
| source_url | Text | No | Original job URL |
| source_platform | String(50) | No | Platform name (LinkedIn, Indeed, etc.) |
| employer_id | UUID | No | Employer ID (for direct posts) |
| quality_score | Float | Yes | Quality score (0-100) |
| status | JobStatus | Yes | Current status |
| posted_at | DateTime | Yes | When job was posted |
| expires_at | DateTime | Yes | When job expires |
| created_at | DateTime | Yes | Record creation time |
| updated_at | DateTime | Yes | Last update time |
| application_count | Integer | Yes | Number of applications |
| view_count | Integer | Yes | Number of views |
| featured | Boolean | Yes | Featured listing flag |
| tags | Array[String(50)] | No | Categorization tags |

## Validation Rules

### Automatic Constraints
- Title: 10-200 characters
- Company: 2-100 characters
- Description: 50-5000 characters
- Salary: min < max (if both provided)
- Quality score: 0-100
- Application count: >= 0
- View count: >= 0
- Expiration: must be after posted date
- Expiration: within 90 days of posting

## Helper Methods

### is_active()
Check if job is currently active.
```python
if job.is_active():
    print("Job is active and accepting applications")
```

### is_expired()
Check if job has expired.
```python
if job.is_expired():
    print("Job has expired")
```

### days_until_expiration()
Get days until job expires.
```python
days = job.days_until_expiration()
print(f"Job expires in {days} days")
```

### is_direct_post()
Check if job is a direct employer post.
```python
if job.is_direct_post():
    print("This is a direct employer post")
```

### can_receive_applications()
Check if job can receive applications.
```python
if job.can_receive_applications():
    print("Job can receive applications")
```

## Common Queries

### Get Active Jobs
```python
from datetime import datetime
from app.models import Job, JobStatus

active_jobs = session.query(Job).filter(
    Job.status == JobStatus.ACTIVE,
    Job.expires_at > datetime.now()
).all()
```

### Search by Title (Full-Text)
```python
from sqlalchemy import func

results = session.query(Job).filter(
    func.to_tsvector('english', Job.title).match('software engineer')
).all()
```

### Get Jobs by Company
```python
jobs = session.query(Job).filter(
    Job.company == "Tech Corp"
).all()
```

### Get Featured Jobs
```python
featured_jobs = session.query(Job).filter(
    Job.featured == True,
    Job.status == JobStatus.ACTIVE
).order_by(Job.quality_score.desc()).all()
```

### Get Jobs by Employer
```python
employer_jobs = session.query(Job).filter(
    Job.employer_id == employer_id,
    Job.status == JobStatus.ACTIVE
).order_by(Job.posted_at.desc()).all()
```

### Search with Filters
```python
from datetime import datetime, timedelta

jobs = session.query(Job).filter(
    Job.status == JobStatus.ACTIVE,
    Job.job_type == JobType.FULL_TIME,
    Job.experience_level == ExperienceLevel.SENIOR,
    Job.remote == True,
    Job.salary_min >= 100000,
    Job.posted_at >= datetime.now() - timedelta(days=7)
).order_by(
    Job.quality_score.desc(),
    Job.posted_at.desc()
).all()
```

## Creating Jobs

### Direct Employer Post
```python
from datetime import datetime, timedelta
import uuid

job = Job(
    id=uuid.uuid4(),
    title="Senior Software Engineer",
    company="Tech Corp",
    location="San Francisco, CA",
    remote=True,
    job_type=JobType.FULL_TIME,
    experience_level=ExperienceLevel.SENIOR,
    description="We are looking for a senior software engineer...",
    requirements=["Python", "FastAPI", "PostgreSQL"],
    responsibilities=["Design APIs", "Write tests"],
    salary_min=120000,
    salary_max=180000,
    salary_currency="USD",
    source_type=SourceType.DIRECT,
    employer_id=employer_id,
    quality_score=85.0,
    status=JobStatus.ACTIVE,
    posted_at=datetime.now(),
    expires_at=datetime.now() + timedelta(days=30),
    tags=["python", "backend"]
)

session.add(job)
session.commit()
```

### Aggregated Job
```python
job = Job(
    id=uuid.uuid4(),
    title="Software Engineer",
    company="Another Corp",
    location="Remote",
    remote=True,
    job_type=JobType.FULL_TIME,
    experience_level=ExperienceLevel.MID,
    description="Join our team as a software engineer...",
    source_type=SourceType.AGGREGATED,
    source_url="https://linkedin.com/jobs/12345",
    source_platform="LinkedIn",
    quality_score=45.0,
    status=JobStatus.ACTIVE,
    posted_at=datetime.now(),
    expires_at=datetime.now() + timedelta(days=30)
)

session.add(job)
session.commit()
```

## Updating Jobs

### Update Status
```python
job.status = JobStatus.FILLED
session.commit()
```

### Increment View Count
```python
job.view_count += 1
session.commit()
```

### Mark as Featured
```python
job.featured = True
session.commit()
```

## Indexes

The Job model has the following indexes for optimal query performance:

### Single Column Indexes
- id (primary key)
- title
- company
- status
- quality_score
- posted_at
- source_type

### Composite Indexes
- (status, quality_score, posted_at) - for search ranking
- (employer_id, status) - for employer dashboard

### Full-Text Search Indexes (GIN)
- title - for full-text search on job titles
- description - for full-text search on job descriptions

## Best Practices

1. **Always set expiration date**: Ensure expires_at is set and within 90 days
2. **Use quality scoring**: Set appropriate quality_score based on source type
3. **Validate before insert**: Check field lengths and constraints
4. **Use full-text search**: Leverage GIN indexes for text search
5. **Filter by status**: Always filter by status for user-facing queries
6. **Check expiration**: Use is_active() or is_expired() methods
7. **Index usage**: Structure queries to use composite indexes

## Performance Tips

1. Use composite index for search ranking:
   ```python
   .filter(Job.status == JobStatus.ACTIVE)
   .order_by(Job.quality_score.desc(), Job.posted_at.desc())
   ```

2. Use full-text search for text queries:
   ```python
   func.to_tsvector('english', Job.title).match('search terms')
   ```

3. Limit results with pagination:
   ```python
   .limit(20).offset(page * 20)
   ```

4. Use select_related for joins (when implemented):
   ```python
   .options(joinedload(Job.employer))
   ```

## Migration

Apply the migration:
```bash
alembic upgrade head
```

Rollback:
```bash
alembic downgrade -1
```

## Testing

Run tests:
```bash
pytest tests/test_job_model.py -v
```
