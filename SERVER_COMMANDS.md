# Server Commands to Fix Admin Dashboard

## Quick Fix (Copy and paste this entire block on the server)

```bash
cd /home/jobplatform/job-platform/frontend && \
pm2 stop job-platform-frontend 2>/dev/null && \
pm2 delete job-platform-frontend 2>/dev/null && \
sudo lsof -ti:3000 | xargs sudo kill -9 2>/dev/null && \
sleep 2 && \
rm -rf .next && \
rm -rf node_modules/.cache && \
npm run build && \
pm2 start npm --name "job-platform-frontend" -- start && \
sleep 10 && \
pm2 status && \
pm2 save
```

## What This Does

1. Stops and deletes the existing pm2 process
2. Kills anything on port 3000
3. Removes Next.js cache (.next directory)
4. Removes node_modules cache
5. Rebuilds the frontend from scratch
6. Starts fresh pm2 process
7. Saves pm2 configuration

## After Running

1. **Clear your browser cache**:
   - Chrome/Firefox: Press `Ctrl+Shift+Delete`, select "Cached images and files", click Clear
   - Or open an incognito/private window

2. **Visit the site**: https://trusanity.com

3. **If still seeing chunk errors**, do a hard refresh:
   - Chrome/Firefox: `Ctrl+Shift+R`
   - Safari: `Cmd+Shift+R`

## Verify It's Working

Check pm2 logs:
```bash
pm2 logs job-platform-frontend --lines 50
```

You should see:
```
> frontend@0.1.0 start
> next start

  ▲ Next.js 14.2.35
  - Local:        http://localhost:3000
  - Network:      http://0.0.0.0:3000

 ✓ Ready in XXXms
```

## Test Admin Dashboard

1. Go to: https://trusanity.com/login
2. Login with:
   - Email: admin@trusanity.com
   - Password: Admin@123
3. After login, you should see "Admin Dashboard" link in the header
4. Click it to access: https://trusanity.com/admin/dashboard

## Troubleshooting

### If pm2 shows "errored" status:
```bash
pm2 logs job-platform-frontend --lines 100
```
Look for the actual error message.

### If port 3000 is still in use:
```bash
sudo lsof -i:3000
sudo lsof -ti:3000 | xargs sudo kill -9
```

### If build fails:
```bash
cd /home/jobplatform/job-platform
sudo git pull origin main
cd frontend
npm run build
```

### Check backend is running:
```bash
sudo systemctl status job-platform-backend
```

If not running:
```bash
sudo systemctl restart job-platform-backend
```
