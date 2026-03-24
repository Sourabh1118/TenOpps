#!/bin/bash

# Fix Admin Role - Create proper admin account in admins table
# This script removes the old admin from employers table and creates a proper admin

set -e

echo "=========================================="
echo "FIX ADMIN ROLE - CREATE PROPER ADMIN"
echo "=========================================="
echo ""
echo "This will:"
echo "1. Delete old admin account from employers table"
echo "2. Create new admin account in admins table"
echo "3. Test login to verify role is 'admin'"
echo ""

# Server details
SERVER_USER="jobplatform"
SERVER_HOST="3.110.220.37"
SERVER_PATH="/home/jobplatform/job-platform"

echo "Step 1: Upload fixed create_admin.py script..."
scp backend/scripts/create_admin.py ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/backend/scripts/

echo ""
echo "Step 2: Connect to server and fix admin account..."
ssh ${SERVER_USER}@${SERVER_HOST} << 'ENDSSH'
cd /home/jobplatform/job-platform/backend

echo ""
echo "Activating virtual environment..."
source venv/bin/activate

echo ""
echo "Step 2a: Delete old admin from employers table..."
python3 << 'ENDPYTHON'
import sys
sys.path.insert(0, '/home/jobplatform/job-platform/backend')

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.employer import Employer

db = SessionLocal()

try:
    # Find and delete old admin account
    old_admin = db.query(Employer).filter(Employer.email == "admin@trusanity.com").first()
    
    if old_admin:
        print(f"Found old admin in employers table: {old_admin.id}")
        db.delete(old_admin)
        db.commit()
        print("✅ Deleted old admin from employers table")
    else:
        print("ℹ️  No admin found in employers table")
        
except Exception as e:
    db.rollback()
    print(f"❌ Error: {e}")
finally:
    db.close()
ENDPYTHON

echo ""
echo "Step 2b: Create new admin in admins table..."
python3 scripts/create_admin.py

echo ""
echo "Step 2c: Verify admin exists in admins table..."
python3 << 'ENDPYTHON'
import sys
sys.path.insert(0, '/home/jobplatform/job-platform/backend')

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.admin import Admin

db = SessionLocal()

try:
    admin = db.query(Admin).filter(Admin.email == "admin@trusanity.com").first()
    
    if admin:
        print("✅ Admin account verified in admins table:")
        print(f"   ID: {admin.id}")
        print(f"   Email: {admin.email}")
        print(f"   Full Name: {admin.full_name}")
        print(f"   Created: {admin.created_at}")
    else:
        print("❌ Admin not found in admins table!")
        
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    db.close()
ENDPYTHON

ENDSSH

echo ""
echo "Step 3: Test admin login via HTTPS..."
echo ""

RESPONSE=$(curl -s -X POST https://trusanity.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@trusanity.com",
    "password": "Admin@123"
  }')

echo "Login Response:"
echo "$RESPONSE" | python3 -m json.tool

# Check if role is admin
ROLE=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('role', 'NOT_FOUND'))" 2>/dev/null || echo "ERROR")

echo ""
if [ "$ROLE" = "admin" ]; then
    echo "=========================================="
    echo "✅ SUCCESS! Admin role is now correct!"
    echo "=========================================="
    echo ""
    echo "Admin login working with role: admin"
    echo "Platform owner can now access admin features"
    echo ""
else
    echo "=========================================="
    echo "❌ FAILED! Role is: $ROLE"
    echo "=========================================="
    echo ""
    echo "Expected role: admin"
    echo "Actual role: $ROLE"
    echo ""
fi
