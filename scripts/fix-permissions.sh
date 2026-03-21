#!/bin/bash
################################################################################
# Permission Fix Script
# Fixes permission issues for the Job Platform deployment
################################################################################

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}Job Platform - Permission Fix Script${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

DEPLOY_USER="jobplatform"
APP_DIR="/home/$DEPLOY_USER/job-platform"

echo "Fixing permissions..."

# Make jobplatform home directory accessible
if [ -d "/home/$DEPLOY_USER" ]; then
    chmod 755 /home/$DEPLOY_USER
    echo -e "${GREEN}✓ Fixed /home/$DEPLOY_USER permissions${NC}"
fi

# Add ubuntu user to jobplatform group
if id "ubuntu" &>/dev/null; then
    usermod -a -G $DEPLOY_USER ubuntu
    echo -e "${GREEN}✓ Added ubuntu user to $DEPLOY_USER group${NC}"
fi

# Fix application directory permissions
if [ -d "$APP_DIR" ]; then
    chmod -R g+rX "$APP_DIR"
    echo -e "${GREEN}✓ Fixed $APP_DIR permissions${NC}"
fi

# Fix log directory permissions
if [ -d "/var/log/job-platform" ]; then
    chmod 755 /var/log/job-platform
    echo -e "${GREEN}✓ Fixed /var/log/job-platform permissions${NC}"
fi

echo ""
echo -e "${GREEN}Permissions fixed successfully!${NC}"
echo ""
echo "Note: The ubuntu user needs to log out and log back in for group changes to take effect."
echo "Or run: newgrp $DEPLOY_USER"
echo ""
echo "You can now access the directory with:"
echo "  ls -la /home/$DEPLOY_USER/job-platform/"
echo "  ls -la /home/$DEPLOY_USER/job-platform/backend/"
