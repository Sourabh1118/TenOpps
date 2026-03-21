# Security Testing Guide

## Overview

This document provides comprehensive security testing procedures for the Job Aggregation Platform. It covers authentication, authorization, input validation, XSS prevention, SQL injection prevention, file upload validation, and rate limiting.

**Related Requirements:** 12.1-12.10, 13.1-13.9, 14.1-14.6

## Table of Contents

1. [Authentication Testing](#authentication-testing)
2. [Authorization Testing](#authorization-testing)
3. [Input Validation Testing](#input-validation-testing)
4. [XSS Prevention Testing](#xss-prevention-testing)
5. [SQL Injection Prevention Testing](#sql-injection-prevention-testing)
6. [File Upload Validation Testing](#file-upload-validation-testing)
7. [Rate Limiting Testing](#rate-limiting-testing)
8. [Security Headers Testing](#security-headers-testing)
9. [CSRF Protection Testing](#csrf-protection-testing)
10. [Automated Security Testing](#automated-security-testing)

---

## Authentication Testing

### Test Cases

#### 1. Password Hashing (Requirement 12.1)

**Test:** Verify bcrypt with cost factor 12
```bash
# Run unit tests
pytest backend/tests/test_security.py::TestHashPassword -v
```

**Manual Verification:**
```python
from app.core.security import hash_password

password = "TestPassword123!"
hashed = hash_password(password)

# Verify bcrypt identifier and cost factor
assert hashed.startswith("$2b$12$") or hashed.startswith("$2a$12$")
```

**Expected Result:** All passwords hashed with bcrypt cost factor 12

---

#### 2. JWT Token Validation (Requirements 12.3, 12.4, 12.5, 12.6)

**Test:** Access token expiration (15 minutes)
```bash
# Test token expiration
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"employer@example.com","password":"SecurePass123!"}'

# Wait 16 minutes, then try to use token
curl -X GET http://localhost:8000/api/jobs/direct \
  -H "Authorization: Bearer <expired_token>"
```

**Expected Result:** HTTP 401 Unauthorized after 15 minutes

---

**Test:** Refresh token expiration (7 days)
```bash
# Use refresh token after 8 days
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<8_day_old_token>"}'
```

**Expected Result:** HTTP 401 Unauthorized after 7 days

---

#### 3. Role-Based Access Control (Requirements 12.7, 12.8)

**Test:** Employer endpoint access
```bash
# Try to access employer endpoint with job seeker token
curl -X GET http://localhost:8000/api/employer/dashboard \
  -H "Authorization: Bearer <job_seeker_token>"
```

**Expected Result:** HTTP 403 Forbidden

---

**Test:** Admin endpoint access
```bash
# Try to access admin endpoint with employer token
curl -X GET http://localhost:8000/api/admin/users \
  -H "Authorization: Bearer <employer_token>"
```

**Expected Result:** HTTP 403 Forbidden

---

## Authorization Testing

### Test Cases

#### 1. Resource Ownership Validation

**Test:** Employer can only access their own jobs
```bash
# Employer A tries to access Employer B's job
curl -X GET http://localhost:8000/api/jobs/<employer_b_job_id> \
  -H "Authorization: Bearer <employer_a_token>"
```

**Expected Result:** HTTP 403 Forbidden or HTTP 404 Not Found

---

**Test:** Employer can only update their own jobs
```bash
# Employer A tries to update Employer B's job
curl -X PUT http://localhost:8000/api/jobs/<employer_b_job_id> \
  -H "Authorization: Bearer <employer_a_token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Updated Title"}'
```

**Expected Result:** HTTP 403 Forbidden

---

#### 2. Subscription Tier Enforcement

**Test:** Free tier quota enforcement
```bash
# Post 4 jobs with free tier account (limit is 3)
for i in {1..4}; do
  curl -X POST http://localhost:8000/api/jobs/direct \
    -H "Authorization: Bearer <free_tier_token>" \
    -H "Content-Type: application/json" \
    -d @job_data.json
done
```

**Expected Result:** First 3 succeed, 4th returns HTTP 403 with quota exceeded message

---

## Input Validation Testing

### Test Cases

#### 1. String Length Validation (Requirement 13.1)

**Test:** Job title length validation
```bash
# Test title too short (< 10 characters)
curl -X POST http://localhost:8000/api/jobs/direct \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Short","company":"Test Corp","location":"NYC","description":"..."}'
```

**Expected Result:** HTTP 400 with validation error

---

**Test:** Job title too long (> 200 characters)
```bash
# Test title too long
curl -X POST http://localhost:8000/api/jobs/direct \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"'$(python -c 'print("A"*201)')'",...}'
```

**Expected Result:** HTTP 400 with validation error

---

#### 2. Enum Validation

**Test:** Invalid job type
```bash
curl -X POST http://localhost:8000/api/jobs/direct \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"job_type":"INVALID_TYPE",...}'
```

**Expected Result:** HTTP 400 with enum validation error

---

## XSS Prevention Testing

### Test Cases

#### 1. Script Tag Injection (Requirement 13.2)

**Test:** Script tag in job description
```bash
curl -X POST http://localhost:8000/api/jobs/direct \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title":"Software Engineer",
    "company":"Test Corp",
    "location":"NYC",
    "description":"<script>alert(\"XSS\")</script><p>Job description</p>"
  }'
```

**Expected Result:** Script tag removed, safe HTML preserved

---

**Test:** Event handler injection
```bash
curl -X POST http://localhost:8000/api/jobs/direct \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "description":"<p onclick=\"alert(1)\">Click me</p>"
  }'
```

**Expected Result:** onclick attribute removed

---

**Test:** JavaScript protocol in links
```bash
curl -X POST http://localhost:8000/api/jobs/direct \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "description":"<a href=\"javascript:alert(1)\">Link</a>"
  }'
```

**Expected Result:** javascript: protocol removed

---

## SQL Injection Prevention Testing

### Test Cases

#### 1. SQL Injection in Search (Requirement 13.3)

**Test:** DROP TABLE injection
```bash
curl -X GET "http://localhost:8000/api/jobs/search?query='; DROP TABLE jobs; --"
```

**Expected Result:** Query treated as literal string, no SQL execution

---

**Test:** UNION SELECT injection
```bash
curl -X GET "http://localhost:8000/api/jobs/search?query=1' UNION SELECT * FROM users --"
```

**Expected Result:** Query treated as literal string, no data leakage

---

**Test:** OR 1=1 injection
```bash
curl -X GET "http://localhost:8000/api/jobs/search?query=admin' OR '1'='1"
```

**Expected Result:** Query treated as literal string, no unauthorized access

---

#### 2. SQL Injection Detection

**Test:** Run detection tests
```bash
pytest backend/tests/test_security_validation.py::TestSQLInjectionDetection -v
```

**Expected Result:** All SQL injection patterns detected

---

## File Upload Validation Testing

### Test Cases

#### 1. File Type Validation (Requirement 13.6)

**Test:** Upload executable file
```bash
# Create malicious file
echo "malicious content" > malware.exe

# Try to upload as resume
curl -X POST http://localhost:8000/api/applications \
  -H "Authorization: Bearer <token>" \
  -F "resume=@malware.exe" \
  -F "job_id=<job_id>"
```

**Expected Result:** HTTP 400 with invalid file type error

---

**Test:** Upload JavaScript file
```bash
echo "alert('xss')" > script.js

curl -X POST http://localhost:8000/api/applications \
  -H "Authorization: Bearer <token>" \
  -F "resume=@script.js" \
  -F "job_id=<job_id>"
```

**Expected Result:** HTTP 400 with invalid file type error

---

**Test:** Valid file types (PDF, DOC, DOCX)
```bash
# Test PDF
curl -X POST http://localhost:8000/api/applications \
  -H "Authorization: Bearer <token>" \
  -F "resume=@resume.pdf" \
  -F "job_id=<job_id>"
```

**Expected Result:** HTTP 200 or 201, file accepted

---

#### 2. File Size Validation (Requirement 13.6)

**Test:** Upload file exceeding 5MB limit
```bash
# Create 10MB file
dd if=/dev/zero of=large_resume.pdf bs=1M count=10

curl -X POST http://localhost:8000/api/applications \
  -H "Authorization: Bearer <token>" \
  -F "resume=@large_resume.pdf" \
  -F "job_id=<job_id>"
```

**Expected Result:** HTTP 400 with file size exceeded error

---

**Test:** Upload zero-byte file
```bash
touch empty.pdf

curl -X POST http://localhost:8000/api/applications \
  -H "Authorization: Bearer <token>" \
  -F "resume=@empty.pdf" \
  -F "job_id=<job_id>"
```

**Expected Result:** HTTP 400 with invalid file size error

---

## Rate Limiting Testing

### Test Cases

#### 1. Request Rate Limiting (Requirements 14.1, 14.2)

**Test:** Exceed 100 requests per minute (standard tier)
```bash
# Send 101 requests in quick succession
for i in {1..101}; do
  curl -X GET http://localhost:8000/api/jobs/search?query=test
done
```

**Expected Result:** First 100 succeed, 101st returns HTTP 429

---

**Test:** Retry-After header (Requirement 14.4)
```bash
# Trigger rate limit
for i in {1..101}; do
  curl -i -X GET http://localhost:8000/api/jobs/search?query=test
done | grep -i "retry-after"
```

**Expected Result:** Retry-After header present in 429 response

---

#### 2. Tier-Based Rate Limits (Requirement 14.5)

**Test:** Premium tier higher limits
```bash
# Send 150 requests with premium tier token
for i in {1..150}; do
  curl -X GET http://localhost:8000/api/jobs/search?query=test \
    -H "Authorization: Bearer <premium_token>"
done
```

**Expected Result:** All 150 requests succeed (premium limit is 500/min)

---

#### 3. Rate Limit Violation Logging (Requirement 14.6)

**Test:** Check violation logs
```bash
# Trigger violations
for i in {1..110}; do
  curl -X GET http://localhost:8000/api/jobs/search?query=test
done

# Check logs
tail -f backend/logs/app.log | grep "Rate limit violation"
```

**Expected Result:** Violations logged with user ID, path, and timestamp

---

## Security Headers Testing

### Test Cases

#### 1. HTTPS Enforcement (Requirement 13.4)

**Test:** Security headers present
```bash
curl -i https://api.example.com/api/jobs/search?query=test
```

**Expected Headers:**
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy: default-src 'self'; ...`

---

## CSRF Protection Testing

### Test Cases

#### 1. CSRF Token Validation (Requirement 13.5)

**Test:** POST without CSRF token
```bash
curl -X POST http://localhost:8000/api/jobs/direct \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d @job_data.json
```

**Expected Result:** HTTP 403 Forbidden (CSRF token missing)

---

**Test:** POST with invalid CSRF token
```bash
curl -X POST http://localhost:8000/api/jobs/direct \
  -H "Authorization: Bearer <token>" \
  -H "X-CSRF-Token: invalid_token" \
  -H "Content-Type: application/json" \
  -d @job_data.json
```

**Expected Result:** HTTP 403 Forbidden (invalid CSRF token)

---

**Test:** POST with valid CSRF token
```bash
# Get CSRF token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Pass123!"}' \
  | jq -r '.csrf_token')

# Use token
curl -X POST http://localhost:8000/api/jobs/direct \
  -H "Authorization: Bearer <access_token>" \
  -H "X-CSRF-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d @job_data.json
```

**Expected Result:** HTTP 200 or 201, request succeeds

---

## Automated Security Testing

### Running All Security Tests

```bash
# Run all security unit tests
pytest backend/tests/test_security.py -v
pytest backend/tests/test_security_validation.py -v
pytest backend/tests/test_rate_limiting.py -v

# Run with coverage
pytest backend/tests/test_security*.py --cov=app.core --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Security Test Checklist

- [ ] Password hashing uses bcrypt cost factor 12
- [ ] JWT tokens expire correctly (15 min access, 7 day refresh)
- [ ] Invalid/expired tokens rejected with HTTP 401
- [ ] Role-based access control enforced
- [ ] Employers can only access their own resources
- [ ] Subscription quotas enforced
- [ ] String length validation working
- [ ] Enum validation working
- [ ] XSS attacks prevented (script tags, event handlers, JS protocols)
- [ ] SQL injection attempts detected and blocked
- [ ] File type validation working (only PDF, DOC, DOCX)
- [ ] File size validation working (max 5MB)
- [ ] Rate limiting enforced (100/min standard, 500/min premium)
- [ ] Retry-After header included in 429 responses
- [ ] Rate limit violations logged
- [ ] Security headers present (HSTS, X-Frame-Options, CSP, etc.)
- [ ] CSRF protection working for state-changing operations
- [ ] Error messages sanitized (no sensitive data exposed)

---

## Penetration Testing Procedures

### Manual Penetration Testing

1. **Authentication Bypass Attempts**
   - Try to access protected endpoints without token
   - Try to forge JWT tokens
   - Try to use expired tokens
   - Try to escalate privileges (job seeker → employer → admin)

2. **Injection Attacks**
   - Test all input fields for SQL injection
   - Test all input fields for XSS
   - Test file uploads for malicious content
   - Test URL parameters for command injection

3. **Authorization Bypass Attempts**
   - Try to access other users' resources
   - Try to modify other users' data
   - Try to delete other users' resources
   - Try to exceed subscription quotas

4. **Session Management**
   - Test token expiration
   - Test token refresh mechanism
   - Test logout functionality
   - Test concurrent sessions

5. **Rate Limiting Bypass Attempts**
   - Try to bypass rate limits with multiple IPs
   - Try to bypass rate limits with multiple accounts
   - Test rate limit reset timing

### Automated Penetration Testing Tools

**OWASP ZAP:**
```bash
# Run ZAP scan
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://localhost:8000 \
  -r zap_report.html
```

**Burp Suite:**
- Configure proxy to intercept requests
- Run active scanner on all endpoints
- Test for common vulnerabilities (OWASP Top 10)

**SQLMap:**
```bash
# Test for SQL injection
sqlmap -u "http://localhost:8000/api/jobs/search?query=test" \
  --batch --level=5 --risk=3
```

---

## Security Monitoring

### Log Analysis

**Check for suspicious activity:**
```bash
# SQL injection attempts
grep -i "sql injection" backend/logs/app.log

# XSS attempts
grep -i "xss" backend/logs/app.log

# Rate limit violations
grep -i "rate limit violation" backend/logs/app.log

# Failed authentication attempts
grep -i "authentication failed" backend/logs/app.log
```

### Metrics to Monitor

1. **Authentication Failures**
   - Failed login attempts per IP
   - Failed login attempts per user
   - Unusual login patterns (time, location)

2. **Rate Limit Violations**
   - Users with repeated violations
   - Endpoints with high violation rates
   - Unusual traffic patterns

3. **Input Validation Failures**
   - SQL injection detection triggers
   - XSS detection triggers
   - File upload rejections

4. **Authorization Failures**
   - Attempts to access unauthorized resources
   - Privilege escalation attempts

---

## Security Incident Response

### Incident Response Procedure

1. **Detection**
   - Monitor logs for suspicious activity
   - Set up alerts for security events
   - Review rate limit violations

2. **Analysis**
   - Identify attack vector
   - Assess impact and scope
   - Determine if data was compromised

3. **Containment**
   - Block malicious IPs
   - Revoke compromised tokens
   - Disable compromised accounts

4. **Eradication**
   - Patch vulnerabilities
   - Update security rules
   - Deploy fixes

5. **Recovery**
   - Restore normal operations
   - Monitor for continued attacks
   - Verify security measures

6. **Post-Incident**
   - Document incident
   - Update security procedures
   - Conduct security review

---

## Security Best Practices

### Development

- Always use parameterized queries (SQLAlchemy ORM)
- Sanitize all user inputs
- Validate all inputs against schemas
- Use HTTPS only in production
- Never log sensitive data (passwords, tokens)
- Keep dependencies updated
- Run security tests in CI/CD pipeline

### Deployment

- Use environment variables for secrets
- Enable security headers
- Configure CORS properly
- Use rate limiting
- Enable CSRF protection
- Monitor security logs
- Regular security audits

### Code Review

- Review all authentication/authorization code
- Review all input validation code
- Review all database queries
- Review all file upload handling
- Review all error handling
- Check for hardcoded secrets
- Verify security headers

---

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
