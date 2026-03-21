"""
Database session management with SQLAlchemy.

This module provides database connection pooling and session management
for the application. It configures connection pooling with min=5, max=20
connections as specified in requirements.

Implements Requirement 15.3: Log database errors with query context
"""
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.logging import get_logger, log_error_with_context, sanitize_log_data

logger = get_logger(__name__)


# Create database engine with connection pooling
# QueuePool maintains a pool of connections for reuse
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,  # Minimum connections (5)
    max_overflow=settings.DATABASE_MAX_OVERFLOW,  # Additional connections (20)
    pool_pre_ping=True,  # Verify connections before using them
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=settings.DEBUG,  # Log SQL queries in debug mode
)


# Database error logging event listeners (Requirement 15.3)
@event.listens_for(engine, "handle_error")
def handle_db_error(exception_context):
    """
    Log database errors with query context.
    
    Implements Requirement 15.3:
    - Logs database errors with query context
    - Sanitizes sensitive data from logs (Requirement 15.6)
    """
    exception = exception_context.original_exception
    
    # Build context with query information
    context = {
        'error_type': type(exception).__name__,
        'is_disconnect': exception_context.is_disconnect,
    }
    
    # Add statement if available
    if exception_context.statement:
        # Sanitize the statement to remove sensitive data
        statement = str(exception_context.statement)
        # Basic sanitization - remove potential password values
        if 'password' in statement.lower():
            statement = statement[:100] + '... [SANITIZED]'
        context['statement'] = statement
    
    # Add parameters if available (sanitized)
    if exception_context.parameters:
        context['parameters'] = sanitize_log_data(dict(exception_context.parameters))
    
    # Log the error with context
    log_error_with_context(
        logger,
        f"Database error occurred: {str(exception)}",
        error=exception,
        context=context
    )

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    
    Yields a database session and ensures it's closed after use.
    Use this as a FastAPI dependency for route handlers.
    
    Example:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Get a database session for use outside of FastAPI dependencies.
    
    Caller is responsible for closing the session.
    
    Returns:
        Session: SQLAlchemy database session
    """
    return SessionLocal()
