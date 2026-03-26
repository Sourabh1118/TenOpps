#!/bin/bash
# Continue Deployment After Successful Migrations
# Run this as jobplatform user (you're already logged in as jobplatform)

set -e

echo "=========================================="
echo "CONTINUING DEPLOYMENT"
echo "=========================================="
echo ""

# Step 1: Create Admin Account
echo "Step 1: Creating Admin Account..."
echo "----------------------------------------"
cd /home/jobplatform/job-platform/backend
source venv/bin/activate
python scripts/create_admin.py
echo ""

# Step 2: Test Backend Locally
echo "Step 2: Testing Backend..."
echo "----------------------------------------"
echo "Starting backend in background for testing..."
cd /home/jobplatform/job-platform/backend
source venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend_test.log 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"
sleep 5

# Test backend health
echo "Testing backend health endpoint..."
curl -s http://localhost:8000/api/health || echo "Health check failed (might be normal if endpoint doesn't exist)"
echo ""

# Kill test backend
echo "Stopping test backend..."
kill $BACKEND_PID 2>/dev/null || true
echo ""

echo "=========================================="
echo "NEXT STEPS (REQUIRES UBUNTU USER)"
echo "=========================================="
echo ""
echo "The following steps require sudo access."
echo "You need to exit to ubuntu user and run these commands:"
echo ""
echo "1. Start Redis:"
echo "   sudo systemctl start redis-server"
echo "   sudo systemctl enable redis-server"
echo ""
echo "2. Create backend systemd service:"
echo "   See SETUP_BACKEND_SERVICE.sh"
echo ""
echo "3. Build and start frontend:"
echo "   See SETUP_FRONTEND.sh"
echo ""
echo "4. Configure Nginx:"
echo "   See SETUP_NGINX.sh"
echo ""
echo "5. Install SSL certificate:"
echo "   See SETUP_SSL.sh"
echo ""
echo "=========================================="
echo "ADMIN CREDENTIALS"
echo "=========================================="
echo "Email: admin@trusanity.com"
echo "Password: Admin@123"
echo "=========================================="
