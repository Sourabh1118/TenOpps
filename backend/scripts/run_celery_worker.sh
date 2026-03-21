#!/bin/bash
# Script to run Celery worker with configured concurrency

# Exit on error
set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Worker configuration
WORKER_NAME="${CELERY_WORKER_NAME:-worker1}"
CONCURRENCY="${CELERY_WORKER_CONCURRENCY:-4}"
POOL="${CELERY_WORKER_POOL:-prefork}"
LOGLEVEL="${CELERY_WORKER_LOGLEVEL:-info}"

echo "Starting Celery worker: $WORKER_NAME"
echo "Concurrency: $CONCURRENCY processes"
echo "Pool: $POOL"
echo "Log level: $LOGLEVEL"

# Run Celery worker
# -A: Application module
# -n: Worker name
# -c: Concurrency (number of worker processes)
# -P: Pool implementation (prefork, solo, threads, gevent)
# -l: Log level
# -Q: Queues to consume from
# --max-tasks-per-child: Restart worker after N tasks to prevent memory leaks
celery -A app.tasks.celery_app worker \
    -n "$WORKER_NAME@%h" \
    -c "$CONCURRENCY" \
    -P "$POOL" \
    -l "$LOGLEVEL" \
    -Q high_priority,default,low_priority \
    --max-tasks-per-child=1000 \
    --time-limit=300 \
    --soft-time-limit=270
