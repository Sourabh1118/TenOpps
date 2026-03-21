# JobSource Model Guide

## Overview

The JobSource model tracks the origin of each job posting in the platform. It supports multiple sources per job, enabling deduplication tracking when the same job appears from different platforms (LinkedIn, Indeed, Naukri, Monster, etc.). This model is essential for the job aggregation system to maintain source provenance and track job freshness across platforms.

## Model Structure

### Fields

#### Primary Key
- **id** (UUID): Unique identifier for the job source record

#### Foreign Keys
- **job_id** (UUID): Reference to the Job this source belongs to
  - Foreign key constraint with CASCADE delete
  - Indexed for efficient source lookups

#### Source Information
- **source_platform** (String, max 50 chars): Platform name
  - Examples: "LinkedIn", "Indeed", "Naukri", "Monster", "Glassdoor"
  - Required field
- **source_url** (String, max 2048 chars): Original job URL
  - Full URL to the job posting on the source platform
  - Required field
  - Used for verification and user redirection
- **source_job_id** (String, max 255 chars): External platform's job ID
  - Optional field
  - Platform-specific identifier (e.g., LinkedIn job ID)
  - Useful for API-based scraping

#### Tracking Timestamps
- **scraped_at** (DateTime with timezone): When the job was first scraped
  - Default: current timestamp
  - Immutable after creation
- **last_verified_at** (DateTime with timezone): Last verification timestamp
  - Default: current timestamp
  - Updated when job is re-scraped and still active

#### Status
- **is_active** (Boolean): Whether the job is still available on source
  - Default: True
  - Set to False when job is no longer found on source platform
  - Used for freshness tracking

### Indexes

1. **idx_job_sources_id**: Primary key index
2. **idx_job_sources_job_id**: Foreign key index for source lookups
   - **Required by task specification**
   - Optimizes queries to find all sources for a job
3. **idx_job_sources_platform_active**: Composite index on (source_platform, is_active)
   - Optimizes platform-specific queries
   - Enables efficient active source filtering
4. **idx_job_sources_last_verified**: Index on last_verified_at
   - Supports freshness tracking queries
   - Identifies stale sources needing re-verification

## Use Cases

### 1. Deduplication Tracking
When the same job appears on multiple platforms, each source is tracked separately:

```
Job: "Senior Software Engineer at TechCorp"
├── Source 1: LinkedIn (scraped 2024-03-15)
├── Source 2: Indeed (scraped 2024-03-16)
└── Source 3: Naukri (scraped 2024-03-17)
```

### 2. Freshness Tracking
Track when jobs were last seen on each platform to identify expired postings:

```python
# Find sources that haven't been verified in 7 days
stale_sources = db.query(JobSource).filter(
    JobSource.last_verified_at < datetime.now() - timedelta(days=7)
).all()
```

### 3. Source Attribution
Display to users where a job was found and provide links to original postings.

## Helper Methods

### is_stale(days=7)
Returns `True` if the source hasn't been verified within the specified number of days.

```python
# Check if source is stale (default: 7 days)
if job_source.is_stale():
    print("Source needs re-verification")

# Check with custom threshold
if job_source.is_stale(days=3):
    print("Source is stale (>3 days)")
```

### mark_verified()
Updates the last_verified_at timestamp to the current time.

```python
# After successful re-scraping
job_source.mark_verified()
db.commit()
```

### mark_inactive()
Sets is_active to False when the job is no longer available on the source.

```python
# Job not found during re-scraping
job_source.mark_inactive()
db.commit()
```

## Usage Examples

### Creating a Job Source

```python
from app.models.job_source import JobSource
import uuid

# Create a new job source when scraping
job_source = JobSource(
    id=uuid.uuid4(),
    job_id=job.id,
    source_platform="LinkedIn",
    source_url="https://www.linkedin.com/jobs/view/123456789",
    source_job_id="123456789"
)

db.add(job_source)
db.commit()
```

### Tracking Multiple Sources (Deduplication)

```python
# Job found on multiple platforms
sources = [
    JobSource(
        job_id=job.id,
        source_platform="LinkedIn",
        source_url="https://www.linkedin.com/jobs/view/123456"
    ),
    JobSource(
        job_id=job.id,
        source_platform="Indeed",
        source_url="https://www.indeed.com/viewjob?jk=abc123"
    ),
    JobSource(
        job_id=job.id,
        source_platform="Naukri",
        source_url="https://www.naukri.com/job-listings/xyz789"
    ),
]

db.add_all(sources)
db.commit()
```

### Querying Job Sources

```python
from sqlalchemy import and_

# Get all sources for a job
sources = db.query(JobSource).filter(
    JobSource.job_id == job_id
).all()

# Get active sources for a job
active_sources = db.query(JobSource).filter(
    and_(
        JobSource.job_id == job_id,
        JobSource.is_active == True
    )
).all()

# Get all jobs from a specific platform
linkedin_sources = db.query(JobSource).filter(
    JobSource.source_platform == "LinkedIn"
).all()

# Find stale sources needing verification
stale_sources = db.query(JobSource).filter(
    JobSource.last_verified_at < datetime.now() - timedelta(days=7)
).all()

# Get sources by platform that are active
active_indeed = db.query(JobSource).filter(
    and_(
        JobSource.source_platform == "Indeed",
        JobSource.is_active == True
    )
).all()
```

### Freshness Tracking Workflow

```python
# During scheduled re-scraping
for source in sources_to_verify:
    try:
        # Attempt to fetch job from source URL
        job_data = scraper.fetch_job(source.source_url)
        
        if job_data:
            # Job still exists
            source.mark_verified()
        else:
            # Job no longer available
            source.mark_inactive()
            
        db.commit()
    except Exception as e:
        logger.error(f"Failed to verify source {source.id}: {e}")
```

### Using Helper Methods

```python
# Check if source needs re-verification
if source.is_stale(days=7):
    # Queue for re-scraping
    scraping_queue.add(source.source_url)

# After successful re-scraping
source.mark_verified()
db.commit()

# Job no longer found on platform
if not job_found:
    source.mark_inactive()
    db.commit()
    
    # Check if job has any active sources
    active_count = db.query(JobSource).filter(
        and_(
            JobSource.job_id == source.job_id,
            JobSource.is_active == True
        )
    ).count()
    
    if active_count == 0:
        # No active sources, mark job as expired
        job.status = JobStatus.EXPIRED
        db.commit()
```

## Integration with Job Aggregation System

### Scraping Flow

```python
async def scrape_and_process_job(raw_job_data, source_platform):
    # Normalize job data
    normalized_job = normalize_job_data(raw_job_data)
    
    # Check for duplicates
    duplicates = await find_duplicates(normalized_job)
    
    if duplicates:
        # Job already exists, add new source
        existing_job_id = duplicates[0]
        job_source = JobSource(
            job_id=existing_job_id,
            source_platform=source_platform,
            source_url=raw_job_data['url'],
            source_job_id=raw_job_data.get('job_id')
        )
        db.add(job_source)
    else:
        # New job, create job and source
        job = Job(**normalized_job)
        db.add(job)
        db.flush()  # Get job.id
        
        job_source = JobSource(
            job_id=job.id,
            source_platform=source_platform,
            source_url=raw_job_data['url'],
            source_job_id=raw_job_data.get('job_id')
        )
        db.add(job_source)
    
    db.commit()
```

### Deduplication Support

```python
def get_job_sources(job_id):
    """Get all sources for a job to display provenance."""
    sources = db.query(JobSource).filter(
        JobSource.job_id == job_id
    ).all()
    
    return {
        'total_sources': len(sources),
        'active_sources': sum(1 for s in sources if s.is_active),
        'platforms': [s.source_platform for s in sources],
        'urls': [s.source_url for s in sources]
    }
```

## Validation Rules

### Database Constraints

1. **Foreign Key Constraint**: job_id must reference an existing job
   - CASCADE delete: Sources are deleted when the job is deleted
2. **Required Fields**: job_id, source_platform, source_url must be provided
3. **URL Length**: source_url limited to 2048 characters (standard URL max)
4. **Platform Name**: source_platform limited to 50 characters

### Application Logic Validation

1. **Unique Source URLs**: Prevent duplicate source URLs for the same job
2. **Valid URLs**: Validate source_url format before insertion
3. **Platform Whitelist**: Validate source_platform against known platforms
4. **Timestamp Logic**: scraped_at should not be modified after creation

## Performance Considerations

### Indexing Strategy
- Index on job_id enables fast source lookups for a job
- Composite index on (source_platform, is_active) optimizes platform queries
- Index on last_verified_at supports freshness tracking queries

### Query Optimization
- Use job_id index for source lookups: `WHERE job_id = ?`
- Use composite index for platform queries: `WHERE source_platform = ? AND is_active = ?`
- Batch load sources when displaying job listings

### Scalability
- JobSources table grows with each scraping run
- Consider partitioning by source_platform for very large datasets
- Archive inactive sources older than 6 months

## Testing

### Unit Tests
See `tests/test_job_source_model.py` for comprehensive test coverage:
- Model creation with required fields
- Optional fields (source_job_id)
- Foreign key constraints
- Cascade delete behavior
- Multiple sources per job (deduplication)
- Helper methods (is_stale, mark_verified, mark_inactive)
- Timestamps and defaults
- Platform tracking

### Integration Tests
- Scraping workflow with source creation
- Deduplication with multiple sources
- Freshness tracking and re-verification
- Source attribution in job listings

## Migration

The JobSource model is created by migration `004_create_job_sources_table.py`.

### Running the Migration

```bash
# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Migration Details
- Creates `job_sources` table with all fields and constraints
- Creates foreign key constraint with CASCADE delete
- Creates all indexes including:
  - Primary key index
  - job_id index (required by task)
  - Composite platform/active index
  - last_verified_at index

## Best Practices

1. **Source Tracking**: Always create a JobSource record when scraping a job
2. **Deduplication**: Check for existing jobs before creating new ones
3. **Freshness**: Regularly re-verify sources to maintain data quality
4. **Inactive Sources**: Mark sources as inactive rather than deleting them
5. **URL Validation**: Validate source URLs before insertion
6. **Platform Names**: Use consistent platform naming (e.g., "LinkedIn" not "linkedin")
7. **Batch Operations**: Use bulk inserts for multiple sources
8. **Monitoring**: Track source verification success rates per platform

## Related Documentation

- [Job Model Guide](./JOB_MODEL_GUIDE.md)
- [Database Setup](./DATABASE_SETUP.md)
- [Database Quick Start](./DATABASE_QUICK_START.md)
- Requirements 1.7, 2.8 (Job Aggregation and Deduplication)

## Requirements Validation

This model satisfies the following requirements:

### Requirement 1.7 (Automated Job Aggregation)
- Tracks source platform for each scraped job
- Stores original source URL for attribution
- Records scraping timestamp

### Requirement 2.8 (Job Deduplication)
- Supports multiple sources per job
- Enables tracking when same job appears from different platforms
- Maintains source provenance for merged jobs
