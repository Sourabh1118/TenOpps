#!/bin/bash

################################################################################
# Comprehensive Login Diagnosis
################################################################################

set -e

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

echo "🔍 Comprehensive Login Diagnosis"
echo "================================="
echo ""

chmod 400 "$SSH_KEY"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << 'ENDSSH'
set -e

echo "1️⃣ Checking bcrypt/passlib versions..."
echo ""

cd /home/jobplatform/job-platform/backend
sudo -u jobplatform bash -c "source venv/bin/activate && pip list | grep -E 'bcrypt|passlib'"

echo ""
echo "2️⃣ Checking backend service environment..."
echo ""

sudo systemctl show job-platform-backend | grep -E "EnvironmentFile|WorkingDirectory"

echo ""
echo "3️⃣ Testing password verification directly..."
echo ""

sudo -u jobplatform bash -c "source venv/bin/activate && python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

from app.db.session import SessionLocal
from app.models.employer import Employer
from app.core.security import verify_password

db = SessionLocal()
try:
    admin = db.query(Employer).filter(Employer.email == 'admin@trusanity.com').first()
    
    if not admin:
        print('❌ Admin not found')
        sys.exit(1)
    
    print(f'✓ Admin found: {admin.email}')
    print(f'  Password hash: {admin.password_hash[:20]}...')
    
    # Test with verify_password function
    try:
        result = verify_password('Admin@123', admin.password_hash)
        print(f'  verify_password result: {result}')
    except Exception as e:
        print(f'  verify_password error: {e}')
    
    # Test with bcrypt directly
    import bcrypt
    password_bytes = 'Admin@123'.encode('utf-8')
    hash_bytes = admin.password_hash.encode('utf-8')
    bcrypt_result = bcrypt.checkpw(password_bytes, hash_bytes)
    print(f'  bcrypt.checkpw result: {bcrypt_result}')
    
finally:
    db.close()
PYEOF
"

echo ""
echo "4️⃣ Checking auth.py for password verification..."
echo ""

grep -A 10 "def login" /home/jobplatform/job-platform/backend/app/api/auth.py | head -20

echo ""
echo "5️⃣ Testing login API with detailed error..."
echo ""

curl -v -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-Proto: https" \
  -d '{
    "email": "admin@trusanity.com",
    "password": "Admin@123"
  }' 2>&1 | tail -30

echo ""
echo "6️⃣ Checking recent backend errors..."
echo ""

sudo journalctl -u job-platform-backend -n 20 --no-pager | grep -i "error\|warning\|bcrypt\|password"

ENDSSH

echo ""
echo "================================="
echo "Diagnosis Complete"
echo "================================="
echo ""

