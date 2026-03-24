# Quick Start: Fix Admin Login

## The Problem

You're seeing 404 errors and can't login as admin at http://trusanity.com/login

## The Solution (3 Steps)

### Step 1: Test Current Status

```bash
./TEST_ADMIN_LOGIN.sh
```

This will tell you exactly what's wrong.

### Step 2: Deploy Missing Routes

```bash
./FIX_FRONTEND_DEPLOYMENT.sh
```

This fixes all the 404 errors by deploying missing pages.

### Step 3: Login as Admin

Open your browser and go to:

**https://trusanity.com/login** (use HTTPS!)

Enter:
- Email: `admin@trusanity.com`
- Password: `Admin@123`

Click "Sign in" → You'll be redirected to the dashboard!

---

## Why It Wasn't Working

1. ❌ You were using **HTTP** → Backend requires **HTTPS**
2. ❌ Missing routes causing 404 errors
3. ❌ Frontend not configured for production

## What I Fixed

✅ Created `/register` page
✅ Created `/employer/pricing` page  
✅ Created `/employer/register` redirect
✅ Created `grid.svg` asset
✅ Configured HTTPS for production
✅ Created deployment scripts

## Important

**Always use HTTPS:**
- ✅ https://trusanity.com/login
- ❌ http://trusanity.com/login

The backend will reject HTTP requests for security.

## If Admin Account Doesn't Exist

Run this to create it:

```bash
./CREATE_ADMIN.sh
```

Then try logging in again.

## Need Help?

Read the detailed guide:
- `ADMIN_LOGIN_SOLUTION.md` - Complete troubleshooting guide
- `ADMIN_LOGIN_FIX.md` - Technical details
- `ADMIN_ACCOUNT_GUIDE.md` - Admin account management

## Quick Commands

```bash
# Test if everything is working
./TEST_ADMIN_LOGIN.sh

# Deploy the fixes
./FIX_FRONTEND_DEPLOYMENT.sh

# Create admin account (if needed)
./CREATE_ADMIN.sh

# Check backend logs
ssh -i trusanity-pem.pem ubuntu@3.110.220.37
sudo journalctl -u job-platform-backend -n 50
```

That's it! 🎉
