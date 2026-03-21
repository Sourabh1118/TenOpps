# Developer Documentation

## Overview

This document provides comprehensive technical documentation for developers working on the Job Aggregation Platform. It covers project structure, architecture, coding standards, testing strategy, and contribution guidelines.

## Table of Contents

1. [Project Structure](#project-structure)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Development Setup](#development-setup)
5. [Coding Standards](#coding-standards)
6. [Testing Strategy](#testing-strategy)
7. [Contribution Guidelines](#contribution-guidelines)
8. [API Development](#api-development)
9. [Database Management](#database-management)
10. [Background Tasks](#background-tasks)

---

## Project Structure

### Repository Layout

```
job-aggregation-platform/
├── backend/                 # FastAPI backend
│   ├── alembic/            # Database migrations
│   │   └── versions/       # Migration files
│   ├── app/                # Application code
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core utilities
│   │   ├── db/             # Database configuration
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── tasks/          # Celery tasks
│   ├── docs/               # Backend documentation
│   ├── scripts/            # Utility scripts
│   ├── tests/              # Test files
│   ├── .env.example        # Environment template
│   ├── Dockerfile          # Docker configuration
│   ├── requirements.txt    # Python dependencies
│   └── pytest.ini          # Pytest configuration
├── frontend/               # Next.js frontend
│   ├── app/                # Next.js app directory
│   │   ├── (auth)/         # Auth pages
│   │   ├── employer/       # Employer pages
│   │   ├── jobs/           # Job pages
│   │   └── applications/   # Application pages
│   ├── components/         # React components
│   │   ├── auth/           # Auth components
│   │   ├── employer/       # Employer components
│   │   ├── jobs/           # Job components
│   │   └── layout/         # Layout components
│   ├── lib/                # Utilities
│   │   ├── api/            # API client
│   │   └── validations/    # Form validations
│   ├── public/             # Static assets
│   ├── types/              # TypeScript types
│   ├── .env.local.example  # Environment template
│   ├── next.config.js      # Next.js configuration
│   └── package.json        # Node dependencies
├── docs/                   # Project documentation
├── .github/                # GitHub workflows
└── README.md               # Project readme
```

See full structure details in `backend/PROJECT_STRUCTURE.md` and `frontend/PROJECT_STRUCTURE.md`.

---

## Architecture

### System Architecture

The platform uses a microservices architecture with the following components:

**Frontend Layer**:
- Next.js 14 with App Router
- Server-side rendering (SSR)
- Client-side state management (Zustand)
- API client (Axios with interceptors)

**API Gateway Layer**:
- FastAPI REST API
- JWT authentication
- Rate limiting middleware
- CORS configuration

**Application Services**:
- Job Service: CRUD operations for jobs
- Employer Service: Employer management
- Search Service: Full-text search with filters
- Application Service: Application tracking
- Subscription Service: Tier management

**Background Processing**:
- Celery workers for async tasks
- Celery Beat for scheduled tasks
- Redis as message broker

**Data Layer**:
- PostgreSQL for persistent data
- Redis for caching and task queue
- Supabase Storage for file uploads

**External Services**:
- Stripe for payments
- Sentry for error tracking
- Email service (SMTP)
- Slack for alerts

### Data Flow

```
User Request → Frontend → API Gateway → Service Layer → Database
                                    ↓
                              Background Tasks → External APIs
```

See detailed architecture diagrams in `.kiro/specs/job-aggregation-platform/design.md`.

---

## Technology Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Programming language |
| FastAPI | 0.104+ | Web framework |
| SQLAlchemy | 2.0+ | ORM |
| Alembic | 1.12+ | Database migrations |
| Celery | 5.3+ | Task queue |
| Redis | 7.0+ | Cache and broker |
| Pydantic | 2.0+ | Data validation |
| Pytest | 7.4+ | Testing framework |
| Hypothesis | 6.92+ | Property-based testing |

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| Node.js | 18+ | Runtime |
| Next.js | 14+ | React framework |
| React | 18+ | UI library |
| TypeScript | 5+ | Type safety |
| Tailwind CSS | 3+ | Styling |
| Zustand | 4+ | State management |
| React Query | 5+ | Data fetching |
| Axios | 1.6+ | HTTP client |

### Infrastructure

| Service | Purpose |
|---------|---------|
| Supabase | PostgreSQL database |
| Railway/Render | Backend hosting |
| Vercel | Frontend hosting |
| Sentry | Error tracking |
| Stripe | Payment processing |

---

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 7+
- Git

### Backend Setup

```bash
# Clone repository
git clone https://github.com/your-org/job-aggregation-platform.git
cd job-aggregation-platform/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment template
cp .env.local.example .env.local

# Edit .env.local with your configuration
nano .env.local

# Start development server
npm run dev
```

### Running Background Workers

```bash
cd backend

# Start Celery worker
celery -A app.tasks.celery_app worker --loglevel=info

# Start Celery Beat (in separate terminal)
celery -A app.tasks.celery_app beat --loglevel=info
```

### Docker Setup

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## Coding Standards

### Python (Backend)

**Style Guide**: PEP 8

**Formatting**: Black (line length: 100)

**Linting**: Flake8, mypy

**Import Order**:
1. Standard library
2. Third-party packages
3. Local imports

**Example**:
```python
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.job import Job
from app.schemas.job import JobResponse
```

**Naming Conventions**:
- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

**Docstrings**: Google style

```python
def calculate_quality_score(job_data: Dict, source_type: SourceType) -> float:
    """
    Calculate quality score for a job posting.
    
    Args:
        job_data: Dictionary containing job information
        source_type: Type of job source (direct, url_import, aggregated)
        
    Returns:
        Quality score between 0.0 and 100.0
        
    Raises:
        ValueError: If job_data is missing required fields
    """
    pass
```

### TypeScript (Frontend)

**Style Guide**: Airbnb TypeScript

**Formatting**: Prettier

**Linting**: ESLint

**Naming Conventions**:
- Components: `PascalCase`
- Functions/variables: `camelCase`
- Constants: `UPPER_SNAKE_CASE`
- Types/Interfaces: `PascalCase`

**Example**:
```typescript
interface JobCardProps {
  job: Job;
  onApply: (jobId: string) => void;
}

export function JobCard({ job, onApply }: JobCardProps) {
  const handleApply = () => {
    onApply(job.id);
  };
  
  return (
    <div className="job-card">
      <h3>{job.title}</h3>
      <button onClick={handleApply}>Apply</button>
    </div>
  );
}
```

**Type Safety**:
- Always define types for props
- Avoid `any` type
- Use strict TypeScript configuration
- Define API response types

### Git Commit Messages

**Format**: Conventional Commits

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

**Examples**:
```
feat(jobs): add URL import functionality

Implement URL import service that scrapes job details from external platforms.
Supports LinkedIn, Indeed, Naukri, and Monster.

Closes #123

fix(auth): resolve token refresh race condition

Prevent multiple simultaneous refresh requests by adding mutex lock.

test(search): add property tests for filter combinations
```

### Code Review Guidelines

**Before Submitting PR**:
- [ ] All tests pass
- [ ] Code follows style guide
- [ ] Documentation updated
- [ ] No console.log or print statements
- [ ] No commented-out code
- [ ] Environment variables documented

**Review Checklist**:
- [ ] Code is readable and maintainable
- [ ] Logic is correct and efficient
- [ ] Edge cases are handled
- [ ] Error handling is appropriate
- [ ] Security best practices followed
- [ ] Performance considerations addressed

---

## Testing Strategy

### Test Pyramid

```
        /\
       /  \  E2E Tests (5%)
      /____\
     /      \  Integration Tests (15%)
    /________\
   /          \  Unit Tests (80%)
  /__________  \
```

### Unit Tests

**Purpose**: Test individual functions and methods

**Location**: `backend/tests/test_*.py`, `frontend/**/*.test.ts`

**Framework**: Pytest (backend), Jest (frontend)

**Example** (Backend):
```python
def test_calculate_quality_score_direct_post():
    """Test quality score calculation for direct posts."""
    job_data = {
        "title": "Senior Developer",
        "company": "Tech Corp",
        "description": "A" * 100,
        "requirements": ["Python", "FastAPI"],
        "responsibilities": ["Build APIs"],
        "salary_min": 100000,
        "salary_max": 150000,
    }
    
    score = calculate_quality_score(job_data, SourceType.DIRECT)
    
    assert score >= 70.0
    assert score <= 100.0
```

**Example** (Frontend):
```typescript
describe('JobCard', () => {
  it('renders job title and company', () => {
    const job = {
      id: '123',
      title: 'Senior Developer',
      company: 'Tech Corp',
      ...
    };
    
    render(<JobCard job={job} onApply={jest.fn()} />);
    
    expect(screen.getByText('Senior Developer')).toBeInTheDocument();
    expect(screen.getByText('Tech Corp')).toBeInTheDocument();
  });
});
```

### Property-Based Tests

**Purpose**: Test universal properties across many inputs

**Framework**: Hypothesis (Python)

**Example**:
```python
from hypothesis import given, strategies as st

@given(
    job1=st.builds(generate_job),
    job2=st.builds(generate_job)
)
def test_deduplication_symmetry(job1, job2):
    """Test that similarity(j1, j2) == similarity(j2, j1)."""
    similarity_1_2 = calculate_similarity(job1, job2)
    similarity_2_1 = calculate_similarity(job2, job1)
    
    assert similarity_1_2 == similarity_2_1
```

### Integration Tests

**Purpose**: Test interactions between components

**Location**: `backend/tests/test_integration.py`

**Example**:
```python
def test_job_posting_flow(client, db_session, employer_token):
    """Test complete job posting flow."""
    # Create job
    response = client.post(
        "/api/jobs/direct",
        json=job_data,
        headers={"Authorization": f"Bearer {employer_token}"}
    )
    assert response.status_code == 201
    job_id = response.json()["job_id"]
    
    # Verify job appears in search
    response = client.get("/api/search?query=developer")
    assert response.status_code == 200
    jobs = response.json()["jobs"]
    assert any(job["id"] == job_id for job in jobs)
```

### Running Tests

**Backend**:
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_jobs_api.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run property tests
pytest tests/test_deduplication_properties.py
```

**Frontend**:
```bash
# Run all tests
npm test

# Run specific test
npm test JobCard.test.ts

# Run with coverage
npm test -- --coverage

# Watch mode
npm test -- --watch
```

### Test Coverage Requirements

- Minimum 80% code coverage
- 100% coverage for critical paths (auth, payments)
- All public APIs must have tests
- All bug fixes must include regression tests

---

## Contribution Guidelines

### Getting Started

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests
5. Submit a pull request

### Branch Naming

```
<type>/<short-description>

Examples:
- feature/url-import
- fix/auth-token-refresh
- docs/api-documentation
```

### Pull Request Process

1. **Create PR**:
   - Use descriptive title
   - Fill out PR template
   - Link related issues

2. **Code Review**:
   - Address reviewer comments
   - Keep PR focused and small
   - Respond to feedback promptly

3. **Merge**:
   - Squash commits if needed
   - Update changelog
   - Delete branch after merge

### Issue Reporting

**Bug Reports**:
- Use bug report template
- Include reproduction steps
- Provide error messages
- Specify environment details

**Feature Requests**:
- Use feature request template
- Describe use case
- Explain expected behavior
- Consider implementation approach

### Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Help others learn and grow
- Follow project guidelines

---

For more detailed information, see:
- API Documentation: `docs/API_DOCUMENTATION.md`
- Deployment Guide: `docs/DEPLOYMENT_DOCUMENTATION.md`
- User Guides: `docs/USER_GUIDE_*.md`


---

## API Development

### Creating New Endpoints

**Step 1: Define Pydantic Schema**

```python
# app/schemas/feature.py
from pydantic import BaseModel, Field
from typing import Optional

class FeatureCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Feature Name",
                "description": "Feature description"
            }
        }

class FeatureResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
```

**Step 2: Create API Endpoint**

```python
# app/api/feature.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.schemas.feature import FeatureCreateRequest, FeatureResponse

router = APIRouter(prefix="/features", tags=["features"])

@router.post(
    "/",
    response_model=FeatureResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_feature(
    feature_data: FeatureCreateRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new feature."""
    # Implementation
    pass
```

**Step 3: Register Router**

```python
# app/main.py
from app.api.feature import router as feature_router

app.include_router(feature_router, prefix="/api")
```

**Step 4: Write Tests**

```python
# tests/test_feature_api.py
def test_create_feature(client, auth_token):
    response = client.post(
        "/api/features",
        json={"name": "Test Feature"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Feature"
```

### API Best Practices

**1. Use Appropriate HTTP Methods**:
- GET: Retrieve resources
- POST: Create resources
- PUT: Replace resources
- PATCH: Update resources
- DELETE: Remove resources

**2. Return Correct Status Codes**:
- 200: Success
- 201: Created
- 204: No Content
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 422: Validation Error
- 500: Server Error

**3. Validate Input**:
- Use Pydantic models
- Define field constraints
- Provide clear error messages

**4. Handle Errors Gracefully**:
```python
try:
    result = perform_operation()
except ValueError as e:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(e)
    )
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred"
    )
```

**5. Document Endpoints**:
- Add docstrings
- Provide examples
- Document error responses

---

## Database Management

### Creating Models

```python
# app/models/feature.py
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.db.base_class import Base

class Feature(Base):
    __tablename__ = "features"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Feature(id={self.id}, name={self.name})>"
```

### Creating Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Add features table"

# Review generated migration
cat alembic/versions/xxx_add_features_table.py

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Migration Best Practices

**1. Review Auto-Generated Migrations**:
- Check for unintended changes
- Verify indexes are created
- Ensure foreign keys are correct

**2. Add Data Migrations When Needed**:
```python
def upgrade():
    # Schema changes
    op.add_column('jobs', sa.Column('new_field', sa.String(50)))
    
    # Data migration
    connection = op.get_bind()
    connection.execute(
        "UPDATE jobs SET new_field = 'default' WHERE new_field IS NULL"
    )
```

**3. Make Migrations Reversible**:
```python
def upgrade():
    op.add_column('jobs', sa.Column('new_field', sa.String(50)))

def downgrade():
    op.drop_column('jobs', 'new_field')
```

**4. Test Migrations**:
```bash
# Test upgrade
alembic upgrade head

# Test downgrade
alembic downgrade -1

# Test upgrade again
alembic upgrade head
```

### Database Queries

**Use ORM for Simple Queries**:
```python
# Get all active jobs
jobs = db.query(Job).filter(Job.status == JobStatus.ACTIVE).all()

# Get job by ID
job = db.query(Job).filter(Job.id == job_id).first()

# Count jobs
count = db.query(Job).filter(Job.status == JobStatus.ACTIVE).count()
```

**Use Raw SQL for Complex Queries**:
```python
from sqlalchemy import text

result = db.execute(
    text("""
        SELECT j.*, COUNT(a.id) as application_count
        FROM jobs j
        LEFT JOIN applications a ON j.id = a.job_id
        WHERE j.employer_id = :employer_id
        GROUP BY j.id
        ORDER BY j.posted_at DESC
    """),
    {"employer_id": employer_id}
)
jobs = result.fetchall()
```

**Optimize Queries**:
```python
# Use eager loading to avoid N+1 queries
from sqlalchemy.orm import joinedload

jobs = db.query(Job).options(
    joinedload(Job.employer),
    joinedload(Job.applications)
).all()

# Use pagination
from sqlalchemy import func

total = db.query(func.count(Job.id)).scalar()
jobs = db.query(Job).offset(offset).limit(limit).all()
```

---

## Background Tasks

### Creating Celery Tasks

```python
# app/tasks/feature_tasks.py
from app.tasks.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger(__name__)

@celery_app.task(bind=True, max_retries=3)
def process_feature(self, feature_id: str):
    """
    Process a feature asynchronously.
    
    Args:
        feature_id: UUID of the feature to process
    """
    try:
        # Implementation
        logger.info(f"Processing feature {feature_id}")
        # ... processing logic ...
        return {"status": "success", "feature_id": feature_id}
        
    except Exception as e:
        logger.error(f"Error processing feature {feature_id}: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
```

### Scheduling Tasks

```python
# app/tasks/celery_app.py
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'process-features-daily': {
        'task': 'app.tasks.feature_tasks.process_feature',
        'schedule': crontab(hour=2, minute=0),  # Run at 2 AM daily
    },
}
```

### Task Best Practices

**1. Make Tasks Idempotent**:
```python
@celery_app.task
def update_job_status(job_id: str):
    """Update job status - safe to run multiple times."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if job and job.expires_at < datetime.utcnow():
        job.status = JobStatus.EXPIRED
        db.commit()
```

**2. Handle Failures Gracefully**:
```python
@celery_app.task(bind=True, max_retries=3)
def risky_operation(self, data):
    try:
        # Risky operation
        pass
    except TemporaryError as e:
        # Retry for temporary errors
        raise self.retry(exc=e, countdown=60)
    except PermanentError as e:
        # Log and don't retry for permanent errors
        logger.error(f"Permanent error: {e}")
        return {"status": "failed", "error": str(e)}
```

**3. Monitor Task Performance**:
```python
from celery.signals import task_prerun, task_postrun
import time

@task_prerun.connect
def task_prerun_handler(task_id, task, *args, **kwargs):
    task.start_time = time.time()

@task_postrun.connect
def task_postrun_handler(task_id, task, *args, **kwargs):
    duration = time.time() - task.start_time
    logger.info(f"Task {task.name} took {duration:.2f}s")
```

**4. Use Task Priorities**:
```python
# High priority task
process_urgent.apply_async(args=[data], priority=9)

# Low priority task
cleanup_old_data.apply_async(args=[data], priority=1)
```

---

## Security Best Practices

### Authentication

**1. Use Strong Password Hashing**:
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

**2. Implement JWT Properly**:
```python
from jose import jwt
from datetime import datetime, timedelta

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

**3. Validate Tokens**:
```python
def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Input Validation

**1. Use Pydantic Models**:
```python
from pydantic import BaseModel, validator, Field

class JobCreateRequest(BaseModel):
    title: str = Field(..., min_length=10, max_length=200)
    description: str = Field(..., min_length=50, max_length=5000)
    
    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()
```

**2. Sanitize HTML**:
```python
import bleach

ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li']
ALLOWED_ATTRIBUTES = {}

def sanitize_html(html: str) -> str:
    return bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
```

**3. Validate File Uploads**:
```python
from fastapi import UploadFile

ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

async def validate_resume(file: UploadFile):
    # Check extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Invalid file type")
    
    # Check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large")
    
    await file.seek(0)  # Reset file pointer
    return file
```

### SQL Injection Prevention

**Always use parameterized queries**:

```python
# ✅ GOOD - Parameterized query
db.query(Job).filter(Job.id == job_id).first()

# ✅ GOOD - Named parameters
db.execute(text("SELECT * FROM jobs WHERE id = :id"), {"id": job_id})

# ❌ BAD - String concatenation
db.execute(f"SELECT * FROM jobs WHERE id = '{job_id}'")
```

### CSRF Protection

```python
from app.core.middleware import generate_csrf_token, verify_csrf_token

@app.post("/api/jobs")
async def create_job(
    request: Request,
    job_data: JobCreateRequest,
    csrf_token: str = Header(None, alias="X-CSRF-Token")
):
    # Verify CSRF token
    session_token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not verify_csrf_token(csrf_token, session_token):
        raise HTTPException(403, "Invalid CSRF token")
    
    # Process request
    pass
```

---

## Performance Optimization

### Database Optimization

**1. Use Indexes**:
```python
# Add index in model
class Job(Base):
    __tablename__ = "jobs"
    
    company = Column(String(100), index=True)  # B-tree index
    status = Column(Enum(JobStatus), index=True)
    
    __table_args__ = (
        Index('ix_jobs_quality_posted', 'quality_score', 'posted_at'),  # Composite index
    )
```

**2. Use Connection Pooling**:
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=20,
    pool_pre_ping=True
)
```

**3. Optimize Queries**:
```python
# Use select_in_loading for relationships
from sqlalchemy.orm import selectinload

jobs = db.query(Job).options(
    selectinload(Job.applications)
).all()

# Use pagination
jobs = db.query(Job).limit(20).offset(page * 20).all()

# Use specific columns
jobs = db.query(Job.id, Job.title, Job.company).all()
```

### Caching

**1. Cache Expensive Operations**:
```python
from app.core.redis import redis_client

def get_popular_searches():
    cache_key = "popular_searches"
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # Expensive database query
    result = db.execute("""
        SELECT query, COUNT(*) as count
        FROM search_logs
        WHERE created_at > NOW() - INTERVAL '7 days'
        GROUP BY query
        ORDER BY count DESC
        LIMIT 10
    """).fetchall()
    
    # Cache for 1 hour
    redis_client.setex(cache_key, 3600, json.dumps(result))
    return result
```

**2. Implement Cache Invalidation**:
```python
def update_job(job_id: str, updates: dict):
    # Update database
    job = db.query(Job).filter(Job.id == job_id).first()
    for key, value in updates.items():
        setattr(job, key, value)
    db.commit()
    
    # Invalidate cache
    redis_client.delete(f"job:{job_id}")
    redis_client.delete("search:*")  # Invalidate search caches
```

### API Optimization

**1. Use Response Compression**:
```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

**2. Implement Pagination**:
```python
from fastapi import Query

@app.get("/api/jobs")
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    offset = (page - 1) * page_size
    jobs = db.query(Job).offset(offset).limit(page_size).all()
    total = db.query(Job).count()
    
    return {
        "jobs": jobs,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size
    }
```

**3. Use Async Operations**:
```python
import asyncio
from httpx import AsyncClient

async def fetch_multiple_sources():
    async with AsyncClient() as client:
        tasks = [
            client.get("https://api1.example.com/jobs"),
            client.get("https://api2.example.com/jobs"),
            client.get("https://api3.example.com/jobs"),
        ]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]
```

---

## Monitoring and Debugging

### Logging

**1. Use Structured Logging**:
```python
from app.core.logging import get_logger

logger = get_logger(__name__)

logger.info("Job created", extra={
    "job_id": job.id,
    "employer_id": employer.id,
    "source_type": job.source_type
})
```

**2. Log Levels**:
- DEBUG: Detailed information for debugging
- INFO: General informational messages
- WARNING: Warning messages
- ERROR: Error messages
- CRITICAL: Critical errors

**3. Log Context**:
```python
import contextvars

request_id = contextvars.ContextVar('request_id', default=None)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    req_id = str(uuid.uuid4())
    request_id.set(req_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    return response
```

### Error Tracking

**1. Integrate Sentry**:
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=SENTRY_DSN,
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    environment=APP_ENV
)
```

**2. Add Context to Errors**:
```python
with sentry_sdk.push_scope() as scope:
    scope.set_tag("job_id", job_id)
    scope.set_context("job_data", job_data)
    sentry_sdk.capture_exception(error)
```

### Debugging

**1. Use Debugger**:
```python
import pdb

def complex_function():
    # Set breakpoint
    pdb.set_trace()
    # Code execution pauses here
    result = perform_calculation()
    return result
```

**2. Use FastAPI Debug Mode**:
```python
# In development only
app = FastAPI(debug=True)
```

**3. Profile Performance**:
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
result = expensive_operation()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

---

## Deployment

### Pre-Deployment Checklist

- [ ] All tests passing
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] Environment variables configured
- [ ] Database migrations tested
- [ ] Security audit completed
- [ ] Performance testing done
- [ ] Monitoring configured
- [ ] Rollback plan documented

### Deployment Process

1. **Tag Release**:
```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

2. **Run Migrations**:
```bash
alembic upgrade head
```

3. **Deploy Services**:
```bash
# Backend
git push railway main

# Frontend
git push vercel main
```

4. **Verify Deployment**:
```bash
# Check health
curl https://api.jobplatform.com/health

# Check frontend
curl https://jobplatform.com
```

5. **Monitor**:
- Check Sentry for errors
- Review service logs
- Monitor response times
- Verify background tasks running

### Rollback Procedure

1. **Identify Issue**:
- Check error logs
- Review metrics
- Determine scope

2. **Rollback Code**:
```bash
# Revert to previous version
git revert <commit-hash>
git push

# Or deploy previous tag
git checkout v0.9.9
git push --force
```

3. **Rollback Database**:
```bash
# Only if needed
alembic downgrade -1
```

4. **Verify**:
- Check health endpoints
- Test critical functionality
- Monitor error rates

---

## Resources

### Documentation

- FastAPI: https://fastapi.tiangolo.com
- SQLAlchemy: https://docs.sqlalchemy.org
- Celery: https://docs.celeryproject.org
- Next.js: https://nextjs.org/docs
- React: https://react.dev

### Tools

- Postman: API testing
- pgAdmin: PostgreSQL management
- Redis Commander: Redis management
- Sentry: Error tracking
- Grafana: Metrics visualization

### Learning Resources

- Python Best Practices: https://docs.python-guide.org
- TypeScript Handbook: https://www.typescriptlang.org/docs
- Database Design: https://www.postgresql.org/docs
- API Design: https://restfulapi.net

---

## Support

For development questions or issues:

- Email: dev@jobplatform.com
- Slack: #engineering
- Wiki: https://wiki.jobplatform.com
- Office Hours: Tuesdays 2-3 PM EST

---

**Happy coding!** 🚀

*Last updated: January 2024*
*Version: 1.0.0*
