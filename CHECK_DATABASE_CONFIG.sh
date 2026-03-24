#!/bin/bash

################################################################################
# Check Database Configuration
################################################################################

set -e

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

echo "🔍 Checking Database Configuration"
echo "==================================="
echo ""

chmod 400 "$SSH_KEY"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << 'ENDSSH'
set -e

cd /home/jobplatform/job-platform/backend

echo "1️⃣ Checking .env file..."
echo ""

if [ -f .env ]; then
    echo "DATABASE_URL from .env:"
    grep "DATABASE_URL" .env | sed 's/:[^:]*@/:****@/g' || echo "Not found"
else
    echo "❌ .env file not found!"
fi

echo ""
echo "2️⃣ Checking which database the backend connects to..."
echo ""

sudo -u jobplatform bash -c "source venv/bin/activate && python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

from app.core.config import settings
from sqlalchemy import text, inspect
from app.db.session import engine

# Print database URL (sanitized)
db_url = str(settings.DATABASE_URL)
db_url_safe = db_url.split('@')[1] if '@' in db_url else db_url
print(f'Backend connects to: ...@{db_url_safe}')

# Check current database
with engine.connect() as conn:
    result = conn.execute(text('SELECT current_database()'))
    db_name = result.scalar()
    print(f'Current database: {db_name}')
    
    # Check current schema
    result = conn.execute(text('SELECT current_schema()'))
    schema = result.scalar()
    print(f'Current schema: {schema}')
    
    # List all schemas
    result = conn.execute(text('SELECT schema_name FROM information_schema.schemata'))
    schemas = [row[0] for row in result]
    print(f'Available schemas: {schemas}')
    
    # Check tables in current schema
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f'\nTables in current schema ({schema}): {len(tables)}')
    for table in sorted(tables):
        print(f'  - {table}')
    
    # Check if employers table exists in public schema
    result = conn.execute(text(\"\"\"
        SELECT table_schema, table_name 
        FROM information_schema.tables 
        WHERE table_name = 'employers'
    \"\"\"))
    employer_tables = list(result)
    print(f'\nemployers table found in schemas:')
    for schema, table in employer_tables:
        print(f'  - {schema}.{table}')
PYEOF
"

echo ""
echo "3️⃣ Checking PostgreSQL search_path..."
echo ""

sudo -u postgres psql -d jobplatform -c "SHOW search_path;"

echo ""
echo "4️⃣ Checking if tables exist in public schema..."
echo ""

sudo -u postgres psql -d jobplatform -c "SELECT schemaname, tablename FROM pg_tables WHERE tablename IN ('employers', 'jobs', 'applications') ORDER BY schemaname, tablename;"

ENDSSH

echo ""
echo "================================="
echo "Configuration check complete"
echo "================================="
echo ""

