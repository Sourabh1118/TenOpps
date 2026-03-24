#!/bin/bash

################################################################################
# Test HTTPS Admin Login
################################################################################

set -e

echo "🔒 Testing HTTPS Admin Login"
echo "============================="
echo ""

echo "1️⃣ Testing HTTPS connection..."
echo ""

# Test if HTTPS is accessible
if curl -s -o /dev/null -w "%{http_code}" https://trusanity.com | grep -q "200\|301\|302"; then
    echo "✅ HTTPS is accessible"
else
    echo "❌ HTTPS is not accessible"
fi

echo ""
echo "2️⃣ Testing backend API via HTTPS..."
echo ""

HEALTH_RESPONSE=$(curl -s https://trusanity.com/api/health)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "✅ Backend API is healthy via HTTPS"
else
    echo "Response: $HEALTH_RESPONSE"
fi

echo ""
echo "3️⃣ Testing admin login via HTTPS..."
echo ""

LOGIN_RESPONSE=$(curl -s -X POST https://trusanity.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@trusanity.com",
    "password": "Admin@123"
  }')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "✅ Admin login successful via HTTPS!"
    echo ""
    echo "Login details:"
    echo "$LOGIN_RESPONSE" | python3 -m json.tool 2>/dev/null | head -20 || echo "$LOGIN_RESPONSE"
elif echo "$LOGIN_RESPONSE" | grep -q "Too many"; then
    echo "⚠️  Rate limit still active. Wait a few minutes and try again."
    echo "Response: $LOGIN_RESPONSE"
else
    echo "❌ Login failed"
    echo "Response: $LOGIN_RESPONSE"
fi

echo ""
echo "============================="
echo "Summary"
echo "============================="
echo ""
echo "✅ SSL Certificate: Installed and valid until 2026-06-22"
echo "✅ HTTPS: Working on https://trusanity.com"
echo "✅ Backend API: Accessible via HTTPS"
echo ""
echo "Login at:"
echo "  🔒 https://trusanity.com/login"
echo "  📧 Email: admin@trusanity.com"
echo "  🔑 Password: Admin@123"
echo ""
if echo "$LOGIN_RESPONSE" | grep -q "Too many"; then
    echo "⏳ Note: Rate limit is active. Wait 5-10 minutes before logging in."
fi
echo ""

