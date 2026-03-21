#!/usr/bin/env python3
"""
Database initialization script.

This script initializes the database by creating all tables.
Use this for development/testing. In production, use Alembic migrations.

Usage:
    python scripts/init_db.py
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import init_db, check_db_health
from app.core.logging import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


def main():
    """Initialize the database."""
    logger.info("Starting database initialization...")
    
    # Check database connection
    if not check_db_health():
        logger.error("Cannot connect to database. Please check your DATABASE_URL configuration.")
        sys.exit(1)
    
    logger.info("Database connection successful")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
