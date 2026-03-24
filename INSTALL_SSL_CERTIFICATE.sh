#!/bin/bash

################################################################################
# Install SSL Certificate for trusanity.com
# Uses Let's Encrypt (Certbot) to obtain and configure SSL
################################################################################

set -e

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

echo "🔒 Installing SSL Certificate"
echo "=============================="
echo ""

chmod 400 "$SSH_KEY"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << 'ENDSSH'
set -e

echo "1️⃣ Installing Certbot..."
echo ""

# Install certbot if not already installed
if ! command -v certbot &> /dev/null; then
    echo "Installing certbot..."
    sudo apt-get update
    sudo apt-get install -y certbot python3-certbot-nginx
else
    echo "✅ Certbot already installed"
fi

echo ""
echo "2️⃣ Checking current Nginx configuration..."
echo ""

cat /etc/nginx/sites-available/job-platform

echo ""
echo "3️⃣ Obtaining SSL certificate from Let's Encrypt..."
echo ""

# Stop nginx temporarily to allow certbot to bind to port 80
sudo systemctl stop nginx

# Obtain certificate using standalone mode
sudo certbot certonly --standalone \
    --non-interactive \
    --agree-tos \
    --email admin@trusanity.com \
    -d trusanity.com \
    -d www.trusanity.com || {
        echo "⚠️  Certificate generation failed. Trying without www..."
        sudo certbot certonly --standalone \
            --non-interactive \
            --agree-tos \
            --email admin@trusanity.com \
            -d trusanity.com
    }

echo ""
echo "4️⃣ Updating Nginx configuration for HTTPS..."
echo ""

# Backup original config
sudo cp /etc/nginx/sites-available/job-platform /etc/nginx/sites-available/job-platform.backup

# Create new Nginx config with SSL
sudo tee /etc/nginx/sites-available/job-platform > /dev/null << 'EOF'
# HTTP - Redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name trusanity.com www.trusanity.com;
    
    # Redirect all HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

# HTTPS - Main configuration
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name trusanity.com www.trusanity.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/trusanity.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/trusanity.com/privkey.pem;
    
    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Root directory for static files
    root /home/jobplatform/job-platform/frontend/.next;

    # Increase client body size for file uploads
    client_max_body_size 10M;

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
    }

    # Frontend - Next.js
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Static files
    location /_next/static/ {
        alias /home/jobplatform/job-platform/frontend/.next/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Public files
    location /public/ {
        alias /home/jobplatform/job-platform/frontend/public/;
        expires 1y;
        add_header Cache-Control "public";
    }

    # Favicon
    location = /favicon.ico {
        alias /home/jobplatform/job-platform/frontend/public/favicon.ico;
        access_log off;
    }

    # Robots.txt
    location = /robots.txt {
        alias /home/jobplatform/job-platform/frontend/public/robots.txt;
        access_log off;
    }
}
EOF

echo "✅ Nginx configuration updated"

echo ""
echo "5️⃣ Testing Nginx configuration..."
echo ""

sudo nginx -t

echo ""
echo "6️⃣ Starting Nginx..."
echo ""

sudo systemctl start nginx
sudo systemctl status nginx --no-pager | head -10

echo ""
echo "7️⃣ Setting up automatic certificate renewal..."
echo ""

# Test renewal
sudo certbot renew --dry-run

echo "✅ Certificate renewal configured"

echo ""
echo "8️⃣ Verifying HTTPS is working..."
echo ""

sleep 3

# Test HTTPS locally
if curl -k -s https://localhost/api/health > /dev/null 2>&1; then
    echo "✅ HTTPS is working locally"
else
    echo "⚠️  HTTPS test failed locally"
fi

# Check if port 443 is listening
if sudo netstat -tlnp 2>/dev/null | grep :443 || sudo ss -tlnp 2>/dev/null | grep :443; then
    echo "✅ Port 443 is listening"
else
    echo "❌ Port 443 is NOT listening"
fi

ENDSSH

echo ""
echo "=============================="
echo "✅ SSL Certificate Installed!"
echo "=============================="
echo ""
echo "Your site is now accessible via HTTPS:"
echo "  https://trusanity.com"
echo ""
echo "Login at:"
echo "  URL: https://trusanity.com/login"
echo "  Email: admin@trusanity.com"
echo "  Password: Admin@123"
echo ""
echo "Note: Wait 1-2 minutes for rate limit to clear, then try logging in."
echo ""

