"""
Structured logging configuration for the application.

Implements Requirement 15.1: Log all errors with timestamp, context, and stack trace
"""
import logging
import sys
import json
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from pythonjsonlogger import jsonlogger

from app.core.config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter with additional fields.
    
    Implements Requirement 15.1:
    - Includes timestamp in ISO format
    - Includes log level
    - Includes context (app name, environment, logger name)
    - Includes stack trace for exceptions
    """
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO format (Requirement 15.1)
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Add log level (Requirement 15.1)
        log_record['level'] = record.levelname
        
        # Add context (Requirement 15.1)
        log_record['app'] = settings.APP_NAME
        log_record['env'] = settings.APP_ENV
        log_record['logger'] = record.name
        
        # Add stack trace for exceptions (Requirement 15.1)
        if record.exc_info:
            log_record['stack_trace'] = self.formatException(record.exc_info)
        
        # Add extra context if provided
        if hasattr(record, 'context'):
            log_record['context'] = record.context


def setup_logging() -> None:
    """
    Configure application logging based on settings.
    
    Implements Requirement 15.1:
    - Configures JSON format logging for container environments
    - Logs to stdout for container compatibility
    - Includes timestamp, level, context, and stack trace
    """
    
    # Get root logger
    root_logger = logging.getLogger()
    
    # Set log level from settings
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Create console handler (logs to stdout for container environments)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Set formatter based on LOG_FORMAT setting
    if settings.LOG_FORMAT.lower() == "json":
        # JSON format for production/container environments (Requirement 15.1)
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        # Standard text format for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # Log startup message
    root_logger.info(
        "Logging configured",
        extra={
            "log_level": settings.LOG_LEVEL,
            "log_format": settings.LOG_FORMAT,
            "environment": settings.APP_ENV
        }
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)


def log_error_with_context(
    logger: logging.Logger,
    message: str,
    error: Optional[Exception] = None,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an error with full context and stack trace.
    
    Implements Requirement 15.1:
    - Logs error with timestamp (handled by formatter)
    - Includes context information
    - Includes stack trace for exceptions
    
    Args:
        logger: Logger instance to use
        message: Error message
        error: Exception object (optional)
        context: Additional context dictionary (optional)
    """
    extra = {}
    if context:
        extra['context'] = context
    
    if error:
        logger.error(message, exc_info=error, extra=extra)
    else:
        logger.error(message, extra=extra)


def sanitize_log_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize sensitive data from log entries.
    
    Implements Requirement 15.6:
    - Removes passwords, tokens, and other sensitive data from logs
    
    Args:
        data: Dictionary that may contain sensitive data
        
    Returns:
        Sanitized dictionary with sensitive fields masked
    """
    sensitive_keys = {
        'password', 'password_hash', 'token', 'access_token', 
        'refresh_token', 'api_key', 'secret', 'secret_key',
        'stripe_key', 'jwt_secret', 'authorization'
    }
    
    sanitized = {}
    for key, value in data.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            sanitized[key] = '***REDACTED***'
        elif isinstance(value, dict):
            sanitized[key] = sanitize_log_data(value)
        else:
            sanitized[key] = value
    
    return sanitized


# Default logger instance for convenience
logger = get_logger(__name__)
