#!/bin/bash

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

chmod 400 "$SSH_KEY"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << 'ENDSSH'
cd /home/jobplatform/job-platform

# Fix ownership
sudo chown -R jobplatform:jobplatform .

# Check current state
echo "Current commit:"
sudo -u jobplatform git log -1 --oneline

echo ""
echo "File content:"
cat backend/app/models/employer.py | grep -A 5 "class SubscriptionTier"
ENDSSH
