"""
Security validation tests.

This module tests input validation and security features including:
- XSS prevention
- SQL injection detection
- File upload validation
- CSRF token validation
- Error message sanitization

Tests for Task 21.8
"""
import pytest
from app.core.validation import (
    sanitize_html,
    validate_enum_value,
    validate_url,
    validate_file_extension,
    validate_file_size,
    sanitize_error_message,
    detect_sql_injection_attempt,
    validate_resume_file,
)


class TestXSSPrevention:
    """Test XSS prevention with malicious HTML."""
    
    def test_sanitize_script_tag(self):
        """Test that script tags are removed."""
        malicious_html = '<script>alert("XSS")</script><p>Safe content</p>'
        sanitized = sanitize_html(malicious_html)
        
        assert '<script>' not in sanitized
        # bleach strips tags but may leave content, which is fine since it's not executable
        assert '<p>Safe content</p>' in sanitized
    
    def test_sanitize_onclick_attribute(self):
        """Test that onclick attributes are removed."""
        malicious_html = '<p onclick="alert(\'XSS\')">Click me</p>'
        sanitized = sanitize_html(malicious_html)
        
        assert 'onclick' not in sanitized
        assert 'alert' not in sanitized
        assert '<p>Click me</p>' in sanitized
    
    def test_sanitize_javascript_protocol(self):
        """Test that javascript: protocol is removed."""
        malicious_html = '<a href="javascript:alert(\'XSS\')">Link</a>'
        sanitized = sanitize_html(malicious_html)
        
        assert 'javascript:' not in sanitized
        assert 'alert' not in sanitized
    
    def test_sanitize_img_onerror(self):
        """Test that img onerror attributes are removed."""
        malicious_html = '<img src="x" onerror="alert(\'XSS\')">'
        sanitized = sanitize_html(malicious_html)
        
        assert 'onerror' not in sanitized
        assert 'alert' not in sanitized
    
    def test_allow_safe_tags(self):
        """Test that safe formatting tags are preserved."""
        safe_html = '<p>Paragraph</p><strong>Bold</strong><em>Italic</em><ul><li>Item</li></ul>'
        sanitized = sanitize_html(safe_html)
        
        assert '<p>Paragraph</p>' in sanitized
        assert '<strong>Bold</strong>' in sanitized
        assert '<em>Italic</em>' in sanitized
        assert '<ul>' in sanitized
        assert '<li>Item</li>' in sanitized
    
    def test_sanitize_empty_string(self):
        """Test sanitizing empty string."""
        assert sanitize_html('') == ''
        assert sanitize_html(None) == ''
    
    def test_sanitize_nested_malicious_tags(self):
        """Test nested malicious tags are removed."""
        malicious_html = '<div><script>alert("XSS")</script><p>Safe</p></div>'
        sanitized = sanitize_html(malicious_html)
        
        assert '<script>' not in sanitized
        # bleach strips tags but may leave content, which is fine since it's not executable
        # div is not in allowed tags, so it should be stripped
        assert '<div>' not in sanitized


class TestSQLInjectionDetection:
    """Test SQL injection detection."""
    
    def test_detect_drop_table(self):
        """Test detection of DROP TABLE statement."""
        malicious_input = "'; DROP TABLE users; --"
        assert detect_sql_injection_attempt(malicious_input) is True
    
    def test_detect_union_select(self):
        """Test detection of UNION SELECT statement."""
        malicious_input = "1' UNION SELECT * FROM users --"
        assert detect_sql_injection_attempt(malicious_input) is True
    
    def test_detect_or_equals(self):
        """Test detection of OR 1=1 pattern."""
        malicious_input = "admin' OR '1'='1"
        assert detect_sql_injection_attempt(malicious_input) is True
    
    def test_detect_comment_syntax(self):
        """Test detection of SQL comment syntax."""
        malicious_input = "admin'--"
        assert detect_sql_injection_attempt(malicious_input) is True
    
    def test_detect_exec_command(self):
        """Test detection of EXEC command."""
        malicious_input = "'; EXEC xp_cmdshell('dir'); --"
        assert detect_sql_injection_attempt(malicious_input) is True
    
    def test_normal_input_not_detected(self):
        """Test that normal input is not flagged."""
        normal_inputs = [
            "Software Engineer",
            "Python Developer",
            "Senior Backend Developer",
            "Full-time position",
        ]
        
        for input_text in normal_inputs:
            assert detect_sql_injection_attempt(input_text) is False
    
    def test_empty_input(self):
        """Test empty input."""
        assert detect_sql_injection_attempt('') is False
        assert detect_sql_injection_attempt(None) is False


class TestFileUploadValidation:
    """Test file upload validation."""
    
    def test_validate_pdf_extension(self):
        """Test PDF file extension validation."""
        is_valid, error = validate_file_extension('resume.pdf', ['pdf', 'doc', 'docx'])
        assert is_valid is True
        assert error is None
    
    def test_validate_doc_extension(self):
        """Test DOC file extension validation."""
        is_valid, error = validate_file_extension('resume.doc', ['pdf', 'doc', 'docx'])
        assert is_valid is True
        assert error is None
    
    def test_validate_docx_extension(self):
        """Test DOCX file extension validation."""
        is_valid, error = validate_file_extension('resume.docx', ['pdf', 'doc', 'docx'])
        assert is_valid is True
        assert error is None
    
    def test_reject_exe_extension(self):
        """Test rejection of EXE files."""
        is_valid, error = validate_file_extension('malware.exe', ['pdf', 'doc', 'docx'])
        assert is_valid is False
        assert 'Invalid file type' in error
    
    def test_reject_js_extension(self):
        """Test rejection of JS files."""
        is_valid, error = validate_file_extension('script.js', ['pdf', 'doc', 'docx'])
        assert is_valid is False
        assert 'Invalid file type' in error
    
    def test_case_insensitive_extension(self):
        """Test case-insensitive extension validation."""
        is_valid, error = validate_file_extension('resume.PDF', ['pdf', 'doc', 'docx'])
        assert is_valid is True
        assert error is None
    
    def test_validate_file_size_within_limit(self):
        """Test file size within limit."""
        file_size = 3 * 1024 * 1024  # 3MB
        is_valid, error = validate_file_size(file_size, max_size_mb=5)
        assert is_valid is True
        assert error is None
    
    def test_reject_file_size_exceeds_limit(self):
        """Test rejection of file exceeding size limit."""
        file_size = 10 * 1024 * 1024  # 10MB
        is_valid, error = validate_file_size(file_size, max_size_mb=5)
        assert is_valid is False
        assert '5MB' in error
    
    def test_reject_zero_size_file(self):
        """Test rejection of zero-size file."""
        is_valid, error = validate_file_size(0, max_size_mb=5)
        assert is_valid is False
        assert 'greater than 0' in error
    
    def test_validate_resume_file_valid(self):
        """Test complete resume file validation."""
        file_size = 2 * 1024 * 1024  # 2MB
        is_valid, error = validate_resume_file('resume.pdf', file_size)
        assert is_valid is True
        assert error is None
    
    def test_validate_resume_file_invalid_type(self):
        """Test resume validation with invalid file type."""
        file_size = 2 * 1024 * 1024  # 2MB
        is_valid, error = validate_resume_file('resume.txt', file_size)
        assert is_valid is False
        assert 'Invalid file type' in error
    
    def test_validate_resume_file_too_large(self):
        """Test resume validation with file too large."""
        file_size = 10 * 1024 * 1024  # 10MB
        is_valid, error = validate_resume_file('resume.pdf', file_size)
        assert is_valid is False
        assert 'exceeds maximum' in error


class TestURLValidation:
    """Test URL validation."""
    
    def test_validate_https_url(self):
        """Test valid HTTPS URL."""
        is_valid, error = validate_url('https://example.com/job')
        assert is_valid is True
        assert error is None
    
    def test_reject_http_url(self):
        """Test rejection of HTTP URL (HTTPS only by default)."""
        is_valid, error = validate_url('http://example.com/job')
        assert is_valid is False
        assert 'https' in error.lower()
    
    def test_allow_http_with_custom_schemes(self):
        """Test allowing HTTP with custom allowed schemes."""
        is_valid, error = validate_url('http://example.com/job', allowed_schemes=['http', 'https'])
        assert is_valid is True
        assert error is None
    
    def test_reject_javascript_protocol(self):
        """Test rejection of javascript: protocol."""
        is_valid, error = validate_url('javascript:alert(1)')
        assert is_valid is False
        # Either rejected as invalid scheme or detected as suspicious
        assert 'scheme' in error.lower() or 'suspicious' in error.lower()
    
    def test_reject_data_protocol(self):
        """Test rejection of data: protocol."""
        is_valid, error = validate_url('data:text/html,<script>alert(1)</script>')
        assert is_valid is False
        # Either rejected as invalid scheme or detected as suspicious
        assert 'scheme' in error.lower() or 'suspicious' in error.lower()
    
    def test_reject_file_protocol(self):
        """Test rejection of file: protocol."""
        is_valid, error = validate_url('file:///etc/passwd')
        assert is_valid is False
        # Either rejected as invalid scheme or detected as suspicious
        assert 'scheme' in error.lower() or 'suspicious' in error.lower()
    
    def test_reject_url_without_domain(self):
        """Test rejection of URL without domain."""
        is_valid, error = validate_url('https://')
        assert is_valid is False
        assert 'domain' in error.lower()
    
    def test_reject_empty_url(self):
        """Test rejection of empty URL."""
        is_valid, error = validate_url('')
        assert is_valid is False
        assert 'empty' in error.lower()


class TestErrorMessageSanitization:
    """Test error message sanitization."""
    
    def test_sanitize_database_error_production(self):
        """Test sanitization of database error in production."""
        error = "Database connection failed: password incorrect"
        sanitized = sanitize_error_message(error, is_production=True)
        
        assert 'password' not in sanitized.lower()
        assert 'database' not in sanitized.lower()
        assert 'internal error' in sanitized.lower()
    
    def test_sanitize_sql_error_production(self):
        """Test sanitization of SQL error in production."""
        error = "SQL syntax error: SELECT * FROM users WHERE password='secret'"
        sanitized = sanitize_error_message(error, is_production=True)
        
        assert 'sql' not in sanitized.lower()
        assert 'password' not in sanitized.lower()
        assert 'internal error' in sanitized.lower()
    
    def test_sanitize_token_error_production(self):
        """Test sanitization of token error in production."""
        error = "Invalid token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        sanitized = sanitize_error_message(error, is_production=True)
        
        assert 'token' not in sanitized.lower()
        assert 'internal error' in sanitized.lower()
    
    def test_preserve_safe_error_production(self):
        """Test that safe errors are preserved in production."""
        error = "Invalid email format"
        sanitized = sanitize_error_message(error, is_production=True)
        
        assert sanitized == error
    
    def test_preserve_all_errors_development(self):
        """Test that all errors are preserved in development."""
        error = "Database connection failed: password incorrect"
        sanitized = sanitize_error_message(error, is_production=False)
        
        assert sanitized == error
    
    def test_sanitize_long_error_message(self):
        """Test sanitization of very long error messages."""
        error = "A" * 300  # 300 character error
        sanitized = sanitize_error_message(error, is_production=True)
        
        assert len(sanitized) < len(error)
        assert 'contact support' in sanitized.lower()


class TestEnumValidation:
    """Test enum value validation."""
    
    def test_validate_valid_enum(self):
        """Test validation of valid enum value."""
        is_valid, error = validate_enum_value('full_time', ['full_time', 'part_time'], 'job_type')
        assert is_valid is True
        assert error is None
    
    def test_reject_invalid_enum(self):
        """Test rejection of invalid enum value."""
        is_valid, error = validate_enum_value('invalid', ['full_time', 'part_time'], 'job_type')
        assert is_valid is False
        assert 'Invalid job_type' in error
        assert 'full_time' in error
        assert 'part_time' in error


class TestStringLengthValidation:
    """Test string length validation."""
    
    def test_validate_within_range(self):
        """Test validation of string within length range."""
        from app.core.validation import validate_string_length
        
        is_valid, error = validate_string_length('Hello', 'title', min_length=3, max_length=10)
        assert is_valid is True
        assert error is None
    
    def test_reject_too_short(self):
        """Test rejection of string too short."""
        from app.core.validation import validate_string_length
        
        is_valid, error = validate_string_length('Hi', 'title', min_length=3, max_length=10)
        assert is_valid is False
        assert 'at least 3' in error
    
    def test_reject_too_long(self):
        """Test rejection of string too long."""
        from app.core.validation import validate_string_length
        
        is_valid, error = validate_string_length('Hello World!', 'title', min_length=3, max_length=10)
        assert is_valid is False
        assert 'not exceed 10' in error
