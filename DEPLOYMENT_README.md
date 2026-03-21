# Cloud Deployment Documentation

Complete deployment guides for the Job Aggregation Platform on Google Cloud Platform (GCP) Compute Engine and Amazon Web Services (AWS) EC2.

## 📚 Documentation Overview

This repository contains comprehensive deployment documentation for deploying the Job Aggregation Platform on cloud infrastructure with all services (PostgreSQL, Redis, Backend, Celery, Frontend) installed natively on the instance.

### Available Guides

1. **[GCP Compute Engine Deployment](DEPLOYMENT_GCP_COMPUTE_ENGINE.md)** - Complete step-by-step guide for Google Cloud Platform
2. **[AWS EC2 Deployment](DEPLOYMENT_AWS_EC2.md)** - Complete step-by-step guide for Amazon Web Services
3. **[Cloud Comparison Guide](DEPLOYMENT_CLOUD_COMPARISON.md)** - Detailed comparison to help you choose between GCP and AWS
4. **[Quick Start Guide](DEPLOYMENT_CLOUD_QUICK_START.md)** - Fast-track deployment in under 2 hours

### Automated Setup Scripts

- **[GCP Setup Script](scripts/gcp-setup.sh)** - Automated installation for GCP Compute Engine
- **[AWS Setup Script](scripts/aws-setup.sh)** - Automated installation for AWS EC2

---

## 🚀 Quick Start

### Choose Your Platform

**New to cloud?** → Start with GCP (simpler interface)
**Need extensive ecosystem?** → Choose AWS (more services)
**Can't decide?** → Read the [comparison guide](DEPLOYMENT_CLOUD_COMPARISON.md)

### Deployment Time

- **Automated Setup:** 30 minutes
- **Manual Setup:** 1.5-2 hours
- **Full Configuration:** 2-3 hours

### Prerequisites

- Cloud account (GCP or AWS) with billing enabled
- Domain name (optional but recommended)
- SSH key pair
- Basic Linux command line knowledge

---

## 📖 Documentation Structure

### For GCP Users

1. Read [DEPLOYMENT_GCP_COMPUTE_ENGINE.md](DEPLOYMENT_GCP_COMPUTE_ENGINE.md)
2. Use [scripts/gcp-setup.sh](scripts/gcp-setup.sh) for automated setup
3. Refer to [DEPLOYMENT_CLOUD_QUICK_START.md](DEPLOYMENT_CLOUD_QUICK_START.md) for quick reference

### For AWS Users

1. Read [DEPLOYMENT_AWS_EC2.md](DEPLOYMENT_AWS_EC2.md)
2. Use [scripts/aws-setup.sh](scripts/aws-setup.sh) for automated setup
3. Refer to [DEPLOYMENT_CLOUD_QUICK_START.md](DEPLOYMENT_CLOUD_QUICK_START.md) for quick reference

### For Decision Making

1. Read [DEPLOYMENT_CLOUD_COMPARISON.md](DEPLOYMENT_CLOUD_COMPARISON.md)
2. Compare costs, features, and use cases
3. Choose the platform that fits your needs

---

## 🏗️ Architecture Overview

### Services Deployed

```
┌─────────────────────────────────────────────┐
│           Cloud Instance (VM)                │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Nginx   │  │ Frontend │  │ Backend  │  │
│  │  (443)   │→ │  (3000)  │  │  (8000)  │  │
│  └──────────┘  └──────────┘  └──────────┘  │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │PostgreSQL│  │  Redis   │  │  Celery  │  │
│  │  (5432)  │  │  (6379)  │  │  Worker  │  │
│  └──────────┘  └──────────┘  └──────────┘  │
│                                              │
└─────────────────────────────────────────────┘
```

### Technology Stack

- **Web Server:** Nginx (reverse proxy, SSL termination)
- **Frontend:** Next.js 14 (React framework)
- **Backend:** FastAPI (Python web framework)
- **Database:** PostgreSQL 15
- **Cache:** Redis 7
- **Task Queue:** Celery with Redis broker
- **Process Manager:** systemd

---

## 💰 Cost Estimates

### Monthly Costs (Production)

| Component | GCP | AWS |
|-----------|-----|-----|
| Compute (4 vCPU, 16GB RAM) | $120 | $120 |
| Storage (50GB SSD) | $8 | $4 |
| Data Transfer (100GB) | $12 | $9 |
| **Total** | **~$140** | **~$133** |

### Cost Optimization

- Use committed/reserved instances for 40-70% savings
- Implement auto-scaling for variable workloads
- Use spot/preemptible instances for dev/test
- Monitor and optimize resource usage

---

## 🔒 Security Features

### Implemented Security Measures

- ✅ SSL/TLS encryption (Let's Encrypt)
- ✅ Firewall configuration (UFW + Cloud firewall)
- ✅ Rate limiting (Nginx)
- ✅ Security headers (HSTS, CSP, etc.)
- ✅ Database password protection
- ✅ Redis authentication
- ✅ SSH key-based authentication
- ✅ Regular security updates
- ✅ Log monitoring and rotation
- ✅ Sentry error tracking

### Security Checklist

See the security checklist in each deployment guide for a complete list of security measures to implement.

---

## 📊 Performance Specifications

### Recommended Instance Sizes

| Environment | GCP | AWS | Monthly Cost |
|-------------|-----|-----|--------------|
| Development | e2-medium | t3.medium | ~$25 |
| Staging | e2-standard-2 | t3.large | ~$60 |
| Production (Small) | e2-standard-4 | t3.xlarge | ~$120 |
| Production (Medium) | e2-standard-8 | t3.2xlarge | ~$240 |

### Performance Metrics

- **Response Time:** < 200ms (API endpoints)
- **Throughput:** 100+ requests/second
- **Concurrent Users:** 500+ simultaneous users
- **Database Connections:** 200 max connections
- **Uptime:** 99.9% target

---

## 🛠️ Maintenance

### Daily Tasks (2 minutes)

```bash
# Check service status
sudo systemctl status job-platform-backend job-platform-celery

# Check resources
df -h && free -h
```

### Weekly Tasks (10 minutes)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Restart services
sudo systemctl restart job-platform-backend
sudo systemctl restart job-platform-celery
```

### Monthly Tasks (30 minutes)

- Review logs for errors
- Check backup integrity
- Review resource usage
- Update dependencies
- Security audit

---

## 🔄 Backup Strategy

### Automated Backups

- **Database:** Daily at 2 AM (7-day retention)
- **EBS/Disk Snapshots:** Weekly (30-day retention)
- **Application Files:** On deployment
- **Configuration:** Version controlled in Git

### Backup Locations

- **GCP:** Cloud Storage buckets
- **AWS:** S3 buckets
- **Local:** `/home/jobplatform/backups`

---

## 📈 Monitoring

### Built-in Monitoring

- **Application Logs:** `/var/log/job-platform/`
- **System Logs:** `journalctl`
- **Nginx Logs:** `/var/log/nginx/`
- **Database Logs:** PostgreSQL logs
- **Error Tracking:** Sentry

### Cloud Monitoring

- **GCP:** Cloud Monitoring (Stackdriver)
- **AWS:** CloudWatch

### Key Metrics to Monitor

- CPU usage
- Memory usage
- Disk space
- Network traffic
- Database connections
- Response times
- Error rates

---

## 🚨 Troubleshooting

### Common Issues

1. **Service won't start** → Check logs with `journalctl`
2. **502 Bad Gateway** → Backend not running or misconfigured
3. **Database connection failed** → Check PostgreSQL status and credentials
4. **Celery not processing** → Check Redis connection
5. **Out of disk space** → Clean logs and old backups

### Getting Help

1. Check the troubleshooting section in your platform's guide
2. Review application logs
3. Check system logs
4. Verify service status
5. Test connections manually

---

## 📝 Post-Deployment Checklist

- [ ] All services running and enabled
- [ ] SSL certificate installed and auto-renewal configured
- [ ] Firewall rules configured
- [ ] DNS pointing to instance
- [ ] Environment variables configured
- [ ] Database migrations completed
- [ ] Backups scheduled and tested
- [ ] Monitoring configured
- [ ] Log rotation configured
- [ ] Security hardening completed
- [ ] Performance testing completed
- [ ] Documentation updated with instance-specific details

---

## 🔗 Related Documentation

### Application Documentation

- [API Documentation](docs/API_DOCUMENTATION.md)
- [Developer Documentation](docs/DEVELOPER_DOCUMENTATION.md)
- [User Guide - Job Seekers](docs/USER_GUIDE_JOB_SEEKERS.md)
- [User Guide - Employers](docs/USER_GUIDE_EMPLOYERS.md)

### Deployment Documentation

- [Docker Deployment](backend/DOCKER_DEPLOYMENT.md)
- [Production Deployment Guide](backend/PRODUCTION_DEPLOYMENT_GUIDE.md)
- [Deployment Quick Reference](DEPLOYMENT_QUICK_REFERENCE.md)

### Testing Documentation

- [Security Testing Guide](backend/SECURITY_TESTING_GUIDE.md)
- [Load Testing Guide](backend/LOAD_TESTING_GUIDE.md)
- [Manual Testing Guide](MANUAL_TESTING_GUIDE.md)

---

## 🤝 Contributing

If you find issues with the deployment documentation or have suggestions for improvements:

1. Open an issue describing the problem
2. Submit a pull request with fixes
3. Update documentation with your learnings

---

## 📄 License

This documentation is part of the Job Aggregation Platform project.

---

## 🆘 Support

For deployment support:

1. Check the troubleshooting section in your platform's guide
2. Review the quick start guide
3. Check application logs
4. Consult cloud provider documentation
5. Open an issue in the repository

---

## 🎯 Next Steps

After successful deployment:

1. **Configure DNS** - Point your domain to the instance
2. **Set up monitoring** - Configure CloudWatch/Cloud Monitoring
3. **Load testing** - Verify performance under load
4. **Security audit** - Run security scans
5. **Staging environment** - Create for testing updates
6. **CI/CD pipeline** - Automate deployments
7. **Documentation** - Document your specific configuration
8. **Team training** - Train team on maintenance procedures

---

## 📞 Emergency Procedures

### Service Down

```bash
# Check all services
sudo systemctl status job-platform-backend
sudo systemctl status job-platform-celery
sudo systemctl status postgresql
sudo systemctl status redis-server
sudo systemctl status nginx

# Restart all services
sudo systemctl restart job-platform-backend
sudo systemctl restart job-platform-celery
sudo systemctl restart nginx
```

### Database Issues

```bash
# Check PostgreSQL
sudo systemctl status postgresql
sudo -u postgres psql -d job_platform -c "SELECT 1;"

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### High Load

```bash
# Check resources
htop
df -h
free -h

# Check connections
sudo netstat -tulpn | grep LISTEN

# Scale vertically (increase instance size)
# Or scale horizontally (add more instances)
```

---

**Ready to deploy? Choose your platform and follow the guide!**

- [Deploy on GCP →](DEPLOYMENT_GCP_COMPUTE_ENGINE.md)
- [Deploy on AWS →](DEPLOYMENT_AWS_EC2.md)
- [Compare Platforms →](DEPLOYMENT_CLOUD_COMPARISON.md)
- [Quick Start →](DEPLOYMENT_CLOUD_QUICK_START.md)
