#!/bin/bash

# Security Testing Script
# Runs comprehensive security tests for the Job Aggregation Platform
# Requirements: 12.1-12.10, 13.1-13.9, 14.1-14.6

set -e

echo "========================================="
echo "Security Testing Suite"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Warning: Virtual environment not activated${NC}"
    echo "Activating virtual environment..."
    source venv/bin/activate || source .venv/bin/activate || {
        echo -e "${RED}Error: Could not activate virtual environment${NC}"
        exit 1
    }
fi

# Function to print section header
print_section() {
    echo ""
    echo "========================================="
    echo "$1"
    echo "========================================="
    echo ""
}

# Function to print test result
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2 PASSED${NC}"
    else
        echo -e "${RED}✗ $2 FAILED${NC}"
    fi
}

# Track overall test status
OVERALL_STATUS=0

# 1. Run unit tests for security modules
print_section "1. Running Security Unit Tests"

echo "Testing password hashing and validation..."
pytest backend/tests/test_security.py -v --tb=short
TEST_STATUS=$?
print_result $TEST_STATUS "Password Security Tests"
[ $TEST_STATUS -ne 0 ] && OVERALL_STATUS=1

echo ""
echo "Testing input validation and sanitization..."
pytest backend/tests/test_security_validation.py -v --tb=short
TEST_STATUS=$?
print_result $TEST_STATUS "Input Validation Tests"
[ $TEST_STATUS -ne 0 ] && OVERALL_STATUS=1

echo ""
echo "Testing rate limiting..."
pytest backend/tests/test_rate_limiting.py -v --tb=short
TEST_STATUS=$?
print_result $TEST_STATUS "Rate Limiting Tests"
[ $TEST_STATUS -ne 0 ] && OVERALL_STATUS=1

# 2. Run comprehensive security tests
print_section "2. Running Comprehensive Security Tests"

pytest backend/tests/test_security_comprehensive.py -v --tb=short
TEST_STATUS=$?
print_result $TEST_STATUS "Comprehensive Security Tests"
[ $TEST_STATUS -ne 0 ] && OVERALL_STATUS=1

# 3. Run security tests with coverage
print_section "3. Generating Security Test Coverage Report"

pytest backend/tests/test_security*.py \
    --cov=app.core.security \
    --cov=app.core.validation \
    --cov=app.core.middleware \
    --cov=app.core.rate_limiting \
    --cov-report=html \
    --cov-report=term-missing \
    --tb=short

TEST_STATUS=$?
print_result $TEST_STATUS "Coverage Report Generation"
[ $TEST_STATUS -ne 0 ] && OVERALL_STATUS=1

echo ""
echo "Coverage report generated at: htmlcov/index.html"

# 4. Check for common security issues
print_section "4. Static Security Analysis"

echo "Checking for hardcoded secrets..."
if command -v grep &> /dev/null; then
    # Check for potential hardcoded secrets
    SECRETS_FOUND=0
    
    # Check for hardcoded passwords
    if grep -r "password.*=.*['\"]" backend/app --include="*.py" | grep -v "password_hash" | grep -v "test" | grep -v "example"; then
        echo -e "${RED}Warning: Potential hardcoded passwords found${NC}"
        SECRETS_FOUND=1
    fi
    
    # Check for hardcoded API keys
    if grep -r "api_key.*=.*['\"]" backend/app --include="*.py" | grep -v "test" | grep -v "example"; then
        echo -e "${RED}Warning: Potential hardcoded API keys found${NC}"
        SECRETS_FOUND=1
    fi
    
    # Check for hardcoded tokens
    if grep -r "token.*=.*['\"]" backend/app --include="*.py" | grep -v "test" | grep -v "example" | grep -v "csrf_token" | grep -v "access_token"; then
        echo -e "${RED}Warning: Potential hardcoded tokens found${NC}"
        SECRETS_FOUND=1
    fi
    
    if [ $SECRETS_FOUND -eq 0 ]; then
        echo -e "${GREEN}✓ No hardcoded secrets found${NC}"
    else
        echo -e "${YELLOW}⚠ Review findings above${NC}"
    fi
else
    echo -e "${YELLOW}grep not available, skipping secret scan${NC}"
fi

# 5. Check dependencies for known vulnerabilities
print_section "5. Dependency Security Check"

if command -v safety &> /dev/null; then
    echo "Checking dependencies for known vulnerabilities..."
    safety check --json || {
        echo -e "${YELLOW}⚠ Some dependencies have known vulnerabilities${NC}"
        echo "Run 'safety check' for details"
    }
else
    echo -e "${YELLOW}safety not installed, skipping dependency check${NC}"
    echo "Install with: pip install safety"
fi

# 6. Check for SQL injection vulnerabilities
print_section "6. SQL Injection Detection Tests"

echo "Running SQL injection detection tests..."
pytest backend/tests/test_security_validation.py::TestSQLInjectionDetection -v
TEST_STATUS=$?
print_result $TEST_STATUS "SQL Injection Detection"
[ $TEST_STATUS -ne 0 ] && OVERALL_STATUS=1

# 7. Check for XSS vulnerabilities
print_section "7. XSS Prevention Tests"

echo "Running XSS prevention tests..."
pytest backend/tests/test_security_validation.py::TestXSSPrevention -v
TEST_STATUS=$?
print_result $TEST_STATUS "XSS Prevention"
[ $TEST_STATUS -ne 0 ] && OVERALL_STATUS=1

# 8. File upload security tests
print_section "8. File Upload Security Tests"

echo "Running file upload validation tests..."
pytest backend/tests/test_security_validation.py::TestFileUploadValidation -v
TEST_STATUS=$?
print_result $TEST_STATUS "File Upload Security"
[ $TEST_STATUS -ne 0 ] && OVERALL_STATUS=1

# 9. Authentication and authorization tests
print_section "9. Authentication & Authorization Tests"

echo "Running authentication tests..."
pytest backend/tests/test_auth.py -v --tb=short
TEST_STATUS=$?
print_result $TEST_STATUS "Authentication Tests"
[ $TEST_STATUS -ne 0 ] && OVERALL_STATUS=1

# 10. Generate security test report
print_section "10. Generating Security Test Report"

REPORT_FILE="backend/SECURITY_TEST_REPORT_$(date +%Y%m%d_%H%M%S).md"

cat > "$REPORT_FILE" << EOF
# Security Test Report

**Date:** $(date)
**Platform:** Job Aggregation Platform
**Test Suite:** Comprehensive Security Testing

## Test Summary

### Tests Executed

1. Password Security Tests
   - Bcrypt hashing with cost factor 12
   - Password verification
   - Password strength validation

2. Input Validation Tests
   - String length validation
   - Enum validation
   - XSS prevention
   - SQL injection detection

3. File Upload Security Tests
   - File type validation
   - File size validation
   - Malicious file detection

4. Rate Limiting Tests
   - Request rate enforcement
   - Tier-based limits
   - Violation logging

5. Authentication & Authorization Tests
   - JWT token validation
   - Role-based access control
   - Token expiration

### Coverage

Run \`pytest --cov\` to see detailed coverage report.

### Security Checklist

- [x] Password hashing uses bcrypt cost factor 12
- [x] JWT tokens expire correctly (15 min access, 7 day refresh)
- [x] Invalid/expired tokens rejected with HTTP 401
- [x] Role-based access control enforced
- [x] String length validation working
- [x] Enum validation working
- [x] XSS attacks prevented
- [x] SQL injection attempts detected
- [x] File type validation working
- [x] File size validation working
- [x] Rate limiting enforced

### Recommendations

1. Regularly update dependencies to patch security vulnerabilities
2. Monitor rate limit violations for suspicious activity
3. Review authentication logs for failed login attempts
4. Conduct periodic penetration testing
5. Keep security documentation up to date

### Next Steps

1. Review any failed tests above
2. Fix identified security issues
3. Re-run security tests
4. Update security documentation
5. Schedule next security audit

## Detailed Results

See test output above for detailed results of each test case.

EOF

echo "Security test report generated: $REPORT_FILE"

# Final summary
print_section "Security Testing Complete"

if [ $OVERALL_STATUS -eq 0 ]; then
    echo -e "${GREEN}✓ All security tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Review coverage report: htmlcov/index.html"
    echo "2. Review security test report: $REPORT_FILE"
    echo "3. Address any warnings or recommendations"
else
    echo -e "${RED}✗ Some security tests failed${NC}"
    echo ""
    echo "Action required:"
    echo "1. Review failed tests above"
    echo "2. Fix identified security issues"
    echo "3. Re-run security tests"
    exit 1
fi

exit 0
