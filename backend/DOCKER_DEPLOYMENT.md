# Docker Deployment Guide

This guide explains how to deploy the Job Aggregation Platform using Docker and Docker Compose.

## Quick Start (Local Development)

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### Step 1: Environment Setup

Copy the Docker environment file:

```bash
cp .env.docker .env
```

Edit `.env` and update any values as needed for your local environment.

### Step 2: Start Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### Step 3: Run Database Migrations

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Verify migration
docker-compose exec backend alembic current
```

### Step 4: Access Services

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Celery Flower**: http://localhost:5555
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### Step 5: Test the Application

```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs
```

## Services Overview

The Docker Compose setup includes the following services:

### 1. PostgreSQL Database

- **Image**: postgres:15-alpine
- **Port**: 5432
- **Volume**: postgres_data (persistent storage)
- **Health Check**: Automatic readiness check

### 2. Redis Cache & Message Broker

- **Image**: redis:7-alpine
- **Port**: 6379
- **Volume**: redis_data (persistent storage)
- **Health Check**: Automatic readiness check

### 3. FastAPI Backend

- **Build**: Local Dockerfile
- **Port**: 8000
- **Dependencies**: PostgreSQL, Redis
- **Auto-reload**: Enabled in development

### 4. Celery Worker

- **Build**: Local Dockerfile
- **Concurrency**: 4 workers
- **Dependencies**: PostgreSQL, Redis
- **Purpose**: Background task processing

### 5. Celery Beat

- **Build**: Local Dockerfile
- **Dependencies**: PostgreSQL, Redis
- **Purpose**: Scheduled task execution

### 6. Celery Flower

- **Build**: Local Dockerfile
- **Port**: 5555
- **Purpose**: Celery monitoring dashboard

## Common Commands

### Service Management

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart a specific service
docker-compose restart backend

# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend

# Check service status
docker-compose ps
```

### Database Operations

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Rollback migration
docker-compose exec backend alembic downgrade -1

# Check current migration
docker-compose exec backend alembic current

# Access PostgreSQL shell
docker-compose exec postgres psql -U jobplatform -d job_platform

# Create database backup
docker-compose exec postgres pg_dump -U jobplatform job_platform > backup.sql

# Restore database backup
docker-compose exec -T postgres psql -U jobplatform job_platform < backup.sql
```

### Application Operations

```bash
# Access backend shell
docker-compose exec backend bash

# Run Python shell
docker-compose exec backend python

# Run tests
docker-compose exec backend pytest

# Check environment variables
docker-compose exec backend env
```

### Celery Operations

```bash
# View Celery worker logs
docker-compose logs -f celery_worker

# View Celery beat logs
docker-compose logs -f celery_beat

# Restart Celery worker
docker-compose restart celery_worker

# Access Flower dashboard
open http://localhost:5555
```

## Development Workflow

### Making Code Changes

The backend service uses volume mounting, so code changes are reflected immediately:

```bash
# Edit code in your editor
vim app/main.py

# Backend will auto-reload (if API_RELOAD=True)
# Check logs to see reload
docker-compose logs -f backend
```

### Adding Dependencies

If you add new Python packages:

```bash
# Add package to requirements.txt
echo "new-package==1.0.0" >> requirements.txt

# Rebuild backend image
docker-compose build backend

# Restart backend service
docker-compose up -d backend
```

### Database Schema Changes

When creating new migrations:

```bash
# Create migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Review migration file
cat alembic/versions/XXX_description.py

# Apply migration
docker-compose exec backend alembic upgrade head
```

## Troubleshooting

### Service Won't Start

Check logs for errors:

```bash
docker-compose logs backend
```

Common issues:
- Database not ready: Wait for health check to pass
- Port already in use: Change port in .env file
- Missing environment variables: Check .env file

### Database Connection Errors

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Test connection
docker-compose exec backend python -c "from app.db import check_db_health; print(check_db_health())"
```

### Redis Connection Errors

```bash
# Check Redis is running
docker-compose ps redis

# Check Redis logs
docker-compose logs redis

# Test connection
docker-compose exec backend python -c "from app.core.redis import get_redis_client; get_redis_client().ping()"
```

### Celery Tasks Not Running

```bash
# Check Celery worker is running
docker-compose ps celery_worker

# Check Celery worker logs
docker-compose logs celery_worker

# Check Celery beat logs
docker-compose logs celery_beat

# View active tasks in Flower
open http://localhost:5555
```

### Permission Errors

If you encounter permission errors with volumes:

```bash
# Fix ownership
sudo chown -R $USER:$USER uploads logs

# Or run as root (not recommended)
docker-compose exec -u root backend bash
```

## Production Deployment

For production deployment, see [PRODUCTION_DEPLOYMENT_GUIDE.md](./PRODUCTION_DEPLOYMENT_GUIDE.md).

Key differences for production:

1. **Use production environment file**: `.env.production`
2. **Disable debug mode**: `DEBUG=False`
3. **Use strong secrets**: Generate random keys
4. **Enable SSL**: Database and Redis connections
5. **Restrict CORS**: Only production domains
6. **Use live Stripe keys**: Not test keys
7. **Configure monitoring**: Sentry, alerts
8. **Set up backups**: Automated database backups
9. **Use container registry**: Don't build on production server
10. **Configure reverse proxy**: Nginx or similar

## Cleanup

### Remove All Containers and Volumes

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: deletes all data)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

### Remove Specific Volumes

```bash
# List volumes
docker volume ls

# Remove specific volume
docker volume rm backend_postgres_data
docker volume rm backend_redis_data
```

## Performance Optimization

### Resource Limits

Add resource limits to docker-compose.yml:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### Connection Pooling

Adjust database pool settings in .env:

```bash
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=30
```

### Celery Concurrency

Adjust worker concurrency based on CPU cores:

```bash
# In docker-compose.yml
command: celery -A app.tasks.celery_app worker --loglevel=info --concurrency=8
```

## Security Best Practices

1. **Never commit .env files** with real credentials
2. **Use secrets management** in production (Docker secrets, Vault)
3. **Run as non-root user** (already configured in Dockerfile)
4. **Keep images updated** regularly
5. **Scan images for vulnerabilities** using Docker scan
6. **Use private registry** for production images
7. **Enable Docker Content Trust** for image signing
8. **Limit container capabilities** using security options

## Monitoring

### Health Checks

All services have health checks configured:

```bash
# Check health status
docker-compose ps

# View health check logs
docker inspect backend_backend_1 | jq '.[0].State.Health'
```

### Resource Usage

```bash
# View resource usage
docker stats

# View specific service
docker stats backend_backend_1
```

### Logs

```bash
# Follow all logs
docker-compose logs -f

# Follow specific service
docker-compose logs -f backend

# View last 100 lines
docker-compose logs --tail=100 backend

# View logs since timestamp
docker-compose logs --since 2024-01-15T10:00:00 backend
```

## Support

For issues or questions:
- Check logs: `docker-compose logs -f`
- Check health: `curl http://localhost:8000/health`
- Review documentation: [PRODUCTION_DEPLOYMENT_GUIDE.md](./PRODUCTION_DEPLOYMENT_GUIDE.md)
- Contact: admin@yourplatform.com
