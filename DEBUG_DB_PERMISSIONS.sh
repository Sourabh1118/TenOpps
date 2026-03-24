#!/bin/bash

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

chmod 400 "$SSH_KEY"

echo "🔍 Debugging Database Permissions"
echo "=================================="

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << 'ENDSSH'

echo "Checking database and schema permissions..."
sudo -u postgres psql -d jobplatform_db << 'EOSQL'
-- Check database owner
SELECT d.datname, pg_catalog.pg_get_userbyid(d.datdba) as owner
FROM pg_catalog.pg_database d
WHERE d.datname = 'jobplatform_db';

-- Check schema owner and permissions
SELECT 
    nspname as schema_name,
    pg_catalog.pg_get_userbyid(nspowner) as owner,
    nspacl as permissions
FROM pg_catalog.pg_namespace
WHERE nspname = 'public';

-- Check user privileges on schema
SELECT 
    grantee,
    privilege_type
FROM information_schema.role_usage_grants
WHERE object_schema = 'public' AND grantee = 'jobplatform_user';

-- Check if user can create tables
SELECT has_schema_privilege('jobplatform_user', 'public', 'CREATE') as can_create;

\q
EOSQL

ENDSSH
