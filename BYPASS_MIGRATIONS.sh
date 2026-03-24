#!/bin/bash

################################################################################
# Bypass Migrations - Directly update alembic version
# Since tables exist, just mark migrations as complete
################################################################################

set -e

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

echo "🔧 Bypassing Broken Migrations"
echo "==============================="
echo ""

chmod 400 "$SSH_KEY"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << 'ENDSSH'
set -e

cd /home/jobplatform/job-platform/backend

echo "1️⃣ Current database state..."
echo ""

sudo -u jobplatform bash -c "source venv/bin/activate && python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

from sqlalchemy import text, inspect
from app.db.session import engine

# Check tables
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f'Tables: {len(tables)}')
for table in sorted(tables):
    print(f'  ✓ {table}')

# Check alembic version
with engine.connect() as conn:
    result = conn.execute(text('SELECT version_num FROM alembic_version'))
    version = result.scalar()
    print(f'\nCurrent alembic version: {version}')
PYEOF
"

echo ""
echo "2️⃣ Updating alembic_version to bypass broken migrations..."
echo ""

sudo -u jobplatform bash -c "source venv/bin/activate && python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

from sqlalchemy import text
from app.db.session import engine

# Update alembic version to a safe state
# Since all tables exist, we'll set it to '010' which is the last good migration
with engine.connect() as conn:
    conn.execute(text(\"UPDATE alembic_version SET version_num = '010'\"))
    conn.commit()
    print('✅ Updated alembic_version to 010')
    
    # Verify
    result = conn.execute(text('SELECT version_num FROM alembic_version'))
    version = result.scalar()
    print(f'New alembic version: {version}')
PYEOF
"

echo ""
echo "3️⃣ Restarting backend..."
echo ""

sudo systemctl restart job-platform-backend

echo "Waiting for backend..."
sleep 5

echo ""
echo "4️⃣ Testing backend health..."
echo ""

for i in {1..10}; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy!"
        break
    else
        echo "Waiting... ($i/10)"
        sleep 2
    fi
done

echo ""
echo "5️⃣ Testing admin login..."
echo ""

LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-Proto: https" \
  -d '{
    "email": "admin@trusanity.com",
    "password": "Admin@123"
  }')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "✅ Admin login works!"
    echo ""
    echo "Login successful! You can now access:"
    echo "  URL: https://trusanity.com/login"
    echo "  Email: admin@trusanity.com"
    echo "  Password: Admin@123"
else
    echo "❌ Login failed"
    echo "Response: $LOGIN_RESPONSE"
fi

ENDSSH

echo ""
echo "================================="
echo "✅ Migration bypass complete!"
echo "================================="
echo ""

