#!/usr/bin/env bash
# =============================================================================
# Update script for Job Platform on EC2
# Run as root: sudo bash /home/jobplatform/job-platform/deploy/update.sh
# =============================================================================
set -euo pipefail

APP_USER="jobplatform"
APP_DIR="/home/${APP_USER}/job-platform"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }

echo ""
echo "=== Updating Job Platform ==="
echo ""

# Pull latest code
log "Pulling latest code..."
sudo -u "$APP_USER" git -C "$APP_DIR" pull origin main

# Update backend
log "Updating backend dependencies..."
sudo -u "$APP_USER" bash -c "
    cd ${APP_DIR}/backend
    source venv/bin/activate
    pip install -r requirements.txt -q
    alembic upgrade head
"

# Restart backend services
log "Restarting backend services..."
systemctl restart job-platform-backend
systemctl restart job-platform-celery-worker
systemctl restart job-platform-celery-beat

# Update frontend
log "Rebuilding frontend..."
sudo -u "$APP_USER" bash -c "
    cd ${APP_DIR}/frontend
    npm ci --production=false 2>/dev/null || npm install
    npm run build
"

# Restart frontend
sudo -u "$APP_USER" pm2 restart job-platform-frontend

# Verify services
echo ""
log "Service status:"
systemctl is-active job-platform-backend && echo "  Backend:        running" || echo "  Backend:        FAILED"
systemctl is-active job-platform-celery-worker && echo "  Celery Worker:  running" || echo "  Celery Worker:  FAILED"
systemctl is-active job-platform-celery-beat && echo "  Celery Beat:    running" || echo "  Celery Beat:    FAILED"
sudo -u "$APP_USER" pm2 pid job-platform-frontend >/dev/null 2>&1 && echo "  Frontend:       running" || echo "  Frontend:       FAILED"
echo ""
log "Update complete"
