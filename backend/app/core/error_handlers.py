"""
Global error handlers for FastAPI application.

This module provides centralized error handling to ensure:
- Internal error details are not exposed to users
- Generic error messages for unexpected errors
- Full error details logged server-side
- Appropriate HTTP status codes

Implements Requirements 13.9, 15.6
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError

from app.core.config import settings
from app.core.logging import get_logger
from app.core.validation import sanitize_error_message


logger = get_logger(__name__)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions.
    
    Logs the error and returns appropriate response to client.
    
    Args:
        request: FastAPI request object
        exc: HTTP exception
        
    Returns:
        JSON response with error details
    """
    # Log the error
    logger.warning(
        f"HTTP exception: {exc.status_code}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
            "detail": exc.detail,
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors.
    
    Implements Requirement 13.8: Return HTTP 400 with specific error messages on validation failure.
    
    Args:
        request: FastAPI request object
        exc: Validation error
        
    Returns:
        JSON response with validation error details
    """
    # Extract validation errors
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        errors.append({
            "field": field,
            "message": message,
            "type": error["type"]
        })
    
    # Log validation error
    logger.info(
        "Validation error",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": errors,
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": "Validation error",
            "errors": errors
        }
    )


async def database_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Handle database errors.
    
    Implements Requirements 13.9 and 15.6:
    - Logs full error details server-side
    - Returns generic error message to user
    - Does not expose internal database details
    
    Args:
        request: FastAPI request object
        exc: SQLAlchemy error
        
    Returns:
        JSON response with generic error message
    """
    # Log full error details server-side
    logger.error(
        "Database error",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        },
        exc_info=True
    )
    
    # Return generic error to user
    is_production = settings.APP_ENV == "production"
    error_message = sanitize_error_message(str(exc), is_production)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": error_message if not is_production else "A database error occurred. Please try again later."
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all other unexpected exceptions.
    
    Implements Requirements 13.9 and 15.6:
    - Logs full error details with stack trace
    - Returns generic error message to user
    - Does not expose internal implementation details
    
    Args:
        request: FastAPI request object
        exc: Any exception
        
    Returns:
        JSON response with generic error message
    """
    # Log full error details with stack trace
    logger.error(
        "Unexpected error",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        },
        exc_info=True
    )
    
    # Return generic error to user
    is_production = settings.APP_ENV == "production"
    
    if is_production:
        error_message = "An unexpected error occurred. Please try again later."
    else:
        # In development, provide more details for debugging
        error_message = f"{type(exc).__name__}: {str(exc)}"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": error_message}
    )


def register_error_handlers(app):
    """
    Register all error handlers with the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
