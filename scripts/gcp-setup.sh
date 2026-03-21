#!/bin/bash
# GCP Compute Engine Automated Setup Script
# This script automates the installation of all required services for the Job Aggregation Platform

set -e  # Exit on any error

echo "=========================================="
echo "Job Platform - GCP Setup Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}➜ $1${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root (use sudo)"
    exit 1
fi

print_info "Starting installation..."
echo ""

# Update system
print_info "Updating system packages..."
apt update && apt upgrade -y
apt install -y build-essential curl git wget vim software-properties-common
print_success "System updated"
echo ""

# Install PostgreSQL
print_info "Installing PostgreSQL 15..."
sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
apt update
apt install -y postgresql-15 postgresql-contrib-15
systemctl start postgresql
systemctl enable postgresql
print_success "PostgreSQL installed"
echo ""

# Install Redis
print_info "Installing Redis..."
apt install -y redis-server
systemctl start redis-server
systemctl enable redis-server
print_success "Redis installed"
echo ""

# Install Python 3.11
print_info "Installing Python 3.11..."
add-apt-repository -y ppa:deadsnakes/ppa
apt update
apt install -y python3.11 python3.11-venv python3.11-dev
print_success "Python 3.11 installed"
echo ""

# Install Node.js 20
print_info "Installing Node.js 20..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs
print_success "Node.js installed"
echo ""

# Install Nginx
print_info "Installing Nginx..."
apt install -y nginx
systemctl enable nginx
print_success "Nginx installed"
echo ""

# Install Certbot
print_info "Installing Certbot..."
apt install -y certbot python3-certbot-nginx
print_success "Certbot installed"
echo ""

# Create application user
print_info "Creating application user..."
if id "jobplatform" &>/dev/null; then
    print_info "User jobplatform already exists"
else
    useradd -m -s /bin/bash jobplatform
    print_success "User jobplatform created"
fi
echo ""

# Create log directory
print_info "Creating log directory..."
mkdir -p /var/log/job-platform
chown jobplatform:jobplatform /var/log/job-platform
print_success "Log directory created"
echo ""

# Create PID directory for Celery
print_info "Creating PID directory..."
mkdir -p /var/run/celery
chown jobplatform:jobplatform /var/run/celery
print_success "PID directory created"
echo ""

# Configure PostgreSQL
print_info "Configuring PostgreSQL..."
read -p "Enter PostgreSQL password for job_platform_user: " DB_PASSWORD
sudo -u postgres psql <<EOF
CREATE DATABASE job_platform;
CREATE USER job_platform_user WITH PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE job_platform TO job_platform_user;
ALTER DATABASE job_platform OWNER TO job_platform_user;
EOF
print_success "PostgreSQL configured"
echo ""

# Configure Redis
print_info "Configuring Redis..."
read -p "Enter Redis password: " REDIS_PASSWORD
sed -i "s/# requirepass foobared/requirepass $REDIS_PASSWORD/" /etc/redis/redis.conf
sed -i "s/bind 127.0.0.1 ::1/bind 127.0.0.1/" /etc/redis/redis.conf
systemctl restart redis-server
print_success "Redis configured"
echo ""

# Clone repository
print_info "Cloning repository..."
read -p "Enter your Git repository URL: " REPO_URL
su - jobplatform -c "cd /home/jobplatform && git clone $REPO_URL job-platform"
print_success "Repository cloned"
echo ""

# Setup backend
print_info "Setting up backend..."
su - jobplatform -c "cd /home/jobplatform/job-platform/backend && python3.11 -m venv venv"
su - jobplatform -c "cd /home/jobplatform/job-platform/backend && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt && pip install gunicorn"
print_success "Backend setup complete"
echo ""

# Setup frontend
print_info "Setting up frontend..."
su - jobplatform -c "cd /home/jobplatform/job-platform/frontend && npm install"
print_success "Frontend setup complete"
echo ""

print_success "Installation complete!"
echo ""
print_info "Next steps:"
echo "1. Configure environment variables in /home/jobplatform/job-platform/backend/.env.production"
echo "2. Run database migrations: cd /home/jobplatform/job-platform/backend && source venv/bin/activate && alembic upgrade head"
echo "3. Build frontend: cd /home/jobplatform/job-platform/frontend && npm run build"
echo "4. Create systemd services (see documentation)"
echo "5. Configure Nginx (see documentation)"
echo "6. Set up SSL with: sudo certbot --nginx -d your-domain.com"
echo ""
print_info "Database password: $DB_PASSWORD"
print_info "Redis password: $REDIS_PASSWORD"
echo ""
print_info "Save these passwords securely!"
