#!/usr/bin/env python3
"""
Environment variable validation script for production deployment.

This script validates that all required environment variables are set
and have appropriate values for production deployment.
"""
import os
import sys
import argparse
from typing import List, Tuple, Dict
from urllib.parse import urlparse


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def check_required_var(var_name: str, env_vars: Dict[str, str]) -> Tuple[bool, str]:
    """Check if a required environment variable is set."""
    value = env_vars.get(var_name)
    if not value:
        return False, f"Missing required variable: {var_name}"
    return True, ""


def check_secret_strength(var_name: str, env_vars: Dict[str, str], min_length: int = 32) -> Tuple[bool, str]:
    """Check if a secret key is strong enough."""
    value = env_vars.get(var_name, "")
    
    if not value:
        return False, f"{var_name} is not set"
    
    if len(value) < min_length:
        return False, f"{var_name} is too short (minimum {min_length} characters)"
    
    # Check for common weak values
    weak_values = [
        "change",
        "secret",
        "password",
        "dev",
        "test",
        "example",
        "your-",
        "CHANGE",
    ]
    
    for weak in weak_values:
        if weak.lower() in value.lower():
            return False, f"{var_name} contains weak/placeholder text: '{weak}'"
    
    return True, ""


def check_database_url(env_vars: Dict[str, str], require_ssl: bool = True) -> Tuple[bool, str]:
    """Validate database URL format and SSL requirement."""
    db_url = env_vars.get("DATABASE_URL", "")
    
    if not db_url:
        return False, "DATABASE_URL is not set"
    
    try:
        parsed = urlparse(db_url)
        
        if parsed.scheme != "postgresql":
            return False, f"DATABASE_URL must use postgresql:// scheme, got: {parsed.scheme}"
        
        if not parsed.hostname:
            return False, "DATABASE_URL missing hostname"
        
        if not parsed.username:
            return False, "DATABASE_URL missing username"
        
        if not parsed.password:
            return False, "DATABASE_URL missing password"
        
        if require_ssl and "sslmode=require" not in db_url:
            return False, "DATABASE_URL should include ?sslmode=require for production"
        
        return True, ""
    
    except Exception as e:
        return False, f"Invalid DATABASE_URL format: {str(e)}"


def check_redis_url(env_vars: Dict[str, str]) -> Tuple[bool, str]:
    """Validate Redis URL format."""
    redis_url = env_vars.get("REDIS_URL", "")
    
    if not redis_url:
        return False, "REDIS_URL is not set"
    
    try:
        parsed = urlparse(redis_url)
        
        if parsed.scheme != "redis":
            return False, f"REDIS_URL must use redis:// scheme, got: {parsed.scheme}"
        
        if not parsed.hostname:
            return False, "REDIS_URL missing hostname"
        
        return True, ""
    
    except Exception as e:
        return False, f"Invalid REDIS_URL format: {str(e)}"


def check_cors_origins(env_vars: Dict[str, str], allow_localhost: bool = False) -> Tuple[bool, str]:
    """Validate CORS origins configuration."""
    cors_origins = env_vars.get("CORS_ORIGINS", "")
    
    if not cors_origins:
        return False, "CORS_ORIGINS is not set"
    
    origins = [o.strip() for o in cors_origins.split(",")]
    
    for origin in origins:
        if not origin.startswith("http://") and not origin.startswith("https://"):
            return False, f"Invalid CORS origin (must start with http:// or https://): {origin}"
        
        if not allow_localhost and ("localhost" in origin or "127.0.0.1" in origin):
            return False, f"CORS origin should not include localhost in production: {origin}"
        
        if origin == "*":
            return False, "CORS origin should not be wildcard (*) in production"
    
    return True, ""


def check_stripe_keys(env_vars: Dict[str, str], require_live: bool = True) -> Tuple[bool, str]:
    """Validate Stripe API keys."""
    secret_key = env_vars.get("STRIPE_SECRET_KEY", "")
    publishable_key = env_vars.get("STRIPE_PUBLISHABLE_KEY", "")
    webhook_secret = env_vars.get("STRIPE_WEBHOOK_SECRET", "")
    
    if not secret_key:
        return False, "STRIPE_SECRET_KEY is not set"
    
    if not publishable_key:
        return False, "STRIPE_PUBLISHABLE_KEY is not set"
    
    if not webhook_secret:
        return False, "STRIPE_WEBHOOK_SECRET is not set"
    
    if require_live:
        if not secret_key.startswith("sk_live_"):
            return False, "STRIPE_SECRET_KEY should start with 'sk_live_' for production (currently using test key)"
        
        if not publishable_key.startswith("pk_live_"):
            return False, "STRIPE_PUBLISHABLE_KEY should start with 'pk_live_' for production (currently using test key)"
    
    if not webhook_secret.startswith("whsec_"):
        return False, "STRIPE_WEBHOOK_SECRET should start with 'whsec_'"
    
    return True, ""


def check_debug_mode(env_vars: Dict[str, str]) -> Tuple[bool, str]:
    """Check that DEBUG mode is disabled in production."""
    debug = env_vars.get("DEBUG", "").lower()
    
    if debug in ["true", "1", "yes"]:
        return False, "DEBUG should be False in production"
    
    return True, ""


def validate_production_env(env_file: str = None) -> bool:
    """
    Validate production environment configuration.
    
    Args:
        env_file: Path to .env file (optional, uses environment if not provided)
    
    Returns:
        True if all validations pass, False otherwise
    """
    # Load environment variables
    env_vars = {}
    
    if env_file:
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        except FileNotFoundError:
            print(f"{Colors.RED}✗ Environment file not found: {env_file}{Colors.RESET}")
            return False
    else:
        env_vars = dict(os.environ)
    
    print(f"\n{Colors.BOLD}=== Production Environment Validation ==={Colors.RESET}\n")
    
    checks = []
    
    # Required variables
    print(f"{Colors.BLUE}Checking required variables...{Colors.RESET}")
    required_vars = [
        "APP_NAME",
        "APP_ENV",
        "SECRET_KEY",
        "DATABASE_URL",
        "REDIS_URL",
        "CELERY_BROKER_URL",
        "CELERY_RESULT_BACKEND",
        "JWT_SECRET_KEY",
        "CORS_ORIGINS",
    ]
    
    for var in required_vars:
        success, message = check_required_var(var, env_vars)
        checks.append((var, success, message))
    
    # Secret strength
    print(f"{Colors.BLUE}Checking secret key strength...{Colors.RESET}")
    for var in ["SECRET_KEY", "JWT_SECRET_KEY"]:
        success, message = check_secret_strength(var, env_vars)
        checks.append((f"{var} strength", success, message))
    
    # Database URL
    print(f"{Colors.BLUE}Checking database configuration...{Colors.RESET}")
    success, message = check_database_url(env_vars, require_ssl=True)
    checks.append(("DATABASE_URL", success, message))
    
    # Redis URL
    print(f"{Colors.BLUE}Checking Redis configuration...{Colors.RESET}")
    success, message = check_redis_url(env_vars)
    checks.append(("REDIS_URL", success, message))
    
    # CORS origins
    print(f"{Colors.BLUE}Checking CORS configuration...{Colors.RESET}")
    success, message = check_cors_origins(env_vars, allow_localhost=False)
    checks.append(("CORS_ORIGINS", success, message))
    
    # Stripe keys
    print(f"{Colors.BLUE}Checking Stripe configuration...{Colors.RESET}")
    success, message = check_stripe_keys(env_vars, require_live=True)
    checks.append(("Stripe keys", success, message))
    
    # Debug mode
    print(f"{Colors.BLUE}Checking debug mode...{Colors.RESET}")
    success, message = check_debug_mode(env_vars)
    checks.append(("DEBUG mode", success, message))
    
    # Print results
    print(f"\n{Colors.BOLD}=== Validation Results ==={Colors.RESET}\n")
    
    passed = 0
    failed = 0
    
    for check_name, success, message in checks:
        if success:
            print(f"{Colors.GREEN}✓{Colors.RESET} {check_name}")
            passed += 1
        else:
            print(f"{Colors.RED}✗{Colors.RESET} {check_name}: {message}")
            failed += 1
    
    # Summary
    print(f"\n{Colors.BOLD}=== Summary ==={Colors.RESET}")
    print(f"Passed: {Colors.GREEN}{passed}{Colors.RESET}")
    print(f"Failed: {Colors.RED}{failed}{Colors.RESET}")
    
    if failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All validations passed! Environment is ready for production.{Colors.RESET}\n")
        return True
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ {failed} validation(s) failed. Please fix the issues before deploying.{Colors.RESET}\n")
        return False


def validate_development_env(env_file: str = None) -> bool:
    """
    Validate development environment configuration.
    
    Args:
        env_file: Path to .env file (optional, uses environment if not provided)
    
    Returns:
        True if all validations pass, False otherwise
    """
    # Load environment variables
    env_vars = {}
    
    if env_file:
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        except FileNotFoundError:
            print(f"{Colors.RED}✗ Environment file not found: {env_file}{Colors.RESET}")
            return False
    else:
        env_vars = dict(os.environ)
    
    print(f"\n{Colors.BOLD}=== Development Environment Validation ==={Colors.RESET}\n")
    
    checks = []
    
    # Required variables (less strict for development)
    required_vars = [
        "DATABASE_URL",
        "REDIS_URL",
        "SECRET_KEY",
        "JWT_SECRET_KEY",
    ]
    
    for var in required_vars:
        success, message = check_required_var(var, env_vars)
        checks.append((var, success, message))
    
    # Database URL (no SSL requirement for dev)
    success, message = check_database_url(env_vars, require_ssl=False)
    checks.append(("DATABASE_URL", success, message))
    
    # Redis URL
    success, message = check_redis_url(env_vars)
    checks.append(("REDIS_URL", success, message))
    
    # Print results
    print(f"\n{Colors.BOLD}=== Validation Results ==={Colors.RESET}\n")
    
    passed = 0
    failed = 0
    
    for check_name, success, message in checks:
        if success:
            print(f"{Colors.GREEN}✓{Colors.RESET} {check_name}")
            passed += 1
        else:
            print(f"{Colors.RED}✗{Colors.RESET} {check_name}: {message}")
            failed += 1
    
    # Summary
    print(f"\n{Colors.BOLD}=== Summary ==={Colors.RESET}")
    print(f"Passed: {Colors.GREEN}{passed}{Colors.RESET}")
    print(f"Failed: {Colors.RED}{failed}{Colors.RESET}")
    
    if failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All validations passed!{Colors.RESET}\n")
        return True
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ {failed} validation(s) failed.{Colors.RESET}\n")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate environment configuration for deployment"
    )
    parser.add_argument(
        "--env",
        choices=["production", "development"],
        default="development",
        help="Environment to validate (default: development)"
    )
    parser.add_argument(
        "--file",
        help="Path to .env file (optional, uses current environment if not provided)"
    )
    
    args = parser.parse_args()
    
    if args.env == "production":
        success = validate_production_env(args.file)
    else:
        success = validate_development_env(args.file)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
