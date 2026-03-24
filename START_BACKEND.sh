#!/bin/bash

################################################################################
# Start Backend API Server
# Run this from your local machine
################################################################################

set -e

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

echo "🚀 Starting Backend API Server"
echo "==============================="
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

cd /home/jobplatform/job-platform/backend

echo "🔧 Stopping any existing backend processes..."
sudo -u jobplatform pkill -f "uvicorn app.main:app" || true
sleep 2

echo ""
echo "🚀 Starting backend API server..."
sudo -u jobplatform bash -c 'source venv/bin/activate && nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &'

sleep 3

echo ""
echo "✓ Backend started"
echo ""
echo "Checking if backend is running..."
if curl -s http://localhost:8000/docs > /dev/null; then
    echo "✅ Backend is running and responding!"
else
    echo "⚠️  Backend may still be starting up..."
    echo "Check logs with: tail -f /tmp/backend.log"
fi

ENDSSH

echo ""
echo "==============================="
echo "✅ Backend Started!"
echo "==============================="
echo ""
echo "API Documentation: http://trusanity.com:8000/docs"
echo "Health Check: http://trusanity.com:8000/health"
echo ""
echo "To view logs:"
echo "  ssh -i $SSH_KEY ubuntu@$EC2_IP 'tail -f /tmp/backend.log'"
echo ""
