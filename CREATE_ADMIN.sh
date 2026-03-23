#!/bin/bash

################################################################################
# Create Admin Account on Server
# Run this from your local machine
################################################################################

set -e

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

echo "🔐 Creating Admin Account"
echo "========================="
echo ""

# Check SSH key
if [ ! -f "$SSH_KEY" ]; then
    echo "❌ Error: SSH key not found: $SSH_KEY"
    exit 1
fi

chmod 400 "$SSH_KEY"

# Get custom credentials if provided
ADMIN_EMAIL="${1:-admin@trusanity.com}"
ADMIN_PASSWORD="${2:-Admin@123}"

echo "Admin Email: $ADMIN_EMAIL"
echo ""
echo "Connecting to server..."
echo ""

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << ENDSSH
set -e

cd /home/jobplatform/job-platform/backend

echo "Creating admin user..."
echo ""

sudo -u jobplatform bash -c "source venv/bin/activate && python scripts/create_admin.py '$ADMIN_EMAIL' '$ADMIN_PASSWORD'"

ENDSSH

echo ""
echo "✅ Done!"
echo ""
echo "You can now login at: http://trusanity.com/login"
echo ""
