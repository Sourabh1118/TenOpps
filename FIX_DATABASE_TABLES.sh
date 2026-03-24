#!/bin/bash

################################################################################
# Fix Database Tables - Run Migrations
# This creates all missing database tables
################################################################################

set -e

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

echo "🔧 Fixing Database Tables"
echo "========================="
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

cd /home/jobplatform/job-platform/backend

echo "1️⃣ Checking current database state..."
echo ""

sudo -u jobplatform bash -c "source venv/bin/activate && python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

from sqlalchemy import inspect
from app.db.session import engine

inspector = inspect(engine)
tables = inspector.get_table_names()

print(f'Current tables in database: {len(tables)}')
if tables:
    for table in sorted(tables):
        print(f'  - {table}')
else:
    print('  (no tables found)')
PYEOF
"

echo ""
echo "2️⃣ Running database migrations..."
echo ""

sudo -u jobplatform bash -c "source venv/bin/activate && alembic upgrade head"

echo ""
echo "3️⃣ Verifying tables were created..."
echo ""

sudo -u jobplatform bash -c "source venv/bin/activate && python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

from sqlalchemy import inspect
from app.db.session import engine

inspector = inspect(engine)
tables = inspector.get_table_names()

print(f'Tables after migration: {len(tables)}')
if tables:
    for table in sorted(tables):
        print(f'  ✓ {table}')
else:
    print('  ❌ No tables found!')

# Check for required tables
required_tables = ['employers', 'jobs', 'applications', 'job_sources', 'scraping_tasks', 'job_seekers']
missing = [t for t in required_tables if t not in tables]

if missing:
    print(f'\n❌ Missing required tables: {", ".join(missing)}')
else:
    print(f'\n✅ All required tables exist!')
PYEOF
"

echo ""
echo "4️⃣ Restarting backend to clear any cached state..."
echo ""

sudo systemctl restart job-platform-backend

echo "Waiting for backend to start..."
sleep 5

echo ""
echo "5️⃣ Testing backend health..."
echo ""

for i in {1..10}; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy!"
        break
    else
        echo "Waiting for backend... ($i/10)"
        sleep 2
    fi
done

ENDSSH

echo ""
echo "================================="
echo "✅ Database tables fixed!"
echo "================================="
echo ""
echo "Next steps:"
echo "  1. Create admin account: ./CREATE_ADMIN.sh"
echo "  2. Test login: ./CHECK_ADMIN_ACCOUNT.sh"
echo ""

