.PHONY: up down restart build logs logs-sync sync install setup

help:
	@echo "Comandos disponíveis:"
	@echo "  up          - Inicia os containers em segundo plano"
	@echo "  down        - Para e remove os containers"
	@echo "  restart     - Reinicia os containers"
	@echo "  build       - Constrói as imagens dos containers"
	@echo "  logs        - Exibe os logs do container sharelatex"
	@echo "  logs-sync   - Exibe os logs do container sync"
	@echo "  sync        - Executa o script de sincronização manualmente"
	@echo "  install     - Instala as dependências e configura o ambiente"
	@echo "  setup       - Configura o ambiente (cria .env e instala dependências)"

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

build:
	docker compose build

logs:
	docker compose logs -f sharelatex

logs-sync:
	docker compose logs -f sync

sync:
	docker compose run --rm sync python3 /repo/scripts/sync.py

install:
	bash scripts/install.sh

setup:
	@if [ ! -f .env ]; then cp .env.example .env && echo ".env criado — preencha com suas credenciais antes de continuar."; \
	else echo ".env já existe, pulando."; fi
	@sed -i "s/^DOCKER_UID=.*/DOCKER_UID=$$(id -u)/" .env
	@sed -i "s/^DOCKER_GID=.*/DOCKER_GID=$$(id -g)/" .env
	@echo "DOCKER_UID/GID configurados para $$(id -u):$$(id -g)"
	bash scripts/install.sh
