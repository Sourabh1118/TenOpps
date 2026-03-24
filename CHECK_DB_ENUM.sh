#!/bin/bash

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

chmod 400 "$SSH_KEY"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << 'ENDSSH'
sudo -u postgres psql -d jobplatform_db << 'EOSQL'
SELECT enum_range(NULL::subscriptiontier);
\q
EOSQL
ENDSSH
