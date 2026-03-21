# GCP Compute Engine Deployment Guide

Complete guide for deploying the Job Aggregation Platform on Google Cloud Platform Compute Engine with all services installed natively on the instance.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Instance Setup](#instance-setup)
3. [PostgreSQL Installation](#postgresql-installation)
4. [Redis Installation](#redis-installation)
5. [Backend Application Setup](#backend-application-setup)
6. [Celery Worker Setup](#celery-worker-setup)
7. [Frontend Application Setup](#frontend-application-setup)
8. [Nginx Configuration](#nginx-configuration)
9. [SSL Certificate Setup](#ssl-certificate-setup)
10. [Firewall Configuration](#firewall-configuration)
11. [Monitoring and Maintenance](#monitoring-and-maintenance)

---

## Prerequisites

- GCP account with billing enabled
- Domain name (optional but recommended)
- Basic knowledge of Linux command line
- SSH key pair for secure access

---

## Instance Setup

### 1. Create Compute Engine Instance

```bash
# Using gcloud CLI
gcloud compute instances create job-platform-server \
  --zone=us-central1-a \
  --machine-type=e2-standard-4 \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB \
  --boot-disk-type=pd-ssd \
  --tags=http-server,https-server
```

**Recommended Specifications:**
- Machine Type: e2-standard-4 (4 vCPUs, 16 GB RAM)
- OS: Ubuntu 22.04 LTS
- Boot Disk: 50GB SSD
- Region: Choose closest to your users

### 2. Connect to Instance

```bash
gcloud compute ssh job-platform-server --zone=us-central1-a
```

### 3. Update System

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential curl git wget vim
```

---

## PostgreSQL Installation

### 1. Install PostgreSQL 15

```bash
# Add PostgreSQL repository
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

# Install PostgreSQL
sudo apt update
sudo apt install -y postgresql-15 postgresql-contrib-15
```

### 2. Configure PostgreSQL

```bash
# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL prompt, create database and user
CREATE DATABASE job_platform;
CREATE USER job_platform_user WITH PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE job_platform TO job_platform_user;
ALTER DATABASE job_platform OWNER TO job_platform_user;
\q
```

### 3. Configure PostgreSQL for Remote Access (if needed)

```bash
# Edit postgresql.conf
sudo vim /etc/postgresql/15/main/postgresql.conf

# Change listen_addresses
listen_addresses = 'localhost'  # Keep localhost for security

# Edit pg_hba.conf for local connections
sudo vim /etc/postgresql/15/main/pg_hba.conf

# Add this line for local connections
local   all             job_platform_user                       scram-sha-256

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### 4. Optimize PostgreSQL Settings

```bash
sudo vim /etc/postgresql/15/main/postgresql.conf
```

Add/modify these settings based on your instance:

```conf
# Memory Settings (for 16GB RAM instance)
shared_buffers = 4GB
effective_cache_size = 12GB
maintenance_work_mem = 1GB
work_mem = 64MB

# Connection Settings
max_connections = 200

# Performance Settings
random_page_cost = 1.1
effective_io_concurrency = 200
```

```bash
sudo systemctl restart postgresql
```

---

## Redis Installation

### 1. Install Redis

```bash
sudo apt install -y redis-server
```

### 2. Configure Redis

```bash
sudo vim /etc/redis/redis.conf
```

Key configurations:

```conf
# Bind to localhost only
bind 127.0.0.1

# Set password
requirepass your_redis_password_here

# Memory management
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# AOF persistence
appendonly yes
appendfsync everysec
```

### 3. Start Redis

```bash
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test Redis
redis-cli ping
# Should return PONG
```

---

## Backend Application Setup

### 1. Install Python 3.11

```bash
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
```

### 2. Create Application User

```bash
sudo useradd -m -s /bin/bash jobplatform
sudo su - jobplatform
```

### 3. Clone Repository

```bash
cd /home/jobplatform
git clone https://github.com/yourusername/job-platform.git
cd job-platform/backend
```

### 4. Setup Python Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Create Production Environment File

```bash
vim .env.production
```

```env
# Database
DATABASE_URL=postgresql://job_platform_user:your_secure_password_here@localhost:5432/job_platform

# Redis
REDIS_URL=redis://:your_redis_password_here@localhost:6379/0

# Security
SECRET_KEY=generate_a_very_long_random_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
ENVIRONMENT=production
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# CORS
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Celery
CELERY_BROKER_URL=redis://:your_redis_password_here@localhost:6379/0
CELERY_RESULT_BACKEND=redis://:your_redis_password_here@localhost:6379/1

# Email (configure your SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@your-domain.com

# Stripe
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret

# Sentry
SENTRY_DSN=your_sentry_dsn_here

# File Upload
MAX_UPLOAD_SIZE=5242880
ALLOWED_EXTENSIONS=pdf,doc,docx
```

### 6. Run Database Migrations

```bash
source venv/bin/activate
alembic upgrade head
```

### 7. Create Systemd Service for Backend

Exit from jobplatform user:
```bash
exit
```

Create service file:
```bash
sudo vim /etc/systemd/system/job-platform-backend.service
```

```ini
[Unit]
Description=Job Platform Backend API
After=network.target postgresql.service redis-server.service

[Service]
Type=notify
User=jobplatform
Group=jobplatform
WorkingDirectory=/home/jobplatform/job-platform/backend
Environment="PATH=/home/jobplatform/job-platform/backend/venv/bin"
EnvironmentFile=/home/jobplatform/job-platform/backend/.env.production
ExecStart=/home/jobplatform/job-platform/backend/venv/bin/gunicorn \
    -k uvicorn.workers.UvicornWorker \
    -w 4 \
    -b 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /var/log/job-platform/backend-access.log \
    --error-logfile /var/log/job-platform/backend-error.log \
    app.main:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 8. Create Log Directory

```bash
sudo mkdir -p /var/log/job-platform
sudo chown jobplatform:jobplatform /var/log/job-platform
```

### 9. Start Backend Service

```bash
sudo systemctl daemon-reload
sudo systemctl start job-platform-backend
sudo systemctl enable job-platform-backend
sudo systemctl status job-platform-backend
```

---

## Celery Worker Setup

### 1. Create Celery Worker Service

```bash
sudo vim /etc/systemd/system/job-platform-celery.service
```

```ini
[Unit]
Description=Job Platform Celery Worker
After=network.target redis-server.service postgresql.service

[Service]
Type=forking
User=jobplatform
Group=jobplatform
WorkingDirectory=/home/jobplatform/job-platform/backend
Environment="PATH=/home/jobplatform/job-platform/backend/venv/bin"
EnvironmentFile=/home/jobplatform/job-platform/backend/.env.production
ExecStart=/home/jobplatform/job-platform/backend/venv/bin/celery -A app.tasks.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --logfile=/var/log/job-platform/celery-worker.log \
    --pidfile=/var/run/celery/worker.pid

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Create Celery Beat Service

```bash
sudo vim /etc/systemd/system/job-platform-celery-beat.service
```

```ini
[Unit]
Description=Job Platform Celery Beat Scheduler
After=network.target redis-server.service

[Service]
Type=simple
User=jobplatform
Group=jobplatform
WorkingDirectory=/home/jobplatform/job-platform/backend
Environment="PATH=/home/jobplatform/job-platform/backend/venv/bin"
EnvironmentFile=/home/jobplatform/job-platform/backend/.env.production
ExecStart=/home/jobplatform/job-platform/backend/venv/bin/celery -A app.tasks.celery_app beat \
    --loglevel=info \
    --logfile=/var/log/job-platform/celery-beat.log \
    --pidfile=/var/run/celery/beat.pid

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. Create PID Directory

```bash
sudo mkdir -p /var/run/celery
sudo chown jobplatform:jobplatform /var/run/celery
```

### 4. Start Celery Services

```bash
sudo systemctl daemon-reload
sudo systemctl start job-platform-celery
sudo systemctl start job-platform-celery-beat
sudo systemctl enable job-platform-celery
sudo systemctl enable job-platform-celery-beat
```

---

## Frontend Application Setup

### 1. Install Node.js 20

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

### 2. Build Frontend

```bash
sudo su - jobplatform
cd /home/jobplatform/job-platform/frontend

# Install dependencies
npm install

# Create production environment file
vim .env.production
```

```env
NEXT_PUBLIC_API_URL=https://your-domain.com/api
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
```

```bash
# Build for production
npm run build
```

### 3. Create Frontend Service

Exit from jobplatform user and create service:

```bash
exit
sudo vim /etc/systemd/system/job-platform-frontend.service
```

```ini
[Unit]
Description=Job Platform Frontend
After=network.target

[Service]
Type=simple
User=jobplatform
Group=jobplatform
WorkingDirectory=/home/jobplatform/job-platform/frontend
Environment="PATH=/usr/bin:/usr/local/bin"
Environment="NODE_ENV=production"
ExecStart=/usr/bin/npm start -- -p 3000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4. Start Frontend Service

```bash
sudo systemctl daemon-reload
sudo systemctl start job-platform-frontend
sudo systemctl enable job-platform-frontend
sudo systemctl status job-platform-frontend
```

---

## Nginx Configuration

### 1. Install Nginx

```bash
sudo apt install -y nginx
```

### 2. Create Nginx Configuration

```bash
sudo vim /etc/nginx/sites-available/job-platform
```

```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=general_limit:10m rate=30r/s;

# Upstream servers
upstream backend {
    server 127.0.0.1:8000;
}

upstream frontend {
    server 127.0.0.1:3000;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name your-domain.com www.your-domain.com;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL certificates (will be configured with Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # API endpoints
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Frontend
    location / {
        limit_req zone=general_limit burst=50 nodelay;
        
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Static files caching
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        proxy_pass http://frontend;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 3. Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/job-platform /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

---

## SSL Certificate Setup

### 1. Install Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 2. Obtain SSL Certificate

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

Follow the prompts to:
- Enter your email
- Agree to terms of service
- Choose whether to redirect HTTP to HTTPS (recommended: yes)

### 3. Auto-renewal Setup

```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot automatically sets up a cron job for renewal
# Verify it exists
sudo systemctl status certbot.timer
```

---

## Firewall Configuration

### 1. Configure GCP Firewall Rules

```bash
# Allow HTTP
gcloud compute firewall-rules create allow-http \
    --allow tcp:80 \
    --source-ranges 0.0.0.0/0 \
    --target-tags http-server

# Allow HTTPS
gcloud compute firewall-rules create allow-https \
    --allow tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --target-tags https-server

# Allow SSH (if not already configured)
gcloud compute firewall-rules create allow-ssh \
    --allow tcp:22 \
    --source-ranges 0.0.0.0/0
```

### 2. Configure UFW (Ubuntu Firewall)

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

---

## Monitoring and Maintenance

### 1. Setup Log Rotation

```bash
sudo vim /etc/logrotate.d/job-platform
```

```conf
/var/log/job-platform/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 jobplatform jobplatform
    sharedscripts
    postrotate
        systemctl reload job-platform-backend
        systemctl reload job-platform-celery
    endscript
}
```

### 2. Monitoring Commands

```bash
# Check all services
sudo systemctl status job-platform-backend
sudo systemctl status job-platform-frontend
sudo systemctl status job-platform-celery
sudo systemctl status job-platform-celery-beat
sudo systemctl status postgresql
sudo systemctl status redis-server
sudo systemctl status nginx

# View logs
sudo journalctl -u job-platform-backend -f
sudo journalctl -u job-platform-celery -f
tail -f /var/log/job-platform/backend-access.log
tail -f /var/log/job-platform/celery-worker.log

# Check resource usage
htop
df -h
free -h
```

### 3. Database Backup Script

```bash
sudo vim /home/jobplatform/backup-db.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/jobplatform/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup PostgreSQL
sudo -u postgres pg_dump job_platform | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Keep only last 7 days of backups
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: db_backup_$DATE.sql.gz"
```

```bash
chmod +x /home/jobplatform/backup-db.sh

# Add to crontab for daily backups at 2 AM
sudo crontab -e
0 2 * * * /home/jobplatform/backup-db.sh
```

### 4. Update Application

```bash
sudo su - jobplatform
cd /home/jobplatform/job-platform

# Pull latest changes
git pull origin main

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
exit

# Update frontend
cd ../frontend
npm install
npm run build
exit

# Restart services
sudo systemctl restart job-platform-backend
sudo systemctl restart job-platform-frontend
sudo systemctl restart job-platform-celery
sudo systemctl restart job-platform-celery-beat
```

---

## Troubleshooting

### Common Issues

1. **Backend not starting:**
   ```bash
   sudo journalctl -u job-platform-backend -n 50
   # Check database connection
   sudo -u postgres psql -d job_platform -c "SELECT 1;"
   ```

2. **Celery workers not processing tasks:**
   ```bash
   sudo journalctl -u job-platform-celery -n 50
   # Check Redis connection
   redis-cli -a your_redis_password_here ping
   ```

3. **Nginx 502 Bad Gateway:**
   ```bash
   # Check if backend is running
   curl http://127.0.0.1:8000/api/health
   # Check Nginx error logs
   sudo tail -f /var/log/nginx/error.log
   ```

4. **Database connection issues:**
   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql
   # Check connections
   sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"
   ```

---

## Security Checklist

- [ ] Changed all default passwords
- [ ] Configured firewall rules
- [ ] SSL certificate installed and auto-renewal configured
- [ ] Database accessible only from localhost
- [ ] Redis password protected
- [ ] Regular backups configured
- [ ] Log rotation configured
- [ ] Security headers configured in Nginx
- [ ] Rate limiting enabled
- [ ] Sentry configured for error tracking
- [ ] SSH key-based authentication enabled
- [ ] Disabled root SSH login

---

## Performance Optimization

### 1. PostgreSQL Connection Pooling

Already handled by SQLAlchemy in the application.

### 2. Redis Memory Optimization

Monitor Redis memory usage:
```bash
redis-cli -a your_redis_password_here INFO memory
```

### 3. Nginx Caching (Optional)

Add to Nginx configuration for static content caching:
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=1g inactive=60m;
```

---

## Cost Optimization

- Use preemptible instances for development/staging
- Set up automatic snapshots for backups
- Monitor resource usage and downsize if possible
- Use committed use discounts for production

---

## Next Steps

1. Configure DNS to point to your instance's external IP
2. Set up monitoring with Google Cloud Monitoring
3. Configure automated backups to Google Cloud Storage
4. Set up staging environment
5. Implement CI/CD pipeline

---

## Support

For issues or questions:
- Check logs: `/var/log/job-platform/`
- Review systemd journals: `sudo journalctl -u <service-name>`
- Monitor Sentry for application errors
