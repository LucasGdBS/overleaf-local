#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const VALID_TEMPLATES = ['cesarschool'];

const COPY_MAP = [
  'docker/sharelatex/Dockerfile',
  'docker/sharelatex/init-admin.sh',
  'docker/sync/Dockerfile',
  'docker/sync/entrypoint.sh',
  'config/mongodb-init-replica-set.js',
  'scripts/setup-env.sh',
  'scripts/setup-push-sync.sh',
  'scripts/sync.py',
  'scripts/upload.py',
  'scripts/zip_project.py',
  'scripts/pdf_project.py',
  'Makefile',
  'docker-compose.yml',
  '.env.example',
  'README.md',
  '.gitignore',
];

const EXECUTABLE_FILES = [
  'scripts/setup-env.sh',
  'scripts/setup-push-sync.sh',
  'docker/sharelatex/init-admin.sh',
  'docker/sync/entrypoint.sh',
];

function printUsage() {
  console.log(`
Usage: npx create-overleaf-local <project-name> [options]

Options:
  --template <name>   Includes a LaTeX template. Available: cesarschool
  --help              Show this help message

Examples:
  npx create-overleaf-local meu-projeto
  npx create-overleaf-local meu-tcc --template cesarschool
`);
}

function parseArgs(argv) {
  const args = argv.slice(2);
  let projectName = null;
  let template = null;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--help' || args[i] === '-h') {
      return { help: true };
    }
    if (args[i] === '--template') {
      template = args[++i];
    } else if (!args[i].startsWith('-')) {
      projectName = args[i];
    }
  }

  return { projectName, template, help: false };
}

function copyFile(src, dest) {
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.copyFileSync(src, dest);
}

function main() {
  const { projectName, template, help } = parseArgs(process.argv);

  if (help) {
    printUsage();
    process.exit(0);
  }

  if (!projectName) {
    console.error('Error: project name is required.');
    printUsage();
    process.exit(1);
  }

  if (template && !VALID_TEMPLATES.includes(template)) {
    console.error(`Error: unknown template "${template}". Available: ${VALID_TEMPLATES.join(', ')}`);
    process.exit(1);
  }

  const targetDir = path.resolve(process.cwd(), projectName);

  if (fs.existsSync(targetDir)) {
    console.error(`Error: directory "${projectName}" already exists.`);
    process.exit(1);
  }

  const pkgRoot = path.join(__dirname, '..');

  console.log(`\nCreating project "${projectName}"...`);

  fs.mkdirSync(targetDir);

  for (const file of COPY_MAP) {
    const src = path.join(pkgRoot, file);
    const dest = path.join(targetDir, file);
    if (fs.existsSync(src)) {
      copyFile(src, dest);
    }
  }

  if (template === 'cesarschool') {
    const templateSrc = path.join(pkgRoot, 'Template');
    const templateDest = path.join(targetDir, 'Template');
    if (fs.existsSync(templateSrc)) {
      fs.cpSync(templateSrc, templateDest, { recursive: true });
    }
  }

  fs.mkdirSync(path.join(targetDir, 'projects'), { recursive: true });
  fs.writeFileSync(path.join(targetDir, 'projects', '.gitkeep'), '');

  for (const file of EXECUTABLE_FILES) {
    const filePath = path.join(targetDir, file);
    if (fs.existsSync(filePath)) {
      fs.chmodSync(filePath, 0o755);
    }
  }

  try {
    execSync('git init', { cwd: targetDir, stdio: 'inherit' });
  } catch {
    console.warn('Warning: could not run git init. Install git and run it manually.');
  }

  try {
    execSync('bash scripts/setup-env.sh', { cwd: targetDir, stdio: 'inherit' });
  } catch {
    console.warn('Warning: could not run setup-env.sh automatically. Run "make setup" manually.');
  }

  console.log(`
Project "${projectName}" is ready!

Next steps:
  cd ${projectName}
  make build    # builds Docker images (a few minutes on first run)
  make up       # starts all containers
  make logs     # shows the admin activation URL
`);
}

main();
