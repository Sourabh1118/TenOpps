# Admin Dashboard Deployment - Step by Step

## Problem Summary
1. Frontend pm2 process keeps crashing with "port 3000 already in use" error
2. Git conflicts preventing code pull from GitHub
3. Admin dashboard code exists but not deployed to server

## Solution

Run these commands on the server (SSH into 3.110.220.37):

### Option 1: Automated Fix (Recommended)

```bash
# SSH into server
ssh ubuntu@3.110.220.37

# Navigate to project directory
cd /home/jobplatform/job-platform

# Download the fix script (copy from local machine or create manually)
# Then run:
bash FIX_GIT_AND_DEPLOY.sh
```

### Option 2: Manual Fix (Step by Step)

If the automated script doesn't work, follow these manual steps:

#### Step 1: Clean up git conflicts
```bash
cd /home/jobplatform/job-platform

# Remove untracked files blocking merge
rm -f FIX_ADMIN_ON_SERVER.sh
rm -f frontend/app/employer/pricing/page.tsx
rm -f frontend/app/employer/register/page.tsx
rm -f frontend/app/register/page.tsx
rm -f frontend/public/grid.svg

# Stash local changes
sudo git stash

# Pull latest code
sudo git pull origin main
```

#### Step 2: Fix import path (if needed)
```bash
# Check if import path needs fixing
grep "from './api-client'" frontend/lib/api/admin.ts

# If found, fix it:
sed -i "s|from './api-client'|from '../api-client'|g" frontend/lib/api/admin.ts
```

#### Step 3: Rebuild frontend
```bash
cd frontend
npm run build
```

#### Step 4: Restart backend
```bash
cd /home/jobplatform/job-platform
sudo systemctl restart job-platform-backend
sudo systemctl status job-platform-backend
```

#### Step 5: Fix frontend pm2 process
```bash
cd /home/jobplatform/job-platform/frontend

# Stop existing process
pm2 stop job-platform-frontend
pm2 delete job-platform-frontend

# Kill any process on port 3000
sudo lsof -ti:3000 | xargs sudo kill -9

# Verify port is free
sudo lsof -i:3000
# Should show nothing

# Start new process
pm2 start npm --name "job-platform-frontend" -- start

# Wait a few seconds
sleep 5

# Check status
pm2 status

# Check logs
pm2 logs job-platform-frontend --lines 20

# Save configuration
pm2 save
```

## Verification

1. Check if frontend is running:
```bash
pm2 status
# Should show job-platform-frontend as "online"
```

2. Check frontend logs:
```bash
pm2 logs job-platform-frontend --lines 50
# Should show "ready started server on 0.0.0.0:3000"
```

3. Test admin dashboard:
```bash
curl -I https://trusanity.com/admin/dashboard
# Should return 200 OK
```

4. Login to admin dashboard:
- URL: https://trusanity.com/admin/dashboard
- Email: admin@trusanity.com
- Password: Admin@123

## Expected Result

After successful deployment, you should see:

1. Admin Dashboard with 4 pages:
   - Dashboard (https://trusanity.com/admin/dashboard)
   - Users (https://trusanity.com/admin/users)
   - Jobs (https://trusanity.com/admin/jobs)
   - Rate Limits (https://trusanity.com/admin/rate-limits)

2. Header navigation showing "Admin Dashboard" link when logged in as admin

3. Platform statistics displayed on dashboard page

## Troubleshooting

### If port 3000 is still in use:
```bash
# Find what's using port 3000
sudo lsof -i:3000

# Kill it forcefully
sudo lsof -ti:3000 | xargs sudo kill -9

# Try starting pm2 again
pm2 start npm --name "job-platform-frontend" -- start
```

### If frontend build fails:
```bash
cd /home/jobplatform/job-platform/frontend

# Check for import errors
npm run build 2>&1 | grep "Module not found"

# If admin.ts import error, fix it:
sed -i "s|from './api-client'|from '../api-client'|g" lib/api/admin.ts

# Rebuild
npm run build
```

### If backend is not responding:
```bash
# Check backend logs
sudo journalctl -u job-platform-backend -n 50

# Restart backend
sudo systemctl restart job-platform-backend

# Check status
sudo systemctl status job-platform-backend
```

## Files Deployed

### Frontend:
- `frontend/app/admin/dashboard/page.tsx` - Main dashboard page
- `frontend/app/admin/users/page.tsx` - User management page
- `frontend/app/admin/jobs/page.tsx` - Job monitoring page
- `frontend/app/admin/rate-limits/page.tsx` - Rate limit monitoring page
- `frontend/lib/api/admin.ts` - Admin API client
- `frontend/components/layout/Header.tsx` - Updated with admin navigation

### Backend:
- `backend/app/api/admin.py` - Admin API endpoints
  - GET /api/admin/stats - Platform statistics
  - GET /api/admin/users - List all users
  - GET /api/admin/rate-limit/violations/{user_id} - User violations
  - GET /api/admin/rate-limit/violators - List violators
  - GET /api/admin/rate-limit/stats - Rate limit statistics
  - DELETE /api/admin/rate-limit/violations/{user_id} - Clear violations

## Next Steps

After deployment is successful:

1. Test all admin dashboard pages
2. Verify statistics are loading correctly
3. Test user management features
4. Test rate limit monitoring
5. Verify admin navigation in header
