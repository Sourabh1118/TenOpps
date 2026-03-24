#!/bin/bash

################################################################################
# Fix Database Permissions
# Run this from your local machine
################################################################################

set -e

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

echo "🔐 Fixing Database Permissions"
echo "=============================="
echo ""

# Check SSH key
if [ ! -f "$SSH_KEY" ]; then
    echo "❌ Error: SSH key not found: $SSH_KEY"
    exit 1
fi

chmod 400 "$SSH_KEY"

echo "Connecting to server..."
echo ""

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << 'ENDSSH'
set -e

echo "🔧 Creating database and granting permissions..."

# Drop and recreate database with proper ownership
sudo -u postgres psql << 'EOSQL'
-- Drop database if exists
DROP DATABASE IF EXISTS jobplatform_db;

-- Drop user if exists
DROP USER IF EXISTS jobplatform_user;

-- Create user
CREATE USER jobplatform_user WITH PASSWORD 'Herculis@123';

-- Create database with user as owner
CREATE DATABASE jobplatform_db OWNER jobplatform_user;

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE jobplatform_db TO jobplatform_user;

\q
EOSQL

# Now connect to the database and grant schema permissions
sudo -u postgres psql -d jobplatform_db << 'EOSQL'
-- Grant schema ownership
ALTER SCHEMA public OWNER TO jobplatform_user;

-- Grant CREATE permission on schema (PostgreSQL 15 requirement)
GRANT CREATE ON SCHEMA public TO jobplatform_user;
GRANT ALL ON SCHEMA public TO jobplatform_user;

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO jobplatform_user;

-- Grant default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO jobplatform_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO jobplatform_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO jobplatform_user;

-- Revoke public access (security best practice)
REVOKE ALL ON SCHEMA public FROM PUBLIC;

\q
EOSQL

echo "✓ Database created and permissions granted"

ENDSSH

echo ""
echo "=============================="
echo "✅ Permissions Fixed!"
echo "=============================="
echo ""
echo "Now run: ./COMPLETE_SETUP.sh"
echo ""
