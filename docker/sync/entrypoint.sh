#!/bin/sh
set -e

if [ $# -gt 0 ]; then
  exec "$@"
fi

# Default: run crond
echo "*/30 * * * * python3 /repo/scripts/sync.py >> /var/log/sync.log 2>&1" | crontab -
echo "[overleaf-sync] Service started. Cron running every 30 minutes."
exec crond -f -d 8
