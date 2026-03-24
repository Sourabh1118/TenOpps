# Admin Role Fix - Complete Guide

## Problem Summary

The admin account was being created in the **Employers** table instead of the **Admin** table, causing the login to return role "employer" instead of "admin".

### Root Cause
- `backend/scripts/create_admin.py` was creating admin users in the Employers table
- Admin and Employer are fundamentally different roles:
  - **Admin**: Platform owner with full system control
  - **Employer**: Normal company that posts jobs and hires candidates

## Solution

Updated `create_admin.py` to create admin users in the proper `admins` table.

### What Changed

1. **Script Updated**: `backend/scripts/create_admin.py`
   - Now imports `Admin` model instead of `Employer` model
   - Creates admin in `admins` table with proper fields
   - Removed employer-specific fields (company_name, subscription_tier, etc.)
   - Added admin-specific fields (full_name)

2. **Login Already Works**: `backend/app/api/auth.py`
   - Already checks Admin table during login
   - Already returns role "admin" for admin users
   - No changes needed here

## Deployment Steps

### Option 1: Run Script on Server (Recommended)

1. **Upload the fixed script to server:**
   ```bash
   scp backend/scripts/create_admin.py jobplatform@3.110.220.37:/home/jobplatform/job-platform/backend/scripts/
   scp FIX_ADMIN_ON_SERVER.sh jobplatform@3.110.220.37:/home/jobplatform/
   ```

2. **SSH to server and run the fix:**
   ```bash
   ssh jobplatform@3.110.220.37
   chmod +x FIX_ADMIN_ON_SERVER.sh
   ./FIX_ADMIN_ON_SERVER.sh
   ```

### Option 2: Manual Steps on Server

1. **SSH to server:**
   ```bash
   ssh jobplatform@3.110.220.37
   cd /home/jobplatform/job-platform/backend
   source venv/bin/activate
   ```

2. **Delete old admin from employers table:**
   ```bash
   python3 << 'EOF'
   import sys
   sys.path.insert(0, '/home/jobplatform/job-platform/backend')
   from sqlalchemy.orm import Session
   from app.db.session import SessionLocal
   from app.models.employer import Employer
   
   db = SessionLocal()
   try:
       old_admin = db.query(Employer).filter(Employer.email == "admin@trusanity.com").first()
       if old_admin:
           db.delete(old_admin)
           db.commit()
           print("✅ Deleted old admin from employers table")
       else:
           print("ℹ️  No admin found in employers table")
   except Exception as e:
       db.rollback()
       print(f"❌ Error: {e}")
   finally:
       db.close()
   EOF
   ```

3. **Create new admin in admins table:**
   ```bash
   python3 scripts/create_admin.py
   ```

4. **Test login:**
   ```bash
   curl -X POST https://trusanity.com/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{
       "email": "admin@trusanity.com",
       "password": "Admin@123"
     }' | python3 -m json.tool
   ```

## Verification

After running the fix, verify:

1. **Admin exists in admins table:**
   ```python
   from app.models.admin import Admin
   admin = db.query(Admin).filter(Admin.email == "admin@trusanity.com").first()
   print(f"Admin ID: {admin.id}, Role will be: admin")
   ```

2. **Login returns role "admin":**
   ```bash
   # Should return: "role": "admin"
   curl -X POST https://trusanity.com/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "admin@trusanity.com", "password": "Admin@123"}'
   ```

3. **Old admin removed from employers table:**
   ```python
   from app.models.employer import Employer
   old_admin = db.query(Employer).filter(Employer.email == "admin@trusanity.com").first()
   print(f"Should be None: {old_admin}")
   ```

## Expected Result

After the fix:
- Login with `admin@trusanity.com` / `Admin@123`
- Response includes: `"role": "admin"`
- Admin has platform-wide control (not limited to employer features)

## Architecture Notes

### Three User Types in the System:

1. **Admin** (Platform Owner)
   - Table: `admins`
   - Role: `admin`
   - Access: Full platform control
   - Can: Manage all users, jobs, settings, view analytics, etc.

2. **Employer** (Companies)
   - Table: `employers`
   - Role: `employer`
   - Access: Own company data only
   - Can: Post jobs, manage applications, view own analytics

3. **Job Seeker** (Candidates)
   - Table: `job_seekers`
   - Role: `job_seeker`
   - Access: Own profile and applications
   - Can: Search jobs, apply, manage profile

### Future Considerations

1. **Admin Dashboard**: Create separate admin UI at `/admin/*` routes
2. **Admin Permissions**: Implement admin-specific middleware and permissions
3. **Admin Features**: Add user management, platform analytics, system settings
4. **Multiple Admins**: Support multiple admin accounts with different permission levels

## Files Modified

- `backend/scripts/create_admin.py` - Fixed to create admin in admins table
- `FIX_ADMIN_ON_SERVER.sh` - New deployment script
- `ADMIN_ROLE_FIX_GUIDE.md` - This documentation

## Files Already Correct (No Changes Needed)

- `backend/app/models/admin.py` - Admin model already exists
- `backend/app/api/auth.py` - Login already checks Admin table
- `backend/alembic/versions/010_create_admins_table.py` - Migration already exists

## Credentials

```
Email: admin@trusanity.com
Password: Admin@123
Role: admin (platform owner)
URL: https://trusanity.com/login
```

⚠️ **Important**: Change the password after first login!
