#!/bin/bash

################################################################################
# Deploy Stunning New Landing Page Design
# Run this from your local machine
################################################################################

set -e

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

echo "🚀 Deploying Stunning New Landing Page Design"
echo "=============================================="
echo ""

# Check SSH key
if [ ! -f "$SSH_KEY" ]; then
    echo "❌ Error: SSH key not found: $SSH_KEY"
    exit 1
fi

chmod 400 "$SSH_KEY"

echo "📡 Connecting to EC2..."
echo ""

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << 'ENDSSH'
set -e

echo "📥 Step 1: Pulling latest code with new design..."
cd /home/jobplatform/job-platform
sudo -u jobplatform git stash
sudo -u jobplatform git pull origin main

echo ""
echo "🎨 Step 2: Installing dependencies..."
cd frontend
sudo -u jobplatform npm install
sudo -u jobplatform npm install tailwindcss-animate

echo ""
echo "🧹 Step 3: Clearing cache..."
sudo -u jobplatform rm -rf .next
sudo -u jobplatform rm -rf node_modules/.cache

echo ""
echo "🔨 Step 4: Building new design..."
sudo -u jobplatform npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo ""
echo "🔄 Step 5: Restarting services..."
sudo -u jobplatform pm2 restart job-platform-frontend || sudo -u jobplatform pm2 start npm --name "job-platform-frontend" -- start
sudo -u jobplatform pm2 save
sudo systemctl restart nginx

echo ""
echo "✅ Step 6: Verifying deployment..."
sleep 3

if systemctl is-active --quiet nginx && sudo -u jobplatform pm2 list | grep -q "job-platform-frontend.*online"; then
    echo "✅ All services running!"
else
    echo "⚠️  Some services may not be running. Check logs."
fi

echo ""
echo "🎉 Deployment Complete!"
echo ""
echo "New Features:"
echo "  ✨ Stunning gradient backgrounds"
echo "  🌙 Beautiful dark mode support"
echo "  🎭 Smooth animations"
echo "  💎 Glass morphism effects"
echo "  🎨 Modern color scheme"
echo "  📱 Fully responsive"
echo ""

ENDSSH

echo ""
echo "=============================================="
echo "✅ Deployment Successful!"
echo "=============================================="
echo ""
echo "🌐 Visit: http://trusanity.com"
echo ""
echo "💡 Tips:"
echo "  • Hard refresh (Ctrl+Shift+R) to see changes"
echo "  • Toggle dark mode in your browser/system"
echo "  • Check mobile responsiveness"
echo ""
echo "🎨 The new design includes:"
echo "  • Animated gradient hero section"
echo "  • Modern card designs with hover effects"
echo "  • Smooth fade-in animations"
echo "  • Professional color gradients"
echo "  • Dark mode that looks amazing"
echo ""
