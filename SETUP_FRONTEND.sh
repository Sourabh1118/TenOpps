#!/bin/bash
# Setup Frontend with PM2
# Run this as ubuntu user

set -e

echo "=========================================="
echo "SETTING UP FRONTEND"
echo "=========================================="
echo ""

# Step 1: Switch to jobplatform user and build frontend
echo "Step 1: Building frontend..."
sudo -u jobplatform bash <<'EOSU'
cd /home/jobplatform/job-platform/frontend

# Create .env.local
cat > .env.local <<'EOF'
NEXT_PUBLIC_API_URL=https://trusanity.com
NEXT_PUBLIC_API_BASE_PATH=/api
EOF

# Create .env.production
cat > .env.production <<'EOF'
NEXT_PUBLIC_API_URL=https://trusanity.com
NEXT_PUBLIC_API_BASE_PATH=/api
EOF

echo "Environment files created"
echo ""

# Install dependencies
echo "Installing dependencies..."
npm install

# Build frontend
echo "Building frontend..."
npm run build

echo "Frontend build complete"
EOSU

echo ""

# Step 2: Start frontend with PM2
echo "Step 2: Starting frontend with PM2..."
sudo -u jobplatform bash <<'EOSU'
cd /home/jobplatform/job-platform/frontend

# Stop if already running
pm2 stop job-platform-frontend 2>/dev/null || true
pm2 delete job-platform-frontend 2>/dev/null || true

# Start frontend
pm2 start npm --name "job-platform-frontend" -- start

# Save PM2 configuration
pm2 save

echo ""
echo "PM2 status:"
pm2 status
EOSU

echo ""

# Step 3: Setup PM2 startup
echo "Step 3: Setting up PM2 startup..."
echo "Run this command to enable PM2 on system boot:"
sudo -u jobplatform pm2 startup | grep "sudo"
echo ""
echo "Copy and run the 'sudo env PATH=...' command above"
echo ""

echo "=========================================="
echo "FRONTEND SETUP COMPLETE"
echo "=========================================="
echo ""
echo "PM2 commands:"
echo "  pm2 status"
echo "  pm2 logs job-platform-frontend"
echo "  pm2 restart job-platform-frontend"
echo "  pm2 stop job-platform-frontend"
echo ""
