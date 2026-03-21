# Cloud Deployment Quick Start Guide

Fast-track guide to deploy the Job Aggregation Platform on GCP or AWS in under 2 hours.

## Prerequisites Checklist

- [ ] Cloud account (GCP or AWS) with billing enabled
- [ ] Domain name configured (optional but recommended)
- [ ] SSH key pair generated
- [ ] Git repository access
- [ ] Stripe account (for payments)
- [ ] Sentry account (for monitoring)
- [ ] Email SMTP credentials

---

## Quick Decision: GCP or AWS?

**Choose GCP if:** You want simplicity and are new to cloud
**Choose AWS if:** You need extensive documentation and ecosystem

**Can't decide?** Flip a coin - both work great!

---

## GCP Compute Engine - 30 Minute Setup

### Step 1: Create Instance (5 min)

```bash
gcloud compute instances create job-platform \
  --zone=us-central1-a \
  --machine-type=e2-standard-4 \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB \
  --boot-disk-type=pd-ssd \
  --tags=http-server,https-server

# Connect
gcloud compute ssh job-platform --zone=us-central1-a
```

### Step 2: Run Installation Script (20 min)

```bash
# Download and run automated setup script
curl -o setup.sh https://raw.githubusercontent.com/yourusername/job-platform/main/scripts/gcp-setup.sh
chmod +x setup.sh
sudo ./setup.sh
```

### Step 3: Configure Environment (5 min)

```bash
sudo su - jobplatform
cd /home/jobplatform/job-platform/backend
vim .env.production
# Fill in your credentials
```

### Step 4: Start Services

```bash
exit
sudo systemctl start job-platform-backend
sudo systemctl start job-platform-frontend
sudo systemctl start job-platform-celery
```

---

## AWS EC2 - 30 Minute Setup

### Step 1: Launch Instance (5 min)

```bash
aws ec2 run-instances \
  --image-id ami-0c7217cdde317cfec \
  --instance-type t3.xlarge \
  --key-name your-key \
  --security-group-ids sg-xxxxx \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":50,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=job-platform}]'

# Connect
ssh -i your-key.pem ubuntu@your-elastic-ip
```

### Step 2: Run Installation Script (20 min)

```bash
# Download and run automated setup script
curl -o setup.sh https://raw.githubusercontent.com/yourusername/job-platform/main/scripts/aws-setup.sh
chmod +x setup.sh
sudo ./setup.sh
```

### Step 3: Configure Environment (5 min)

```bash
sudo su - jobplatform
cd /home/jobplatform/job-platform/backend
vim .env.production
# Fill in your credentials
```

### Step 4: Start Services

```bash
exit
sudo systemctl start job-platform-backend
sudo systemctl start job-platform-frontend
sudo systemctl start job-platform-celery
```

---

## Essential Commands Reference

### Service Management

```bash
# Check status
sudo systemctl status job-platform-backend
sudo systemctl status job-platform-frontend
sudo systemctl status job-platform-celery

# Restart services
sudo systemctl restart job-platform-backend
sudo systemctl restart job-platform-frontend
sudo systemctl restart job-platform-celery

# View logs
sudo journalctl -u job-platform-backend -f
tail -f /var/log/job-platform/backend-error.log
```

### Database Operations

```bash
# Connect to database
sudo -u postgres psql job_platform

# Backup database
sudo -u postgres pg_dump job_platform | gzip > backup.sql.gz

# Restore database
gunzip < backup.sql.gz | sudo -u postgres psql job_platform

# Run migrations
cd /home/jobplatform/job-platform/backend
source venv/bin/activate
alembic upgrade head
```

### Monitoring

```bash
# System resources
htop
df -h
free -h

# Check services
curl http://localhost:8000/api/health
curl http://localhost:3000

# Network
sudo netstat -tulpn | grep LISTEN
```

---

## SSL Certificate Setup (15 min)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

---

## Firewall Configuration

### GCP

```bash
gcloud compute firewall-rules create allow-http --allow tcp:80 --target-tags http-server
gcloud compute firewall-rules create allow-https --allow tcp:443 --target-tags https-server
```

### AWS

```bash
# Via Security Groups in AWS Console or:
aws ec2 authorize-security-group-ingress --group-id sg-xxxxx --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id sg-xxxxx --protocol tcp --port 443 --cidr 0.0.0.0/0
```

---

## Environment Variables Template

```env
# Database
DATABASE_URL=postgresql://job_platform_user:PASSWORD@localhost:5432/job_platform

# Redis
REDIS_URL=redis://:PASSWORD@localhost:6379/0

# Security
SECRET_KEY=GENERATE_WITH_openssl_rand_hex_32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
ENVIRONMENT=production
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# CORS
CORS_ORIGINS=https://your-domain.com

# Celery
CELERY_BROKER_URL=redis://:PASSWORD@localhost:6379/0
CELERY_RESULT_BACKEND=redis://:PASSWORD@localhost:6379/1

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@your-domain.com

# Stripe
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# Sentry
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
```

---

## Troubleshooting Quick Fixes

### Backend won't start

```bash
# Check logs
sudo journalctl -u job-platform-backend -n 50

# Test database connection
sudo -u postgres psql -d job_platform -c "SELECT 1;"

# Restart
sudo systemctl restart job-platform-backend
```

### Celery not processing

```bash
# Check Redis
redis-cli -a PASSWORD ping

# Check Celery logs
sudo journalctl -u job-platform-celery -n 50

# Restart
sudo systemctl restart job-platform-celery
```

### Nginx 502 Error

```bash
# Check backend
curl http://127.0.0.1:8000/api/health

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log

# Restart Nginx
sudo systemctl restart nginx
```

### Out of disk space

```bash
# Check usage
df -h

# Clean logs
sudo journalctl --vacuum-time=7d

# Clean old backups
find /home/jobplatform/backups -mtime +7 -delete
```

---

## Daily Maintenance Tasks

```bash
# Morning check (2 minutes)
sudo systemctl status job-platform-backend job-platform-celery
df -h
free -h

# Weekly tasks (10 minutes)
sudo apt update && sudo apt upgrade -y
sudo systemctl restart job-platform-backend
sudo systemctl restart job-platform-celery

# Monthly tasks (30 minutes)
# Review logs for errors
# Check backup integrity
# Review resource usage
# Update dependencies
```

---

## Backup Strategy

### Automated Daily Backup

```bash
# Create backup script
sudo vim /home/jobplatform/backup.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/jobplatform/backups"
mkdir -p $BACKUP_DIR

# Database backup
sudo -u postgres pg_dump job_platform | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Keep last 7 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete
```

```bash
# Make executable
chmod +x /home/jobplatform/backup.sh

# Add to crontab
sudo crontab -e
0 2 * * * /home/jobplatform/backup.sh
```

---

## Performance Tuning Quick Wins

### PostgreSQL

```bash
sudo vim /etc/postgresql/15/main/postgresql.conf
```

```conf
shared_buffers = 4GB
effective_cache_size = 12GB
work_mem = 64MB
maintenance_work_mem = 1GB
```

### Redis

```bash
sudo vim /etc/redis/redis.conf
```

```conf
maxmemory 2gb
maxmemory-policy allkeys-lru
```

### Nginx

```bash
sudo vim /etc/nginx/nginx.conf
```

```nginx
worker_processes auto;
worker_connections 2048;
keepalive_timeout 65;
```

---

## Scaling Checklist

When you need more power:

### Vertical Scaling (Easier)

**GCP:**
```bash
gcloud compute instances stop job-platform
gcloud compute instances set-machine-type job-platform --machine-type e2-standard-8
gcloud compute instances start job-platform
```

**AWS:**
```bash
aws ec2 stop-instances --instance-ids i-xxxxx
aws ec2 modify-instance-attribute --instance-id i-xxxxx --instance-type t3.2xlarge
aws ec2 start-instances --instance-ids i-xxxxx
```

### Horizontal Scaling (Better)

1. Create load balancer
2. Create instance template/AMI
3. Set up auto-scaling group
4. Configure health checks
5. Update DNS

---

## Security Hardening Checklist

- [ ] Change all default passwords
- [ ] Enable firewall (UFW)
- [ ] Configure security groups properly
- [ ] Install fail2ban
- [ ] Enable automatic security updates
- [ ] Set up SSH key-only authentication
- [ ] Disable root SSH login
- [ ] Configure rate limiting in Nginx
- [ ] Enable SSL/TLS
- [ ] Set up Sentry for error tracking
- [ ] Configure log rotation
- [ ] Regular backup testing

---

## Cost Monitoring

### GCP

```bash
# View current costs
gcloud billing accounts list
gcloud billing projects describe PROJECT_ID

# Set up budget alerts in Console
```

### AWS

```bash
# View current costs
aws ce get-cost-and-usage --time-period Start=2024-01-01,End=2024-01-31 --granularity MONTHLY --metrics BlendedCost

# Set up budget alerts in Console
```

---

## Getting Help

### Check Logs First

```bash
# Application logs
sudo journalctl -u job-platform-backend -n 100
sudo journalctl -u job-platform-celery -n 100
tail -f /var/log/job-platform/*.log

# System logs
sudo journalctl -xe
dmesg | tail -50
```

### Common Log Locations

- Backend: `/var/log/job-platform/backend-error.log`
- Celery: `/var/log/job-platform/celery-worker.log`
- Nginx: `/var/log/nginx/error.log`
- PostgreSQL: `/var/log/postgresql/postgresql-15-main.log`
- Redis: `/var/log/redis/redis-server.log`

---

## Next Steps After Deployment

1. **Configure DNS** - Point domain to server IP
2. **Set up monitoring** - CloudWatch/Cloud Monitoring
3. **Configure backups** - Automated to cloud storage
4. **Load testing** - Verify performance
5. **Security audit** - Run security scans
6. **Documentation** - Document your specific setup
7. **Staging environment** - Create for testing
8. **CI/CD pipeline** - Automate deployments

---

## Emergency Contacts

- Cloud Provider Support
- Database Administrator
- DevOps Team
- Application Developer
- Security Team

---

## Useful Resources

- Full GCP Guide: `DEPLOYMENT_GCP_COMPUTE_ENGINE.md`
- Full AWS Guide: `DEPLOYMENT_AWS_EC2.md`
- Comparison Guide: `DEPLOYMENT_CLOUD_COMPARISON.md`
- Application Docs: `docs/DEPLOYMENT_DOCUMENTATION.md`

---

## Success Checklist

- [ ] Instance running
- [ ] PostgreSQL installed and configured
- [ ] Redis installed and configured
- [ ] Backend service running
- [ ] Frontend service running
- [ ] Celery workers running
- [ ] Nginx configured
- [ ] SSL certificate installed
- [ ] Firewall configured
- [ ] Backups scheduled
- [ ] Monitoring enabled
- [ ] DNS configured
- [ ] Application accessible via domain
- [ ] All tests passing

**Congratulations! Your Job Aggregation Platform is now live! 🎉**
