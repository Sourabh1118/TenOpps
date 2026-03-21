#!/bin/bash
################################################################################
# Resume Deployment Script
# Continues deployment from where it failed
################################################################################

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Resume Deployment Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

DEPLOY_USER="jobplatform"
APP_DIR="/home/$DEPLOY_USER/job-platform"
LOG_FILE="/var/log/job-platform-deploy.log"

# Check if repository exists
if [ ! -d "$APP_DIR" ]; then
    echo -e "${RED}Repository not found at $APP_DIR${NC}"
    echo "Please run the full deployment script first."
    exit 1
fi

echo -e "${YELLOW}This script will:${NC}"
echo "1. Check existing installation"
echo "2. Install/update Python dependencies"
echo "3. Install/update Node.js dependencies"
echo "4. Create environment files"
echo "5. Run database migrations"
echo "6. Build frontend"
echo "7. Create/update systemd services"
echo "8. Start all services"
echo ""

read -p "Continue? (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "Aborted."
    exit 0
fi

# Collect configuration
echo ""
echo -e "${BLUE}Configuration${NC}"
echo ""

read -sp "PostgreSQL password for job_platform_user: " DB_PASSWORD
echo ""
read -sp "Redis password: " REDIS_PASSWORD
echo ""

# Generate SECRET_KEY if not provided
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
echo -e "${BLUE}Starting deployment...${NC}"
echo ""

# Backend Setup
echo -e "${YELLOW}Setting up backend...${NC}"
cd "$APP_DIR/backend"

# Check if venv exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    sudo -u $DEPLOY_USER python3.11 -m venv venv
fi

# Install dependencies
echo "Installing Python dependencies..."
sudo -u $DEPLOY_USER bash -c "source venv/bin/activate && pip install --upgrade pip"
sudo -u $DEPLOY_USER bash -c "source venv/bin/activate && pip install -r requirements.txt"
sudo -u $DEPLOY_USER bash -c "source venv/bin/activate && pip install gunicorn"

echo -e "${GREEN}✓ Python dependencies installed${NC}"

# Create environment file
echo "Creating backend environment file..."
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

# Create symlink for .env to point to .env.production
ln -sf .env.production "$APP_DIR/backend/.env"
chown -h $DEPLOY_USER:$DEPLOY_USER "$APP_DIR/backend/.env"

echo -e "${GREEN}✓ Backend environment file created${NC}"

# Run migrations
echo "Running database migrations..."
sudo -u $DEPLOY_USER bash -c "cd $APP_DIR/backend && source venv/bin/activate && alembic upgrade head"
echo -e "${GREEN}✓ Database migrations completed${NC}"

# Frontend Setup
echo ""
echo -e "${YELLOW}Setting up frontend...${NC}"
cd "$APP_DIR/frontend"

echo "Installing Node.js dependencies..."
sudo -u $DEPLOY_USER npm install

echo "Creating frontend environment file..."
cat > "$APP_DIR/frontend/.env.production" <<EOF
NEXT_PUBLIC_API_URL=https://${DOMAIN_NAME:-localhost}/api
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=$STRIPE_PUBLISHABLE_KEY
EOF

chown $DEPLOY_USER:$DEPLOY_USER "$APP_DIR/frontend/.env.production"

echo "Building frontend..."
sudo -u $DEPLOY_USER npm run build

echo -e "${GREEN}✓ Frontend setup completed${NC}"

# Create systemd services
echo ""
echo -e "${YELLOW}Creating systemd services...${NC}"

# Backend service
cat > /etc/systemd/system/job-platform-backend.service <<EOF
[Unit]
Description=Job Platform Backend API
After=network.target postgresql.service redis-server.service

[Service]
Type=notify
User=$DEPLOY_USER
Group=$DEPLOY_USER
WorkingDirectory=$APP_DIR/backend
Environment="PATH=$APP_DIR/backend/venv/bin"
EnvironmentFile=$APP_DIR/backend/.env.production
ExecStart=$APP_DIR/backend/venv/bin/gunicorn \\
    -k uvicorn.workers.UvicornWorker \\
    -w 4 \\
    -b 127.0.0.1:8000 \\
    --timeout 120 \\
    --max-requests 1000 \\
    --max-requests-jitter 50 \\
    --access-logfile /var/log/job-platform/backend-access.log \\
    --error-logfile /var/log/job-platform/backend-error.log \\
    app.main:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Frontend service
cat > /etc/systemd/system/job-platform-frontend.service <<EOF
[Unit]
Description=Job Platform Frontend
After=network.target

[Service]
Type=simple
User=$DEPLOY_USER
Group=$DEPLOY_USER
WorkingDirectory=$APP_DIR/frontend
Environment="PATH=/usr/bin:/usr/local/bin"
Environment="NODE_ENV=production"
Environment="PORT=3000"
ExecStart=/usr/bin/npm start

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Celery worker service
cat > /etc/systemd/system/job-platform-celery.service <<EOF
[Unit]
Description=Job Platform Celery Worker
After=network.target redis-server.service postgresql.service

[Service]
Type=simple
User=$DEPLOY_USER
Group=$DEPLOY_USER
WorkingDirectory=$APP_DIR/backend
Environment="PATH=$APP_DIR/backend/venv/bin"
EnvironmentFile=$APP_DIR/backend/.env.production
ExecStart=$APP_DIR/backend/venv/bin/celery -A app.tasks.celery_app worker \\
    --loglevel=info \\
    --concurrency=4 \\
    --max-tasks-per-child=1000 \\
    --logfile=/var/log/job-platform/celery-worker.log

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Celery beat service
cat > /etc/systemd/system/job-platform-celery-beat.service <<EOF
[Unit]
Description=Job Platform Celery Beat Scheduler
After=network.target redis-server.service

[Service]
Type=simple
User=$DEPLOY_USER
Group=$DEPLOY_USER
WorkingDirectory=$APP_DIR/backend
Environment="PATH=$APP_DIR/backend/venv/bin"
EnvironmentFile=$APP_DIR/backend/.env.production
ExecStart=$APP_DIR/backend/venv/bin/celery -A app.tasks.celery_app beat \\
    --loglevel=info \\
    --logfile=/var/log/job-platform/celery-beat.log

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo -e "${GREEN}✓ Systemd services created${NC}"

# Start services
echo ""
echo -e "${YELLOW}Starting services...${NC}"

systemctl enable job-platform-backend
systemctl start job-platform-backend
sleep 5

if systemctl is-active --quiet job-platform-backend; then
    echo -e "${GREEN}✓ Backend service started${NC}"
else
    echo -e "${RED}✗ Backend service failed to start${NC}"
    echo "Check logs: sudo journalctl -u job-platform-backend -n 50"
fi

systemctl enable job-platform-frontend
systemctl start job-platform-frontend
sleep 5

if systemctl is-active --quiet job-platform-frontend; then
    echo -e "${GREEN}✓ Frontend service started${NC}"
else
    echo -e "${RED}✗ Frontend service failed to start${NC}"
    echo "Check logs: sudo journalctl -u job-platform-frontend -n 50"
fi

systemctl enable job-platform-celery
systemctl start job-platform-celery
sleep 3

if systemctl is-active --quiet job-platform-celery; then
    echo -e "${GREEN}✓ Celery worker started${NC}"
else
    echo -e "${YELLOW}⚠ Celery worker failed to start (non-critical)${NC}"
fi

systemctl enable job-platform-celery-beat
systemctl start job-platform-celery-beat
sleep 3

if systemctl is-active --quiet job-platform-celery-beat; then
    echo -e "${GREEN}✓ Celery beat started${NC}"
else
    echo -e "${YELLOW}⚠ Celery beat failed to start (non-critical)${NC}"
fi

# Verify deployment
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Deployment Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo "Service Status:"
systemctl is-active --quiet job-platform-backend && echo -e "  ${GREEN}✓ Backend: Running${NC}" || echo -e "  ${RED}✗ Backend: Stopped${NC}"
systemctl is-active --quiet job-platform-frontend && echo -e "  ${GREEN}✓ Frontend: Running${NC}" || echo -e "  ${RED}✗ Frontend: Stopped${NC}"
systemctl is-active --quiet job-platform-celery && echo -e "  ${GREEN}✓ Celery Worker: Running${NC}" || echo -e "  ${RED}✗ Celery Worker: Stopped${NC}"
systemctl is-active --quiet job-platform-celery-beat && echo -e "  ${GREEN}✓ Celery Beat: Running${NC}" || echo -e "  ${RED}✗ Celery Beat: Stopped${NC}"

echo ""
echo "Access Information:"
if [ -n "$DOMAIN_NAME" ]; then
    echo "  Application URL: https://$DOMAIN_NAME"
    echo "  API URL: https://$DOMAIN_NAME/api"
else
    PUBLIC_IP=$(curl -s ifconfig.me)
    echo "  Application URL: http://$PUBLIC_IP"
    echo "  API URL: http://$PUBLIC_IP/api"
fi

echo ""
echo "Useful Commands:"
echo "  Check backend logs: sudo journalctl -u job-platform-backend -f"
echo "  Check frontend logs: sudo journalctl -u job-platform-frontend -f"
echo "  Restart backend: sudo systemctl restart job-platform-backend"
echo "  Check all services: sudo systemctl status job-platform-*"

echo ""
echo -e "${GREEN}Deployment completed!${NC}"
