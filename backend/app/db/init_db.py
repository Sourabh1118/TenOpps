"""
Database initialization utilities.

This module provides functions to initialize the database,
create tables, and perform health checks.
"""
import logging
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.db.session import engine
from app.db.base import Base

logger = logging.getLogger(__name__)


def init_db() -> None:
    """
    Initialize the database by creating all tables.
    
    This function creates all tables defined in SQLAlchemy models
    that inherit from Base. It's idempotent - safe to call multiple times.
    
    Note: In production, use Alembic migrations instead of this function.
    This is primarily for development and testing.
    """
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def drop_db() -> None:
    """
    Drop all database tables.
    
    WARNING: This will delete all data in the database.
    Use only in development/testing environments.
    """
    try:
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise


def check_db_health() -> bool:
    """
    Check database connection health.
    
    Attempts to execute a simple query to verify the database
    connection is working properly.
    
    Returns:
        bool: True if database is healthy, False otherwise
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database health check passed")
        return True
    except OperationalError as e:
        logger.error(f"Database health check failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during database health check: {e}")
        return False


def get_db_info() -> dict:
    """
    Get database connection information.
    
    Returns:
        dict: Database connection details (without sensitive info)
    """
    return {
        "pool_size": engine.pool.size(),
        "checked_in_connections": engine.pool.checkedin(),
        "checked_out_connections": engine.pool.checkedout(),
        "overflow": engine.pool.overflow(),
        "total_connections": engine.pool.size() + engine.pool.overflow(),
    }
