#!/bin/bash

# Test Admin Login - Quick Diagnostic
# This script tests if admin login is working

set -e

echo "🔍 Testing Admin Login..."
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Test 1: Backend Health
echo -e "${YELLOW}Test 1: Backend Health Check${NC}"
HEALTH=$(curl -s https://trusanity.com/api/health 2>&1 || echo "FAILED")
if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Backend is healthy${NC}"
else
    echo -e "${RED}✗ Backend health check failed${NC}"
    echo "Response: $HEALTH"
fi
echo ""

# Test 2: Login API
echo -e "${YELLOW}Test 2: Admin Login API${NC}"
LOGIN_RESPONSE=$(curl -s -X POST https://trusanity.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@trusanity.com",
    "password": "Admin@123"
  }' 2>&1 || echo "FAILED")

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✓ Admin login successful!${NC}"
    echo "Admin account exists and credentials are correct"
else
    echo -e "${RED}✗ Admin login failed${NC}"
    echo "Response: $LOGIN_RESPONSE"
    echo ""
    echo "This means either:"
    echo "  1. Admin account doesn't exist"
    echo "  2. Wrong password"
    echo "  3. Backend issue"
    echo ""
    echo "To create admin account, run:"
    echo "  ./CREATE_ADMIN.sh"
fi
echo ""

# Test 3: Frontend Routes
echo -e "${YELLOW}Test 3: Frontend Routes${NC}"

test_route() {
    local route=$1
    local status=$(curl -s -o /dev/null -w "%{http_code}" https://trusanity.com$route 2>&1)
    if [ "$status" = "200" ] || [ "$status" = "301" ] || [ "$status" = "302" ]; then
        echo -e "${GREEN}✓${NC} $route (HTTP $status)"
    else
        echo -e "${RED}✗${NC} $route (HTTP $status)"
    fi
}

test_route "/login"
test_route "/register"
test_route "/employer/pricing"
test_route "/employer/register"
echo ""

# Test 4: Check for 404 errors
echo -e "${YELLOW}Test 4: Check for Missing Assets${NC}"
GRID_SVG=$(curl -s -o /dev/null -w "%{http_code}" https://trusanity.com/grid.svg 2>&1)
if [ "$GRID_SVG" = "200" ]; then
    echo -e "${GREEN}✓ grid.svg exists${NC}"
else
    echo -e "${YELLOW}⚠ grid.svg not found (HTTP $GRID_SVG)${NC}"
    echo "  This is optional and won't prevent login"
fi
echo ""

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Test Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✅ Admin login is working!${NC}"
    echo ""
    echo "You can now login at:"
    echo "  URL: https://trusanity.com/login"
    echo "  Email: admin@trusanity.com"
    echo "  Password: Admin@123"
    echo ""
    echo "⚠️  IMPORTANT: Use HTTPS, not HTTP!"
else
    echo -e "${RED}❌ Admin login is NOT working${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Create admin account: ./CREATE_ADMIN.sh"
    echo "  2. Deploy missing routes: ./FIX_FRONTEND_DEPLOYMENT.sh"
    echo "  3. Run this test again: ./TEST_ADMIN_LOGIN.sh"
fi
echo ""
