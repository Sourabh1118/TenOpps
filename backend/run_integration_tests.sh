#!/bin/bash

# Script to run integration tests for Job Aggregation Platform
# This script sets up the test database and runs the integration tests

set -e

echo "========================================="
echo "Integration Tests Setup and Execution"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Database configuration
DB_USER="${POSTGRES_USER:-postgres}"
DB_NAME="job_platform_test"
TEST_DB_URL="postgresql://${DB_USER}@localhost:5432/${DB_NAME}"

echo -e "${YELLOW}Step 1: Checking PostgreSQL service...${NC}"
if ! systemctl is-active --quiet postgresql; then
    echo -e "${RED}PostgreSQL is not running. Please start it first:${NC}"
    echo "  sudo systemctl start postgresql"
    exit 1
fi
echo -e "${GREEN}✓ PostgreSQL is running${NC}"
echo ""

echo -e "${YELLOW}Step 2: Creating test database...${NC}"
# Drop existing test database if it exists
sudo -u postgres psql -c "DROP DATABASE IF EXISTS ${DB_NAME};" 2>/dev/null || true

# Create test database
sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME};" 2>/dev/null
echo -e "${GREEN}✓ Test database created: ${DB_NAME}${NC}"
echo ""

echo -e "${YELLOW}Step 3: Running database migrations...${NC}"
# Set environment variables for migrations
export DATABASE_URL="${TEST_DB_URL}"
export SECRET_KEY="test-secret-key"
export JWT_SECRET_KEY="test-jwt-secret"
export REDIS_URL="redis://localhost:6379/0"
export CELERY_BROKER_URL="redis://localhost:6379/0"
export CELERY_RESULT_BACKEND="redis://localhost:6379/0"
export LINKEDIN_RSS_URLS=""
export CORS_ORIGINS="http://localhost:3000"

# Run migrations
alembic upgrade head
echo -e "${GREEN}✓ Migrations completed${NC}"
echo ""

echo -e "${YELLOW}Step 4: Running integration tests...${NC}"
echo ""

# Run the integration tests
TEST_DATABASE_URL="${TEST_DB_URL}" python -m pytest tests/test_integration.py -v --tb=short

TEST_EXIT_CODE=$?

echo ""
echo -e "${YELLOW}Step 5: Cleanup...${NC}"
# Drop test database
sudo -u postgres psql -c "DROP DATABASE IF EXISTS ${DB_NAME};" 2>/dev/null || true
echo -e "${GREEN}✓ Test database cleaned up${NC}"
echo ""

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}✓ All integration tests passed!${NC}"
    echo -e "${GREEN}=========================================${NC}"
else
    echo -e "${RED}=========================================${NC}"
    echo -e "${RED}✗ Some integration tests failed${NC}"
    echo -e "${RED}=========================================${NC}"
    exit $TEST_EXIT_CODE
fi
