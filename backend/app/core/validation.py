"""
Input validation and sanitization utilities.

This module provides comprehensive input validation and sanitization functions
to protect against XSS, SQL injection, and other security threats.

Implements Requirements 13.1, 13.2, 13.8, 13.9
"""
import re
import bleach
from typing import List, Optional, Tuple
from urllib.parse import urlparse


# Allowed HTML tags for job descriptions (safe formatting only)
ALLOWED_TAGS = ['p', 'br', 'ul', 'ol', 'li', 'strong', 'em', 'b', 'i', 'u', 'h3', 'h4']
ALLOWED_ATTRIBUTES = {}  # No attributes allowed for maximum security


def sanitize_html(html_content: str) -> str:
    """
    Sanitize HTML content to prevent XSS attacks.
    
    Implements Requirement 13.2:
    - Uses bleach library to sanitize HTML
    - Strips dangerous tags and attributes
    - Allows only safe formatting tags
    
    Args:
        html_content: Raw HTML content to sanitize
        
    Returns:
        Sanitized HTML content with only safe tags
        
    Example:
        >>> sanitize_html('<script>alert("xss")</script><p>Safe content</p>')
        '<p>Safe content</p>'
    """
    if not html_content:
        return ""
    
    # Clean HTML with bleach
    cleaned = bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True  # Strip disallowed tags instead of escaping
    )
    
    return cleaned


def validate_enum_value(value: str, allowed_values: List[str], field_name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a value is in the allowed enum values.
    
    Implements Requirement 13.1:
    - Validates enum values against allowed values
    - Returns specific error messages
    
    Args:
        value: Value to validate
        allowed_values: List of allowed values
        field_name: Name of the field for error message
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Example:
        >>> validate_enum_value('full_time', ['full_time', 'part_time'], 'job_type')
        (True, None)
    """
    if value not in allowed_values:
        return False, f"Invalid {field_name}. Allowed values: {', '.join(allowed_values)}"
    
    return True, None


def validate_url(url: str, allowed_schemes: Optional[List[str]] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate URL format and protocol.
    
    Implements Requirement 13.7:
    - Validates URL format
    - Validates protocol (HTTPS only by default)
    
    Args:
        url: URL to validate
        allowed_schemes: List of allowed URL schemes (default: ['https'])
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Example:
        >>> validate_url('https://example.com/job')
        (True, None)
        >>> validate_url('javascript:alert(1)')
        (False, 'Invalid URL scheme. Only https is allowed')
    """
    if not url:
        return False, "URL cannot be empty"
    
    if allowed_schemes is None:
        allowed_schemes = ['https']
    
    try:
        parsed = urlparse(url)
        
        if not parsed.scheme:
            return False, "URL must include a scheme (e.g., https://)"
        
        if parsed.scheme not in allowed_schemes:
            return False, f"Invalid URL scheme. Only {', '.join(allowed_schemes)} is allowed"
        
        if not parsed.netloc:
            return False, "URL must include a domain"
        
        # Check for suspicious patterns
        suspicious_patterns = [
            'javascript:',
            'data:',
            'vbscript:',
            'file:',
        ]
        
        url_lower = url.lower()
        for pattern in suspicious_patterns:
            if pattern in url_lower:
                return False, f"URL contains suspicious pattern: {pattern}"
        
        return True, None
        
    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate file extension.
    
    Implements Requirement 13.6:
    - Validates file type by extension
    - Case-insensitive validation
    
    Args:
        filename: Name of the file
        allowed_extensions: List of allowed extensions (e.g., ['pdf', 'doc', 'docx'])
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Example:
        >>> validate_file_extension('resume.pdf', ['pdf', 'doc', 'docx'])
        (True, None)
        >>> validate_file_extension('malware.exe', ['pdf', 'doc', 'docx'])
        (False, 'Invalid file type. Allowed types: pdf, doc, docx')
    """
    if not filename:
        return False, "Filename cannot be empty"
    
    # Extract extension
    if '.' not in filename:
        return False, "File must have an extension"
    
    extension = filename.rsplit('.', 1)[-1].lower()
    
    # Normalize allowed extensions to lowercase
    allowed_extensions_lower = [ext.lower() for ext in allowed_extensions]
    
    if extension not in allowed_extensions_lower:
        return False, f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
    
    return True, None


def validate_file_size(file_size_bytes: int, max_size_mb: int = 5) -> Tuple[bool, Optional[str]]:
    """
    Validate file size.
    
    Implements Requirement 13.6:
    - Validates file size (max 5MB by default)
    
    Args:
        file_size_bytes: File size in bytes
        max_size_mb: Maximum allowed size in megabytes
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Example:
        >>> validate_file_size(1024 * 1024, 5)  # 1MB
        (True, None)
        >>> validate_file_size(10 * 1024 * 1024, 5)  # 10MB
        (False, 'File size exceeds maximum allowed size of 5MB')
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file_size_bytes > max_size_bytes:
        return False, f"File size exceeds maximum allowed size of {max_size_mb}MB"
    
    if file_size_bytes <= 0:
        return False, "File size must be greater than 0"
    
    return True, None


def sanitize_error_message(error_message: str, is_production: bool = True) -> str:
    """
    Sanitize error messages to prevent information disclosure.
    
    Implements Requirements 13.9 and 15.6:
    - Ensures internal error details are not exposed to users
    - Returns generic error messages for unexpected errors in production
    
    Args:
        error_message: Original error message
        is_production: Whether running in production environment
        
    Returns:
        Sanitized error message safe for user display
        
    Example:
        >>> sanitize_error_message('Database connection failed: password incorrect', True)
        'An internal error occurred. Please try again later.'
    """
    if not is_production:
        # In development, return full error for debugging
        return error_message
    
    # Patterns that indicate internal errors that should not be exposed
    sensitive_patterns = [
        'database',
        'sql',
        'password',
        'token',
        'secret',
        'key',
        'connection',
        'internal',
        'traceback',
        'exception',
        'stack',
    ]
    
    error_lower = error_message.lower()
    
    for pattern in sensitive_patterns:
        if pattern in error_lower:
            return "An internal error occurred. Please try again later."
    
    # If error message is too long, it might contain sensitive info
    if len(error_message) > 200:
        return "An error occurred. Please contact support if the problem persists."
    
    # Return original message if it seems safe
    return error_message


def validate_string_length(
    value: str,
    field_name: str,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None
) -> Tuple[bool, Optional[str]]:
    """
    Validate string length constraints.
    
    Implements Requirement 13.1:
    - Validates string length constraints
    - Returns specific error messages
    
    Args:
        value: String value to validate
        field_name: Name of the field for error message
        min_length: Minimum allowed length (optional)
        max_length: Maximum allowed length (optional)
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Example:
        >>> validate_string_length('Hello', 'title', min_length=3, max_length=10)
        (True, None)
    """
    if value is None:
        return False, f"{field_name} cannot be None"
    
    length = len(value)
    
    if min_length is not None and length < min_length:
        return False, f"{field_name} must be at least {min_length} characters"
    
    if max_length is not None and length > max_length:
        return False, f"{field_name} must not exceed {max_length} characters"
    
    return True, None


def detect_sql_injection_attempt(value: str) -> bool:
    """
    Detect potential SQL injection attempts in user input.
    
    Note: This is a defense-in-depth measure. The primary protection
    against SQL injection is using parameterized queries (SQLAlchemy ORM).
    
    Implements Requirement 13.3:
    - Detects common SQL injection patterns
    - Used for logging and monitoring
    
    Args:
        value: User input to check
        
    Returns:
        True if potential SQL injection detected, False otherwise
        
    Example:
        >>> detect_sql_injection_attempt("'; DROP TABLE users; --")
        True
        >>> detect_sql_injection_attempt("Normal job title")
        False
    """
    if not value:
        return False
    
    # Common SQL injection patterns
    sql_patterns = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|#|/\*|\*/)",
        r"(\bOR\b.*=.*)",
        r"(\bAND\b.*=.*)",
        r"(;.*\b(DROP|DELETE|UPDATE|INSERT)\b)",
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bEXEC\b.*\()",
        r"(xp_cmdshell)",
    ]
    
    value_upper = value.upper()
    
    for pattern in sql_patterns:
        if re.search(pattern, value_upper, re.IGNORECASE):
            return True
    
    return False


def validate_resume_file(filename: str, file_size_bytes: int) -> Tuple[bool, Optional[str]]:
    """
    Validate resume file upload.
    
    Implements Requirement 13.6:
    - Validates file type (PDF, DOC, DOCX only)
    - Validates file size (max 5MB)
    
    Args:
        filename: Name of the uploaded file
        file_size_bytes: Size of the file in bytes
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Example:
        >>> validate_resume_file('resume.pdf', 1024 * 1024)
        (True, None)
    """
    # Validate file extension
    is_valid_ext, ext_error = validate_file_extension(
        filename,
        ['pdf', 'doc', 'docx']
    )
    
    if not is_valid_ext:
        return False, ext_error
    
    # Validate file size
    is_valid_size, size_error = validate_file_size(file_size_bytes, max_size_mb=5)
    
    if not is_valid_size:
        return False, size_error
    
    return True, None
