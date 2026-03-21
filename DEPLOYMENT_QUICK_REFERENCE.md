# Deployment Quick Reference

Quick reference for deploying the Job Aggregation Platform to production.

## Service URLs

```bash
# PostgreSQL (Supabase)
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:6543/postgres?sslmode=require

# Redis (Railway)
REDIS_URL=redis://default:[PASSWORD]@redis.railway.internal:6379

# Backend (Railway)
BACKEND_URL=https://your-service-production.up.railway.app
HEALTH_CHECK=https://your-service-production.up.railway.app/health
API_DOCS=https://your-service-production.up.railway.app/docs

# Frontend (Vercel)
FRONTEND_URL=https://your-project.vercel.app

# Sentry
BACKEND_SENTRY_DSN=https://xxxxxxxxxxxxx@o123456.ingest.sentry.io/7890123
FRONTEND_SENTRY_DSN=https://yyyyyyyyyyyyy@o123456.ingest.sentry.io/7890124
```

## Deployment Order

1. **PostgreSQL** (Supabase) - Task 36.1
2. **Redis** (Railway/Render) - Task 36.2
3. **Backend** (Railway/Render) - Task 36.3
4. **Celery Workers** (Railway/Render) - Task 36.4
5. **Frontend** (Vercel) - Task 36.5
6. **Sentry** (Error Tracking) - Task 36.6

## Essential Commands

### Database Migrations

```bash
# Run migrations
alembic upgrade head

# Check current version
alembic current

# Rollback one version
alembic downgrade -1
```

### Testing Endpoints

```bash
# Health check
curl https://your-backend.up.railway.app/health

# API docs
open https://your-backend.up.railway.app/docs

# Test job search
curl https://your-backend.up.railway.app/api/jobs/search?query=developer
```

### Celery Monitoring

```python
# Check worker status
from app.tasks.celery_app import celery_app
inspect = celery_app.control.inspect()
print(inspect.active())
print(inspect.stats())

# Check queue length
from app.core.redis import get_redis_client
redis_client = get_redis_client()
print(f"Queue length: {redis_client.llen('celery')}")
```

## Environment Variables Checklist

### Backend (Railway/Render)

```bash
# Application
APP_ENV=production
DEBUG=False
SECRET_KEY=<generate-with-openssl-rand-hex-32>
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>

# Database
DATABASE_URL=<from-supabase>
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=20

# Redis
REDIS_URL=<from-railway-or-render>
CELERY_BROKER_URL=<same-as-redis-url>
CELERY_RESULT_BACKEND=<same-as-redis-url>

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# External APIs
INDEED_API_KEY=...
LINKEDIN_RSS_URLS=...

# Storage
STORAGE_BACKEND=supabase
SUPABASE_URL=...
SUPABASE_KEY=...

# Monitoring
SENTRY_DSN=<from-sentry>

# CORS
CORS_ORIGINS=<frontend-url>
```

### Frontend (Vercel)

```bash
# API
NEXT_PUBLIC_API_URL=<backend-url>
NEXT_PUBLIC_API_BASE_PATH=/api

# Stripe
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...

# Environment
NEXT_PUBLIC_ENV=production

# Sentry
SENTRY_DSN=<from-sentry>
SENTRY_AUTH_TOKEN=<from-sentry>
SENTRY_ORG=<your-org>
SENTRY_PROJECT=job-platform-frontend
```

## Common Issues & Solutions

### Backend Won't Start
- Check DATABASE_URL is correct
- Verify Redis connection
- Check environment variables are set
- Review logs for specific error

### CORS Errors
- Verify CORS_ORIGINS includes frontend URL
- No trailing slash in URLs
- Redeploy backend after changing CORS

### Database Connection Fails
- Verify ?sslmode=require in connection string
- Check Supabase project is not paused
- Use pooled connection (port 6543)

### Celery Tasks Not Running
- Check worker service is running
- Verify Redis connection
- Check Beat scheduler is running
- Review worker logs

### Frontend Build Fails
- Check package.json scripts
- Verify all dependencies installed
- Test build locally: npm run build
- Check for TypeScript errors

## Free Tier Limits

| Service | Limit | Cost |
|---------|-------|------|
| Supabase | 500MB DB, 2GB bandwidth | $0 |
| Railway | 512MB RAM per service, $5 credit | $0 |
| Render | 512MB RAM, 100GB bandwidth | $0 |
| Vercel | 100GB bandwidth, unlimited deploys | $0 |
| Sentry | 5K errors, 10K transactions/month | $0 |

**Total Monthly Cost**: $0 (within free tiers)

## Monitoring Dashboards

- **Supabase**: https://app.supabase.com/project/[project-id]
- **Railway**: https://railway.app/project/[project-id]
- **Render**: https://dashboard.render.com
- **Vercel**: https://vercel.com/[username]/[project]
- **Sentry**: https://sentry.io/organizations/[org]/projects/

## Support Links

- **Supabase Docs**: https://supabase.com/docs
- **Railway Docs**: https://docs.railway.app
- **Render Docs**: https://render.com/docs
- **Vercel Docs**: https://vercel.com/docs
- **Sentry Docs**: https://docs.sentry.io

## Deployment Checklist

### Pre-Deployment
- [ ] Code pushed to GitHub
- [ ] All tests passing
- [ ] Environment variables prepared
- [ ] Secrets generated (SECRET_KEY, JWT_SECRET_KEY)
- [ ] Stripe keys obtained
- [ ] Domain name ready (optional)

### Deployment
- [ ] PostgreSQL deployed (Supabase)
- [ ] Redis deployed (Railway/Render)
- [ ] Backend deployed (Railway/Render)
- [ ] Database migrations run
- [ ] Celery workers deployed
- [ ] Celery Beat deployed
- [ ] Frontend deployed (Vercel)
- [ ] Sentry configured

### Post-Deployment
- [ ] Health check returns 200
- [ ] API docs accessible
- [ ] Frontend loads correctly
- [ ] Can register/login
- [ ] Job search works
- [ ] Celery tasks executing
- [ ] Sentry capturing errors
- [ ] CORS configured correctly
- [ ] Custom domain configured (optional)

## Emergency Procedures

### Rollback Backend
```bash
# Railway: Redeploy previous version
railway rollback

# Render: Deploy previous commit
# Go to service → Manual Deploy → Select commit
```

### Rollback Database
```bash
# Downgrade one migration
alembic downgrade -1

# Or restore from backup
# Supabase → Database → Backups → Restore
```

### Restart Services
```bash
# Railway: Restart service
railway restart

# Render: Restart service
# Go to service → Manual Deploy → Restart
```

### Check Service Status
- Railway: https://status.railway.app
- Render: https://status.render.com
- Vercel: https://vercel-status.com
- Supabase: https://status.supabase.com

## Performance Optimization

### Database
- Use connection pooling (port 6543)
- Add indexes for frequent queries
- Monitor slow queries
- Use prepared statements

### Redis
- Set TTL on all keys
- Use appropriate data structures
- Monitor memory usage
- Implement cache eviction

### Backend
- Enable gzip compression
- Use async endpoints
- Implement caching
- Optimize database queries

### Frontend
- Use Next.js Image component
- Implement code splitting
- Enable caching headers
- Optimize bundle size

### Celery
- Use appropriate concurrency
- Implement task chunking
- Set task time limits
- Monitor queue length

## Security Checklist

- [ ] DEBUG=False in production
- [ ] Strong SECRET_KEY and JWT_SECRET_KEY
- [ ] CORS restricted to production domains
- [ ] Database uses SSL (sslmode=require)
- [ ] HTTPS enabled on all services
- [ ] Stripe live keys (not test keys)
- [ ] Sentry DSN configured
- [ ] Rate limiting enabled
- [ ] CSRF protection enabled
- [ ] Security headers configured
- [ ] File upload validation enabled
- [ ] Secrets not in code/git

## Maintenance Schedule

### Daily
- Check Sentry for new errors
- Review service health dashboards
- Monitor error rates

### Weekly
- Review database performance
- Check Redis memory usage
- Review Celery task success rates
- Check free tier usage

### Monthly
- Update dependencies
- Rotate secrets
- Review performance metrics
- Plan for scaling if needed

---

For detailed instructions, see individual deployment guides:
- [DEPLOYMENT_36.1_POSTGRESQL.md](./DEPLOYMENT_36.1_POSTGRESQL.md)
- [DEPLOYMENT_36.2_REDIS.md](./DEPLOYMENT_36.2_REDIS.md)
- [DEPLOYMENT_36.3_BACKEND.md](./DEPLOYMENT_36.3_BACKEND.md)
- [DEPLOYMENT_36.4_CELERY.md](./DEPLOYMENT_36.4_CELERY.md)
- [DEPLOYMENT_36.5_FRONTEND.md](./DEPLOYMENT_36.5_FRONTEND.md)
- [DEPLOYMENT_36.6_SENTRY.md](./DEPLOYMENT_36.6_SENTRY.md)
