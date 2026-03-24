# Manual Deployment - Admin Dashboard

## Problem
The automated script failed because SSH key authentication isn't set up:
```
Permission denied (publickey)
```

## Solution: Deploy Manually on Server

Since you have access to the server, you can deploy directly on the server itself.

## Step-by-Step Instructions

### Option 1: Upload Files from Your Computer

If you have password authentication or can set up SSH keys:

1. **Set up SSH key (if needed):**
   ```bash
   # On your local machine
   ssh-keygen -t rsa -b 4096
   ssh-copy-id jobplatform@3.110.220.37
   ```

2. **Then run the deployment script:**
   ```bash
   ./DEPLOY_NOW.sh
   ```

### Option 2: Deploy Directly on Server (Recommended)

If you can access the server directly, do this:

#### 1. SSH to Server
```bash
ssh jobplatform@3.110.220.37
# Or use your existing method to access the server
```

#### 2. Navigate to Project
```bash
cd /home/jobplatform/job-platform
```

#### 3. Update Backend Files

Create/update the admin API file:
```bash
nano backend/app/api/admin.py
```

Copy the content from your local `backend/app/api/admin.py` file and paste it.
Or use git if your code is in a repository:
```bash
git pull origin main
```

#### 4. Update Frontend Files

Create admin dashboard directory:
```bash
mkdir -p frontend/app/admin/dashboard
mkdir -p frontend/app/admin/users
mkdir -p frontend/app/admin/jobs
mkdir -p frontend/app/admin/rate-limits
mkdir -p frontend/lib/api
```

Copy these files from your local machine to the server:
- `frontend/app/admin/dashboard/page.tsx`
- `frontend/app/admin/users/page.tsx`
- `frontend/app/admin/jobs/page.tsx`
- `frontend/app/admin/rate-limits/page.tsx`
- `frontend/lib/api/admin.ts`
- `frontend/components/layout/Header.tsx`

#### 5. Restart Services

```bash
# Restart backend
sudo systemctl restart job-platform-backend

# Check backend status
sudo systemctl status job-platform-backend

# Rebuild frontend
cd /home/jobplatform/job-platform/frontend
npm run build

# Restart frontend
pm2 restart job-platform-frontend

# Check frontend status
pm2 status
```

### Option 3: Use Git (If Your Code is in a Repository)

If your code is in a git repository:

```bash
# SSH to server
ssh jobplatform@3.110.220.37

# Navigate to project
cd /home/jobplatform/job-platform

# Pull latest changes
git pull origin main

# Restart backend
sudo systemctl restart job-platform-backend

# Rebuild and restart frontend
cd frontend
npm run build
pm2 restart job-platform-frontend
```

## Files to Copy

If copying manually, you need these files:

### Backend (1 file):
```
backend/app/api/admin.py
```

### Frontend (6 files):
```
frontend/app/admin/dashboard/page.tsx
frontend/app/admin/users/page.tsx
frontend/app/admin/jobs/page.tsx
frontend/app/admin/rate-limits/page.tsx
frontend/lib/api/admin.ts
frontend/components/layout/Header.tsx
```

## Verify Deployment

After deployment, test:

### 1. Check Backend is Running
```bash
sudo systemctl status job-platform-backend
```

### 2. Check Frontend is Running
```bash
pm2 status
```

### 3. Test Admin Login
```bash
curl -X POST https://trusanity.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@trusanity.com",
    "password": "Admin@123"
  }'
```

Should return role: "admin"

### 4. Access Dashboard
Open browser and go to:
- https://trusanity.com/login
- Login with admin@trusanity.com / Admin@123
- You should see "Admin Dashboard" in the header
- Click it to access the dashboard

## Troubleshooting

### Backend not starting?
```bash
# Check logs
sudo journalctl -u job-platform-backend -n 50

# Check if port is in use
sudo netstat -tlnp | grep 8000
```

### Frontend not building?
```bash
# Check for errors
cd /home/jobplatform/job-platform/frontend
npm run build

# Check pm2 logs
pm2 logs job-platform-frontend
```

### Admin navigation not showing?
- Clear browser cache
- Hard refresh (Ctrl+Shift+R)
- Check you're logged in as admin
- Verify Header.tsx was updated

## Alternative: Use FileZilla or SCP

If you prefer a GUI tool:

1. **Install FileZilla** (or similar SFTP client)
2. **Connect to server:**
   - Host: 3.110.220.37
   - Username: jobplatform
   - Password: (your password)
   - Port: 22

3. **Upload files** to:
   - `/home/jobplatform/job-platform/backend/app/api/admin.py`
   - `/home/jobplatform/job-platform/frontend/app/admin/...`
   - etc.

4. **SSH and restart services** (see step 5 above)

## Need Help?

If you're stuck:
1. Make sure you can SSH to the server
2. Check if services are running
3. Review the logs for errors
4. Verify file permissions are correct

---

**Easiest Method:** If you have direct server access, just copy the files directly on the server and restart the services!
