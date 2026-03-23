# Manual Deployment Commands

## Option 1: Automated Script (Recommended)

Run this from your local machine:

```bash
chmod +x deploy-to-ec2.sh
./deploy-to-ec2.sh
```

The script will:
- SSH into EC2 using your key
- Pull latest code
- Fix migrations
- Run complete deployment
- Verify all services

---

## Option 2: Manual SSH Commands

### Step 1: SSH into EC2
```bash
ssh -i trusanity-pem.pem ubuntu@3.110.220.37
```

### Step 2: Pull Latest Code
```bash
# If directory exists
cd /home/jobplatform/job-platform && sudo -u jobplatform git pull

# OR if directory doesn't exist
cd /home/jobplatform && sudo -u jobplatform git clone https://YOUR_GITHUB_TOKEN@github.com/Sourabh1118/TenOpps.git job-platform
```

### Step 3: Fix Migrations
```bash
cd /home/jobplatform/job-platform
chmod +x scripts/fix-all-migrations.sh
sudo -u jobplatform bash scripts/fix-all-migrations.sh
```

### Step 4: Run Deployment
```bash
sudo bash scripts/complete-clean-deploy.sh trusanity.com YOUR_GITHUB_TOKEN Herculis@123 Herculis@123
```

### Step 5: Configure SSL (After Deployment)
```bash
sudo certbot --nginx -d trusanity.com
```

---

## Verify Deployment

### Check Service Status
```bash
sudo systemctl status job-platform-backend
sudo systemctl status job-platform-celery-worker
sudo systemctl status job-platform-celery-beat
sudo -u jobplatform pm2 status
sudo systemctl status nginx
```

### Test API
```bash
curl http://localhost:8000/api/health
curl http://localhost:3000
```

### View Logs
```bash
# Backend logs
sudo journalctl -u job-platform-backend -f

# Celery logs
sudo journalctl -u job-platform-celery-worker -f

# Frontend logs
sudo -u jobplatform pm2 logs job-platform-frontend

# Nginx logs
sudo tail -f /var/log/nginx/error.log
```

---

## Troubleshooting

### If SSH connection fails:
```bash
# Check key permissions
chmod 400 trusanity-pem.pem

# Test connection
ssh -i trusanity-pem.pem -v ubuntu@3.110.220.37
```

### If migrations fail:
```bash
cd /home/jobplatform/job-platform/backend
sudo -u jobplatform bash -c 'source venv/bin/activate && alembic current'
sudo -u jobplatform bash -c 'source venv/bin/activate && alembic history'
```

### If frontend build fails:
```bash
cd /home/jobplatform/job-platform/frontend
sudo -u jobplatform npm install tailwindcss-animate
sudo -u jobplatform npm run build
```

### If services don't start:
```bash
# Check logs for errors
sudo journalctl -u job-platform-backend -n 50 --no-pager
sudo journalctl -u job-platform-celery-worker -n 50 --no-pager

# Restart services
sudo systemctl restart job-platform-backend
sudo systemctl restart job-platform-celery-worker
sudo systemctl restart nginx
sudo -u jobplatform pm2 restart job-platform-frontend
```

---

## Quick Status Check

```bash
# One-liner to check all services
ssh -i trusanity-pem.pem ubuntu@3.110.220.37 "sudo systemctl status job-platform-backend job-platform-celery-worker nginx --no-pager | grep Active && sudo -u jobplatform pm2 list"
```

---

## Access URLs

- Application: http://trusanity.com (or http://3.110.220.37)
- Backend API: http://trusanity.com/api
- After SSL: https://trusanity.com
