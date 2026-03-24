#!/bin/bash

# Fix Frontend PM2 Process
# This script resolves port conflicts and restarts the frontend

echo "=========================================="
echo "FIXING FRONTEND PM2 PROCESS"
echo "=========================================="
echo ""

# Step 1: Stop pm2 process
echo "Step 1: Stopping pm2 process..."
pm2 stop job-platform-frontend 2>/dev/null || echo "Process not running"
pm2 delete job-platform-frontend 2>/dev/null || echo "Process not found"

# Step 2: Kill any process on port 3000
echo ""
echo "Step 2: Killing any process on port 3000..."
PORT_PID=$(lsof -ti:3000 2>/dev/null)
if [ ! -z "$PORT_PID" ]; then
    echo "Found process $PORT_PID on port 3000, killing it..."
    kill -9 $PORT_PID 2>/dev/null || sudo kill -9 $PORT_PID
    sleep 2
else
    echo "No process found on port 3000"
fi

# Step 3: Verify port is free
echo ""
echo "Step 3: Verifying port 3000 is free..."
if lsof -ti:3000 >/dev/null 2>&1; then
    echo "ERROR: Port 3000 is still in use!"
    echo "Please manually check: sudo lsof -i:3000"
    exit 1
else
    echo "✓ Port 3000 is free"
fi

# Step 4: Navigate to frontend directory
echo ""
echo "Step 4: Navigating to frontend directory..."
cd /home/jobplatform/job-platform/frontend || exit 1

# Step 5: Start pm2 process
echo ""
echo "Step 5: Starting pm2 process..."
pm2 start npm --name "job-platform-frontend" -- start

# Step 6: Wait and check status
echo ""
echo "Step 6: Waiting for process to start..."
sleep 5

pm2 status

# Step 7: Check logs
echo ""
echo "Step 7: Checking logs..."
pm2 logs job-platform-frontend --lines 20 --nostream

# Step 8: Save pm2 configuration
echo ""
echo "Step 8: Saving pm2 configuration..."
pm2 save

echo ""
echo "=========================================="
echo "DONE!"
echo "=========================================="
echo ""
echo "If the process is running, the admin dashboard should be accessible at:"
echo "https://trusanity.com/admin/dashboard"
echo ""
echo "To check logs: pm2 logs job-platform-frontend"
echo "To restart: pm2 restart job-platform-frontend"
