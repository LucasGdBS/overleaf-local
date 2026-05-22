#!/usr/bin/env bash
# Install git pre-push hook. The cron sync runs inside the Docker sync service.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOK="$REPO_ROOT/.git/hooks/pre-push"

echo "Installing git pre-push hook..."
cat > "$HOOK" <<EOF
#!/usr/bin/env bash
echo "[overleaf-sync] Syncing projects before push..."
docker compose -f "$REPO_ROOT/docker-compose.yml" run --rm sync python3 /repo/scripts/sync.py \
  || echo "[overleaf-sync] Sync failed, continuing push anyway."
EOF
chmod +x "$HOOK"
echo "  -> .git/hooks/pre-push installed."

echo ""
echo "Setup complete:"
echo "  - Auto sync:   docker compose up -d  (sync service runs every 30 min)"
echo "  - Manual sync: docker compose run --rm sync python3 /repo/scripts/sync.py"
echo "  - Pre-push:    runs automatically on git push"
