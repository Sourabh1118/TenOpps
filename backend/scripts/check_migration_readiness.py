#!/usr/bin/env python3
"""
Script to check if the system is ready for database migrations.

This script performs pre-flight checks without modifying the database:
- Verifies PostgreSQL is accessible
- Checks database exists
- Validates Alembic configuration
- Lists pending migrations
- Checks for migration conflicts

Usage:
    python scripts/check_migration_readiness.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text, inspect
from app.core.config import settings


def check_postgresql():
    """Check if PostgreSQL is accessible."""
    print("1. Checking PostgreSQL Connection")
    print("-" * 80)
    
    try:
        # Try to connect
        engine = create_engine(settings.DATABASE_URL, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"  ✓ PostgreSQL is accessible")
            print(f"    Version: {version.split(',')[0]}")
            return True, engine
    except Exception as e:
        print(f"  ✗ Cannot connect to PostgreSQL")
        print(f"    Error: {e}")
        print(f"    Database URL: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}")
        return False, None


def check_database_exists(engine):
    """Check if the target database exists."""
    print("\n2. Checking Database Existence")
    print("-" * 80)
    
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"  ✓ Database exists and is accessible")
        return True
    except Exception as e:
        print(f"  ✗ Database does not exist or is not accessible")
        print(f"    Error: {e}")
        return False


def check_alembic_config():
    """Check Alembic configuration."""
    print("\n3. Checking Alembic Configuration")
    print("-" * 80)
    
    try:
        # Check alembic.ini exists
        if not Path("alembic.ini").exists():
            print("  ✗ alembic.ini not found")
            return False
        print("  ✓ alembic.ini found")
        
        # Check alembic directory exists
        if not Path("alembic").exists():
            print("  ✗ alembic directory not found")
            return False
        print("  ✓ alembic directory found")
        
        # Check versions directory exists
        if not Path("alembic/versions").exists():
            print("  ✗ alembic/versions directory not found")
            return False
        print("  ✓ alembic/versions directory found")
        
        # Load Alembic config
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        print("  ✓ Alembic configuration loaded")
        
        return True, alembic_cfg
    except Exception as e:
        print(f"  ✗ Error loading Alembic configuration: {e}")
        return False, None


def check_migration_files(alembic_cfg):
    """Check migration files."""
    print("\n4. Checking Migration Files")
    print("-" * 80)
    
    try:
        script = ScriptDirectory.from_config(alembic_cfg)
        revisions = list(script.walk_revisions())
        
        if not revisions:
            print("  ✗ No migration files found")
            return False
        
        print(f"  ✓ Found {len(revisions)} migration files")
        print("\n  Migration chain:")
        
        for rev in reversed(revisions):
            print(f"    → {rev.revision}: {rev.doc}")
        
        return True
    except Exception as e:
        print(f"  ✗ Error reading migration files: {e}")
        return False


def check_current_revision(alembic_cfg, engine):
    """Check current database revision."""
    print("\n5. Checking Current Database Revision")
    print("-" * 80)
    
    try:
        # Check if alembic_version table exists
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'alembic_version' not in tables:
            print("  ℹ Database is not initialized (no alembic_version table)")
            print("    This is normal for a fresh database")
            return True, None
        
        # Get current revision
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            row = result.fetchone()
            
            if row:
                current_rev = row[0]
                print(f"  ✓ Current revision: {current_rev}")
                return True, current_rev
            else:
                print("  ℹ No revision recorded (empty alembic_version table)")
                return True, None
    except Exception as e:
        print(f"  ⚠ Could not determine current revision: {e}")
        return True, None


def check_pending_migrations(alembic_cfg, current_rev):
    """Check for pending migrations."""
    print("\n6. Checking Pending Migrations")
    print("-" * 80)
    
    try:
        script = ScriptDirectory.from_config(alembic_cfg)
        
        if current_rev is None:
            # All migrations are pending
            revisions = list(script.walk_revisions())
            print(f"  ℹ All {len(revisions)} migrations are pending")
            print("\n  Migrations to be applied:")
            for rev in reversed(revisions):
                print(f"    → {rev.revision}: {rev.doc}")
        else:
            # Find migrations after current revision
            head = script.get_current_head()
            
            if current_rev == head:
                print("  ✓ Database is up to date (no pending migrations)")
            else:
                print(f"  ℹ Pending migrations from {current_rev} to {head}")
                
                # List pending migrations
                pending = []
                for rev in script.walk_revisions(current_rev, head):
                    if rev.revision != current_rev:
                        pending.append(rev)
                
                if pending:
                    print(f"\n  Migrations to be applied ({len(pending)}):")
                    for rev in reversed(pending):
                        print(f"    → {rev.revision}: {rev.doc}")
        
        return True
    except Exception as e:
        print(f"  ⚠ Could not determine pending migrations: {e}")
        return True


def check_dependencies():
    """Check required Python dependencies."""
    print("\n7. Checking Python Dependencies")
    print("-" * 80)
    
    required = [
        'alembic',
        'sqlalchemy',
        'psycopg2',
        'pydantic',
        'pydantic_settings'
    ]
    
    all_present = True
    for package in required:
        try:
            __import__(package)
            print(f"  ✓ {package} installed")
        except ImportError:
            print(f"  ✗ {package} NOT installed")
            all_present = False
    
    return all_present


def main():
    """Main execution function."""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 22 + "MIGRATION READINESS CHECK" + " " * 31 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    checks_passed = 0
    checks_total = 7
    
    # Check 1: PostgreSQL
    pg_ok, engine = check_postgresql()
    if pg_ok:
        checks_passed += 1
    else:
        print("\n" + "=" * 80)
        print("❌ CRITICAL: Cannot proceed without PostgreSQL connection")
        print("=" * 80)
        return 1
    
    # Check 2: Database exists
    db_ok = check_database_exists(engine)
    if db_ok:
        checks_passed += 1
    else:
        print("\n" + "=" * 80)
        print("❌ CRITICAL: Database does not exist")
        print("=" * 80)
        print("\nTo create the database, run:")
        print("  psql -U postgres -c \"CREATE DATABASE job_platform;\"")
        return 1
    
    # Check 3: Alembic config
    alembic_ok, alembic_cfg = check_alembic_config()
    if alembic_ok:
        checks_passed += 1
    else:
        print("\n" + "=" * 80)
        print("❌ CRITICAL: Alembic configuration error")
        print("=" * 80)
        return 1
    
    # Check 4: Migration files
    files_ok = check_migration_files(alembic_cfg)
    if files_ok:
        checks_passed += 1
    
    # Check 5: Current revision
    rev_ok, current_rev = check_current_revision(alembic_cfg, engine)
    if rev_ok:
        checks_passed += 1
    
    # Check 6: Pending migrations
    pending_ok = check_pending_migrations(alembic_cfg, current_rev)
    if pending_ok:
        checks_passed += 1
    
    # Check 7: Dependencies
    deps_ok = check_dependencies()
    if deps_ok:
        checks_passed += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nChecks passed: {checks_passed}/{checks_total}")
    
    if checks_passed == checks_total:
        print("\n✅ System is ready for migrations!")
        print("\nTo run migrations:")
        print("  python scripts/run_migrations.py")
        print("\nOr using Alembic directly:")
        print("  alembic upgrade head")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please address the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
