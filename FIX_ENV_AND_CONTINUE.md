# Fix .env File and Continue Deployment

## Problem
The `.env` file had incorrect field names that don't match the Settings model in `backend/app/core/config.py`.

## Solution

### Option 1: Use the Script (Recommended)

1. Copy the script to your server:
```bash
scp UPDATE_ENV_FILE.sh jobplatform@3.110.220.37:/home/jobplatform/
```

2. SSH to your server and run it:
```bash
ssh jobplatform@3.110.220.37
cd /home/jobplatform
chmod +x UPDATE_ENV_FILE.sh
./UPDATE_ENV_FILE.sh
```

3. It will prompt for your PostgreSQL password and create the correct `.env` file.

### Option 2: Manual Update

SSH to your server and edit the file:
```bash
ssh jobplatform@3.110.220.37
nano /home/jobplatform/job-platform/backend/.env
```

Copy the content from `CORRECT_ENV_FILE_FIXED.txt` and replace `YOUR_POSTGRESQL_PASSWORD` with your actual password.

## Key Differences Fixed

The Settings model requires these exact field names:
- ✓ `JWT_SECRET_KEY` (not just `SECRET_KEY` for JWT)
- ✓ `JWT_ALGORITHM` (not `ALGORITHM`)
- ✓ `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` (not `ACCESS_TOKEN_EXPIRE_MINUTES`)
- ✓ `JWT_REFRESH_TOKEN_EXPIRE_DAYS` (not `REFRESH_TOKEN_EXPIRE_DAYS`)
- ✓ `CELERY_BROKER_URL` (required)
- ✓ `CELERY_RESULT_BACKEND` (required)
- ✗ Removed `ENVIRONMENT` (not in Settings model, use `APP_ENV` instead)

## Next Steps

After updating the `.env` file:

1. **Run migrations:**
```bash
cd /home/jobplatform/job-platform/backend
source venv/bin/activate
alembic upgrade head
```

2. **Create admin account:**
```bash
python scripts/create_admin.py
```

3. **Start backend service:**
```bash
sudo systemctl start job-platform-backend
sudo systemctl status job-platform-backend
```

4. **Build and start frontend:**
```bash
cd /home/jobplatform/job-platform/frontend
npm run build
pm2 start npm --name "job-platform-frontend" -- start
pm2 save
```

5. **Configure Nginx** (follow section 5 of FRESH_EC2_DEPLOYMENT_GUIDE.md)

6. **Install SSL certificate** (follow section 6 of FRESH_EC2_DEPLOYMENT_GUIDE.md)

## Verify Everything Works

```bash
# Check backend
curl http://localhost:8000/health

# Check frontend
curl http://localhost:3000

# Check services
sudo systemctl status job-platform-backend
pm2 status
```

## Reference Files
- `CORRECT_ENV_FILE_FIXED.txt` - Complete correct .env content
- `FRESH_EC2_DEPLOYMENT_GUIDE.md` - Full deployment guide
- `backend/.env.example` - Example with all available options
