#!/bin/bash

################################################################################
# Fix Migration Chain - Fix duplicate 007 migrations
################################################################################

set -e

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

echo "🔧 Fixing Migration Chain"
echo "========================="
echo ""

chmod 400 "$SSH_KEY"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << 'ENDSSH'
set -e

cd /home/jobplatform/job-platform/backend

echo "1️⃣ Checking migration files..."
echo ""

sudo -u jobplatform bash -c "ls -la alembic/versions/*.py | grep -v __pycache__ | grep -v '\.pyc'"

echo ""
echo "2️⃣ Checking migration 007_add_url_imports..."
echo ""

sudo -u jobplatform bash -c "head -20 alembic/versions/007_add_url_imports_used_to_employers.py"

echo ""
echo "3️⃣ Fixing migration 007_add_url_imports to reference correct down_revision..."
echo ""

# Fix the down_revision in 007_add_url_imports_used_to_employers.py
sudo -u jobplatform bash -c "sed -i \"s/down_revision = '006'/down_revision = '006_create_job_seekers_table'/g\" alembic/versions/007_add_url_imports_used_to_employers.py"

echo "✅ Fixed down_revision"

echo ""
echo "4️⃣ Renaming 007_add_url_imports to 011 to avoid conflict..."
echo ""

sudo -u jobplatform bash -c "mv alembic/versions/007_add_url_imports_used_to_employers.py alembic/versions/011_add_url_imports_used_to_employers.py"

echo "✅ Renamed to 011"

echo ""
echo "5️⃣ Updating revision ID in the file..."
echo ""

sudo -u jobplatform bash -c "sed -i \"s/revision = '007'/revision = '011'/g\" alembic/versions/011_add_url_imports_used_to_employers.py"
sudo -u jobplatform bash -c "sed -i \"s/down_revision = '006_create_job_seekers_table'/down_revision = '010'/g\" alembic/versions/011_add_url_imports_used_to_employers.py"

echo "✅ Updated revision IDs"

echo ""
echo "6️⃣ Verifying migration files..."
echo ""

sudo -u jobplatform bash -c "ls -la alembic/versions/*.py | grep -v __pycache__ | grep -v '\.pyc'"

echo ""
echo "7️⃣ Stamping database to current state (010)..."
echo ""

sudo -u jobplatform bash -c "source venv/bin/activate && alembic stamp 010"

echo ""
echo "8️⃣ Running migration 011..."
echo ""

sudo -u jobplatform bash -c "source venv/bin/activate && alembic upgrade head"

echo ""
echo "9️⃣ Restarting backend..."
echo ""

sudo systemctl restart job-platform-backend

echo "Waiting for backend..."
sleep 5

curl -s http://localhost:8000/api/health > /dev/null && echo "✅ Backend is healthy!" || echo "⚠️  Backend may still be starting..."

ENDSSH

echo ""
echo "================================="
echo "✅ Migration chain fixed!"
echo "================================="
echo ""

