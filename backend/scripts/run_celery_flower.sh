#!/bin/bash
# Script to run Celery Flower for monitoring and management

# Exit on error
set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Flower configuration
PORT="${CELERY_FLOWER_PORT:-5555}"
LOGLEVEL="${CELERY_FLOWER_LOGLEVEL:-info}"

echo "Starting Celery Flower monitoring"
echo "Port: $PORT"
echo "Log level: $LOGLEVEL"
echo "Access at: http://localhost:$PORT"

# Run Celery Flower
# -A: Application module
# --port: Port to listen on
# --loglevel: Log level
celery -A app.tasks.celery_app flower \
    --port="$PORT" \
    --loglevel="$LOGLEVEL"
