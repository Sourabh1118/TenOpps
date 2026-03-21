#!/bin/bash

################################################################################
# Install Prerequisites for Job Platform Deployment
# Run this BEFORE running complete-clean-deploy.sh
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Installing Prerequisites ===${NC}\n"

# Update system
echo -e "${YELLOW}Step 1: Updating system packages...${NC}"
sudo apt update
sudo apt upgrade -y

# Install PostgreSQL 15
echo -e "${YELLOW}Step 2: Installing PostgreSQL 15...${NC}"

# Add PostgreSQL official repository
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update

# Install PostgreSQL 15
sudo apt install -y postgresql-15 postgresql-contrib-15

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

echo -e "${GREEN}✓ PostgreSQL 15 installed${NC}"

# Install Redis 7
echo -e "${YELLOW}Step 3: Installing Redis 7...${NC}"
sudo apt install -y redis-server

# Configure Redis to require password
sudo sed -i 's/^# requirepass .*/requirepass Herculis@123/' /etc/redis/redis.conf

# Start and enable Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

echo -e "${GREEN}✓ Redis 7 installed${NC}"

# Install Python 3.11
echo -e "${YELLOW}Step 4: Installing Python 3.11...${NC}"
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

echo -e "${GREEN}✓ Python 3.11 installed${NC}"

# Install Node.js 20
echo -e "${YELLOW}Step 5: Installing Node.js 20...${NC}"
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

echo -e "${GREEN}✓ Node.js 20 installed${NC}"

# Install Nginx
echo -e "${YELLOW}Step 6: Installing Nginx...${NC}"
sudo apt install -y nginx

echo -e "${GREEN}✓ Nginx installed${NC}"

# Install PM2
echo -e "${YELLOW}Step 7: Installing PM2...${NC}"
sudo npm install -g pm2

echo -e "${GREEN}✓ PM2 installed${NC}"

# Install Certbot (for SSL)
echo -e "${YELLOW}Step 8: Installing Certbot...${NC}"
sudo apt install -y certbot python3-certbot-nginx

echo -e "${GREEN}✓ Certbot installed${NC}"

# Install build essentials
echo -e "${YELLOW}Step 9: Installing build tools...${NC}"
sudo apt install -y build-essential libpq-dev

echo -e "${GREEN}✓ Build tools installed${NC}"

# Verify installations
echo -e "\n${GREEN}=== Verifying Installations ===${NC}\n"

echo "PostgreSQL version:"
psql --version

echo -e "\nRedis version:"
redis-server --version

echo -e "\nPython version:"
python3.11 --version

echo -e "\nNode.js version:"
node --version

echo -e "\nNPM version:"
npm --version

echo -e "\nNginx version:"
nginx -v

echo -e "\nPM2 version:"
pm2 --version

echo -e "\nCertbot version:"
certbot --version

# Test PostgreSQL
echo -e "\n${YELLOW}Testing PostgreSQL...${NC}"
sudo systemctl status postgresql --no-pager | head -5

# Test Redis
echo -e "\n${YELLOW}Testing Redis...${NC}"
redis-cli -a Herculis@123 ping 2>/dev/null && echo -e "${GREEN}✓ Redis is working${NC}" || echo -e "${RED}✗ Redis test failed${NC}"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Prerequisites Installation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "All prerequisites are now installed."
echo ""
echo "Next step: Run the deployment script"
echo "  sudo ~/complete-clean-deploy.sh trusanity.com <REDACTED_TOKEN> Herculis@123 Herculis@123"
echo ""
