#!/bin/bash
################################################################################
# Recreate Environment File
# Recreates .env.production with correct field names
################################################################################

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}Recreating environment file with correct format...${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

DEPLOY_USER="jobplatform"
APP_DIR="/home/$DEPLOY_USER/job-platform"

# Collect configuration
read -sp "PostgreSQL password for job_platform_user: " DB_PASSWORD
echo ""
read -sp "Redis password: " REDIS_PASSWORD
echo ""

# Generate SECRET_KEY
SECRET_KEY=$(openssl rand -hex 32)

read -p "Domain name (leave empty if none): " DOMAIN_NAME
read -p "Stripe Secret Key (optional): " STRIPE_SECRET_KEY
read -p "Stripe Publishable Key (optional): " STRIPE_PUBLISHABLE_KEY
read -p "Sentry DSN (optional): " SENTRY_DSN
read -p "SMTP Host (e.g., smtp.gmail.com): " SMTP_HOST
read -p "SMTP Port (default: 587): " SMTP_PORT
SMTP_PORT=${SMTP_PORT:-587}
read -p "SMTP User: " SMTP_USER
read -sp "SMTP Password: " SMTP_PASSWORD
echo ""

echo ""
echo "Creating environment file..."

# Create environment file
cat > "$APP_DIR/backend/.env.production" <<EOF
# Application
APP_NAME=Job Aggregation Platform
APP_ENV=production
DEBUG=False
SECRET_KEY=$SECRET_KEY

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=False

# Database
DATABASE_URL=postgresql://job_platform_user:$DB_PASSWORD@localhost:5432/job_platform
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://:$REDIS_PASSWORD@localhost:6379/0
REDIS_CACHE_DB=1

# Celery
CELERY_BROKER_URL=redis://:$REDIS_PASSWORD@localhost:6379/0
CELERY_RESULT_BACKEND=redis://:$REDIS_PASSWORD@localhost:6379/1

# JWT Authentication
JWT_SECRET_KEY=$SECRET_KEY
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# External API Keys
INDEED_API_KEY=
LINKEDIN_RSS_URLS=

# Stripe Payment
STRIPE_SECRET_KEY=$STRIPE_SECRET_KEY
STRIPE_PUBLISHABLE_KEY=$STRIPE_PUBLISHABLE_KEY
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
SENTRY_DSN=$SENTRY_DSN

# Alerting
SMTP_HOST=$SMTP_HOST
SMTP_PORT=$SMTP_PORT
SMTP_USER=$SMTP_USER
SMTP_PASSWORD=$SMTP_PASSWORD
ADMIN_EMAIL=$SMTP_USER
FROM_EMAIL=noreply@${DOMAIN_NAME:-localhost}
SLACK_WEBHOOK_URL=

# CORS
CORS_ORIGINS=https://${DOMAIN_NAME:-localhost},http://${DOMAIN_NAME:-localhost}

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
EOF

chown $DEPLOY_USER:$DEPLOY_USER "$APP_DIR/backend/.env.production"
chmod 600 "$APP_DIR/backend/.env.production"

# Create symlink
cd "$APP_DIR/backend"
ln -sf .env.production .env
chown -h $DEPLOY_USER:$DEPLOY_USER .env

echo -e "${GREEN}✓ Environment file created successfully${NC}"
echo ""
echo "Now run migrations:"
echo "  cd /home/jobplatform/job-platform/backend"
echo "  sudo -u jobplatform bash -c 'source venv/bin/activate && alembic upgrade head'"
