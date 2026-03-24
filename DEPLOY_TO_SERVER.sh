#!/bin/bash

# Complete deployment script for EC2 server
# This script will:
# 1. Clone the repository
# 2. Set up backend with correct environment variables
# 3. Set up frontend with production API URL
# 4. Start both services with PM2

set -e

SERVER_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"
GITHUB_PAT="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"
REPO_URL="https://${GITHUB_PAT}@github.com/sourabh1983/job-platform.git"
DOMAIN="trusanity.com"

echo "=========================================="
echo "Deploying to EC2 Server"
echo "=========================================="

# Deploy script to server
ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no ubuntu@${SERVER_IP} << 'ENDSSH'

set -e

echo "Step 1: Cleaning up old deployment..."
pm2 delete all 2>/dev/null || true
rm -rf /home/ubuntu/job-platform

echo "Step 2: Cloning repository..."
cd /home/ubuntu
git clone https://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@github.com/sourabh1983/job-platform.git
cd job-platform

echo "Step 3: Setting up backend..."
cd backend

# Create .env file with production settings
cat > .env << 'EOF'
# Application
APP_NAME="Job Aggregation Platform"
APP_ENV=production
DEBUG=False
SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=False

# Database
DATABASE_URL=postgresql://jobplatform_user:jobplatform2024@localhost/jobplatform_db
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_DB=1

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# JWT Authentication
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS - Allow frontend domain
CORS_ORIGINS=http://trusanity.com,http://www.trusanity.com,http://3.110.220.37,http://localhost:3000

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# External APIs (optional)
INDEED_API_KEY=
LINKEDIN_RSS_URLS=

# Stripe (optional)
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=

# Storage
STORAGE_BACKEND=local
STORAGE_LOCAL_PATH=./uploads

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

# Scraping
SCRAPING_USER_AGENT=Mozilla/5.0 (compatible; JobBot/1.0)
SCRAPING_RATE_LIMIT_LINKEDIN=10
SCRAPING_RATE_LIMIT_INDEED=20
SCRAPING_RATE_LIMIT_NAUKRI=5
SCRAPING_RATE_LIMIT_MONSTER=5
EOF

echo "Installing backend dependencies..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Step 4: Setting up frontend..."
cd ../frontend

# Create production environment file
cat > .env.production.local << 'EOF'
NEXT_PUBLIC_API_URL=http://trusanity.com:8000
EOF

echo "Installing frontend dependencies..."
npm install

echo "Building frontend..."
npm run build

echo "Step 5: Starting services with PM2..."

# Start backend
cd /home/ubuntu/job-platform/backend
pm2 start venv/bin/uvicorn --name "backend" -- app.main:app --host 0.0.0.0 --port 8000

# Start frontend
cd /home/ubuntu/job-platform/frontend
pm2 start npm --name "frontend" -- start

# Save PM2 configuration
pm2 save
pm2 startup

echo "Step 6: Checking service status..."
sleep 5
pm2 list

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo "Backend API: http://trusanity.com:8000"
echo "Frontend: http://trusanity.com:3000"
echo "API Docs: http://trusanity.com:8000/docs"
echo ""
echo "Admin Login:"
echo "Email: admin@trusanity.com"
echo "Password: Admin@123"
echo ""
echo "To check logs:"
echo "  pm2 logs backend"
echo "  pm2 logs frontend"
echo ""
echo "To restart services:"
echo "  pm2 restart all"
echo "=========================================="

ENDSSH

echo ""
echo "Deployment script completed!"
echo ""
echo "IMPORTANT: You need to configure EC2 Security Group to allow:"
echo "  - Port 8000 (Backend API)"
echo "  - Port 3000 (Frontend)"
echo ""
echo "To test the deployment:"
echo "  curl http://trusanity.com:8000/health"
echo "  curl http://trusanity.com:3000"
