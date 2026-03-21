"""
Unit tests for password hashing and validation utilities.

Tests cover password hashing with bcrypt cost factor 12, password verification,
and password strength validation according to requirement 12.1.
"""
import pytest
from app.core.security import hash_password, verify_password, validate_password_strength


class TestHashPassword:
    """Test cases for password hashing functionality."""
    
    def test_hash_password_returns_non_empty_string(self):
        """Test that hashing returns a non-empty string."""
        password = "MySecurePass123!"
        hashed = hash_password(password)
        
        assert isinstance(hashed, str)
        assert len(hashed) > 0
    
    def test_hash_password_different_for_same_input(self):
        """Test that hashing the same password twice produces different hashes (salt)."""
        password = "MySecurePass123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Hashes should be different due to random salt
        assert hash1 != hash2
    
    def test_hash_password_contains_bcrypt_identifier(self):
        """Test that hashed password contains bcrypt identifier."""
        password = "MySecurePass123!"
        hashed = hash_password(password)
        
        # Bcrypt hashes start with $2b$ (or $2a$, $2y$)
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$") or hashed.startswith("$2y$")
    
    def test_hash_password_uses_cost_factor_12(self):
        """Test that bcrypt uses cost factor 12 as per requirement 12.1."""
        password = "MySecurePass123!"
        hashed = hash_password(password)
        
        # Extract cost factor from hash (format: $2b$12$...)
        parts = hashed.split("$")
        cost_factor = int(parts[2])
        
        assert cost_factor == 12
    
    def test_hash_password_raises_error_for_empty_password(self):
        """Test that hashing empty password raises ValueError."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            hash_password("")
    
    def test_hash_password_raises_error_for_none_password(self):
        """Test that hashing None password raises ValueError."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            hash_password(None)
    
    def test_hash_password_handles_special_characters(self):
        """Test that hashing works with special characters."""
        password = "P@ssw0rd!#$%^&*()"
        hashed = hash_password(password)
        
        assert isinstance(hashed, str)
        assert len(hashed) > 0
    
    def test_hash_password_handles_unicode_characters(self):
        """Test that hashing works with unicode characters."""
        password = "Pässwörd123!你好"
        hashed = hash_password(password)
        
        assert isinstance(hashed, str)
        assert len(hashed) > 0


class TestVerifyPassword:
    """Test cases for password verification functionality."""
    
    def test_verify_password_returns_true_for_correct_password(self):
        """Test that verification succeeds with correct password."""
        password = "MySecurePass123!"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_returns_false_for_incorrect_password(self):
        """Test that verification fails with incorrect password."""
        password = "MySecurePass123!"
        hashed = hash_password(password)
        
        assert verify_password("WrongPassword123!", hashed) is False
    
    def test_verify_password_case_sensitive(self):
        """Test that password verification is case-sensitive."""
        password = "MySecurePass123!"
        hashed = hash_password(password)
        
        assert verify_password("mysecurepass123!", hashed) is False
        assert verify_password("MYSECUREPASS123!", hashed) is False
    
    def test_verify_password_returns_false_for_empty_plain_password(self):
        """Test that verification fails with empty plain password."""
        hashed = hash_password("MySecurePass123!")
        
        assert verify_password("", hashed) is False
    
    def test_verify_password_returns_false_for_empty_hashed_password(self):
        """Test that verification fails with empty hashed password."""
        assert verify_password("MySecurePass123!", "") is False
    
    def test_verify_password_returns_false_for_none_passwords(self):
        """Test that verification fails with None values."""
        hashed = hash_password("MySecurePass123!")
        
        assert verify_password(None, hashed) is False
        assert verify_password("MySecurePass123!", None) is False
    
    def test_verify_password_returns_false_for_malformed_hash(self):
        """Test that verification fails gracefully with malformed hash."""
        assert verify_password("MySecurePass123!", "not_a_valid_hash") is False
    
    def test_verify_password_handles_special_characters(self):
        """Test that verification works with special characters."""
        password = "P@ssw0rd!#$%^&*()"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
        assert verify_password("P@ssw0rd!#$%^&*()X", hashed) is False
    
    def test_verify_password_handles_unicode_characters(self):
        """Test that verification works with unicode characters."""
        password = "Pässwörd123!你好"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
        assert verify_password("Pässwörd123!", hashed) is False


class TestValidatePasswordStrength:
    """Test cases for password strength validation."""
    
    def test_validate_strong_password(self):
        """Test that a strong password passes all validations."""
        is_valid, error = validate_password_strength("MySecurePass123!")
        
        assert is_valid is True
        assert error == ""
    
    def test_validate_password_minimum_length(self):
        """Test that password must be at least 8 characters."""
        is_valid, error = validate_password_strength("Short1!")
        
        assert is_valid is False
        assert "at least 8 characters" in error
    
    def test_validate_password_requires_uppercase(self):
        """Test that password must contain uppercase letter."""
        is_valid, error = validate_password_strength("lowercase123!")
        
        assert is_valid is False
        assert "uppercase letter" in error
    
    def test_validate_password_requires_lowercase(self):
        """Test that password must contain lowercase letter."""
        is_valid, error = validate_password_strength("UPPERCASE123!")
        
        assert is_valid is False
        assert "lowercase letter" in error
    
    def test_validate_password_requires_digit(self):
        """Test that password must contain digit."""
        is_valid, error = validate_password_strength("NoDigitsHere!")
        
        assert is_valid is False
        assert "digit" in error
    
    def test_validate_password_requires_special_character(self):
        """Test that password must contain special character."""
        is_valid, error = validate_password_strength("NoSpecial123")
        
        assert is_valid is False
        assert "special character" in error
    
    def test_validate_empty_password(self):
        """Test that empty password is rejected."""
        is_valid, error = validate_password_strength("")
        
        assert is_valid is False
        assert "cannot be empty" in error
    
    def test_validate_none_password(self):
        """Test that None password is rejected."""
        is_valid, error = validate_password_strength(None)
        
        assert is_valid is False
        assert "cannot be empty" in error
    
    def test_validate_password_exactly_8_characters(self):
        """Test that exactly 8 characters is valid if other requirements met."""
        is_valid, error = validate_password_strength("Pass123!")
        
        assert is_valid is True
        assert error == ""
    
    def test_validate_password_various_special_characters(self):
        """Test that various special characters are accepted."""
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?/~`"
        
        for char in special_chars:
            password = f"Password123{char}"
            is_valid, error = validate_password_strength(password)
            assert is_valid is True, f"Failed for special character: {char}"
    
    def test_validate_password_with_spaces(self):
        """Test that spaces count as special characters."""
        is_valid, error = validate_password_strength("Pass Word 123")
        
        assert is_valid is True
        assert error == ""
    
    def test_validate_long_password(self):
        """Test that very long passwords are accepted."""
        long_password = "MyVeryLongSecurePassword123!WithLotsOfCharacters"
        is_valid, error = validate_password_strength(long_password)
        
        assert is_valid is True
        assert error == ""
    
    def test_validate_password_multiple_missing_requirements(self):
        """Test that first missing requirement is reported."""
        # Missing uppercase, digit, and special character
        is_valid, error = validate_password_strength("lowercase")
        
        assert is_valid is False
        # Should report the first issue encountered
        assert len(error) > 0


class TestPasswordWorkflow:
    """Integration tests for complete password workflow."""
    
    def test_hash_and_verify_workflow(self):
        """Test complete workflow of hashing and verifying password."""
        password = "MySecurePass123!"
        
        # Hash the password
        hashed = hash_password(password)
        
        # Verify correct password
        assert verify_password(password, hashed) is True
        
        # Verify incorrect password
        assert verify_password("WrongPassword", hashed) is False
    
    def test_validate_then_hash_workflow(self):
        """Test workflow of validating strength before hashing."""
        password = "MySecurePass123!"
        
        # Validate strength
        is_valid, error = validate_password_strength(password)
        assert is_valid is True
        
        # Hash if valid
        if is_valid:
            hashed = hash_password(password)
            assert verify_password(password, hashed) is True
    
    def test_reject_weak_password_workflow(self):
        """Test workflow of rejecting weak password."""
        weak_password = "weak"
        
        # Validate strength
        is_valid, error = validate_password_strength(weak_password)
        assert is_valid is False
        assert len(error) > 0
        
        # Should not proceed to hashing in real application
        # But we can still hash it (validation is separate concern)
        hashed = hash_password(weak_password)
        assert verify_password(weak_password, hashed) is True
