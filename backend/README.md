# Job Aggregation Platform - Backend

FastAPI backend for the Job Aggregation and Posting Platform.

## Features

- **Automated Job Aggregation**: Scrapes jobs from LinkedIn, Indeed, Naukri, and Monster
- **Direct Job Posting**: Employers can post jobs directly with application tracking
- **URL Import**: Import jobs from external platforms via URL
- **Intelligent Deduplication**: Fuzzy matching to merge duplicate jobs
- **Quality Scoring**: Prioritizes high-quality job postings
- **Subscription Management**: Freemium model with tiered features
- **Advanced Search**: Full-text search with multiple filters

## Tech Stack

- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Task Queue**: Celery with Redis
- **Authentication**: JWT tokens with bcrypt password hashing
- **Web Scraping**: Scrapy, BeautifulSoup4, Selenium
- **Monitoring**: Sentry

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Installation

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run database migrations:
```bash
alembic upgrade head
```

### Running the Application

Development server:
```bash
python app/main.py
```

Or with uvicorn directly:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Celery Workers

Start Celery worker:
```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

Start Celery Beat scheduler:
```bash
celery -A app.tasks.celery_app beat --loglevel=info
```

## Project Structure

```
backend/
├── alembic/              # Database migrations
├── app/
│   ├── api/             # API endpoints
│   ├── core/            # Core configuration
│   ├── db/              # Database setup
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── tasks/           # Celery tasks
│   └── main.py          # Application entry point
├── tests/               # Test suite
├── .env.example         # Environment template
└── requirements.txt     # Python dependencies
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

Run tests:
```bash
pytest
```

With coverage:
```bash
pytest --cov=app --cov-report=html
```

## License

Proprietary
