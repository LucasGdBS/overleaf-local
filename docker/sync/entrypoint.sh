#!/bin/sh
set -e

if [ $# -gt 0 ]; then
  exec "$@"
fi

echo "[overleaf-sync] Service started. Syncing every 30 minutes."
while true; do
  python3 /repo/scripts/sync.py 2>&1 | tee -a /repo/sync.log
  sleep 1800
done
