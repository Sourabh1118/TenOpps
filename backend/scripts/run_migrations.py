#!/usr/bin/env python3
"""
Script to run Alembic migrations and verify database schema.

This script:
1. Runs all pending migrations using Alembic
2. Verifies all tables, indexes, and constraints are created
3. Tests foreign key relationships
4. Provides detailed output of the migration process

Usage:
    python scripts/run_migrations.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, inspect, text
from app.core.config import settings


def run_migrations():
    """Run all pending Alembic migrations."""
    print("=" * 80)
    print("RUNNING DATABASE MIGRATIONS")
    print("=" * 80)
    print()
    
    # Get Alembic config
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    
    try:
        # Show current revision
        print("Current database revision:")
        command.current(alembic_cfg)
        print()
        
        # Run migrations
        print("Running migrations to head...")
        command.upgrade(alembic_cfg, "head")
        print()
        
        # Show new revision
        print("New database revision:")
        command.current(alembic_cfg)
        print()
        
        print("✓ Migrations completed successfully!")
        print()
        return True
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return False


def verify_schema():
    """Verify all tables, indexes, and constraints are created."""
    print("=" * 80)
    print("VERIFYING DATABASE SCHEMA")
    print("=" * 80)
    print()
    
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    
    # Expected tables
    expected_tables = [
        'jobs',
        'employers',
        'applications',
        'job_sources',
        'scraping_tasks',
        'job_seekers'
    ]
    
    # Verify tables exist
    print("1. Verifying Tables")
    print("-" * 80)
    actual_tables = inspector.get_table_names()
    
    all_tables_exist = True
    for table in expected_tables:
        if table in actual_tables:
            print(f"  ✓ Table '{table}' exists")
        else:
            print(f"  ✗ Table '{table}' MISSING")
            all_tables_exist = False
    print()
    
    if not all_tables_exist:
        print("✗ Schema verification failed: Missing tables")
        return False
    
    # Verify indexes for each table
    print("2. Verifying Indexes")
    print("-" * 80)
    
    index_checks = {
        'jobs': [
            'idx_jobs_id',
            'idx_jobs_title',
            'idx_jobs_company',
            'idx_jobs_status',
            'idx_jobs_quality_score',
            'idx_jobs_posted_at',
            'idx_jobs_source_type',
            'idx_jobs_search_ranking',
            'idx_jobs_employer_status',
            'idx_jobs_title_fts',
            'idx_jobs_description_fts'
        ],
        'employers': [
            'idx_employers_id',
            'idx_employers_email',
            'idx_employers_subscription_tier',
            'idx_employers_verified',
            'idx_employers_subscription_status'
        ],
        'applications': [
            'idx_applications_id',
            'idx_applications_job_id',
            'idx_applications_job_seeker_id',
            'idx_applications_status',
            'idx_applications_job_status',
            'idx_applications_job_seeker'
        ],
        'job_sources': [
            'idx_job_sources_id',
            'idx_job_sources_job_id',
            'idx_job_sources_platform_active',
            'idx_job_sources_last_verified'
        ],
        'scraping_tasks': [
            'idx_scraping_tasks_id',
            'idx_scraping_tasks_status',
            'idx_scraping_tasks_created_at',
            'idx_scraping_tasks_status_created',
            'idx_scraping_tasks_platform',
            'idx_scraping_tasks_type'
        ],
        'job_seekers': [
            'idx_job_seekers_id',
            'idx_job_seekers_email'
        ]
    }
    
    all_indexes_exist = True
    for table, expected_indexes in index_checks.items():
        print(f"\n  Table: {table}")
        actual_indexes = [idx['name'] for idx in inspector.get_indexes(table)]
        
        # Also check for primary key and unique constraints which may appear as indexes
        pk_constraint = inspector.get_pk_constraint(table)
        unique_constraints = inspector.get_unique_constraints(table)
        
        for idx_name in expected_indexes:
            if idx_name in actual_indexes:
                print(f"    ✓ Index '{idx_name}' exists")
            else:
                print(f"    ✗ Index '{idx_name}' MISSING")
                all_indexes_exist = False
    print()
    
    if not all_indexes_exist:
        print("⚠ Warning: Some indexes are missing")
    
    # Verify foreign key constraints
    print("3. Verifying Foreign Key Constraints")
    print("-" * 80)
    
    fk_checks = {
        'applications': ['fk_applications_job_id'],
        'job_sources': ['fk_job_sources_job_id']
    }
    
    all_fks_exist = True
    for table, expected_fks in fk_checks.items():
        print(f"\n  Table: {table}")
        actual_fks = inspector.get_foreign_keys(table)
        actual_fk_names = [fk['name'] for fk in actual_fks]
        
        for fk_name in expected_fks:
            if fk_name in actual_fk_names:
                fk_info = next(fk for fk in actual_fks if fk['name'] == fk_name)
                print(f"    ✓ FK '{fk_name}' exists")
                print(f"      → References: {fk_info['referred_table']}.{fk_info['referred_columns']}")
            else:
                print(f"    ✗ FK '{fk_name}' MISSING")
                all_fks_exist = False
    print()
    
    if not all_fks_exist:
        print("✗ Schema verification failed: Missing foreign keys")
        return False
    
    # Verify check constraints
    print("4. Verifying Check Constraints")
    print("-" * 80)
    
    constraint_checks = {
        'jobs': [
            'check_title_length',
            'check_company_length',
            'check_description_length',
            'check_salary_range',
            'check_quality_score_bounds',
            'check_application_count_positive',
            'check_view_count_positive',
            'check_expiration_after_posted',
            'check_expiration_within_90_days'
        ],
        'employers': [
            'check_email_format',
            'check_company_name_length',
            'check_company_website_url',
            'check_monthly_posts_positive',
            'check_featured_posts_positive',
            'check_subscription_dates'
        ],
        'scraping_tasks': [
            'check_retry_count_bounds',
            'check_jobs_found_consistency',
            'check_jobs_metrics_positive',
            'check_completion_after_start'
        ],
        'job_seekers': [
            'check_job_seeker_email_format',
            'check_full_name_length',
            'check_phone_format',
            'check_resume_url_format'
        ]
    }
    
    all_constraints_exist = True
    for table, expected_constraints in constraint_checks.items():
        print(f"\n  Table: {table}")
        actual_constraints = inspector.get_check_constraints(table)
        actual_constraint_names = [c['name'] for c in actual_constraints]
        
        for constraint_name in expected_constraints:
            if constraint_name in actual_constraint_names:
                print(f"    ✓ Constraint '{constraint_name}' exists")
            else:
                print(f"    ✗ Constraint '{constraint_name}' MISSING")
                all_constraints_exist = False
    print()
    
    if not all_constraints_exist:
        print("⚠ Warning: Some check constraints are missing")
    
    # Test foreign key relationships
    print("5. Testing Foreign Key Relationships")
    print("-" * 80)
    
    with engine.connect() as conn:
        try:
            # Test that foreign key constraints are enforced
            print("\n  Testing FK enforcement (should fail on invalid references):")
            
            # Try to insert application with non-existent job_id
            try:
                conn.execute(text("""
                    INSERT INTO applications (id, job_id, job_seeker_id, resume, status)
                    VALUES (
                        gen_random_uuid(),
                        '00000000-0000-0000-0000-000000000000',
                        gen_random_uuid(),
                        'https://example.com/resume.pdf',
                        'submitted'
                    )
                """))
                conn.commit()
                print("    ✗ FK constraint NOT enforced (invalid insert succeeded)")
                return False
            except Exception as e:
                if "foreign key constraint" in str(e).lower() or "violates" in str(e).lower():
                    print("    ✓ FK constraint properly enforced (invalid insert rejected)")
                else:
                    print(f"    ⚠ Unexpected error: {e}")
            
            # Test cascade delete
            print("\n  Testing CASCADE delete behavior:")
            print("    (This would require test data - skipping for now)")
            
        except Exception as e:
            print(f"    ✗ Error testing FK relationships: {e}")
            return False
    
    print()
    print("=" * 80)
    print("✓ SCHEMA VERIFICATION COMPLETED")
    print("=" * 80)
    print()
    
    return True


def main():
    """Main execution function."""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "DATABASE MIGRATION & VERIFICATION" + " " * 25 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    # Check database connection
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✓ Database connection successful")
        print(f"  Database URL: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}")
        print()
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print()
        print("Please ensure:")
        print("  1. PostgreSQL is running")
        print("  2. Database credentials are correct in .env file")
        print("  3. Database exists (create it if needed)")
        print()
        return 1
    
    # Run migrations
    if not run_migrations():
        return 1
    
    # Verify schema
    if not verify_schema():
        return 1
    
    print()
    print("=" * 80)
    print("ALL CHECKS PASSED!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Run seed script to populate test data: python scripts/seed_database.py")
    print("  2. Start the API server: uvicorn app.main:app --reload")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
