# Security Quick Reference Guide

## For Developers: How to Use Security Features

### 1. Input Validation

**All API endpoints automatically validate using Pydantic models.**

```python
from pydantic import BaseModel, Field

class JobCreateRequest(BaseModel):
    title: str = Field(..., min_length=10, max_length=200)
    description: str = Field(..., min_length=50, max_length=5000)
```

**Custom validation:**

```python
from app.core.validation import validate_enum_value, validate_string_length

# Validate enum
is_valid, error = validate_enum_value(
    value='full_time',
    allowed_values=['full_time', 'part_time'],
    field_name='job_type'
)

# Validate string length
is_valid, error = validate_string_length(
    value='Hello',
    field_name='title',
    min_length=3,
    max_length=100
)
```

---

### 2. XSS Prevention

**Always sanitize HTML content before storing:**

```python
from app.core.validation import sanitize_html

# Sanitize job description
clean_description = sanitize_html(job_data.description)

# Store sanitized content
job.description = clean_description
```

**Allowed tags:** `<p>`, `<br>`, `<ul>`, `<li>`, `<strong>`, `<em>`, `<b>`, `<i>`, `<u>`, `<h3>`, `<h4>`

---

### 3. SQL Injection Prevention

**Always use SQLAlchemy ORM (never concatenate SQL):**

```python
# ✅ GOOD - Parameterized query
jobs = db.query(Job).filter(Job.title == user_input).all()

# ❌ BAD - String concatenation
query = f"SELECT * FROM jobs WHERE title = '{user_input}'"
```

**Monitor for SQL injection attempts:**

```python
from app.core.validation import detect_sql_injection_attempt
from app.core.logging import get_logger

logger = get_logger(__name__)

if detect_sql_injection_attempt(user_input):
    logger.warning(f"SQL injection attempt: {user_input}")
```

---

### 4. HTTPS and Security Headers

**Automatically applied to all responses via middleware.**

No code changes needed. Headers added:
- `Strict-Transport-Security` (production only)
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy`

---

### 5. CSRF Protection

**Client-side flow:**

```javascript
// 1. Get CSRF token after authentication
const response = await fetch('/api/csrf-token', {
  headers: {
    'Authorization': `Bearer ${jwtToken}`
  }
});
const { csrf_token } = await response.json();

// 2. Include CSRF token in state-changing requests
await fetch('/api/jobs/direct', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${jwtToken}`,
    'X-CSRF-Token': csrf_token,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(jobData)
});
```

**Server-side (automatic):**
- CSRF middleware validates tokens automatically
- Exempt paths: `/api/auth/*`, `/health`, `/docs`
- Development mode: CSRF disabled when `DEBUG=True`

---

### 6. File Upload Validation

**Validate resume uploads:**

```python
from app.services.file_validation import validate_file_upload

# Validate uploaded file
is_valid, error = validate_file_upload(
    filename=file.filename,
    file_content=await file.read(),
    max_size_mb=5
)

if not is_valid:
    raise HTTPException(status_code=400, detail=error)
```

**Allowed file types:** PDF, DOC, DOCX (max 5MB)

---

### 7. Error Message Sanitization

**Automatic in production:**

```python
# Development: Full error details
"Database connection failed: password incorrect"

# Production: Sanitized message
"An internal error occurred. Please try again later."
```

**Manual sanitization:**

```python
from app.core.validation import sanitize_error_message
from app.core.config import settings

is_production = settings.APP_ENV == "production"
safe_message = sanitize_error_message(error_str, is_production)
```

---

## Common Patterns

### Creating a New API Endpoint

```python
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.dependencies import get_current_employer
from app.core.validation import sanitize_html
from app.schemas.job import JobCreateRequest

router = APIRouter()

@router.post("/jobs")
async def create_job(
    job_data: JobCreateRequest,  # ✅ Automatic validation
    employer: TokenData = Depends(get_current_employer),  # ✅ Authentication
    db: Session = Depends(get_db)
):
    # ✅ Sanitize HTML
    clean_description = sanitize_html(job_data.description)
    
    # ✅ Use ORM (no SQL injection)
    job = Job(
        title=job_data.title,
        description=clean_description,
        employer_id=employer.user_id
    )
    
    db.add(job)
    db.commit()
    
    return {"job_id": job.id}
```

### Handling File Uploads

```python
from fastapi import UploadFile, File
from app.services.file_validation import validate_file_upload

@router.post("/applications")
async def submit_application(
    resume: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Read file content
    content = await resume.read()
    
    # ✅ Validate file
    is_valid, error = validate_file_upload(
        filename=resume.filename,
        file_content=content
    )
    
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    # Process file...
```

---

## Testing Security Features

### Test XSS Prevention

```python
def test_xss_prevention():
    malicious = '<script>alert("XSS")</script><p>Safe</p>'
    clean = sanitize_html(malicious)
    
    assert '<script>' not in clean
    assert '<p>Safe</p>' in clean
```

### Test SQL Injection Detection

```python
def test_sql_injection():
    malicious = "'; DROP TABLE users; --"
    assert detect_sql_injection_attempt(malicious) is True
```

### Test File Validation

```python
def test_file_validation():
    is_valid, error = validate_resume_file('resume.pdf', 1024 * 1024)
    assert is_valid is True
```

---

## Security Checklist for New Features

- [ ] Use Pydantic models for input validation
- [ ] Sanitize HTML content with `sanitize_html()`
- [ ] Use SQLAlchemy ORM (no raw SQL)
- [ ] Validate file uploads if accepting files
- [ ] Add authentication/authorization checks
- [ ] Handle errors with proper sanitization
- [ ] Write security tests
- [ ] Test with malicious inputs
- [ ] Review CSRF token requirements
- [ ] Check CORS configuration

---

## Environment Configuration

### Development

```env
APP_ENV=development
DEBUG=True
# CSRF disabled in debug mode
# Full error details shown
# HTTP allowed
```

### Production

```env
APP_ENV=production
DEBUG=False
# CSRF enabled
# Error messages sanitized
# HTTPS enforced
```

---

## Troubleshooting

### CSRF Token Issues

**Problem:** "CSRF token missing" error

**Solution:**
1. Ensure client requests CSRF token: `GET /api/csrf-token`
2. Include token in header: `X-CSRF-Token: <token>`
3. Check token hasn't expired (1 hour TTL)

### File Upload Rejected

**Problem:** "Invalid file type" error

**Solution:**
1. Check file extension is PDF, DOC, or DOCX
2. Verify file size is under 5MB
3. Ensure file is not corrupted

### XSS Sanitization Too Aggressive

**Problem:** Legitimate HTML tags removed

**Solution:**
1. Check if tag is in allowed list
2. If needed, request addition to allowed tags
3. Consider using plain text instead

---

## Security Contacts

- **Security Issues**: Report to security team
- **Questions**: Check documentation or ask team lead
- **Vulnerabilities**: Follow responsible disclosure process

---

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Pydantic Validation](https://docs.pydantic.dev/latest/concepts/validators/)
- [Bleach Documentation](https://bleach.readthedocs.io/)
