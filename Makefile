.PHONY: up down restart build logs logs-sync sync upload upload-template setup push-sync zip pdf cron-sync

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
	@echo "  setup            - Configura o ambiente (cria .env com valores do sistema)"
	@echo "  push-sync        - Instala hook de pre-push para sincronizar antes de cada push"
	@echo "  cron-sync        - Inicia o sync automático a cada 30 minutos em background"
	@echo "  zip PROJECT=...  - Baixa o projeto do Overleaf como arquivo zip"
	@echo "  pdf PROJECT=...  - Compila e baixa o PDF do projeto do Overleaf"

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
	docker compose --profile cron logs -f sync

sync:
	docker compose run --rm sync python3 /repo/scripts/sync.py

upload:
	@test -n "$(PATH_ARG)" || (echo "Uso: make upload PATH_ARG=caminho/do/projeto" && exit 1)
	docker compose run --rm sync python3 /repo/scripts/upload.py "$(PATH_ARG)"

upload-template:
	docker compose run --rm sync python3 /repo/scripts/upload.py /repo/Template --name "Template TCC CesarSchool"

setup:
	bash scripts/setup-env.sh

push-sync:
	bash scripts/setup-push-sync.sh

cron-sync:
	docker compose --profile cron up -d sync

zip:
	@test -n "$(PROJECT)" || (echo "Uso: make zip PROJECT=nome-do-projeto" && exit 1)
	docker compose run --rm sync python3 /repo/scripts/zip_project.py "$(PROJECT)"

pdf:
	@test -n "$(PROJECT)" || (echo "Uso: make pdf PROJECT=nome-do-projeto" && exit 1)
	docker compose run --rm sync python3 /repo/scripts/pdf_project.py "$(PROJECT)"
