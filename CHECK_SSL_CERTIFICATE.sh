#!/bin/bash

################################################################################
# Check SSL Certificate Installation
################################################################################

set -e

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

echo "🔒 Checking SSL Certificate Installation"
echo "========================================="
echo ""

chmod 400 "$SSH_KEY"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << 'ENDSSH'
set -e

echo "1️⃣ Checking Nginx configuration..."
echo ""

if [ -f /etc/nginx/sites-available/job-platform ]; then
    echo "Nginx config exists. Checking SSL settings:"
    echo ""
    grep -A 5 "listen 443" /etc/nginx/sites-available/job-platform || echo "No HTTPS listener found"
    echo ""
    grep "ssl_certificate" /etc/nginx/sites-available/job-platform || echo "No SSL certificate configured"
else
    echo "❌ Nginx config not found at /etc/nginx/sites-available/job-platform"
fi

echo ""
echo "2️⃣ Checking for SSL certificates..."
echo ""

if [ -d /etc/letsencrypt/live/trusanity.com ]; then
    echo "✅ Let's Encrypt certificates found:"
    ls -la /etc/letsencrypt/live/trusanity.com/
else
    echo "❌ No Let's Encrypt certificates found for trusanity.com"
fi

echo ""
echo "3️⃣ Checking Nginx status..."
echo ""

sudo systemctl status nginx --no-pager | head -15

echo ""
echo "4️⃣ Testing HTTPS connection..."
echo ""

# Test if port 443 is listening
if sudo netstat -tlnp 2>/dev/null | grep :443 || sudo ss -tlnp 2>/dev/null | grep :443; then
    echo "✅ Port 443 is listening"
else
    echo "❌ Port 443 is NOT listening"
fi

echo ""
echo "5️⃣ Testing domain resolution..."
echo ""

echo "Domain: trusanity.com"
dig +short trusanity.com || nslookup trusanity.com | grep Address | tail -1

echo ""
echo "6️⃣ Checking Nginx error logs..."
echo ""

sudo tail -20 /var/log/nginx/error.log 2>/dev/null || echo "No error log found"

ENDSSH

echo ""
echo "========================================="
echo "SSL Certificate Check Complete"
echo "========================================="
echo ""

