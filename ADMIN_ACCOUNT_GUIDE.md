# Admin Account Setup Guide

## Quick Setup

Run this command to create an admin account:

```bash
./CREATE_ADMIN.sh
```

This will create an admin account with:
- **Email**: admin@trusanity.com
- **Password**: Admin@123
- **Subscription**: Premium (10 years)
- **Verified**: Yes

## Custom Credentials

To create an admin with custom credentials:

```bash
./CREATE_ADMIN.sh your-email@example.com YourPassword123
```

## Login

1. Go to: http://trusanity.com/login
2. Enter your admin credentials
3. You'll be logged in as an employer with premium access

## Admin Capabilities

As an admin (premium employer), you have:

✅ **Unlimited Job Postings** - No monthly limits
✅ **Featured Listings** - Up to 10 featured jobs
✅ **Analytics Access** - Full analytics dashboard
✅ **Application Tracking** - Track all applications
✅ **URL Import** - Import jobs from external URLs
✅ **Priority Support** - Premium support access

## Admin Dashboard

After login, access:
- `/employer/dashboard` - Main dashboard
- `/employer/jobs` - Manage jobs
- `/employer/analytics` - View analytics
- `/employer/applications` - Track applications
- `/employer/subscription` - Subscription management

## Security Notes

⚠️ **Important**:
1. Change the default password after first login
2. Use a strong, unique password
3. Enable 2FA if available
4. Don't share admin credentials

## Troubleshooting

### Admin Already Exists
If you see "Admin user already exists", the account is already created. Use the existing credentials or reset the password.

### Can't Login
1. Check if backend is running: `curl http://trusanity.com/api/health`
2. Verify database connection
3. Check backend logs: `sudo journalctl -u job-platform-backend -n 50`

### Reset Admin Password

SSH into the server and run:

```bash
cd /home/jobplatform/job-platform/backend
sudo -u jobplatform bash -c 'source venv/bin/activate && python scripts/create_admin.py admin@trusanity.com NewPassword123'
```

## Manual Creation (On Server)

If you prefer to create the admin manually on the server:

```bash
# SSH into server
ssh -i trusanity-pem.pem ubuntu@3.110.220.37

# Navigate to backend
cd /home/jobplatform/job-platform/backend

# Activate virtual environment
sudo -u jobplatform bash -c 'source venv/bin/activate && python scripts/create_admin.py'
```

## API Access

You can also use the API directly:

```bash
# Register as employer
curl -X POST http://trusanity.com/api/auth/register/employer \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@trusanity.com",
    "password": "Admin@123",
    "company_name": "TruSanity Admin"
  }'

# Login
curl -X POST http://trusanity.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@trusanity.com",
    "password": "Admin@123"
  }'
```

## Next Steps

After creating the admin account:

1. ✅ Login to the platform
2. ✅ Change the default password
3. ✅ Explore the employer dashboard
4. ✅ Post a test job
5. ✅ Check analytics
6. ✅ Configure platform settings

## Support

For issues or questions:
- Check backend logs: `sudo journalctl -u job-platform-backend -f`
- Check frontend logs: `sudo -u jobplatform pm2 logs job-platform-frontend`
- Verify services: `sudo systemctl status job-platform-backend`
