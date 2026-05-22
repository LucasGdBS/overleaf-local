#!/bin/bash
set -e

cd /overleaf/services/web
node modules/server-ce-scripts/scripts/create-user.js --email=admin@overleaf.local \
  && echo "Admin criado. Veja a URL para definir a senha em: docker compose logs sharelatex" \
  || echo "Admin já existe, pulando criação."
