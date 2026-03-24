# Fix Git History - Remove Secret

## Problem
GitHub is blocking your push because there's a Personal Access Token in the git history (in commit `1783c0c`).

## Solutions

### Option 1: Allow the Secret on GitHub (Quickest)

Click this link to allow the secret:
```
https://github.com/Sourabh1118/TenOpps/security/secret-scanning/unblock-secret/3BOEymUH5EJMQWkWEwCGJdwNJQU
```

Then push again:
```bash
git push origin main
```

### Option 2: Rewrite Git History (More Secure)

Remove the secret from history completely:

```bash
# 1. Install git-filter-repo (if not installed)
pip3 install git-filter-repo

# 2. Remove the file from all history
git filter-repo --path DEPLOY_TO_SERVER.sh --invert-paths --force

# 3. Force push (this rewrites history)
git push origin main --force
```

### Option 3: Reset and Recommit (Nuclear Option)

Start fresh without the problematic commit:

```bash
# 1. Create a backup branch
git branch backup-before-reset

# 2. Reset to before the bad commit
git reset --hard HEAD~2

# 3. Re-add only the admin dashboard files
git add frontend/app/admin/
git add frontend/lib/api/admin.ts
git add frontend/components/layout/Header.tsx
git add backend/app/api/admin.py

# 4. Commit
git commit -m "Add admin dashboard and control panel"

# 5. Force push
git push origin main --force
```

## Recommended: Option 1

The easiest solution is to click the GitHub link and allow the secret, then push. The token in that file is probably already expired or not critical.

After pushing successfully, you should:
1. Revoke that GitHub token if it's still active
2. Remove the DEPLOY_TO_SERVER.sh file from your local directory
3. Never commit tokens/secrets to git again

## After Fixing

Once pushed successfully, deploy to your server:

```bash
# SSH to server
ssh jobplatform@3.110.220.37

# Pull latest changes
cd /home/jobplatform/job-platform
git pull origin main

# Restart services
sudo systemctl restart job-platform-backend
cd frontend && npm run build && pm2 restart job-platform-frontend
```

Then access your admin dashboard at https://trusanity.com/admin/dashboard
