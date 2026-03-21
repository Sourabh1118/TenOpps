# Database Quick Start Guide

Quick reference for working with the database in the Job Aggregation Platform.

## Setup (First Time)

```bash
# 1. Install PostgreSQL (if not already installed)
# Ubuntu/Debian:
sudo apt install postgresql postgresql-contrib

# macOS:
brew install postgresql
brew services start postgresql

# 2. Create database and user
sudo -u postgres psql
CREATE USER jobuser WITH PASSWORD 'secretpass';
CREATE DATABASE job_aggregation OWNER jobuser;
GRANT ALL PRIVILEGES ON DATABASE job_aggregation TO jobuser;
\q

# 3. Configure environment
cp .env.example .env
# Edit .env and set:
# DATABASE_URL=postgresql://jobuser:secretpass@localhost:5432/job_aggregation

# 4. Test connection
python scripts/test_db_connection.py

# 5. Run migrations
alembic upgrade head
```

## Common Tasks

### Check Database Health
```bash
# Via script
python scripts/test_db_connection.py

# Via API
curl http://localhost:8000/health
```

### Create a Migration
```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "Add user table"

# Apply migration
alembic upgrade head
```

### Use Database in Code

#### In FastAPI Routes
```python
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db import get_db

@app.get("/items")
def get_items(db: Session = Depends(get_db)):
    items = db.query(Item).all()
    return items
```

#### In Background Tasks
```python
from app.db import get_db_session

def my_task():
    db = get_db_session()
    try:
        # Do work
        items = db.query(Item).all()
    finally:
        db.close()  # Always close!
```

#### Health Checks
```python
from app.db import check_db_health, get_db_info

# Check if database is accessible
if check_db_health():
    print("Database OK")

# Get pool metrics
info = get_db_info()
print(f"Active: {info['checked_out_connections']}")
```

## Configuration

### Environment Variables
```bash
DATABASE_URL=postgresql://user:password@host:port/database
DATABASE_POOL_SIZE=5          # Minimum connections
DATABASE_MAX_OVERFLOW=20      # Additional connections
```

### Connection Pool
- **Min connections**: 5 (always maintained)
- **Max connections**: 25 (5 + 20 overflow)
- **Pre-ping**: Enabled (verifies before use)
- **Recycle**: 3600s (1 hour)

## Troubleshooting

### Can't Connect
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection string
echo $DATABASE_URL

# Test with psql
psql postgresql://jobuser:secretpass@localhost:5432/job_aggregation
```

### Too Many Connections
```bash
# Check active connections
python -c "from app.db import get_db_info; print(get_db_info())"

# Reduce pool size in .env
DATABASE_POOL_SIZE=3
DATABASE_MAX_OVERFLOW=10
```

### Migration Issues
```bash
# Check current version
alembic current

# View history
alembic history

# Downgrade one version
alembic downgrade -1

# Upgrade to latest
alembic upgrade head
```

## Best Practices

1. ✅ **Always use `Depends(get_db)` in FastAPI routes**
2. ✅ **Always close sessions from `get_db_session()`**
3. ✅ **Use Alembic for schema changes**
4. ✅ **Monitor connection pool usage**
5. ❌ **Never create new engines**
6. ❌ **Never commit `.env` files**

## Quick Commands

```bash
# Test database
python scripts/test_db_connection.py

# Initialize database (dev only)
python scripts/init_db.py

# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Check migration status
alembic current

# View migration history
alembic history

# Health check
curl http://localhost:8000/health
```

## Need More Help?

See [DATABASE_SETUP.md](./DATABASE_SETUP.md) for detailed documentation.
