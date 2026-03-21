# Database Setup Guide

This guide explains the PostgreSQL database setup for the Job Aggregation Platform.

## Overview

The application uses PostgreSQL as the primary database with SQLAlchemy as the ORM. The database layer includes:

- **Connection pooling** with configurable pool size (min=5, max=20 connections)
- **Session management** with FastAPI dependency injection
- **Health checks** for monitoring database connectivity
- **Alembic migrations** for schema version control

## Architecture

### Components

1. **`app/db/base.py`** - SQLAlchemy declarative base for all models
2. **`app/db/session.py`** - Database engine and session management
3. **`app/db/init_db.py`** - Database initialization and health check utilities
4. **`alembic/`** - Database migration scripts

### Connection Pooling

The database uses SQLAlchemy's `QueuePool` with the following configuration:

- **Pool Size**: 5 connections (minimum maintained connections)
- **Max Overflow**: 20 connections (additional connections when needed)
- **Pool Pre-Ping**: Enabled (verifies connections before use)
- **Pool Recycle**: 3600 seconds (recycles connections after 1 hour)

This configuration ensures efficient connection reuse while preventing connection exhaustion.

## Configuration

### Environment Variables

Configure the following in your `.env` file:

```bash
# Database connection URL
DATABASE_URL=postgresql://user:password@localhost:5432/job_platform

# Connection pool settings
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=20
```

### Connection URL Format

```
postgresql://[user]:[password]@[host]:[port]/[database]
```

Example:
```
postgresql://jobuser:secretpass@localhost:5432/job_aggregation
```

## Setup Instructions

### 1. Install PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Docker:**
```bash
docker run --name postgres \
  -e POSTGRES_USER=jobuser \
  -e POSTGRES_PASSWORD=secretpass \
  -e POSTGRES_DB=job_aggregation \
  -p 5432:5432 \
  -d postgres:15
```

### 2. Create Database and User

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create user
CREATE USER jobuser WITH PASSWORD 'secretpass';

# Create database
CREATE DATABASE job_aggregation OWNER jobuser;

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE job_aggregation TO jobuser;

# Exit
\q
```

### 3. Configure Application

Update your `.env` file with the database connection details:

```bash
DATABASE_URL=postgresql://jobuser:secretpass@localhost:5432/job_aggregation
```

### 4. Test Connection

Run the database connection test script:

```bash
python scripts/test_db_connection.py
```

This will verify:
- Database connectivity
- Connection pool configuration
- Session creation and query execution
- Multiple concurrent sessions

### 5. Run Migrations

Initialize the database schema using Alembic:

```bash
# Create initial migration (if needed)
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

## Usage

### In FastAPI Routes

Use the `get_db` dependency to inject database sessions:

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db import get_db

@app.get("/items")
def get_items(db: Session = Depends(get_db)):
    items = db.query(Item).all()
    return items
```

### In Background Tasks

Use `get_db_session` for manual session management:

```python
from app.db import get_db_session

def background_task():
    db = get_db_session()
    try:
        # Perform database operations
        items = db.query(Item).all()
        # ...
    finally:
        db.close()
```

### Health Checks

Check database health programmatically:

```python
from app.db import check_db_health, get_db_info

# Check if database is accessible
if check_db_health():
    print("Database is healthy")
    
# Get connection pool information
info = get_db_info()
print(f"Active connections: {info['checked_out_connections']}")
```

## Monitoring

### Health Check Endpoint

The application exposes a health check endpoint at `/health` that includes database status:

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-03-18T19:00:00Z",
  "database": {
    "connected": true,
    "pool_size": 5,
    "checked_in_connections": 4,
    "checked_out_connections": 1,
    "overflow": 0,
    "total_connections": 5
  }
}
```

### Connection Pool Metrics

Monitor connection pool usage:

```python
from app.db import get_db_info

info = get_db_info()
print(f"Pool size: {info['pool_size']}")
print(f"Checked in: {info['checked_in_connections']}")
print(f"Checked out: {info['checked_out_connections']}")
print(f"Overflow: {info['overflow']}")
print(f"Total: {info['total_connections']}")
```

## Migrations with Alembic

### Create a New Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add user table"

# Create empty migration
alembic revision -m "Custom migration"
```

### Apply Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific revision
alembic upgrade <revision_id>

# Downgrade one revision
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade <revision_id>
```

### View Migration History

```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic history --verbose
```

## Troubleshooting

### Connection Refused

**Problem**: `psycopg2.OperationalError: could not connect to server`

**Solutions**:
1. Verify PostgreSQL is running: `sudo systemctl status postgresql`
2. Check connection details in `.env`
3. Verify firewall allows connections on port 5432
4. Check PostgreSQL `pg_hba.conf` for authentication settings

### Too Many Connections

**Problem**: `FATAL: too many connections for role`

**Solutions**:
1. Reduce `DATABASE_POOL_SIZE` and `DATABASE_MAX_OVERFLOW`
2. Increase PostgreSQL `max_connections` in `postgresql.conf`
3. Check for connection leaks (unclosed sessions)

### Slow Queries

**Problem**: Database queries are slow

**Solutions**:
1. Add indexes to frequently queried columns
2. Use `EXPLAIN ANALYZE` to identify bottlenecks
3. Enable query logging in PostgreSQL
4. Consider connection pooling adjustments

### Migration Conflicts

**Problem**: Alembic migration conflicts

**Solutions**:
1. Check current revision: `alembic current`
2. View migration history: `alembic history`
3. Resolve conflicts manually in migration files
4. Use `alembic stamp head` to mark current state (careful!)

## Best Practices

1. **Always use sessions via dependency injection** in FastAPI routes
2. **Close sessions explicitly** when using `get_db_session()`
3. **Use connection pooling** - don't create new engines
4. **Monitor pool usage** to detect connection leaks
5. **Use Alembic migrations** for schema changes (not `create_all()`)
6. **Test database connectivity** before deploying
7. **Set appropriate pool sizes** based on workload
8. **Enable query logging** in development for debugging

## Security

1. **Never commit `.env` files** with real credentials
2. **Use strong passwords** for database users
3. **Restrict database access** to application servers only
4. **Use SSL/TLS** for database connections in production
5. **Regularly update** PostgreSQL and dependencies
6. **Backup database** regularly
7. **Use read-only users** for reporting/analytics queries

## Performance Tuning

### Connection Pool Sizing

Calculate optimal pool size:
```
pool_size = (number_of_workers * 2) + spare_connections
max_overflow = pool_size * 2
```

For example, with 4 workers:
```
pool_size = (4 * 2) + 2 = 10
max_overflow = 10 * 2 = 20
```

### PostgreSQL Configuration

Recommended settings for production:

```ini
# postgresql.conf
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
```

## References

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [FastAPI Database Guide](https://fastapi.tiangolo.com/tutorial/sql-databases/)
