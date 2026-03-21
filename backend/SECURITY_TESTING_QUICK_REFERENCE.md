# Security Testing Quick Reference

## Quick Start

```bash
# Run all security tests
./backend/scripts/run_security_tests.sh

# Run specific test category
pytest backend/tests/test_security.py -v                    # Password & JWT
pytest backend/tests/test_security_validation.py -v         # Input validation
pytest backend/tests/test_security_comprehensive.py -v      # Integration
pytest backend/tests/test_rate_limiting.py -v               # Rate limiting
```

---

## Common Test Commands

### Authentication Testing
```bash
# Test password hashing
pytest backend/tests/test_security.py::TestHashPassword -v

# Test JWT tokens
pytest backend/tests/test_security.py::TestPasswordWorkflow -v

# Test login endpoint
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Pass123!"}'
```

### XSS Testing
```bash
# Test XSS prevention
pytest backend/tests/test_security_validation.py::TestXSSPrevention -v

# Manual XSS test
curl -X POST http://localhost:8000/api/jobs/direct \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"description":"<script>alert(1)</script>",...}'
```

### SQL Injection Testing
```bash
# Test SQL injection detection
pytest backend/tests/test_security_validation.py::TestSQLInjectionDetection -v

# Manual SQL injection test
curl "http://localhost:8000/api/jobs/search?query='; DROP TABLE jobs; --"
```

### File Upload Testing
```bash
# Test file validation
pytest backend/tests/test_security_validation.py::TestFileUploadValidation -v

# Manual file upload test
curl -X POST http://localhost:8000/api/applications \
  -H "Authorization: Bearer <token>" \
  -F "resume=@malware.exe" \
  -F "job_id=<job_id>"
```

### Rate Limiting Testing
```bash
# Test rate limiting
pytest backend/tests/test_rate_limiting.py -v

# Manual rate limit test (send 101 requests)
for i in {1..101}; do
  curl -X GET http://localhost:8000/api/jobs/search?query=test
done
```

---

## Security Test Coverage

```bash
# Generate coverage report
pytest backend/tests/test_security*.py \
  --cov=app.core.security \
  --cov=app.core.validation \
  --cov=app.core.middleware \
  --cov=app.core.rate_limiting \
  --cov-report=html

# View coverage
open htmlcov/index.html
```

---

## Requirements Coverage

| Requirement | Test File | Test Class |
|-------------|-----------|------------|
| 12.1 Password Hashing | test_security.py | TestHashPassword |
| 12.2 Password Verification | test_security.py | TestVerifyPassword |
| 12.3-12.6 JWT Tokens | test_security.py | TestPasswordWorkflow |
| 12.7-12.8 RBAC | test_security_comprehensive.py | TestAuthorizationSecurity |
| 13.1 Input Validation | test_security_validation.py | TestStringLengthValidation |
| 13.2 XSS Prevention | test_security_validation.py | TestXSSPrevention |
| 13.3 SQL Injection | test_security_validation.py | TestSQLInjectionDetection |
| 13.4 HTTPS/Headers | test_security_comprehensive.py | TestSecurityHeadersSecurity |
| 13.5 CSRF Protection | test_security_comprehensive.py | TestCSRFProtectionSecurity |
| 13.6 File Upload | test_security_validation.py | TestFileUploadValidation |
| 13.7 URL Validation | test_security_validation.py | TestURLValidation |
| 13.8-13.9 Error Handling | test_security_validation.py | TestErrorMessageSanitization |
| 14.1-14.2 Rate Limiting | test_rate_limiting.py | TestRateLimiting |
| 14.4 Retry-After | test_rate_limiting.py | TestRateLimitHeaders |
| 14.5 Tier Limits | test_rate_limiting.py | TestTierBasedLimits |
| 14.6 Violation Logging | test_rate_limiting.py | TestViolationLogging |

---

## Security Checklist (Quick)

### Authentication ✓
- [x] Bcrypt cost factor 12
- [x] JWT expiration (15 min / 7 days)
- [x] Role-based access control

### Input Validation ✓
- [x] String length validation
- [x] Enum validation
- [x] XSS prevention
- [x] SQL injection detection

### File Security ✓
- [x] File type validation (PDF, DOC, DOCX only)
- [x] File size validation (max 5MB)
- [x] Malicious file rejection

### Rate Limiting ✓
- [x] 100 req/min (standard)
- [x] 500 req/min (premium)
- [x] Retry-After header
- [x] Violation logging

---

## Common Issues & Solutions

### Issue: Tests fail with "Redis connection refused"
**Solution:** Start Redis server
```bash
redis-server
# or
docker run -d -p 6379:6379 redis:7-alpine
```

### Issue: Tests fail with "Database connection error"
**Solution:** Start PostgreSQL and run migrations
```bash
docker-compose up -d postgres
alembic upgrade head
```

### Issue: Import errors in tests
**Solution:** Install test dependencies
```bash
pip install -r requirements.txt
pip install pytest pytest-cov hypothesis
```

### Issue: Coverage report not generated
**Solution:** Install coverage tools
```bash
pip install pytest-cov coverage
```

---

## Security Test Metrics

### Target Metrics
- **Test Coverage:** ≥ 80% for security modules
- **Critical Path Coverage:** ≥ 95%
- **Test Pass Rate:** 100%
- **Security Issues:** 0 critical, 0 high

### Current Status
Run tests to see current metrics:
```bash
./backend/scripts/run_security_tests.sh
```

---

## Penetration Testing Tools

### OWASP ZAP
```bash
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://localhost:8000 \
  -r zap_report.html
```

### SQLMap
```bash
sqlmap -u "http://localhost:8000/api/jobs/search?query=test" \
  --batch --level=5 --risk=3
```

### Burp Suite
1. Configure proxy: localhost:8080
2. Set browser to use proxy
3. Browse application
4. Run active scanner

---

## Security Monitoring

### Check Logs
```bash
# Authentication failures
grep "authentication failed" backend/logs/app.log

# Rate limit violations
grep "rate limit violation" backend/logs/app.log

# SQL injection attempts
grep "sql injection" backend/logs/app.log

# XSS attempts
grep "xss" backend/logs/app.log
```

### Monitor Metrics
```bash
# Check Redis for rate limit data
redis-cli
> KEYS rate_limit:*
> KEYS rate_limit_violations:*
```

---

## Emergency Response

### If Security Issue Found

1. **Immediate Actions**
   ```bash
   # Stop affected service
   docker-compose stop backend
   
   # Block malicious IPs (if applicable)
   # Add to firewall rules
   
   # Revoke compromised tokens
   # Clear Redis token cache
   redis-cli FLUSHDB
   ```

2. **Investigation**
   ```bash
   # Check logs
   tail -f backend/logs/app.log
   
   # Check database
   psql -d jobplatform -c "SELECT * FROM audit_log WHERE created_at > NOW() - INTERVAL '1 hour';"
   ```

3. **Remediation**
   - Patch vulnerability
   - Update security rules
   - Deploy fix
   - Re-run security tests

4. **Post-Incident**
   - Document incident
   - Update security procedures
   - Conduct security review

---

## Resources

- **Security Guide:** `backend/SECURITY_TESTING_GUIDE.md`
- **Test Checklist:** `backend/SECURITY_TEST_CHECKLIST.md`
- **Test Script:** `backend/scripts/run_security_tests.sh`
- **Coverage Report:** `htmlcov/index.html`

---

## Contact

For security issues or questions:
- **Security Team:** security@example.com
- **On-Call:** +1-XXX-XXX-XXXX
- **Incident Response:** incidents@example.com
