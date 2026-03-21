#!/usr/bin/env python3
"""
Simple script to test database connection and configuration.

This script verifies that the database setup is working correctly
without requiring pytest or other test dependencies.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.logging import setup_logging, get_logger
from app.db import check_db_health, get_db_info, get_db_session
from sqlalchemy import text

# Setup logging
setup_logging()
logger = get_logger(__name__)


def test_connection():
    """Test basic database connection."""
    logger.info("Testing database connection...")
    
    if not check_db_health():
        logger.error("❌ Database health check failed")
        return False
    
    logger.info("✓ Database health check passed")
    return True


def test_pool_configuration():
    """Test connection pool configuration."""
    logger.info("Testing connection pool configuration...")
    
    db_info = get_db_info()
    logger.info(f"Pool configuration: {db_info}")
    
    if db_info.get("pool_size", 0) < 5:
        logger.error("❌ Pool size is less than 5")
        return False
    
    logger.info("✓ Connection pool configured correctly")
    return True


def test_session_creation():
    """Test session creation and query execution."""
    logger.info("Testing session creation and queries...")
    
    try:
        db = get_db_session()
        
        # Execute a simple query
        result = db.execute(text("SELECT 1 as num, 'test' as text"))
        row = result.fetchone()
        
        if row is None or row[0] != 1 or row[1] != "test":
            logger.error("❌ Query execution failed")
            db.close()
            return False
        
        logger.info("✓ Session creation and query execution successful")
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Session test failed: {e}")
        return False


def test_multiple_sessions():
    """Test multiple concurrent sessions."""
    logger.info("Testing multiple concurrent sessions...")
    
    try:
        sessions = []
        for i in range(3):
            db = get_db_session()
            result = db.execute(text(f"SELECT {i+1}"))
            value = result.scalar()
            
            if value != i + 1:
                logger.error(f"❌ Session {i+1} query failed")
                for s in sessions:
                    s.close()
                db.close()
                return False
            
            sessions.append(db)
        
        # Close all sessions
        for db in sessions:
            db.close()
        
        logger.info("✓ Multiple concurrent sessions work correctly")
        return True
        
    except Exception as e:
        logger.error(f"❌ Multiple sessions test failed: {e}")
        return False


def main():
    """Run all database tests."""
    logger.info("=" * 60)
    logger.info("Database Connection Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Connection Health", test_connection),
        ("Pool Configuration", test_pool_configuration),
        ("Session Creation", test_session_creation),
        ("Multiple Sessions", test_multiple_sessions),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\nRunning: {test_name}")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"❌ Test '{test_name}' raised exception: {e}")
            failed += 1
    
    logger.info("\n" + "=" * 60)
    logger.info(f"Test Results: {passed} passed, {failed} failed")
    logger.info("=" * 60)
    
    if failed > 0:
        logger.error("\n⚠️  Some tests failed. Please check your database configuration.")
        sys.exit(1)
    else:
        logger.info("\n✅ All database tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
