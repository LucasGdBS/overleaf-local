---
name: Bug
about: Reportar um comportamento inesperado ou quebrado
title: "[Bug] "
labels: bug
---

## O que aconteceu

<!-- Descreva o problema. O que você esperava que acontecesse e o que aconteceu de fato? -->

## Como reproduzir

<!-- Passos pra reproduzir o problema. Ex:
1. make down && make build && make up
2. Acessar http://localhost e fazer login
3. ...
-->

## Ambiente

- SO / arquitetura (ex.: macOS Apple Silicon, Linux x86_64):
- `DOCKER_PLATFORM` no `.env`:
- Saída de `docker compose version`:

## Logs relevantes

<!-- Cole aqui a saída de `make logs` ou `make logs-sync`, se aplicável -->

```

```

## Checklist

- [ ] Rodei `make down && make build && make up` e o problema persiste
- [ ] Não há `.env` ou credenciais nos logs colados acima
