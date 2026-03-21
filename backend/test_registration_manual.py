"""
Manual test script to verify registration endpoints.
This script tests the registration functionality without pytest.
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.models.employer import Employer, SubscriptionTier
from app.models.job_seeker import JobSeeker
from app.core.security import hash_password, verify_password, validate_password_strength
from app.schemas.auth import EmployerRegistrationRequest, JobSeekerRegistrationRequest


def test_password_validation():
    """Test password strength validation."""
    print("Testing password validation...")
    
    # Valid password
    is_valid, msg = validate_password_strength("SecurePass123!")
    assert is_valid, f"Valid password rejected: {msg}"
    print("✓ Valid password accepted")
    
    # Weak passwords
    weak_passwords = [
        ("short", "Too short"),
        ("nouppercase123!", "No uppercase"),
        ("NOLOWERCASE123!", "No lowercase"),
        ("NoDigits!", "No digits"),
        ("NoSpecial123", "No special characters"),
    ]
    
    for weak_pass, reason in weak_passwords:
        is_valid, msg = validate_password_strength(weak_pass)
        assert not is_valid, f"Weak password accepted: {reason}"
        print(f"✓ Weak password rejected: {reason}")
    
    print("✓ Password validation tests passed\n")


def test_password_hashing():
    """Test password hashing."""
    print("Testing password hashing...")
    
    password = "SecurePass123!"
    hashed = hash_password(password)
    
    # Verify hash is different from password
    assert hashed != password, "Password not hashed"
    print("✓ Password is hashed")
    
    # Verify hash starts with bcrypt prefix
    assert hashed.startswith("$2b$"), "Not a bcrypt hash"
    print("✓ Using bcrypt hashing")
    
    # Verify password verification works
    assert verify_password(password, hashed), "Password verification failed"
    print("✓ Password verification works")
    
    # Verify wrong password fails
    assert not verify_password("WrongPassword", hashed), "Wrong password accepted"
    print("✓ Wrong password rejected")
    
    # Verify same password produces different hashes (salt)
    hashed2 = hash_password(password)
    assert hashed != hashed2, "Same password produces same hash (no salt)"
    print("✓ Salt is used (different hashes for same password)")
    
    print("✓ Password hashing tests passed\n")


def test_employer_model():
    """Test employer model creation."""
    print("Testing employer model...")
    
    # Create in-memory database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create employer
    employer = Employer(
        email="test@company.com",
        password_hash=hash_password("SecurePass123!"),
        company_name="Test Corp",
        company_website="https://testcorp.com",
        subscription_tier=SubscriptionTier.FREE,
        monthly_posts_used=0,
        featured_posts_used=0,
    )
    
    session.add(employer)
    session.commit()
    
    # Verify employer was created
    retrieved = session.query(Employer).filter(Employer.email == "test@company.com").first()
    assert retrieved is not None, "Employer not created"
    assert retrieved.company_name == "Test Corp", "Company name mismatch"
    assert retrieved.subscription_tier == SubscriptionTier.FREE, "Subscription tier mismatch"
    print("✓ Employer model created successfully")
    
    session.close()
    print("✓ Employer model tests passed\n")


def test_job_seeker_model():
    """Test job seeker model creation."""
    print("Testing job seeker model...")
    
    # Create in-memory database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create job seeker
    job_seeker = JobSeeker(
        email="test@example.com",
        password_hash=hash_password("SecurePass123!"),
        full_name="John Doe",
        phone="+1234567890",
    )
    
    session.add(job_seeker)
    session.commit()
    
    # Verify job seeker was created
    retrieved = session.query(JobSeeker).filter(JobSeeker.email == "test@example.com").first()
    assert retrieved is not None, "Job seeker not created"
    assert retrieved.full_name == "John Doe", "Full name mismatch"
    assert retrieved.phone == "+1234567890", "Phone mismatch"
    print("✓ Job seeker model created successfully")
    
    session.close()
    print("✓ Job seeker model tests passed\n")


def test_schemas():
    """Test Pydantic schemas."""
    print("Testing Pydantic schemas...")
    
    # Test employer registration schema
    employer_data = {
        "email": "employer@company.com",
        "password": "SecurePass123!",
        "company_name": "Tech Corp",
        "company_website": "https://techcorp.com",
        "company_description": "Leading technology company"
    }
    
    employer_schema = EmployerRegistrationRequest(**employer_data)
    assert employer_schema.email == "employer@company.com"
    assert employer_schema.company_name == "Tech Corp"
    print("✓ Employer registration schema validated")
    
    # Test job seeker registration schema
    job_seeker_data = {
        "email": "jobseeker@example.com",
        "password": "SecurePass123!",
        "full_name": "John Doe",
        "phone": "+1234567890"
    }
    
    job_seeker_schema = JobSeekerRegistrationRequest(**job_seeker_data)
    assert job_seeker_schema.email == "jobseeker@example.com"
    assert job_seeker_schema.full_name == "John Doe"
    print("✓ Job seeker registration schema validated")
    
    print("✓ Schema tests passed\n")


def main():
    """Run all tests."""
    print("=" * 60)
    print("MANUAL REGISTRATION TESTS")
    print("=" * 60 + "\n")
    
    try:
        test_password_validation()
        test_password_hashing()
        test_employer_model()
        test_job_seeker_model()
        test_schemas()
        
        print("=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
