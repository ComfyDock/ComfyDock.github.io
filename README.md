# ComfyDock

A package and environment manager for ComfyUI, bringing reproducibility and version control to AI image generation workflows.

## Why ComfyDock?

If you've worked with ComfyUI for a while, you've probably hit these problems:

- **Dependency hell**: Installing a new custom node breaks your existing workflows
- **No reproducibility**: "It worked last month" but you can't remember what changed
- **Sharing is painful**: Sending someone your workflow means a wall of text about which models/nodes to install
- **Environment sprawl**: Testing new nodes means risking your stable setup

ComfyDock solves this by treating your ComfyUI environments like code projects:

- ✅ **Multiple isolated environments** — test new nodes without breaking production
- ✅ **Git-based versioning** — commit changes, rollback when things break
- ✅ **One-command sharing** — export/import complete working environments
- ✅ **Smart model management** — content-addressable index, no duplicate storage
- ✅ **Standard tooling** — built on UV and pyproject.toml, works with Python ecosystem

## Installation

**Requirements:** Python 3.10+, Windows/Linux/macOS

Install with UV (recommended):
```bash
# Install UV first (Linux/macOS)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install UV first (Windows)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
```bash
# Install ComfyDock CLI
uv tool install comfydock-cli
```

Or with pip:
```bash
pip install comfydock-cli
```

> **Note**: The old Docker-based `comfydock` (v0.x) is being deprecated. This is a complete rewrite with a new approach. See [Migration](#migrating-from-old-comfydock) if you were using the old version.

## Quick Start

### Scenario 1: Basic Environment Setup

```bash
# Initialize workspace (one-time setup)
cfd init

# Create an environment
cfd create my-project --use

# Add some custom nodes
cfd node add comfyui-akatz-nodes
cfd node add https://github.com/ltdrdata/ComfyUI-Impact-Pack

# Run ComfyUI
cfd run
```

Your ComfyUI opens at `http://localhost:8188` with an isolated environment.

### Scenario 2: Version Control Workflow

```bash
# Save current state
cfd commit -m "Initial setup with Impact Pack"

# Add more nodes, test things out
cfd node add https://github.com/cubiq/ComfyUI_IPAdapter_plus
cfd commit -m "Added IPAdapter"

# Oops, something broke
cfd rollback v1  # Back to the first commit

# Or discard uncommitted changes
cfd rollback
```

### Scenario 3: Sharing Workflows (Export/Import)

```bash
# Package your environment
cfd export my-workflow-pack.tar.gz

# Share the .tar.gz file, then on another machine:
cfd import my-workflow-pack.tar.gz --name imported-workflow
# Downloads all nodes and models, ready to run
```

### Scenario 4: Team Collaboration (Git Remote)

```bash
# Add a git remote (GitHub, GitLab, etc)
cfd remote add origin https://github.com/username/my-comfyui-env.git

# Push your environment
cfd push

# On another machine, import from git:
cfd import https://github.com/username/my-comfyui-env.git --name team-env

# Pull updates
cfd pull
```

## How It Works

ComfyDock uses a **two-tier reproducibility model**:

### Local Tier: Git-Based Versioning
Each environment has a `.cec/` directory (a git repository) tracking:
- `pyproject.toml` — custom nodes, model references, Python dependencies
- `uv.lock` — locked Python dependency versions
- `workflows/` — tracked workflow files

When you run `cfd commit`, it snapshots this state. Rollback restores any previous commit.

### Global Tier: Export/Import Packages
Export bundles everything needed to recreate the environment:
- Node metadata (registry IDs, git URLs + commits)
- Model download sources (CivitAI URLs, HuggingFace, etc)
- Python dependency lockfile
- Development node source code

Import recreates the environment on any machine with compatible hardware.

### Under the Hood
- **UV for Python** — Fast dependency resolution and virtual environments
- **Standard pyproject.toml** — Each custom node gets its own dependency group to avoid conflicts
- **Content-addressable models** — Models identified by hash, allowing path-independent resolution
- **Registry integration** — Uses ComfyUI's official registry for node lookup

## Model Management

### The Problem
ComfyUI workflows reference models by path (e.g., `checkpoints/mymodel.safetensors`), but:
- Different machines have different folder structures
- Models get duplicated across projects
- Sharing workflows means "download this from CivitAI and put it here..."

### ComfyDock's Solution
A **workspace-wide model index** using content-addressable storage:
1. Point ComfyDock at your existing models directory (or use ComfyDock's)
2. It scans and indexes models by hash (Blake3 quick hash for speed)
3. When importing workflows, models are matched by hash, not path
4. Download sources (CivitAI URLs, etc) are tracked and can be auto-downloaded

### Basic Usage

```bash
# During init, you're prompted to set models directory
cfd init  # Interactive setup

# Or point to existing models
cfd model index dir ~/my-huge-model-library

# Sync the index
cfd model index sync

# Download models
cfd model download https://civitai.com/models/...

# Find models
cfd model index find "juggernaut"
```

Models are symlinked into each environment from the global directory, so no duplication.

## Comparison to Alternatives

| Tool | Approach | Pros | Cons |
|------|----------|------|------|
| **ComfyUI Manager** | In-UI node installer | Easy, visual | No versioning, no isolation, one global environment |
| **Manual Git Clones** | Clone nodes to `custom_nodes/` | Full control | Dependency conflicts, no reproducibility |
| **Docker** | Containerize everything | Isolation | Heavy, slow iteration, complex setup |
| **ComfyDock (old)** | Docker-based manager | GUI, isolation | Slow, Docker-only, not shareable |
| **ComfyDock (new)** | UV-based package manager | Fast, reproducible, shareable, standard tooling | CLI-focused, newer/less mature |

## Workspace Structure

```
~/comfydock/                    # Default workspace root
├── environments/               # Your environments
│   ├── production/
│   │   ├── ComfyUI/           # Actual ComfyUI installation
│   │   │   ├── custom_nodes/  # Installed nodes
│   │   │   ├── models/        # Symlinks to workspace models
│   │   │   └── .venv/         # Python virtual environment
│   │   └── .cec/              # Version control (git repo)
│   │       ├── workflows/     # Tracked workflows
│   │       ├── pyproject.toml # Dependencies & config
│   │       └── uv.lock        # Dependency lockfile
│   └── experimental/          # Another environment
├── models/                     # Shared models (optional)
└── .metadata/                  # Workspace config & model index DB
```

## Features

### Environment Management
```bash
cfd create <name>              # Create new environment
cfd list                       # List all environments
cfd use <name>                 # Set active environment
cfd delete <name>              # Delete environment
cfd status                     # Show environment state
```

### Custom Nodes
```bash
cfd node add <id>              # Add from registry
cfd node add <github-url>      # Add from GitHub
cfd node add <dir> --dev       # Track development node
cfd node remove <id>           # Remove node
cfd node list                  # List installed nodes
cfd node update <id>           # Update node
```

### Versioning
```bash
cfd commit -m "message"        # Save snapshot
cfd commit log                 # View history
cfd rollback <version>         # Restore previous state
cfd rollback                   # Discard uncommitted changes
```

### Sharing & Collaboration
```bash
cfd export <file.tar.gz>       # Export environment
cfd import <file.tar.gz>       # Import environment
cfd import <git-url>           # Import from git repo
cfd remote add origin <url>    # Add git remote
cfd push                       # Push to remote
cfd pull                       # Pull from remote
```

### Workflows
```bash
cfd workflow list              # List tracked workflows
cfd workflow resolve <name>    # Resolve missing dependencies
```

### Python Dependencies
```bash
cfd py add <package>           # Add Python package
cfd py remove <package>        # Remove Python package
cfd py list                    # List dependencies
```

## Documentation

Full documentation at **[www.comfydock.com](https://www.comfydock.com)**

## Migrating from Old ComfyDock

The old Docker-based ComfyDock (v0.x, `pip install comfydock`) is being deprecated. This is a complete rewrite with a different architecture. Both can coexist on the same system:

- **Old**: `comfydock` command, Docker containers, GUI-focused
- **New**: `cfd` command, UV-based, CLI-focused, shareable

There's no automatic migration path. We recommend starting fresh with the new version for new projects. See [migration guide](https://www.comfydock.com/migration) for details.

## Project Structure

ComfyDock is a Python monorepo:
- **comfydock-core** — Core library for environment/node/model management
- **comfydock-cli** — Command-line interface (`cfd` command)

For development setup, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Contributing

This project is currently maintained by a single developer. Contributions are welcome!

- **Issues**: Bug reports and feature requests
- **Discussions**: Questions, ideas, showcase your workflows
- **PRs**: Code contributions (see CONTRIBUTING.md)

## Community

- **Docs**: [www.comfydock.com](https://www.comfydock.com)
- **Issues**: [GitHub Issues](https://github.com/ComfyDock/comfydock/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ComfyDock/comfydock/discussions)

## License

ComfyDock is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

This means you can freely use, modify, and distribute ComfyDock, but any modifications or network services using ComfyDock must also be open-sourced under AGPL-3.0.

**For businesses** requiring a permissive license for commercial use, dual licensing is available. Please contact us to discuss your use case and licensing options.

See [LICENSE.txt](LICENSE.txt) for the full license text.
