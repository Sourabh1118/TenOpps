"""
Pytest configuration and fixtures for tests.

Provides database session fixtures for integration tests.
"""
import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Set test environment variables before importing app modules
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret")
os.environ.setdefault("LINKEDIN_RSS_URLS", "")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

from app.db.base import Base


@pytest.fixture(scope="function")
def db_session():
    """
    Create a test database session for integration tests.
    
    This fixture creates a temporary in-memory SQLite database
    for each test function, ensuring test isolation.
    """
    # Create in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:")
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    # Cleanup
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def pg_db_session():
    """
    Create a test database session using PostgreSQL.
    
    This fixture requires a PostgreSQL database to be available.
    Use this for tests that require PostgreSQL-specific features
    like full-text search.
    
    Set TEST_DATABASE_URL environment variable to use a test database.
    """
    # Try to get PostgreSQL test database URL
    test_db_url = os.environ.get("TEST_DATABASE_URL")
    
    if not test_db_url:
        pytest.skip("PostgreSQL test database not configured. Set TEST_DATABASE_URL environment variable.")
    
    # Create engine
    engine = create_engine(test_db_url)
    
    # Test connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        pytest.skip(f"Cannot connect to PostgreSQL test database: {e}")
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    # Cleanup - drop all data but keep schema
    session.rollback()
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
    session.close()
