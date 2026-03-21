#!/bin/bash

#############################################
# Clean Reinstall Script for AWS EC2
# This script removes all existing installation
# and prepares for fresh deployment
#############################################

set -e

echo "=========================================="
echo "Clean Reinstall - Removing Old Installation"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Stop all services
echo -e "${YELLOW}Step 1: Stopping all services...${NC}"
sudo systemctl stop job-platform-backend || true
sudo systemctl stop job-platform-celery-worker || true
sudo systemctl stop job-platform-celery-beat || true
sudo systemctl stop nginx || true

echo -e "${GREEN}Services stopped${NC}"

# Step 2: Disable and remove systemd service files
echo -e "${YELLOW}Step 2: Removing systemd service files...${NC}"
sudo systemctl disable job-platform-backend || true
sudo systemctl disable job-platform-celery-worker || true
sudo systemctl disable job-platform-celery-beat || true

sudo rm -f /etc/systemd/system/job-platform-backend.service
sudo rm -f /etc/systemd/system/job-platform-celery-worker.service
sudo rm -f /etc/systemd/system/job-platform-celery-beat.service

sudo systemctl daemon-reload
echo -e "${GREEN}Systemd files removed${NC}"

# Step 3: Remove application directory
echo -e "${YELLOW}Step 3: Removing application directory...${NC}"
sudo rm -rf /home/jobplatform/job-platform
echo -e "${GREEN}Application directory removed${NC}"

# Step 4: Drop and recreate database
echo -e "${YELLOW}Step 4: Resetting database...${NC}"
sudo -u postgres psql << EOF
-- Terminate all connections to the database
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'job_platform'
  AND pid <> pg_backend_pid();

-- Drop and recreate database
DROP DATABASE IF EXISTS job_platform;
CREATE DATABASE job_platform;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE job_platform TO job_platform_user;
EOF

echo -e "${GREEN}Database reset complete${NC}"

# Step 5: Clear Redis data
echo -e "${YELLOW}Step 5: Clearing Redis data...${NC}"
redis-cli -a Herculis@123 --no-auth-warning FLUSHALL
echo -e "${GREEN}Redis cleared${NC}"

# Step 6: Remove nginx configuration
echo -e "${YELLOW}Step 6: Removing nginx configuration...${NC}"
sudo rm -f /etc/nginx/sites-enabled/job-platform
sudo rm -f /etc/nginx/sites-available/job-platform
echo -e "${GREEN}Nginx configuration removed${NC}"

# Step 7: Clean up logs
echo -e "${YELLOW}Step 7: Cleaning up logs...${NC}"
sudo rm -rf /var/log/job-platform
echo -e "${GREEN}Logs cleaned${NC}"

echo ""
echo -e "${GREEN}=========================================="
echo "Clean Reinstall Complete!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Pull the latest deployment script from your repository:"
echo "   cd ~"
echo "   wget https://raw.githubusercontent.com/Sourabh1118/TenOpps/main/scripts/aws-complete-deploy.sh"
echo "   chmod +x aws-complete-deploy.sh"
echo ""
echo "2. Run the deployment script:"
echo "   sudo ./aws-complete-deploy.sh"
echo ""
echo "The updated script has the correct environment variable template."
