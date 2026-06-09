# CLI de Scaffolding — `create-overleaf-local`

## O que foi adicionado

### Arquivos novos

| Arquivo         | Descrição                                                         |
| --------------- | ----------------------------------------------------------------- |
| `package.json`  | Define o pacote npm `create-overleaf-local` (bin, files, engines) |
| `bin/create.js` | CLI entry point — toda a lógica de scaffolding em Node.js puro    |

### Arquivos modificados

| Arquivo      | Alteração                                                          |
| ------------ | ------------------------------------------------------------------ |
| `.gitignore` | Adicionado `node_modules/` e `*.tgz`                               |
| `README.md`  | Seção "Quick Start (via npx)" adicionada antes de "Pré-requisitos" |

---

## Como funciona

O comando cria um novo diretório com toda a infraestrutura pronta, configura o `.env` automaticamente (UID/GID/plataforma detectados) e inicializa um repositório git.

```bash
# Projeto sem template
npx create-overleaf-local meu-projeto

# Com template TCC CesarSchool
npx create-overleaf-local meu-tcc --template cesarschool

# Alias nativo do npm (após publicação)
npm create overleaf-local meu-projeto
```

O que o comando faz internamente:

1. Cria o diretório `<project-name>/`
2. Copia todos os arquivos de infraestrutura (`docker/`, `scripts/`, `Makefile`, etc.)
3. Copia `Template/` se `--template cesarschool` for passado
4. Cria `projects/.gitkeep`
5. Restaura permissões executáveis nos shell scripts (`chmod 755`)
6. Roda `git init`
7. Roda `bash scripts/setup-env.sh` (equivalente ao `make setup`)

---

## Próximos passos

### 1. Publicar no npm

```bash
# Login na sua conta npmjs.com (só precisa fazer uma vez)
npm login

# Verificar o manifest antes de publicar
npm pack --dry-run

# Publicar
npm publish --access public
```

> O nome `create-overleaf-local` precisa estar disponível no registro npm.
> Verifique em: [https://www.npmjs.com/package/create-overleaf-local](https://www.npmjs.com/package/create-overleaf-local)

### 2. Testar após publicação

```bash
# Em um diretório qualquer fora do repo
npx create-overleaf-local teste-publicado
cd teste-publicado && cat .env
```

### 3. (Opcional) Adicionar ao repositório como GitHub Template

No GitHub, vá em **Settings → General → Template repository** e ative a opção. Isso adiciona um botão "Use this template" no topo do repo, complementando o fluxo de `npx` para quem prefere a interface web.

### 4. (Opcional) Versionamento

Para futuras versões, atualize `version` no `package.json` antes de publicar:

```bash
npm version patch   # 1.0.0 → 1.0.1 (bug fix)
npm version minor   # 1.0.0 → 1.1.0 (nova feature)
npm version major   # 1.0.0 → 2.0.0 (breaking change)
npm publish --access public
```

### 5. (Opcional) Adicionar mais templates

Para adicionar um novo template ao CLI, edite `bin/create.js`:

```js
// Linha 9: adicione o novo nome ao array
const VALID_TEMPLATES = ["cesarschool", "novo-template"];
```

E adicione a pasta correspondente ao `files` em `package.json` se necessário.
