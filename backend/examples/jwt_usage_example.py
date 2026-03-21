"""
JWT Token Usage Examples

This file demonstrates how to use the JWT token system for authentication
in the Job Aggregation Platform.

Run this file to see examples of:
- Creating access and refresh tokens
- Decoding and validating tokens
- Handling token expiration
- Using tokens with FastAPI dependencies
"""
from datetime import timedelta
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type
)
from jose import JWTError


def example_1_create_tokens():
    """Example 1: Creating access and refresh tokens"""
    print("\n=== Example 1: Creating Tokens ===")
    
    # User data to encode in token
    user_data = {
        "sub": "123e4567-e89b-12d3-a456-426614174000",  # User ID
        "role": "employer",
        "email": "employer@example.com"
    }
    
    # Create access token (15-minute expiration)
    access_token = create_access_token(user_data)
    print(f"Access Token: {access_token[:50]}...")
    
    # Create refresh token (7-day expiration)
    refresh_token = create_refresh_token(user_data)
    print(f"Refresh Token: {refresh_token[:50]}...")
    
    return access_token, refresh_token


def example_2_decode_tokens(access_token, refresh_token):
    """Example 2: Decoding and validating tokens"""
    print("\n=== Example 2: Decoding Tokens ===")
    
    # Decode access token
    access_payload = decode_token(access_token)
    print(f"Access Token Payload:")
    print(f"  User ID: {access_payload['sub']}")
    print(f"  Role: {access_payload['role']}")
    print(f"  Type: {access_payload['type']}")
    print(f"  Expires: {access_payload['exp']}")
    
    # Decode refresh token
    refresh_payload = decode_token(refresh_token)
    print(f"\nRefresh Token Payload:")
    print(f"  User ID: {refresh_payload['sub']}")
    print(f"  Role: {refresh_payload['role']}")
    print(f"  Type: {refresh_payload['type']}")
    print(f"  Expires: {refresh_payload['exp']}")


def example_3_verify_token_types(access_token, refresh_token):
    """Example 3: Verifying token types"""
    print("\n=== Example 3: Verifying Token Types ===")
    
    # Decode tokens
    access_payload = decode_token(access_token)
    refresh_payload = decode_token(refresh_token)
    
    # Verify access token
    is_access = verify_token_type(access_payload, "access")
    print(f"Access token is 'access' type: {is_access}")
    
    is_refresh = verify_token_type(access_payload, "refresh")
    print(f"Access token is 'refresh' type: {is_refresh}")
    
    # Verify refresh token
    is_access = verify_token_type(refresh_payload, "access")
    print(f"Refresh token is 'access' type: {is_access}")
    
    is_refresh = verify_token_type(refresh_payload, "refresh")
    print(f"Refresh token is 'refresh' type: {is_refresh}")


def example_4_custom_expiration():
    """Example 4: Creating tokens with custom expiration"""
    print("\n=== Example 4: Custom Expiration ===")
    
    user_data = {"sub": "user123", "role": "admin"}
    
    # Create token with 30-minute expiration
    custom_token = create_access_token(
        user_data,
        expires_delta=timedelta(minutes=30)
    )
    
    payload = decode_token(custom_token)
    print(f"Custom token created with 30-minute expiration")
    print(f"Token type: {payload['type']}")


def example_5_handle_invalid_token():
    """Example 5: Handling invalid tokens"""
    print("\n=== Example 5: Handling Invalid Tokens ===")
    
    invalid_tokens = [
        "invalid.token.here",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
        ""
    ]
    
    for token in invalid_tokens:
        try:
            decode_token(token)
            print(f"Token validated (unexpected)")
        except JWTError as e:
            print(f"Token validation failed (expected): {str(e)[:50]}...")


def example_6_handle_expired_token():
    """Example 6: Handling expired tokens"""
    print("\n=== Example 6: Handling Expired Tokens ===")
    
    # Create token that expires immediately
    user_data = {"sub": "user123", "role": "employer"}
    expired_token = create_access_token(
        user_data,
        expires_delta=timedelta(seconds=-1)  # Already expired
    )
    
    try:
        decode_token(expired_token)
        print("Token validated (unexpected)")
    except JWTError as e:
        print(f"Token expired (expected): {str(e)}")


def example_7_token_refresh_flow():
    """Example 7: Complete token refresh flow"""
    print("\n=== Example 7: Token Refresh Flow ===")
    
    # Step 1: User logs in, receives both tokens
    print("Step 1: User logs in")
    user_data = {"sub": "user123", "role": "employer"}
    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token(user_data)
    print("  ✓ Access token issued (15 min)")
    print("  ✓ Refresh token issued (7 days)")
    
    # Step 2: User makes API requests with access token
    print("\nStep 2: User makes API requests")
    try:
        payload = decode_token(access_token)
        if verify_token_type(payload, "access"):
            print("  ✓ Access token validated")
            print(f"  ✓ User {payload['sub']} authenticated")
    except JWTError:
        print("  ✗ Access token invalid")
    
    # Step 3: Access token expires, use refresh token
    print("\nStep 3: Access token expires")
    print("  ✓ Client detects 401 Unauthorized")
    
    # Step 4: Request new access token with refresh token
    print("\nStep 4: Request new access token")
    try:
        refresh_payload = decode_token(refresh_token)
        if verify_token_type(refresh_payload, "refresh"):
            # Generate new access token
            new_access_token = create_access_token({
                "sub": refresh_payload["sub"],
                "role": refresh_payload["role"]
            })
            print("  ✓ Refresh token validated")
            print("  ✓ New access token issued")
            
            # Step 5: Continue making requests with new access token
            print("\nStep 5: Continue with new access token")
            new_payload = decode_token(new_access_token)
            print(f"  ✓ User {new_payload['sub']} re-authenticated")
    except JWTError:
        print("  ✗ Refresh token invalid, user must log in again")


def example_8_role_based_access():
    """Example 8: Role-based access control"""
    print("\n=== Example 8: Role-Based Access Control ===")
    
    # Create tokens for different roles
    employer_token = create_access_token({
        "sub": "employer123",
        "role": "employer"
    })
    
    job_seeker_token = create_access_token({
        "sub": "seeker456",
        "role": "job_seeker"
    })
    
    admin_token = create_access_token({
        "sub": "admin789",
        "role": "admin"
    })
    
    # Simulate role checking
    def check_employer_access(token):
        payload = decode_token(token)
        return payload.get("role") == "employer"
    
    def check_job_seeker_access(token):
        payload = decode_token(token)
        return payload.get("role") == "job_seeker"
    
    def check_admin_access(token):
        payload = decode_token(token)
        return payload.get("role") == "admin"
    
    print("Employer accessing /jobs/create:")
    print(f"  Access granted: {check_employer_access(employer_token)}")
    
    print("\nJob seeker accessing /jobs/create:")
    print(f"  Access granted: {check_employer_access(job_seeker_token)}")
    
    print("\nAdmin accessing /admin/stats:")
    print(f"  Access granted: {check_admin_access(admin_token)}")
    
    print("\nEmployer accessing /admin/stats:")
    print(f"  Access granted: {check_admin_access(employer_token)}")


def main():
    """Run all examples"""
    print("=" * 60)
    print("JWT Token Usage Examples")
    print("=" * 60)
    
    # Example 1: Create tokens
    access_token, refresh_token = example_1_create_tokens()
    
    # Example 2: Decode tokens
    example_2_decode_tokens(access_token, refresh_token)
    
    # Example 3: Verify token types
    example_3_verify_token_types(access_token, refresh_token)
    
    # Example 4: Custom expiration
    example_4_custom_expiration()
    
    # Example 5: Invalid tokens
    example_5_handle_invalid_token()
    
    # Example 6: Expired tokens
    example_6_handle_expired_token()
    
    # Example 7: Token refresh flow
    example_7_token_refresh_flow()
    
    # Example 8: Role-based access
    example_8_role_based_access()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
