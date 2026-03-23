#!/bin/bash

################################################################################
# Quick Deployment Script - Run this NOW from your local machine
################################################################################

set -e

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

echo "=== Deploying to EC2: ${EC2_IP} ==="
echo ""

# Check SSH key
if [ ! -f "$SSH_KEY" ]; then
    echo "Error: SSH key not found: $SSH_KEY"
    echo "Please ensure trusanity-pem.pem is in the current directory"
    exit 1
fi

chmod 400 "$SSH_KEY"

echo "Step 1: Connecting to EC2..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << 'ENDSSH'
set -e

echo "Step 2: Pulling latest code..."
if [ -d "/home/jobplatform/job-platform" ]; then
    cd /home/jobplatform/job-platform
    sudo -u jobplatform git pull
else
    cd /home/jobplatform
    sudo -u jobplatform git clone https://YOUR_GITHUB_TOKEN@github.com/Sourabh1118/TenOpps.git job-platform
fi

echo "Step 3: Fixing migrations..."
cd /home/jobplatform/job-platform
chmod +x scripts/fix-all-migrations.sh
sudo -u jobplatform bash scripts/fix-all-migrations.sh

echo "Step 4: Running deployment (this takes 10-15 minutes)..."
sudo bash scripts/complete-clean-deploy.sh trusanity.com YOUR_GITHUB_TOKEN Herculis@123 Herculis@123

echo ""
echo "=== Deployment Complete! ==="
echo ""
echo "Checking services..."
systemctl is-active job-platform-backend && echo "✓ Backend running" || echo "✗ Backend not running"
systemctl is-active job-platform-celery-worker && echo "✓ Celery running" || echo "✗ Celery not running"
systemctl is-active nginx && echo "✓ Nginx running" || echo "✗ Nginx not running"
sudo -u jobplatform pm2 list | grep -q "job-platform-frontend.*online" && echo "✓ Frontend running" || echo "✗ Frontend not running"

echo ""
echo "Application URL: http://trusanity.com"
echo "Backend API: http://trusanity.com/api"
echo ""
echo "Next: Configure SSL with: sudo certbot --nginx -d trusanity.com"

ENDSSH

echo ""
echo "Done! Visit http://trusanity.com to see your application"
