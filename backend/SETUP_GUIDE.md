# Backend Setup Guide

This guide will help you set up the Job Aggregation Platform backend for development.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11 or higher**: Check with `python3 --version`
- **PostgreSQL 15+**: Database server
- **Redis 7+**: Cache and message broker
- **Git**: Version control

## Quick Start with Docker (Recommended)

The easiest way to get started is using Docker Compose:

```bash
# Start all services (PostgreSQL, Redis, API, Celery)
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop all services
docker-compose down
```

The API will be available at http://localhost:8000

## Manual Setup

### 1. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

**Required Configuration:**

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: Random secret key for security
- `JWT_SECRET_KEY`: Random secret key for JWT tokens

**Generate Secret Keys:**

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. Start PostgreSQL and Redis

**Option A: Using Docker**

```bash
# Start PostgreSQL
docker run -d --name postgres \
  -e POSTGRES_USER=jobplatform \
  -e POSTGRES_PASSWORD=jobplatform \
  -e POSTGRES_DB=job_platform \
  -p 5432:5432 \
  postgres:15-alpine

# Start Redis
docker run -d --name redis \
  -p 6379:6379 \
  redis:7-alpine
```

**Option B: System Installation**

Install PostgreSQL and Redis using your system's package manager.

### 5. Run Database Migrations

```bash
alembic upgrade head
```

### 6. Start the Application

```bash
# Development server with auto-reload
python app/main.py

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Start Celery Workers (Optional)

In separate terminal windows:

```bash
# Terminal 1: Celery worker
celery -A app.tasks.celery_app worker --loglevel=info

# Terminal 2: Celery beat scheduler
celery -A app.tasks.celery_app beat --loglevel=info
```

## Verify Installation

1. **Check API Health:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **View API Documentation:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

3. **Run Tests:**
   ```bash
   pytest
   ```

## Common Issues

### Issue: ModuleNotFoundError

**Solution:** Ensure virtual environment is activated and dependencies are installed:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: Database Connection Error

**Solution:** Verify PostgreSQL is running and DATABASE_URL is correct:
```bash
# Test PostgreSQL connection
psql -h localhost -U jobplatform -d job_platform
```

### Issue: Redis Connection Error

**Solution:** Verify Redis is running:
```bash
# Test Redis connection
redis-cli ping
# Should return: PONG
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_main.py

# Run tests matching pattern
pytest -k "test_auth"
```

### Creating Database Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add user table"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Code Quality

```bash
# Format code (install black first: pip install black)
black app/ tests/

# Lint code (install ruff first: pip install ruff)
ruff check app/ tests/
```

## Project Structure

```
backend/
├── alembic/              # Database migrations
│   ├── versions/        # Migration files
│   └── env.py           # Alembic configuration
├── app/
│   ├── api/             # API endpoints (routers)
│   ├── core/            # Core configuration
│   │   ├── config.py    # Settings management
│   │   └── logging.py   # Logging configuration
│   ├── db/              # Database setup
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── tasks/           # Celery tasks
│   └── main.py          # Application entry point
├── tests/               # Test suite
├── .env.example         # Environment template
├── requirements.txt     # Python dependencies
└── README.md           # Project documentation
```

## Next Steps

After completing the setup:

1. Review the [API Documentation](http://localhost:8000/docs)
2. Explore the codebase structure
3. Read the requirements and design documents in `.kiro/specs/job-aggregation-platform/`
4. Start implementing features according to the task list

## Getting Help

If you encounter issues:

1. Check the logs: `docker-compose logs -f` or application console output
2. Review the `.env` configuration
3. Ensure all services (PostgreSQL, Redis) are running
4. Check the project documentation in `.kiro/specs/`

## Useful Commands

```bash
# Using Makefile
make install    # Install dependencies
make run        # Run development server
make test       # Run tests
make migrate    # Run migrations
make worker     # Start Celery worker
make clean      # Clean cache files

# Using setup script
chmod +x setup.sh
./setup.sh
```
