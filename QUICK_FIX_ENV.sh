#!/bin/bash

# Quick fix for .env file on server
# Run this on your EC2 instance: bash QUICK_FIX_ENV.sh

echo "=== Quick Fix for .env file ==="

# Backup current .env
cp /home/jobplatform/job-platform/backend/.env /home/jobplatform/job-platform/backend/.env.backup

# Create complete .env file
cat > /home/jobplatform/job-platform/backend/.env << 'EOF'
# Application
APP_NAME="Job Aggregation Platform"
APP_ENV=production
DEBUG=False
SECRET_KEY=cf1c2839a5f8e7d6b4c3a2f1e0d9c8b7a6f5e4d3c2b1a0f9e8d7c6b5a4f3e2d1

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=False

# Database
DATABASE_URL=postgresql://jobplatform:Herculis%40123@localhost/jobplatform_db
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_DB=1

# Celery (REQUIRED)
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# JWT Authentication (REQUIRED)
JWT_SECRET_KEY=cf1c2839afd3888717e2d59740ad26f3b24d4578a2d2eed56044e3639c4da1a9
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# External API Keys (optional)
INDEED_API_KEY=
LINKEDIN_RSS_URLS=

# Stripe Payment (optional)
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=

# Scraping Configuration
SCRAPING_USER_AGENT=Mozilla/5.0 (compatible; JobBot/1.0)
SCRAPING_RATE_LIMIT_LINKEDIN=10
SCRAPING_RATE_LIMIT_INDEED=20
SCRAPING_RATE_LIMIT_NAUKRI=5
SCRAPING_RATE_LIMIT_MONSTER=5

# File Storage
STORAGE_BACKEND=local
STORAGE_LOCAL_PATH=./uploads
SUPABASE_URL=
SUPABASE_KEY=

# Monitoring
SENTRY_DSN=

# Alerting
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
ADMIN_EMAIL=admin@trusanity.com
FROM_EMAIL=noreply@trusanity.com
SLACK_WEBHOOK_URL=

# CORS
CORS_ORIGINS=https://trusanity.com,https://www.trusanity.com

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
EOF

echo "✓ .env file fixed!"
echo ""
echo "Now run:"
echo "  cd /home/jobplatform/job-platform/backend"
echo "  source venv/bin/activate"
echo "  alembic upgrade head"
