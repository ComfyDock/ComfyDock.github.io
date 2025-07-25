# Makefile - Development automation
.PHONY: help install dev test lint format clean docker-build docker-up docker-down

# Default target
help:
	@echo "ComfyDock Development Commands:"
	@echo "  make install      - Install all packages in development mode"
	@echo "  make dev          - Start development environment"
	@echo "  make test         - Run all tests"
	@echo "  make test-cec     - Test CEC in container"
	@echo "  make lint         - Run linting"
	@echo "  make format       - Format code"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make docker-build - Build all Docker images"
	@echo "  make docker-up    - Start development containers"
	@echo "  make docker-down  - Stop development containers"

# Install all packages in development mode
install:
	uv sync --all-packages
	cd packages/frontend && npm install

# Start development environment
dev: docker-up
	@echo "Development environment is running!"
	@echo "  - CEC Dev Shell: make shell-cec"
	@echo "  - Server: http://localhost:8000"
	@echo "  - Frontend: http://localhost:5173"

# Run all tests
test:
	uv run pytest packages/core/tests
	uv run pytest packages/cec/tests
	uv run pytest packages/server/tests

# Test CEC in container
test-cec: docker-build
	cd dev && ./scripts/dev-cec.sh test

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
	cd dev && docker-compose build

docker-up:
	cd dev && docker-compose up -d

docker-down:
	cd dev && docker-compose down

# Shell access
shell-cec:
	cd dev && docker-compose run --rm cec-dev

shell-server:
	cd dev && docker-compose exec server-dev /bin/bash

# CEC specific commands
cec-scan:
	cd dev && ./scripts/dev-cec.sh scan

cec-recreate:
	cd dev && ./scripts/dev-cec.sh recreate

# Release commands
release-patch:
	cd build-scripts && uv run python version_manager.py bump patch

release-minor:
	cd build-scripts && uv run python version_manager.py bump minor

release-major:
	cd build-scripts && uv run python version_manager.py bump major