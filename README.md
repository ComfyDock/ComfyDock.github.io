# ComfyDock Development Guide

## Overview

ComfyDock uses a monorepo structure with uv workspaces for better development ergonomics. All packages are developed together with shared tooling and a unified development environment.

## Project Structure

```
comfydock/
├── packages/          # All ComfyDock packages
│   ├── core/          # Core functionality
│   ├── cec/           # Environment Capture & Creation
│   ├── server/        # FastAPI server
│   ├── cli/           # CLI interface
│   └── frontend/      # Vite frontend
├── docker/            # Docker configurations
│   ├── base/          # Base images
│   ├── dev/           # Development containers
│   └── prod/          # Production containers
├── dev/               # Development environment
│   ├── docker-compose.yml
│   ├── scripts/       # Dev automation scripts
│   ├── test-environments/
│   └── caches/        # Shared caches
├── docs/              # Documentation
├── integrations/      # External integrations
└── Makefile           # Development automation
```

## Quick Start

### 1. Initial Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/comfydock.git
cd comfydock

# Install all packages in development mode
make install

# Build development containers
make docker-build
```

### 2. Development Workflow

```bash
# Start the development environment
make dev

# This starts:
# - CEC development container
# - Server with hot reload
# - Frontend with hot reload
# - Test ComfyUI instance
```

### 3. Testing CEC in Container

```bash
# Enter CEC development shell
make shell-cec

# Or run specific CEC commands
make cec-scan      # Scan a test ComfyUI installation
make cec-recreate  # Recreate from a manifest

# Run CEC tests in container
make test-cec
```

## Development Commands

### Package Management

```bash
# Add dependency to specific package
cd packages/cec
uv add some-package

# Add dev dependency to workspace
uv add --dev pytest-mock

# Sync all dependencies
uv sync --all-packages
```

### Testing

```bash
# Run all tests
make test

# Run specific package tests
uv run pytest packages/cec/tests -v

# Run with coverage
uv run pytest packages/cec/tests --cov=comfydock_cec
```

### Code Quality

```bash
# Run linting
make lint

# Format code
make format

# Type checking
uv run mypy packages/cec
```

## Working with CEC

### Development Setup

The CEC development container includes:
- All necessary build tools for Python packages
- CUDA libraries for GPU packages
- Pre-configured uv with caching
- Test ComfyUI installations

### Testing Workflow

1. **Prepare Test Environment**
   ```bash
   # Create a test ComfyUI installation
   cd dev/test-comfyui
   git clone https://github.com/comfyanonymous/ComfyUI.git instance1
   ```

2. **Scan the Installation**
   ```bash
   make cec-scan
   # This scans dev/test-comfyui/instance1
   # Output: dev/test-environments/scanned-manifest.json
   ```

3. **Test Recreation**
   ```bash
   make cec-recreate
   # Recreates from the manifest
   # Target: dev/test-environments/recreated
   ```

### Manual Testing in Container

```bash
# Enter the container
make shell-cec

# Inside container:
cd /workspace/cec
uv sync
uv run python -m comfydock_cec scan --help

# Scan a custom path
uv run python -m comfydock_cec scan \
  --target /test-comfyui/instance1 \
  --output /test-environments/my-manifest.json

# Test with different Python versions
uv run --python 3.11 python -m comfydock_cec scan ...
```

## Docker Development

### Container Architecture

- **cec-dev**: CEC development with build tools
- **server-dev**: FastAPI server with hot reload
- **frontend-dev**: Vite frontend with hot reload
- **test-comfyui**: Test ComfyUI instances

### Volume Mounts

```yaml
# Source code (live reload)
- ../packages/cec:/workspace/cec

# Test data
- ./test-environments:/test-environments
- ./test-comfyui:/test-comfyui

# Shared caches (persistent)
- ./caches/uv:/home/user/.cache/uv
- ./caches/comfydock:/home/user/.cache/comfydock
```

## Best Practices

### 1. Use the Development Environment

Always test CEC functionality inside the development container to ensure consistency with production environments.

### 2. Commit Lockfiles

Always commit `uv.lock` files to ensure reproducible builds.

### 3. Test Across Python Versions

```bash
# Test with different Python versions
uv run --python 3.10 pytest
uv run --python 3.11 pytest
uv run --python 3.12 pytest
```

### 4. Document Container Changes

When modifying Dockerfiles, update both development and production versions.

## Troubleshooting

### Container Issues

```bash
# Clean up and rebuild
make docker-down
docker system prune -f
make docker-build
make docker-up
```

### Permission Issues

The development containers run as UID 1000. If you have permission issues:

```bash
# Fix ownership
sudo chown -R 1000:1000 dev/caches
sudo chown -R 1000:1000 dev/test-environments
```

### Cache Issues

```bash
# Clear uv cache
rm -rf dev/caches/uv/*

# Clear ComfyDock cache
rm -rf dev/caches/comfydock/*
```

## Release Process

```bash
# Bump version (patch/minor/major)
make release-patch

# Build and test
make test
make docker-build

# Tag and push
git tag v$(cat VERSION)
git push origin main --tags
```