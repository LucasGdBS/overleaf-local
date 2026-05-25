#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOK="$REPO_ROOT/.git/hooks/pre-push"

echo "Instalando git pre-push hook..."
cat > "$HOOK" <<EOF
#!/usr/bin/env bash
echo "[overleaf-sync] Sincronizando projetos antes do push..."
docker compose -f "$REPO_ROOT/docker-compose.yml" run --rm sync python3 /repo/scripts/sync.py \
  || echo "[overleaf-sync] Sync falhou, continuando push mesmo assim."
EOF
chmod +x "$HOOK"
echo "  -> .git/hooks/pre-push instalado."
