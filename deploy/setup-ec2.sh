#!/usr/bin/env bash
# =============================================================================
# EC2 Single-Server Deployment Script for Job Platform (trusanity.com)
# Ubuntu 22.04 LTS | Postgres + Redis + FastAPI + Celery + Next.js + Nginx
# =============================================================================
# Usage:
#   1. Launch Ubuntu 22.04 EC2 (t2.medium+, 30GB+ storage)
#   2. Open ports 22, 80, 443 in Security Group
#   3. SSH in:  ssh -i your-key.pem ubuntu@<ELASTIC_IP>
#   4. Clone repo: git clone https://github.com/Sourabh1118/TenOpps.git /tmp/TenOpps
#   5. Run:  sudo bash /tmp/TenOpps/deploy/setup-ec2.sh
# =============================================================================

set -euo pipefail

# ---- Configuration (edit these before running) ----
DOMAIN="trusanity.com"
APP_USER="jobplatform"
APP_DIR="/home/${APP_USER}/job-platform"
REPO_URL="https://github.com/Sourabh1118/TenOpps.git"
DB_NAME="jobplatform_db"
DB_USER="jobplatform"
ADMIN_EMAIL="admin@trusanity.com"
ADMIN_PASSWORD="Admin@123"
NODE_MAJOR=20

# Generate secrets if not set
DB_PASSWORD="${DB_PASSWORD:-$(openssl rand -hex 16)}"
SECRET_KEY="${SECRET_KEY:-$(openssl rand -hex 32)}"
JWT_SECRET_KEY="${JWT_SECRET_KEY:-$(openssl rand -hex 32)}"

# ---- Colors ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[x]${NC} $1"; }
section() { echo -e "\n${CYAN}=== $1 ===${NC}\n"; }

# ---- Pre-flight checks ----
if [[ $EUID -ne 0 ]]; then
    err "This script must be run as root (use sudo)"
    exit 1
fi

section "Step 1/10: System Update"
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -qq
log "System updated"

section "Step 2/10: Install System Dependencies"

# Node.js 20.x
if ! command -v node &>/dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_${NODE_MAJOR}.x | bash -
    apt-get install -y -qq nodejs
fi
log "Node.js $(node --version)"

# Python 3.11
apt-get install -y -qq python3 python3-venv python3-pip python3-dev build-essential
log "Python $(python3 --version)"

# PostgreSQL
apt-get install -y -qq postgresql postgresql-contrib libpq-dev
log "PostgreSQL installed"

# Redis
apt-get install -y -qq redis-server
log "Redis installed"

# Nginx
apt-get install -y -qq nginx
log "Nginx installed"

# Certbot
apt-get install -y -qq certbot python3-certbot-nginx
log "Certbot installed"

# PM2
if ! command -v pm2 &>/dev/null; then
    npm install -g pm2
fi
log "PM2 $(pm2 --version)"

# UFW
apt-get install -y -qq ufw
log "All dependencies installed"

section "Step 3/10: Create Application User"
if ! id "$APP_USER" &>/dev/null; then
    useradd -m -s /bin/bash "$APP_USER"
    log "User '${APP_USER}' created"
else
    log "User '${APP_USER}' already exists"
fi

section "Step 4/10: Configure PostgreSQL"
systemctl enable postgresql
systemctl start postgresql

# Create database and user
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" | grep -q 1 || {
    sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';"
    log "Database user '${DB_USER}' created"
}
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1 || {
    sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"
    log "Database '${DB_NAME}' created"
}
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};"

# Enable uuid-ossp extension (needed for UUID primary keys)
sudo -u postgres psql -d "${DB_NAME}" -c 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'
log "PostgreSQL configured"

section "Step 5/10: Configure Redis"
systemctl enable redis-server
systemctl start redis

# Verify Redis is running
redis-cli ping | grep -q PONG && log "Redis is running" || { err "Redis failed to start"; exit 1; }

section "Step 6/10: Clone and Setup Application"
if [[ -d "$APP_DIR" ]]; then
    warn "App directory exists. Pulling latest code..."
    sudo -u "$APP_USER" git -C "$APP_DIR" pull origin main || true
else
    sudo -u "$APP_USER" git clone "$REPO_URL" "$APP_DIR"
    log "Repository cloned"
fi

# Create upload and log directories
sudo -u "$APP_USER" mkdir -p "${APP_DIR}/backend/uploads" "${APP_DIR}/backend/logs"

section "Step 7/10: Setup Backend"

# Create Python virtual environment
sudo -u "$APP_USER" bash -c "
    cd ${APP_DIR}/backend
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
"
log "Python dependencies installed"

# Write backend .env file
cat > "${APP_DIR}/backend/.env" <<ENVEOF
# Application
APP_NAME=Job Aggregation Platform
APP_ENV=production
DEBUG=False
SECRET_KEY=${SECRET_KEY}

# API
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=False

# Database
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_DB=1

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=${JWT_SECRET_KEY}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# External APIs (fill in when available)
INDEED_API_KEY=
LINKEDIN_RSS_URLS=

# Stripe (fill in with live keys for payments)
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=

# Scraping
SCRAPING_USER_AGENT=Mozilla/5.0 (compatible; JobBot/1.0)
SCRAPING_RATE_LIMIT_LINKEDIN=10
SCRAPING_RATE_LIMIT_INDEED=20
SCRAPING_RATE_LIMIT_NAUKRI=5
SCRAPING_RATE_LIMIT_MONSTER=5

# Storage
STORAGE_BACKEND=local
STORAGE_LOCAL_PATH=./uploads
SUPABASE_URL=
SUPABASE_KEY=

# Monitoring (optional)
SENTRY_DSN=

# Alerting (optional)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
ADMIN_EMAIL=
FROM_EMAIL=
SLACK_WEBHOOK_URL=

# CORS
CORS_ORIGINS=https://trusanity.com,https://www.trusanity.com

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
ENVEOF

chown "${APP_USER}:${APP_USER}" "${APP_DIR}/backend/.env"
chmod 600 "${APP_DIR}/backend/.env"
log "Backend .env created (secrets auto-generated)"

# Run database migrations
sudo -u "$APP_USER" bash -c "
    cd ${APP_DIR}/backend
    source venv/bin/activate
    alembic upgrade head
"
log "Database migrations applied"

# Create admin account
sudo -u "$APP_USER" bash -c "
    cd ${APP_DIR}/backend
    source venv/bin/activate
    python scripts/create_admin.py '${ADMIN_EMAIL}' '${ADMIN_PASSWORD}'
" || warn "Admin may already exist (this is OK)"
log "Admin account ready"

section "Step 8/10: Setup Frontend"

# Create frontend .env.production.local
cat > "${APP_DIR}/frontend/.env.production.local" <<FENVEOF
NEXT_PUBLIC_API_URL=https://${DOMAIN}
NEXT_PUBLIC_API_BASE_PATH=/api
NEXT_PUBLIC_ENV=production
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_FEATURED_JOBS=true
FENVEOF
chown "${APP_USER}:${APP_USER}" "${APP_DIR}/frontend/.env.production.local"

# Install dependencies and build
sudo -u "$APP_USER" bash -c "
    cd ${APP_DIR}/frontend
    npm ci --production=false 2>/dev/null || npm install
    npm run build
"
log "Frontend built"

# Start frontend with PM2 (as the app user)
sudo -u "$APP_USER" bash -c "
    cd ${APP_DIR}/frontend
    pm2 delete job-platform-frontend 2>/dev/null || true
    pm2 start npm --name job-platform-frontend -- start
    pm2 save
"

# Setup PM2 to start on boot
env PATH=$PATH:/usr/bin pm2 startup systemd -u "$APP_USER" --hp "/home/${APP_USER}"
sudo -u "$APP_USER" pm2 save
log "Frontend running via PM2"

section "Step 9/10: Install Systemd Services & Nginx"

# Copy systemd service files
cp "${APP_DIR}/deploy/systemd/job-platform-backend.service" /etc/systemd/system/
cp "${APP_DIR}/deploy/systemd/job-platform-celery-worker.service" /etc/systemd/system/
cp "${APP_DIR}/deploy/systemd/job-platform-celery-beat.service" /etc/systemd/system/

systemctl daemon-reload

# Enable and start backend services
for svc in job-platform-backend job-platform-celery-worker job-platform-celery-beat; do
    systemctl enable "$svc"
    systemctl start "$svc"
    log "${svc} started"
done

# Install rate-limit zone definitions (goes in http{} context via conf.d)
cat > /etc/nginx/conf.d/rate-limits.conf <<'RATELIMITEOF'
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=30r/s;
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;
RATELIMITEOF

# Setup Nginx -- start with HTTP-only config first (SSL added by certbot)
cat > /etc/nginx/sites-available/job-platform <<'NGINXEOF'
server {
    listen 80;
    listen [::]:80;
    server_name trusanity.com www.trusanity.com;

    client_max_body_size 10M;

    # Backend API
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;

        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Stricter rate limit for login
    location /api/auth/login {
        limit_req zone=login_limit burst=3 nodelay;

        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    location /_next/static/ {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        expires 365d;
        add_header Cache-Control "public, immutable";
    }

    # Frontend (Next.js)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
NGINXEOF

# Enable site, disable default
ln -sf /etc/nginx/sites-available/job-platform /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

nginx -t && systemctl restart nginx
log "Nginx configured and running"

section "Step 10/10: SSL Certificate & Firewall"

# Configure UFW
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
log "Firewall configured (22, 80, 443 open)"

# Obtain SSL certificate
warn "Requesting SSL certificate for ${DOMAIN}..."
certbot --nginx -d "${DOMAIN}" -d "www.${DOMAIN}" --non-interactive --agree-tos --email "${ADMIN_EMAIL}" --redirect || {
    warn "Certbot failed. DNS may not have propagated yet."
    warn "After DNS is ready, run:  sudo certbot --nginx -d ${DOMAIN} -d www.${DOMAIN}"
}

# Setup auto-renewal cron
(crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'") | sort -u | crontab -
log "SSL auto-renewal configured"

# After certbot succeeds, replace the HTTP config with the full production config
if [[ -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]]; then
    cp "${APP_DIR}/deploy/nginx/job-platform.conf" /etc/nginx/sites-available/job-platform
    nginx -t && systemctl reload nginx
    log "Full HTTPS Nginx config installed"
fi

# =========================================================================
section "DEPLOYMENT COMPLETE"
# =========================================================================

echo ""
echo -e "${GREEN}All services are running:${NC}"
echo ""
echo "  Website:         https://${DOMAIN}"
echo "  API Docs:        https://${DOMAIN}/docs"
echo "  Health Check:    https://${DOMAIN}/health"
echo ""
echo "  Admin Login:     https://${DOMAIN}/login"
echo "  Admin Email:     ${ADMIN_EMAIL}"
echo "  Admin Password:  ${ADMIN_PASSWORD}"
echo ""
echo -e "${YELLOW}IMPORTANT - Save these generated secrets:${NC}"
echo ""
echo "  DB Password:     ${DB_PASSWORD}"
echo "  SECRET_KEY:      ${SECRET_KEY}"
echo "  JWT_SECRET_KEY:  ${JWT_SECRET_KEY}"
echo ""
echo "  Backend .env:    ${APP_DIR}/backend/.env"
echo ""
echo -e "${YELLOW}Change the admin password after first login!${NC}"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status job-platform-backend"
echo "  sudo systemctl status job-platform-celery-worker"
echo "  sudo -u ${APP_USER} pm2 status"
echo "  sudo journalctl -u job-platform-backend -f"
echo "  sudo -u ${APP_USER} pm2 logs job-platform-frontend"
echo ""
