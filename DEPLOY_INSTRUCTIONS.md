# 🚀 Deploy Admin Dashboard - Instructions

## Server Information
- **IP Address**: 3.110.220.37
- **User**: jobplatform
- **Domain**: trusanity.com

## Quick Deploy (Recommended)

Run this single command:
```bash
./DEPLOY_NOW.sh
```

This will:
1. Upload backend files (admin API endpoints)
2. Upload frontend files (admin dashboard pages)
3. Restart backend service
4. Rebuild and restart frontend

## Manual Deploy (Alternative)

If the script doesn't work, follow these steps:

### 1. Upload Backend
```bash
scp backend/app/api/admin.py jobplatform@3.110.220.37:/home/jobplatform/job-platform/backend/app/api/
```

### 2. Upload Frontend
```bash
scp -r frontend/app/admin jobplatform@3.110.220.37:/home/jobplatform/job-platform/frontend/app/
scp frontend/lib/api/admin.ts jobplatform@3.110.220.37:/home/jobplatform/job-platform/frontend/lib/api/
scp frontend/components/layout/Header.tsx jobplatform@3.110.220.37:/home/jobplatform/job-platform/frontend/components/layout/
```

### 3. SSH and Restart
```bash
ssh jobplatform@3.110.220.37
cd /home/jobplatform/job-platform

# Restart backend
sudo systemctl restart job-platform-backend

# Rebuild frontend
cd frontend
npm run build

# Restart frontend
pm2 restart job-platform-frontend
```

## After Deployment

### 1. Test Admin Login
```bash
curl -X POST https://trusanity.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@trusanity.com",
    "password": "Admin@123"
  }' | python3 -m json.tool
```

Should return:
```json
{
  "user_id": "...",
  "role": "admin",
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer"
}
```

### 2. Access Admin Dashboard

1. Go to: https://trusanity.com/login
2. Login with:
   - Email: `admin@trusanity.com`
   - Password: `Admin@123`
3. After login, you'll see admin navigation in header
4. Click "Admin Dashboard"

### 3. Verify Pages Load

Check these URLs work:
- https://trusanity.com/admin/dashboard
- https://trusanity.com/admin/users
- https://trusanity.com/admin/jobs
- https://trusanity.com/admin/rate-limits

## What You'll See

### Header Navigation (After Login as Admin)
- Home
- Search Jobs
- **Admin Dashboard** ← New!
- **Users** ← New!
- **Jobs** ← New!
- Logout

### Dashboard Page
- Platform statistics (users, jobs, applications)
- User breakdown chart
- Today's activity
- Rate limit monitoring
- Quick action buttons

## Troubleshooting

### Script fails with "Connection refused"
- Check server IP is correct: `3.110.220.37`
- Verify SSH access: `ssh jobplatform@3.110.220.37`
- Check your SSH key is configured

### Admin navigation not showing
- Clear browser cache
- Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
- Check you're logged in as admin (not employer)
- Verify role in login response is "admin"

### Dashboard shows errors
- Check backend is running: `sudo systemctl status job-platform-backend`
- Check frontend is running: `pm2 status`
- View backend logs: `sudo journalctl -u job-platform-backend -n 50`
- View frontend logs: `pm2 logs job-platform-frontend`

### Statistics showing 0
- This is normal for a new platform
- Stats will populate as users join and post jobs
- Backend endpoints are working correctly

## Files Deployed

### Backend:
- `backend/app/api/admin.py` - Admin API endpoints

### Frontend:
- `frontend/app/admin/dashboard/page.tsx` - Dashboard
- `frontend/app/admin/users/page.tsx` - User management
- `frontend/app/admin/jobs/page.tsx` - Job management
- `frontend/app/admin/rate-limits/page.tsx` - Rate limits
- `frontend/lib/api/admin.ts` - API client
- `frontend/components/layout/Header.tsx` - Updated navigation

## Next Steps After Deployment

1. ✅ Deploy using `./DEPLOY_NOW.sh`
2. ✅ Test admin login
3. ✅ Access admin dashboard
4. ✅ Verify all pages load
5. ✅ Check navigation works
6. ✅ Test on mobile

## Support

If you encounter any issues:
1. Check the troubleshooting section above
2. Verify server IP is correct (3.110.220.37)
3. Check SSH access works
4. Review service logs

---

**Ready to deploy?** Run: `./DEPLOY_NOW.sh`
