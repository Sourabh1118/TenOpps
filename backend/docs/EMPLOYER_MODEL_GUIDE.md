# Employer Model Guide

This guide provides comprehensive documentation for the Employer model in the Job Aggregation Platform.

## Overview

The Employer model represents registered employers who can post jobs, manage applications, and access platform features based on their subscription tier. It includes authentication fields, company information, subscription management, and usage tracking for quota enforcement.

## Model Structure

### Location
- **File**: `backend/app/models/employer.py`
- **Table**: `employers`
- **Migration**: `backend/alembic/versions/002_create_employers_table.py`

### Fields

#### Primary Key
- **id**: UUID (auto-generated)
  - Primary key for the employer
  - Indexed for fast lookups

#### Authentication
- **email**: String(255), required, unique
  - Employer's email address for login
  - Must be valid email format (validated by check constraint)
  - Indexed for authentication queries
  
- **password_hash**: String(255), required
  - Bcrypt hashed password (never store plain text)
  - Cost factor: 12 (as per security requirements)

#### Company Information
- **company_name**: String(100), required
  - Company name (2-100 characters)
  - Validated by check constraint
  
- **company_website**: String(500), optional
  - Company website URL
  - Must start with http:// or https:// if provided
  - Validated by check constraint
  
- **company_logo**: String(500), optional
  - URL to company logo image
  
- **company_description**: Text, optional
  - Detailed company description

#### Subscription Management
- **subscription_tier**: Enum(SubscriptionTier), required
  - Default: FREE
  - Values: FREE, BASIC, PREMIUM
  - Indexed for subscription queries
  
- **subscription_start_date**: DateTime(timezone=True), required
  - Default: current timestamp
  - When the current subscription started
  
- **subscription_end_date**: DateTime(timezone=True), required
  - When the current subscription expires
  - Must be after subscription_start_date (validated by check constraint)

#### Usage Tracking
- **monthly_posts_used**: Integer, required
  - Default: 0
  - Number of jobs posted in current billing cycle
  - Must be non-negative (validated by check constraint)
  - Reset monthly
  
- **featured_posts_used**: Integer, required
  - Default: 0
  - Number of featured posts used in current billing cycle
  - Must be non-negative (validated by check constraint)
  - Reset monthly

#### Payment Integration
- **stripe_customer_id**: String(255), optional, unique
  - Stripe customer ID for payment processing
  - Unique to prevent duplicate payment accounts

#### Account Status
- **verified**: Boolean, required
  - Default: false
  - Whether the employer's email is verified
  - Indexed for filtering verified accounts

#### Timestamps
- **created_at**: DateTime(timezone=True), required
  - Default: current timestamp
  - When the employer account was created
  
- **updated_at**: DateTime(timezone=True), required
  - Default: current timestamp
  - Auto-updated on record modification

## Subscription Tiers

### FREE Tier
- **Monthly Posts**: 3
- **Featured Posts**: 0
- **Application Tracking**: No
- **Analytics Access**: No
- **Cost**: $0/month

### BASIC Tier
- **Monthly Posts**: 20
- **Featured Posts**: 2
- **Application Tracking**: Yes
- **Analytics Access**: No
- **Cost**: $29/month (example)

### PREMIUM Tier
- **Monthly Posts**: Unlimited
- **Featured Posts**: 10
- **Application Tracking**: Yes
- **Analytics Access**: Yes
- **Cost**: $99/month (example)

## Validation Constraints

### Email Format
```sql
email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
```
- Must be valid email format
- Case-insensitive regex validation

### Company Name Length
```sql
char_length(company_name) >= 2 AND char_length(company_name) <= 100
```
- Minimum: 2 characters
- Maximum: 100 characters

### Company Website URL
```sql
company_website IS NULL OR company_website ~* '^https?://.+'
```
- Must start with http:// or https://
- Can be NULL

### Usage Counters
```sql
monthly_posts_used >= 0
featured_posts_used >= 0
```
- Both must be non-negative

### Subscription Dates
```sql
subscription_end_date > subscription_start_date
```
- End date must be after start date

## Indexes

### Single Column Indexes
1. **idx_employers_id**: Primary key index
2. **idx_employers_email**: Unique index for authentication
3. **idx_employers_subscription_tier**: For filtering by tier
4. **idx_employers_verified**: For filtering verified accounts

### Composite Indexes
1. **idx_employers_subscription_status**: (subscription_tier, subscription_end_date)
   - Optimizes subscription management queries
   - Used for finding expired subscriptions

## Helper Methods

### is_subscription_active()
```python
def is_subscription_active(self) -> bool:
    """Check if the employer's subscription is currently active."""
    return self.subscription_end_date > datetime.now()
```
Returns True if subscription hasn't expired.

### get_monthly_post_limit()
```python
def get_monthly_post_limit(self) -> int:
    """Get the monthly post limit based on subscription tier."""
```
Returns:
- FREE: 3
- BASIC: 20
- PREMIUM: float('inf') (unlimited)

### get_featured_post_limit()
```python
def get_featured_post_limit(self) -> int:
    """Get the featured post limit based on subscription tier."""
```
Returns:
- FREE: 0
- BASIC: 2
- PREMIUM: 10

### can_post_job()
```python
def can_post_job(self) -> bool:
    """Check if employer can post a new job based on quota."""
```
Returns True if:
- Subscription is active AND
- monthly_posts_used < monthly post limit

### can_feature_job()
```python
def can_feature_job(self) -> bool:
    """Check if employer can feature a job based on quota."""
```
Returns True if:
- Subscription is active AND
- featured_posts_used < featured post limit

### has_application_tracking()
```python
def has_application_tracking(self) -> bool:
    """Check if employer has access to application tracking."""
```
Returns True for BASIC and PREMIUM tiers.

### has_analytics_access()
```python
def has_analytics_access(self) -> bool:
    """Check if employer has access to analytics."""
```
Returns True only for PREMIUM tier.

## Usage Examples

### Creating an Employer

```python
from app.models import Employer, SubscriptionTier
from datetime import datetime, timedelta

# Create a new employer with free tier
employer = Employer(
    email="employer@company.com",
    password_hash="$2b$12$...",  # Use bcrypt to hash password
    company_name="Tech Startup Inc",
    company_website="https://techstartup.com",
    subscription_end_date=datetime.now() + timedelta(days=30)
)

db.add(employer)
db.commit()
```

### Checking Quota Before Posting

```python
# Check if employer can post a job
if employer.can_post_job():
    # Create job
    job = Job(...)
    db.add(job)
    
    # Increment usage counter
    employer.monthly_posts_used += 1
    db.commit()
else:
    raise HTTPException(
        status_code=403,
        detail="Monthly posting quota exceeded"
    )
```

### Upgrading Subscription

```python
from datetime import datetime, timedelta

# Upgrade to premium tier
employer.subscription_tier = SubscriptionTier.PREMIUM
employer.subscription_start_date = datetime.now()
employer.subscription_end_date = datetime.now() + timedelta(days=365)
employer.stripe_customer_id = "cus_123456789"

db.commit()
```

### Resetting Monthly Quotas

```python
# Reset quotas at start of billing cycle (run as scheduled task)
employer.monthly_posts_used = 0
employer.featured_posts_used = 0
db.commit()
```

### Checking Feature Access

```python
# Check if employer can access application tracking
if employer.has_application_tracking():
    applications = db.query(Application).filter(
        Application.job_id.in_(employer_job_ids)
    ).all()
else:
    raise HTTPException(
        status_code=403,
        detail="Application tracking requires Basic or Premium tier"
    )
```

## Database Migration

### Running the Migration

```bash
# Apply the migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### Migration Details

The migration creates:
1. `subscriptiontier` enum type
2. `employers` table with all fields
3. Check constraints for validation
4. Indexes for query performance

## Testing

### Running Tests

```bash
# Run all employer model tests
pytest tests/test_employer_model.py -v

# Run specific test class
pytest tests/test_employer_model.py::TestEmployerModel -v

# Run with coverage
pytest tests/test_employer_model.py --cov=app.models.employer
```

### Test Coverage

The test suite covers:
- Model creation with required and optional fields
- Email uniqueness constraint
- Company name length validation
- Company website URL validation
- Usage counter non-negative constraints
- Subscription date validation
- Subscription tier logic
- Quota enforcement
- Feature access control
- Helper methods

## Integration with Other Models

### Relationship with Job Model

```python
# In Job model (to be added)
employer_id = Column(UUID(as_uuid=True), ForeignKey('employers.id'), nullable=True)
employer = relationship("Employer", back_populates="jobs")

# In Employer model (to be added)
jobs = relationship("Job", back_populates="employer")
```

### Relationship with Application Model

```python
# Applications are accessed through jobs
employer_jobs = db.query(Job).filter(Job.employer_id == employer.id).all()
job_ids = [job.id for job in employer_jobs]
applications = db.query(Application).filter(Application.job_id.in_(job_ids)).all()
```

## Security Considerations

### Password Hashing

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password
password_hash = pwd_context.hash("plain_password")

# Verify password
is_valid = pwd_context.verify("plain_password", password_hash)
```

### Email Verification

```python
# Generate verification token
import secrets
verification_token = secrets.token_urlsafe(32)

# Send verification email
send_verification_email(employer.email, verification_token)

# Verify email
employer.verified = True
db.commit()
```

### Rate Limiting

Implement rate limiting on authentication endpoints:
- Login: 5 attempts per 15 minutes
- Registration: 3 attempts per hour
- Password reset: 3 attempts per hour

## Common Queries

### Find Employer by Email

```python
employer = db.query(Employer).filter(
    Employer.email == "employer@company.com"
).first()
```

### Find Expired Subscriptions

```python
from datetime import datetime

expired_employers = db.query(Employer).filter(
    Employer.subscription_end_date < datetime.now()
).all()
```

### Find Employers by Tier

```python
premium_employers = db.query(Employer).filter(
    Employer.subscription_tier == SubscriptionTier.PREMIUM
).all()
```

### Find Employers Near Quota

```python
# Free tier employers who have used 2+ posts (1 remaining)
near_quota = db.query(Employer).filter(
    Employer.subscription_tier == SubscriptionTier.FREE,
    Employer.monthly_posts_used >= 2
).all()
```

## Troubleshooting

### Issue: Email Already Exists

**Error**: `IntegrityError: duplicate key value violates unique constraint "employers_email_key"`

**Solution**: Check if email exists before creating employer:
```python
existing = db.query(Employer).filter(Employer.email == email).first()
if existing:
    raise HTTPException(status_code=400, detail="Email already registered")
```

### Issue: Invalid Company Website URL

**Error**: `IntegrityError: new row violates check constraint "check_company_website_url"`

**Solution**: Validate URL format before saving:
```python
import re
url_pattern = r'^https?://.+'
if company_website and not re.match(url_pattern, company_website):
    raise ValueError("Website must start with http:// or https://")
```

### Issue: Subscription Date Validation

**Error**: `IntegrityError: new row violates check constraint "check_subscription_dates"`

**Solution**: Ensure end date is after start date:
```python
if subscription_end_date <= subscription_start_date:
    raise ValueError("Subscription end date must be after start date")
```

## Related Documentation

- [Job Model Guide](./JOB_MODEL_GUIDE.md)
- [Database Setup](./DATABASE_SETUP.md)
- [API Authentication](./API_AUTHENTICATION.md) (to be created)
- [Subscription Management](./SUBSCRIPTION_MANAGEMENT.md) (to be created)

## Requirements Mapping

This model satisfies the following requirements:

- **Requirement 8.1**: Subscription Management - Employer subscription tiers and quotas
- **Requirement 12.1**: Authentication and Authorization - Email and password hash fields

See `.kiro/specs/job-aggregation-platform/requirements.md` for full requirement details.
