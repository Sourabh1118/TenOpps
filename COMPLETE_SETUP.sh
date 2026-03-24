#!/bin/bash

################################################################################
# Complete Setup: Migrations + Admin Account
# Run this from your local machine
################################################################################

set -e

EC2_IP="3.110.220.37"
SSH_KEY="trusanity-pem.pem"

echo "🚀 Complete Setup: Migrations + Admin Account"
echo "=============================================="
echo ""

# Check SSH key
if [ ! -f "$SSH_KEY" ]; then
    echo "❌ Error: SSH key not found: $SSH_KEY"
    exit 1
fi

chmod 400 "$SSH_KEY"

ADMIN_EMAIL="${1:-admin@trusanity.com}"
ADMIN_PASSWORD="${2:-Admin@123}"

echo "Admin Email: $ADMIN_EMAIL"
echo ""
echo "Connecting to server..."
echo ""

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@${EC2_IP} << ENDSSH
set -e

echo "📥 Step 1: Pulling latest code..."
cd /home/jobplatform/job-platform

# Fix git ownership
sudo chown -R jobplatform:jobplatform .git

# Force hard reset to ensure all files are updated
sudo -u jobplatform git fetch origin
sudo -u jobplatform git reset --hard origin/main
sudo -u jobplatform git clean -fd

echo ""
echo "🔧 Step 2: Fixing migration files..."
cd backend/alembic/versions/

# Fix all migration revision IDs
sudo -u jobplatform sed -i "s/revision = '001_create_jobs_table'/revision = '001'/" 001_create_jobs_table.py
sudo -u jobplatform sed -i "s/revision = '002_create_employers_table'/revision = '002'/" 002_create_employers_table.py
sudo -u jobplatform sed -i "s/down_revision = '001_create_jobs_table'/down_revision = '001'/" 002_create_employers_table.py
sudo -u jobplatform sed -i "s/revision = '003_create_applications_table'/revision = '003'/" 003_create_applications_table.py
sudo -u jobplatform sed -i "s/down_revision = '002_create_employers_table'/down_revision = '002'/" 003_create_applications_table.py
sudo -u jobplatform sed -i "s/revision = '004_create_job_sources_table'/revision = '004'/" 004_create_job_sources_table.py
sudo -u jobplatform sed -i "s/down_revision = '003_create_applications_table'/down_revision = '003'/" 004_create_job_sources_table.py
sudo -u jobplatform sed -i "s/revision = '005_create_scraping_tasks_table'/revision = '005'/" 005_create_scraping_tasks_table.py
sudo -u jobplatform sed -i "s/down_revision = '004_create_job_sources_table'/down_revision = '004'/" 005_create_scraping_tasks_table.py
sudo -u jobplatform sed -i "s/revision = '006_create_job_seekers_table'/revision = '006'/" 006_create_job_seekers_table.py
sudo -u jobplatform sed -i "s/down_revision = '005_create_scraping_tasks_table'/down_revision = '005'/" 006_create_job_seekers_table.py

# Fix migration 007 and later if they exist
if [ -f "007_create_analytics_tables.py" ]; then
    sudo -u jobplatform sed -i "s/down_revision = '006_create_job_seekers_table'/down_revision = '006'/" 007_create_analytics_tables.py
fi
if [ -f "008_add_url_imports_to_employers.py" ]; then
    sudo -u jobplatform sed -i "s/down_revision = '007_create_analytics_tables'/down_revision = '007'/" 008_add_url_imports_to_employers.py
fi
if [ -f "009_add_performance_indexes.py" ]; then
    sudo -u jobplatform sed -i "s/down_revision = '008_add_url_imports_to_employers'/down_revision = '008'/" 009_add_performance_indexes.py
fi

# Clear Python cache
sudo -u jobplatform rm -rf __pycache__

echo "✓ Migration files fixed"

echo ""
echo "🗄️  Step 3: Running database migrations..."
cd /home/jobplatform/job-platform/backend

# Make .env readable for migration
sudo chmod 644 .env

# Run migrations with properly URL-encoded DATABASE_URL
echo "Running migrations..."
sudo -u jobplatform bash -c 'export DATABASE_URL="postgresql://jobplatform_user:jobplatform2024@localhost/jobplatform_db" && source venv/bin/activate && alembic upgrade head'

if [ \$? -ne 0 ]; then
    echo "❌ Migration failed!"
    exit 1
fi

echo "✓ Database tables created"

echo ""
echo "👤 Step 4: Creating admin user..."
cd /home/jobplatform/job-platform/backend

# Clear Python cache to ensure latest code is used
sudo -u jobplatform find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
sudo -u jobplatform find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Create admin user
sudo -u jobplatform bash -c "source venv/bin/activate && python scripts/create_admin.py '$ADMIN_EMAIL' '$ADMIN_PASSWORD'"

ENDSSH

echo ""
echo "=============================================="
echo "✅ Setup Complete!"
echo "=============================================="
echo ""
echo "🎉 Your platform is ready!"
echo ""
echo "Admin Credentials:"
echo "  Email:    $ADMIN_EMAIL"
echo "  Password: $ADMIN_PASSWORD"
echo ""
echo "Login at: http://trusanity.com/login"
echo ""
