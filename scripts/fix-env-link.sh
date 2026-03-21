#!/bin/bash
################################################################################
# Fix Environment File Link
# Creates symlink from .env to .env.production
################################################################################

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}Fixing environment file link...${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

DEPLOY_USER="jobplatform"
APP_DIR="/home/$DEPLOY_USER/job-platform"

# Check if .env.production exists
if [ ! -f "$APP_DIR/backend/.env.production" ]; then
    echo -e "${RED}.env.production not found!${NC}"
    echo "Please run the resume-deployment.sh script first."
    exit 1
fi

# Create symlink
cd "$APP_DIR/backend"
ln -sf .env.production .env
chown -h $DEPLOY_USER:$DEPLOY_USER .env

echo -e "${GREEN}✓ Created symlink: .env -> .env.production${NC}"
echo ""
echo "Now you can run migrations:"
echo "  cd /home/jobplatform/job-platform/backend"
echo "  sudo -u jobplatform bash -c 'source venv/bin/activate && alembic upgrade head'"
