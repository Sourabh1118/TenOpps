#!/bin/bash

# Fix duplicate migration 007 files on server
# Run this on your EC2 instance

echo "=== Fixing Duplicate Migration Numbers ==="

cd /home/jobplatform/job-platform/backend

# Check current migration files
echo "Current 007 migrations:"
ls -la alembic/versions/007_*.py

# The issue: Two files numbered 007
# - 007_add_url_imports_used_to_employers.py (smaller, should be 007)
# - 007_create_analytics_tables.py (larger, should be renumbered to 008)

# Solution: Rename analytics to 008, and shift others up
echo ""
echo "Renaming migrations..."

# Backup first
cp -r alembic/versions alembic/versions.backup

# Rename in reverse order to avoid conflicts
mv alembic/versions/010_create_admins_table.py alembic/versions/011_create_admins_table.py
mv alembic/versions/009_add_performance_indexes.py alembic/versions/010_add_performance_indexes.py  
mv alembic/versions/008_create_consents_table.py alembic/versions/009_create_consents_table.py
mv alembic/versions/007_create_analytics_tables.py alembic/versions/008_create_analytics_tables.py

echo "✓ Files renamed"
echo ""
echo "Now updating down_revision references in the files..."

# Update down_revision in 008 (was 007_create_analytics)
sed -i "s/down_revision = '006'/down_revision = '007'/" alembic/versions/008_create_analytics_tables.py

# Update down_revision in 009 (was 008_create_consents)  
sed -i "s/down_revision = '007'/down_revision = '008'/" alembic/versions/009_create_consents_table.py

# Update down_revision in 010 (was 009_add_performance)
sed -i "s/down_revision = '008'/down_revision = '009'/" alembic/versions/010_add_performance_indexes.py

# Update down_revision in 011 (was 010_create_admins)
sed -i "s/down_revision = '009'/down_revision = '010'/" alembic/versions/011_create_admins_table.py

echo "✓ References updated"
echo ""
echo "New migration order:"
ls -la alembic/versions/*.py | grep -E "00[0-9]_|01[0-1]_"

echo ""
echo "Now run: alembic upgrade head"
