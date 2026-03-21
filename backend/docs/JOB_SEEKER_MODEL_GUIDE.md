# JobSeeker Model Guide

## Overview

The `JobSeeker` model represents users who search for and apply to jobs on the platform. It stores authentication credentials, profile information, and supports application tracking.

## Model Structure

### Fields

#### Primary Key
- **id**: UUID - Unique identifier for the job seeker

#### Authentication
- **email**: String(255) - Unique email address for login (indexed)
- **password_hash**: String(255) - Bcrypt hashed password (cost factor 12)

#### Profile Information
- **full_name**: String(100) - Job seeker's full name (2-100 characters)
- **phone**: String(20) - Optional phone number
- **resume_url**: String(500) - Optional URL to default resume file
- **profile_summary**: Text - Optional profile summary/bio

#### Timestamps
- **created_at**: DateTime - Account creation timestamp
- **updated_at**: DateTime - Last update timestamp (auto-updated)

## Validation Rules

### Email
- **Format**: Must match email regex pattern
- **Uniqueness**: Must be unique across all job seekers
- **Example**: `john.doe@example.com`

### Full Name
- **Length**: 2-100 characters
- **Required**: Yes
- **Example**: `John Doe`

### Phone
- **Format**: Must match phone regex pattern (if provided)
- **Pattern**: `^[+]?[0-9\s\-\(\)]{7,20}$`
- **Optional**: Yes
- **Examples**: 
  - `+1-555-0100`
  - `(555) 123-4567`
  - `+44 20 7946 0958`

### Resume URL
- **Format**: Must be valid HTTP/HTTPS URL (if provided)
- **Optional**: Yes
- **Example**: `https://storage.example.com/resumes/john-doe.pdf`

## Indexes

1. **idx_job_seekers_id**: Primary key index on `id`
2. **idx_job_seekers_email**: Unique index on `email` for authentication queries

## Business Logic Methods

### has_complete_profile()
Returns `True` if all profile fields are filled (full_name, phone, resume_url, profile_summary).

```python
job_seeker = JobSeeker.query.get(job_seeker_id)
if job_seeker.has_complete_profile():
    print("Profile is complete")
```

### can_apply()
Returns `True` if the job seeker has a resume uploaded (required for applications).

```python
job_seeker = JobSeeker.query.get(job_seeker_id)
if job_seeker.can_apply():
    # Allow application submission
    pass
```

## Usage Examples

### Creating a Job Seeker

```python
from app.models.job_seeker import JobSeeker
import bcrypt

# Hash password
password = "secure_password"
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')

# Create job seeker
job_seeker = JobSeeker(
    email="john.doe@example.com",
    password_hash=password_hash,
    full_name="John Doe",
    phone="+1-555-0100",
    resume_url="https://storage.example.com/resumes/john-doe.pdf",
    profile_summary="Experienced software engineer with 5 years in Python and JavaScript"
)

db.session.add(job_seeker)
db.session.commit()
```

### Querying Job Seekers

```python
# Find by email (for authentication)
job_seeker = JobSeeker.query.filter_by(email="john.doe@example.com").first()

# Find by ID
job_seeker = JobSeeker.query.get(job_seeker_id)

# Check if can apply
if job_seeker and job_seeker.can_apply():
    print("Job seeker can submit applications")
```

### Updating Profile

```python
job_seeker = JobSeeker.query.get(job_seeker_id)
job_seeker.phone = "+1-555-0200"
job_seeker.profile_summary = "Updated profile summary"
db.session.commit()
```

## Authentication Flow

### Registration
1. Validate email format and uniqueness
2. Hash password using bcrypt (cost factor 12)
3. Create JobSeeker record with required fields
4. Return success with job seeker ID

### Login
1. Query JobSeeker by email
2. Verify password hash using bcrypt
3. Generate JWT access token (15 minutes)
4. Generate refresh token (7 days)
5. Return tokens to client

## Requirements Mapping

This model satisfies the following requirements:

- **Requirement 7.1**: Job seekers must be authenticated to submit applications
  - Implemented via `email` and `password_hash` fields
  - `can_apply()` method checks for resume requirement

- **Requirement 12.1**: User registration with password hashing
  - Password stored as bcrypt hash with cost factor 12
  - Email has unique constraint
  - Email format validation via check constraint

## Database Migration

The migration file `006_create_job_seekers_table.py` creates:
- The `job_seekers` table with all fields
- Unique constraint on email
- Check constraints for validation
- Indexes for efficient authentication queries

To apply the migration:
```bash
alembic upgrade head
```

To rollback:
```bash
alembic downgrade -1
```

## Testing

Unit tests are located in `tests/test_job_seeker_model.py` and cover:
- Model creation with all fields
- Model creation with minimal fields
- Email uniqueness constraint
- Email format validation
- Full name length validation
- Phone format validation
- Resume URL format validation
- `has_complete_profile()` method
- `can_apply()` method
- Timestamp auto-generation
- Password hash storage

Run tests:
```bash
pytest tests/test_job_seeker_model.py -v
```

## Security Considerations

1. **Password Storage**: Never store plain text passwords. Always use bcrypt with cost factor 12.
2. **Email Validation**: Email format is validated at database level, but additional validation should be done at API level.
3. **Authentication**: Use JWT tokens with short expiration times (15 minutes for access tokens).
4. **Rate Limiting**: Implement rate limiting on login endpoints to prevent brute force attacks.
5. **Email Verification**: Consider implementing email verification before allowing applications.

## Related Models

- **Application**: Job seekers create applications (via `job_seeker_id` foreign key)
- **Job**: Job seekers apply to jobs (indirect relationship through Application)

## Future Enhancements

1. Add email verification status field
2. Add profile completion percentage
3. Add skills and experience fields
4. Add saved jobs functionality
5. Add application history tracking
6. Add notification preferences
