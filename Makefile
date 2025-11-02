# Makefile - Development automation
.PHONY: help install dev test lint format clean docker-build docker-up docker-down show-versions bump-major bump-package check-versions
.PHONY: cec-setup cec-build cec-shell cec-test cec-scan cec-recreate cec-clean
.PHONY: build-core build-cli build-all
.PHONY: docs-serve docs-build docs-deploy docs-clean

# Default target
help:
	@echo "ComfyDock Development Commands:"
	@echo ""
	@echo "General Commands:"
	@echo "  make install      - Install all packages in development mode"
	@echo "  make dev          - Start development environment"
	@echo "  make test         - Run all tests"
	@echo "  make lint         - Run linting"
	@echo "  make format       - Format code"
	@echo "  make clean        - Clean build artifacts"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make docker-build - Build all Docker images"
	@echo "  make docker-up    - Start development containers"
	@echo "  make docker-down  - Stop development containers"
	@echo ""
	@echo "CEC Development Commands:"
	@echo "  make cec-setup    - Set up CEC test environment"
	@echo "  make cec-build    - Build CEC development container"
	@echo "  make cec-shell    - Enter CEC development shell"
	@echo "  make cec-test     - Run CEC tests in container"
	@echo "  make cec-scan     - Scan a test ComfyUI installation"
	@echo "  make cec-recreate - Recreate environment from manifest"
	@echo "  make cec-clean    - Clean up CEC containers"
	@echo ""
	@echo "Version Management:"
	@echo "  make show-versions - Show all package versions"
	@echo "  make check-versions - Check version compatibility"
	@echo "  make bump-major VERSION=X - Bump major version for all packages"
	@echo "  make bump-package PACKAGE=core VERSION=X.Y.Z - Bump individual package"
	@echo ""
	@echo "Build & Publishing:"
	@echo "  make build-core   - Build comfydock_core package"
	@echo "  make build-cli    - Build comfydock_cli package"
	@echo "  make build-all    - Build all packages"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs-serve   - Serve docs locally at http://localhost:8000"
	@echo "  make docs-build   - Build static documentation site"
	@echo "  make docs-deploy  - Deploy docs to GitHub Pages"
	@echo "  make docs-clean   - Clean built documentation files"

# Install all packages in development mode
install:
	uv sync --all-packages
	cd packages/frontend && npm install

# Start development environment
dev: docker-up
	@echo "Development environment is running!"
	@echo "  - CEC Dev Shell: make cec-shell"
	@echo "  - Server: http://localhost:8000"
	@echo "  - Frontend: http://localhost:5173"

# Run all tests
test:
	uv run pytest packages/core/tests
	uv run pytest packages/cec/tests
	uv run pytest packages/server/tests

# Run linting
lint:
	uv run ruff check packages/
	cd packages/frontend && npm run lint

# Format code
format:
	uv run ruff format packages/
	cd packages/frontend && npm run format

# Clean build artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +
	rm -rf .coverage htmlcov .pytest_cache

# Docker commands
docker-build:
	cd dev && docker compose build

docker-up:
	cd dev && docker compose up -d

docker-down:
	cd dev && docker compose down

# CEC-specific development commands
cec-setup:
	@echo "Setting up CEC test environment..."
	cd dev && ./scripts/dev-cec.sh setup

cec-build:
	@echo "Building CEC development container..."
	cd dev && ./scripts/dev-cec.sh build

cec-shell:
	@echo "Starting CEC development shell..."
	cd dev && ./scripts/dev-cec.sh shell

cec-test:
	@echo "Running CEC tests in container..."
	cd dev && ./scripts/dev-cec.sh test

cec-scan:
	@echo "Scanning test ComfyUI installation..."
	@if [ -z "$(TARGET)" ]; then \
		cd dev && ./scripts/dev-cec.sh scan; \
	else \
		cd dev && ./scripts/dev-cec.sh scan "$(TARGET)" "$(OUTPUT)"; \
	fi

cec-recreate:
	@echo "Recreating environment from manifest..."
	@if [ -z "$(MANIFEST)" ]; then \
		cd dev && ./scripts/dev-cec.sh recreate; \
	else \
		cd dev && ./scripts/dev-cec.sh recreate "$(MANIFEST)" "$(TARGET)"; \
	fi

cec-clean:
	@echo "Cleaning up CEC containers..."
	cd dev && ./scripts/dev-cec.sh clean

# Quick CEC workflow
cec-workflow: cec-setup cec-build
	@echo "CEC development environment ready!"
	@echo "Run 'make cec-shell' to start developing"

# Shell access to other containers
shell-server:
	cd dev && docker compose exec server-dev /bin/bash

# Version management commands
show-versions:
	@echo "Current package versions:"
	@echo -n "  comfydock:      " && grep '^version =' pyproject.toml | grep -oP 'version = "\K[^"]+'
	@echo -n "  comfydock-core: " && grep '^version =' packages/core/pyproject.toml | grep -oP 'version = "\K[^"]+'
	@echo -n "  comfydock-cli:  " && grep '^version =' packages/cli/pyproject.toml | grep -oP 'version = "\K[^"]+'

# Check version compatibility
check-versions:
	@python3 dev/scripts/check-versions.py

# Bump major version for all packages
bump-major:
	@echo "Bumping to major version $(VERSION).0.0"
	@sed -i 's/version = "[0-9]\+\.[0-9]\+\.[0-9]\+"/version = "$(VERSION).0.0"/' packages/*/pyproject.toml
	@sed -i 's/version = "[0-9]\+\.[0-9]\+\.[0-9]\+"/version = "$(VERSION).0.0"/' pyproject.toml
	@echo "Don't forget to update dependency constraints!"

# Bump individual package version
bump-package:
	@if [ -z "$(PACKAGE)" ] || [ -z "$(VERSION)" ]; then \
		echo "Usage: make bump-package PACKAGE=core VERSION=0.2.3"; \
		exit 1; \
	fi
	@sed -i 's/version = "[^"]*"/version = "$(VERSION)"/' packages/$(PACKAGE)/pyproject.toml
	@echo "Updated comfydock-$(PACKAGE) to version $(VERSION)"

# Build individual packages
build-core:
	@echo "Building comfydock_core..."
	@rm -rf dist/
	uv build --package comfydock_core --no-sources
	@echo "✓ Built comfydock_core (see dist/)"

build-cli:
	@echo "Building comfydock_cli..."
	@rm -rf dist/
	uv build --package comfydock_cli --no-sources
	@echo "✓ Built comfydock_cli (see dist/)"

build-all:
	@echo "Building all packages..."
	@rm -rf dist/
	uv build --package comfydock_core --no-sources
	@echo "✓ Built comfydock_core"
	uv build --package comfydock_cli --no-sources
	@echo "✓ Built comfydock_cli"
	@echo "✓ All packages built (see dist/)"

# Documentation commands
docs-serve:
	@echo "Starting documentation server..."
	@echo "Visit http://localhost:8000"
	cd docs/comfydock-docs && mkdocs serve

docs-build:
	@echo "Building documentation..."
	cd docs/comfydock-docs && mkdocs build
	@echo "✓ Documentation built (see docs/comfydock-docs/site/)"

docs-deploy:
	@echo "Deploying documentation to GitHub Pages..."
	cd docs/comfydock-docs && mkdocs gh-deploy
	@echo "✓ Documentation deployed"

docs-clean:
	@echo "Cleaning documentation build artifacts..."
	rm -rf docs/comfydock-docs/site/
	@echo "✓ Documentation cleaned"