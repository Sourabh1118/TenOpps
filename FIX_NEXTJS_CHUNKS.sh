#!/bin/bash
# Fix Next.js chunk loading errors - Run on server

echo "=========================================="
echo "FIXING NEXT.JS CHUNK ERRORS"
echo "=========================================="

cd /home/jobplatform/job-platform/frontend || exit 1

# Step 1: Stop pm2
echo "Step 1: Stopping pm2..."
pm2 stop job-platform-frontend 2>/dev/null || true
pm2 delete job-platform-frontend 2>/dev/null || true

# Step 2: Kill port 3000
echo ""
echo "Step 2: Killing port 3000..."
sudo lsof -ti:3000 | xargs sudo kill -9 2>/dev/null || true
sleep 2

# Step 3: Clean Next.js cache
echo ""
echo "Step 3: Cleaning Next.js cache..."
rm -rf .next
rm -rf node_modules/.cache

# Step 4: Rebuild
echo ""
echo "Step 4: Rebuilding..."
npm run build

if [ $? -ne 0 ]; then
    echo "ERROR: Build failed!"
    exit 1
fi

# Step 5: Start pm2
echo ""
echo "Step 5: Starting pm2..."
pm2 start npm --name "job-platform-frontend" -- start

# Step 6: Wait and check
echo ""
echo "Step 6: Waiting for startup..."
sleep 10

pm2 status

# Step 7: Check logs
echo ""
echo "Step 7: Checking logs..."
pm2 logs job-platform-frontend --lines 20 --nostream

# Step 8: Save
pm2 save

echo ""
echo "=========================================="
echo "DONE!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Clear your browser cache (Ctrl+Shift+Delete)"
echo "2. Or open in incognito/private window"
echo "3. Visit: https://trusanity.com"
echo ""
echo "If still seeing errors, do a hard refresh:"
echo "  - Chrome/Firefox: Ctrl+Shift+R"
echo "  - Safari: Cmd+Shift+R"
