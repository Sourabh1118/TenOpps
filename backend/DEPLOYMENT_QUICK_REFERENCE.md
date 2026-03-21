# Deployment Quick Reference

Quick commands and checklists for deploying the Job Aggregation Platform.

## Pre-Deployment Checklist

### Environment Configuration

- [ ] Copy `.env.production.example` to `.env.production`
- [ ] Generate strong `SECRET_KEY` (32+ chars)
- [ ] Generate strong `JWT_SECRET_KEY` (32+ chars)
- [ ] Configure `DATABASE_URL` with SSL
- [ ] Configure `REDIS_URL`
- [ ] Set `CORS_ORIGINS` to production domains only
- [ ] Configure Stripe live keys (sk_live_, pk_live_)
- [ ] Set `DEBUG=False`
- [ ] Configure `SENTRY_DSN` for monitoring
- [ ] Configure SMTP for email alerts
- [ ] Configure Slack webhook for alerts

### Validation

```bash
# Validate production environment
python scripts/validate_env.py --env production --file .env.production
```

### Database Preparation

- [ ] Database instance created
- [ ] Database backup scheduled
- [ ] Database connection tested
- [ ] SSL enabled on database

## Deployment Commands

### 1. Build Docker Image

```bash
# Build production image
docker build -t job-platform-backend:latest .

# Tag for registry
docker tag job-platform-backend:latest registry.example.com/job-platform-backend:v1.0.0
```

### 2. Push to Registry

```bash
# Login to registry
docker login registry.example.com

# Push image
docker push registry.example.com/job-platform-backend:v1.0.0
```

### 3. Deploy Services

```bash
# Pull latest image
docker-compose -f docker-compose.production.yml pull

# Start services
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose -f docker-compose.production.yml ps
```

### 4. Run Database Migrations

```bash
# Backup database first!
docker-compose -f docker-compose.production.yml exec backend \
  python scripts/backup_database.py

# Run migrations
docker-compose -f docker-compose.production.yml exec backend \
  alembic upgrade head

# Verify migration
docker-compose -f docker-compose.production.yml exec backend \
  alembic current
```

### 5. Verify Deployment

```bash
# Health check
curl https://api.yourplatform.com/health

# Expected response (200 OK):
# {
#   "status": "healthy",
#   "services": {
#     "database": {"status": "healthy", "connected": true},
#     "redis": {"status": "healthy", "connected": true}
#   }
# }

# Check logs
docker-compose -f docker-compose.production.yml logs -f backend
```

## Quick Commands

### Service Management

```bash
# Start all services
docker-compose -f docker-compose.production.yml up -d

# Stop all services
docker-compose -f docker-compose.production.yml down

# Restart backend
docker-compose -f docker-compose.production.yml restart backend

# View logs
docker-compose -f docker-compose.production.yml logs -f

# Check status
docker-compose -f docker-compose.production.yml ps
```

### Database Operations

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Rollback migration (1 step)
docker-compose exec backend python scripts/rollback_migration.py --steps 1

# Check current migration
docker-compose exec backend alembic current

# Create backup
docker-compose exec postgres pg_dump -U user database > backup.sql
```

### Monitoring

```bash
# Health check
curl https://api.yourplatform.com/health

# View backend logs
docker-compose logs -f backend

# View Celery worker logs
docker-compose logs -f celery_worker

# View Celery beat logs
docker-compose logs -f celery_beat

# Access Flower dashboard
open http://localhost:5555
```

## Rollback Procedures

### Application Rollback

```bash
# Stop current version
docker-compose -f docker-compose.production.yml down

# Pull previous version
docker pull registry.example.com/job-platform-backend:v0.9.0

# Update docker-compose.yml to use previous version
# Then start services
docker-compose -f docker-compose.production.yml up -d
```

### Database Rollback

```bash
# Option 1: Rollback migration
docker-compose exec backend python scripts/rollback_migration.py --steps 1

# Option 2: Restore from backup
docker-compose exec -T postgres psql -U user database < backup.sql
```

## Environment Variables Quick Reference

### Critical Security Variables

```bash
SECRET_KEY=<32+ char random string>
JWT_SECRET_KEY=<32+ char random string>
DEBUG=False
```

### Database (Requirement 16.8)

```bash
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=20
```

### Redis (Requirement 16.8)

```bash
REDIS_URL=redis://host:6379/0
REDIS_CACHE_DB=1
CELERY_BROKER_URL=redis://host:6379/0
CELERY_RESULT_BACKEND=redis://host:6379/0
```

### CORS (Requirement 13.4)

```bash
# Production domains only!
CORS_ORIGINS=https://yourplatform.com,https://www.yourplatform.com
```

### Stripe (Requirement 13.4)

```bash
# Use live keys (sk_live_, pk_live_)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Monitoring (Requirement 19.7)

```bash
SENTRY_DSN=https://...@sentry.io/...
```

### Alerting (Requirements 15.5, 15.7)

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=app_password
ADMIN_EMAIL=admin@yourplatform.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

## Health Check Endpoints

### GET /health

Returns 200 if healthy, 503 if unhealthy.

**Healthy Response:**

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

**Unhealthy Response (503):**

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

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs backend

# Check environment variables
docker-compose exec backend env | grep -E "DATABASE|REDIS|SECRET"

# Test database connection
docker-compose exec backend python -c "from app.db import check_db_health; print(check_db_health())"
```

### Database Connection Failed

```bash
# Check PostgreSQL is accessible
psql -h HOST -U USER -d DATABASE

# Check SSL requirement
# Ensure DATABASE_URL includes ?sslmode=require

# Check connection pooling
docker-compose exec backend python -c "from app.db import get_db_info; print(get_db_info())"
```

### Redis Connection Failed

```bash
# Check Redis is accessible
redis-cli -h HOST -p PORT ping

# Test from backend
docker-compose exec backend python -c "from app.core.redis import get_redis_client; get_redis_client().ping()"
```

### Migrations Failed

```bash
# Check current migration
docker-compose exec backend alembic current

# Check migration history
docker-compose exec backend alembic history

# Rollback and retry
docker-compose exec backend python scripts/rollback_migration.py --steps 1
docker-compose exec backend alembic upgrade head
```

### Health Check Failing

```bash
# Check health endpoint
curl -v https://api.yourplatform.com/health

# Check service logs
docker-compose logs backend

# Check database connectivity
docker-compose exec backend python -c "from app.db import check_db_health; print(check_db_health())"

# Check Redis connectivity
docker-compose exec backend python -c "from app.core.redis import get_redis_client; get_redis_client().ping()"
```

## Security Checklist

- [ ] DEBUG=False
- [ ] Strong SECRET_KEY (32+ chars)
- [ ] Strong JWT_SECRET_KEY (32+ chars)
- [ ] CORS_ORIGINS restricted to production domains
- [ ] Database uses SSL (sslmode=require)
- [ ] HTTPS enabled with valid certificate
- [ ] Stripe live keys (not test keys)
- [ ] Sentry configured for error tracking
- [ ] Rate limiting enabled
- [ ] CSRF protection enabled
- [ ] Security headers middleware active
- [ ] File upload validation enabled
- [ ] Secrets not in code/version control

## Post-Deployment Verification

1. **Health Check**: `curl https://api.yourplatform.com/health` → 200 OK
2. **API Docs**: `https://api.yourplatform.com/docs` → Accessible
3. **Authentication**: Test login/registration
4. **Job Search**: Test search functionality
5. **Job Posting**: Test employer job posting
6. **Applications**: Test job application
7. **Payments**: Test subscription upgrade
8. **Monitoring**: Check Sentry dashboard
9. **Alerts**: Verify email/Slack alerts work
10. **Logs**: Check for errors in logs

## Support Contacts

- **Technical Issues**: admin@yourplatform.com
- **Sentry Dashboard**: https://sentry.io/organizations/your-org
- **Documentation**: See PRODUCTION_DEPLOYMENT_GUIDE.md
