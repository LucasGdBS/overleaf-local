# Overleaf Local

Overleaf Community Edition rodando localmente via Docker, com sync automático dos projetos para o repositório git. Suporta AMD64 e ARM64 (incluindo Apple Silicon).

## Quick Start (via npx)

> Requer Node.js 18+ e Docker instalados.

```bash
npx create-overleaf-local meu-projeto
cd meu-projeto
make build && make up
make logs   # mostra a URL de ativação do admin
```

Com o template TCC CesarSchool incluso:

```bash
npx create-overleaf-local meu-tcc --template cesarschool
```

---

## Pré-requisitos

- Docker e Docker Compose
- Git
- Make (opcional, mas recomendado para facilitar os comandos)

## Primeiro uso

### 1. Configurar o ambiente

```bash
make setup
```

Cria o `.env` a partir do exemplo e preenche automaticamente:

- `DOCKER_UID` / `DOCKER_GID` com o usuário atual
- `DOCKER_PLATFORM` com a arquitetura da máquina (`linux/amd64` ou `linux/arm64`)

Preencha o `.env` gerado com suas credenciais:

```env
OVERLEAF_EMAIL=admin@overleaf.local   # email do admin criado automaticamente
OVERLEAF_PASSWORD=sua_senha           # senha que você vai definir no passo 3
```

### 2. Subir os containers

```bash
make up
```

Na primeira execução, o build da imagem do Overleaf demora alguns minutos (instala o TexLive com suporte a português).

### 3. Definir senha do admin

O usuário `admin@overleaf.local` é criado automaticamente. Para definir a senha, veja o link gerado nos logs:

```bash
make logs
```

A saída vai conter algo como:

```link
http://localhost/user/activate?token=...&user_id=...
```

Acesse essa URL no navegador, defina a senha e volte para atualizar o `.env` com ela.

### 4. Acessar o Overleaf

Abra [http://localhost](http://localhost) e entre com `admin@overleaf.local`.

---

## Sync de projetos

Os projetos do Overleaf são espelhados na pasta `projects/`, um subdiretório por projeto. O sync acontece de três formas:

| Modo           | Como funciona                                    |
| -------------- | ------------------------------------------------ |
| **Automático** | Container `overleaf-sync` roda a cada 30 minutos |
| **Pre-push**   | Dispara antes de todo `git push` (opcional)      |
| **Manual**     | Comando abaixo                                   |

```bash
make sync
```

O log do cron fica em `sync.log` (ignorado pelo git).

### Sync automático no pre-push (opcional)

Para sincronizar automaticamente antes de cada `git push`, instale o hook:

```bash
make push-sync
```

---

## Upload de projetos

Além do sync de download, é possível subir projetos locais para o Overleaf — útil para o setup inicial ou para importar templates.

O upload sempre cria um **projeto novo** no Overleaf (não sobrescreve um existente). O script empacota o diretório em zip e usa a mesma API interna que o Overleaf usa quando você arrasta um zip na interface web.

### Subir o Template padrão

```bash
make upload-template
```

Sobe a pasta `Template/` como um novo projeto chamado `"Template TCC CesarSchool"`.

### Subir qualquer pasta ou zip

```bash
# Subir um diretório (será empacotado automaticamente em zip)
make upload PATH_ARG=projects/MeuProjeto

# Subir um zip já pronto com nome personalizado
docker compose run --rm sync python3 /repo/scripts/upload.py /repo/Template/Template.zip --name "Meu Projeto"
```

---

## Comandos disponíveis

| Comando                       | O que faz                                                     |
| ----------------------------- | ------------------------------------------------------------- |
| `make setup`                  | Cria `.env` e configura UID, GID e plataforma automaticamente |
| `make push-sync`              | Instala hook de pre-push para sincronizar antes de cada push  |
| `make up`                     | Sobe todos os containers em background                        |
| `make down`                   | Para e remove os containers                                   |
| `make restart`                | Reinicia os containers                                        |
| `make build`                  | Reconstrói as imagens                                         |
| `make logs`                   | Acompanha os logs do Overleaf                                 |
| `make logs-sync`              | Acompanha os logs do serviço de sync                          |
| `make sync`                   | Executa o sync manualmente                                    |
| `make upload PATH_ARG=<path>` | Sobe um diretório ou zip como novo projeto no Overleaf        |
| `make upload-template`        | Sobe o Template padrão para o Overleaf                        |

---

## Estrutura do repositório

```yaml
├── docker/
│   ├── sharelatex/         # Imagem do Overleaf com TexLive em português
│   └── sync/               # Container de sync (Python + git + crond)
├── scripts/
│   ├── sync.py             # Script de sync (download) dos projetos
│   ├── upload.py           # Script de upload de projetos para o Overleaf
│   ├── setup-env.sh        # Configura .env com UID, GID e plataforma do sistema
│   └── setup-push-sync.sh  # Instala o hook pre-push
├── config/
│   └── mongodb-init-replica-set.js
├── Template/               # Template LaTeX do TCC CesarSchool
├── projects/               # Projetos espelhados do Overleaf (versionados)
├── data/                   # Dados persistentes dos containers (ignorado pelo git)
├── docker-compose.yml
├── Makefile
├── .env.example
└── .env                    # Credenciais (ignorado pelo git)
```
