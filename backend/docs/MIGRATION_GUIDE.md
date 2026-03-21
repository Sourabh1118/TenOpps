# Database Migration Guide

## Overview

This guide covers running Alembic migrations for the Job Aggregation Platform database schema. The platform uses 6 migrations to create all necessary tables, indexes, and constraints.

## Prerequisites

1. **PostgreSQL Database**: Ensure PostgreSQL is installed and running
2. **Database Created**: Create the database if it doesn't exist
3. **Environment Variables**: Configure `.env` file with database credentials
4. **Dependencies Installed**: Run `pip install -r requirements.txt`

## Migration Files

The following migrations are included (in order):

1. **001_create_jobs_table.py** - Core jobs table with full-text search indexes
2. **002_create_employers_table.py** - Employer accounts and subscription management
3. **003_create_applications_table.py** - Job applications with foreign keys to jobs
4. **004_create_job_sources_table.py** - Job source tracking for aggregated jobs
5. **005_create_scraping_tasks_table.py** - Scraping task history and metrics
6. **006_create_job_seekers_table.py** - Job seeker accounts and profiles

## Quick Start

### Option 1: Using the Migration Script (Recommended)

```bash
cd backend
python scripts/run_migrations.py
```

This script will:
- Run all pending migrations
- Verify all tables, indexes, and constraints
- Test foreign key relationships
- Provide detailed output

### Option 2: Using Alembic Directly

```bash
cd backend
alembic upgrade head
```

## Step-by-Step Instructions

### 1. Setup Database

Create the PostgreSQL database:

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE job_platform;

# Create user (if needed)
CREATE USER job_user WITH PASSWORD 'your_password';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE job_platform TO job_user;

# Exit
\q
```

### 2. Configure Environment

Create `.env` file from example:

```bash
cp .env.example .env
```

Edit `.env` and update database credentials:

```env
DATABASE_URL=postgresql://job_user:your_password@localhost:5432/job_platform
```

### 3. Run Migrations

Execute the migration script:

```bash
python scripts/run_migrations.py
```

Expected output:
```
================================================================================
RUNNING DATABASE MIGRATIONS
================================================================================

Current database revision:

Running migrations to head...
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001_create_jobs_table
INFO  [alembic.runtime.migration] Running upgrade 001_create_jobs_table -> 002_create_employers_table
INFO  [alembic.runtime.migration] Running upgrade 002_create_employers_table -> 003_create_applications_table
INFO  [alembic.runtime.migration] Running upgrade 003_create_applications_table -> 004_create_job_sources_table
INFO  [alembic.runtime.migration] Running upgrade 004_create_job_sources_table -> 005_create_scraping_tasks_table
INFO  [alembic.runtime.migration] Running upgrade 005_create_scraping_tasks_table -> 006_create_job_seekers_table

✓ Migrations completed successfully!
```

### 4. Verify Schema

The script automatically verifies:
- All tables exist
- All indexes are created
- All foreign key constraints are in place
- All check constraints are enforced

### 5. Seed Test Data (Optional)

Populate the database with test data:

```bash
python scripts/seed_database.py
```

This creates:
- 3 employers (free, basic, premium tiers)
- 2 job seekers
- 5 jobs (direct posts, URL imports, aggregated)
- 3 applications
- Job sources for aggregated jobs
- Sample scraping tasks

## Schema Details

### Tables Created

| Table | Description | Key Indexes |
|-------|-------------|-------------|
| `jobs` | Core job postings | Full-text search on title/description, quality score, status |
| `employers` | Employer accounts | Email (unique), subscription tier |
| `applications` | Job applications | Job ID, job seeker ID, status |
| `job_sources` | Source tracking | Job ID, platform, last verified |
| `scraping_tasks` | Task history | Status, created_at, platform |
| `job_seekers` | Job seeker accounts | Email (unique) |

### Key Indexes (Requirement 16.2)

All tables include appropriate indexes for efficient querying:

**Jobs Table:**
- `idx_jobs_search_ranking` - Composite index for search results (status, quality_score, posted_at)
- `idx_jobs_title_fts` - Full-text search on job titles
- `idx_jobs_description_fts` - Full-text search on descriptions
- Individual indexes on: id, title, company, status, quality_score, posted_at, source_type

**Employers Table:**
- `idx_employers_subscription_status` - Composite index for subscription queries
- Individual indexes on: id, email (unique), subscription_tier, verified

**Applications Table:**
- `idx_applications_job_status` - Composite index for employer queries
- Individual indexes on: id, job_id, job_seeker_id, status

**Job Sources Table:**
- `idx_job_sources_platform_active` - Composite index for platform queries
- Individual indexes on: id, job_id, last_verified_at

**Scraping Tasks Table:**
- `idx_scraping_tasks_status_created` - Composite index for monitoring
- Individual indexes on: id, status, created_at, platform, task_type

**Job Seekers Table:**
- Individual indexes on: id, email (unique)

### Foreign Key Relationships

- `applications.job_id` → `jobs.id` (CASCADE delete)
- `job_sources.job_id` → `jobs.id` (CASCADE delete)

### Check Constraints

All tables include validation constraints:
- Email format validation
- Length constraints on text fields
- Salary range validation (min < max)
- Quality score bounds (0-100)
- Date logic (expiration after posting, within 90 days)
- Positive counters (application_count, view_count, etc.)

## Troubleshooting

### Connection Refused

**Problem:** Cannot connect to PostgreSQL

**Solution:**
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start PostgreSQL if needed
sudo systemctl start postgresql
```

### Database Does Not Exist

**Problem:** `FATAL: database "job_platform" does not exist`

**Solution:**
```bash
psql -U postgres -c "CREATE DATABASE job_platform;"
```

### Permission Denied

**Problem:** `permission denied for schema public`

**Solution:**
```bash
psql -U postgres -d job_platform -c "GRANT ALL ON SCHEMA public TO job_user;"
```

### Migration Already Applied

**Problem:** Alembic says migration is already applied

**Solution:**
```bash
# Check current revision
alembic current

# Downgrade if needed
alembic downgrade -1

# Or downgrade all
alembic downgrade base
```

### Enum Type Already Exists

**Problem:** `type "jobtype" already exists`

**Solution:**
```bash
# Drop and recreate database
psql -U postgres -c "DROP DATABASE job_platform;"
psql -U postgres -c "CREATE DATABASE job_platform;"

# Run migrations again
python scripts/run_migrations.py
```

## Rollback Instructions

### Rollback One Migration

```bash
alembic downgrade -1
```

### Rollback to Specific Revision

```bash
# List all revisions
alembic history

# Downgrade to specific revision
alembic downgrade 005_create_scraping_tasks_table
```

### Rollback All Migrations

```bash
alembic downgrade base
```

## Manual Verification

If you want to manually verify the schema:

```bash
# Connect to database
psql -U job_user -d job_platform

# List all tables
\dt

# Describe a table
\d jobs

# List all indexes
\di

# List all constraints
\d+ jobs
```

## Next Steps

After successful migration:

1. **Seed Test Data**: Run `python scripts/seed_database.py`
2. **Start API Server**: Run `uvicorn app.main:app --reload`
3. **Run Tests**: Run `pytest tests/`
4. **Start Celery Workers**: See `docs/CELERY_SETUP.md`

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Database Setup Guide](./DATABASE_SETUP.md)
- [Database Quick Start](./DATABASE_QUICK_START.md)
