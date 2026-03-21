#!/bin/bash

################################################################################
# Complete Clean Deployment Script for AWS EC2
# This script performs a complete clean installation from scratch
################################################################################

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="${1:-trusanity.com}"
GITHUB_PAT="${2}"
DB_PASSWORD="${3:-Herculis@123}"
REDIS_PASSWORD="${4:-Herculis@123}"

# Validate required parameters
if [ -z "$GITHUB_PAT" ]; then
    echo -e "${RED}Error: GitHub PAT is required${NC}"
    echo "Usage: $0 <domain> <github_pat> [db_password] [redis_password]"
    exit 1
fi

# Logging
LOG_FILE="/tmp/deployment-$(date +%Y%m%d-%H%M%S).log"
exec 1> >(tee -a "$LOG_FILE")
exec 2>&1

echo -e "${GREEN}=== Starting Complete Clean Deployment ===${NC}"
echo "Domain: $DOMAIN"
echo "Log file: $LOG_FILE"
echo ""

################################################################################
# Step 1: Clean up existing installation
################################################################################
echo -e "${YELLOW}Step 1: Cleaning up existing installation...${NC}"

# Stop all services
echo "Stopping services..."
sudo systemctl stop job-platform-backend 2>/dev/null || true
sudo systemctl stop job-platform-celery-worker 2>/dev/null || true
sudo systemctl stop job-platform-celery-beat 2>/dev/null || true
sudo systemctl stop nginx 2>/dev/null || true

# Remove systemd service files
echo "Removing systemd service files..."
sudo rm -f /etc/systemd/system/job-platform-*.service
sudo systemctl daemon-reload

# Remove application directory
echo "Removing application directory..."
sudo rm -rf /home/jobplatform

# Remove nginx configuration
echo "Removing nginx configuration..."
sudo rm -f /etc/nginx/sites-enabled/job-platform
sudo rm -f /etc/nginx/sites-available/job-platform

# Drop and recreate database
echo "Recreating database..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS job_platform;" 2>/dev/null || true
sudo -u postgres psql -c "DROP USER IF EXISTS job_platform_user;" 2>/dev/null || true
sudo -u postgres psql -c "CREATE USER job_platform_user WITH PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "CREATE DATABASE job_platform OWNER job_platform_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE job_platform TO job_platform_user;"

# Flush Redis
echo "Flushing Redis..."
redis-cli -a "$REDIS_PASSWORD" FLUSHALL 2>/dev/null || true

echo -e "${GREEN}Cleanup completed!${NC}\n"

################################################################################
# Step 2: Create user and directory structure
################################################################################
echo -e "${YELLOW}Step 2: Creating user and directory structure...${NC}"

# Create jobplatform user if it doesn't exist
if ! id -u jobplatform >/dev/null 2>&1; then
    sudo useradd -m -s /bin/bash jobplatform
    echo "Created jobplatform user"
fi

# Create application directory with proper permissions
sudo mkdir -p /home/jobplatform
sudo chown jobplatform:jobplatform /home/jobplatform
sudo chmod 755 /home/jobplatform

# Add ubuntu user to jobplatform group
sudo usermod -a -G jobplatform ubuntu

echo -e "${GREEN}User and directory structure created!${NC}\n"

################################################################################
# Step 3: Clone repository
################################################################################
echo -e "${YELLOW}Step 3: Cloning repository...${NC}"

cd /home/jobplatform
sudo -u jobplatform git clone https://${GITHUB_PAT}@github.com/Sourabh1118/TenOpps.git job-platform

if [ ! -d "/home/jobplatform/job-platform" ]; then
    echo -e "${RED}Failed to clone repository${NC}"
    exit 1
fi

echo -e "${GREEN}Repository cloned successfully!${NC}\n"

################################################################################
# Step 4: Setup Backend
################################################################################
echo -e "${YELLOW}Step 4: Setting up backend...${NC}"

cd /home/jobplatform/job-platform/backend

# Create virtual environment
echo "Creating Python virtual environment..."
sudo -u jobplatform python3.11 -m venv venv

# Install dependencies
echo "Installing Python dependencies..."
sudo -u jobplatform bash -c 'source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt'

# Generate SECRET_KEY and JWT_SECRET_KEY
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# URL-encode the database password (replace @ with %40)
DB_PASSWORD_ENCODED=$(echo -n "$DB_PASSWORD" | python3 -c "import sys; from urllib.parse import quote; print(quote(sys.stdin.read(), safe=''))")
REDIS_PASSWORD_ENCODED=$(echo -n "$REDIS_PASSWORD" | python3 -c "import sys; from urllib.parse import quote; print(quote(sys.stdin.read(), safe=''))")

# Create .env.production file with CORRECT field names matching config.py
echo "Creating .env.production file..."
sudo -u jobplatform tee /home/jobplatform/job-platform/backend/.env.production > /dev/null <<EOF
# Application
APP_NAME=Job Aggregation Platform
APP_ENV=production
DEBUG=False
SECRET_KEY=${SECRET_KEY}

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=False

# Database
DATABASE_URL=postgresql://job_platform_user:${DB_PASSWORD_ENCODED}@localhost:5432/job_platform
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://:${REDIS_PASSWORD_ENCODED}@localhost:6379/0
REDIS_CACHE_DB=1

# Celery
CELERY_BROKER_URL=redis://:${REDIS_PASSWORD_ENCODED}@localhost:6379/0
CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD_ENCODED}@localhost:6379/0

# JWT Authentication
JWT_SECRET_KEY=${JWT_SECRET_KEY}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# External API Keys (optional - leave empty if not using)
INDEED_API_KEY=
LINKEDIN_RSS_URLS=

# Stripe Payment (optional - leave empty if not using)
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

# Monitoring (optional)
SENTRY_DSN=

# Alerting (optional)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
ADMIN_EMAIL=
FROM_EMAIL=
SLACK_WEBHOOK_URL=

# CORS
CORS_ORIGINS=https://${DOMAIN}

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
EOF

# Create symlink for .env
sudo -u jobplatform ln -sf /home/jobplatform/job-platform/backend/.env.production /home/jobplatform/job-platform/backend/.env

# Create uploads directory
sudo -u jobplatform mkdir -p /home/jobplatform/job-platform/backend/uploads
sudo chmod 755 /home/jobplatform/job-platform/backend/uploads

# Run database migrations
echo "Running database migrations..."
cd /home/jobplatform/job-platform/backend
sudo -u jobplatform bash -c 'source venv/bin/activate && alembic upgrade head'

if [ $? -ne 0 ]; then
    echo -e "${RED}Database migration failed!${NC}"
    echo "Check the log file: $LOG_FILE"
    exit 1
fi

echo -e "${GREEN}Backend setup completed!${NC}\n"

################################################################################
# Step 5: Setup Frontend
################################################################################
echo -e "${YELLOW}Step 5: Setting up frontend...${NC}"

cd /home/jobplatform/job-platform/frontend

# Create .env.production file
echo "Creating frontend .env.production..."
sudo -u jobplatform tee /home/jobplatform/job-platform/frontend/.env.production > /dev/null <<EOF
NEXT_PUBLIC_API_URL=https://${DOMAIN}/api
EOF

# Install dependencies
echo "Installing Node.js dependencies..."
sudo -u jobplatform npm install

# Install tailwindcss-animate (required for build)
echo "Installing tailwindcss-animate..."
sudo -u jobplatform npm install tailwindcss-animate

# Build frontend
echo "Building frontend..."
sudo -u jobplatform npm run build

if [ $? -ne 0 ]; then
    echo -e "${RED}Frontend build failed!${NC}"
    exit 1
fi

echo -e "${GREEN}Frontend setup completed!${NC}\n"

################################################################################
# Step 6: Create systemd services
################################################################################
echo -e "${YELLOW}Step 6: Creating systemd services...${NC}"

# Backend service
sudo tee /etc/systemd/system/job-platform-backend.service > /dev/null <<EOF
[Unit]
Description=Job Platform Backend API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=jobplatform
Group=jobplatform
WorkingDirectory=/home/jobplatform/job-platform/backend
Environment="PATH=/home/jobplatform/job-platform/backend/venv/bin"
ExecStart=/home/jobplatform/job-platform/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Celery worker service
sudo tee /etc/systemd/system/job-platform-celery-worker.service > /dev/null <<EOF
[Unit]
Description=Job Platform Celery Worker
After=network.target redis.service

[Service]
Type=simple
User=jobplatform
Group=jobplatform
WorkingDirectory=/home/jobplatform/job-platform/backend
Environment="PATH=/home/jobplatform/job-platform/backend/venv/bin"
ExecStart=/home/jobplatform/job-platform/backend/venv/bin/celery -A app.tasks.celery_app worker --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Celery beat service
sudo tee /etc/systemd/system/job-platform-celery-beat.service > /dev/null <<EOF
[Unit]
Description=Job Platform Celery Beat Scheduler
After=network.target redis.service

[Service]
Type=simple
User=jobplatform
Group=jobplatform
WorkingDirectory=/home/jobplatform/job-platform/backend
Environment="PATH=/home/jobplatform/job-platform/backend/venv/bin"
ExecStart=/home/jobplatform/job-platform/backend/venv/bin/celery -A app.tasks.celery_app beat --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

echo -e "${GREEN}Systemd services created!${NC}\n"

################################################################################
# Step 7: Configure Nginx
################################################################################
echo -e "${YELLOW}Step 7: Configuring Nginx...${NC}"

sudo tee /etc/nginx/sites-available/job-platform > /dev/null <<EOF
server {
    listen 80;
    server_name ${DOMAIN};

    client_max_body_size 10M;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Static files
    location /static {
        alias /home/jobplatform/job-platform/backend/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Uploads
    location /uploads {
        alias /home/jobplatform/job-platform/backend/uploads;
        expires 7d;
        add_header Cache-Control "public";
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/job-platform /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t

if [ $? -ne 0 ]; then
    echo -e "${RED}Nginx configuration test failed!${NC}"
    exit 1
fi

echo -e "${GREEN}Nginx configured!${NC}\n"

################################################################################
# Step 8: Start all services
################################################################################
echo -e "${YELLOW}Step 8: Starting all services...${NC}"

# Start backend services
sudo systemctl enable job-platform-backend
sudo systemctl start job-platform-backend

sudo systemctl enable job-platform-celery-worker
sudo systemctl start job-platform-celery-worker

sudo systemctl enable job-platform-celery-beat
sudo systemctl start job-platform-celery-beat

# Start frontend (using PM2)
cd /home/jobplatform/job-platform/frontend
sudo -u jobplatform bash -c 'pm2 delete job-platform-frontend 2>/dev/null || true'
sudo -u jobplatform bash -c 'pm2 start npm --name "job-platform-frontend" -- start'
sudo -u jobplatform bash -c 'pm2 save'

# Restart nginx
sudo systemctl restart nginx

echo -e "${GREEN}All services started!${NC}\n"

################################################################################
# Step 9: Verify deployment
################################################################################
echo -e "${YELLOW}Step 9: Verifying deployment...${NC}"

sleep 5

# Check service status
echo "Checking service status..."
sudo systemctl status job-platform-backend --no-pager | head -10
sudo systemctl status job-platform-celery-worker --no-pager | head -10
sudo systemctl status nginx --no-pager | head -10

# Test backend API
echo ""
echo "Testing backend API..."
curl -f http://localhost:8000/api/health 2>/dev/null && echo -e "${GREEN}✓ Backend API is responding${NC}" || echo -e "${RED}✗ Backend API is not responding${NC}"

# Test frontend
echo "Testing frontend..."
curl -f http://localhost:3000 2>/dev/null && echo -e "${GREEN}✓ Frontend is responding${NC}" || echo -e "${RED}✗ Frontend is not responding${NC}"

################################################################################
# Deployment Summary
################################################################################
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Completed Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Application URL: http://${DOMAIN}"
echo "Backend API: http://${DOMAIN}/api"
echo ""
echo "Service Status Commands:"
echo "  sudo systemctl status job-platform-backend"
echo "  sudo systemctl status job-platform-celery-worker"
echo "  sudo systemctl status job-platform-celery-beat"
echo "  sudo -u jobplatform pm2 status"
echo ""
echo "View Logs:"
echo "  sudo journalctl -u job-platform-backend -f"
echo "  sudo journalctl -u job-platform-celery-worker -f"
echo "  sudo -u jobplatform pm2 logs job-platform-frontend"
echo ""
echo "Deployment log saved to: $LOG_FILE"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Configure SSL certificate: sudo certbot --nginx -d ${DOMAIN}"
echo "2. Test the application in your browser"
echo "3. Create admin user if needed"
echo ""
