# Overleaf Local

Overleaf Community Edition rodando localmente via Docker, com sync automático dos projetos para o seu repositório git. Suporta AMD64 e ARM64 (incluindo Apple Silicon).

Feito para estudantes de Ciência da Computação escrevendo o TCC: você escreve o LaTeX num Overleaf que roda na sua própria máquina (sem depender do servidor oficial, sem limite de projetos) e tudo fica versionado no seu git como backup.

## Antes de começar: o que você precisa entender

- **Isso roda dentro de containers Docker.** Você não instala Overleaf "de verdade" no seu computador — o Docker sobe um ambiente isolado com tudo que o Overleaf precisa (banco de dados, fila de jobs, o próprio Overleaf). Por isso o único pré-requisito pesado é o Docker.
- **Seus arquivos `.tex` ficam sincronizados em dois lugares**: dentro do Overleaf (interface web) e na pasta `projects/` do seu repositório (arquivos comuns, que você pode versionar, ver diff, etc.). O sync entre os dois é automático.
- **Isso é local.** Só você acessa esse Overleaf, pelo seu navegador, em `http://localhost`. Ninguém de fora consegue acessar — é como se fosse um site rodando só na sua máquina.

## Como começar

### 1. Crie o seu repositório a partir deste template

Clique em **"Use this template"** no topo desta página do GitHub → **"Create a new repository"**. Isso cria uma cópia independente deste projeto na sua conta, sem herdar o histórico de commits daqui.

### 2. Clone o seu repositório

```bash
git clone git@github.com:seu-usuario/seu-repositorio.git meu-tcc
cd meu-tcc
```

(Troque a URL pela do repositório que você acabou de criar.)

### 3. Instale os pré-requisitos

| Ferramenta         | Para que serve                                              | Como instalar                                                                                                               |
| ------------------ | ----------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **Docker Desktop** | Roda o Overleaf e o banco de dados                          | [docs.docker.com/get-docker](https://docs.docker.com/get-docker/) — no Windows, o instalador já configura o WSL2 necessário |
| **Git**            | Clonar o repositório e versionar seus arquivos              | [git-scm.com/downloads](https://git-scm.com/downloads)                                                                      |
| **Make**           | Roda os comandos do projeto (`make up`, `make build`, etc.) | Linux/Mac já vem instalado. No Windows, use o **Git Bash** que acompanha a instalação do Git, ou WSL2                       |

> **Importante:** depois de instalar o Docker Desktop, **abra o programa** e espere o ícone dele indicar que está rodando antes de continuar. É o erro mais comum de quem está começando: instalar o Docker mas esquecer de abrir o app.

### 4. Configure o ambiente

```bash
make setup
```

Isso cria o arquivo `.env` a partir do `.env.example` e preenche automaticamente:

- `DOCKER_UID` / `DOCKER_GID` com o seu usuário do sistema
- `DOCKER_PLATFORM` com a arquitetura da sua máquina (`linux/amd64` ou `linux/arm64`)

Abra o `.env` gerado e defina:

```env
OVERLEAF_EMAIL=admin@overleaf.local   # pode deixar esse valor
OVERLEAF_PASSWORD=sua_senha           # você vai definir essa senha no passo 6
```

### 5. Suba os containers

```bash
make build
make up
```

Na primeira vez, o `make build` demora alguns minutos — ele instala o TexLive com suporte a português dentro da imagem do Overleaf. Isso só acontece uma vez.

### 6. Ative o usuário admin

O usuário `admin@overleaf.local` é criado automaticamente, mas ainda não tem senha. Veja o link de ativação nos logs:

```bash
make logs
```

Procure por uma linha parecida com:

```
http://localhost/user/activate?token=...&user_id=...
```

Copie essa URL, cole no navegador, e defina a senha. Depois, volte no `.env` e atualize `OVERLEAF_PASSWORD` com a senha que você escolheu (ela é usada pelo sync automático pra fazer login).

### 7. Acesse o Overleaf

Abra [http://localhost](http://localhost) no navegador e entre com `admin@overleaf.local` e a senha que você definiu.

---

## Resolução de problemas comuns

| Sintoma                                                 | Causa provável                                                               | O que fazer                                                                                                                                                                                                                |
| ------------------------------------------------------- | ---------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Cannot connect to the Docker daemon`                   | Docker Desktop instalado mas não está aberto                                 | Abra o Docker Desktop e espere o ícone ficar "verde"/ativo antes de rodar `make` de novo                                                                                                                                   |
| `make: command not found` (Windows)                     | Terminal padrão do Windows (cmd/PowerShell) não tem `make`                   | Use o **Git Bash** (instalado junto com o Git) ou WSL2                                                                                                                                                                     |
| `port is already allocated` na porta 80                 | Outro programa (ex: outro servidor web, Skype antigo, IIS) já usa a porta 80 | Feche o programa que está usando a porta, ou pare o container com `make down` e verifique o que mais está rodando na porta 80                                                                                              |
| Link de ativação não aparece em `make logs`             | Containers ainda estão subindo, ou você já ativou antes                      | Espere alguns segundos e rode `make logs` de novo; se já tiver ativado, acesse `http://localhost` direto e faça login                                                                                                      |
| Esqueci a senha do admin                                | —                                                                            | Não há recuperação de senha automática nesse setup local; apague a pasta `data/` (isso reseta TUDO, incluindo projetos salvos só no Overleaf) e refaça o setup do zero — por isso é importante manter o `make sync` em dia |
| Erros de permissão em arquivos criados pelos containers | `DOCKER_UID`/`DOCKER_GID` não bateram com seu usuário                        | Rode `make setup` de novo — ele recalcula esses valores                                                                                                                                                                    |

Se nada disso resolver, rode `make logs` e `make logs-sync` e leia a mensagem de erro completa antes de pedir ajuda — ela quase sempre indica o problema exato.

---

## Sync de projetos

Os projetos do Overleaf são espelhados na pasta `projects/`, um subdiretório por projeto. O sync acontece de três formas:

| Modo           | Como funciona                                                                    |
| -------------- | -------------------------------------------------------------------------------- |
| **Automático** | Container `overleaf-sync` roda a cada 30 minutos (opt-in, veja `make cron-sync`) |
| **Pre-push**   | Dispara antes de todo `git push` (opcional)                                      |
| **Manual**     | Comando abaixo                                                                   |

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
| `make build`                  | Constrói/reconstrói as imagens                                |
| `make up`                     | Sobe todos os containers em background                        |
| `make down`                   | Para e remove os containers                                   |
| `make restart`                | Reinicia os containers                                        |
| `make logs`                   | Acompanha os logs do Overleaf                                 |
| `make logs-sync`              | Acompanha os logs do serviço de sync                          |
| `make sync`                   | Executa o sync manualmente                                    |
| `make push-sync`              | Instala hook de pre-push para sincronizar antes de cada push  |
| `make cron-sync`              | Inicia o sync automático a cada 30 minutos em background      |
| `make upload PATH_ARG=<path>` | Sobe um diretório ou zip como novo projeto no Overleaf        |
| `make upload-template`        | Sobe o Template padrão para o Overleaf                        |
| `make zip PROJECT=<nome>`     | Baixa o projeto do Overleaf como arquivo zip                  |
| `make pdf PROJECT=<nome>`     | Compila e baixa o PDF do projeto do Overleaf                  |

---

## Estrutura do repositório

```
├── docker/
│   ├── sharelatex/         # Imagem do Overleaf com TexLive em português
│   └── sync/               # Container de sync (Python + git + crond)
├── scripts/
│   ├── sync.py             # Script de sync (download) dos projetos
│   ├── upload.py           # Script de upload de projetos para o Overleaf
│   ├── zip_project.py      # Baixa um projeto do Overleaf como zip
│   ├── pdf_project.py      # Compila e baixa o PDF de um projeto do Overleaf
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
