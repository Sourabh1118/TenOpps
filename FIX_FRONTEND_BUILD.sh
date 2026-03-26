#!/bin/bash
# Fix Frontend Build Issue
# Run this as jobplatform user

set -e

echo "=========================================="
echo "FIXING FRONTEND BUILD"
echo "=========================================="
echo ""

cd /home/jobplatform/job-platform/frontend

# Step 1: Create .env.local file
echo "Step 1: Creating .env.local file..."
cat > .env.local <<'EOF'
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_BASE_PATH=/api
EOF

echo "Created .env.local"
echo ""

# Step 2: Create .env.production file
echo "Step 2: Creating .env.production file..."
cat > .env.production <<'EOF'
NEXT_PUBLIC_API_URL=https://trusanity.com
NEXT_PUBLIC_API_BASE_PATH=/api
EOF

echo "Created .env.production"
echo ""

# Step 3: Show current environment files
echo "Step 3: Verifying environment files..."
echo "Contents of .env.local:"
cat .env.local
echo ""
echo "Contents of .env.production:"
cat .env.production
echo ""

# Step 4: Build frontend
echo "Step 4: Building frontend..."
npm run build

echo ""
echo "=========================================="
echo "FRONTEND BUILD COMPLETE"
echo "=========================================="
echo ""
echo "Next step: Start frontend with PM2"
echo "  pm2 start npm --name 'job-platform-frontend' -- start"
echo "  pm2 save"
echo ""
