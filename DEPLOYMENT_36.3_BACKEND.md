# Task 36.3: Deploy FastAPI Backend

**Requirement**: 16.8 - Backend deployment with auto-scaling, health checks, and environment configuration

## Overview

This guide covers deploying the FastAPI backend on Railway or Render's free tier with:
- Automatic deployments from GitHub
- Environment variable management
- Health check monitoring
- Auto-scaling (within free tier limits)
- SSL/HTTPS enabled
- Public API endpoint

## Prerequisites

- [ ] PostgreSQL deployed (Task 36.1)
- [ ] Redis deployed (Task 36.2)
- [ ] Railway or Render account
- [ ] GitHub repository with backend code
- [ ] Dockerfile in `backend/` directory

---

## Option A: Railway (Recommended)

### Step 1: Add Backend Service to Project

1. **Open Railway Project**:
   - Go to your Railway project (created in Task 36.2)
   - You should see Redis service already deployed

2. **Add New Service**:
   - Click "New" button
   - Select "GitHub Repo"
   - Choose your repository
   - Railway will detect the Dockerfile

### Step 2: Configure Build Settings

1. **Click on Backend Service**:
   - Railway creates a service card
   - Click on it to open settings

2. **Configure Build**:
   - Go to **Settings** tab
   - Scroll to **Build** section
   - Set:
     - **Builder**: Dockerfile
     - **Dockerfile Path**: `backend/Dockerfile`
     - **Root Directory**: `backend`
   - Click "Save"

3. **Configure Deploy**:
   - Scroll to **Deploy** section
   - Set **Custom Start Command**:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Note**: Railway automatically sets `$PORT` variable

### Step 3: Configure Environment Variables

1. **Go to Variables Tab**:
   - Click **Variables** in the service menu
   - Click "Raw Editor" for bulk paste

2. **Add All Environment Variables**:

```bash
# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================
APP_NAME=Job Aggregation Platform
APP_ENV=production
DEBUG=False
API_HOST=0.0.0.0
API_PORT=$PORT
API_RELOAD=False

# CRITICAL: Generate strong secrets
# Run: openssl rand -hex 32
SECRET_KEY=REPLACE_WITH_GENERATED_SECRET_KEY
JWT_SECRET_KEY=REPLACE_WITH_GENERATED_JWT_SECRET_KEY
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# ============================================================================
# DATABASE CONFIGURATION (from Task 36.1)
# ============================================================================
DATABASE_URL=postgresql://postgres:PASSWORD@db.xxxxxxxxxxxxx.supabase.co:6543/postgres?sslmode=require
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=20

# ============================================================================
# REDIS CONFIGURATION (from Task 36.2)
# ============================================================================
# Use Railway's internal Redis URL for better performance
REDIS_URL=${{Redis.REDIS_URL}}
REDIS_CACHE_DB=1
CELERY_BROKER_URL=${{Redis.REDIS_URL}}
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP=True
CELERY_RESULT_EXPIRES=3600

# ============================================================================
# STRIPE PAYMENT INTEGRATION
# ============================================================================
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# ============================================================================
# EXTERNAL API KEYS
# ============================================================================
INDEED_API_KEY=your_indeed_api_key
LINKEDIN_RSS_URLS=https://linkedin.com/feed1,https://linkedin.com/feed2

# ============================================================================
# SCRAPING CONFIGURATION
# ============================================================================
SCRAPING_USER_AGENT=Mozilla/5.0 (compatible; JobBot/1.0; +https://yourplatform.com/bot)
SCRAPING_RATE_LIMIT_LINKEDIN=10
SCRAPING_RATE_LIMIT_INDEED=20
SCRAPING_RATE_LIMIT_NAUKRI=5
SCRAPING_RATE_LIMIT_MONSTER=5

# ============================================================================
# FILE STORAGE (Supabase)
# ============================================================================
STORAGE_BACKEND=supabase
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# ============================================================================
# MONITORING (add after Task 36.6)
# ============================================================================
SENTRY_DSN=https://xxxxxxxxxxxxx@sentry.io/project_id

# ============================================================================
# ALERTING
# ============================================================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
ADMIN_EMAIL=admin@yourplatform.com
FROM_EMAIL=noreply@yourplatform.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# ============================================================================
# CORS (update after Task 36.5)
# ============================================================================
CORS_ORIGINS=https://your-frontend.vercel.app

# ============================================================================
# LOGGING
# ============================================================================
LOG_LEVEL=INFO
LOG_FORMAT=json
```

3. **Generate Secrets**:
   
   Run these commands locally to generate secure secrets:
   ```bash
   # Generate SECRET_KEY
   openssl rand -hex 32
   
   # Generate JWT_SECRET_KEY
   openssl rand -hex 32
   ```
   
   Replace the placeholder values in the environment variables.

4. **Railway Variable References**:
   
   Notice `${{Redis.REDIS_URL}}` - this automatically references the Redis service URL. Railway will replace it with the actual URL.

### Step 4: Configure Health Checks

1. **Go to Settings → Health Check**:
   - Enable health checks
   - Set:
     - **Path**: `/health`
     - **Timeout**: 10 seconds
     - **Interval**: 30 seconds
     - **Restart Threshold**: 3 failures

2. **Verify Health Endpoint Exists**:
   
   Your `backend/app/main.py` should have:
   ```python
   @app.get("/health")
   async def health_check():
       return {
           "status": "healthy",
           "timestamp": datetime.now().isoformat()
       }
   ```

### Step 5: Enable Public Networking

1. **Go to Settings → Networking**:
   - Click "Generate Domain"
   - Railway provides a public URL:
     ```
     https://your-service-production.up.railway.app
     ```
   - Save this URL - you'll need it for:
     - Frontend API configuration
     - Stripe webhook configuration
     - Testing

2. **Custom Domain** (Optional):
   - Click "Add Custom Domain"
   - Enter your domain: `api.yourplatform.com`
   - Add CNAME record to your DNS:
     ```
     CNAME api.yourplatform.com -> your-service-production.up.railway.app
     ```
   - Railway automatically provisions SSL certificate

### Step 6: Deploy

1. **Trigger Deployment**:
   - Railway automatically deploys on push to main branch
   - Or click "Deploy" button to trigger manual deployment

2. **Monitor Deployment**:
   - Go to **Deployments** tab
   - Watch build logs in real-time
   - Look for:
     ```
     Building Dockerfile...
     Successfully built image
     Starting deployment...
     Deployment successful
     ```

3. **Check for Errors**:
   - If build fails, check logs for errors
   - Common issues:
     - Missing dependencies in requirements.txt
     - Dockerfile syntax errors
     - Port configuration issues

### Step 7: Run Database Migrations

1. **Access Service Shell**:
   - Click on backend service
   - Click "Connect" → "Shell"
   - This opens a terminal in your running container

2. **Run Migrations**:
   ```bash
   alembic upgrade head
   ```

3. **Verify Migrations**:
   ```bash
   alembic current
   # Should show: [latest_revision] (head)
   ```

4. **Check Tables**:
   ```bash
   python -c "from app.db.session import SessionLocal; from app.models.job import Job; db = SessionLocal(); print(f'Jobs: {db.query(Job).count()}'); db.close()"
   ```

### Step 8: Test API Endpoints

1. **Health Check**:
   ```bash
   curl https://your-service-production.up.railway.app/health
   ```
   
   Expected response:
   ```json
   {
     "status": "healthy",
     "timestamp": "2024-01-15T10:30:00Z"
   }
   ```

2. **API Documentation**:
   ```bash
   curl https://your-service-production.up.railway.app/docs
   ```
   
   Or open in browser: `https://your-service-production.up.railway.app/docs`

3. **Test Authentication**:
   ```bash
   curl -X POST https://your-service-production.up.railway.app/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "SecurePass123!",
       "user_type": "job_seeker"
     }'
   ```

4. **Test Job Search**:
   ```bash
   curl https://your-service-production.up.railway.app/api/jobs/search?query=developer
   ```

### Step 9: Configure Auto-Scaling

Railway free tier doesn't support true auto-scaling, but you can configure resource limits:

1. **Go to Settings → Resources**:
   - Free tier limits:
     - **Memory**: 512MB
     - **CPU**: Shared
     - **Disk**: 1GB ephemeral

2. **Optimize for Free Tier**:
   - Keep memory usage under 400MB
   - Use connection pooling
   - Implement caching
   - Offload heavy tasks to Celery

---

## Option B: Render

### Step 1: Create Web Service

1. **Go to Render Dashboard**:
   - Click "New" → "Web Service"

2. **Connect Repository**:
   - Click "Connect account" to link GitHub
   - Select your repository
   - Click "Connect"

3. **Configure Service**:
   - **Name**: `job-platform-backend`
   - **Region**: Oregon (US West) or Frankfurt (Europe)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: Docker
   - **Plan**: Free

### Step 2: Configure Build

1. **Docker Configuration**:
   - Render auto-detects Dockerfile
   - **Dockerfile Path**: `Dockerfile` (relative to root directory)

2. **Start Command**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

### Step 3: Add Environment Variables

1. **Scroll to Environment Variables**:
   - Click "Add Environment Variable"
   - Or use "Add from .env" to bulk import

2. **Add All Variables**:
   - Copy the same variables from Railway section above
   - Replace Railway-specific references:
     - `${{Redis.REDIS_URL}}` → Your Render Redis URL
     - `$PORT` → Automatically set by Render

### Step 4: Configure Health Check

1. **Health Check Path**:
   - Set to: `/health`

2. **Auto-Deploy**:
   - Enable "Auto-Deploy" for automatic deployments on push

### Step 5: Deploy

1. **Click "Create Web Service"**:
   - Render starts building immediately
   - Monitor logs in real-time

2. **Wait for Deployment**:
   - First deployment takes 5-10 minutes
   - Subsequent deployments are faster

3. **Get Service URL**:
   - Render provides: `https://job-platform-backend.onrender.com`
   - Save this URL

### Step 6: Run Migrations

1. **Access Shell**:
   - Click "Shell" in service dashboard
   - Wait for shell to connect

2. **Run Migrations**:
   ```bash
   alembic upgrade head
   ```

### Step 7: Test Deployment

Same as Railway Step 8 above, but use your Render URL.

---

## Configuration Summary

### Environment Variables Checklist

- [ ] `SECRET_KEY` - Generated with `openssl rand -hex 32`
- [ ] `JWT_SECRET_KEY` - Generated with `openssl rand -hex 32`
- [ ] `DATABASE_URL` - From Supabase (Task 36.1)
- [ ] `REDIS_URL` - From Railway/Render (Task 36.2)
- [ ] `STRIPE_SECRET_KEY` - From Stripe dashboard
- [ ] `STRIPE_PUBLISHABLE_KEY` - From Stripe dashboard
- [ ] `STRIPE_WEBHOOK_SECRET` - From Stripe webhook settings
- [ ] `SUPABASE_URL` - From Supabase project settings
- [ ] `SUPABASE_KEY` - From Supabase project settings
- [ ] `CORS_ORIGINS` - Will update after frontend deployment
- [ ] `SENTRY_DSN` - Will add after Task 36.6

### Service URLs to Save

```bash
# Backend API URL
BACKEND_URL=https://your-service-production.up.railway.app

# API Documentation
API_DOCS=https://your-service-production.up.railway.app/docs

# Health Check
HEALTH_CHECK=https://your-service-production.up.railway.app/health
```

## Testing Checklist

- [ ] Service deployed successfully
- [ ] Health check returns 200
- [ ] API documentation accessible at `/docs`
- [ ] Database connection works
- [ ] Redis connection works
- [ ] Can register new user
- [ ] Can login and get JWT token
- [ ] Can search for jobs
- [ ] CORS configured (will test after frontend deployment)
- [ ] Logs show no errors

## Troubleshooting

### Build Fails

**Problem**: Docker build fails

**Solutions**:
1. Check Dockerfile syntax
2. Verify all dependencies in requirements.txt
3. Check build logs for specific error
4. Test build locally:
   ```bash
   cd backend
   docker build -t test-backend .
   ```

### Service Crashes on Startup

**Problem**: Service starts but immediately crashes

**Solutions**:
1. Check logs for error messages
2. Verify environment variables are set
3. Test database connection:
   ```python
   from app.db.session import SessionLocal
   db = SessionLocal()
   print("DB connected!")
   ```
4. Test Redis connection:
   ```python
   from app.core.redis import get_redis_client
   print(get_redis_client().ping())
   ```

### Database Connection Fails

**Problem**: Cannot connect to Supabase

**Solutions**:
1. Verify `DATABASE_URL` is correct
2. Check `?sslmode=require` is included
3. Verify Supabase project is not paused
4. Test connection from local machine
5. Check Supabase connection limits

### Redis Connection Fails

**Problem**: Cannot connect to Redis

**Solutions**:
1. Verify `REDIS_URL` is correct
2. Check Redis service is running
3. Use internal URL for Railway/Render services
4. Test connection manually

### Health Check Fails

**Problem**: Health check endpoint returns 503

**Solutions**:
1. Check `/health` endpoint exists
2. Verify database and Redis connections in health check
3. Check logs for specific error
4. Test health endpoint manually:
   ```bash
   curl https://your-service.up.railway.app/health
   ```

### CORS Errors

**Problem**: Frontend can't connect due to CORS

**Solutions**:
1. Verify `CORS_ORIGINS` includes frontend URL
2. Check CORS middleware is configured
3. Ensure frontend URL is correct (no trailing slash)
4. Test with curl:
   ```bash
   curl -H "Origin: https://your-frontend.vercel.app" \
        -H "Access-Control-Request-Method: GET" \
        -X OPTIONS \
        https://your-backend.up.railway.app/api/jobs
   ```

## Performance Optimization

### 1. Connection Pooling

Already configured in environment variables:
```bash
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=20
```

### 2. Caching

Implement Redis caching for expensive queries:
```python
from app.core.redis import get_redis_client
import json

def get_cached_jobs(cache_key: str):
    redis_client = get_redis_client()
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    return None

def set_cached_jobs(cache_key: str, data: dict, ttl: int = 300):
    redis_client = get_redis_client()
    redis_client.setex(cache_key, ttl, json.dumps(data))
```

### 3. Database Indexes

Verify indexes are created (from Task 33):
```bash
python backend/scripts/verify_indexes.py
```

### 4. Monitoring

Monitor key metrics:
- Response times
- Error rates
- Memory usage
- Database query performance

## Free Tier Limits

### Railway Free Tier

- **Memory**: 512MB RAM
- **CPU**: Shared
- **Disk**: 1GB ephemeral
- **Bandwidth**: Unlimited
- **Uptime**: 99.9% SLA
- **Cost**: $0/month (with $5 credit)

### Render Free Tier

- **Memory**: 512MB RAM
- **CPU**: Shared (0.1 CPU)
- **Disk**: Ephemeral
- **Bandwidth**: 100GB/month
- **Spin Down**: After 15 min inactivity
- **Spin Up**: 30-60 seconds
- **Cost**: $0/month

**Note**: Render free tier spins down after inactivity, causing slow first requests.

## Next Steps

After completing backend deployment:

1. ✅ Backend deployed and running
2. ✅ Health checks passing
3. ✅ Database migrations applied
4. ✅ API endpoints accessible
5. ➡️ **Next**: Deploy Celery Workers (Task 36.4)
6. ➡️ Deploy Frontend (Task 36.5)
7. ➡️ Update CORS_ORIGINS with frontend URL

## Support Resources

- **Railway Documentation**: https://docs.railway.app
- **Render Documentation**: https://render.com/docs
- **FastAPI Documentation**: https://fastapi.tiangolo.com
- **Railway Discord**: https://discord.gg/railway
- **Render Community**: https://community.render.com

---

**Task 36.3 Complete!** ✅

Your FastAPI backend is now deployed and serving API requests.
