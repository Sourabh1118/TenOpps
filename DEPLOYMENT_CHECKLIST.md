# Deployment Checklist

## Current Status: ✅ Migrations Complete

You are currently logged in as `jobplatform` user (running as root in venv).

## Completed Steps
- [x] Database migrations (all 11 migrations successful)
- [x] Database tables created
- [x] Environment configuration fixed

## Next Steps

### 1. Create Admin Account (As jobplatform user - YOU ARE HERE)
```bash
cd /home/jobplatform/job-platform/backend
source venv/bin/activate
python scripts/create_admin.py
```

Expected output:
- ✅ Admin user created successfully
- Email: admin@trusanity.com
- Password: Admin@123

### 2. Exit to Ubuntu User
```bash
exit  # Exit from root/venv
exit  # Exit from jobplatform user to ubuntu user
```

### 3. Setup Backend Service (As ubuntu user with sudo)
```bash
bash SETUP_BACKEND_SERVICE.sh
```

This will:
- Start Redis service
- Create systemd service for backend
- Start backend on port 8000
- Enable auto-start on boot

### 4. Setup Frontend (As ubuntu user)
```bash
bash SETUP_FRONTEND.sh
```

This will:
- Create environment files
- Install dependencies
- Build Next.js frontend
- Start with PM2 on port 3000
- Setup PM2 auto-start

### 5. Configure Nginx (As ubuntu user with sudo)
```bash
bash SETUP_NGINX.sh
```

This will:
- Create Nginx configuration
- Enable site
- Test configuration
- Restart Nginx
- Site accessible at http://trusanity.com

### 6. Install SSL Certificate (As ubuntu user with sudo)
```bash
bash SETUP_SSL.sh
```

This will:
- Install Let's Encrypt certificate
- Configure HTTPS
- Setup auto-renewal
- Site accessible at https://trusanity.com

## Verification Steps

After all steps complete:

1. Check all services:
```bash
sudo systemctl status job-platform-backend
pm2 status
sudo systemctl status nginx
sudo systemctl status redis-server
sudo systemctl status postgresql
```

2. Test the application:
- Visit: https://trusanity.com
- Login: https://trusanity.com/login
  - Email: admin@trusanity.com
  - Password: Admin@123
- Access admin dashboard: https://trusanity.com/admin/dashboard

## Troubleshooting

### View Logs
```bash
# Backend logs
sudo journalctl -u job-platform-backend -f

# Frontend logs
pm2 logs job-platform-frontend

# Nginx logs
sudo tail -f /var/log/nginx/error.log
```

### Restart Services
```bash
# Backend
sudo systemctl restart job-platform-backend

# Frontend
pm2 restart job-platform-frontend

# Nginx
sudo systemctl restart nginx
```

## Important Notes

1. You are currently in venv as root, but logged in as jobplatform user
2. You don't need sudo password for jobplatform user
3. Use ubuntu user for sudo commands
4. Admin credentials: admin@trusanity.com / Admin@123
5. Change admin password after first login
6. Server IP: 3.110.220.37
7. Domain: trusanity.com

## Quick Commands Reference

```bash
# Switch users
exit                    # Exit current shell
sudo su - jobplatform   # Switch to jobplatform (from ubuntu)
sudo su - ubuntu        # Switch to ubuntu (from root)

# Service management
sudo systemctl status job-platform-backend
sudo systemctl restart job-platform-backend
pm2 status
pm2 restart job-platform-frontend

# View logs
sudo journalctl -u job-platform-backend -f
pm2 logs job-platform-frontend
sudo tail -f /var/log/nginx/error.log

# Database
psql -U jobplatform -d jobplatform_db -h localhost
```
