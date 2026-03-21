# Job Aggregation Platform - Deployment Documentation

## Overview

This document provides comprehensive deployment instructions for the Job Aggregation Platform. The platform uses a microservices architecture deployed across multiple free-tier hosting services.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Environment Variables](#environment-variables)
4. [Service Deployment](#service-deployment)
5. [Database Migrations](#database-migrations)
6. [Backup and Recovery](#backup-and-recovery)
7. [Monitoring and Health Checks](#monitoring-and-health-checks)
8. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Internet                             │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
    ┌────▼─────┐          ┌─────▼────┐
    │  Vercel  │          │  Sentry  │
    │ Frontend │          │  Errors  │
    └────┬─────┘          └──────────┘
         │
         │ HTTPS
         │
    ┌────▼──────────────────────────────────────┐
    │         Railway/Render                     │
    │  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
    │  │ FastAPI  │  │  Celery  │  │  Redis  │ │
    │  │ Backend  │  │ Workers  │  │         │ │
    │  └────┬─────┘  └────┬─────┘  └────┬────┘ │
    └───────┼─────────────┼─────────────┼──────┘
            │             │             │
            └─────────────┴─────────────┘
                          │
                    ┌─────▼─────┐
                    │ Supabase  │
                    │PostgreSQL │
                    └───────────┘
```

### Services

| Service | Platform | Purpose |
|---------|----------|---------|
| PostgreSQL | Supabase | Primary database |
| Redis | Railway/Render | Cache and task queue |
| FastAPI Backend | Railway/Render | REST API server |
| Celery Workers | Railway/Render | Background tasks |
| Celery Beat | Railway/Render | Task scheduler |
| Next.js Frontend | Vercel | Web application |
| Sentry | Sentry.io | Error tracking |

---

## Prerequisites

Before deploying, ensure you have:

- [ ] GitHub account with repository access
- [ ] Supabase account (https://supabase.com)
- [ ] Railway account (https://railway.app) OR Render account (https://render.com)
- [ ] Vercel account (https://vercel.com)
- [ ] Sentry account (https://sentry.io)
- [ ] Stripe account (https://stripe.com)
- [ ] Domain name (optional but recommended)
- [ ] Git repository with code pushed to main branch

### Required Tools

- Git
- Node.js 18+ (for local testing)
- Python 3.11+ (for local testing)
- PostgreSQL client (for database management)
- Redis CLI (for cache management)

---

## Environment Variables

### Backend Environment Variables

Create a `.env.production` file with the following variables:

```bash
# Application
APP_NAME=Job Aggregation Platform
APP_ENV=production
DEBUG=False
SECRET_KEY=<generate-with-openssl-rand-hex-32>
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=False

# Database (from Supabase)
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:6543/postgres
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=20

# Redis (from Railway/Render)
REDIS_URL=redis://default:[PASSWORD]@[HOST]:[PORT]
REDIS_CACHE_DB=1
CELERY_BROKER_URL=redis://default:[PASSWORD]@[HOST]:[PORT]/0
CELERY_RESULT_BACKEND=redis://default:[PASSWORD]@[HOST]:[PORT]/0

# JWT
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Stripe
STRIPE_SECRET_KEY=sk_live_your_key
STRIPE_PUBLISHABLE_KEY=pk_live_your_key
STRIPE_WEBHOOK_SECRET=whsec_your_secret

# External APIs
INDEED_API_KEY=your_indeed_api_key
LINKEDIN_RSS_URLS=https://www.linkedin.com/jobs/...

# Scraping
SCRAPING_USER_AGENT=Mozilla/5.0 (compatible; JobBot/1.0)
SCRAPING_RATE_LIMIT_LINKEDIN=10
SCRAPING_RATE_LIMIT_INDEED=20
SCRAPING_RATE_LIMIT_NAUKRI=5
SCRAPING_RATE_LIMIT_MONSTER=5

# Storage
STORAGE_BACKEND=supabase
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Monitoring
SENTRY_DSN=https://xxxxxxxxxxxxx@o123456.ingest.sentry.io/7890123

# Alerting
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
ADMIN_EMAIL=admin@jobplatform.com
FROM_EMAIL=noreply@jobplatform.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# CORS
CORS_ORIGINS=https://your-frontend-domain.vercel.app

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Frontend Environment Variables

Create a `.env.production` file with:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app
NEXT_PUBLIC_API_BASE_PATH=/api

# Stripe
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_your_key

# Environment
NEXT_PUBLIC_ENV=production

# Analytics (optional)
NEXT_PUBLIC_GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_FEATURED_JOBS=true
```

### Generating Secret Keys

```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate JWT_SECRET_KEY
openssl rand -hex 32
```

---

## Service Deployment

### 1. PostgreSQL Database (Supabase)

#### Step 1: Create Project

1. Go to https://supabase.com and sign in
2. Click "New Project"
3. Fill in details:
   - Name: `job-aggregation-platform`
   - Database Password: Generate strong password
   - Region: Choose closest to users
   - Plan: Free
4. Wait ~2 minutes for provisioning

#### Step 2: Get Connection Details

1. Go to **Settings** → **Database**
2. Copy connection pooling URL (port 6543):
   ```
   postgresql://postgres:[PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:6543/postgres
   ```
3. Save as `DATABASE_URL` environment variable

#### Step 3: Configure Connection Pooling

Connection pooling is enabled by default on port 6543:
- Pool mode: Transaction
- Default pool size: 15
- Max client connections: 200

#### Step 4: Verify Backups

1. Go to **Settings** → **Database** → **Backup and Restore**
2. Verify daily backups are enabled (7-day retention)
3. Point-in-time recovery available for last 7 days

---

### 2. Redis Instance (Railway)

#### Step 1: Create Railway Project

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository

#### Step 2: Add Redis Service

1. Click "New" → "Database" → "Add Redis"
2. Railway provisions Redis automatically
3. Copy `REDIS_URL` from Variables tab

#### Step 3: Configure Persistence

1. Go to Redis service → **Settings** → **Deploy**
2. Add custom start command:
   ```bash
   redis-server --appendonly yes --appendfsync everysec
   ```
3. This enables AOF persistence with 1-second fsync

#### Step 4: Test Connection

```bash
# Using Railway CLI
railway connect redis

# Test
PING
# Should return: PONG
```

---

### 3. FastAPI Backend (Railway)

#### Step 1: Add Backend Service

1. In Railway project, click "New" → "GitHub Repo"
2. Select your repository
3. Railway detects Dockerfile automatically

#### Step 2: Configure Build

1. Go to **Settings** → **Build**
2. Set:
   - Builder: Dockerfile
   - Dockerfile Path: `backend/Dockerfile`
   - Root Directory: `backend`

#### Step 3: Add Environment Variables

1. Go to **Variables** tab
2. Click "Raw Editor" and paste all backend environment variables
3. Use Railway variable references:
   ```bash
   REDIS_URL=${{Redis.REDIS_URL}}
   ```

#### Step 4: Configure Start Command

1. Go to **Settings** → **Deploy**
2. Set custom start command:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

#### Step 5: Enable Health Checks

1. Go to **Settings** → **Health Check**
2. Set:
   - Path: `/health`
   - Timeout: 10 seconds
   - Interval: 30 seconds

#### Step 6: Generate Public URL

1. Go to **Settings** → **Networking**
2. Click "Generate Domain"
3. Save URL: `https://your-service.up.railway.app`

#### Step 7: Deploy

Railway automatically deploys on push to main branch.

Monitor deployment:
1. Go to **Deployments** tab
2. Check build logs for errors
3. Verify service is running

---

### 4. Celery Workers (Railway)

#### Step 1: Add Celery Worker Service

1. Click "New" → "GitHub Repo"
2. Select same repository
3. Name: `celery-worker`

#### Step 2: Configure Build

Same as backend:
- Builder: Dockerfile
- Dockerfile Path: `backend/Dockerfile`
- Root Directory: `backend`

#### Step 3: Copy Environment Variables

1. Go to **Variables** tab
2. Click "Reference Variables" → Select backend service
3. This copies all environment variables

#### Step 4: Set Start Command

```bash
celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2
```

#### Step 5: Add Celery Beat Service

1. Create another service: `celery-beat`
2. Same build configuration
3. Start command:
   ```bash
   celery -A app.tasks.celery_app beat --loglevel=info
   ```

#### Step 6: Verify Workers

Check logs for:
```
[INFO/MainProcess] Connected to redis://...
[INFO/MainProcess] celery@hostname ready.
```

---

### 5. Next.js Frontend (Vercel)

#### Step 1: Import Project

1. Go to https://vercel.com
2. Click "Add New" → "Project"
3. Import GitHub repository
4. Vercel detects Next.js automatically

#### Step 2: Configure Project

1. Framework Preset: Next.js
2. Root Directory: `frontend`
3. Build Command: `npm run build`
4. Output Directory: `.next`

#### Step 3: Add Environment Variables

1. Click "Environment Variables"
2. Add all frontend environment variables
3. Set for Production, Preview, and Development

#### Step 4: Deploy

1. Click "Deploy"
2. Wait 2-3 minutes for build
3. Vercel provides URL: `https://your-project.vercel.app`

#### Step 5: Update Backend CORS

1. Go to Railway backend service
2. Update `CORS_ORIGINS`:
   ```bash
   CORS_ORIGINS=https://your-project.vercel.app
   ```
3. Redeploy backend

#### Step 6: Configure Custom Domain (Optional)

1. Go to **Settings** → **Domains**
2. Add domain: `yourplatform.com`
3. Configure DNS:
   ```
   Type: CNAME
   Name: @
   Value: cname.vercel-dns.com
   ```
4. Vercel provisions SSL automatically

---

### 6. Sentry Error Tracking

#### Step 1: Create Backend Project

1. Go to https://sentry.io
2. Click "Create Project"
3. Platform: Python
4. Name: `job-platform-backend`
5. Copy DSN

#### Step 2: Create Frontend Project

1. Create another project
2. Platform: Next.js
3. Name: `job-platform-frontend`
4. Copy DSN

#### Step 3: Configure Backend

1. Add to Railway backend environment:
   ```bash
   SENTRY_DSN=https://xxxxxxxxxxxxx@o123456.ingest.sentry.io/7890123
   ```
2. Redeploy backend

#### Step 4: Configure Frontend

1. Install Sentry SDK:
   ```bash
   cd frontend
   npm install @sentry/nextjs
   npx @sentry/wizard@latest -i nextjs
   ```
2. Enter frontend DSN when prompted
3. Commit changes and push

#### Step 5: Test Error Reporting

Backend test:
```python
# Add to backend/app/main.py
@app.get("/test-sentry")
def test_sentry():
    raise Exception("Test Sentry error")
```

Visit: `https://your-backend.up.railway.app/test-sentry`

Check Sentry dashboard for error.

#### Step 6: Configure Alerts

1. Go to **Alerts** → "Create Alert Rule"
2. Condition: When an event occurs
3. Action: Send notification to email/Slack
4. Save rule

---

## Database Migrations

### Running Migrations

#### Option 1: Railway Shell

1. Go to backend service
2. Click **Settings** → "Connect" → "Shell"
3. Run migrations:
   ```bash
   alembic upgrade head
   ```

#### Option 2: One-Time Job

1. Click "New" → "Empty Service"
2. Link to same repo
3. Set start command:
   ```bash
   alembic upgrade head
   ```
4. Deploy once, then delete service

#### Option 3: Local with Production Database

```bash
# Set DATABASE_URL to production
export DATABASE_URL="postgresql://postgres:..."

# Run migrations
cd backend
alembic upgrade head
```

### Creating New Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Add new column"

# Review generated migration
cat alembic/versions/xxx_add_new_column.py

# Test locally
alembic upgrade head

# Commit and push
git add alembic/versions/xxx_add_new_column.py
git commit -m "Add migration: Add new column"
git push
```

### Migration Rollback

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# Rollback all migrations
alembic downgrade base
```

### Migration Best Practices

1. **Always test migrations locally first**
2. **Backup database before running migrations**
3. **Run migrations during low-traffic periods**
4. **Have rollback plan ready**
5. **Monitor application after migration**

### Migration Checklist

- [ ] Test migration on local database
- [ ] Backup production database
- [ ] Review migration SQL
- [ ] Plan rollback strategy
- [ ] Schedule maintenance window
- [ ] Run migration
- [ ] Verify data integrity
- [ ] Monitor application logs
- [ ] Test critical functionality

---

## Backup and Recovery

### Database Backups

#### Automated Backups (Supabase)

Supabase provides automatic backups:
- **Daily backups**: Retained for 7 days
- **Point-in-time recovery**: Last 7 days
- **Location**: Same region as database

#### Manual Backups

```bash
# Backup entire database
pg_dump -h db.xxxxxxxxxxxxx.supabase.co \
  -U postgres \
  -d postgres \
  -F c \
  -f backup_$(date +%Y%m%d).dump

# Backup specific tables
pg_dump -h db.xxxxxxxxxxxxx.supabase.co \
  -U postgres \
  -d postgres \
  -t jobs -t employers \
  -F c \
  -f backup_tables_$(date +%Y%m%d).dump
```

#### Restore from Backup

```bash
# Restore entire database
pg_restore -h db.xxxxxxxxxxxxx.supabase.co \
  -U postgres \
  -d postgres \
  -c \
  backup_20240115.dump

# Restore specific tables
pg_restore -h db.xxxxxxxxxxxxx.supabase.co \
  -U postgres \
  -d postgres \
  -t jobs \
  backup_tables_20240115.dump
```

### Redis Backups

#### Automated Backups (Railway)

Railway Redis with AOF persistence:
- **Append-only file**: Synced every second
- **Automatic recovery**: On restart

#### Manual Backup

```bash
# Connect to Redis
railway connect redis

# Trigger save
BGSAVE

# Check save status
LASTSAVE
```

### Application State Backups

#### Environment Variables

```bash
# Export Railway environment variables
railway variables > env_backup_$(date +%Y%m%d).txt

# Export Vercel environment variables
vercel env pull env_backup_$(date +%Y%m%d).env
```

#### Code Backups

```bash
# Tag release
git tag -a v1.0.0 -m "Production release 1.0.0"
git push origin v1.0.0

# Create GitHub release
gh release create v1.0.0 --title "v1.0.0" --notes "Production release"
```

### Disaster Recovery Plan

#### Scenario 1: Database Corruption

1. Stop all services writing to database
2. Restore from latest backup
3. Run migrations if needed
4. Verify data integrity
5. Restart services
6. Monitor for errors

#### Scenario 2: Service Outage

1. Check service status pages
2. Review service logs
3. Restart affected services
4. Verify health checks
5. Monitor recovery

#### Scenario 3: Data Loss

1. Identify scope of data loss
2. Restore from point-in-time backup
3. Replay transactions if possible
4. Notify affected users
5. Document incident

### Recovery Time Objectives (RTO)

| Service | RTO | RPO |
|---------|-----|-----|
| Database | 1 hour | 24 hours |
| Redis | 15 minutes | 1 second |
| Backend | 15 minutes | N/A |
| Frontend | 5 minutes | N/A |

---

## Monitoring and Health Checks

### Health Check Endpoints

#### Backend Health Check

```bash
curl https://your-backend.up.railway.app/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "database": {
      "status": "healthy",
      "connected": true,
      "pool_size": 5,
      "overflow": 0
    },
    "redis": {
      "status": "healthy",
      "connected": true,
      "ping": "ok"
    }
  }
}
```

#### Frontend Health Check

```bash
curl https://your-project.vercel.app/
```

### Monitoring Tools

#### Sentry (Error Tracking)

- Dashboard: https://sentry.io
- Monitors: Unhandled exceptions, API errors
- Alerts: Email/Slack on critical errors

#### Railway/Render (Infrastructure)

- Dashboard: https://railway.app
- Monitors: CPU, memory, disk usage
- Alerts: Service crashes, deployment failures

#### Vercel (Frontend)

- Dashboard: https://vercel.com
- Monitors: Build status, deployment errors
- Alerts: Build failures, runtime errors

### Custom Monitoring

#### API Response Times

```python
# Tracked automatically by middleware
# View in logs or Sentry performance monitoring
```

#### Scraping Success Rates

```bash
# Query scraping_tasks table
SELECT 
  source_platform,
  COUNT(*) as total,
  SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful,
  ROUND(100.0 * SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM scraping_tasks
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY source_platform;
```

#### Database Connection Pool

```bash
# Check pool usage
curl https://your-backend.up.railway.app/health | jq '.services.database'
```

### Alert Configuration

#### Critical Alerts

- Database connection failures
- Redis connection failures
- 3+ consecutive scraping failures
- API error rate > 5%
- Service crashes

#### Warning Alerts

- High response times (>1 second)
- Database pool near capacity
- Redis memory > 80%
- Scraping success rate < 90%

### Monitoring Checklist

Daily:
- [ ] Check Sentry for new errors
- [ ] Review service health dashboards
- [ ] Check scraping success rates

Weekly:
- [ ] Review database performance
- [ ] Check Redis memory usage
- [ ] Review API response times
- [ ] Check backup status

Monthly:
- [ ] Review security logs
- [ ] Update dependencies
- [ ] Review cost and usage
- [ ] Test disaster recovery

---

## Troubleshooting

### Common Issues

#### Issue: Backend Won't Start

**Symptoms**: Service crashes on startup

**Diagnosis**:
```bash
# Check logs
railway logs

# Common causes:
# - Missing environment variables
# - Database connection failure
# - Redis connection failure
```

**Solutions**:
1. Verify all environment variables are set
2. Test database connection:
   ```bash
   psql $DATABASE_URL -c "SELECT 1"
   ```
3. Test Redis connection:
   ```bash
   redis-cli -u $REDIS_URL ping
   ```

---

#### Issue: Celery Workers Not Processing Tasks

**Symptoms**: Tasks stuck in queue

**Diagnosis**:
```bash
# Check worker logs
railway logs --service celery-worker

# Check Redis queue
redis-cli -u $REDIS_URL
LLEN celery
```

**Solutions**:
1. Restart worker service
2. Check Redis connection
3. Verify worker is connected:
   ```bash
   # Should see: celery@hostname ready
   ```

---

#### Issue: Frontend Can't Connect to Backend

**Symptoms**: API calls fail with CORS errors

**Diagnosis**:
```bash
# Check browser console
# Look for CORS error messages

# Verify backend CORS configuration
curl -H "Origin: https://your-project.vercel.app" \
  -H "Access-Control-Request-Method: GET" \
  -X OPTIONS \
  https://your-backend.up.railway.app/api/jobs
```

**Solutions**:
1. Verify `NEXT_PUBLIC_API_URL` is correct
2. Update backend `CORS_ORIGINS`:
   ```bash
   CORS_ORIGINS=https://your-project.vercel.app
   ```
3. Redeploy backend

---

#### Issue: Database Connection Pool Exhausted

**Symptoms**: "Too many connections" errors

**Diagnosis**:
```bash
# Check pool status
curl https://your-backend.up.railway.app/health | jq '.services.database'

# Check active connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity"
```

**Solutions**:
1. Increase `DATABASE_MAX_OVERFLOW`
2. Check for connection leaks in code
3. Restart backend service
4. Consider upgrading Supabase plan

---

#### Issue: Redis Memory Full

**Symptoms**: Redis operations fail

**Diagnosis**:
```bash
redis-cli -u $REDIS_URL
INFO memory
```

**Solutions**:
1. Clear old cache keys:
   ```bash
   redis-cli -u $REDIS_URL
   FLUSHDB
   ```
2. Reduce cache TTL
3. Implement cache eviction policy
4. Upgrade to paid Redis plan

---

#### Issue: Migrations Fail

**Symptoms**: Alembic migration errors

**Diagnosis**:
```bash
# Check current version
alembic current

# Check migration history
alembic history
```

**Solutions**:
1. Rollback to previous version:
   ```bash
   alembic downgrade -1
   ```
2. Fix migration file
3. Test locally before redeploying
4. If stuck, manually fix database and stamp version:
   ```bash
   alembic stamp head
   ```

---

### Getting Help

#### Service Status Pages

- Railway: https://status.railway.app
- Render: https://status.render.com
- Vercel: https://vercel-status.com
- Supabase: https://status.supabase.com

#### Documentation

- Railway: https://docs.railway.app
- Render: https://render.com/docs
- Vercel: https://vercel.com/docs
- Supabase: https://supabase.com/docs

#### Community Support

- Railway Discord
- Render Community Forum
- Vercel Discord
- Stack Overflow

#### Emergency Contacts

- On-call engineer: oncall@jobplatform.com
- DevOps team: devops@jobplatform.com
- Security team: security@jobplatform.com

---

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing
- [ ] Code reviewed and approved
- [ ] Environment variables configured
- [ ] Database migrations tested
- [ ] Backup created
- [ ] Rollback plan documented

### Deployment

- [ ] Deploy database migrations
- [ ] Deploy backend service
- [ ] Deploy Celery workers
- [ ] Deploy frontend
- [ ] Verify health checks
- [ ] Test critical functionality

### Post-Deployment

- [ ] Monitor error rates
- [ ] Check service logs
- [ ] Verify scraping tasks running
- [ ] Test user flows
- [ ] Update documentation
- [ ] Notify team of deployment

---

## Conclusion

This deployment documentation provides comprehensive instructions for deploying and maintaining the Job Aggregation Platform. For questions or issues, refer to the troubleshooting section or contact the DevOps team.

**Last Updated**: 2024-01-15

**Version**: 1.0.0
