#!/bin/bash

################################################################################
# Final Admin Login Fix
# Comprehensive fix for admin login issues
################################################################################

set -e

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

echo "🔧 Final Admin Login Fix"
echo "========================"
echo ""

chmod 400 "$SSH_KEY"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << 'ENDSSH'
set -e

cd /home/jobplatform/job-platform/backend

echo "1️⃣ Verifying database and tables..."
echo ""

sudo -u jobplatform bash -c "source venv/bin/activate && python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

from sqlalchemy import text, inspect
from app.db.session import engine

with engine.connect() as conn:
    result = conn.execute(text('SELECT current_database()'))
    print(f'✓ Connected to database: {result.scalar()}')
    
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f'✓ Found {len(tables)} tables')

if 'employers' in tables:
    print('✓ employers table exists')
else:
    print('❌ employers table NOT found!')
    sys.exit(1)
PYEOF
"

echo ""
echo "2️⃣ Checking if admin account exists..."
echo ""

ADMIN_EXISTS=$(sudo -u jobplatform bash -c "source venv/bin/activate && python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

from app.db.session import SessionLocal
from app.models.employer import Employer

db = SessionLocal()
try:
    admin = db.query(Employer).filter(Employer.email == 'admin@trusanity.com').first()
    if admin:
        print('EXISTS')
        print(f'User ID: {admin.id}', file=sys.stderr)
        print(f'Email: {admin.email}', file=sys.stderr)
        print(f'Company: {admin.company_name}', file=sys.stderr)
    else:
        print('NOT_EXISTS')
finally:
    db.close()
PYEOF
")

if echo "$ADMIN_EXISTS" | grep -q "EXISTS"; then
    echo "✓ Admin account exists"
else
    echo "❌ Admin account does NOT exist"
    echo ""
    echo "Creating admin account..."
    sudo -u jobplatform bash -c "source venv/bin/activate && python scripts/create_admin.py admin@trusanity.com Admin@123"
fi

echo ""
echo "3️⃣ Testing login with correct database connection..."
echo ""

sudo -u jobplatform bash -c "source venv/bin/activate && python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

from app.db.session import SessionLocal
from app.models.employer import Employer
from app.core.security import verify_password
import bcrypt

db = SessionLocal()
try:
    # Find admin
    admin = db.query(Employer).filter(Employer.email == 'admin@trusanity.com').first()
    
    if not admin:
        print('❌ Admin not found in database')
        sys.exit(1)
    
    print(f'✓ Found admin: {admin.email}')
    print(f'  ID: {admin.id}')
    print(f'  Company: {admin.company_name}')
    print(f'  Verified: {admin.verified}')
    
    # Test password
    password = 'Admin@123'
    password_bytes = password.encode('utf-8')
    hash_bytes = admin.password_hash.encode('utf-8')
    
    if bcrypt.checkpw(password_bytes, hash_bytes):
        print(f'✓ Password verification successful!')
    else:
        print(f'❌ Password verification failed!')
        sys.exit(1)
        
finally:
    db.close()
PYEOF
"

echo ""
echo "4️⃣ Testing login API endpoint..."
echo ""

# Wait a moment for any connection pool issues to clear
sleep 2

LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-Proto: https" \
  -d '{
    "email": "admin@trusanity.com",
    "password": "Admin@123"
  }')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "✅ Login API works!"
    echo ""
    echo "Token received:"
    echo "$LOGIN_RESPONSE" | python3 -m json.tool 2>/dev/null | head -20
else
    echo "❌ Login API failed"
    echo ""
    echo "Response:"
    echo "$LOGIN_RESPONSE"
    echo ""
    echo "Checking backend logs for errors..."
    sudo journalctl -u job-platform-backend -n 20 --no-pager | grep -i error || echo "No recent errors"
fi

echo ""
echo "5️⃣ Testing external HTTPS access..."
echo ""

EXTERNAL_RESPONSE=$(curl -s -X POST https://trusanity.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@trusanity.com",
    "password": "Admin@123"
  }')

if echo "$EXTERNAL_RESPONSE" | grep -q "access_token"; then
    echo "✅ External HTTPS login works!"
else
    echo "⚠️  External login response:"
    echo "$EXTERNAL_RESPONSE"
fi

ENDSSH

echo ""
echo "================================="
echo "Summary"
echo "================================="
echo ""
echo "If all tests passed, you can login at:"
echo "  URL: https://trusanity.com/login"
echo "  Email: admin@trusanity.com"
echo "  Password: Admin@123"
echo ""
echo "⚠️  IMPORTANT: Always use HTTPS, not HTTP!"
echo ""

