#!/bin/bash
# Install SSL Certificate with Let's Encrypt
# Run this as ubuntu user with sudo access

set -e

echo "=========================================="
echo "INSTALLING SSL CERTIFICATE"
echo "=========================================="
echo ""

echo "IMPORTANT: Before running this script, ensure:"
echo "1. DNS records point to this server's IP (3.110.220.37)"
echo "2. Nginx is running and accessible on port 80"
echo "3. Domain trusanity.com resolves to this server"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."
echo ""

# Step 1: Install Certbot if not already installed
echo "Step 1: Checking Certbot installation..."
if ! command -v certbot &> /dev/null; then
    echo "Installing Certbot..."
    sudo apt update
    sudo apt install -y certbot python3-certbot-nginx
else
    echo "Certbot already installed"
fi
echo ""

# Step 2: Get SSL certificate
echo "Step 2: Obtaining SSL certificate..."
echo "You will be prompted for:"
echo "  - Email address (for renewal notifications)"
echo "  - Agreement to terms of service"
echo "  - Whether to redirect HTTP to HTTPS (choose Yes/2)"
echo ""
sudo certbot --nginx -d trusanity.com -d www.trusanity.com
echo ""

# Step 3: Test auto-renewal
echo "Step 3: Testing certificate auto-renewal..."
sudo certbot renew --dry-run
echo ""

# Step 4: Setup auto-renewal cron job
echo "Step 4: Setting up auto-renewal..."
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
sudo systemctl status certbot.timer --no-pager
echo ""

echo "=========================================="
echo "SSL CERTIFICATE INSTALLED"
echo "=========================================="
echo ""
echo "Your site is now accessible at:"
echo "  https://trusanity.com"
echo "  https://www.trusanity.com"
echo ""
echo "Certificate will auto-renew before expiration"
echo ""
echo "To check certificate status:"
echo "  sudo certbot certificates"
echo ""
echo "To manually renew:"
echo "  sudo certbot renew"
echo ""
