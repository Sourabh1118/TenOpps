# Application Model Guide

## Overview

The Application model tracks job applications from job seekers to direct-posted jobs. It supports application status management, resume and cover letter storage, and employer notes for tracking the hiring process.

## Model Structure

### Fields

#### Primary Key
- **id** (UUID): Unique identifier for the application

#### Foreign Keys
- **job_id** (UUID): Reference to the Job being applied to
  - Foreign key constraint with CASCADE delete
  - Indexed for efficient queries
- **job_seeker_id** (UUID): Reference to the job seeker (user)
  - Indexed for job seeker queries

#### Application Materials
- **resume** (String, max 500 chars): URL to the resume file
  - Required field
  - Stored in external storage (e.g., Supabase Storage)
- **cover_letter** (Text): Optional cover letter text
  - Can be null

#### Status Tracking
- **status** (Enum): Current application status
  - Values: SUBMITTED, REVIEWED, SHORTLISTED, REJECTED, ACCEPTED
  - Default: SUBMITTED
  - Indexed for filtering

#### Employer Notes
- **employer_notes** (Text): Optional notes from the employer
  - Used for internal tracking and communication

#### Timestamps
- **applied_at** (DateTime with timezone): When the application was submitted
  - Default: current timestamp
  - Cannot be modified
- **updated_at** (DateTime with timezone): Last update timestamp
  - Default: current timestamp
  - Auto-updated on changes

### Indexes

1. **idx_applications_id**: Primary key index
2. **idx_applications_job_id**: Foreign key index for job lookups
3. **idx_applications_job_seeker_id**: Index for job seeker queries
4. **idx_applications_status**: Index for status filtering
5. **idx_applications_job_status**: Composite index on (job_id, status)
   - Optimizes employer queries for applications by job and status
6. **idx_applications_job_seeker**: Index for job seeker application history

## Application Status Enum

```python
class ApplicationStatus(str, enum.Enum):
    SUBMITTED = "submitted"      # Initial state when application is submitted
    REVIEWED = "reviewed"        # Employer has reviewed the application
    SHORTLISTED = "shortlisted"  # Candidate is shortlisted for interview
    REJECTED = "rejected"        # Application was rejected
    ACCEPTED = "accepted"        # Candidate was accepted/hired
```

### Status Flow

```
SUBMITTED → REVIEWED → SHORTLISTED → ACCEPTED
                    ↘ REJECTED
```

## Helper Methods

### is_pending()
Returns `True` if the application status is SUBMITTED (pending initial review).

```python
application.is_pending()  # True if status == SUBMITTED
```

### is_active()
Returns `True` if the application is in an active state (not in a final state).

Active states: SUBMITTED, REVIEWED, SHORTLISTED
Inactive states: REJECTED, ACCEPTED

```python
application.is_active()  # True if not rejected or accepted
```

### is_final()
Returns `True` if the application has reached a final state.

Final states: REJECTED, ACCEPTED

```python
application.is_final()  # True if rejected or accepted
```

## Usage Examples

### Creating an Application

```python
from app.models.application import Application, ApplicationStatus
import uuid

# Create a new application
application = Application(
    id=uuid.uuid4(),
    job_id=job.id,
    job_seeker_id=user.id,
    resume="https://storage.example.com/resumes/user123_resume.pdf",
    cover_letter="I am very interested in this position...",
    status=ApplicationStatus.SUBMITTED
)

db.add(application)
db.commit()
```

### Updating Application Status

```python
# Employer reviews application
application.status = ApplicationStatus.REVIEWED
application.employer_notes = "Strong technical background, schedule phone screen"
db.commit()

# Shortlist candidate
application.status = ApplicationStatus.SHORTLISTED
application.employer_notes += "\nPhone screen went well, schedule onsite"
db.commit()

# Final decision
application.status = ApplicationStatus.ACCEPTED
application.employer_notes += "\nExtended offer"
db.commit()
```

### Querying Applications

```python
from sqlalchemy import and_

# Get all applications for a job
applications = db.query(Application).filter(
    Application.job_id == job_id
).all()

# Get applications by status for a job
pending_applications = db.query(Application).filter(
    and_(
        Application.job_id == job_id,
        Application.status == ApplicationStatus.SUBMITTED
    )
).all()

# Get all applications for a job seeker
my_applications = db.query(Application).filter(
    Application.job_seeker_id == user_id
).order_by(Application.applied_at.desc()).all()

# Get active applications for a job
active_applications = db.query(Application).filter(
    and_(
        Application.job_id == job_id,
        Application.status.in_([
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.REVIEWED,
            ApplicationStatus.SHORTLISTED
        ])
    )
).all()
```

### Using Helper Methods

```python
# Check application state
if application.is_pending():
    print("Application is awaiting initial review")

if application.is_active():
    print("Application is still in progress")
    # Allow status updates
else:
    print("Application has been finalized")
    # Prevent further status changes

if application.is_final():
    print("Application process is complete")
    # Send notification to job seeker
```

## Validation Rules

### Database Constraints

1. **Foreign Key Constraint**: job_id must reference an existing job
   - CASCADE delete: Applications are deleted when the job is deleted
2. **Required Fields**: job_id, job_seeker_id, resume, status must be provided
3. **Status Enum**: status must be one of the valid ApplicationStatus values

### Application Logic Validation

1. **Job Type Validation**: Applications can only be submitted to direct-posted jobs
   - Aggregated and URL-imported jobs should redirect to external application pages
2. **Duplicate Prevention**: Prevent multiple applications from the same job seeker to the same job
3. **Status Transitions**: Validate status transitions follow logical flow
   - Cannot go from REJECTED/ACCEPTED back to earlier states
4. **Resume URL**: Must be a valid URL pointing to stored file
5. **Job Status**: Can only apply to ACTIVE jobs

## Integration with Other Models

### Job Model
- Applications reference jobs via job_id foreign key
- When a job is deleted, all its applications are cascade deleted
- Job model tracks application_count for direct posts

### Employer Model
- Employers can view applications for their jobs
- Access to application tracking requires BASIC or PREMIUM subscription tier
- Employers can add notes and update application status

### Job Seeker (User) Model
- Job seekers can view their application history
- Track application status changes
- Receive notifications on status updates

## API Endpoints (Future Implementation)

### Job Seeker Endpoints
- `POST /api/applications` - Submit a new application
- `GET /api/applications` - Get my applications
- `GET /api/applications/:id` - Get application details

### Employer Endpoints
- `GET /api/jobs/:jobId/applications` - Get applications for a job
- `PATCH /api/applications/:id` - Update application status
- `POST /api/applications/:id/notes` - Add employer notes

## Performance Considerations

### Indexing Strategy
- Composite index on (job_id, status) optimizes employer dashboard queries
- Index on job_seeker_id enables fast job seeker application history retrieval
- Status index supports filtering by application state

### Query Optimization
- Use composite index for employer queries: `WHERE job_id = ? AND status = ?`
- Batch load applications when displaying job listings
- Cache application counts per job

### Scalability
- Applications table can grow large (millions of records)
- Consider partitioning by date (applied_at) for very large datasets
- Archive old applications (>1 year) to separate table

## Testing

### Unit Tests
See `tests/test_application_model.py` for comprehensive test coverage:
- Model creation with required fields
- Optional fields (cover_letter, employer_notes)
- Status enum values
- Helper methods (is_pending, is_active, is_final)
- Foreign key constraints
- Cascade delete behavior
- Timestamps and defaults

### Integration Tests
- Application submission flow
- Status update workflow
- Employer application management
- Job seeker application tracking

## Migration

The Application model is created by migration `003_create_applications_table.py`.

### Running the Migration

```bash
# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Migration Details
- Creates `applications` table with all fields and constraints
- Creates `applicationstatus` enum type
- Creates all indexes including composite index
- Sets up foreign key constraint with CASCADE delete

## Best Practices

1. **Status Transitions**: Implement validation logic to ensure valid status transitions
2. **Notifications**: Send notifications to job seekers when status changes
3. **Audit Trail**: Consider adding a separate table for status change history
4. **File Storage**: Store resumes in secure, scalable storage (e.g., Supabase Storage)
5. **Privacy**: Ensure job seekers can only view their own applications
6. **Access Control**: Verify employers can only access applications for their jobs
7. **Soft Deletes**: Consider soft deletes for applications to maintain history
8. **Analytics**: Track application metrics (time to review, acceptance rate, etc.)

## Related Documentation

- [Job Model Guide](./JOB_MODEL_GUIDE.md)
- [Employer Model Guide](./EMPLOYER_MODEL_GUIDE.md)
- [Database Setup](./DATABASE_SETUP.md)
- [Database Quick Start](./DATABASE_QUICK_START.md)
