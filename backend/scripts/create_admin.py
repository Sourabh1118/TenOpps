#!/usr/bin/env python3
"""
Create an admin user for the job platform.

This script creates an employer account with admin privileges.
Run this script on the server after deployment.
"""
import sys
import os
import bcrypt
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.employer import Employer, SubscriptionTier


def create_admin_user(
    email: str = "admin@trusanity.com",
    password: str = "Admin@123",
    company_name: str = "TruSanity Admin"
):
    """
    Create an admin user with premium subscription.
    
    Args:
        email: Admin email address
        password: Admin password
        company_name: Company name for admin account
    """
    db: Session = SessionLocal()
    
    try:
        # Check if admin already exists
        existing_admin = db.query(Employer).filter(Employer.email == email).first()
        if existing_admin:
            print(f"❌ Admin user with email {email} already exists!")
            print(f"   User ID: {existing_admin.id}")
            print(f"   Company: {existing_admin.company_name}")
            print(f"   Subscription: {existing_admin.subscription_tier}")
            return False
        
        # Create admin user
        # Hash password directly with bcrypt to avoid passlib issues
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=12)
        hashed_pw = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        
        admin_user = Employer(
            email=email,
            password_hash=hashed_pw,
            company_name=company_name,
            company_description="Platform Administrator Account",
            subscription_tier=SubscriptionTier.PREMIUM,  # Use enum value
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=3650),  # 10 years
            verified=True,
            monthly_posts_used=0,
            featured_posts_used=0,
            url_imports_used=0
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ Admin user created successfully!")
        print("")
        print("=" * 60)
        print("ADMIN CREDENTIALS")
        print("=" * 60)
        print(f"Email:        {email}")
        print(f"Password:     {password}")
        print(f"User ID:      {admin_user.id}")
        print(f"Company:      {admin_user.company_name}")
        print(f"Subscription: {admin_user.subscription_tier}")
        print(f"Verified:     {admin_user.verified}")
        print("=" * 60)
        print("")
        print("⚠️  IMPORTANT: Change the password after first login!")
        print("")
        print("Login at: http://trusanity.com/login")
        print("")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating admin user: {e}")
        return False
        
    finally:
        db.close()


def main():
    """Main function to create admin user."""
    print("")
    print("=" * 60)
    print("CREATE ADMIN USER")
    print("=" * 60)
    print("")
    
    # Get custom credentials if provided
    if len(sys.argv) > 1:
        email = sys.argv[1]
        password = sys.argv[2] if len(sys.argv) > 2 else "Admin@123"
        company_name = sys.argv[3] if len(sys.argv) > 3 else "TruSanity Admin"
    else:
        email = "admin@trusanity.com"
        password = "Admin@123"
        company_name = "TruSanity Admin"
    
    print(f"Creating admin user: {email}")
    print(f"Password length: {len(password)} characters, {len(password.encode('utf-8'))} bytes")
    print("")
    
    success = create_admin_user(email, password, company_name)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
