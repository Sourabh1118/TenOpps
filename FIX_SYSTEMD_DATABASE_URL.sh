#!/bin/bash

################################################################################
# Fix Systemd Database URL
# Ensure backend service uses correct database
################################################################################

set -e

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

echo "🔧 Fixing Systemd Database Configuration"
echo "========================================="
echo ""

chmod 400 "$SSH_KEY"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << 'ENDSSH'
set -e

echo "1️⃣ Checking systemd service file..."
echo ""

cat /etc/systemd/system/job-platform-backend.service

echo ""
echo "2️⃣ Checking .env file..."
echo ""

cd /home/jobplatform/job-platform/backend
grep "DATABASE_URL" .env | sed 's/:[^:]*@/:****@/g'

echo ""
echo "3️⃣ The systemd service should use EnvironmentFile to load .env"
echo "   Let's update the service file..."
echo ""

# Create updated service file
sudo tee /etc/systemd/system/job-platform-backend.service > /dev/null << 'EOF'
[Unit]
Description=TenOpps Backend API
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=jobplatform
Group=jobplatform
WorkingDirectory=/home/jobplatform/job-platform/backend
EnvironmentFile=/home/jobplatform/job-platform/backend/.env
ExecStart=/home/jobplatform/job-platform/backend/venv/bin/gunicorn \
    -k uvicorn.workers.UvicornWorker \
    -w 2 \
    -b 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /var/log/job-platform/backend-access.log \
    --error-logfile /var/log/job-platform/backend-error.log \
    app.main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Updated systemd service file"

echo ""
echo "4️⃣ Reloading systemd and restarting service..."
echo ""

sudo systemctl daemon-reload
sudo systemctl restart job-platform-backend

echo "Waiting for service to start..."
sleep 5

echo ""
echo "5️⃣ Testing login..."
echo ""

for i in {1..10}; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy!"
        break
    else
        echo "Waiting... ($i/10)"
        sleep 2
    fi
done

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
    echo "SUCCESS! You can now login at:"
    echo "  URL: https://trusanity.com/login"
    echo "  Email: admin@trusanity.com"
    echo "  Password: Admin@123"
else
    echo "❌ Login still failing"
    echo "Response: $LOGIN_RESPONSE"
fi

ENDSSH

echo ""
echo "========================================="
echo "Systemd configuration updated"
echo "========================================="
echo ""

