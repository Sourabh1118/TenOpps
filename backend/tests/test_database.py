"""
Tests for database connection and session management.
"""
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import (
    engine,
    SessionLocal,
    get_db,
    get_db_session,
    check_db_health,
    get_db_info,
)


def test_database_connection():
    """Test that database connection is established."""
    assert check_db_health() is True


def test_database_pool_configuration():
    """Test that connection pool is configured correctly."""
    # Check pool size configuration
    assert engine.pool.size() >= 5, "Pool size should be at least 5"
    
    # Get pool info
    db_info = get_db_info()
    assert "pool_size" in db_info
    assert "total_connections" in db_info


def test_session_creation():
    """Test that database sessions can be created."""
    session = SessionLocal()
    assert session is not None
    assert isinstance(session, Session)
    session.close()


def test_get_db_dependency():
    """Test the get_db dependency function."""
    db_generator = get_db()
    db = next(db_generator)
    
    assert db is not None
    assert isinstance(db, Session)
    
    # Test that session can execute queries
    result = db.execute(text("SELECT 1"))
    assert result.scalar() == 1
    
    # Close the generator
    try:
        next(db_generator)
    except StopIteration:
        pass


def test_get_db_session():
    """Test the get_db_session function."""
    db = get_db_session()
    
    assert db is not None
    assert isinstance(db, Session)
    
    # Test that session can execute queries
    result = db.execute(text("SELECT 1"))
    assert result.scalar() == 1
    
    db.close()


def test_database_query_execution():
    """Test that queries can be executed successfully."""
    db = get_db_session()
    
    try:
        # Execute a simple query
        result = db.execute(text("SELECT 1 as num, 'test' as text"))
        row = result.fetchone()
        
        assert row is not None
        assert row[0] == 1
        assert row[1] == "test"
    finally:
        db.close()


def test_connection_pool_reuse():
    """Test that connection pool reuses connections."""
    # Get initial pool info
    initial_info = get_db_info()
    
    # Create and close multiple sessions
    sessions = []
    for _ in range(3):
        db = get_db_session()
        sessions.append(db)
        db.execute(text("SELECT 1"))
    
    # Close all sessions
    for db in sessions:
        db.close()
    
    # Pool should have reused connections
    final_info = get_db_info()
    
    # Total connections should not have grown excessively
    assert final_info["total_connections"] <= initial_info["total_connections"] + 3


def test_session_isolation():
    """Test that sessions are isolated from each other."""
    db1 = get_db_session()
    db2 = get_db_session()
    
    try:
        # Sessions should be different objects
        assert db1 is not db2
        
        # Both should be able to execute queries independently
        result1 = db1.execute(text("SELECT 1"))
        result2 = db2.execute(text("SELECT 2"))
        
        assert result1.scalar() == 1
        assert result2.scalar() == 2
    finally:
        db1.close()
        db2.close()
