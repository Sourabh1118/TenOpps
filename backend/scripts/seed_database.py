#!/usr/bin/env python3
"""
Script to seed the database with test data for development.

This script creates:
- Sample employers with different subscription tiers
- Sample job seekers
- Sample jobs (direct posts, URL imports, aggregated)
- Sample applications
- Sample job sources
- Sample scraping tasks

Usage:
    python scripts/seed_database.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings


def seed_employers(conn):
    """Seed sample employers with different subscription tiers."""
    print("Seeding employers...")
    
    employers = [
        {
            'id': uuid4(),
            'email': 'employer1@techcorp.com',
            'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MRfg3u',  # "password123"
            'company_name': 'TechCorp Inc',
            'company_website': 'https://techcorp.example.com',
            'company_description': 'Leading technology company specializing in AI and cloud solutions',
            'subscription_tier': 'premium',
            'subscription_end_date': datetime.now() + timedelta(days=365),
            'monthly_posts_used': 5,
            'featured_posts_used': 2,
            'verified': True
        },
        {
            'id': uuid4(),
            'email': 'hr@startupxyz.com',
            'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MRfg3u',
            'company_name': 'StartupXYZ',
            'company_website': 'https://startupxyz.example.com',
            'company_description': 'Fast-growing startup in fintech space',
            'subscription_tier': 'basic',
            'subscription_end_date': datetime.now() + timedelta(days=30),
            'monthly_posts_used': 3,
            'featured_posts_used': 1,
            'verified': True
        },
        {
            'id': uuid4(),
            'email': 'jobs@smallbiz.com',
            'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MRfg3u',
            'company_name': 'Small Business Co',
            'company_website': None,
            'company_description': 'Local business looking for talent',
            'subscription_tier': 'free',
            'subscription_end_date': datetime.now() + timedelta(days=30),
            'monthly_posts_used': 1,
            'featured_posts_used': 0,
            'verified': False
        }
    ]
    
    for employer in employers:
        conn.execute(text("""
            INSERT INTO employers (
                id, email, password_hash, company_name, company_website,
                company_description, subscription_tier, subscription_end_date,
                monthly_posts_used, featured_posts_used, verified
            ) VALUES (
                :id, :email, :password_hash, :company_name, :company_website,
                :company_description, :subscription_tier::subscriptiontier, :subscription_end_date,
                :monthly_posts_used, :featured_posts_used, :verified
            )
        """), employer)
    
    conn.commit()
    print(f"  ✓ Created {len(employers)} employers")
    return employers


def seed_job_seekers(conn):
    """Seed sample job seekers."""
    print("Seeding job seekers...")
    
    job_seekers = [
        {
            'id': uuid4(),
            'email': 'john.doe@example.com',
            'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MRfg3u',
            'full_name': 'John Doe',
            'phone': '+1-555-0101',
            'resume_url': 'https://example.com/resumes/john-doe.pdf',
            'profile_summary': 'Experienced software engineer with 5 years in full-stack development'
        },
        {
            'id': uuid4(),
            'email': 'jane.smith@example.com',
            'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MRfg3u',
            'full_name': 'Jane Smith',
            'phone': '+1-555-0102',
            'resume_url': 'https://example.com/resumes/jane-smith.pdf',
            'profile_summary': 'Data scientist specializing in machine learning and AI'
        }
    ]
    
    for seeker in job_seekers:
        conn.execute(text("""
            INSERT INTO job_seekers (
                id, email, password_hash, full_name, phone, resume_url, profile_summary
            ) VALUES (
                :id, :email, :password_hash, :full_name, :phone, :resume_url, :profile_summary
            )
        """), seeker)
    
    conn.commit()
    print(f"  ✓ Created {len(job_seekers)} job seekers")
    return job_seekers


def seed_jobs(conn, employers):
    """Seed sample jobs with different source types."""
    print("Seeding jobs...")
    
    jobs = [
        # Direct posts
        {
            'id': uuid4(),
            'title': 'Senior Full Stack Developer',
            'company': employers[0]['company_name'],
            'location': 'San Francisco, CA',
            'remote': True,
            'job_type': 'full_time',
            'experience_level': 'senior',
            'description': 'We are looking for an experienced full-stack developer to join our team. You will work on cutting-edge projects using React, Node.js, and cloud technologies.',
            'requirements': ['5+ years experience', 'React expertise', 'Node.js proficiency', 'AWS knowledge'],
            'responsibilities': ['Build scalable web applications', 'Mentor junior developers', 'Code reviews'],
            'salary_min': 120000,
            'salary_max': 180000,
            'salary_currency': 'USD',
            'source_type': 'direct',
            'employer_id': employers[0]['id'],
            'quality_score': 85.0,
            'status': 'active',
            'posted_at': datetime.now() - timedelta(days=2),
            'expires_at': datetime.now() + timedelta(days=28),
            'featured': True,
            'tags': ['react', 'nodejs', 'aws', 'fullstack']
        },
        {
            'id': uuid4(),
            'title': 'Product Manager - Fintech',
            'company': employers[1]['company_name'],
            'location': 'New York, NY',
            'remote': False,
            'job_type': 'full_time',
            'experience_level': 'mid',
            'description': 'Join our fintech startup as a Product Manager. You will define product strategy and work closely with engineering and design teams.',
            'requirements': ['3+ years PM experience', 'Fintech background', 'Agile methodology'],
            'responsibilities': ['Define product roadmap', 'Stakeholder management', 'Feature prioritization'],
            'salary_min': 90000,
            'salary_max': 130000,
            'salary_currency': 'USD',
            'source_type': 'direct',
            'employer_id': employers[1]['id'],
            'quality_score': 78.0,
            'status': 'active',
            'posted_at': datetime.now() - timedelta(days=5),
            'expires_at': datetime.now() + timedelta(days=25),
            'featured': False,
            'tags': ['product', 'fintech', 'agile']
        },
        # URL import
        {
            'id': uuid4(),
            'title': 'Data Scientist - Machine Learning',
            'company': 'AI Research Labs',
            'location': 'Boston, MA',
            'remote': True,
            'job_type': 'full_time',
            'experience_level': 'senior',
            'description': 'Work on cutting-edge ML research and applications. PhD preferred but not required for exceptional candidates.',
            'requirements': ['MS/PhD in CS or related field', 'Deep learning expertise', 'Python proficiency'],
            'responsibilities': ['Research and develop ML models', 'Publish research papers', 'Collaborate with team'],
            'salary_min': 140000,
            'salary_max': 200000,
            'salary_currency': 'USD',
            'source_type': 'url_import',
            'source_url': 'https://linkedin.com/jobs/view/12345',
            'source_platform': 'LinkedIn',
            'employer_id': employers[0]['id'],
            'quality_score': 72.0,
            'status': 'active',
            'posted_at': datetime.now() - timedelta(days=7),
            'expires_at': datetime.now() + timedelta(days=23),
            'featured': False,
            'tags': ['ml', 'ai', 'python', 'research']
        },
        # Aggregated jobs
        {
            'id': uuid4(),
            'title': 'Frontend Developer - React',
            'company': 'WebDev Solutions',
            'location': 'Austin, TX',
            'remote': True,
            'job_type': 'contract',
            'experience_level': 'mid',
            'description': 'Contract position for experienced React developer. 6-month contract with possibility of extension.',
            'requirements': ['3+ years React', 'TypeScript', 'Modern CSS'],
            'responsibilities': ['Build UI components', 'Optimize performance', 'Write tests'],
            'salary_min': None,
            'salary_max': None,
            'salary_currency': 'USD',
            'source_type': 'aggregated',
            'source_url': 'https://indeed.com/viewjob?jk=abc123',
            'source_platform': 'Indeed',
            'quality_score': 55.0,
            'status': 'active',
            'posted_at': datetime.now() - timedelta(days=10),
            'expires_at': datetime.now() + timedelta(days=20),
            'featured': False,
            'tags': ['react', 'frontend', 'typescript']
        },
        {
            'id': uuid4(),
            'title': 'DevOps Engineer',
            'company': 'Cloud Infrastructure Inc',
            'location': 'Seattle, WA',
            'remote': True,
            'job_type': 'full_time',
            'experience_level': 'senior',
            'description': 'Looking for DevOps engineer to manage our cloud infrastructure and CI/CD pipelines.',
            'requirements': ['Kubernetes experience', 'AWS/GCP', 'Terraform', 'CI/CD tools'],
            'responsibilities': ['Manage infrastructure', 'Automate deployments', 'Monitor systems'],
            'salary_min': 110000,
            'salary_max': 160000,
            'salary_currency': 'USD',
            'source_type': 'aggregated',
            'source_url': 'https://monster.com/job/xyz789',
            'source_platform': 'Monster',
            'quality_score': 48.0,
            'status': 'active',
            'posted_at': datetime.now() - timedelta(days=15),
            'expires_at': datetime.now() + timedelta(days=15),
            'featured': False,
            'tags': ['devops', 'kubernetes', 'aws', 'terraform']
        }
    ]
    
    for job in jobs:
        conn.execute(text("""
            INSERT INTO jobs (
                id, title, company, location, remote, job_type, experience_level,
                description, requirements, responsibilities, salary_min, salary_max,
                salary_currency, source_type, source_url, source_platform, employer_id,
                quality_score, status, posted_at, expires_at, featured, tags
            ) VALUES (
                :id, :title, :company, :location, :remote, :job_type::jobtype,
                :experience_level::experiencelevel, :description, :requirements,
                :responsibilities, :salary_min, :salary_max, :salary_currency,
                :source_type::sourcetype, :source_url, :source_platform, :employer_id,
                :quality_score, :status::jobstatus, :posted_at, :expires_at, :featured, :tags
            )
        """), job)
    
    conn.commit()
    print(f"  ✓ Created {len(jobs)} jobs")
    return jobs


def seed_applications(conn, jobs, job_seekers):
    """Seed sample applications."""
    print("Seeding applications...")
    
    # Only create applications for direct posts
    direct_jobs = [j for j in jobs if j['source_type'] == 'direct']
    
    applications = [
        {
            'id': uuid4(),
            'job_id': direct_jobs[0]['id'],
            'job_seeker_id': job_seekers[0]['id'],
            'resume': 'https://example.com/resumes/john-doe.pdf',
            'cover_letter': 'I am very interested in this position and believe my skills align well with your requirements.',
            'status': 'reviewed',
            'applied_at': datetime.now() - timedelta(days=1)
        },
        {
            'id': uuid4(),
            'job_id': direct_jobs[0]['id'],
            'job_seeker_id': job_seekers[1]['id'],
            'resume': 'https://example.com/resumes/jane-smith.pdf',
            'cover_letter': None,
            'status': 'submitted',
            'applied_at': datetime.now() - timedelta(hours=12)
        },
        {
            'id': uuid4(),
            'job_id': direct_jobs[1]['id'],
            'job_seeker_id': job_seekers[0]['id'],
            'resume': 'https://example.com/resumes/john-doe.pdf',
            'cover_letter': 'My experience in product management makes me a great fit for this role.',
            'status': 'shortlisted',
            'applied_at': datetime.now() - timedelta(days=3)
        }
    ]
    
    for app in applications:
        conn.execute(text("""
            INSERT INTO applications (
                id, job_id, job_seeker_id, resume, cover_letter, status, applied_at
            ) VALUES (
                :id, :job_id, :job_seeker_id, :resume, :cover_letter,
                :status::applicationstatus, :applied_at
            )
        """), app)
    
    # Update application counts on jobs
    for job in direct_jobs:
        app_count = sum(1 for app in applications if app['job_id'] == job['id'])
        conn.execute(text("""
            UPDATE jobs SET application_count = :count WHERE id = :job_id
        """), {'count': app_count, 'job_id': job['id']})
    
    conn.commit()
    print(f"  ✓ Created {len(applications)} applications")
    return applications


def seed_job_sources(conn, jobs):
    """Seed job sources for aggregated and URL import jobs."""
    print("Seeding job sources...")
    
    sources = []
    for job in jobs:
        if job['source_type'] in ['aggregated', 'url_import']:
            source = {
                'id': uuid4(),
                'job_id': job['id'],
                'source_platform': job['source_platform'],
                'source_url': job['source_url'],
                'source_job_id': f"ext_{uuid4().hex[:8]}",
                'scraped_at': job['posted_at'],
                'last_verified_at': datetime.now() - timedelta(days=1),
                'is_active': True
            }
            sources.append(source)
            
            conn.execute(text("""
                INSERT INTO job_sources (
                    id, job_id, source_platform, source_url, source_job_id,
                    scraped_at, last_verified_at, is_active
                ) VALUES (
                    :id, :job_id, :source_platform, :source_url, :source_job_id,
                    :scraped_at, :last_verified_at, :is_active
                )
            """), source)
    
    conn.commit()
    print(f"  ✓ Created {len(sources)} job sources")
    return sources


def seed_scraping_tasks(conn):
    """Seed sample scraping tasks."""
    print("Seeding scraping tasks...")
    
    tasks = [
        {
            'id': uuid4(),
            'task_type': 'scheduled_scrape',
            'source_platform': 'Indeed',
            'status': 'completed',
            'started_at': datetime.now() - timedelta(hours=2),
            'completed_at': datetime.now() - timedelta(hours=2) + timedelta(minutes=15),
            'jobs_found': 25,
            'jobs_created': 3,
            'jobs_updated': 22,
            'retry_count': 0
        },
        {
            'id': uuid4(),
            'task_type': 'scheduled_scrape',
            'source_platform': 'LinkedIn',
            'status': 'completed',
            'started_at': datetime.now() - timedelta(hours=1),
            'completed_at': datetime.now() - timedelta(hours=1) + timedelta(minutes=10),
            'jobs_found': 18,
            'jobs_created': 2,
            'jobs_updated': 16,
            'retry_count': 0
        },
        {
            'id': uuid4(),
            'task_type': 'url_import',
            'target_url': 'https://linkedin.com/jobs/view/12345',
            'status': 'completed',
            'started_at': datetime.now() - timedelta(days=7),
            'completed_at': datetime.now() - timedelta(days=7) + timedelta(seconds=30),
            'jobs_found': 1,
            'jobs_created': 1,
            'jobs_updated': 0,
            'retry_count': 0
        },
        {
            'id': uuid4(),
            'task_type': 'scheduled_scrape',
            'source_platform': 'Monster',
            'status': 'failed',
            'started_at': datetime.now() - timedelta(minutes=30),
            'completed_at': datetime.now() - timedelta(minutes=25),
            'jobs_found': 0,
            'jobs_created': 0,
            'jobs_updated': 0,
            'error_message': 'Rate limit exceeded',
            'retry_count': 1
        }
    ]
    
    for task in tasks:
        conn.execute(text("""
            INSERT INTO scraping_tasks (
                id, task_type, source_platform, target_url, status,
                started_at, completed_at, jobs_found, jobs_created, jobs_updated,
                error_message, retry_count
            ) VALUES (
                :id, :task_type::tasktype, :source_platform, :target_url,
                :status::taskstatus, :started_at, :completed_at, :jobs_found,
                :jobs_created, :jobs_updated, :error_message, :retry_count
            )
        """), task)
    
    conn.commit()
    print(f"  ✓ Created {len(tasks)} scraping tasks")
    return tasks


def main():
    """Main execution function."""
    print()
    print("=" * 80)
    print("DATABASE SEEDING SCRIPT")
    print("=" * 80)
    print()
    
    # Connect to database
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✓ Database connection successful")
        print()
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return 1
    
    # Seed data
    try:
        with engine.begin() as conn:
            employers = seed_employers(conn)
            job_seekers = seed_job_seekers(conn)
            jobs = seed_jobs(conn, employers)
            applications = seed_applications(conn, jobs, job_seekers)
            job_sources = seed_job_sources(conn, jobs)
            scraping_tasks = seed_scraping_tasks(conn)
        
        print()
        print("=" * 80)
        print("✓ DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print()
        print("Summary:")
        print(f"  - {len(employers)} employers")
        print(f"  - {len(job_seekers)} job seekers")
        print(f"  - {len(jobs)} jobs")
        print(f"  - {len(applications)} applications")
        print(f"  - {len(job_sources)} job sources")
        print(f"  - {len(scraping_tasks)} scraping tasks")
        print()
        print("Test credentials:")
        print("  Employer: employer1@techcorp.com / password123")
        print("  Job Seeker: john.doe@example.com / password123")
        print()
        
        return 0
        
    except Exception as e:
        print(f"✗ Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
