#!/bin/bash
# Setup Nginx Configuration
# Run this as ubuntu user with sudo access

set -e

echo "=========================================="
echo "SETTING UP NGINX"
echo "=========================================="
echo ""

# Step 1: Create Nginx configuration
echo "Step 1: Creating Nginx configuration..."
sudo tee /etc/nginx/sites-available/job-platform > /dev/null <<'EOF'
server {
    listen 80;
    server_name trusanity.com www.trusanity.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend docs
    location /docs {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
EOF

echo "Nginx configuration created"
echo ""

# Step 2: Enable site
echo "Step 2: Enabling site..."
sudo ln -sf /etc/nginx/sites-available/job-platform /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
echo ""

# Step 3: Test configuration
echo "Step 3: Testing Nginx configuration..."
sudo nginx -t
echo ""

# Step 4: Restart Nginx
echo "Step 4: Restarting Nginx..."
sudo systemctl restart nginx
sudo systemctl status nginx --no-pager
echo ""

echo "=========================================="
echo "NGINX SETUP COMPLETE"
echo "=========================================="
echo ""
echo "Your site should now be accessible at:"
echo "  http://trusanity.com"
echo "  http://www.trusanity.com"
echo ""
echo "Next step: Install SSL certificate with SETUP_SSL.sh"
echo ""
