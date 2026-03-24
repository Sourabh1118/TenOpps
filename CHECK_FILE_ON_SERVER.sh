#!/bin/bash

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

chmod 400 "$SSH_KEY"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << 'ENDSSH'
echo "Checking create_admin.py on server..."
grep -n "subscription_tier" /home/jobplatform/job-platform/backend/scripts/create_admin.py | head -5
ENDSSH
