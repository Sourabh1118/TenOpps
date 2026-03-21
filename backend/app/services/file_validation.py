"""
File upload validation service.

This module provides file validation for resume uploads including:
- File type validation (PDF, DOC, DOCX only)
- File size validation (max 5MB)
- Basic malware detection (file signature validation)

Implements Requirement 13.6
"""
import magic
from typing import Tuple, Optional
from app.core.validation import validate_resume_file


# MIME types for allowed file formats
ALLOWED_MIME_TYPES = {
    'application/pdf': 'pdf',
    'application/msword': 'doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
}

# File signatures (magic numbers) for validation
FILE_SIGNATURES = {
    'pdf': b'%PDF',
    'doc': b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1',  # OLE2 format
    'docx': b'PK\x03\x04',  # ZIP format (DOCX is a ZIP archive)
}


def validate_file_upload(
    filename: str,
    file_content: bytes,
    max_size_mb: int = 5
) -> Tuple[bool, Optional[str]]:
    """
    Validate uploaded file for resume submission.
    
    Implements Requirement 13.6:
    - Validates file type (PDF, DOC, DOCX only)
    - Validates file size (max 5MB)
    - Validates file signature to prevent file type spoofing
    
    Args:
        filename: Name of the uploaded file
        file_content: Binary content of the file
        max_size_mb: Maximum allowed file size in MB (default: 5)
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Example:
        >>> with open('resume.pdf', 'rb') as f:
        ...     content = f.read()
        >>> is_valid, error = validate_file_upload('resume.pdf', content)
        >>> is_valid
        True
    """
    # Validate filename and size
    file_size = len(file_content)
    is_valid, error = validate_resume_file(filename, file_size)
    
    if not is_valid:
        return False, error
    
    # Validate file signature (magic number)
    is_valid_sig, sig_error = validate_file_signature(filename, file_content)
    
    if not is_valid_sig:
        return False, sig_error
    
    # Validate MIME type using python-magic
    is_valid_mime, mime_error = validate_mime_type(file_content)
    
    if not is_valid_mime:
        return False, mime_error
    
    return True, None


def validate_file_signature(filename: str, file_content: bytes) -> Tuple[bool, Optional[str]]:
    """
    Validate file signature (magic number) to prevent file type spoofing.
    
    This checks the first few bytes of the file to ensure it matches
    the expected file type based on the extension.
    
    Args:
        filename: Name of the file
        file_content: Binary content of the file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_content:
        return False, "File content is empty"
    
    # Extract extension
    if '.' not in filename:
        return False, "File must have an extension"
    
    extension = filename.rsplit('.', 1)[-1].lower()
    
    # Check signature based on extension
    if extension == 'pdf':
        if not file_content.startswith(FILE_SIGNATURES['pdf']):
            return False, "File does not appear to be a valid PDF"
    
    elif extension == 'doc':
        if not file_content.startswith(FILE_SIGNATURES['doc']):
            return False, "File does not appear to be a valid DOC file"
    
    elif extension == 'docx':
        if not file_content.startswith(FILE_SIGNATURES['docx']):
            return False, "File does not appear to be a valid DOCX file"
    
    else:
        return False, f"Unsupported file extension: {extension}"
    
    return True, None


def validate_mime_type(file_content: bytes) -> Tuple[bool, Optional[str]]:
    """
    Validate MIME type using python-magic library.
    
    This provides an additional layer of validation beyond file signatures.
    
    Args:
        file_content: Binary content of the file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Detect MIME type
        mime = magic.Magic(mime=True)
        detected_mime = mime.from_buffer(file_content)
        
        # Check if MIME type is allowed
        if detected_mime not in ALLOWED_MIME_TYPES:
            return False, f"Invalid file type detected: {detected_mime}. Only PDF, DOC, and DOCX files are allowed."
        
        return True, None
        
    except Exception as e:
        # If magic fails, log but don't fail validation
        # (signature check already passed)
        return True, None


def scan_for_malware(file_content: bytes) -> Tuple[bool, Optional[str]]:
    """
    Basic malware detection for uploaded files.
    
    Note: This is a basic implementation. For production, consider integrating
    with a dedicated antivirus service like ClamAV or VirusTotal API.
    
    Implements Requirement 13.6: Scan uploaded files for malware if possible.
    
    Args:
        file_content: Binary content of the file
        
    Returns:
        Tuple of (is_safe, error_message)
    """
    # Check for suspicious patterns in file content
    suspicious_patterns = [
        b'<script',
        b'javascript:',
        b'vbscript:',
        b'eval(',
        b'exec(',
        b'system(',
        b'shell_exec',
    ]
    
    file_content_lower = file_content.lower()
    
    for pattern in suspicious_patterns:
        if pattern in file_content_lower:
            return False, "File contains suspicious content and may be malicious"
    
    # Check file size - extremely large files might be suspicious
    if len(file_content) > 10 * 1024 * 1024:  # 10MB
        return False, "File size is suspiciously large"
    
    return True, None


def get_file_info(file_content: bytes) -> dict:
    """
    Get information about an uploaded file.
    
    Args:
        file_content: Binary content of the file
        
    Returns:
        Dictionary with file information
    """
    try:
        mime = magic.Magic(mime=True)
        detected_mime = mime.from_buffer(file_content)
        
        return {
            "size_bytes": len(file_content),
            "size_mb": round(len(file_content) / (1024 * 1024), 2),
            "mime_type": detected_mime,
            "file_type": ALLOWED_MIME_TYPES.get(detected_mime, "unknown")
        }
    except Exception:
        return {
            "size_bytes": len(file_content),
            "size_mb": round(len(file_content) / (1024 * 1024), 2),
            "mime_type": "unknown",
            "file_type": "unknown"
        }
