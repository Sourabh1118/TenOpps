#!/bin/bash

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

chmod 400 "$SSH_KEY"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << 'ENDSSH'
echo "Checking employer model on server..."
grep -A 3 "class SubscriptionTier" /home/jobplatform/job-platform/backend/app/models/employer.py
ENDSSH
