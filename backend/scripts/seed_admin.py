"""
Script to seed the first admin account.
"""
import sys
import os
from pathlib import Path
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.security import get_password_hash


def seed_admin(conn, email, password, full_name):
    """Seed the initial admin account."""
    print(f"Seeding admin account: {email}...")
    
    # Check if admin already exists
    result = conn.execute(
        text("SELECT id FROM admins WHERE email = :email"),
        {"email": email}
    ).fetchone()
    
    if result:
        print(f"  ! Admin with email {email} already exists. Skipping.")
        return
    
    # Create admin
    admin_id = uuid4()
    password_hash = get_password_hash(password)
    
    conn.execute(
        text("""
            INSERT INTO admins (id, email, password_hash, full_name, created_at, updated_at)
            VALUES (:id, :email, :password_hash, :full_name, NOW(), NOW())
        """),
        {
            "id": admin_id,
            "email": email,
            "password_hash": password_hash,
            "full_name": full_name
        }
    )
    
    print(f"  ✓ Admin account created successfully!")
    print(f"  - Email: {email}")
    print(f"  - Password: {password}")
    print(f"  - Full Name: {full_name}")


def main():
    """Main execution function."""
    # Get credentials from environment or use defaults
    admin_email = os.getenv("ADMIN_EMAIL", "admin@trusanity.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "AdminPass123!")
    admin_name = os.getenv("ADMIN_NAME", "System Administrator")
    
    print("\n" + "="*50)
    print("ADMIN SEEDING SCRIPT")
    print("="*50 + "\n")
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.begin() as conn:
            seed_admin(conn, admin_email, admin_password, admin_name)
        
        print("\n" + "="*50)
        print("✓ SEEDING COMPLETED SUCCESSFULLY")
        print("="*50 + "\n")
        return 0
    except Exception as e:
        print(f"\n✗ Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
