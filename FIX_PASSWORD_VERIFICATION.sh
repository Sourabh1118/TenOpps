#!/bin/bash

################################################################################
# Fix Password Verification Issue
# Updates security.py to use bcrypt directly
################################################################################

set -e

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

echo "🔧 Fixing Password Verification"
echo "================================"
echo ""

chmod 400 "$SSH_KEY"

# Copy the fixed file to server
echo "1️⃣ Uploading fixed security.py..."
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    backend/app/core/security.py \
    ubuntu@${EC2_IP}:/tmp/security.py

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << 'ENDSSH'
set -e

echo "2️⃣ Backing up original file..."
sudo cp /home/jobplatform/job-platform/backend/app/core/security.py \
       /home/jobplatform/job-platform/backend/app/core/security.py.backup

echo "3️⃣ Installing fixed file..."
sudo mv /tmp/security.py /home/jobplatform/job-platform/backend/app/core/security.py
sudo chown jobplatform:jobplatform /home/jobplatform/job-platform/backend/app/core/security.py

echo "4️⃣ Restarting backend service..."
sudo systemctl restart job-platform-backend

echo "Waiting for backend to start..."
sleep 5

echo ""
echo "5️⃣ Testing password verification..."

cd /home/jobplatform/job-platform/backend
sudo -u jobplatform bash -c "source venv/bin/activate && python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

from app.core.security import verify_password
from app.db.session import SessionLocal
from app.models.employer import Employer

db = SessionLocal()
try:
    admin = db.query(Employer).filter(Employer.email == 'admin@trusanity.com').first()
    
    if not admin:
        print('❌ Admin not found')
        sys.exit(1)
    
    result = verify_password('Admin@123', admin.password_hash)
    print(f'verify_password result: {result}')
    
    if result:
        print('✅ Password verification now works!')
    else:
        print('❌ Password verification still failing')
        sys.exit(1)
finally:
    db.close()
PYEOF
"

echo ""
echo "6️⃣ Testing login API..."

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
    echo "Login successful! Token received:"
    echo "$LOGIN_RESPONSE" | python3 -m json.tool 2>/dev/null | head -10
else
    echo "❌ Login API failed"
    echo "Response: $LOGIN_RESPONSE"
fi

ENDSSH

echo ""
echo "================================"
echo "Fix Complete!"
echo "================================"
echo ""
echo "You can now login at:"
echo "  🔒 https://trusanity.com/login"
echo "  📧 Email: admin@trusanity.com"
echo "  🔑 Password: Admin@123"
echo ""

