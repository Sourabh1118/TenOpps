#!/bin/bash

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

chmod 400 "$SSH_KEY"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << 'ENDSSH'
cd /home/jobplatform/job-platform
echo "Current commit:"
git log -1 --oneline
echo ""
echo "Checking employer.py in current commit:"
git show HEAD:backend/app/models/employer.py | grep -A 5 "class SubscriptionTier"
ENDSSH
