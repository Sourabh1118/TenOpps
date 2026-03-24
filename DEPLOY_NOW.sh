#!/bin/bash

# Quick Deploy Script - Deploy Admin Dashboard Now
# Server IP: 3.110.220.37

set -e

echo "=========================================="
echo "DEPLOYING ADMIN DASHBOARD"
echo "=========================================="
echo ""
echo "Server: 3.110.220.37"
echo "User: jobplatform"
echo ""

# Server details
SERVER_USER="jobplatform"
SERVER_HOST="3.110.220.37"
SERVER_PATH="/home/jobplatform/job-platform"

echo "Step 1: Uploading backend files..."
scp backend/app/api/admin.py ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/backend/app/api/
echo "✅ Backend uploaded"

echo ""
echo "Step 2: Uploading frontend files..."
scp -r frontend/app/admin ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/frontend/app/
scp frontend/lib/api/admin.ts ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/frontend/lib/api/
scp frontend/components/layout/Header.tsx ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/frontend/components/layout/
echo "✅ Frontend uploaded"

echo ""
echo "Step 3: Restarting services..."
ssh ${SERVER_USER}@${SERVER_HOST} << 'ENDSSH'
cd /home/jobplatform/job-platform

echo "Restarting backend..."
sudo systemctl restart job-platform-backend
echo "✅ Backend restarted"

echo ""
echo "Rebuilding frontend..."
cd frontend
npm run build
echo "✅ Frontend built"

echo ""
echo "Restarting frontend..."
pm2 restart job-platform-frontend || pm2 start npm --name "job-platform-frontend" -- start
echo "✅ Frontend restarted"

ENDSSH

echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "🎉 Admin Dashboard is now live!"
echo ""
echo "Access it at: https://trusanity.com/admin/dashboard"
echo ""
echo "Login credentials:"
echo "  📧 Email: admin@trusanity.com"
echo "  🔑 Password: Admin@123"
echo ""
echo "Available pages:"
echo "  📊 Dashboard: /admin/dashboard"
echo "  👥 Users: /admin/users"
echo "  💼 Jobs: /admin/jobs"
echo "  ⚠️  Rate Limits: /admin/rate-limits"
echo ""
echo "After login, you'll see admin navigation in the header!"
echo ""
