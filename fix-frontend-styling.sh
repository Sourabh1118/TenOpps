#!/bin/bash

################################################################################
# Fix Frontend Styling on EC2
# Run this from your local machine
################################################################################

set -e

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

echo "=== Fixing Frontend Styling on EC2 ==="

# Check SSH key
if [ ! -f "$SSH_KEY" ]; then
    echo "Error: SSH key not found: $SSH_KEY"
    exit 1
fi

chmod 400 "$SSH_KEY"

echo "Connecting to EC2 and fixing frontend..."

ssh -i "$SSH_KEY" ubuntu@${EC2_IP} << 'ENDSSH'
set -e

cd /home/jobplatform/job-platform/frontend

echo "Step 1: Pulling latest code..."
sudo -u jobplatform git pull

echo "Step 2: Installing dependencies..."
sudo -u jobplatform npm install
sudo -u jobplatform npm install tailwindcss-animate

echo "Step 3: Clearing Next.js cache..."
sudo -u jobplatform rm -rf .next
sudo -u jobplatform rm -rf node_modules/.cache

echo "Step 4: Rebuilding frontend..."
sudo -u jobplatform npm run build

echo "Step 5: Restarting frontend service..."
sudo -u jobplatform pm2 restart job-platform-frontend || sudo -u jobplatform pm2 start npm --name "job-platform-frontend" -- start
sudo -u jobplatform pm2 save

echo "Step 6: Restarting Nginx..."
sudo systemctl restart nginx

echo ""
echo "✓ Frontend styling fixed!"
echo ""
echo "Testing..."
curl -I http://localhost:3000 | head -5

ENDSSH

echo ""
echo "Done! Check http://trusanity.com"
echo "If styles still don't load, check browser console for errors"
