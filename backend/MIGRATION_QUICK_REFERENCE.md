# Database Migration Quick Reference

## 🚀 Quick Start

```bash
# 1. Setup database
psql -U postgres -c "CREATE DATABASE job_platform;"

# 2. Configure environment
cd backend
cp .env.example .env
# Edit .env with your credentials

# 3. Run migrations
python scripts/run_migrations.py

# 4. Seed test data (optional)
python scripts/seed_database.py
```

## 📋 Common Commands

### Run Migrations
```bash
# Using script (recommended)
python scripts/run_migrations.py

# Using Alembic directly
alembic upgrade head
```

### Check Status
```bash
# Current revision
alembic current

# Migration history
alembic history

# Show pending migrations
alembic heads
```

### Rollback
```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade 003_create_applications_table

# Rollback all
alembic downgrade base
```

### Verify Schema
```bash
# Connect to database
psql -U postgres -d job_platform

# List tables
\dt

# Describe table
\d jobs

# List indexes
\di

# Count records
SELECT COUNT(*) FROM jobs;
```

## 🗂️ Migration Order

1. `001_create_jobs_table` - Core jobs table
2. `002_create_employers_table` - Employer accounts
3. `003_create_applications_table` - Job applications
4. `004_create_job_sources_table` - Source tracking
5. `005_create_scraping_tasks_table` - Task history
6. `006_create_job_seekers_table` - Job seeker accounts

## 🔍 Verification Checklist

- [ ] PostgreSQL is running (`pg_isready`)
- [ ] Database exists
- [ ] `.env` file configured
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Migrations completed successfully
- [ ] All tables created (6 tables)
- [ ] All indexes created (34+ indexes)
- [ ] Foreign keys working
- [ ] Test data seeded (optional)

## 🐛 Troubleshooting

### Connection Failed
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Start PostgreSQL
sudo systemctl start postgresql
```

### Database Not Found
```bash
# Create database
psql -U postgres -c "CREATE DATABASE job_platform;"
```

### Permission Denied
```bash
# Grant permissions
psql -U postgres -d job_platform -c "GRANT ALL ON SCHEMA public TO job_user;"
```

### Enum Already Exists
```bash
# Drop and recreate database
psql -U postgres -c "DROP DATABASE job_platform;"
psql -U postgres -c "CREATE DATABASE job_platform;"
python scripts/run_migrations.py
```

## 📊 Schema Overview

| Table | Records (after seed) | Key Indexes |
|-------|---------------------|-------------|
| jobs | 5 | 11 indexes, FTS |
| employers | 3 | 5 indexes |
| applications | 3 | 6 indexes |
| job_sources | 3 | 4 indexes |
| scraping_tasks | 4 | 6 indexes |
| job_seekers | 2 | 2 indexes |

## 🔐 Test Credentials

After seeding:
- **Employer**: `employer1@techcorp.com` / `password123`
- **Job Seeker**: `john.doe@example.com` / `password123`

## 📚 Documentation

- Full guide: `docs/MIGRATION_GUIDE.md`
- Database setup: `docs/DATABASE_SETUP.md`
- Quick start: `docs/DATABASE_QUICK_START.md`
- Task completion: `TASK_2.7_COMPLETION.md`

## ⚡ Performance Notes

All tables include appropriate indexes for:
- Primary key lookups (O(log n))
- Foreign key joins (indexed)
- Full-text search (GIN indexes)
- Composite queries (multi-column indexes)
- Status filtering (indexed)

## 🎯 Next Steps

1. ✅ Run migrations
2. ✅ Verify schema
3. ✅ Seed test data
4. 🔄 Start API server
5. 🔄 Run tests
6. 🔄 Start Celery workers
