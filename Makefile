.PHONY: up down restart build logs logs-sync sync upload upload-template install setup

help:
	@echo "Comandos disponíveis:"
	@echo "  up               - Inicia os containers em segundo plano"
	@echo "  down             - Para e remove os containers"
	@echo "  restart          - Reinicia os containers"
	@echo "  build            - Constrói as imagens dos containers"
	@echo "  logs             - Exibe os logs do container sharelatex"
	@echo "  logs-sync        - Exibe os logs do container sync"
	@echo "  sync             - Baixa todos os projetos do Overleaf para local"
	@echo "  upload PATH_ARG=... - Sobe um diretório ou zip como novo projeto no Overleaf"
	@echo "  upload-template  - Sobe o Template padrão para o Overleaf"
	@echo "  install          - Instala as dependências e configura o ambiente"
	@echo "  setup            - Configura o ambiente (cria .env e instala dependências)"

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

upload:
	@test -n "$(PATH_ARG)" || (echo "Uso: make upload PATH_ARG=caminho/do/projeto" && exit 1)
	docker compose run --rm sync python3 /repo/scripts/upload.py "$(PATH_ARG)"

upload-template:
	docker compose run --rm sync python3 /repo/scripts/upload.py /repo/Template --name "Template TCC CesarSchool"

install:
	bash scripts/install.sh

setup:
	bash scripts/setup-env.sh
	bash scripts/install.sh
