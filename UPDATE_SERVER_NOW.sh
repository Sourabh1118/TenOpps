#!/bin/bash

################################################################################
# Update Server with CSS Fixes - Run this from your local machine
################################################################################

set -e

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

echo "=== Updating Server with CSS Fixes ==="
echo ""

# Check SSH key
if [ ! -f "$SSH_KEY" ]; then
    echo "Error: SSH key not found: $SSH_KEY"
    echo "Please ensure trusanity-pem.pem is in the current directory"
    exit 1
fi

chmod 400 "$SSH_KEY"

echo "Connecting to EC2 and updating..."
echo ""

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << 'ENDSSH'
set -e

echo "=== Step 1: Updating Code ==="
cd /home/jobplatform/job-platform

# Stash any local changes
sudo -u jobplatform git stash

# Pull latest code
sudo -u jobplatform git pull origin main

echo ""
echo "=== Step 2: Updating Frontend CSS ==="
cd /home/jobplatform/job-platform/frontend

# Update globals.css with correct HSL format
sudo -u jobplatform tee app/globals.css > /dev/null << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 0 0% 3.9%;
    --card: 0 0% 100%;
    --card-foreground: 0 0% 3.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 0 0% 3.9%;
    --primary: 0 0% 9%;
    --primary-foreground: 0 0% 98%;
    --secondary: 0 0% 96.1%;
    --secondary-foreground: 0 0% 9%;
    --muted: 0 0% 96.1%;
    --muted-foreground: 0 0% 45.1%;
    --accent: 0 0% 96.1%;
    --accent-foreground: 0 0% 9%;
    --destructive: 0 84.2% 60.2%;
    --border: 0 0% 89.8%;
    --input: 0 0% 89.8%;
    --ring: 0 0% 3.9%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 0 0% 3.9%;
    --foreground: 0 0% 98%;
    --card: 0 0% 3.9%;
    --card-foreground: 0 0% 98%;
    --popover: 0 0% 3.9%;
    --popover-foreground: 0 0% 98%;
    --primary: 0 0% 98%;
    --primary-foreground: 0 0% 9%;
    --secondary: 0 0% 14.9%;
    --secondary-foreground: 0 0% 98%;
    --muted: 0 0% 14.9%;
    --muted-foreground: 0 0% 63.9%;
    --accent: 0 0% 14.9%;
    --accent-foreground: 0 0% 98%;
    --destructive: 0 62.8% 30.6%;
    --border: 0 0% 14.9%;
    --input: 0 0% 14.9%;
    --ring: 0 0% 83.1%;
  }
  
  * {
    border-color: hsl(var(--border));
  }
  
  body {
    background-color: hsl(var(--background));
    color: hsl(var(--foreground));
    font-family: var(--font-sans), system-ui, sans-serif;
  }
}
EOF

echo ""
echo "=== Step 3: Installing Dependencies ==="
sudo -u jobplatform npm install
sudo -u jobplatform npm install tailwindcss-animate

echo ""
echo "=== Step 4: Clearing Cache ==="
sudo -u jobplatform rm -rf .next
sudo -u jobplatform rm -rf node_modules/.cache

echo ""
echo "=== Step 5: Building Frontend ==="
sudo -u jobplatform npm run build

if [ $? -ne 0 ]; then
    echo "Build failed! Check the error above."
    exit 1
fi

echo ""
echo "=== Step 6: Restarting Services ==="
# Restart frontend
sudo -u jobplatform pm2 restart job-platform-frontend || sudo -u jobplatform pm2 start npm --name "job-platform-frontend" -- start
sudo -u jobplatform pm2 save

# Restart Nginx
sudo systemctl restart nginx

echo ""
echo "=== Step 7: Verifying ==="
sleep 3

# Check if services are running
if systemctl is-active --quiet nginx; then
    echo "✓ Nginx is running"
else
    echo "✗ Nginx is not running"
fi

if sudo -u jobplatform pm2 list | grep -q "job-platform-frontend.*online"; then
    echo "✓ Frontend is running"
else
    echo "✗ Frontend is not running"
fi

# Test the frontend
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✓ Frontend is responding"
else
    echo "✗ Frontend is not responding"
fi

echo ""
echo "=== Update Complete! ==="
echo ""
echo "Visit http://trusanity.com to see the updated styling"
echo ""

ENDSSH

echo ""
echo "✓ Server updated successfully!"
echo ""
echo "Next steps:"
echo "1. Visit http://trusanity.com in your browser"
echo "2. Hard refresh (Ctrl+Shift+R or Cmd+Shift+R) to clear browser cache"
echo "3. You should now see properly formatted, styled pages"
echo ""
