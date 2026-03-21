# AWS EC2 Deployment Guide

Complete guide for deploying the Job Aggregation Platform on Amazon Web Services EC2 with all services installed natively on the instance.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [EC2 Instance Setup](#ec2-instance-setup)
3. [PostgreSQL Installation](#postgresql-installation)
4. [Redis Installation](#redis-installation)
5. [Backend Application Setup](#backend-application-setup)
6. [Celery Worker Setup](#celery-worker-setup)
7. [Frontend Application Setup](#frontend-application-setup)
8. [Nginx Configuration](#nginx-configuration)
9. [SSL Certificate Setup](#ssl-certificate-setup)
10. [Security Groups Configuration](#security-groups-configuration)
11. [Monitoring and Maintenance](#monitoring-and-maintenance)

---

## Prerequisites

- AWS account with appropriate permissions
- Domain name (optional but recommended)
- Basic knowledge of Linux command line
- SSH key pair for EC2 access

---

## EC2 Instance Setup

### 1. Launch EC2 Instance

**Via AWS Console:**

1. Go to EC2 Dashboard
2. Click "Launch Instance"
3. Configure:
   - Name: job-platform-server
   - AMI: Ubuntu Server 22.04 LTS
   - Instance Type: t3.xlarge (4 vCPUs, 16 GB RAM)
   - Key pair: Select or create new
   - Storage: 50 GB gp3 SSD

**Via AWS CLI:**

```bash
aws ec2 run-instances \
  --image-id ami-0c7217cdde317cfec \
  --instance-type t3.xlarge \
  --key-name your-key-pair \
  --security-group-ids sg-xxxxxxxxx \
  --subnet-id subnet-xxxxxxxxx \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":50,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=job-platform-server}]'
```

**Recommended Specifications:**
- Instance Type: t3.xlarge or t3a.xlarge
- OS: Ubuntu 22.04 LTS
- Storage: 50GB gp3 SSD
- Region: Choose closest to your users

### 2. Allocate Elastic IP

```bash
# Allocate Elastic IP
aws ec2 allocate-address --domain vpc

# Associate with instance
aws ec2 associate-address \
  --instance-id i-xxxxxxxxx \
  --allocation-id eipalloc-xxxxxxxxx
```

### 3. Connect to Instance

```bash
ssh -i your-key.pem ubuntu@your-elastic-ip
```

### 4. Update System

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

### 3. Configure PostgreSQL for Local Access

```bash
# Edit postgresql.conf
sudo vim /etc/postgresql/15/main/postgresql.conf

# Change listen_addresses
listen_addresses = 'localhost'

# Edit pg_hba.conf
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

Add/modify these settings:

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
wal_buffers = 16MB
checkpoint_completion_target = 0.9
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

# Disable protected mode for localhost
protected-mode yes
```

### 3. Start Redis

```bash
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test Redis
redis-cli -a your_redis_password_here ping
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
pip install gunicorn
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
SECRET_KEY=generate_a_very_long_random_secret_key_here_use_openssl_rand_hex_32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
ENVIRONMENT=production
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,your-elastic-ip

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

# AWS (if using S3 for file storage)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-bucket-name
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
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile /var/log/job-platform/backend-access.log \
    --error-logfile /var/log/job-platform/backend-error.log \
    app.main:app

Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

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
    --max-tasks-per-child=1000 \
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
sudo systemctl status job-platform-celery
sudo systemctl status job-platform-celery-beat
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
Environment="PORT=3000"
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

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
    server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

upstream frontend {
    server 127.0.0.1:3000 max_fails=3 fail_timeout=30s;
    keepalive 32;
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
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_stapling on;
    ssl_stapling_verify on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Max upload size
    client_max_body_size 10M;

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
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # WebSocket support (if needed)
    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
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
        access_log off;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
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

### 2. Create Certbot Directory

```bash
sudo mkdir -p /var/www/certbot
```

### 3. Obtain SSL Certificate

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

Follow the prompts to:
- Enter your email
- Agree to terms of service
- Choose whether to redirect HTTP to HTTPS (recommended: yes)

### 4. Auto-renewal Setup

```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot automatically sets up a systemd timer for renewal
# Verify it exists
sudo systemctl status certbot.timer

# Enable the timer
sudo systemctl enable certbot.timer
```

---

## Security Groups Configuration

### 1. Configure EC2 Security Group

**Via AWS Console:**

1. Go to EC2 Dashboard → Security Groups
2. Select your instance's security group
3. Add inbound rules:

| Type  | Protocol | Port Range | Source    | Description        |
|-------|----------|------------|-----------|--------------------|
| SSH   | TCP      | 22         | Your IP   | SSH access         |
| HTTP  | TCP      | 80         | 0.0.0.0/0 | HTTP traffic       |
| HTTPS | TCP      | 443        | 0.0.0.0/0 | HTTPS traffic      |

**Via AWS CLI:**

```bash
# Get security group ID
SECURITY_GROUP_ID=$(aws ec2 describe-instances \
  --instance-ids i-xxxxxxxxx \
  --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' \
  --output text)

# Allow SSH from your IP
aws ec2 authorize-security-group-ingress \
  --group-id $SECURITY_GROUP_ID \
  --protocol tcp \
  --port 22 \
  --cidr your-ip-address/32

# Allow HTTP
aws ec2 authorize-security-group-ingress \
  --group-id $SECURITY_GROUP_ID \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

# Allow HTTPS
aws ec2 authorize-security-group-ingress \
  --group-id $SECURITY_GROUP_ID \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0
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

### 1. Setup CloudWatch Agent (Optional)

```bash
# Download CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb

# Install
sudo dpkg -i amazon-cloudwatch-agent.deb

# Configure (create config file)
sudo vim /opt/aws/amazon-cloudwatch-agent/etc/config.json
```

```json
{
  "metrics": {
    "namespace": "JobPlatform",
    "metrics_collected": {
      "cpu": {
        "measurement": [
          {"name": "cpu_usage_idle", "rename": "CPU_IDLE", "unit": "Percent"},
          {"name": "cpu_usage_iowait", "rename": "CPU_IOWAIT", "unit": "Percent"}
        ],
        "totalcpu": false
      },
      "disk": {
        "measurement": [
          {"name": "used_percent", "rename": "DISK_USED", "unit": "Percent"}
        ],
        "resources": ["*"]
      },
      "mem": {
        "measurement": [
          {"name": "mem_used_percent", "rename": "MEM_USED", "unit": "Percent"}
        ]
      }
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/job-platform/backend-error.log",
            "log_group_name": "/job-platform/backend",
            "log_stream_name": "{instance_id}"
          },
          {
            "file_path": "/var/log/job-platform/celery-worker.log",
            "log_group_name": "/job-platform/celery",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
```

```bash
# Start CloudWatch agent
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json
```

### 2. Setup Log Rotation

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

### 3. Monitoring Commands

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
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Check resource usage
htop
df -h
free -h
iostat -x 1
```

### 4. Database Backup Script

```bash
sudo su - jobplatform
vim /home/jobplatform/backup-db.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/jobplatform/backups"
DATE=$(date +%Y%m%d_%H%M%S)
S3_BUCKET="your-backup-bucket"
mkdir -p $BACKUP_DIR

# Backup PostgreSQL
sudo -u postgres pg_dump job_platform | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/db_backup_$DATE.sql.gz s3://$S3_BUCKET/backups/

# Keep only last 7 days of local backups
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: db_backup_$DATE.sql.gz"
```

```bash
chmod +x /home/jobplatform/backup-db.sh
exit

# Add to crontab for daily backups at 2 AM
sudo crontab -e
0 2 * * * /home/jobplatform/backup-db.sh
```

### 5. Create EBS Snapshot Script

```bash
vim /home/ubuntu/create-snapshot.sh
```

```bash
#!/bin/bash
INSTANCE_ID=$(ec2-metadata --instance-id | cut -d " " -f 2)
VOLUME_ID=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].BlockDeviceMappings[0].Ebs.VolumeId' \
  --output text)

DESCRIPTION="Job Platform Backup - $(date +%Y-%m-%d)"

aws ec2 create-snapshot \
  --volume-id $VOLUME_ID \
  --description "$DESCRIPTION" \
  --tag-specifications "ResourceType=snapshot,Tags=[{Key=Name,Value=job-platform-backup}]"

echo "Snapshot created for volume $VOLUME_ID"
```

```bash
chmod +x /home/ubuntu/create-snapshot.sh

# Add to crontab for weekly snapshots
crontab -e
0 3 * * 0 /home/ubuntu/create-snapshot.sh
```

### 6. Update Application

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
deactivate

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

## Auto Scaling Setup (Optional)

### 1. Create AMI from Instance

```bash
aws ec2 create-image \
  --instance-id i-xxxxxxxxx \
  --name "job-platform-$(date +%Y%m%d)" \
  --description "Job Platform Production Image"
```

### 2. Create Launch Template

```bash
aws ec2 create-launch-template \
  --launch-template-name job-platform-template \
  --version-description "v1" \
  --launch-template-data '{
    "ImageId": "ami-xxxxxxxxx",
    "InstanceType": "t3.xlarge",
    "KeyName": "your-key-pair",
    "SecurityGroupIds": ["sg-xxxxxxxxx"],
    "IamInstanceProfile": {"Name": "job-platform-role"},
    "UserData": "base64-encoded-startup-script"
  }'
```

### 3. Create Auto Scaling Group

```bash
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name job-platform-asg \
  --launch-template LaunchTemplateName=job-platform-template,Version='$Latest' \
  --min-size 1 \
  --max-size 4 \
  --desired-capacity 2 \
  --vpc-zone-identifier "subnet-xxxxx,subnet-yyyyy" \
  --target-group-arns arn:aws:elasticloadbalancing:region:account:targetgroup/xxx \
  --health-check-type ELB \
  --health-check-grace-period 300
```

---

## Load Balancer Setup (Optional)

### 1. Create Application Load Balancer

```bash
aws elbv2 create-load-balancer \
  --name job-platform-alb \
  --subnets subnet-xxxxx subnet-yyyyy \
  --security-groups sg-xxxxxxxxx \
  --scheme internet-facing \
  --type application \
  --ip-address-type ipv4
```

### 2. Create Target Group

```bash
aws elbv2 create-target-group \
  --name job-platform-targets \
  --protocol HTTP \
  --port 80 \
  --vpc-id vpc-xxxxxxxxx \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3
```

---

## Troubleshooting

### Common Issues

1. **Backend not starting:**
   ```bash
   sudo journalctl -u job-platform-backend -n 100 --no-pager
   # Check database connection
   sudo -u postgres psql -d job_platform -c "SELECT 1;"
   ```

2. **Celery workers not processing tasks:**
   ```bash
   sudo journalctl -u job-platform-celery -n 100 --no-pager
   # Check Redis connection
   redis-cli -a your_redis_password_here ping
   # Check Celery status
   sudo su - jobplatform
   cd /home/jobplatform/job-platform/backend
   source venv/bin/activate
   celery -A app.tasks.celery_app inspect active
   ```

3. **Nginx 502 Bad Gateway:**
   ```bash
   # Check if backend is running
   curl http://127.0.0.1:8000/api/health
   # Check Nginx error logs
   sudo tail -f /var/log/nginx/error.log
   # Check backend logs
   sudo journalctl -u job-platform-backend -n 50
   ```

4. **Database connection issues:**
   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql
   # Check connections
   sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"
   # Test connection
   psql -h localhost -U job_platform_user -d job_platform
   ```

5. **High memory usage:**
   ```bash
   # Check memory
   free -h
   # Check processes
   ps aux --sort=-%mem | head -20
   # Restart services if needed
   sudo systemctl restart job-platform-celery
   ```

6. **Disk space issues:**
   ```bash
   # Check disk usage
   df -h
   # Find large files
   sudo du -h /var/log | sort -rh | head -20
   # Clean old logs
   sudo journalctl --vacuum-time=7d
   ```

---

## Security Checklist

- [ ] Changed all default passwords
- [ ] Configured Security Groups properly
- [ ] SSH key-based authentication enabled
- [ ] Disabled root SSH login
- [ ] SSL certificate installed and auto-renewal configured
- [ ] Database accessible only from localhost
- [ ] Redis password protected
- [ ] Regular backups configured (database + EBS snapshots)
- [ ] Log rotation configured
- [ ] Security headers configured in Nginx
- [ ] Rate limiting enabled
- [ ] Sentry configured for error tracking
- [ ] CloudWatch monitoring enabled
- [ ] IAM roles configured with least privilege
- [ ] UFW firewall enabled
- [ ] Fail2ban installed (optional)

---

## Performance Optimization

### 1. Enable Nginx Caching

```bash
sudo vim /etc/nginx/nginx.conf
```

Add inside http block:

```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g inactive=60m use_temp_path=off;
```

### 2. PostgreSQL Connection Pooling

Already handled by SQLAlchemy in the application with pgbouncer as optional enhancement.

### 3. Redis Optimization

Monitor Redis:
```bash
redis-cli -a your_redis_password_here INFO stats
redis-cli -a your_redis_password_here INFO memory
```

### 4. Enable HTTP/2

Already enabled in Nginx configuration.

---

## Cost Optimization

### 1. Use Reserved Instances

For production workloads, purchase Reserved Instances for 1-3 years to save up to 72%.

### 2. Use Spot Instances for Workers

For Celery workers, consider using Spot Instances to reduce costs.

### 3. Enable EBS Optimization

Use gp3 volumes instead of gp2 for better price/performance.

### 4. Set up Auto Scaling

Scale down during off-peak hours.

### 5. Use S3 for Static Assets

Move uploaded files to S3 to reduce EBS costs.

---

## Disaster Recovery

### 1. Backup Strategy

- Daily database backups to S3
- Weekly EBS snapshots
- Keep backups for 30 days
- Test restore procedures monthly

### 2. Recovery Procedure

```bash
# Restore database from backup
gunzip < db_backup_YYYYMMDD_HHMMSS.sql.gz | sudo -u postgres psql job_platform

# Or restore from S3
aws s3 cp s3://your-backup-bucket/backups/db_backup_YYYYMMDD_HHMMSS.sql.gz .
gunzip < db_backup_YYYYMMDD_HHMMSS.sql.gz | sudo -u postgres psql job_platform
```

---

## Next Steps

1. Configure Route 53 for DNS management
2. Set up CloudWatch alarms for critical metrics
3. Configure AWS Backup for automated backups
4. Set up staging environment
5. Implement CI/CD pipeline with CodePipeline or GitHub Actions
6. Configure AWS WAF for additional security
7. Set up CloudFront CDN for static assets
8. Enable AWS Shield for DDoS protection

---

## Support and Resources

- AWS Documentation: https://docs.aws.amazon.com/
- EC2 Best Practices: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-best-practices.html
- Check logs: `/var/log/job-platform/`
- Review systemd journals: `sudo journalctl -u <service-name>`
- Monitor Sentry for application errors
- AWS Support: https://console.aws.amazon.com/support/

---

## Appendix: Useful Commands

```bash
# Service management
sudo systemctl status <service-name>
sudo systemctl restart <service-name>
sudo systemctl stop <service-name>
sudo systemctl start <service-name>

# Log viewing
sudo journalctl -u <service-name> -f
sudo journalctl -u <service-name> --since "1 hour ago"
tail -f /var/log/job-platform/*.log

# Resource monitoring
htop
iotop
nethogs
df -h
free -h

# Network testing
curl -I https://your-domain.com
curl http://127.0.0.1:8000/api/health
netstat -tulpn | grep LISTEN

# Database
sudo -u postgres psql job_platform
psql -h localhost -U job_platform_user -d job_platform

# Redis
redis-cli -a your_redis_password_here
redis-cli -a your_redis_password_here INFO
redis-cli -a your_redis_password_here MONITOR
```
