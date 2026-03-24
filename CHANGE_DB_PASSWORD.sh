#!/bin/bash

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

chmod 400 "$SSH_KEY"

echo "🔐 Changing Database Password"
echo "=============================="

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << 'ENDSSH'
set -e

echo "Changing jobplatform_user password to a simpler one..."
sudo -u postgres psql << 'EOSQL'
ALTER USER jobplatform_user WITH PASSWORD 'jobplatform2024';
\q
EOSQL

echo "✓ Password changed"

echo ""
echo "Updating .env file..."
cd /home/jobplatform/job-platform/backend
sudo -u jobplatform sed -i 's|^DATABASE_URL=.*|DATABASE_URL=postgresql://jobplatform_user:jobplatform2024@localhost/jobplatform_db|' .env

echo "✓ .env updated"

ENDSSH

echo ""
echo "=============================="
echo "✅ Password Changed!"
echo "=============================="
echo ""
echo "New password: jobplatform2024"
echo ""
