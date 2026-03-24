#!/bin/bash

################################################################################
# Configure SSL Certificate Auto-Renewal
################################################################################

set -e

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

echo "🔄 Configuring SSL Auto-Renewal"
echo "================================"
echo ""

chmod 400 "$SSH_KEY"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << 'ENDSSH'
set -e

echo "1️⃣ Updating certbot renewal configuration..."
echo ""

# Update renewal config to use webroot
sudo tee /etc/letsencrypt/renewal/trusanity.com.conf > /dev/null << 'EOF'
# renew_before_expiry = 30 days
version = 2.11.0
archive_dir = /etc/letsencrypt/archive/trusanity.com
cert = /etc/letsencrypt/live/trusanity.com/cert.pem
privkey = /etc/letsencrypt/live/trusanity.com/privkey.pem
chain = /etc/letsencrypt/live/trusanity.com/chain.pem
fullchain = /etc/letsencrypt/live/trusanity.com/fullchain.pem

# Options used in the renewal process
[renewalparams]
account = REDACTED
authenticator = webroot
webroot_path = /var/www/html,
server = https://acme-v02.api.letsencrypt.org/directory
key_type = ecdsa
[[webroot_map]]
trusanity.com = /var/www/html
www.trusanity.com = /var/www/html
EOF

echo "✅ Renewal configuration updated"

echo ""
echo "2️⃣ Creating webroot directory..."
echo ""

sudo mkdir -p /var/www/html/.well-known/acme-challenge
sudo chown -R www-data:www-data /var/www/html

echo ""
echo "3️⃣ Updating Nginx to serve ACME challenges..."
echo ""

# Add ACME challenge location to Nginx config
sudo sed -i '/listen 80;/a\    \n    # Let'\''s Encrypt ACME challenge\n    location /.well-known/acme-challenge/ {\n        root /var/www/html;\n    }' /etc/nginx/sites-available/job-platform

sudo nginx -t && sudo systemctl reload nginx

echo "✅ Nginx configured for ACME challenges"

echo ""
echo "4️⃣ Testing HTTPS connection..."
echo ""

# Wait for Nginx to fully reload
sleep 2

# Test HTTPS
if curl -k -s https://localhost/api/health | grep -q "healthy"; then
    echo "✅ HTTPS is working!"
else
    echo "⚠️  HTTPS health check response:"
    curl -k -s https://localhost/api/health || echo "Failed"
fi

echo ""
echo "5️⃣ Checking certificate details..."
echo ""

sudo certbot certificates

ENDSSH

echo ""
echo "================================"
echo "✅ SSL Configuration Complete!"
echo "================================"
echo ""
echo "Your site is now accessible via HTTPS:"
echo "  🔒 https://trusanity.com"
echo ""
echo "Admin Login:"
echo "  URL: https://trusanity.com/login"
echo "  Email: admin@trusanity.com"
echo "  Password: Admin@123"
echo ""
echo "Certificate will auto-renew before expiration."
echo ""

