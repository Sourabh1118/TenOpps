#!/bin/bash

# Fix for Alembic ConfigParser interpolation issue with % in DATABASE_URL
# This script will push the fix to GitHub and deploy to server

echo "=== Fixing Alembic env.py and deploying ==="

# Commit and push the fix
git add backend/alembic/env.py
git commit -m "Fix: Alembic ConfigParser interpolation issue with URL-encoded passwords"
git push origin main

echo ""
echo "✓ Fix pushed to GitHub"
echo ""
echo "Now run these commands on your server:"
echo ""
echo "ssh jobplatform@YOUR_SERVER_IP"
echo "cd /home/jobplatform/job-platform"
echo "git pull origin main"
echo "cd backend"
echo "source venv/bin/activate"
echo "alembic upgrade head"
