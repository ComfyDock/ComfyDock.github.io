# Publishing Workflows

This directory contains GitHub Actions workflows for publishing ComfyDock packages to PyPI.

## Prerequisites

### PyPI Trusted Publishing Setup

Before using these workflows, configure Trusted Publishing on PyPI:

1. Go to https://pypi.org/manage/account/publishing/
2. Add a new publisher for each package:
   - **PyPI Project Name**: `comfydock_core` (or `comfydock_cli`)
   - **Owner**: `ComfyDock`
   - **Repository name**: `ComfyDock`
   - **Workflow name**: `publish-core.yml` (or `publish-cli.yml`)
   - **Environment name**: (leave blank)

## Workflows

### `publish-core.yml`
Builds and publishes `comfydock_core` package to PyPI.

**Usage:**
1. Bump version: `make bump-package PACKAGE=core VERSION=1.0.1`
2. Commit and push changes
3. Go to Actions → "Publish Core Package" → Run workflow

### `publish-cli.yml`
Builds and publishes `comfydock_cli` package to PyPI.

**Usage:**
1. Bump version: `make bump-package PACKAGE=cli VERSION=1.0.1`
2. Commit and push changes
3. Go to Actions → "Publish CLI Package" → Run workflow

## Publishing Order

**Important:** If both packages have interdependent changes:

1. **First:** Publish `comfydock_core`
2. **Wait:** ~2 minutes for PyPI to index the new version
3. **Then:** Publish `comfydock_cli`

The CLI package depends on `comfydock_core` from PyPI, so core must be published first.

## Local Testing

Test builds locally before publishing:

```bash
# Build core package
make build-core

# Build CLI package
make build-cli

# Build both
make build-all

# Inspect built packages
ls -lh dist/
```

## Security

- Workflows use **Trusted Publishing** (no API tokens required)
- Actions use stable version tags (@v4, @v5)
- Minimal permissions (read-only by default)
- Credentials are not persisted after checkout
