#!/bin/bash

################################################################################
# Deploy Full Stack (Frontend + Backend)
# Run this from your local machine
################################################################################

set -e

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

echo "🚀 Deploying Full Stack to Production"
echo "======================================"
echo ""

# Check SSH key
if [ ! -f "$SSH_KEY" ]; then
    echo "❌ Error: SSH key not found: $SSH_KEY"
    exit 1
fi

chmod 400 "$SSH_KEY"

echo "Connecting to server..."
echo ""

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << 'ENDSSH'
set -e

cd /home/jobplatform/job-platform

echo "📥 Step 1: Pulling latest code..."
sudo chown -R jobplatform:jobplatform .
sudo -u jobplatform git fetch origin
sudo -u jobplatform git reset --hard origin/main
sudo -u jobplatform git clean -fd

echo ""
echo "🔧 Step 2: Configuring frontend environment..."
cd frontend
sudo -u jobplatform cat > .env.production.local << 'EOF'
# API Configuration
NEXT_PUBLIC_API_URL=http://trusanity.com:8000
NEXT_PUBLIC_API_BASE_PATH=/api

# Environment
NEXT_PUBLIC_ENV=production
EOF

echo ""
echo "📦 Step 3: Building frontend..."
sudo -u jobplatform npm run build

echo ""
echo "🔧 Step 4: Restarting backend..."
cd ../backend
sudo -u jobplatform pkill -f "uvicorn app.main:app" || true
sleep 2
sudo -u jobplatform bash -c 'source venv/bin/activate && nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &'
sleep 3

echo ""
echo "🔧 Step 5: Restarting frontend..."
cd ../frontend
sudo -u jobplatform pkill -f "next start" || true
sleep 2
sudo -u jobplatform bash -c 'nohup npm start > /tmp/frontend.log 2>&1 &'
sleep 3

echo ""
echo "✓ Deployment complete"

ENDSSH

echo ""
echo "======================================"
echo "✅ Full Stack Deployed!"
echo "======================================"
echo ""
echo "Frontend: http://trusanity.com:3000"
echo "Backend API: http://trusanity.com:8000/docs"
echo ""
echo "To view logs:"
echo "  Frontend: ssh -i $SSH_KEY ubuntu@$EC2_IP 'tail -f /tmp/frontend.log'"
echo "  Backend:  ssh -i $SSH_KEY ubuntu@$EC2_IP 'tail -f /tmp/backend.log'"
echo ""
