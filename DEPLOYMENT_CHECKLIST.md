# Cloud Deployment Checklist

Use this checklist to ensure a complete and successful deployment of the Job Aggregation Platform on GCP or AWS.

---

## Pre-Deployment Preparation

### Account Setup
- [ ] Cloud account created (GCP or AWS)
- [ ] Billing enabled and verified
- [ ] Payment method added
- [ ] Budget alerts configured
- [ ] IAM users/roles created (if needed)

### Domain & DNS
- [ ] Domain name purchased
- [ ] DNS provider access confirmed
- [ ] DNS records ready to update

### Third-Party Services
- [ ] Stripe account created
- [ ] Stripe API keys obtained (test and live)
- [ ] Sentry account created
- [ ] Sentry DSN obtained
- [ ] SMTP credentials obtained (for email)

### Local Preparation
- [ ] SSH key pair generated
- [ ] Git repository accessible
- [ ] Environment variables documented
- [ ] Passwords generated and stored securely

---

## Instance Setup

### Create Instance
- [ ] Instance created with correct specifications
  - [ ] Machine type: e2-standard-4 (GCP) or t3.xlarge (AWS)
  - [ ] OS: Ubuntu 22.04 LTS
  - [ ] Storage: 50GB SSD
  - [ ] Region selected (closest to users)
- [ ] Elastic/Static IP allocated
- [ ] Instance tagged appropriately
- [ ] SSH access verified

### Initial Configuration
- [ ] Connected to instance via SSH
- [ ] System updated (`apt update && apt upgrade`)
- [ ] Basic tools installed (git, curl, wget, vim)
- [ ] Timezone configured
- [ ] Hostname set

---

## Software Installation

### Database (PostgreSQL)
- [ ] PostgreSQL 15 installed
- [ ] PostgreSQL service started and enabled
- [ ] Database created (`job_platform`)
- [ ] Database user created (`job_platform_user`)
- [ ] User password set (strong password)
- [ ] Privileges granted
- [ ] Connection tested
- [ ] PostgreSQL optimized for instance size

### Cache (Redis)
- [ ] Redis installed
- [ ] Redis service started and enabled
- [ ] Redis password configured
- [ ] Redis bound to localhost
- [ ] Connection tested
- [ ] Memory limits configured

### Application Runtime
- [ ] Python 3.11 installed
- [ ] Python virtual environment created
- [ ] Node.js 20 installed
- [ ] npm verified working

### Web Server
- [ ] Nginx installed
- [ ] Nginx service enabled
- [ ] Default site disabled

### SSL Certificate
- [ ] Certbot installed
- [ ] Certbot nginx plugin installed

---

## Application Setup

### User & Directories
- [ ] Application user created (`jobplatform`)
- [ ] Log directory created (`/var/log/job-platform`)
- [ ] PID directory created (`/var/run/celery`)
- [ ] Backup directory created
- [ ] Permissions set correctly

### Repository
- [ ] Repository cloned to `/home/jobplatform/job-platform`
- [ ] Correct branch checked out
- [ ] Repository ownership set to jobplatform user

### Backend Setup
- [ ] Virtual environment created
- [ ] Dependencies installed from requirements.txt
- [ ] Gunicorn installed
- [ ] Environment file created (`.env.production`)
- [ ] All environment variables configured:
  - [ ] DATABASE_URL
  - [ ] REDIS_URL
  - [ ] SECRET_KEY
  - [ ] CORS_ORIGINS
  - [ ] STRIPE_SECRET_KEY
  - [ ] STRIPE_PUBLISHABLE_KEY
  - [ ] SENTRY_DSN
  - [ ] SMTP credentials
- [ ] Database migrations run (`alembic upgrade head`)
- [ ] Backend tested manually

### Frontend Setup
- [ ] Dependencies installed (`npm install`)
- [ ] Environment file created (`.env.production`)
- [ ] Environment variables configured:
  - [ ] NEXT_PUBLIC_API_URL
  - [ ] NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY
- [ ] Production build created (`npm run build`)
- [ ] Frontend tested manually

---

## Service Configuration

### Backend Service
- [ ] Systemd service file created (`job-platform-backend.service`)
- [ ] Service file configured correctly
- [ ] Service enabled
- [ ] Service started
- [ ] Service status verified (running)
- [ ] Logs checked for errors

### Frontend Service
- [ ] Systemd service file created (`job-platform-frontend.service`)
- [ ] Service file configured correctly
- [ ] Service enabled
- [ ] Service started
- [ ] Service status verified (running)
- [ ] Logs checked for errors

### Celery Worker Service
- [ ] Systemd service file created (`job-platform-celery.service`)
- [ ] Service file configured correctly
- [ ] Service enabled
- [ ] Service started
- [ ] Service status verified (running)
- [ ] Logs checked for errors

### Celery Beat Service
- [ ] Systemd service file created (`job-platform-celery-beat.service`)
- [ ] Service file configured correctly
- [ ] Service enabled
- [ ] Service started
- [ ] Service status verified (running)
- [ ] Logs checked for errors

---

## Nginx Configuration

### Configuration File
- [ ] Nginx config file created (`/etc/nginx/sites-available/job-platform`)
- [ ] Upstream servers configured
- [ ] Rate limiting configured
- [ ] HTTP to HTTPS redirect configured
- [ ] SSL certificate paths configured
- [ ] Security headers configured
- [ ] Proxy settings configured
- [ ] Static file caching configured
- [ ] Config file symlinked to sites-enabled
- [ ] Nginx configuration tested (`nginx -t`)
- [ ] Nginx restarted

---

## SSL/TLS Setup

### Certificate Installation
- [ ] Certbot directory created (`/var/www/certbot`)
- [ ] SSL certificate obtained
- [ ] Certificate for main domain
- [ ] Certificate for www subdomain
- [ ] Auto-renewal tested (`certbot renew --dry-run`)
- [ ] Auto-renewal timer enabled
- [ ] HTTPS working correctly

---

## Firewall & Security

### Cloud Firewall (GCP/AWS)
- [ ] HTTP (80) allowed
- [ ] HTTPS (443) allowed
- [ ] SSH (22) allowed (restricted to your IP if possible)
- [ ] All other ports blocked
- [ ] Firewall rules tested

### Instance Firewall (UFW)
- [ ] UFW installed
- [ ] SSH allowed
- [ ] HTTP allowed
- [ ] HTTPS allowed
- [ ] UFW enabled
- [ ] UFW status verified

### Security Hardening
- [ ] All default passwords changed
- [ ] Strong passwords used everywhere
- [ ] SSH key-based authentication configured
- [ ] Root SSH login disabled
- [ ] Fail2ban installed (optional)
- [ ] Automatic security updates enabled

---

## DNS Configuration

### DNS Records
- [ ] A record created (@ → instance IP)
- [ ] A record created (www → instance IP)
- [ ] DNS propagation verified
- [ ] Domain accessible via browser

---

## Backup Configuration

### Database Backups
- [ ] Backup script created
- [ ] Backup directory configured
- [ ] Backup tested manually
- [ ] Cron job configured (daily at 2 AM)
- [ ] Backup retention configured (7 days)
- [ ] Cloud storage configured (optional)

### Disk Snapshots
- [ ] Snapshot schedule configured
- [ ] Weekly snapshots enabled
- [ ] Snapshot retention configured (30 days)
- [ ] Snapshot tested

---

## Monitoring Setup

### Application Monitoring
- [ ] Sentry configured and tested
- [ ] Error tracking verified
- [ ] Log rotation configured
- [ ] Log retention configured

### Cloud Monitoring
- [ ] CloudWatch/Cloud Monitoring enabled
- [ ] CPU alerts configured
- [ ] Memory alerts configured
- [ ] Disk space alerts configured
- [ ] Service health checks configured

### Log Management
- [ ] Log rotation configured (`/etc/logrotate.d/job-platform`)
- [ ] Log retention set (14 days)
- [ ] Logs accessible and readable

---

## Testing

### Functionality Testing
- [ ] Homepage loads correctly
- [ ] API health endpoint responds (`/api/health`)
- [ ] User registration works
- [ ] User login works
- [ ] Job search works
- [ ] Job posting works (employers)
- [ ] Application submission works
- [ ] Payment processing works (Stripe)
- [ ] Email sending works

### Performance Testing
- [ ] Response times acceptable (< 200ms)
- [ ] Page load times acceptable (< 2s)
- [ ] Database queries optimized
- [ ] Caching working correctly

### Security Testing
- [ ] HTTPS enforced
- [ ] Security headers present
- [ ] Rate limiting working
- [ ] SQL injection protection verified
- [ ] XSS protection verified
- [ ] CSRF protection verified

---

## Documentation

### Instance Documentation
- [ ] Instance details documented (IP, region, size)
- [ ] Passwords stored securely
- [ ] Environment variables documented
- [ ] Service configurations documented
- [ ] Backup procedures documented
- [ ] Recovery procedures documented

### Team Documentation
- [ ] Deployment guide shared with team
- [ ] Access credentials shared securely
- [ ] Maintenance procedures documented
- [ ] Emergency contacts documented
- [ ] Escalation procedures documented

---

## Post-Deployment

### Verification
- [ ] All services running
- [ ] No errors in logs
- [ ] Application accessible via domain
- [ ] SSL certificate valid
- [ ] Monitoring working
- [ ] Backups running
- [ ] Email notifications working

### Optimization
- [ ] Resource usage monitored
- [ ] Performance metrics collected
- [ ] Bottlenecks identified
- [ ] Optimizations applied

### Maintenance Plan
- [ ] Update schedule defined
- [ ] Backup verification schedule set
- [ ] Monitoring review schedule set
- [ ] Security audit schedule set

---

## Launch Preparation

### Pre-Launch
- [ ] Staging environment tested
- [ ] Load testing completed
- [ ] Security audit completed
- [ ] Backup and recovery tested
- [ ] Rollback plan prepared
- [ ] Team trained on procedures

### Launch Day
- [ ] Final backup taken
- [ ] DNS updated to production
- [ ] SSL certificate verified
- [ ] All services verified running
- [ ] Monitoring actively watched
- [ ] Team on standby

### Post-Launch
- [ ] Monitor for 24 hours
- [ ] Check error rates
- [ ] Verify performance metrics
- [ ] Review logs for issues
- [ ] Collect user feedback
- [ ] Document any issues

---

## Ongoing Maintenance

### Daily (2 minutes)
- [ ] Check service status
- [ ] Check disk space
- [ ] Check memory usage
- [ ] Review error logs

### Weekly (10 minutes)
- [ ] Update system packages
- [ ] Restart services
- [ ] Review monitoring alerts
- [ ] Check backup success

### Monthly (30 minutes)
- [ ] Review logs for patterns
- [ ] Test backup restoration
- [ ] Review resource usage
- [ ] Update dependencies
- [ ] Security audit
- [ ] Performance review

### Quarterly (2 hours)
- [ ] Full security audit
- [ ] Disaster recovery drill
- [ ] Performance optimization
- [ ] Cost optimization review
- [ ] Documentation update
- [ ] Team training refresh

---

## Emergency Procedures

### Service Down
- [ ] Emergency contact list available
- [ ] Restart procedures documented
- [ ] Rollback procedures documented
- [ ] Communication plan defined

### Data Loss
- [ ] Backup restoration procedure tested
- [ ] Recovery time objective (RTO) defined
- [ ] Recovery point objective (RPO) defined

### Security Incident
- [ ] Incident response plan documented
- [ ] Security team contacts available
- [ ] Forensics procedures defined

---

## Sign-Off

### Deployment Team
- [ ] System Administrator: _________________ Date: _______
- [ ] DevOps Engineer: _________________ Date: _______
- [ ] Backend Developer: _________________ Date: _______
- [ ] Frontend Developer: _________________ Date: _______

### Management Approval
- [ ] Technical Lead: _________________ Date: _______
- [ ] Project Manager: _________________ Date: _______

---

## Notes

Use this space to document any deployment-specific notes, issues encountered, or deviations from the standard procedure:

```
_________________________________________________________________

_________________________________________________________________

_________________________________________________________________

_________________________________________________________________

_________________________________________________________________
```

---

**Deployment Status:** [ ] In Progress  [ ] Completed  [ ] Issues Found

**Deployment Date:** _______________

**Deployed By:** _______________

**Instance Details:**
- Platform: [ ] GCP  [ ] AWS
- Instance ID: _______________
- IP Address: _______________
- Domain: _______________

---

**Congratulations on your deployment! 🎉**
