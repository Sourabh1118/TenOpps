#!/bin/bash

################################################################################
# Restart Backend Service
# Force backend to reconnect to database
################################################################################

set -e

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

echo "🔄 Restarting Backend Service"
echo "=============================="
echo ""

chmod 400 "$SSH_KEY"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << 'ENDSSH'
set -e

echo "1️⃣ Stopping backend service..."
sudo systemctl stop job-platform-backend

echo "Waiting for service to stop..."
sleep 3

echo ""
echo "2️⃣ Starting backend service..."
sudo systemctl start job-platform-backend

echo "Waiting for service to start..."
sleep 5

echo ""
echo "3️⃣ Checking service status..."
sudo systemctl status job-platform-backend --no-pager | head -20

echo ""
echo "4️⃣ Waiting for backend to be ready..."

for i in {1..15}; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy!"
        break
    else
        echo "Waiting... ($i/15)"
        sleep 2
    fi
done

echo ""
echo "5️⃣ Testing login..."

LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-Proto: https" \
  -d '{
    "email": "admin@trusanity.com",
    "password": "Admin@123"
  }')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "✅ Login works!"
    echo ""
    echo "You can now login at: https://trusanity.com/login"
else
    echo "❌ Login still failing"
    echo "Response: $LOGIN_RESPONSE"
    echo ""
    echo "Checking recent logs..."
    sudo journalctl -u job-platform-backend -n 10 --no-pager | grep -i "error\|database"
fi

ENDSSH

echo ""
echo "=============================="
echo "Backend restart complete"
echo "=============================="
echo ""

