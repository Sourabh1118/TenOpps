#!/bin/bash
################################################################################
# AWS EC2 Complete Automated Deployment Script
# Job Aggregation Platform - Full Stack Deployment
# 
# This script performs complete automated deployment with:
# - Error handling and rollback
# - Progress tracking
# - Detailed logging
# - Service verification
# - Automatic recovery
################################################################################

set -o pipefail  # Catch errors in pipes

# Configuration
SCRIPT_VERSION="1.0.0"
LOG_FILE="/var/log/job-platform-deploy.log"
DEPLOY_USER="jobplatform"
APP_DIR="/home/$DEPLOY_USER/job-platform"
BACKUP_DIR="/home/$DEPLOY_USER/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Error tracking
ERRORS=()
WARNINGS=()

################################################################################
# Utility Functions
################################################################################

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    log "SECTION: $1"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    log "SUCCESS: $1"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    log "ERROR: $1"
    ERRORS+=("$1")
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
    log "WARNING: $1"
    WARNINGS+=("$1")
}

print_info() {
    echo -e "${YELLOW}➜ $1${NC}"
    log "INFO: $1"
}


check_error() {
    if [ $? -ne 0 ]; then
        print_error "$1"
        return 1
    fi
    return 0
}

prompt_user() {
    local prompt="$1"
    local var_name="$2"
    local default="$3"
    
    if [ -n "$default" ]; then
        read -p "$prompt [$default]: " value
        value=${value:-$default}
    else
        read -p "$prompt: " value
    fi
    
    eval "$var_name='$value'"
}

prompt_password() {
    local prompt="$1"
    local var_name="$2"
    
    read -sp "$prompt: " value
    echo ""
    eval "$var_name='$value'"
}

verify_root() {
    if [ "$EUID" -ne 0 ]; then 
        print_error "Please run as root (use sudo)"
        exit 1
    fi
}

create_backup() {
    local backup_name="$1"
    mkdir -p "$BACKUP_DIR"
    if [ -d "$APP_DIR" ]; then
        tar -czf "$BACKUP_DIR/backup_${backup_name}_${TIMESTAMP}.tar.gz" -C "$(dirname $APP_DIR)" "$(basename $APP_DIR)" 2>/dev/null
        print_success "Backup created: backup_${backup_name}_${TIMESTAMP}.tar.gz"
    fi
}

rollback() {
    print_error "Deployment failed. Initiating rollback..."
    
    # Stop services
    systemctl stop job-platform-backend 2>/dev/null
    systemctl stop job-platform-frontend 2>/dev/null
    systemctl stop job-platform-celery 2>/dev/null
    systemctl stop job-platform-celery-beat 2>/dev/null
    
    # Restore from backup if exists
    latest_backup=$(ls -t "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null | head -1)
    if [ -n "$latest_backup" ]; then
        print_info "Restoring from backup: $latest_backup"
        rm -rf "$APP_DIR"
        tar -xzf "$latest_backup" -C "$(dirname $APP_DIR)"
        print_success "Rollback completed"
    fi
    
    exit 1
}

################################################################################
# Pre-flight Checks
################################################################################

preflight_checks() {
    print_header "Pre-flight Checks"
    
    # Check OS
    if [ ! -f /etc/lsb-release ]; then
        print_error "This script requires Ubuntu"
        exit 1
    fi
    
    source /etc/lsb-release
    if [[ ! "$DISTRIB_ID" == "Ubuntu" ]]; then
        print_error "This script requires Ubuntu"
        exit 1
    fi
    print_success "OS: Ubuntu $DISTRIB_RELEASE"
    
    # Check internet connectivity
    if ! ping -c 1 google.com &> /dev/null; then
        print_error "No internet connectivity"
        exit 1
    fi
    print_success "Internet connectivity verified"
    
    # Check available disk space (need at least 10GB)
    available_space=$(df / | tail -1 | awk '{print $4}')
    if [ "$available_space" -lt 10485760 ]; then
        print_warning "Less than 10GB disk space available"
    else
        print_success "Sufficient disk space available"
    fi
    
    # Check memory (need at least 2GB)
    total_mem=$(free -m | awk '/^Mem:/{print $2}')
    if [ "$total_mem" -lt 2000 ]; then
        print_warning "Less than 2GB RAM available"
    else
        print_success "Sufficient memory available"
    fi
}

################################################################################
# Collect Configuration
################################################################################

collect_configuration() {
    print_header "Configuration Collection"
    
    echo "Please provide the following information:"
    echo ""
    
    # Git repository
    echo "Git Repository URL Formats:"
    echo "  - With PAT: https://YOUR_PAT@github.com/username/repo.git"
    echo "  - Public: https://github.com/username/repo.git"
    echo "  - SSH: git@github.com:username/repo.git"
    echo ""
    prompt_user "Git repository URL" GIT_REPO_URL
    prompt_user "Git branch" GIT_BRANCH "main"
    
    # Database
    prompt_password "PostgreSQL password for job_platform_user" DB_PASSWORD
    
    # Redis
    prompt_password "Redis password" REDIS_PASSWORD
    
    # Application secrets
    print_info "Generating SECRET_KEY..."
    SECRET_KEY=$(openssl rand -hex 32)
    
    # Domain
    prompt_user "Domain name (leave empty if none)" DOMAIN_NAME ""
    
    # Stripe (optional)
    prompt_user "Stripe Secret Key (optional)" STRIPE_SECRET_KEY ""
    prompt_user "Stripe Publishable Key (optional)" STRIPE_PUBLISHABLE_KEY ""
    
    # Sentry (optional)
    prompt_user "Sentry DSN (optional)" SENTRY_DSN ""
    
    # Email
    prompt_user "SMTP Host (e.g., smtp.gmail.com)" SMTP_HOST "smtp.gmail.com"
    prompt_user "SMTP Port" SMTP_PORT "587"
    prompt_user "SMTP User" SMTP_USER ""
    prompt_password "SMTP Password" SMTP_PASSWORD
    
    print_success "Configuration collected"
    
    # Save configuration
    cat > /tmp/deploy_config.env <<EOF
GIT_REPO_URL=$GIT_REPO_URL
GIT_BRANCH=$GIT_BRANCH
DB_PASSWORD=$DB_PASSWORD
REDIS_PASSWORD=$REDIS_PASSWORD
SECRET_KEY=$SECRET_KEY
DOMAIN_NAME=$DOMAIN_NAME
STRIPE_SECRET_KEY=$STRIPE_SECRET_KEY
STRIPE_PUBLISHABLE_KEY=$STRIPE_PUBLISHABLE_KEY
SENTRY_DSN=$SENTRY_DSN
SMTP_HOST=$SMTP_HOST
SMTP_PORT=$SMTP_PORT
SMTP_USER=$SMTP_USER
SMTP_PASSWORD=$SMTP_PASSWORD
EOF
    chmod 600 /tmp/deploy_config.env
}

################################################################################
# System Update
################################################################################

update_system() {
    print_header "System Update"
    
    print_info "Updating package lists..."
    apt update >> "$LOG_FILE" 2>&1
    check_error "Failed to update package lists" || rollback
    
    print_info "Upgrading packages..."
    DEBIAN_FRONTEND=noninteractive apt upgrade -y >> "$LOG_FILE" 2>&1
    check_error "Failed to upgrade packages" || rollback
    
    print_info "Installing essential packages..."
    apt install -y build-essential curl git wget vim software-properties-common \
        unzip htop net-tools >> "$LOG_FILE" 2>&1
    check_error "Failed to install essential packages" || rollback
    
    print_success "System updated"
}

################################################################################
# Install PostgreSQL
################################################################################

install_postgresql() {
    print_header "Installing PostgreSQL"
    
    print_info "Adding PostgreSQL repository..."
    sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - >> "$LOG_FILE" 2>&1
    
    apt update >> "$LOG_FILE" 2>&1
    
    print_info "Installing PostgreSQL 15..."
    apt install -y postgresql-15 postgresql-contrib-15 >> "$LOG_FILE" 2>&1
    check_error "Failed to install PostgreSQL" || rollback
    
    print_info "Starting PostgreSQL..."
    systemctl start postgresql
    systemctl enable postgresql >> "$LOG_FILE" 2>&1
    
    # Wait for PostgreSQL to be ready
    sleep 5
    
    print_info "Creating database and user..."
    sudo -u postgres psql <<EOF >> "$LOG_FILE" 2>&1
CREATE DATABASE job_platform;
CREATE USER job_platform_user WITH PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE job_platform TO job_platform_user;
ALTER DATABASE job_platform OWNER TO job_platform_user;
\q
EOF
    check_error "Failed to create database" || rollback
    
    print_info "Optimizing PostgreSQL configuration..."
    cat >> /etc/postgresql/15/main/postgresql.conf <<EOF

# Performance tuning
shared_buffers = 4GB
effective_cache_size = 12GB
maintenance_work_mem = 1GB
work_mem = 64MB
max_connections = 200
random_page_cost = 1.1
effective_io_concurrency = 200
EOF
    
    systemctl restart postgresql
    
    print_success "PostgreSQL installed and configured"
}

################################################################################
# Install Redis
################################################################################

install_redis() {
    print_header "Installing Redis"
    
    print_info "Installing Redis..."
    apt install -y redis-server >> "$LOG_FILE" 2>&1
    check_error "Failed to install Redis" || rollback
    
    print_info "Configuring Redis..."
    sed -i "s/^# requirepass .*/requirepass $REDIS_PASSWORD/" /etc/redis/redis.conf
    sed -i "s/^bind .*/bind 127.0.0.1/" /etc/redis/redis.conf
    
    # Add performance settings
    cat >> /etc/redis/redis.conf <<EOF

# Performance settings
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec
EOF
    
    print_info "Starting Redis..."
    systemctl restart redis-server
    systemctl enable redis-server >> "$LOG_FILE" 2>&1
    
    # Test Redis
    sleep 2
    redis-cli -a "$REDIS_PASSWORD" --no-auth-warning ping >> "$LOG_FILE" 2>&1
    check_error "Redis connection test failed" || rollback
    
    print_success "Redis installed and configured"
}

################################################################################
# Install Python
################################################################################

install_python() {
    print_header "Installing Python 3.11"
    
    print_info "Adding Python repository..."
    add-apt-repository -y ppa:deadsnakes/ppa >> "$LOG_FILE" 2>&1
    apt update >> "$LOG_FILE" 2>&1
    
    print_info "Installing Python 3.11..."
    apt install -y python3.11 python3.11-venv python3.11-dev python3-pip >> "$LOG_FILE" 2>&1
    check_error "Failed to install Python" || rollback
    
    python3.11 --version
    print_success "Python 3.11 installed"
}

################################################################################
# Install Node.js
################################################################################

install_nodejs() {
    print_header "Installing Node.js"
    
    print_info "Adding Node.js repository..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - >> "$LOG_FILE" 2>&1
    
    print_info "Installing Node.js 20..."
    apt install -y nodejs >> "$LOG_FILE" 2>&1
    check_error "Failed to install Node.js" || rollback
    
    node --version
    npm --version
    print_success "Node.js installed"
}

################################################################################
# Install Nginx
################################################################################

install_nginx() {
    print_header "Installing Nginx"
    
    apt install -y nginx >> "$LOG_FILE" 2>&1
    check_error "Failed to install Nginx" || rollback
    
    systemctl enable nginx >> "$LOG_FILE" 2>&1
    
    print_success "Nginx installed"
}

################################################################################
# Install Certbot
################################################################################

install_certbot() {
    print_header "Installing Certbot"
    
    apt install -y certbot python3-certbot-nginx >> "$LOG_FILE" 2>&1
    check_error "Failed to install Certbot" || rollback
    
    print_success "Certbot installed"
}


################################################################################
# Setup Application User
################################################################################

setup_app_user() {
    print_header "Setting Up Application User"
    
    if id "$DEPLOY_USER" &>/dev/null; then
        print_info "User $DEPLOY_USER already exists"
    else
        useradd -m -s /bin/bash "$DEPLOY_USER"
        print_success "User $DEPLOY_USER created"
    fi
    
    # Make home directory accessible for troubleshooting
    chmod 755 /home/$DEPLOY_USER
    
    # Add ubuntu user to jobplatform group for easier access
    if id "ubuntu" &>/dev/null; then
        usermod -a -G $DEPLOY_USER ubuntu
        print_info "Added ubuntu user to $DEPLOY_USER group"
    fi
    
    # Create directories
    mkdir -p /var/log/job-platform
    mkdir -p /var/run/celery
    mkdir -p "$BACKUP_DIR"
    
    chown $DEPLOY_USER:$DEPLOY_USER /var/log/job-platform
    chown $DEPLOY_USER:$DEPLOY_USER /var/run/celery
    chown $DEPLOY_USER:$DEPLOY_USER "$BACKUP_DIR"
    
    # Make log directory readable by group
    chmod 755 /var/log/job-platform
    
    print_success "Directories created and permissions set"
}

################################################################################
# Clone Repository
################################################################################

clone_repository() {
    print_header "Cloning Repository"
    
    if [ -d "$APP_DIR" ]; then
        print_info "Application directory exists, creating backup..."
        create_backup "pre_clone"
        rm -rf "$APP_DIR"
    fi
    
    print_info "Cloning from $GIT_REPO_URL..."
    sudo -u $DEPLOY_USER git clone -b "$GIT_BRANCH" "$GIT_REPO_URL" "$APP_DIR" >> "$LOG_FILE" 2>&1
    check_error "Failed to clone repository" || rollback
    
    # Set proper permissions for group access
    chmod -R g+rX "$APP_DIR"
    
    print_success "Repository cloned"
}

################################################################################
# Setup Backend
################################################################################

setup_backend() {
    print_header "Setting Up Backend"
    
    # Check if backend directory exists
    if [ ! -d "$APP_DIR/backend" ]; then
        print_error "Backend directory not found at $APP_DIR/backend"
        print_info "Repository structure:"
        ls -la "$APP_DIR"
        rollback
    fi
    
    cd "$APP_DIR/backend" || rollback
    
    # Check if requirements.txt exists
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found in backend directory"
        print_info "Backend directory contents:"
        ls -la
        rollback
    fi
    
    print_info "Creating Python virtual environment..."
    sudo -u $DEPLOY_USER python3.11 -m venv venv >> "$LOG_FILE" 2>&1
    check_error "Failed to create virtual environment" || rollback
    
    print_info "Installing Python dependencies..."
    sudo -u $DEPLOY_USER bash -c "source venv/bin/activate && pip install --upgrade pip >> $LOG_FILE 2>&1"
    check_error "Failed to upgrade pip" || rollback
    
    sudo -u $DEPLOY_USER bash -c "source venv/bin/activate && pip install -r requirements.txt >> $LOG_FILE 2>&1"
    check_error "Failed to install Python dependencies" || rollback
    
    sudo -u $DEPLOY_USER bash -c "source venv/bin/activate && pip install gunicorn >> $LOG_FILE 2>&1"
    check_error "Failed to install gunicorn" || rollback
    
    print_info "Creating production environment file..."
    cat > "$APP_DIR/backend/.env.production" <<EOF
# Application
APP_NAME=Job Aggregation Platform
APP_ENV=production
DEBUG=False
SECRET_KEY=$SECRET_KEY

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=False

# Database
DATABASE_URL=postgresql://job_platform_user:$DB_PASSWORD@localhost:5432/job_platform
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://:$REDIS_PASSWORD@localhost:6379/0
REDIS_CACHE_DB=1

# Celery
CELERY_BROKER_URL=redis://:$REDIS_PASSWORD@localhost:6379/0
CELERY_RESULT_BACKEND=redis://:$REDIS_PASSWORD@localhost:6379/1

# JWT Authentication
JWT_SECRET_KEY=$SECRET_KEY
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# External API Keys
INDEED_API_KEY=
LINKEDIN_RSS_URLS=

# Stripe Payment
STRIPE_SECRET_KEY=$STRIPE_SECRET_KEY
STRIPE_PUBLISHABLE_KEY=$STRIPE_PUBLISHABLE_KEY
STRIPE_WEBHOOK_SECRET=

# Scraping Configuration
SCRAPING_USER_AGENT=Mozilla/5.0 (compatible; JobBot/1.0)
SCRAPING_RATE_LIMIT_LINKEDIN=10
SCRAPING_RATE_LIMIT_INDEED=20
SCRAPING_RATE_LIMIT_NAUKRI=5
SCRAPING_RATE_LIMIT_MONSTER=5

# File Storage
STORAGE_BACKEND=local
STORAGE_LOCAL_PATH=./uploads
SUPABASE_URL=
SUPABASE_KEY=

# Monitoring
SENTRY_DSN=$SENTRY_DSN

# Alerting
SMTP_HOST=$SMTP_HOST
SMTP_PORT=$SMTP_PORT
SMTP_USER=$SMTP_USER
SMTP_PASSWORD=$SMTP_PASSWORD
ADMIN_EMAIL=$SMTP_USER
FROM_EMAIL=noreply@${DOMAIN_NAME:-localhost}
SLACK_WEBHOOK_URL=

# CORS
CORS_ORIGINS=https://${DOMAIN_NAME:-localhost},http://${DOMAIN_NAME:-localhost}

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
EOF
    
    chown $DEPLOY_USER:$DEPLOY_USER "$APP_DIR/backend/.env.production"
    chmod 600 "$APP_DIR/backend/.env.production"
    
    # Create symlink for .env to point to .env.production
    ln -sf .env.production "$APP_DIR/backend/.env"
    chown -h $DEPLOY_USER:$DEPLOY_USER "$APP_DIR/backend/.env"
    
    print_info "Running database migrations..."
    sudo -u $DEPLOY_USER bash -c "cd $APP_DIR/backend && source venv/bin/activate && alembic upgrade head >> $LOG_FILE 2>&1"
    check_error "Failed to run migrations" || rollback
    
    print_success "Backend setup completed"
}

################################################################################
# Setup Frontend
################################################################################

setup_frontend() {
    print_header "Setting Up Frontend"
    
    cd "$APP_DIR/frontend" || rollback
    
    print_info "Installing Node.js dependencies..."
    sudo -u $DEPLOY_USER npm install >> "$LOG_FILE" 2>&1
    check_error "Failed to install Node.js dependencies" || rollback
    
    print_info "Creating frontend environment file..."
    cat > "$APP_DIR/frontend/.env.production" <<EOF
NEXT_PUBLIC_API_URL=https://${DOMAIN_NAME:-localhost}/api
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=$STRIPE_PUBLISHABLE_KEY
EOF
    
    chown $DEPLOY_USER:$DEPLOY_USER "$APP_DIR/frontend/.env.production"
    
    print_info "Building frontend..."
    sudo -u $DEPLOY_USER npm run build >> "$LOG_FILE" 2>&1
    check_error "Failed to build frontend" || rollback
    
    print_success "Frontend setup completed"
}

################################################################################
# Create Systemd Services
################################################################################

create_systemd_services() {
    print_header "Creating Systemd Services"
    
    # Backend service
    print_info "Creating backend service..."
    cat > /etc/systemd/system/job-platform-backend.service <<EOF
[Unit]
Description=Job Platform Backend API
After=network.target postgresql.service redis-server.service

[Service]
Type=notify
User=$DEPLOY_USER
Group=$DEPLOY_USER
WorkingDirectory=$APP_DIR/backend
Environment="PATH=$APP_DIR/backend/venv/bin"
EnvironmentFile=$APP_DIR/backend/.env.production
ExecStart=$APP_DIR/backend/venv/bin/gunicorn \\
    -k uvicorn.workers.UvicornWorker \\
    -w 4 \\
    -b 127.0.0.1:8000 \\
    --timeout 120 \\
    --max-requests 1000 \\
    --max-requests-jitter 50 \\
    --access-logfile /var/log/job-platform/backend-access.log \\
    --error-logfile /var/log/job-platform/backend-error.log \\
    app.main:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Frontend service
    print_info "Creating frontend service..."
    cat > /etc/systemd/system/job-platform-frontend.service <<EOF
[Unit]
Description=Job Platform Frontend
After=network.target

[Service]
Type=simple
User=$DEPLOY_USER
Group=$DEPLOY_USER
WorkingDirectory=$APP_DIR/frontend
Environment="PATH=/usr/bin:/usr/local/bin"
Environment="NODE_ENV=production"
Environment="PORT=3000"
ExecStart=/usr/bin/npm start

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Celery worker service
    print_info "Creating Celery worker service..."
    cat > /etc/systemd/system/job-platform-celery.service <<EOF
[Unit]
Description=Job Platform Celery Worker
After=network.target redis-server.service postgresql.service

[Service]
Type=simple
User=$DEPLOY_USER
Group=$DEPLOY_USER
WorkingDirectory=$APP_DIR/backend
Environment="PATH=$APP_DIR/backend/venv/bin"
EnvironmentFile=$APP_DIR/backend/.env.production
ExecStart=$APP_DIR/backend/venv/bin/celery -A app.tasks.celery_app worker \\
    --loglevel=info \\
    --concurrency=4 \\
    --max-tasks-per-child=1000 \\
    --logfile=/var/log/job-platform/celery-worker.log

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Celery beat service
    print_info "Creating Celery beat service..."
    cat > /etc/systemd/system/job-platform-celery-beat.service <<EOF
[Unit]
Description=Job Platform Celery Beat Scheduler
After=network.target redis-server.service

[Service]
Type=simple
User=$DEPLOY_USER
Group=$DEPLOY_USER
WorkingDirectory=$APP_DIR/backend
Environment="PATH=$APP_DIR/backend/venv/bin"
EnvironmentFile=$APP_DIR/backend/.env.production
ExecStart=$APP_DIR/backend/venv/bin/celery -A app.tasks.celery_app beat \\
    --loglevel=info \\
    --logfile=/var/log/job-platform/celery-beat.log

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    print_success "Systemd services created"
}

################################################################################
# Configure Nginx
################################################################################

configure_nginx() {
    print_header "Configuring Nginx"
    
    cat > /etc/nginx/sites-available/job-platform <<'NGINX_EOF'
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

# HTTP server
server {
    listen 80;
    listen [::]:80;
    server_name _;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
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

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
NGINX_EOF
    
    ln -sf /etc/nginx/sites-available/job-platform /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    nginx -t >> "$LOG_FILE" 2>&1
    check_error "Nginx configuration test failed" || rollback
    
    systemctl restart nginx
    
    print_success "Nginx configured"
}

################################################################################
# Configure Firewall
################################################################################

configure_firewall() {
    print_header "Configuring Firewall"
    
    print_info "Setting up UFW..."
    ufw --force reset >> "$LOG_FILE" 2>&1
    ufw default deny incoming >> "$LOG_FILE" 2>&1
    ufw default allow outgoing >> "$LOG_FILE" 2>&1
    ufw allow 22/tcp >> "$LOG_FILE" 2>&1
    ufw allow 80/tcp >> "$LOG_FILE" 2>&1
    ufw allow 443/tcp >> "$LOG_FILE" 2>&1
    ufw --force enable >> "$LOG_FILE" 2>&1
    
    print_success "Firewall configured"
}

################################################################################
# Setup Log Rotation
################################################################################

setup_log_rotation() {
    print_header "Setting Up Log Rotation"
    
    cat > /etc/logrotate.d/job-platform <<EOF
/var/log/job-platform/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 $DEPLOY_USER $DEPLOY_USER
    sharedscripts
    postrotate
        systemctl reload job-platform-backend
        systemctl reload job-platform-celery
    endscript
}
EOF
    
    print_success "Log rotation configured"
}

################################################################################
# Setup Backup Cron
################################################################################

setup_backup_cron() {
    print_header "Setting Up Automated Backups"
    
    cat > /home/$DEPLOY_USER/backup-db.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/home/jobplatform/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup PostgreSQL
sudo -u postgres pg_dump job_platform | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: db_backup_$DATE.sql.gz"
EOF
    
    chmod +x /home/$DEPLOY_USER/backup-db.sh
    chown $DEPLOY_USER:$DEPLOY_USER /home/$DEPLOY_USER/backup-db.sh
    
    # Add to crontab
    (crontab -u $DEPLOY_USER -l 2>/dev/null; echo "0 2 * * * /home/$DEPLOY_USER/backup-db.sh") | crontab -u $DEPLOY_USER -
    
    print_success "Backup cron job configured"
}


################################################################################
# Start Services
################################################################################

start_services() {
    print_header "Starting Services"
    
    print_info "Enabling and starting backend..."
    systemctl enable job-platform-backend >> "$LOG_FILE" 2>&1
    systemctl start job-platform-backend
    sleep 5
    
    if systemctl is-active --quiet job-platform-backend; then
        print_success "Backend service started"
    else
        print_error "Backend service failed to start"
        journalctl -u job-platform-backend -n 50 --no-pager
        rollback
    fi
    
    print_info "Enabling and starting frontend..."
    systemctl enable job-platform-frontend >> "$LOG_FILE" 2>&1
    systemctl start job-platform-frontend
    sleep 5
    
    if systemctl is-active --quiet job-platform-frontend; then
        print_success "Frontend service started"
    else
        print_error "Frontend service failed to start"
        journalctl -u job-platform-frontend -n 50 --no-pager
        rollback
    fi
    
    print_info "Enabling and starting Celery worker..."
    systemctl enable job-platform-celery >> "$LOG_FILE" 2>&1
    systemctl start job-platform-celery
    sleep 3
    
    if systemctl is-active --quiet job-platform-celery; then
        print_success "Celery worker started"
    else
        print_warning "Celery worker failed to start (non-critical)"
    fi
    
    print_info "Enabling and starting Celery beat..."
    systemctl enable job-platform-celery-beat >> "$LOG_FILE" 2>&1
    systemctl start job-platform-celery-beat
    sleep 3
    
    if systemctl is-active --quiet job-platform-celery-beat; then
        print_success "Celery beat started"
    else
        print_warning "Celery beat failed to start (non-critical)"
    fi
}

################################################################################
# Verify Deployment
################################################################################

verify_deployment() {
    print_header "Verifying Deployment"
    
    # Check backend
    print_info "Testing backend API..."
    sleep 5
    if curl -f http://localhost:8000/api/health &>/dev/null; then
        print_success "Backend API responding"
    else
        print_error "Backend API not responding"
        ERRORS+=("Backend API health check failed")
    fi
    
    # Check frontend
    print_info "Testing frontend..."
    if curl -f http://localhost:3000 &>/dev/null; then
        print_success "Frontend responding"
    else
        print_error "Frontend not responding"
        ERRORS+=("Frontend health check failed")
    fi
    
    # Check PostgreSQL
    print_info "Testing PostgreSQL..."
    if sudo -u postgres psql -d job_platform -c "SELECT 1;" &>/dev/null; then
        print_success "PostgreSQL connection OK"
    else
        print_error "PostgreSQL connection failed"
        ERRORS+=("PostgreSQL connection failed")
    fi
    
    # Check Redis
    print_info "Testing Redis..."
    if redis-cli -a "$REDIS_PASSWORD" --no-auth-warning ping &>/dev/null; then
        print_success "Redis connection OK"
    else
        print_error "Redis connection failed"
        ERRORS+=("Redis connection failed")
    fi
    
    # Check Nginx
    print_info "Testing Nginx..."
    if curl -f http://localhost/health &>/dev/null; then
        print_success "Nginx responding"
    else
        print_error "Nginx not responding"
        ERRORS+=("Nginx health check failed")
    fi
}

################################################################################
# Setup SSL (if domain provided)
################################################################################

setup_ssl() {
    if [ -n "$DOMAIN_NAME" ]; then
        print_header "Setting Up SSL Certificate"
        
        print_info "Creating certbot directory..."
        mkdir -p /var/www/certbot
        
        print_info "Obtaining SSL certificate for $DOMAIN_NAME..."
        print_warning "Make sure DNS is pointing to this server!"
        
        read -p "Proceed with SSL setup? (y/n): " proceed
        if [ "$proceed" = "y" ]; then
            certbot --nginx -d "$DOMAIN_NAME" --non-interactive --agree-tos --email "admin@$DOMAIN_NAME" >> "$LOG_FILE" 2>&1
            if [ $? -eq 0 ]; then
                print_success "SSL certificate obtained"
            else
                print_warning "SSL certificate setup failed (you can run certbot manually later)"
            fi
        else
            print_info "Skipping SSL setup"
        fi
    fi
}

################################################################################
# Print Summary
################################################################################

print_summary() {
    print_header "Deployment Summary"
    
    echo ""
    echo "Deployment completed at: $(date)"
    echo ""
    
    if [ ${#ERRORS[@]} -eq 0 ]; then
        print_success "Deployment completed successfully!"
    else
        print_warning "Deployment completed with ${#ERRORS[@]} error(s)"
        echo ""
        echo "Errors:"
        for error in "${ERRORS[@]}"; do
            echo "  - $error"
        done
    fi
    
    if [ ${#WARNINGS[@]} -gt 0 ]; then
        echo ""
        echo "Warnings:"
        for warning in "${WARNINGS[@]}"; do
            echo "  - $warning"
        done
    fi
    
    echo ""
    echo "Service Status:"
    systemctl is-active --quiet job-platform-backend && echo "  ✓ Backend: Running" || echo "  ✗ Backend: Stopped"
    systemctl is-active --quiet job-platform-frontend && echo "  ✓ Frontend: Running" || echo "  ✗ Frontend: Stopped"
    systemctl is-active --quiet job-platform-celery && echo "  ✓ Celery Worker: Running" || echo "  ✗ Celery Worker: Stopped"
    systemctl is-active --quiet job-platform-celery-beat && echo "  ✓ Celery Beat: Running" || echo "  ✗ Celery Beat: Stopped"
    systemctl is-active --quiet postgresql && echo "  ✓ PostgreSQL: Running" || echo "  ✗ PostgreSQL: Stopped"
    systemctl is-active --quiet redis-server && echo "  ✓ Redis: Running" || echo "  ✗ Redis: Stopped"
    systemctl is-active --quiet nginx && echo "  ✓ Nginx: Running" || echo "  ✗ Nginx: Stopped"
    
    echo ""
    echo "Access Information:"
    if [ -n "$DOMAIN_NAME" ]; then
        echo "  Application URL: https://$DOMAIN_NAME"
        echo "  API URL: https://$DOMAIN_NAME/api"
    else
        echo "  Application URL: http://$(curl -s ifconfig.me)"
        echo "  API URL: http://$(curl -s ifconfig.me)/api"
    fi
    
    echo ""
    echo "Important Files:"
    echo "  Backend env: $APP_DIR/backend/.env.production"
    echo "  Frontend env: $APP_DIR/frontend/.env.production"
    echo "  Logs: /var/log/job-platform/"
    echo "  Backups: $BACKUP_DIR"
    echo "  Deploy log: $LOG_FILE"
    
    echo ""
    echo "Useful Commands:"
    echo "  Check backend logs: sudo journalctl -u job-platform-backend -f"
    echo "  Check frontend logs: sudo journalctl -u job-platform-frontend -f"
    echo "  Restart backend: sudo systemctl restart job-platform-backend"
    echo "  Restart frontend: sudo systemctl restart job-platform-frontend"
    echo "  Check all services: sudo systemctl status job-platform-*"
    
    echo ""
    echo "Next Steps:"
    if [ -z "$DOMAIN_NAME" ]; then
        echo "  1. Configure your domain DNS to point to this server"
        echo "  2. Run: sudo certbot --nginx -d your-domain.com"
    fi
    echo "  3. Review logs for any errors"
    echo "  4. Test the application thoroughly"
    echo "  5. Set up monitoring and alerts"
    
    echo ""
    print_success "Deployment script completed!"
}

################################################################################
# Main Execution
################################################################################

main() {
    clear
    echo "=========================================="
    echo "Job Platform - AWS EC2 Deployment"
    echo "Version: $SCRIPT_VERSION"
    echo "=========================================="
    echo ""
    
    # Initialize log file
    touch "$LOG_FILE"
    chmod 644 "$LOG_FILE"
    
    log "Deployment started"
    
    # Verify running as root
    verify_root
    
    # Run deployment steps
    preflight_checks
    collect_configuration
    update_system
    install_postgresql
    install_redis
    install_python
    install_nodejs
    install_nginx
    install_certbot
    setup_app_user
    clone_repository
    setup_backend
    setup_frontend
    create_systemd_services
    configure_nginx
    configure_firewall
    setup_log_rotation
    setup_backup_cron
    start_services
    verify_deployment
    setup_ssl
    
    # Clean up sensitive data
    rm -f /tmp/deploy_config.env
    
    # Print summary
    print_summary
    
    log "Deployment completed"
}

# Trap errors
trap 'print_error "Script interrupted"; rollback' INT TERM

# Run main function
main "$@"
