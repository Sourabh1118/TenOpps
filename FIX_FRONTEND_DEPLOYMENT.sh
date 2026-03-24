#!/bin/bash

# Fix Frontend Deployment Issues
# This script fixes the 404 errors and HTTPS configuration

set -e

echo "🔧 Fixing Frontend Deployment..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
SERVER_IP="3.110.220.37"
PEM_FILE="trusanity-pem.pem"
FRONTEND_DIR="/home/jobplatform/job-platform/frontend"

echo -e "${YELLOW}Step 1: Creating production environment file...${NC}"
cat > frontend/.env.production.local << 'EOF'
# Production API Configuration
NEXT_PUBLIC_API_URL=https://trusanity.com
NEXT_PUBLIC_API_BASE_PATH=/api

# Environment
NEXT_PUBLIC_ENV=production

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_FEATURED_JOBS=true
EOF

echo -e "${GREEN}✓ Production environment file created${NC}"

echo -e "${YELLOW}Step 2: Uploading new files to server...${NC}"

# Upload the new route files
scp -i "$PEM_FILE" frontend/app/register/page.tsx ubuntu@$SERVER_IP:$FRONTEND_DIR/app/register/
scp -i "$PEM_FILE" -r frontend/app/employer/pricing ubuntu@$SERVER_IP:$FRONTEND_DIR/app/employer/
scp -i "$PEM_FILE" frontend/.env.production.local ubuntu@$SERVER_IP:$FRONTEND_DIR/

echo -e "${GREEN}✓ Files uploaded${NC}"

echo -e "${YELLOW}Step 3: Rebuilding frontend on server...${NC}"

ssh -i "$PEM_FILE" ubuntu@$SERVER_IP << 'ENDSSH'
set -e

cd /home/jobplatform/job-platform/frontend

# Switch to jobplatform user and rebuild
sudo -u jobplatform bash << 'EOF'
set -e

# Load environment
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

cd /home/jobplatform/job-platform/frontend

echo "Installing dependencies..."
npm install

echo "Building frontend with production config..."
npm run build

echo "Restarting frontend service..."
pm2 restart job-platform-frontend || pm2 start npm --name "job-platform-frontend" -- start

echo "Frontend rebuilt and restarted successfully!"
EOF

ENDSSH

echo -e "${GREEN}✓ Frontend rebuilt${NC}"

echo -e "${YELLOW}Step 4: Verifying deployment...${NC}"

# Wait for service to start
sleep 5

# Check if pages are accessible
echo "Checking /register..."
curl -I https://trusanity.com/register 2>&1 | grep -q "200\|301\|302" && echo -e "${GREEN}✓ /register is accessible${NC}" || echo -e "${RED}✗ /register failed${NC}"

echo "Checking /employer/pricing..."
curl -I https://trusanity.com/employer/pricing 2>&1 | grep -q "200\|301\|302" && echo -e "${GREEN}✓ /employer/pricing is accessible${NC}" || echo -e "${RED}✗ /employer/pricing failed${NC}"

echo "Checking /login..."
curl -I https://trusanity.com/login 2>&1 | grep -q "200\|301\|302" && echo -e "${GREEN}✓ /login is accessible${NC}" || echo -e "${RED}✗ /login failed${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Frontend Deployment Fixed!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "✅ Missing routes created:"
echo "   - /register (account type selection)"
echo "   - /employer/pricing (pricing page)"
echo ""
echo "✅ HTTPS configuration updated"
echo ""
echo "🔗 Test the following URLs:"
echo "   - https://trusanity.com/login"
echo "   - https://trusanity.com/register"
echo "   - https://trusanity.com/employer/pricing"
echo ""
echo "👤 Admin Login:"
echo "   Email: admin@trusanity.com"
echo "   Password: Admin@123"
echo "   URL: https://trusanity.com/login"
echo ""
echo "📝 Note: Make sure to use HTTPS (not HTTP)"
echo ""
