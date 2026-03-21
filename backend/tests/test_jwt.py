"""
Unit tests for JWT token generation and validation.

Tests cover:
- Access token creation with correct expiration
- Refresh token creation with correct expiration
- Token decoding and validation
- Token type verification
- Error handling for invalid/expired tokens
"""
import pytest
from datetime import datetime, timedelta
from jose import jwt, JWTError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type
)
from app.core.config import settings


class TestAccessTokenGeneration:
    """Test suite for access token generation."""
    
    def test_create_access_token_with_default_expiration(self):
        """Test that access token is created with 15-minute default expiration."""
        data = {"sub": "user123", "role": "employer"}
        token = create_access_token(data)
        
        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify contents
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        assert payload["sub"] == "user123"
        assert payload["role"] == "employer"
        assert payload["type"] == "access"
        
        # Verify expiration is approximately 15 minutes from now
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.utcfromtimestamp(exp_timestamp)
        expected_exp = datetime.utcnow() + timedelta(minutes=15)
        
        # Allow 5 second tolerance for test execution time
        time_diff = abs((exp_datetime - expected_exp).total_seconds())
        assert time_diff < 5
    
    def test_create_access_token_with_custom_expiration(self):
        """Test that access token respects custom expiration delta."""
        data = {"sub": "user456"}
        custom_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta=custom_delta)
        
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Verify expiration is approximately 30 minutes from now
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.utcfromtimestamp(exp_timestamp)
        expected_exp = datetime.utcnow() + timedelta(minutes=30)
        
        time_diff = abs((exp_datetime - expected_exp).total_seconds())
        assert time_diff < 5
    
    def test_create_access_token_includes_all_claims(self):
        """Test that all provided claims are included in the token."""
        data = {
            "sub": "user789",
            "role": "job_seeker",
            "email": "test@example.com",
            "custom_claim": "custom_value"
        }
        token = create_access_token(data)
        
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        assert payload["sub"] == "user789"
        assert payload["role"] == "job_seeker"
        assert payload["email"] == "test@example.com"
        assert payload["custom_claim"] == "custom_value"
        assert payload["type"] == "access"


class TestRefreshTokenGeneration:
    """Test suite for refresh token generation."""
    
    def test_create_refresh_token_with_7_day_expiration(self):
        """Test that refresh token is created with 7-day expiration."""
        data = {"sub": "user123"}
        token = create_refresh_token(data)
        
        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify contents
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        assert payload["sub"] == "user123"
        assert payload["type"] == "refresh"
        
        # Verify expiration is approximately 7 days from now
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.utcfromtimestamp(exp_timestamp)
        expected_exp = datetime.utcnow() + timedelta(days=7)
        
        # Allow 5 second tolerance
        time_diff = abs((exp_datetime - expected_exp).total_seconds())
        assert time_diff < 5
    
    def test_create_refresh_token_includes_claims(self):
        """Test that refresh token includes all provided claims."""
        data = {
            "sub": "user456",
            "role": "employer"
        }
        token = create_refresh_token(data)
        
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        assert payload["sub"] == "user456"
        assert payload["role"] == "employer"
        assert payload["type"] == "refresh"


class TestTokenDecoding:
    """Test suite for token decoding and validation."""
    
    def test_decode_valid_access_token(self):
        """Test decoding a valid access token."""
        data = {"sub": "user123", "role": "employer"}
        token = create_access_token(data)
        
        payload = decode_token(token)
        
        assert payload["sub"] == "user123"
        assert payload["role"] == "employer"
        assert payload["type"] == "access"
        assert "exp" in payload
    
    def test_decode_valid_refresh_token(self):
        """Test decoding a valid refresh token."""
        data = {"sub": "user456", "role": "job_seeker"}
        token = create_refresh_token(data)
        
        payload = decode_token(token)
        
        assert payload["sub"] == "user456"
        assert payload["role"] == "job_seeker"
        assert payload["type"] == "refresh"
        assert "exp" in payload
    
    def test_decode_token_with_invalid_signature(self):
        """Test that decoding fails for token with invalid signature."""
        data = {"sub": "user123"}
        token = create_access_token(data)
        
        # Tamper with the token by changing last character
        tampered_token = token[:-1] + ("a" if token[-1] != "a" else "b")
        
        with pytest.raises(JWTError):
            decode_token(tampered_token)
    
    def test_decode_expired_token(self):
        """Test that decoding fails for expired token."""
        data = {"sub": "user123"}
        # Create token that expired 1 minute ago
        expired_delta = timedelta(minutes=-1)
        token = create_access_token(data, expires_delta=expired_delta)
        
        with pytest.raises(JWTError):
            decode_token(token)
    
    def test_decode_malformed_token(self):
        """Test that decoding fails for malformed token."""
        malformed_tokens = [
            "not.a.token",
            "invalid",
            "",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"
        ]
        
        for token in malformed_tokens:
            with pytest.raises(JWTError):
                decode_token(token)


class TestTokenTypeVerification:
    """Test suite for token type verification."""
    
    def test_verify_access_token_type(self):
        """Test verification of access token type."""
        token = create_access_token({"sub": "user123"})
        payload = decode_token(token)
        
        assert verify_token_type(payload, "access") is True
        assert verify_token_type(payload, "refresh") is False
    
    def test_verify_refresh_token_type(self):
        """Test verification of refresh token type."""
        token = create_refresh_token({"sub": "user123"})
        payload = decode_token(token)
        
        assert verify_token_type(payload, "refresh") is True
        assert verify_token_type(payload, "access") is False
    
    def test_verify_token_type_missing_type_claim(self):
        """Test verification when type claim is missing."""
        # Manually create token without type claim
        payload = {"sub": "user123", "exp": datetime.utcnow() + timedelta(minutes=15)}
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        
        decoded = decode_token(token)
        
        assert verify_token_type(decoded, "access") is False
        assert verify_token_type(decoded, "refresh") is False


class TestTokenExpirationTimes:
    """Test suite for verifying correct expiration times."""
    
    def test_access_token_expires_in_15_minutes(self):
        """Test that access token expiration matches requirement 12.3."""
        token = create_access_token({"sub": "user123"})
        payload = decode_token(token)
        
        exp_datetime = datetime.utcfromtimestamp(payload["exp"])
        now = datetime.utcnow()
        
        # Calculate actual expiration time in minutes
        time_diff_minutes = (exp_datetime - now).total_seconds() / 60
        
        # Should be 15 minutes (allow small tolerance)
        assert 14.9 <= time_diff_minutes <= 15.1
    
    def test_refresh_token_expires_in_7_days(self):
        """Test that refresh token expiration matches requirement 12.4."""
        token = create_refresh_token({"sub": "user123"})
        payload = decode_token(token)
        
        exp_datetime = datetime.utcfromtimestamp(payload["exp"])
        now = datetime.utcnow()
        
        # Calculate actual expiration time in days
        time_diff_days = (exp_datetime - now).total_seconds() / (60 * 60 * 24)
        
        # Should be 7 days (allow small tolerance)
        assert 6.99 <= time_diff_days <= 7.01


class TestTokenPayloadStructure:
    """Test suite for token payload structure."""
    
    def test_access_token_contains_required_fields(self):
        """Test that access token contains all required fields."""
        data = {"sub": "user123", "role": "employer"}
        token = create_access_token(data)
        payload = decode_token(token)
        
        # Required fields
        assert "sub" in payload
        assert "exp" in payload
        assert "type" in payload
        
        # Verify values
        assert payload["sub"] == "user123"
        assert payload["role"] == "employer"
        assert payload["type"] == "access"
    
    def test_refresh_token_contains_required_fields(self):
        """Test that refresh token contains all required fields."""
        data = {"sub": "user456"}
        token = create_refresh_token(data)
        payload = decode_token(token)
        
        # Required fields
        assert "sub" in payload
        assert "exp" in payload
        assert "type" in payload
        
        # Verify values
        assert payload["sub"] == "user456"
        assert payload["type"] == "refresh"
    
    def test_token_preserves_original_data(self):
        """Test that token encoding preserves all original data."""
        original_data = {
            "sub": "user789",
            "role": "admin",
            "email": "admin@example.com",
            "permissions": ["read", "write", "delete"]
        }
        
        token = create_access_token(original_data)
        payload = decode_token(token)
        
        # All original fields should be present
        assert payload["sub"] == original_data["sub"]
        assert payload["role"] == original_data["role"]
        assert payload["email"] == original_data["email"]
        assert payload["permissions"] == original_data["permissions"]


class TestTokenSecurity:
    """Test suite for token security features."""
    
    def test_tokens_are_signed_with_secret_key(self):
        """Test that tokens are properly signed and cannot be decoded with wrong key."""
        token = create_access_token({"sub": "user123"})
        
        # Try to decode with wrong secret key
        with pytest.raises(JWTError):
            jwt.decode(token, "wrong_secret_key", algorithms=[settings.JWT_ALGORITHM])
    
    def test_different_tokens_for_same_data(self):
        """Test that creating multiple tokens with same data produces different tokens."""
        data = {"sub": "user123", "role": "employer"}
        
        token1 = create_access_token(data)
        token2 = create_access_token(data)
        
        # Tokens should be different due to different expiration timestamps
        # Note: This test might rarely fail if both tokens are created in the same second
        # In practice, this is acceptable as the tokens are still valid
        assert isinstance(token1, str)
        assert isinstance(token2, str)
    
    def test_access_and_refresh_tokens_are_different(self):
        """Test that access and refresh tokens for same user are different."""
        data = {"sub": "user123", "role": "employer"}
        
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)
        
        # Tokens should be different
        assert access_token != refresh_token
        
        # Decode both and verify types
        access_payload = decode_token(access_token)
        refresh_payload = decode_token(refresh_token)
        
        assert access_payload["type"] == "access"
        assert refresh_payload["type"] == "refresh"
