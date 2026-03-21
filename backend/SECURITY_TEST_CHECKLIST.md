# Security Test Checklist

## Overview

This checklist provides a comprehensive guide for security testing the Job Aggregation Platform. Use this checklist to ensure all security requirements are tested and validated.

**Requirements Covered:** 12.1-12.10, 13.1-13.9, 14.1-14.6

---

## Authentication Testing (Requirements 12.1-12.10)

### Password Security (12.1)
- [ ] Passwords hashed with bcrypt cost factor 12
- [ ] Password hashes are unique (different salt each time)
- [ ] Password verification works correctly
- [ ] Empty passwords rejected
- [ ] Special characters in passwords handled correctly

### Password Strength (12.1)
- [ ] Minimum 8 characters enforced
- [ ] At least one uppercase letter required
- [ ] At least one lowercase letter required
- [ ] At least one digit required
- [ ] At least one special character required
- [ ] Weak passwords rejected during registration

### JWT Token Management (12.3-12.6)
- [ ] Access tokens expire after 15 minutes
- [ ] Refresh tokens expire after 7 days
- [ ] Invalid tokens rejected with HTTP 401
- [ ] Expired tokens rejected with HTTP 401
- [ ] Token type validation working (access vs refresh)
- [ ] Token payload contains correct claims (sub, role, exp)

### Role-Based Access Control (12.7-12.8)
- [ ] Employer endpoints require employer role
- [ ] Admin endpoints require admin role
- [ ] Job seeker cannot access employer endpoints
- [ ] Employer cannot access admin endpoints
- [ ] Unauthenticated users cannot access protected endpoints

### Token Lifecycle (12.9-12.10)
- [ ] Refresh token can generate new access token
- [ ] Logout invalidates refresh token
- [ ] Blacklisted tokens rejected
- [ ] Multiple concurrent sessions supported

---

## Input Validation Testing (Requirements 13.1-13.9)

### String Validation (13.1)
- [ ] Job title length validated (10-200 characters)
- [ ] Company name length validated (2-100 characters)
- [ ] Description length validated (50-5000 characters)
- [ ] Strings too short rejected with HTTP 400
- [ ] Strings too long rejected with HTTP 400
- [ ] Empty strings rejected where required

### Enum Validation (13.1)
- [ ] Invalid job types rejected
- [ ] Invalid experience levels rejected
- [ ] Invalid job statuses rejected
- [ ] Invalid subscription tiers rejected
- [ ] Enum validation errors include allowed values

### Numeric Validation (13.1)
- [ ] Negative salary values rejected
- [ ] Salary min < salary max enforced
- [ ] Invalid numeric formats rejected
- [ ] Numeric ranges validated

---

## XSS Prevention Testing (Requirement 13.2)

### Script Injection
- [ ] `<script>` tags removed from HTML
- [ ] `<script>` tags in job descriptions sanitized
- [ ] `<script>` tags in company descriptions sanitized
- [ ] Inline JavaScript removed

### Event Handler Injection
- [ ] `onclick` attributes removed
- [ ] `onerror` attributes removed
- [ ] `onload` attributes removed
- [ ] All event handlers stripped from HTML

### Protocol Injection
- [ ] `javascript:` protocol removed from links
- [ ] `data:` protocol removed from links
- [ ] `vbscript:` protocol removed from links
- [ ] Only safe protocols allowed (http, https)

### Safe HTML Preservation
- [ ] Paragraph tags (`<p>`) preserved
- [ ] Bold tags (`<strong>`, `<b>`) preserved
- [ ] Italic tags (`<em>`, `<i>`) preserved
- [ ] List tags (`<ul>`, `<ol>`, `<li>`) preserved
- [ ] Heading tags (`<h3>`, `<h4>`) preserved

---

## SQL Injection Prevention Testing (Requirement 13.3)

### SQL Injection Detection
- [ ] DROP TABLE statements detected
- [ ] UNION SELECT statements detected
- [ ] OR 1=1 patterns detected
- [ ] SQL comment syntax (--) detected
- [ ] EXEC commands detected
- [ ] Normal input not flagged as injection

### SQL Injection Protection
- [ ] Search queries use parameterized queries
- [ ] Filter queries use parameterized queries
- [ ] All database queries use ORM (SQLAlchemy)
- [ ] No raw SQL queries with user input
- [ ] SQL injection attempts logged

---

## HTTPS and Security Headers (Requirements 13.4-13.5)

### HTTPS Enforcement (13.4)
- [ ] HTTPS enforced in production
- [ ] HTTP redirects to HTTPS in production
- [ ] HSTS header present in production
- [ ] HSTS max-age set to 1 year

### Security Headers (13.4)
- [ ] X-Content-Type-Options: nosniff
- [ ] X-Frame-Options: DENY
- [ ] X-XSS-Protection: 1; mode=block
- [ ] Content-Security-Policy present
- [ ] Referrer-Policy present
- [ ] Permissions-Policy present

### CSRF Protection (13.5)
- [ ] CSRF tokens required for POST requests
- [ ] CSRF tokens required for PUT requests
- [ ] CSRF tokens required for PATCH requests
- [ ] CSRF tokens required for DELETE requests
- [ ] Invalid CSRF tokens rejected with HTTP 403
- [ ] Missing CSRF tokens rejected with HTTP 403
- [ ] CSRF tokens stored in Redis
- [ ] CSRF tokens expire after 1 hour

---

## File Upload Validation Testing (Requirement 13.6)

### File Type Validation
- [ ] PDF files accepted
- [ ] DOC files accepted
- [ ] DOCX files accepted
- [ ] EXE files rejected
- [ ] JS files rejected
- [ ] PHP files rejected
- [ ] Shell scripts rejected
- [ ] File extension validation case-insensitive

### File Size Validation
- [ ] Files under 5MB accepted
- [ ] Files over 5MB rejected
- [ ] Zero-byte files rejected
- [ ] File size error message includes limit

### Resume File Validation
- [ ] Resume validation combines type and size checks
- [ ] Invalid resume types rejected
- [ ] Oversized resumes rejected
- [ ] Valid resumes accepted

---

## URL Validation Testing (Requirement 13.7)

### URL Format Validation
- [ ] HTTPS URLs accepted
- [ ] HTTP URLs rejected (HTTPS only by default)
- [ ] URLs without scheme rejected
- [ ] URLs without domain rejected
- [ ] Empty URLs rejected

### Protocol Validation
- [ ] javascript: protocol rejected
- [ ] data: protocol rejected
- [ ] file: protocol rejected
- [ ] vbscript: protocol rejected
- [ ] Only allowed protocols accepted

---

## Error Handling Testing (Requirements 13.8-13.9)

### Error Message Sanitization (13.9)
- [ ] Database errors sanitized in production
- [ ] SQL errors sanitized in production
- [ ] Token errors sanitized in production
- [ ] Password errors sanitized in production
- [ ] Stack traces not exposed to users
- [ ] Internal errors return generic messages
- [ ] Safe errors preserved in production
- [ ] All errors preserved in development

### Error Response Codes (13.8)
- [ ] Validation errors return HTTP 400
- [ ] Authentication errors return HTTP 401
- [ ] Authorization errors return HTTP 403
- [ ] Not found errors return HTTP 404
- [ ] Rate limit errors return HTTP 429
- [ ] Server errors return HTTP 500

---

## Rate Limiting Testing (Requirements 14.1-14.6)

### Request Rate Limiting (14.1-14.2)
- [ ] Standard tier limited to 100 requests/minute
- [ ] Free tier limited to 100 requests/minute
- [ ] Basic tier limited to 200 requests/minute
- [ ] Premium tier limited to 500 requests/minute
- [ ] Rate limit exceeded returns HTTP 429
- [ ] Rate limit resets every minute

### Rate Limit Headers (14.4)
- [ ] X-RateLimit-Limit header present
- [ ] X-RateLimit-Remaining header present
- [ ] X-RateLimit-Reset header present
- [ ] Retry-After header present on 429 responses

### Tier-Based Limits (14.5)
- [ ] Premium tier gets higher limits
- [ ] Basic tier gets medium limits
- [ ] Free tier gets standard limits
- [ ] Unauthenticated users get standard limits
- [ ] Tier correctly identified from JWT token

### Violation Logging (14.6)
- [ ] Rate limit violations logged
- [ ] Violation logs include user ID
- [ ] Violation logs include endpoint
- [ ] Violation logs include timestamp
- [ ] Repeated violations trigger alerts
- [ ] Violation logs stored in Redis
- [ ] Violation logs expire after 7 days

---

## Authorization Testing

### Resource Ownership
- [ ] Employers can only view their own jobs
- [ ] Employers can only edit their own jobs
- [ ] Employers can only delete their own jobs
- [ ] Employers can only view applications to their jobs
- [ ] Job seekers can only view their own applications

### Subscription Enforcement
- [ ] Free tier quota enforced (3 posts/month)
- [ ] Basic tier quota enforced (20 posts/month)
- [ ] Premium tier unlimited posts allowed
- [ ] Featured post quota enforced per tier
- [ ] Quota exceeded returns HTTP 403
- [ ] Quota consumption tracked correctly

---

## Session Management Testing

### Token Lifecycle
- [ ] Access tokens expire correctly
- [ ] Refresh tokens expire correctly
- [ ] Expired tokens cannot be used
- [ ] Refresh tokens can be used once
- [ ] Logout invalidates refresh token

### Concurrent Sessions
- [ ] Multiple sessions allowed per user
- [ ] Each session has unique tokens
- [ ] Logout affects only current session
- [ ] Token blacklist working correctly

---

## Integration Testing

### Complete Authentication Flow
- [ ] Registration with strong password succeeds
- [ ] Registration with weak password fails
- [ ] Login with correct credentials succeeds
- [ ] Login with incorrect credentials fails
- [ ] Access token allows access to protected endpoints
- [ ] Expired token denies access
- [ ] Refresh token generates new access token

### Complete Job Posting Flow
- [ ] Job posting with valid data succeeds
- [ ] Job posting with XSS payload sanitized
- [ ] Job posting with SQL injection blocked
- [ ] Job posting respects quota limits
- [ ] Job posting requires authentication
- [ ] Job posting requires employer role

### Complete Application Flow
- [ ] Application with valid resume succeeds
- [ ] Application with invalid file type fails
- [ ] Application with oversized file fails
- [ ] Application requires authentication
- [ ] Application only allowed for direct posts

---

## Penetration Testing

### Manual Testing
- [ ] Attempted authentication bypass
- [ ] Attempted privilege escalation
- [ ] Attempted SQL injection in all inputs
- [ ] Attempted XSS in all inputs
- [ ] Attempted CSRF attacks
- [ ] Attempted rate limit bypass
- [ ] Attempted file upload attacks

### Automated Testing
- [ ] OWASP ZAP scan completed
- [ ] Burp Suite scan completed
- [ ] SQLMap scan completed
- [ ] No critical vulnerabilities found
- [ ] Medium/low vulnerabilities documented

---

## Security Monitoring

### Log Analysis
- [ ] Authentication failures logged
- [ ] Authorization failures logged
- [ ] Rate limit violations logged
- [ ] SQL injection attempts logged
- [ ] XSS attempts logged
- [ ] File upload rejections logged

### Metrics Monitoring
- [ ] Failed login attempts tracked
- [ ] Rate limit violations tracked
- [ ] Suspicious activity alerts configured
- [ ] Security metrics dashboard available

---

## Compliance

### OWASP Top 10
- [ ] A01:2021 - Broken Access Control: Tested
- [ ] A02:2021 - Cryptographic Failures: Tested
- [ ] A03:2021 - Injection: Tested
- [ ] A04:2021 - Insecure Design: Reviewed
- [ ] A05:2021 - Security Misconfiguration: Tested
- [ ] A06:2021 - Vulnerable Components: Checked
- [ ] A07:2021 - Authentication Failures: Tested
- [ ] A08:2021 - Software and Data Integrity: Tested
- [ ] A09:2021 - Security Logging Failures: Tested
- [ ] A10:2021 - Server-Side Request Forgery: Tested

---

## Test Execution

### Automated Tests
```bash
# Run all security tests
./backend/scripts/run_security_tests.sh

# Run specific test suites
pytest backend/tests/test_security.py -v
pytest backend/tests/test_security_validation.py -v
pytest backend/tests/test_security_comprehensive.py -v
pytest backend/tests/test_rate_limiting.py -v

# Run with coverage
pytest backend/tests/test_security*.py --cov --cov-report=html
```

### Manual Tests
- [ ] Test authentication flows manually
- [ ] Test authorization manually
- [ ] Test file uploads manually
- [ ] Test rate limiting manually
- [ ] Test XSS prevention manually
- [ ] Test SQL injection prevention manually

---

## Sign-Off

### Test Completion
- [ ] All automated tests passing
- [ ] All manual tests completed
- [ ] All checklist items verified
- [ ] Security test report generated
- [ ] Coverage report reviewed

### Approval
- **Tester:** _____________________ Date: _______
- **Security Lead:** _____________________ Date: _______
- **Project Manager:** _____________________ Date: _______

---

## Notes

Use this space to document any issues, exceptions, or additional findings:

```
[Add notes here]
```
