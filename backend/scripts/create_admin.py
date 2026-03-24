#!/usr/bin/env python3
"""
Create an admin user for the job platform.

This script creates a proper admin account in the admins table.
Admin users have platform-wide control and are separate from employers.
Run this script on the server after deployment.
"""
import sys
import os
import bcrypt
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.admin import Admin


def create_admin_user(
    email: str = "admin@trusanity.com",
    password: str = "Admin@123",
    full_name: str = "Platform Administrator"
):
    """
    Create an admin user in the admins table.
    
    Admin users are platform owners with full control over the system.
    They are separate from employers (companies who post jobs).
    
    Args:
        email: Admin email address
        password: Admin password
        full_name: Full name of the administrator
    """
    db: Session = SessionLocal()
    
    try:
        # Check if admin already exists
        existing_admin = db.query(Admin).filter(Admin.email == email).first()
        if existing_admin:
            print(f"❌ Admin user with email {email} already exists!")
            print(f"   User ID: {existing_admin.id}")
            print(f"   Full Name: {existing_admin.full_name}")
            print(f"   Created: {existing_admin.created_at}")
            return False
        
        # Create admin user
        # Hash password directly with bcrypt to avoid passlib issues
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=12)
        hashed_pw = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        
        admin_user = Admin(
            email=email,
            password_hash=hashed_pw,
            full_name=full_name
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
        print(f"Full Name:    {admin_user.full_name}")
        print(f"Role:         admin (platform owner)")
        print(f"Created:      {admin_user.created_at}")
        print("=" * 60)
        print("")
        print("⚠️  IMPORTANT: Change the password after first login!")
        print("")
        print("Login at: https://trusanity.com/login")
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
    print("CREATE ADMIN USER (PLATFORM OWNER)")
    print("=" * 60)
    print("")
    print("Admin users have full platform control and are separate from employers.")
    print("")
    
    # Get custom credentials if provided
    if len(sys.argv) > 1:
        email = sys.argv[1]
        password = sys.argv[2] if len(sys.argv) > 2 else "Admin@123"
        full_name = sys.argv[3] if len(sys.argv) > 3 else "Platform Administrator"
    else:
        email = "admin@trusanity.com"
        password = "Admin@123"
        full_name = "Platform Administrator"
    
    print(f"Creating admin user: {email}")
    print(f"Full name: {full_name}")
    print(f"Password length: {len(password)} characters")
    print("")
    
    success = create_admin_user(email, password, full_name)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
