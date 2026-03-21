# Task 36.1: Deploy PostgreSQL Database (Supabase)

**Requirement**: 16.8 - Database deployment with connection pooling and backups

## Overview

This guide walks through deploying PostgreSQL on Supabase's free tier, which includes:
- 500MB database storage
- 2GB bandwidth per month
- Automatic daily backups (7-day retention)
- Built-in connection pooling
- SSL connections by default
- Point-in-time recovery

## Prerequisites

- [ ] Supabase account (https://supabase.com)
- [ ] Database schema ready (Alembic migrations)
- [ ] Backend code ready to deploy

## Step-by-Step Instructions

### Step 1: Create Supabase Project

1. **Sign in to Supabase**:
   - Go to https://supabase.com
   - Click "Sign in" or "Start your project"
   - Sign in with GitHub (recommended) or email

2. **Create New Project**:
   - Click "New Project" button
   - Select your organization (or create one)

3. **Configure Project**:
   - **Name**: `job-aggregation-platform`
   - **Database Password**: Click "Generate a password" or create a strong password
     - **IMPORTANT**: Save this password securely! You'll need it for connection strings.
   - **Region**: Choose the region closest to your users:
     - `us-east-1` (US East - Virginia)
     - `us-west-1` (US West - California)
     - `eu-west-1` (Europe - Ireland)
     - `ap-southeast-1` (Asia Pacific - Singapore)
   - **Pricing Plan**: Free

4. **Create Project**:
   - Click "Create new project"
   - Wait 2-3 minutes for provisioning

### Step 2: Get Database Connection Details

1. **Navigate to Database Settings**:
   - In your project dashboard, click **Settings** (gear icon in sidebar)
   - Click **Database** in the settings menu

2. **Copy Connection Information**:
   
   You'll see several connection strings. Here's what each is for:
   
   **Direct Connection** (Port 5432):
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:5432/postgres
   ```
   - Use for: Admin tasks, migrations, direct database access
   - Connections: Limited to 60 concurrent connections
   
   **Connection Pooling** (Port 6543):
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:6543/postgres
   ```
   - Use for: Application connections (RECOMMENDED)
   - Connections: Supports thousands of concurrent connections
   - Mode: Transaction pooling (PgBouncer)

3. **Save Connection Details**:
   
   Create a secure note with:
   ```bash
   # Supabase PostgreSQL Connection Details
   
   # Project Details
   Project Name: job-aggregation-platform
   Project URL: https://xxxxxxxxxxxxx.supabase.co
   Region: us-east-1
   
   # Database Credentials
   Host: db.xxxxxxxxxxxxx.supabase.co
   Database: postgres
   User: postgres
   Password: [YOUR-PASSWORD]
   
   # Connection Strings
   # Use this for your application (connection pooling)
   DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:6543/postgres?sslmode=require
   
   # Use this for migrations and admin tasks
   DATABASE_DIRECT_URL=postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:5432/postgres?sslmode=require
   
   # Pool Configuration
   DATABASE_POOL_SIZE=5
   DATABASE_MAX_OVERFLOW=20
   ```

### Step 3: Configure Connection Pooling

Supabase uses PgBouncer for connection pooling. Configuration is automatic, but you should understand the settings:

1. **Pooling Mode**: Transaction
   - Each client connection is assigned a server connection only during a transaction
   - Most efficient for web applications
   - Automatically configured

2. **Pool Size**: 
   - Free tier: Up to 60 direct connections
   - Pooled connections: Thousands supported
   - Your app should use pooled connection (port 6543)

3. **Application Pool Settings**:
   ```bash
   DATABASE_POOL_SIZE=5        # Number of connections to maintain
   DATABASE_MAX_OVERFLOW=20    # Additional connections when needed
   ```

### Step 4: Enable and Verify Backups

1. **Check Backup Settings**:
   - Go to **Settings** → **Database**
   - Scroll to **Backup and Restore** section

2. **Verify Backup Configuration**:
   - ✅ **Daily Backups**: Enabled by default
   - ✅ **Retention**: 7 days (free tier)
   - ✅ **Point-in-Time Recovery**: Last 7 days
   - ✅ **Automatic Backups**: Runs daily at 2 AM UTC

3. **Manual Backup** (Optional):
   - Click "Create backup" to create an immediate backup
   - Useful before major migrations or changes

4. **Test Restore** (Optional but Recommended):
   - Click on a backup
   - Click "Restore" to test the restore process
   - This creates a new project with the backup data

### Step 5: Configure Database Security

1. **Enable SSL** (Already Enabled):
   - Supabase enforces SSL by default
   - Always use `?sslmode=require` in connection strings

2. **Network Access**:
   - Supabase allows connections from any IP by default
   - For additional security, you can restrict IPs in **Settings** → **Database** → **Connection Pooling**

3. **Database Roles**:
   - Default `postgres` user has full access
   - For production, consider creating limited-privilege users:
   
   ```sql
   -- Connect to Supabase SQL Editor
   
   -- Create application user with limited privileges
   CREATE USER app_user WITH PASSWORD 'secure_password';
   
   -- Grant necessary permissions
   GRANT CONNECT ON DATABASE postgres TO app_user;
   GRANT USAGE ON SCHEMA public TO app_user;
   GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
   GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
   
   -- Set default privileges for future tables
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO app_user;
   ```

### Step 6: Run Database Migrations

**Important**: Run migrations AFTER deploying your backend service. This ensures the backend can connect to the database.

#### Option A: From Local Machine

1. **Install PostgreSQL Client** (if not already installed):
   ```bash
   # macOS
   brew install postgresql
   
   # Ubuntu/Debian
   sudo apt-get install postgresql-client
   
   # Windows
   # Download from https://www.postgresql.org/download/windows/
   ```

2. **Set Environment Variable**:
   ```bash
   export DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:5432/postgres?sslmode=require"
   ```

3. **Run Migrations**:
   ```bash
   cd backend
   alembic upgrade head
   ```

4. **Verify Migrations**:
   ```bash
   alembic current
   # Should show: [latest_revision] (head)
   ```

#### Option B: From Deployed Backend (Recommended)

1. **Deploy Backend First** (see Task 36.3)

2. **Access Backend Shell**:
   - Railway: Click service → "Connect" → "Shell"
   - Render: Click service → "Shell"

3. **Run Migrations**:
   ```bash
   alembic upgrade head
   ```

4. **Verify**:
   ```bash
   alembic current
   ```

### Step 7: Verify Database Setup

1. **Connect to SQL Editor**:
   - In Supabase dashboard, click **SQL Editor** in sidebar
   - This opens an interactive SQL console

2. **Check Tables**:
   ```sql
   -- List all tables
   SELECT table_name 
   FROM information_schema.tables 
   WHERE table_schema = 'public';
   ```
   
   Expected tables:
   - `jobs`
   - `employers`
   - `applications`
   - `job_sources`
   - `scraping_tasks`
   - `job_seekers`
   - `analytics_events`
   - `analytics_metrics`
   - `consents`
   - `alembic_version`

3. **Check Indexes**:
   ```sql
   -- List all indexes
   SELECT 
       tablename,
       indexname,
       indexdef
   FROM pg_indexes
   WHERE schemaname = 'public'
   ORDER BY tablename, indexname;
   ```

4. **Test Connection from Backend**:
   ```python
   # In backend shell or Python script
   from app.db.session import SessionLocal
   from app.models.job import Job
   
   db = SessionLocal()
   try:
       # Test query
       count = db.query(Job).count()
       print(f"Database connected! Job count: {count}")
   finally:
       db.close()
   ```

### Step 8: Monitor Database Performance

1. **Database Dashboard**:
   - Go to **Database** in Supabase sidebar
   - View real-time metrics:
     - Active connections
     - Database size
     - Query performance

2. **Query Performance**:
   - Click **SQL Editor**
   - Run slow query analysis:
   ```sql
   -- Find slow queries
   SELECT 
       query,
       calls,
       total_time,
       mean_time,
       max_time
   FROM pg_stat_statements
   ORDER BY mean_time DESC
   LIMIT 10;
   ```

3. **Connection Monitoring**:
   ```sql
   -- Check active connections
   SELECT 
       count(*) as connections,
       state,
       application_name
   FROM pg_stat_activity
   GROUP BY state, application_name;
   ```

## Configuration Summary

Add these environment variables to your backend service:

```bash
# Database Connection (use pooled connection)
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:6543/postgres?sslmode=require

# For migrations (use direct connection)
DATABASE_DIRECT_URL=postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxxx.supabase.co:5432/postgres?sslmode=require

# Connection Pool Settings
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=20
```

## Testing Checklist

- [ ] Can connect to database from local machine
- [ ] Can connect to database from deployed backend
- [ ] All migrations applied successfully
- [ ] All tables created with correct schema
- [ ] Indexes created for performance
- [ ] Backups are enabled and running
- [ ] SSL connection enforced
- [ ] Connection pooling working
- [ ] Can query data successfully

## Troubleshooting

### Connection Refused

**Problem**: Cannot connect to database

**Solutions**:
1. Verify password is correct
2. Check connection string format
3. Ensure `?sslmode=require` is included
4. Verify project is not paused (free tier pauses after inactivity)

### Too Many Connections

**Problem**: "Too many connections" error

**Solutions**:
1. Use pooled connection (port 6543) instead of direct (port 5432)
2. Reduce `DATABASE_POOL_SIZE` and `DATABASE_MAX_OVERFLOW`
3. Check for connection leaks in application code
4. Ensure connections are properly closed

### Migration Fails

**Problem**: Alembic migration fails

**Solutions**:
1. Check migration file for syntax errors
2. Verify database user has necessary permissions
3. Check for conflicting table/column names
4. Review migration logs for specific error
5. Try running migration with `--sql` flag to see generated SQL

### Slow Queries

**Problem**: Database queries are slow

**Solutions**:
1. Check if indexes are created (run verification script)
2. Analyze query execution plans:
   ```sql
   EXPLAIN ANALYZE SELECT * FROM jobs WHERE ...;
   ```
3. Add missing indexes
4. Optimize query structure
5. Consider upgrading to paid tier for more resources

## Free Tier Limits

Be aware of Supabase free tier limits:

- **Storage**: 500MB database size
- **Bandwidth**: 2GB per month
- **Connections**: 60 direct, thousands pooled
- **Backups**: 7-day retention
- **Pausing**: Projects pause after 1 week of inactivity

**Monitoring Usage**:
- Go to **Settings** → **Billing**
- View current usage and limits
- Set up alerts for approaching limits

## Next Steps

After completing database deployment:

1. ✅ Database deployed and configured
2. ➡️ **Next**: Deploy Redis (Task 36.2)
3. ➡️ Deploy Backend (Task 36.3) - will use this database
4. ➡️ Run migrations from deployed backend

## Support Resources

- **Supabase Documentation**: https://supabase.com/docs/guides/database
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/
- **Supabase Community**: https://github.com/supabase/supabase/discussions
- **Status Page**: https://status.supabase.com

---

**Task 36.1 Complete!** ✅

Your PostgreSQL database is now deployed and ready for use.
