#!/bin/bash
# Setup Backend as Systemd Service
# Run this as ubuntu user with sudo access

set -e

echo "=========================================="
echo "SETTING UP BACKEND SERVICE"
echo "=========================================="
echo ""

# Step 1: Start Redis
echo "Step 1: Starting Redis..."
sudo systemctl start redis-server
sudo systemctl enable redis-server
sudo systemctl status redis-server --no-pager
echo ""

# Step 2: Create systemd service file
echo "Step 2: Creating systemd service file..."
sudo tee /etc/systemd/system/job-platform-backend.service > /dev/null <<'EOF'
[Unit]
Description=Job Platform Backend API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=jobplatform
WorkingDirectory=/home/jobplatform/job-platform/backend
Environment="PATH=/home/jobplatform/job-platform/backend/venv/bin"
ExecStart=/home/jobplatform/job-platform/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "Service file created at /etc/systemd/system/job-platform-backend.service"
echo ""

# Step 3: Reload systemd and start service
echo "Step 3: Starting backend service..."
sudo systemctl daemon-reload
sudo systemctl enable job-platform-backend
sudo systemctl start job-platform-backend
sleep 3
sudo systemctl status job-platform-backend --no-pager
echo ""

# Step 4: Test backend
echo "Step 4: Testing backend..."
sleep 2
curl -s http://localhost:8000/api/health || echo "Health check endpoint not available"
echo ""

echo "=========================================="
echo "BACKEND SERVICE SETUP COMPLETE"
echo "=========================================="
echo ""
echo "Service commands:"
echo "  sudo systemctl status job-platform-backend"
echo "  sudo systemctl restart job-platform-backend"
echo "  sudo systemctl stop job-platform-backend"
echo "  sudo journalctl -u job-platform-backend -f"
echo ""
