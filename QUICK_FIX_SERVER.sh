#!/bin/bash
# Quick fix for frontend pm2 - Run this on the server

echo "Fixing frontend pm2 process..."

# Navigate to project
cd /home/jobplatform/job-platform || exit 1

# Clean git conflicts
echo "Cleaning git conflicts..."
rm -f FIX_ADMIN_ON_SERVER.sh frontend/app/employer/pricing/page.tsx frontend/app/employer/register/page.tsx frontend/app/register/page.tsx frontend/public/grid.svg
sudo git stash
sudo git pull origin main

# Fix import if needed
if grep -q "from './api-client'" frontend/lib/api/admin.ts 2>/dev/null; then
    sed -i "s|from './api-client'|from '../api-client'|g" frontend/lib/api/admin.ts
fi

# Rebuild frontend
echo "Building frontend..."
cd frontend && npm run build || exit 1

# Restart backend
echo "Restarting backend..."
cd .. && sudo systemctl restart job-platform-backend

# Fix frontend pm2
echo "Fixing frontend pm2..."
cd frontend
pm2 delete job-platform-frontend 2>/dev/null || true
sudo lsof -ti:3000 | xargs sudo kill -9 2>/dev/null || true
sleep 2
pm2 start npm --name "job-platform-frontend" -- start
sleep 5
pm2 status
pm2 save

echo ""
echo "Done! Check https://trusanity.com/admin/dashboard"
echo "Login: admin@trusanity.com / Admin@123"
