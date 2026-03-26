# Complete AWS EC2 Deployment Guide - Fresh Instance

## Prerequisites
- AWS Account
- Domain name (trusanity.com)
- GitHub repository: https://github.com/Sourabh1118/TenOpps

## Part 1: Create EC2 Instance

### 1.1 Launch EC2 Instance
1. Go to AWS Console → EC2 → Launch Instance
2. **Name**: job-platform-server
3. **AMI**: Ubuntu Server 22.04 LTS (Free tier eligible)
4. **Instance Type**: t2.medium (minimum) or t2.large (recommended)
5. **Key Pair**: Create new or use existing (download .pem file)
6. **Network Settings**:
   - Allow SSH (port 22) from your IP
   - Allow HTTP (port 80) from anywhere
   - Allow HTTPS (port 443) from anywhere
7. **Storage**: 30 GB gp3 (minimum)
8. Click "Launch Instance"

### 1.2 Allocate Elastic IP
1. Go to EC2 → Elastic IPs → Allocate Elastic IP
2. Associate it with your new instance
3. Note the Elastic IP address

### 1.3 Update DNS Records
1. Go to your domain registrar (GoDaddy, Namecheap, etc.)
2. Update A records:
   - `trusanity.com` → Your Elastic IP
   - `www.trusanity.com` → Your Elastic IP
3. Wait 5-10 minutes for DNS propagation

## Part 2: Initial Server Setup

### 2.1 Connect to Server
```bash
# On your local machine
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@YOUR_ELASTIC_IP
```

### 2.2 Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### 2.3 Install Required Software
```bash
# Install Node.js 20.x
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Install Redis
sudo apt install -y redis-server

# Install Nginx
sudo apt install -y nginx

# Install PM2 globally
sudo npm install -g pm2

# Install Git
sudo apt install -y git

# Install Certbot for SSL
sudo apt install -y certbot python3-certbot-nginx
```

## Part 3: Setup PostgreSQL Database

### 3.1 Configure PostgreSQL
```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL prompt, run:
CREATE DATABASE jobplatform_db;
CREATE USER jobplatform WITH PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE jobplatform_db TO jobplatform;
ALTER DATABASE jobplatform_db OWNER TO jobplatform;
\q
```

### 3.2 Configure PostgreSQL for Local Access
```bash
# Edit pg_hba.conf
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Add this line before other rules:
# local   all             jobplatform                             md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

## Part 4: Setup Redis

```bash
# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test Redis
redis-cli ping
# Should return: PONG
```

## Part 5: Clone and Setup Application

### 5.1 Create Application User and Directory
```bash
# Create user
sudo useradd -m -s /bin/bash jobplatform
sudo usermod -aG sudo jobplatform

# Create directory
sudo mkdir -p /home/jobplatform
sudo chown -R jobplatform:jobplatform /home/jobplatform
```

### 5.2 Clone Repository
```bash
# Switch to jobplatform user
sudo su - jobplatform

# Clone repository
cd /home/jobplatform
git clone https://github.com/Sourabh1118/TenOpps.git job-platform
cd job-platform
```

## Part 6: Setup Backend

### 6.1 Create Python Virtual Environment
```bash
cd /home/jobplatform/job-platform/backend
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 6.2 Create Backend .env File
```bash
cd /home/jobplatform/job-platform/backend
nano .env
```

Paste this content (update values):
```env
# Database
DATABASE_URL=postgresql://jobplatform:your_secure_password_here@localhost/jobplatform_db

# Security
SECRET_KEY=your-super-secret-key-min-32-chars-long-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ORIGINS=["https://trusanity.com","https://www.trusanity.com"]

# Environment
ENVIRONMENT=production
```

### 6.3 Run Database Migrations
```bash
cd /home/jobplatform/job-platform/backend
source venv/bin/activate
alembic upgrade head
```

### 6.4 Create Admin Account
```bash
cd /home/jobplatform/job-platform/backend
source venv/bin/activate
python scripts/create_admin.py
```

### 6.5 Create Backend Systemd Service
```bash
# Exit jobplatform user
exit

# Create service file
sudo nano /etc/systemd/system/job-platform-backend.service
```

Paste this content:
```ini
[Unit]
Description=Job Platform Backend API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=jobplatform
WorkingDirectory=/home/jobplatform/job-platform/backend
Environment="PATH=/home/jobplatform/job-platform/backend/venv/bin"
EnvironmentFile=/home/jobplatform/job-platform/backend/.env
ExecStart=/home/jobplatform/job-platform/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 6.6 Start Backend Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable job-platform-backend
sudo systemctl start job-platform-backend
sudo systemctl status job-platform-backend
```

## Part 7: Setup Frontend

### 7.1 Install Dependencies and Build
```bash
sudo su - jobplatform
cd /home/jobplatform/job-platform/frontend
npm install
npm run build
```

### 7.2 Create Frontend .env Files
```bash
cd /home/jobplatform/job-platform/frontend

# Create .env.local
nano .env.local
```

Paste:
```env
NEXT_PUBLIC_API_URL=https://trusanity.com
NEXT_PUBLIC_API_BASE_PATH=/api
```

```bash
# Create .env.production
nano .env.production
```

Paste:
```env
NEXT_PUBLIC_API_URL=https://trusanity.com
NEXT_PUBLIC_API_BASE_PATH=/api
```

### 7.3 Start Frontend with PM2
```bash
cd /home/jobplatform/job-platform/frontend
pm2 start npm --name "job-platform-frontend" -- start
pm2 save
pm2 startup
# Copy and run the command it outputs
exit
```

## Part 8: Configure Nginx

### 8.1 Create Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/job-platform
```

Paste this content:
```nginx
server {
    listen 80;
    server_name trusanity.com www.trusanity.com;

    # Redirect HTTP to HTTPS (will be enabled after SSL)
    # return 301 https://$server_name$request_uri;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend docs
    location /docs {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
```

### 8.2 Enable Site and Test
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/job-platform /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

## Part 9: Install SSL Certificate

### 9.1 Get Let's Encrypt Certificate
```bash
sudo certbot --nginx -d trusanity.com -d www.trusanity.com
```

Follow prompts:
- Enter email address
- Agree to terms
- Choose to redirect HTTP to HTTPS (option 2)

### 9.2 Test Auto-Renewal
```bash
sudo certbot renew --dry-run
```

## Part 10: Verify Deployment

### 10.1 Check Services
```bash
# Check backend
sudo systemctl status job-platform-backend

# Check frontend
pm2 status

# Check Nginx
sudo systemctl status nginx

# Check PostgreSQL
sudo systemctl status postgresql

# Check Redis
sudo systemctl status redis-server
```

### 10.2 Test Application
1. Visit: https://trusanity.com
2. Should see homepage
3. Login: https://trusanity.com/login
   - Email: admin@trusanity.com
   - Password: Admin@123
4. After login, click "Admin Dashboard" in header
5. Should see admin dashboard with statistics

## Part 11: Firewall Configuration (Optional but Recommended)

```bash
# Install UFW
sudo apt install -y ufw

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

## Part 12: Setup Monitoring and Logs

### 12.1 View Logs
```bash
# Backend logs
sudo journalctl -u job-platform-backend -f

# Frontend logs
pm2 logs job-platform-frontend

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 12.2 Setup Log Rotation
```bash
# PM2 log rotation
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 7
```

## Troubleshooting

### Backend Not Starting
```bash
# Check logs
sudo journalctl -u job-platform-backend -n 50

# Check if port 8000 is in use
sudo lsof -i:8000

# Restart service
sudo systemctl restart job-platform-backend
```

### Frontend Not Starting
```bash
# Check PM2 logs
pm2 logs job-platform-frontend --lines 50

# Restart PM2
pm2 restart job-platform-frontend

# If port 3000 is in use
sudo lsof -i:3000
sudo kill -9 <PID>
```

### Database Connection Issues
```bash
# Test database connection
psql -U jobplatform -d jobplatform_db -h localhost

# Check PostgreSQL status
sudo systemctl status postgresql

# View PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

### SSL Certificate Issues
```bash
# Renew certificate manually
sudo certbot renew

# Check certificate status
sudo certbot certificates
```

## Maintenance Commands

### Update Application
```bash
# SSH into server
ssh -i your-key.pem ubuntu@YOUR_ELASTIC_IP

# Switch to jobplatform user
sudo su - jobplatform

# Pull latest code
cd /home/jobplatform/job-platform
git pull origin main

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
exit

# Restart backend
sudo systemctl restart job-platform-backend

# Update frontend
sudo su - jobplatform
cd /home/jobplatform/job-platform/frontend
npm install
npm run build
pm2 restart job-platform-frontend
exit
```

### Backup Database
```bash
# Create backup
sudo -u postgres pg_dump jobplatform_db > backup_$(date +%Y%m%d).sql

# Restore backup
sudo -u postgres psql jobplatform_db < backup_20240324.sql
```

## Security Checklist

- [ ] Changed default PostgreSQL password
- [ ] Created strong SECRET_KEY in backend .env
- [ ] Enabled UFW firewall
- [ ] SSL certificate installed and auto-renewal configured
- [ ] Only necessary ports open (22, 80, 443)
- [ ] Regular system updates scheduled
- [ ] Database backups configured
- [ ] Application logs monitored

## Summary

Your application is now deployed at:
- **Website**: https://trusanity.com
- **Admin Login**: https://trusanity.com/login
- **Admin Dashboard**: https://trusanity.com/admin/dashboard
- **API Docs**: https://trusanity.com/docs

Admin credentials:
- Email: admin@trusanity.com
- Password: Admin@123

Remember to change the admin password after first login!
