# ComfyDock Codebase Map

This file provides a comprehensive overview of the ComfyDock monorepo structure.

## Project Overview

ComfyDock is a monorepo workspace using `uv` for Python package management. It provides unified environment management for ComfyUI through multiple coordinated packages.

## Root Structure

```
.
├── CLAUDE.md                          # 📋 AI assistant instructions and project conventions
├── LICENSE
├── Makefile                           # 🔧 Development automation commands
├── README.md                          # 📖 Main development guide
├── dev/                               # 🛠️ Development environment
│   ├── dev-cec.sh                     # CEC development helper script
│   ├── docker-compose.yml             # Docker services configuration
│   ├── scripts/
│   │   └── check-versions.py          # ✅ Version compatibility checker
│   └── test-environments/             # Test environment configurations
├── docker/                            # 🐳 Docker configurations
│   ├── base/                          # Base Docker images
│   │   ├── Dockerfile
│   │   └── docker_startup_scripts/
│   │       ├── entrypoint.py          # 🚀 Container entry point
│   │       ├── install_comfyui.py     # ComfyUI installation script
│   │       ├── install_pytorch.py     # PyTorch installation script
│   │       └── utils/
│   ├── dev/                           # Development containers
│   │   └── Dockerfile.cec-dev
│   └── prod/                          # Production containers (empty)
├── docs/                              # 📚 Documentation root
│   ├── docs/                          # Documentation source files
│   │   ├── assets/                    # Images and videos
│   │   ├── best_practices.md
│   │   ├── environments.md
│   │   ├── index.md
│   │   ├── installation.md
│   │   ├── troubleshooting/           # Troubleshooting guides
│   │   └── usage.md
│   ├── mkdocs.yml                     # MkDocs configuration
│   └── site/                          # Generated documentation site
├── integrations/                      # External integrations (empty)
├── packages/                          # 📦 All ComfyDock packages
│   ├── cec/                           # 🔍 ComfyUI Environment Capture (v0.1.0)
│   │   ├── pyproject.toml             # Dependencies: packaging, pipdeptree, requests, uv
│   │   ├── scripts/                   # Testing and migration scripts
│   │   ├── src/comfyui_detector/
│   │   │   ├── cli/                   # CEC CLI interface
│   │   │   ├── core/                  # 🎯 Core detection/recreation logic
│   │   │   │   ├── detector.py       # Main detection engine
│   │   │   │   ├── manifest_generator.py  # Environment manifest creation
│   │   │   │   └── recreator.py      # Environment recreation logic
│   │   │   ├── detection/             # 🔎 Detection modules
│   │   │   │   ├── custom_node_scanner.py   # Custom node detection
│   │   │   │   ├── package_detector.py      # Python package detection
│   │   │   │   └── system_detector.py       # System info detection
│   │   │   ├── integrations/
│   │   │   │   └── uv.py              # UV package manager integration
│   │   │   ├── setup/                 # 🔨 Environment setup
│   │   │   │   ├── custom_node_installer.py  # Custom node installation
│   │   │   │   ├── environment_setup.py      # Environment configuration
│   │   │   │   └── environment_validator.py  # Setup validation
│   │   │   └── utils/                 # Various utility modules
│   │   └── tests/                     # Unit and integration tests
│   ├── cli/                           # 💻 Command-line interface (v0.3.3)
│   │   ├── comfydock_cli/
│   │   │   ├── cli.py                 # 🎯 Main CLI entry point
│   │   │   ├── commands/              # CLI command implementations
│   │   │   │   ├── config.py         # Configuration management
│   │   │   │   ├── dev.py            # Development commands
│   │   │   │   ├── server.py         # Server control commands
│   │   │   │   └── update.py         # Update management
│   │   │   ├── core/                  # CLI core functionality
│   │   │   │   ├── config.py         # Config handling
│   │   │   │   ├── logging.py        # Logging setup
│   │   │   │   └── updates.py        # Update logic
│   │   │   └── utils/                 # CLI utilities
│   │   ├── config files               # Various JSON configuration files
│   │   └── pyproject.toml             # Dependencies: click, comfydock-server
│   ├── core/                          # 🏗️ Core functionality (v0.2.2)
│   │   ├── pyproject.toml             # Dependencies: aiodocker, docker, filelock, pydantic
│   │   ├── src/comfydock_core/
│   │   │   ├── __init__.py
│   │   │   ├── comfyui_integration.py # 🔗 ComfyUI integration logic
│   │   │   ├── connection.py          # Connection management
│   │   │   ├── docker_interface.py    # 🐳 Docker API interface
│   │   │   ├── environment.py         # Environment management
│   │   │   ├── persistence.py         # 💾 Data persistence layer
│   │   │   ├── user_settings.py       # User settings management
│   │   │   └── utils.py               # Utility functions
│   │   └── tests/                     # Unit tests
│   ├── frontend/                      # 🌐 Web UI (React/Vite)
│   │   ├── package.json               # Node dependencies
│   │   ├── public/                    # Static assets
│   │   ├── src/
│   │   │   ├── App.tsx                # 🎯 Main application component
│   │   │   ├── api/                   # API client code
│   │   │   ├── components/            # React components
│   │   │   │   ├── EnvironmentCard.tsx
│   │   │   │   ├── EnvironmentManager.tsx
│   │   │   │   ├── dialogs/          # Dialog components
│   │   │   │   ├── form/             # Form components
│   │   │   │   └── ui/               # UI library components
│   │   │   ├── hooks/                 # React hooks
│   │   │   └── types/                 # TypeScript definitions
│   │   └── vite.config.ts             # Vite configuration
│   └── server/                        # 🖥️ FastAPI server (v0.3.2)
│       ├── pyproject.toml             # Dependencies: comfydock-core, fastapi, uvicorn
│       ├── src/comfydock_server/
│       │   ├── app.py                 # 🎯 FastAPI application setup
│       │   ├── config/                # Configuration management
│       │   │   ├── default_config.json
│       │   │   ├── loader.py          # Config loading logic
│       │   │   └── schema.py          # Config schema definitions
│       │   ├── docker_utils.py        # Docker utilities
│       │   ├── routes/                # 🛣️ API endpoints
│       │   │   ├── comfyui_routes.py  # ComfyUI control endpoints
│       │   │   ├── environment_routes.py  # Environment management
│       │   │   ├── image_routes.py    # Image handling
│       │   │   ├── user_settings_routes.py  # Settings management
│       │   │   └── websocket_routes.py      # WebSocket connections
│       │   └── server.py              # Server entry point
│       └── test/                      # Manual testing scripts
├── pyproject.toml                     # 📝 Root workspace configuration (v0.5.0)
└── uv.lock                            # 🔒 Workspace dependency lock

```

## Key Features by Package

### comfydock-core (v0.2.2)
- Base classes and interfaces for all other packages
- Docker container management
- Environment persistence
- ComfyUI integration abstractions

### comfydock-server (v0.3.2)
- REST API for environment management
- WebSocket support for real-time updates
- Docker container orchestration
- Image serving and management

### comfydock-cli (v0.3.3)
- Command-line interface for ComfyDock
- Server management commands
- Configuration management
- Development utilities

### comfydock-cec (v0.1.0)
- Detect existing ComfyUI installations
- Capture environment configurations
- Recreate environments from manifests
- Custom node detection and installation

### Frontend (React/Vite)
- Web-based UI for environment management
- Real-time status updates
- Environment creation and configuration
- Docker container control

## Development Commands

```bash
# Install all packages in development mode
make install

# Start development environment
make dev

# Run all tests
make test

# Run linting
make lint

# Format code
make format

# Check version compatibility
make check-versions

# Show all package versions
make show-versions

# Bump major version for all packages
make bump-major VERSION=1

# Bump individual package version
make bump-package PACKAGE=core VERSION=0.2.3
```

## Version Management Strategy

- **Major version (X.0.0)**: All packages move together for breaking changes
- **Minor version (0.X.0)**: Independent feature additions per package
- **Patch version (0.0.X)**: Independent bug fixes per package
- **Dependency upper bounds**: Prevent major version incompatibilities

## Important Notes

- This is a monorepo managed by `uv` workspaces
- All packages must maintain the same major version
- Use provided Make commands for development tasks
- Follow version management workflow in CLAUDE.md
- Docker is required for full functionality