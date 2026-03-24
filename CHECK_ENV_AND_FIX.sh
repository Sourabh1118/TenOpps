#!/bin/bash

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

chmod 400 "$SSH_KEY"

echo "🔍 Checking .env Configuration"
echo "==============================="

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << 'ENDSSH'
set -e

cd /home/jobplatform/job-platform/backend

echo "Current DATABASE_URL in .env:"
sudo -u jobplatform grep "^DATABASE_URL" .env || echo "Not found"

echo ""
echo "Updating .env with correct DATABASE_URL..."
# URL-encode the @ symbol and escape % for ConfigParser: Herculis@123 becomes Herculis%%40123
sudo -u jobplatform sed -i 's|^DATABASE_URL=.*|DATABASE_URL=postgresql://jobplatform_user:Herculis%%40123@localhost/jobplatform_db|' .env

echo ""
echo "Updated DATABASE_URL:"
sudo -u jobplatform grep "^DATABASE_URL" .env

echo ""
echo "Testing connection with this URL..."
sudo -u jobplatform bash -c 'source venv/bin/activate && python -c "
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
db_url = os.getenv(\"DATABASE_URL\")
print(f\"Using URL: {db_url}\")

engine = create_engine(db_url)
with engine.connect() as conn:
    result = conn.execute(text(\"SELECT current_user, current_database(), has_schema_privilege(current_user, \\\"public\\\", \\\"CREATE\\\")\"))
    row = result.fetchone()
    print(f\"Connected as: {row[0]}\")
    print(f\"Database: {row[1]}\")
    print(f\"Can CREATE: {row[2]}\")
"'

ENDSSH
