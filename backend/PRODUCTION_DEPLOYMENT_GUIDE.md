# Production Deployment Guide

This guide provides step-by-step instructions for deploying the Job Aggregation Platform to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Database Migration](#database-migration)
4. [Docker Deployment](#docker-deployment)
5. [Health Checks](#health-checks)
6. [Rollback Procedures](#rollback-procedures)
7. [Monitoring](#monitoring)

## Prerequisites

Before deploying to production, ensure you have:

- [ ] PostgreSQL 15+ database instance
- [ ] Redis 7+ instance
- [ ] Docker and Docker Compose installed
- [ ] SSL certificates for HTTPS
- [ ] Domain name configured
- [ ] Sentry account for error monitoring
- [ ] Stripe account for payment processing
- [ ] SMTP credentials for email alerts

## Environment Configuration

### Step 1: Create Production Environment File

Copy the production environment template:

```bash
cp .env.production.example .env.production
```

### Step 2: Configure Required Variables

Edit `.env.production` and set all required values:

#### Critical Security Settings (Requirement 13.4)

```bash
# Generate strong random keys
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
```

**IMPORTANT**: Never use default or weak values in production!

#### Database Configuration (Requirement 16.8)

```bash
DATABASE_URL=postgresql://username:password@host:port/database?sslmode=require
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=20
```

**Note**: Always use SSL for database connections in production (`?sslmode=require`)

#### Redis Configuration (Requirement 16.8)

```bash
REDIS_URL=redis://host:port/0
REDIS_CACHE_DB=1
CELERY_BROKER_URL=redis://host:port/0
CELERY_RESULT_BACKEND=redis://host:port/0
```

#### CORS Configuration (Requirement 13.4)

```bash
# Only whitelist your production frontend domain(s)
CORS_ORIGINS=https://yourplatform.com,https://www.yourplatform.com
```

**CRITICAL**: Never use wildcards (*) or localhost in production CORS settings!

#### Stripe Payment (Requirement 13.4)

```bash
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
```

**Note**: Use live keys (sk_live_, pk_live_) for production, not test keys.

#### Monitoring (Requirement 19.7)

```bash
SENTRY_DSN=https://your_sentry_dsn@sentry.io/project_id
```

#### Alerting (Requirements 15.5, 15.7)

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your_email_app_password
ADMIN_EMAIL=admin@yourplatform.com
FROM_EMAIL=noreply@yourplatform.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Step 3: Validate Configuration

```bash
# Check that all required variables are set
python scripts/validate_env.py --env production
```

## Database Migration

### Pre-Migration Checklist

- [ ] Database backup completed
- [ ] Maintenance window scheduled
- [ ] Rollback plan prepared
- [ ] Migration tested in staging environment

### Migration Process (Requirement 16.2)

#### Step 1: Backup Database

```bash
# Create a backup before migration
pg_dump -h HOST -U USER -d DATABASE > backup_$(date +%Y%m%d_%H%M%S).sql
```

**CRITICAL**: Always backup before running migrations!

#### Step 2: Test Migrations (Dry Run)

```bash
# Check migration status
alembic current

# Show pending migrations
alembic history

# Test migration without applying (if supported by your setup)
alembic upgrade head --sql > migration.sql
# Review migration.sql before proceeding
```

#### Step 3: Run Migrations

```bash
# Apply all pending migrations
alembic upgrade head
```

#### Step 4: Verify Migration

```bash
# Check current migration version
alembic current

# Verify tables were created
psql -h HOST -U USER -d DATABASE -c "\dt"

# Verify indexes were created
psql -h HOST -U USER -d DATABASE -c "\di"
```

### Migration Rollback Plan

If migration fails or causes issues:

#### Option 1: Rollback to Previous Version

```bash
# Downgrade to previous version
alembic downgrade -1

# Or downgrade to specific version
alembic downgrade <revision_id>
```

#### Option 2: Restore from Backup

```bash
# Stop application
docker-compose down

# Restore database from backup
psql -h HOST -U USER -d DATABASE < backup_YYYYMMDD_HHMMSS.sql

# Restart application
docker-compose up -d
```

### Available Migrations

The following migrations will be applied in order:

1. `001_create_jobs_table.py` - Core jobs table
2. `002_create_employers_table.py` - Employers and subscriptions
3. `003_create_applications_table.py` - Job applications
4. `004_create_job_sources_table.py` - Job sources tracking
5. `005_create_scraping_tasks_table.py` - Scraping task logs
6. `006_create_job_seekers_table.py` - Job seeker profiles
7. `007_create_analytics_tables.py` - Analytics and metrics
8. `008_create_consents_table.py` - Privacy consents
9. `009_add_performance_indexes.py` - Performance optimization indexes

## Docker Deployment

### Step 1: Build Docker Images

```bash
# Build production image
docker build -t job-platform-backend:latest .

# Tag for registry (if using container registry)
docker tag job-platform-backend:latest registry.example.com/job-platform-backend:latest
```

### Step 2: Push to Container Registry (Optional)

```bash
# Push to registry
docker push registry.example.com/job-platform-backend:latest
```

### Step 3: Deploy with Docker Compose

For production deployment, create a `docker-compose.production.yml`:

```yaml
version: '3.8'

services:
  backend:
    image: job-platform-backend:latest
    env_file:
      - .env.production
    ports:
      - "8000:8000"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  celery_worker:
    image: job-platform-backend:latest
    env_file:
      - .env.production
    command: celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4
    restart: unless-stopped

  celery_beat:
    image: job-platform-backend:latest
    env_file:
      - .env.production
    command: celery -A app.tasks.celery_app beat --loglevel=info
    restart: unless-stopped
```

Deploy:

```bash
# Start services
docker-compose -f docker-compose.production.yml up -d

# Check service status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f
```

### Step 4: Run Database Migrations

```bash
# Run migrations in backend container
docker-compose -f docker-compose.production.yml exec backend alembic upgrade head
```

## Health Checks

### Endpoint: GET /health

The health check endpoint monitors critical services (Requirement 19.7):

```bash
curl http://localhost:8000/health
```

**Response (Healthy - 200 OK):**

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "database": {
      "status": "healthy",
      "connected": true,
      "pool_size": 5,
      "checked_in": 4,
      "checked_out": 1
    },
    "redis": {
      "status": "healthy",
      "connected": true,
      "ping": "ok"
    }
  }
}
```

**Response (Unhealthy - 503 Service Unavailable):**

```json
{
  "status": "unhealthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "database": {
      "status": "unhealthy",
      "connected": false
    },
    "redis": {
      "status": "unhealthy",
      "connected": false,
      "error": "Connection failed"
    }
  }
}
```

### Monitoring Integration

Configure your monitoring system to check `/health` endpoint:

- **Interval**: Every 30 seconds
- **Timeout**: 10 seconds
- **Success**: HTTP 200
- **Failure**: HTTP 503 or timeout

## Rollback Procedures

### Application Rollback

If the new version has issues:

```bash
# Stop current version
docker-compose -f docker-compose.production.yml down

# Deploy previous version
docker-compose -f docker-compose.production.yml pull <previous-tag>
docker-compose -f docker-compose.production.yml up -d
```

### Database Rollback

See [Migration Rollback Plan](#migration-rollback-plan) above.

## Monitoring

### Error Monitoring (Requirement 19.1)

Sentry automatically captures:
- Unhandled exceptions
- API errors with context
- Database errors
- Background task failures

Access Sentry dashboard: https://sentry.io/organizations/your-org/projects/

### Alerting (Requirements 15.5, 15.7)

The system sends alerts for:
- Critical errors (via email and Slack)
- 3+ consecutive scraping failures
- Database connection failures
- Redis connection failures

Configure alert channels in `.env.production`:
- Email: SMTP settings
- Slack: SLACK_WEBHOOK_URL

### Logs

View application logs:

```bash
# Backend logs
docker-compose -f docker-compose.production.yml logs -f backend

# Celery worker logs
docker-compose -f docker-compose.production.yml logs -f celery_worker

# Celery beat logs
docker-compose -f docker-compose.production.yml logs -f celery_beat
```

### Metrics

Monitor key metrics:
- API response times
- Database query performance
- Celery task success/failure rates
- Job scraping success rates
- Active user counts

## Security Checklist

Before going live:

- [ ] DEBUG=False in production
- [ ] Strong SECRET_KEY and JWT_SECRET_KEY
- [ ] CORS_ORIGINS restricted to production domains only
- [ ] Database uses SSL connection
- [ ] HTTPS enabled with valid SSL certificate
- [ ] Stripe live keys configured (not test keys)
- [ ] Sentry DSN configured for error tracking
- [ ] Rate limiting enabled
- [ ] CSRF protection enabled
- [ ] Security headers middleware active
- [ ] File upload validation enabled
- [ ] All secrets stored securely (not in code)

## Post-Deployment Verification

After deployment:

1. **Health Check**: Verify `/health` returns 200
2. **Authentication**: Test login/registration
3. **Job Search**: Test job search and filtering
4. **Job Posting**: Test employer job posting
5. **Applications**: Test job application submission
6. **Payments**: Test subscription upgrade flow
7. **Monitoring**: Verify Sentry receives events
8. **Alerts**: Test email/Slack alerts

## Support

For deployment issues:
- Check logs: `docker-compose logs -f`
- Check health: `curl http://localhost:8000/health`
- Review Sentry errors: https://sentry.io
- Contact: admin@yourplatform.com
