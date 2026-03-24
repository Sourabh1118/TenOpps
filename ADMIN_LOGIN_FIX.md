# Admin Login Fix Guide

## Issues Identified

1. **404 Errors**: Missing frontend routes (`/register`, `/employer/pricing`)
2. **HTTPS Required**: Backend requires HTTPS but you might be using HTTP
3. **RSC Errors**: Next.js Server Components trying to fetch non-existent routes

## Quick Fix

### Option 1: Run the Automated Fix Script

```bash
./FIX_FRONTEND_DEPLOYMENT.sh
```

This will:
- Create missing routes (`/register`, `/employer/pricing`)
- Update HTTPS configuration
- Rebuild and restart the frontend
- Verify all routes are working

### Option 2: Manual Fix

If you prefer to fix manually:

#### 1. Use HTTPS (Not HTTP)

❌ Wrong: `http://trusanity.com/login`
✅ Correct: `https://trusanity.com/login`

The backend requires HTTPS and will reject HTTP requests.

#### 2. Admin Login Credentials

- **URL**: https://trusanity.com/login (use HTTPS!)
- **Email**: admin@trusanity.com
- **Password**: Admin@123

#### 3. Deploy Missing Routes

SSH into the server and rebuild:

```bash
ssh -i trusanity-pem.pem ubuntu@3.110.220.37

cd /home/jobplatform/job-platform/frontend

sudo -u jobplatform bash << 'EOF'
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Pull latest changes
git pull origin main

# Install and build
npm install
npm run build

# Restart
pm2 restart job-platform-frontend
EOF
```

## Testing Admin Login

### 1. Check Backend Health

```bash
curl https://trusanity.com/api/health
```

Should return: `{"status":"healthy"}`

### 2. Test Login API Directly

```bash
curl -X POST https://trusanity.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@trusanity.com",
    "password": "Admin@123"
  }'
```

Should return a JWT token and user info.

### 3. Test Frontend Login

1. Open: https://trusanity.com/login (HTTPS!)
2. Enter:
   - Email: admin@trusanity.com
   - Password: Admin@123
3. Click "Sign in"
4. Should redirect to: https://trusanity.com/employer/dashboard

## Common Issues & Solutions

### Issue: "An error occurred. Please try again."

**Cause**: Using HTTP instead of HTTPS

**Solution**: 
- Always use `https://trusanity.com` (not `http://`)
- Clear browser cache
- Try in incognito mode

### Issue: 404 on /register or /employer/pricing

**Cause**: Missing routes in frontend

**Solution**: Run `./FIX_FRONTEND_DEPLOYMENT.sh`

### Issue: "Invalid email or password"

**Cause**: Admin account not created or wrong credentials

**Solution**: Create admin account:

```bash
ssh -i trusanity-pem.pem ubuntu@3.110.220.37

cd /home/jobplatform/job-platform/backend

sudo -u jobplatform bash -c 'source venv/bin/activate && python scripts/create_admin.py admin@trusanity.com Admin@123'
```

### Issue: RSC errors in console

**Cause**: Next.js trying to prefetch routes that don't exist

**Solution**: 
- Deploy missing routes (run fix script)
- These are warnings and don't prevent login

## Verification Checklist

After running the fix:

- [ ] Backend health check passes: `curl https://trusanity.com/api/health`
- [ ] Login page loads: https://trusanity.com/login
- [ ] Register page loads: https://trusanity.com/register
- [ ] Pricing page loads: https://trusanity.com/employer/pricing
- [ ] Admin can login with credentials
- [ ] Redirects to dashboard after login
- [ ] No 404 errors in browser console

## Admin Dashboard Access

After successful login, you can access:

- **Dashboard**: https://trusanity.com/employer/dashboard
- **Jobs**: https://trusanity.com/employer/jobs
- **Analytics**: https://trusanity.com/employer/analytics
- **Applications**: https://trusanity.com/employer/applications
- **Subscription**: https://trusanity.com/employer/subscription

## Browser Console Errors

The RSC (React Server Components) errors you're seeing are Next.js trying to prefetch routes. After deploying the missing routes, these will disappear.

Example errors that will be fixed:
```
register?_rsc=19zvn:1 Failed to load resource: 404
grid.svg:1 Failed to load resource: 404
employer/pricing?_rsc=19zvn:1 Failed to load resource: 404
employer/register?_rsc=19zvn:1 Failed to load resource: 404
```

## Need Help?

If issues persist:

1. Check backend logs:
   ```bash
   ssh -i trusanity-pem.pem ubuntu@3.110.220.37
   sudo journalctl -u job-platform-backend -n 100 -f
   ```

2. Check frontend logs:
   ```bash
   ssh -i trusanity-pem.pem ubuntu@3.110.220.37
   sudo -u jobplatform pm2 logs job-platform-frontend
   ```

3. Verify nginx configuration:
   ```bash
   ssh -i trusanity-pem.pem ubuntu@3.110.220.37
   sudo nginx -t
   sudo systemctl status nginx
   ```

## Summary

The main issue is using HTTP instead of HTTPS. The backend enforces HTTPS for security. Always use:

✅ **https://trusanity.com/login**

Not:

❌ http://trusanity.com/login
