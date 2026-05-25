#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"
ENV_EXAMPLE="$REPO_ROOT/.env.example"

# Portable sed -i (macOS requires empty string argument)
sed_inplace() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "$@"
    else
        sed -i "$@"
    fi
}

if [ ! -f "$ENV_FILE" ]; then
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    echo ".env criado — preencha com suas credenciais antes de continuar."
else
    echo ".env já existe, pulando cópia."
fi

# Set UID/GID
sed_inplace "s/^DOCKER_UID=.*/DOCKER_UID=$(id -u)/" "$ENV_FILE"
sed_inplace "s/^DOCKER_GID=.*/DOCKER_GID=$(id -g)/" "$ENV_FILE"
echo "DOCKER_UID/GID configurados para $(id -u):$(id -g)"

# Detect architecture
ARCH="$(uname -m)"
case "$ARCH" in
    x86_64)  PLATFORM="linux/amd64" ;;
    arm64|aarch64) PLATFORM="linux/arm64" ;;
    *)
        echo "Arquitetura desconhecida: $ARCH — usando linux/amd64 como padrão."
        PLATFORM="linux/amd64"
        ;;
esac

sed_inplace "s|^DOCKER_PLATFORM=.*|DOCKER_PLATFORM=$PLATFORM|" "$ENV_FILE"
echo "DOCKER_PLATFORM configurado para $PLATFORM ($ARCH)"
