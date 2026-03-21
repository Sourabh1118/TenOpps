#!/bin/bash
# Script to run Celery Beat scheduler for periodic tasks

# Exit on error
set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Beat configuration
LOGLEVEL="${CELERY_BEAT_LOGLEVEL:-info}"
SCHEDULE_FILE="${CELERY_BEAT_SCHEDULE:-celerybeat-schedule}"

echo "Starting Celery Beat scheduler"
echo "Log level: $LOGLEVEL"
echo "Schedule file: $SCHEDULE_FILE"

# Run Celery Beat
# -A: Application module
# -l: Log level
# -s: Schedule database file
# --pidfile: PID file location
celery -A app.tasks.celery_app beat \
    -l "$LOGLEVEL" \
    -s "$SCHEDULE_FILE" \
    --pidfile=/tmp/celerybeat.pid
