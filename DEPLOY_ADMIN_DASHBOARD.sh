#!/bin/bash

# Deploy Admin Dashboard to Server
# This script deploys the new admin dashboard and backend API endpoints

set -e

echo "=========================================="
echo "DEPLOY ADMIN DASHBOARD"
echo "=========================================="
echo ""

# Server details
SERVER_USER="jobplatform"
SERVER_HOST="3.110.220.37"
SERVER_PATH="/home/jobplatform/job-platform"

echo "Step 1: Upload backend changes..."
scp backend/app/api/admin.py ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/backend/app/api/

echo ""
echo "Step 2: Upload frontend changes..."
scp -r frontend/app/admin ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/frontend/app/
scp -r frontend/lib/api/admin.ts ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/frontend/lib/api/
scp frontend/components/layout/Header.tsx ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/frontend/components/layout/

echo ""
echo "Step 3: Restart services on server..."
ssh ${SERVER_USER}@${SERVER_HOST} << 'ENDSSH'
cd /home/jobplatform/job-platform

echo "Restarting backend..."
sudo systemctl restart job-platform-backend

echo "Rebuilding frontend..."
cd frontend
npm run build

echo "Restarting frontend..."
pm2 restart job-platform-frontend || pm2 start npm --name "job-platform-frontend" -- start

echo "✅ Services restarted"
ENDSSH

echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Admin Dashboard is now available at:"
echo "  https://trusanity.com/admin/dashboard"
echo ""
echo "Login with admin credentials:"
echo "  Email: admin@trusanity.com"
echo "  Password: Admin@123"
echo ""
echo "Available Admin Pages:"
echo "  - Dashboard: /admin/dashboard"
echo "  - User Management: /admin/users"
echo "  - Job Management: /admin/jobs"
echo "  - Rate Limits: /admin/rate-limits"
echo ""
