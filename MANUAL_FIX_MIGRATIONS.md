# Manual Instructions to Fix Duplicate Migration Numbers

## Problem
You have TWO migration files numbered `007`:
- `007_add_url_imports_used_to_employers.py` (small file)
- `007_create_analytics_tables.py` (large file)

This creates a conflict in the migration chain.

## Solution
Renumber the files from 007 onwards to fix the duplicate.

## Step-by-Step Manual Instructions

### Step 1: Navigate to migrations directory
```bash
cd /home/jobplatform/job-platform/backend/alembic/versions
```

### Step 2: Create a backup
```bash
cp -r /home/jobplatform/job-platform/backend/alembic/versions /home/jobplatform/job-platform/backend/alembic/versions.backup
```

### Step 3: Rename files (in REVERSE order to avoid conflicts)

```bash
# Rename 010 → 011
mv 010_create_admins_table.py 011_create_admins_table.py

# Rename 009 → 010
mv 009_add_performance_indexes.py 010_add_performance_indexes.py

# Rename 008 → 009
mv 008_create_consents_table.py 009_create_consents_table.py

# Rename 007_create_analytics → 008
mv 007_create_analytics_tables.py 008_create_analytics_tables.py

# Keep 007_add_url_imports_used_to_employers.py as is
```

### Step 4: Update down_revision in each renamed file

Edit `008_create_analytics_tables.py`:
```bash
nano 008_create_analytics_tables.py
```
Find the line: `down_revision = '006'`
Change it to: `down_revision = '007'`
Save and exit (Ctrl+X, then Y, then Enter)

Edit `009_create_consents_table.py`:
```bash
nano 009_create_consents_table.py
```
Find the line: `down_revision = '007'`
Change it to: `down_revision = '008'`
Save and exit

Edit `010_add_performance_indexes.py`:
```bash
nano 010_add_performance_indexes.py
```
Find the line: `down_revision = '008'`
Change it to: `down_revision = '009'`
Save and exit

Edit `011_create_admins_table.py`:
```bash
nano 011_create_admins_table.py
```
Find the line: `down_revision = '009'`
Change it to: `down_revision = '010'`
Save and exit

### Step 5: Verify the changes
```bash
ls -la *.py | grep -E "00[0-9]_|01[0-1]_"
```

You should see:
- 001_create_jobs_table.py
- 002_create_employers_table.py
- 003_create_applications_table.py
- 004_create_job_sources_table.py
- 005_create_scraping_tasks_table.py
- 006_create_job_seekers_table.py
- 007_add_url_imports_used_to_employers.py
- 008_create_analytics_tables.py
- 009_create_consents_table.py
- 010_add_performance_indexes.py
- 011_create_admins_table.py

### Step 6: Run migrations
```bash
cd /home/jobplatform/job-platform/backend
source venv/bin/activate
alembic upgrade head
```

## Quick sed commands (alternative to manual editing)

If you prefer using sed instead of nano:

```bash
cd /home/jobplatform/job-platform/backend/alembic/versions

# Update down_revision in each file
sed -i "s/down_revision = '006'/down_revision = '007'/" 008_create_analytics_tables.py
sed -i "s/down_revision = '007'/down_revision = '008'/" 009_create_consents_table.py
sed -i "s/down_revision = '008'/down_revision = '009'/" 010_add_performance_indexes.py
sed -i "s/down_revision = '009'/down_revision = '010'/" 011_create_admins_table.py
```

## What This Does

The migration chain will now be:
```
001 → 002 → 003 → 004 → 005 → 006 → 007 → 008 → 009 → 010 → 011
```

Instead of the broken:
```
001 → 002 → 003 → 004 → 005 → 006 → 007 (two files!) → ...
```

## If Something Goes Wrong

Restore from backup:
```bash
rm -rf /home/jobplatform/job-platform/backend/alembic/versions
mv /home/jobplatform/job-platform/backend/alembic/versions.backup /home/jobplatform/job-platform/backend/alembic/versions
```
