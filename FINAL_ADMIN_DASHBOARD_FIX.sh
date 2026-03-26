#!/bin/bash
# Final fix for admin dashboard - Run on server

echo "=========================================="
echo "FINAL ADMIN DASHBOARD FIX"
echo "=========================================="

cd /home/jobplatform/job-platform || exit 1

# Pull the import fix
echo "Pulling latest fix from GitHub..."
sudo git pull origin main

# Rebuild frontend
echo ""
echo "Rebuilding frontend..."
cd frontend
npm run build

if [ $? -ne 0 ]; then
    echo "ERROR: Build failed!"
    exit 1
fi

echo ""
echo "✓ Build successful!"

# Restart backend
echo ""
echo "Restarting backend..."
cd ..
sudo systemctl restart job-platform-backend

# Fix frontend pm2
echo ""
echo "Restarting frontend..."
cd frontend

# Stop existing
pm2 stop job-platform-frontend 2>/dev/null || true
pm2 delete job-platform-frontend 2>/dev/null || true

# Kill port 3000
sudo lsof -ti:3000 | xargs sudo kill -9 2>/dev/null || true
sleep 2

# Start fresh
pm2 start npm --name "job-platform-frontend" -- start
sleep 5

# Check status
pm2 status

# Check logs
echo ""
echo "Checking logs..."
pm2 logs job-platform-frontend --lines 10 --nostream

# Save
pm2 save

echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Admin dashboard: https://trusanity.com/admin/dashboard"
echo "Login: admin@trusanity.com / Admin@123"
