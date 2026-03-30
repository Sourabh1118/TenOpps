#!/bin/bash

################################################################################
# Local Deployment Script - Run this from your local machine
# This script will SSH into EC2 and deploy the application
################################################################################

set -e

# Configuration
EC2_IP="15.206.62.92"
SSH_KEY="/home/sourabh/Desktop/TenOpps/Keys/Portal.pem"
GITHUB_PAT="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"
DOMAIN="trusanity.com"
DB_PASSWORD="Herculis@123"
REDIS_PASSWORD="Herculis@123"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Deploying to EC2: ${EC2_IP} ===${NC}\n"

# Check if SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}Error: SSH key not found: $SSH_KEY${NC}"
    echo "Please ensure the SSH key is in the current directory"
    exit 1
fi

# Set correct permissions for SSH key
chmod 400 "$SSH_KEY"

echo -e "${YELLOW}Step 1: Testing SSH connection...${NC}"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} "echo 'SSH connection successful'" || {
    echo -e "${RED}Failed to connect to EC2${NC}"
    exit 1
}

echo -e "${GREEN}✓ SSH connection successful${NC}\n"

echo -e "${YELLOW}Step 2: Pulling latest code from GitHub...${NC}"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} "bash -s" << ENDSSH
set -e

# Navigate to project directory or clone if it doesn't exist
if [ -d "/home/jobplatform/job-platform" ]; then
    echo "Pulling latest code tracking to origin/main..."
    cd /home/jobplatform/job-platform
    sudo -u jobplatform git config pull.rebase false
    sudo -u jobplatform git pull origin main
else
    echo "Cloning repository..."
    cd /home/jobplatform
    sudo -u jobplatform git clone https://${GITHUB_PAT}@github.com/Sourabh1118/TenOpps-Portal.git job-platform
fi

echo "✓ Code updated"
ENDSSH

echo -e "${GREEN}✓ Code updated on EC2${NC}\n"

echo -e "${YELLOW}Step 3: Fixing migration files...${NC}"
ssh -i "$SSH_KEY" ubuntu@${EC2_IP} << 'ENDSSH'
set -e

cd /home/jobplatform/job-platform

# Make script executable
chmod +x scripts/fix-all-migrations.sh

# Run migration fix
echo "Fixing migration revision IDs..."
sudo -u jobplatform bash scripts/fix-all-migrations.sh

echo "✓ Migrations fixed"
ENDSSH

echo -e "${GREEN}✓ Migrations fixed${NC}\n"

echo -e "${YELLOW}Step 4: Running complete deployment...${NC}"
echo "This will take 10-15 minutes..."
echo ""

ssh -i "$SSH_KEY" ubuntu@${EC2_IP} << ENDSSH
set -e

cd /home/jobplatform/job-platform

# Run deployment script
sudo bash scripts/complete-clean-deploy.sh ${DOMAIN} ${GITHUB_PAT} ${DB_PASSWORD} ${REDIS_PASSWORD}

echo ""
echo "✓ Deployment completed"
ENDSSH

echo -e "${GREEN}✓ Deployment completed successfully!${NC}\n"

echo -e "${YELLOW}Step 5: Verifying services...${NC}"
ssh -i "$SSH_KEY" ubuntu@${EC2_IP} << 'ENDSSH'
echo "Checking service status..."
echo ""

# Backend
if systemctl is-active --quiet job-platform-backend; then
    echo "✓ Backend: Running"
else
    echo "✗ Backend: Not running"
fi

# Celery Worker
if systemctl is-active --quiet job-platform-celery-worker; then
    echo "✓ Celery Worker: Running"
else
    echo "✗ Celery Worker: Not running"
fi

# Celery Beat
if systemctl is-active --quiet job-platform-celery-beat; then
    echo "✓ Celery Beat: Running"
else
    echo "✗ Celery Beat: Not running"
fi

# Frontend (PM2)
if sudo -u jobplatform pm2 list | grep -q "job-platform-frontend.*online"; then
    echo "✓ Frontend: Running"
else
    echo "✗ Frontend: Not running"
fi

# Nginx
if systemctl is-active --quiet nginx; then
    echo "✓ Nginx: Running"
else
    echo "✗ Nginx: Not running"
fi

echo ""
echo "Testing API endpoint..."
if curl -f http://localhost:8000/api/health 2>/dev/null; then
    echo "✓ Backend API responding"
else
    echo "✗ Backend API not responding"
fi

ENDSSH

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Application URL: http://${DOMAIN}"
echo "Backend API: http://${DOMAIN}/api"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Configure SSL certificate:"
echo "   ssh -i ${SSH_KEY} ubuntu@${EC2_IP}"
echo "   sudo certbot --nginx -d ${DOMAIN}"
echo ""
echo "2. Test the application in your browser:"
echo "   http://${DOMAIN}"
echo ""
echo "3. View logs if needed:"
echo "   ssh -i ${SSH_KEY} ubuntu@${EC2_IP}"
echo "   sudo journalctl -u job-platform-backend -f"
echo ""

