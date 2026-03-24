#!/bin/bash

# Fix Git Conflicts and Deploy Admin Dashboard
# This script resolves git conflicts and deploys the latest code

echo "=========================================="
echo "FIXING GIT CONFLICTS AND DEPLOYING"
echo "=========================================="
echo ""

cd /home/jobplatform/job-platform || exit 1

# Step 1: Remove untracked files that are blocking merge
echo "Step 1: Removing untracked files that block merge..."
rm -f FIX_ADMIN_ON_SERVER.sh
rm -f frontend/app/employer/pricing/page.tsx
rm -f frontend/app/employer/register/page.tsx
rm -f frontend/app/register/page.tsx
rm -f frontend/public/grid.svg
echo "✓ Untracked files removed"

# Step 2: Stash local changes
echo ""
echo "Step 2: Stashing local changes..."
sudo git stash
echo "✓ Local changes stashed"

# Step 3: Pull latest code
echo ""
echo "Step 3: Pulling latest code from GitHub..."
sudo git pull origin main
if [ $? -ne 0 ]; then
    echo "ERROR: Git pull failed!"
    echo "Please check git status and resolve manually"
    exit 1
fi
echo "✓ Code pulled successfully"

# Step 4: Fix import path in admin.ts (if needed)
echo ""
echo "Step 4: Checking admin.ts import path..."
if grep -q "from './api-client'" frontend/lib/api/admin.ts 2>/dev/null; then
    echo "Fixing import path..."
    sed -i "s|from './api-client'|from '../api-client'|g" frontend/lib/api/admin.ts
    echo "✓ Import path fixed"
else
    echo "✓ Import path is correct"
fi

# Step 5: Rebuild frontend
echo ""
echo "Step 5: Rebuilding frontend..."
cd frontend
npm run build
if [ $? -ne 0 ]; then
    echo "ERROR: Frontend build failed!"
    exit 1
fi
echo "✓ Frontend built successfully"

# Step 6: Restart backend
echo ""
echo "Step 6: Restarting backend..."
cd ..
sudo systemctl restart job-platform-backend
sleep 3
sudo systemctl status job-platform-backend --no-pager
echo "✓ Backend restarted"

# Step 7: Fix frontend pm2 process
echo ""
echo "Step 7: Fixing frontend pm2 process..."
cd frontend

# Stop and delete existing process
pm2 stop job-platform-frontend 2>/dev/null || true
pm2 delete job-platform-frontend 2>/dev/null || true

# Kill any process on port 3000
PORT_PID=$(lsof -ti:3000 2>/dev/null)
if [ ! -z "$PORT_PID" ]; then
    echo "Killing process on port 3000..."
    kill -9 $PORT_PID 2>/dev/null || sudo kill -9 $PORT_PID
    sleep 2
fi

# Start new process
pm2 start npm --name "job-platform-frontend" -- start
sleep 5

# Check status
pm2 status
pm2 save

echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Admin dashboard should now be accessible at:"
echo "https://trusanity.com/admin/dashboard"
echo ""
echo "Login with:"
echo "Email: admin@trusanity.com"
echo "Password: Admin@123"
echo ""
echo "To check logs:"
echo "  Backend: sudo journalctl -u job-platform-backend -f"
echo "  Frontend: pm2 logs job-platform-frontend"
