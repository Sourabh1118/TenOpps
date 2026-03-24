#!/bin/bash

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

chmod 400 "$SSH_KEY"

echo "🔍 Checking Services Status"
echo "============================"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << 'ENDSSH'

echo "Backend processes:"
ps aux | grep uvicorn | grep -v grep || echo "No backend process found"

echo ""
echo "Frontend processes:"
ps aux | grep "next start" | grep -v grep || echo "No frontend process found"

echo ""
echo "Testing backend API:"
curl -s http://localhost:8000/docs > /dev/null && echo "✅ Backend responding" || echo "❌ Backend not responding"

echo ""
echo "Testing frontend:"
curl -s http://localhost:3000 > /dev/null && echo "✅ Frontend responding" || echo "❌ Frontend not responding"

echo ""
echo "Backend logs (last 30 lines):"
tail -30 /tmp/backend.log 2>/dev/null || echo "No backend log found"

echo ""
echo "Checking port 8000:"
netstat -tlnp 2>/dev/null | grep :8000 || ss -tlnp 2>/dev/null | grep :8000 || echo "Port 8000 not listening"

ENDSSH
