# SSH Key Setup Guide

## What Happened?

The deployment script failed with:
```
Permission denied (publickey)
```

This means your computer doesn't have SSH key authentication set up for the server.

## What This Means

SSH (Secure Shell) can authenticate in two ways:
1. **Password** - You type a password each time
2. **SSH Key** - Your computer has a "key" that automatically authenticates

Your server is configured to only accept SSH keys, not passwords.

## Solutions

### Option 1: Set Up SSH Key (Recommended for Future)

This lets you use automated scripts:

```bash
# 1. Generate SSH key (if you don't have one)
ssh-keygen -t rsa -b 4096
# Press Enter for all prompts (use defaults)

# 2. Copy key to server
ssh-copy-id jobplatform@3.110.220.37
# You'll need to enter the password once

# 3. Test connection
ssh jobplatform@3.110.220.37
# Should connect without asking for password

# 4. Now run the deployment script
./DEPLOY_NOW.sh
```

### Option 2: Deploy Manually on Server (Easiest Right Now)

Since you have server access, just do it directly on the server:

```bash
# 1. SSH to server (however you normally do it)
ssh jobplatform@3.110.220.37

# 2. Go to project directory
cd /home/jobplatform/job-platform

# 3. If using git, pull latest changes
git pull origin main

# 4. Restart backend
sudo systemctl restart job-platform-backend

# 5. Rebuild frontend
cd frontend
npm run build
pm2 restart job-platform-frontend
```

### Option 3: Use Git Push/Pull

If your code is in a git repository:

```bash
# On your local machine
git add .
git commit -m "Add admin dashboard"
git push origin main

# On the server
ssh jobplatform@3.110.220.37
cd /home/jobplatform/job-platform
git pull origin main
sudo systemctl restart job-platform-backend
cd frontend && npm run build && pm2 restart job-platform-frontend
```

## Which Option Should You Choose?

- **Have git repository?** → Use Option 3 (easiest)
- **Want automated deployments?** → Use Option 1 (set up SSH key)
- **Just want it working now?** → Use Option 2 (manual on server)

## After Deployment

Test the admin dashboard:
1. Go to https://trusanity.com/login
2. Login with admin@trusanity.com / Admin@123
3. You should see "Admin Dashboard" in the header
4. Click it to access your control panel

## Need More Help?

Check these files:
- `MANUAL_DEPLOY_ADMIN.md` - Detailed manual deployment steps
- `DEPLOY_INSTRUCTIONS.md` - Complete deployment guide
- `README_ADMIN_DASHBOARD.md` - What you're deploying

---

**Quick Fix:** Just SSH to your server and run the commands in Option 2!
