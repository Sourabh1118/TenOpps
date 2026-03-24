#!/bin/bash

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

chmod 400 "$SSH_KEY"

echo "📋 Checking Backend Logs"
echo "========================"
echo ""

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << 'ENDSSH'

echo "Backend Error Logs (last 50 lines):"
echo "===================================="
sudo tail -50 /var/log/job-platform/backend-error.log 2>/dev/null || echo "No error log found"

echo ""
echo ""
echo "Backend Access Logs (last 20 lines):"
echo "====================================="
sudo tail -20 /var/log/job-platform/backend-access.log 2>/dev/null || echo "No access log found"

echo ""
echo ""
echo "Systemd Service Logs (last 30 lines):"
echo "======================================"
sudo journalctl -u job-platform-backend -n 30 --no-pager 2>/dev/null || echo "No systemd logs found"

ENDSSH

