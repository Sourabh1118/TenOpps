#!/bin/bash

################################################################################
# Check Admin Account Status on Server
# Tests if admin account exists and can login
################################################################################

set -e

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

echo "🔍 Checking Admin Account Status"
echo "================================="
echo ""

# Check SSH key
if [ ! -f "$SSH_KEY" ]; then
    echo "❌ Error: SSH key not found: $SSH_KEY"
    exit 1
fi

chmod 400 "$SSH_KEY"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << 'ENDSSH'
set -e

cd /home/jobplatform/job-platform/backend

echo "1️⃣ Checking if admin account exists in database..."
echo ""

sudo -u jobplatform bash -c "source venv/bin/activate && python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

from app.db.session import SessionLocal
from app.models.employer import Employer

db = SessionLocal()
try:
    admin = db.query(Employer).filter(Employer.email == 'admin@trusanity.com').first()
    if admin:
        print('✅ Admin account EXISTS')
        print(f'   User ID: {admin.id}')
        print(f'   Email: {admin.email}')
        print(f'   Company: {admin.company_name}')
        print(f'   Subscription: {admin.subscription_tier}')
        print(f'   Verified: {admin.verified}')
    else:
        print('❌ Admin account DOES NOT EXIST')
        print('   Run ./CREATE_ADMIN.sh to create it')
finally:
    db.close()
PYEOF
"

echo ""
echo "2️⃣ Testing login API on server (internal)..."
echo ""

LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-Proto: https" \
  -d '{
    "email": "admin@trusanity.com",
    "password": "Admin@123"
  }')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "✅ Login API works! Admin can login."
    echo ""
    echo "Response:"
    echo "$LOGIN_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$LOGIN_RESPONSE"
else
    echo "❌ Login API failed!"
    echo ""
    echo "Response:"
    echo "$LOGIN_RESPONSE"
fi

echo ""
echo "3️⃣ Testing external access..."
echo ""

EXTERNAL_RESPONSE=$(curl -s -X POST https://trusanity.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@trusanity.com",
    "password": "Admin@123"
  }')

if echo "$EXTERNAL_RESPONSE" | grep -q "access_token"; then
    echo "✅ External login works! You can login from browser."
else
    echo "❌ External login failed!"
    echo ""
    echo "Response:"
    echo "$EXTERNAL_RESPONSE"
fi

ENDSSH

echo ""
echo "================================="
echo "Summary:"
echo "================================="
echo ""
echo "If admin account exists and login works:"
echo "  → Login at: https://trusanity.com/login"
echo "  → Email: admin@trusanity.com"
echo "  → Password: Admin@123"
echo ""
echo "If admin account doesn't exist:"
echo "  → Run: ./CREATE_ADMIN.sh"
echo ""

