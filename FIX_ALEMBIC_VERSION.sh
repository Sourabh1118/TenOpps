#!/bin/bash

################################################################################
# Fix Alembic Version - Stamp current database state
################################################################################

set -e

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

echo "🔧 Fixing Alembic Migration State"
echo "=================================="
echo ""

chmod 400 "$SSH_KEY"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << 'ENDSSH'
set -e

cd /home/jobplatform/job-platform/backend

echo "1️⃣ Checking current alembic version..."
echo ""

sudo -u jobplatform bash -c "source venv/bin/activate && python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

from sqlalchemy import text
from app.db.session import engine

with engine.connect() as conn:
    result = conn.execute(text('SELECT version_num FROM alembic_version'))
    version = result.scalar()
    print(f'Current alembic version: {version}')
PYEOF
"

echo ""
echo "2️⃣ Listing available migrations..."
echo ""

sudo -u jobplatform bash -c "source venv/bin/activate && ls -la alembic/versions/ | grep -E '\\.py$' | grep -v __pycache__"

echo ""
echo "3️⃣ Stamping database to latest migration..."
echo ""

# Find the latest migration file
LATEST_MIGRATION=$(sudo -u jobplatform bash -c "ls alembic/versions/*.py | grep -v __pycache__ | sort | tail -1 | xargs basename | cut -d'_' -f1")

echo "Latest migration: $LATEST_MIGRATION"
echo ""

sudo -u jobplatform bash -c "source venv/bin/activate && alembic stamp head"

echo ""
echo "4️⃣ Verifying alembic version..."
echo ""

sudo -u jobplatform bash -c "source venv/bin/activate && python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

from sqlalchemy import text
from app.db.session import engine

with engine.connect() as conn:
    result = conn.execute(text('SELECT version_num FROM alembic_version'))
    version = result.scalar()
    print(f'✅ Alembic version now: {version}')
PYEOF
"

echo ""
echo "5️⃣ Restarting backend..."
echo ""

sudo systemctl restart job-platform-backend

echo "Waiting for backend to start..."
sleep 5

curl -s http://localhost:8000/api/health > /dev/null && echo "✅ Backend is healthy!" || echo "⚠️  Backend may still be starting..."

ENDSSH

echo ""
echo "================================="
echo "✅ Alembic version fixed!"
echo "================================="
echo ""

