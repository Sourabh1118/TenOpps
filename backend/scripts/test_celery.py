#!/usr/bin/env python3
"""
Test script to verify Celery configuration and connectivity.

This script tests:
1. Celery app initialization
2. Redis broker connection
3. Redis result backend connection
4. Task execution
5. Task routing
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.tasks.celery_app import celery_app, debug_task
from app.core.logging import logger


def test_celery_config():
    """Test Celery configuration."""
    print("\n" + "="*60)
    print("Testing Celery Configuration")
    print("="*60 + "\n")
    
    # Test 1: Check Celery app initialization
    print("1. Checking Celery app initialization...")
    try:
        assert celery_app is not None
        print("   ✓ Celery app initialized successfully")
        print(f"   - App name: {celery_app.main}")
        print(f"   - Broker: {celery_app.conf.broker_url}")
        print(f"   - Backend: {celery_app.conf.result_backend}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    # Test 2: Check broker connection
    print("\n2. Checking Redis broker connection...")
    try:
        celery_app.connection().ensure_connection(max_retries=3)
        print("   ✓ Broker connection successful")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        print("   Make sure Redis is running and CELERY_BROKER_URL is correct")
        return False
    
    # Test 3: Check task queues configuration
    print("\n3. Checking task queues configuration...")
    try:
        queues = celery_app.conf.task_queues
        print(f"   ✓ {len(queues)} queues configured:")
        for queue in queues:
            print(f"     - {queue.name} (priority: {queue.queue_arguments.get('x-max-priority', 'N/A')})")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    # Test 4: Check task routing
    print("\n4. Checking task routing configuration...")
    try:
        routes = celery_app.conf.task_routes
        print(f"   ✓ {len(routes)} task routes configured")
        for task_name, route_config in list(routes.items())[:3]:
            print(f"     - {task_name.split('.')[-1]}: queue={route_config['queue']}, priority={route_config['priority']}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    # Test 5: Check Beat schedule
    print("\n5. Checking Celery Beat schedule...")
    try:
        schedule = celery_app.conf.beat_schedule
        print(f"   ✓ {len(schedule)} periodic tasks scheduled:")
        for task_name, task_config in list(schedule.items())[:3]:
            print(f"     - {task_name}: {task_config['task'].split('.')[-1]}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    # Test 6: Check registered tasks
    print("\n6. Checking registered tasks...")
    try:
        tasks = [task for task in celery_app.tasks.keys() if task.startswith('app.tasks')]
        print(f"   ✓ {len(tasks)} tasks registered:")
        for task in tasks[:5]:
            print(f"     - {task}")
        if len(tasks) > 5:
            print(f"     ... and {len(tasks) - 5} more")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False
    
    print("\n" + "="*60)
    print("All Celery configuration tests passed! ✓")
    print("="*60 + "\n")
    
    print("Next steps:")
    print("1. Start a Celery worker:")
    print("   ./scripts/run_celery_worker.sh")
    print("\n2. Start Celery Beat scheduler:")
    print("   ./scripts/run_celery_beat.sh")
    print("\n3. (Optional) Start Celery Flower for monitoring:")
    print("   ./scripts/run_celery_flower.sh")
    print("\n4. Test task execution:")
    print("   python scripts/test_celery_task.py")
    
    return True


def test_task_execution():
    """Test task execution (requires running worker)."""
    print("\n" + "="*60)
    print("Testing Task Execution")
    print("="*60 + "\n")
    
    print("Note: This test requires a running Celery worker.")
    print("Start a worker with: ./scripts/run_celery_worker.sh\n")
    
    try:
        # Send debug task
        print("Sending debug task...")
        result = debug_task.apply_async()
        print(f"   Task ID: {result.id}")
        print(f"   Task state: {result.state}")
        
        # Wait for result (with timeout)
        print("   Waiting for result (timeout: 10s)...")
        task_result = result.get(timeout=10)
        print(f"   ✓ Task completed successfully!")
        print(f"   Result: {task_result}")
        
        return True
    except Exception as e:
        print(f"   ✗ Task execution failed: {e}")
        print("   Make sure a Celery worker is running")
        return False


if __name__ == "__main__":
    # Test configuration
    config_ok = test_celery_config()
    
    if not config_ok:
        sys.exit(1)
    
    # Ask if user wants to test task execution
    print("\nDo you want to test task execution? (requires running worker)")
    response = input("Enter 'yes' to test task execution, or press Enter to skip: ")
    
    if response.lower() in ['yes', 'y']:
        test_task_execution()
    
    sys.exit(0)
