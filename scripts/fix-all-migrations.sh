#!/bin/bash

# Fix all migration revision IDs to use simple numbers
# This script must be run from the project root

set -e

echo "=== Fixing All Migration Revision IDs ==="

cd backend/alembic/versions/

# Fix 001
sed -i "s/revision = '001_create_jobs_table'/revision = '001'/" 001_create_jobs_table.py

# Fix 002
sed -i "s/revision = '002_create_employers_table'/revision = '002'/" 002_create_employers_table.py
sed -i "s/down_revision = '001_create_jobs_table'/down_revision = '001'/" 002_create_employers_table.py

# Fix 003
sed -i "s/revision = '003_create_applications_table'/revision = '003'/" 003_create_applications_table.py
sed -i "s/down_revision = '002_create_employers_table'/down_revision = '002'/" 003_create_applications_table.py

# Fix 004
sed -i "s/revision = '004_create_job_sources_table'/revision = '004'/" 004_create_job_sources_table.py
sed -i "s/down_revision = '003_create_applications_table'/down_revision = '003'/" 004_create_job_sources_table.py

# Fix 005
sed -i "s/revision = '005_create_scraping_tasks_table'/revision = '005'/" 005_create_scraping_tasks_table.py
sed -i "s/down_revision = '004_create_job_sources_table'/down_revision = '004'/" 005_create_scraping_tasks_table.py

# Fix 006
sed -i "s/revision = '006_create_job_seekers_table'/revision = '006'/" 006_create_job_seekers_table.py
sed -i "s/down_revision = '005_create_scraping_tasks_table'/down_revision = '005'/" 006_create_job_seekers_table.py

# Remove duplicate 007 file (url_imports)
if [ -f "007_add_url_imports_used_to_employers.py" ]; then
    rm -f 007_add_url_imports_used_to_employers.py
    echo "Removed duplicate 007_add_url_imports_used_to_employers.py"
fi

# Remove 008 and 009 (they depend on missing structures)
if [ -f "008_create_consents_table.py" ]; then
    rm -f 008_create_consents_table.py
    echo "Removed 008_create_consents_table.py"
fi

if [ -f "009_add_performance_indexes.py" ]; then
    rm -f 009_add_performance_indexes.py
    echo "Removed 009_add_performance_indexes.py"
fi

# 007 is already correct (revision = '007', down_revision = '006')

# Clear Python cache
rm -rf __pycache__

echo "=== Migration files fixed ==="
echo ""
echo "Migration chain:"
echo "001 -> 002 -> 003 -> 004 -> 005 -> 006 -> 007"
echo ""
echo "Now run: cd /home/jobplatform/job-platform/backend && source venv/bin/activate && alembic upgrade head"
