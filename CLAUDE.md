# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

Local Overleaf Community Edition running via Docker Compose, with tooling to mirror projects back to git and upload local LaTeX projects into Overleaf. Supports AMD64 and ARM64 (Apple Silicon via `DOCKER_PLATFORM`).

## Common commands

```bash
# First-time setup — generates .env with correct UID/GID/platform
make setup

# Container lifecycle
make up          # start all services in background
make down        # stop and remove containers
make build       # rebuild images (needed after Dockerfile changes)
make logs        # follow Overleaf logs (also shows the admin activation URL on first run)
make logs-sync   # follow the sync container logs

# Sync and upload
make sync                        # download all Overleaf projects → projects/ (one-shot)
make upload PATH_ARG=path/to/dir # pack a directory as a new Overleaf project
make upload-template             # upload Template/ as "Template TCC CesarSchool"
make cron-sync                   # start the sync container in background (syncs every 30 min)
```

To run a script directly inside the sync container (e.g. for debugging):

```bash
docker compose run --rm sync python3 /repo/scripts/sync.py
docker compose run --rm sync python3 /repo/scripts/upload.py /repo/Template --name "My Project"
```

## Architecture

### Docker services (`docker-compose.yml`)

| Service      | Image                               | Role                                                                                                    |
| ------------ | ----------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `sharelatex` | custom build (`docker/sharelatex/`) | Overleaf CE + TexLive with Portuguese support, port 80                                                  |
| `mongo`      | `mongo:8.0`                         | MongoDB with replica set (`--replSet overleaf`), initialised by `config/mongodb-init-replica-set.js`    |
| `redis`      | `redis:6.2`                         | Session/job queue for Overleaf                                                                          |
| `sync`       | custom build (`docker/sync/`)       | Python Alpine container; mounts the whole repo at `/repo`, runs `sync.py` every 30 min via a shell loop. Uses Docker Compose profile `cron` — **not started by `make up`**, only by `make cron-sync`. |

The `sync` container (when started via `make cron-sync`) starts only after `sharelatex` passes its healthcheck (`curl /login`). One-off commands like `make sync` and `make upload` use `docker compose run --rm sync` and don't require the container to be running.

### Sync flow (`scripts/sync.py`)

1. Loads credentials from `.env`
2. GETs `/login` to extract CSRF token
3. POSTs credentials to `/login`
4. Fetches project list from `/user/projects` (falls back to parsing `ol-prefetchedProjectsBlob` meta tag)
5. Downloads each active project as a zip via `/project/<id>/download/zip`, extracts to `projects/<sanitized-name>/`
6. Removes local dirs that no longer exist as active projects

### Upload flow (`scripts/upload.py`)

Same authentication pattern. Packs a directory into a zip (files at root level, no wrapper directory), then POSTs to `/project/new/upload` with CSRF token and `multipart/form-data`.

### Key env vars (`.env`)

| Variable                    | Purpose                                                                               |
| --------------------------- | ------------------------------------------------------------------------------------- |
| `OVERLEAF_EMAIL`            | Admin account email (default `admin@overleaf.local`)                                  |
| `OVERLEAF_PASSWORD`         | Admin password — set after visiting the activation URL from `make logs`               |
| `DOCKER_UID` / `DOCKER_GID` | Run the sync container as the host user (avoids permission issues on mounted volumes) |
| `DOCKER_PLATFORM`           | `linux/amd64` or `linux/arm64` — controls the Overleaf container platform             |

The `.env` file is gitignored; `.env.example` is the template.

### Pre-push hook (optional)

`make push-sync` installs `.git/hooks/pre-push` via `scripts/setup-push-sync.sh`, which runs `make sync` before every `git push` to keep `projects/` up to date.

### Persistent data

`data/` holds MongoDB, Redis, and Overleaf file data. It is gitignored and must not be committed.

### LaTeX template

`Template/` contains a CesarSchool TCC template structured as `main.tex` + chapter/pretextual/postextual includes. Use `make upload-template` to push it into a running Overleaf instance.
