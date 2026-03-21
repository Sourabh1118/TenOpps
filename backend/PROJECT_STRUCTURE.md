# Backend Project Structure

This document describes the organization of the Job Aggregation Platform backend.

## Directory Structure

```
backend/
├── alembic/                    # Database migrations
│   ├── versions/              # Migration version files
│   ├── env.py                 # Alembic environment configuration
│   ├── script.py.mako         # Migration template
│   └── README                 # Alembic usage guide
│
├── app/                       # Main application package
│   ├── api/                   # API endpoints and routers
│   │   └── __init__.py
│   │
│   ├── core/                  # Core application modules
│   │   ├── __init__.py
│   │   ├── config.py          # Settings and configuration
│   │   └── logging.py         # Structured logging setup
│   │
│   ├── db/                    # Database configuration
│   │   ├── __init__.py        # Database exports
│   │   ├── base.py            # SQLAlchemy declarative base
│   │   ├── session.py         # Database engine and session management
│   │   └── init_db.py         # Database initialization utilities
│   │
│   ├── models/                # SQLAlchemy ORM models
│   │   └── __init__.py
│   │
│   ├── schemas/               # Pydantic schemas for validation
│   │   └── __init__.py
│   │
│   ├── services/              # Business logic layer
│   │   └── __init__.py
│   │
│   ├── tasks/                 # Celery background tasks
│   │   └── __init__.py
│   │
│   ├── __init__.py
│   └── main.py                # FastAPI application entry point
│
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── test_main.py           # Basic application tests
│   └── test_database.py       # Database connection tests
│
├── scripts/                   # Utility scripts
│   ├── init_db.py             # Database initialization script
│   └── test_db_connection.py # Database connection test script
│
├── docs/                      # Documentation
│   └── DATABASE_SETUP.md      # Database setup guide
│
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── alembic.ini                # Alembic configuration
├── docker-compose.yml         # Docker services configuration
├── Dockerfile                 # Docker image definition
├── Makefile                   # Common development tasks
├── PROJECT_STRUCTURE.md       # This file
├── pytest.ini                 # Pytest configuration
├── README.md                  # Project overview
├── requirements.txt           # Python dependencies
├── setup.sh                   # Setup automation script
└── SETUP_GUIDE.md            # Detailed setup instructions
```

## Module Descriptions

### app/core/

Core application configuration and utilities.

- **config.py**: Centralized settings management using Pydantic. Loads configuration from environment variables with validation and type checking.
- **logging.py**: Structured logging configuration supporting both JSON and text formats. Includes custom formatters and log level management.

### app/db/

Database layer with SQLAlchemy integration.

- **base.py**: SQLAlchemy declarative base class for all ORM models
- **session.py**: Database engine with connection pooling (min=5, max=20 connections) and session management
- **init_db.py**: Database initialization utilities and health check functions

Features:
- Connection pooling with QueuePool for efficient connection reuse
- Session dependency injection for FastAPI routes
- Health check endpoint integration
- Connection pool monitoring and metrics

### app/api/

API endpoints organized by resource type. Will contain routers for:
- Jobs (CRUD, search, import)
- Authentication (login, register, tokens)
- Employers (dashboard, subscriptions)
- Applications (submit, track, manage)

### app/models/

SQLAlchemy ORM models representing database tables:
- Job
- Employer
- JobSeeker
- Application
- JobSource
- ScrapingTask
- Subscription

### app/schemas/

Pydantic schemas for request/response validation:
- Input validation (create/update DTOs)
- Response serialization
- Type safety and documentation

### app/services/

Business logic layer containing:
- Job service (CRUD operations)
- Scraping service (web scraping orchestration)
- Deduplication service (fuzzy matching)
- Quality scoring service
- Search service (filtering, ranking)
- Subscription service (quota management)
- Authentication service (JWT, passwords)

### app/tasks/

Celery background tasks for:
- Scheduled job scraping
- URL import processing
- Job expiration checks
- Quota resets
- Email notifications

### app/db/

Database configuration:
- SQLAlchemy engine setup
- Session management
- Connection pooling
- Database utilities

### tests/

Test suite organized by module:
- Unit tests for individual functions
- Integration tests for API endpoints
- Property-based tests for algorithms
- Fixtures and test utilities

## Configuration Files

### .env.example

Template for environment variables. Copy to `.env` and customize:
- Database connection
- Redis connection
- API keys (Indeed, Stripe)
- JWT secrets
- Scraping configuration
- Feature flags

### requirements.txt

Python dependencies with pinned versions:
- FastAPI and Uvicorn (web framework)
- SQLAlchemy and Alembic (database)
- Celery and Redis (task queue)
- Pydantic (validation)
- Scrapy, BeautifulSoup4, Selenium (scraping)
- pytest (testing)

### alembic.ini

Alembic migration configuration:
- Migration script location
- Database URL (overridden by settings)
- Logging configuration

### docker-compose.yml

Development environment with:
- PostgreSQL database
- Redis cache/broker
- FastAPI application
- Celery worker
- Celery beat scheduler

### pytest.ini

Test configuration:
- Test discovery patterns
- Markers (unit, integration, slow)
- Coverage settings
- Async test support

## Design Patterns

### Layered Architecture

```
API Layer (FastAPI routers)
    ↓
Service Layer (Business logic)
    ↓
Data Layer (SQLAlchemy models)
    ↓
Database (PostgreSQL)
```

### Dependency Injection

FastAPI's dependency injection system is used for:
- Database sessions
- Authentication
- Configuration
- Service instances

### Repository Pattern

Data access is abstracted through repository classes:
- Encapsulates database queries
- Provides clean interface for services
- Enables easier testing with mocks

### Background Tasks

Long-running operations use Celery:
- Asynchronous execution
- Retry logic
- Task scheduling
- Result tracking

## Naming Conventions

### Files and Directories

- Lowercase with underscores: `job_service.py`
- Plural for collections: `models/`, `schemas/`
- Descriptive names: `deduplication_service.py`

### Python Code

- Classes: PascalCase (`JobService`)
- Functions: snake_case (`create_job`)
- Constants: UPPER_SNAKE_CASE (`MAX_RETRIES`)
- Private: prefix with underscore (`_internal_method`)

### Database

- Tables: lowercase plural (`jobs`, `employers`)
- Columns: lowercase snake_case (`posted_at`, `quality_score`)
- Foreign keys: `{table}_id` (`employer_id`)
- Indexes: `ix_{table}_{column}` (`ix_jobs_company`)

## Development Workflow

1. **Feature Development**
   - Create feature branch
   - Implement models, schemas, services
   - Add API endpoints
   - Write tests
   - Update documentation

2. **Database Changes**
   - Modify SQLAlchemy models
   - Generate migration: `alembic revision --autogenerate -m "description"`
   - Review and edit migration
   - Apply: `alembic upgrade head`

3. **Testing**
   - Write tests alongside code
   - Run tests: `pytest`
   - Check coverage: `pytest --cov=app`
   - Fix failing tests before commit

4. **Code Review**
   - Format code: `black app/ tests/`
   - Lint code: `ruff check app/`
   - Run full test suite
   - Submit pull request

## Best Practices

### Configuration

- Never commit `.env` file
- Use environment variables for secrets
- Provide sensible defaults in `config.py`
- Document all settings in `.env.example`

### Logging

- Use structured logging (JSON format)
- Include context in log messages
- Use appropriate log levels
- Never log sensitive data (passwords, tokens)

### Error Handling

- Use FastAPI exception handlers
- Return appropriate HTTP status codes
- Provide clear error messages
- Log errors with full context

### Testing

- Write tests for all business logic
- Use fixtures for common setup
- Mock external dependencies
- Aim for 80%+ code coverage

### Security

- Validate all inputs with Pydantic
- Use parameterized queries (SQLAlchemy ORM)
- Hash passwords with bcrypt
- Implement rate limiting
- Use HTTPS in production

## Future Enhancements

Planned additions to the structure:

- `app/middleware/`: Custom middleware (rate limiting, logging)
- `app/utils/`: Shared utility functions
- `app/exceptions/`: Custom exception classes
- `app/constants/`: Application constants and enums
- `scripts/`: Deployment and maintenance scripts
- `docs/`: Additional documentation
