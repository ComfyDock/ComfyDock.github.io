# ComfyDock Core

Core library for programmatic ComfyUI environment and package management. Build custom tools, GUIs, web interfaces, or CI/CD integrations on top of ComfyDock's architecture.

> **⚠️ MVP Status**: This library is under active development. APIs may change between versions. Pin your dependencies to specific versions in production.

## What is ComfyDock Core?

ComfyDock Core is the **reusable library** that powers the `cfd` CLI and can power your own tools. It provides:

- **Workspace & Environment Management** - Create and manage isolated ComfyUI installations
- **Custom Node Management** - Install, update, remove nodes with conflict detection
- **Workflow Tracking** - Track workflows and resolve missing dependencies
- **Model Management** - Content-addressable model index with automatic resolution
- **Version Control** - Git-based commit/rollback for environment snapshots
- **Export/Import** - Package and share complete working environments
- **Strategy Pattern** - Plug in your own UI logic via callbacks

This is a **library, not a CLI**. No `print()` or `input()` statements - all user interaction happens through callbacks you provide.

## Installation

Published separately to PyPI as `comfydock-core`:

```bash
# With pip
pip install comfydock-core

# With uv
uv add comfydock-core
```

## Quick Start

### Basic Workspace and Environment Operations

```python
from pathlib import Path
from comfydock_core.factories.workspace_factory import WorkspaceFactory

# Create a new workspace
workspace = WorkspaceFactory.create(Path.home() / "my-comfyui-workspace")

# Or find an existing workspace
workspace = WorkspaceFactory.find(Path.home() / "my-comfyui-workspace")

# Create an environment (downloads ComfyUI, sets up Python venv)
env = workspace.create_environment(
    name="production",
    python_version="3.11",
    comfyui_version="master",  # or specific commit hash
    torch_backend="auto"  # auto-detect GPU, or "cpu", "cu121", etc.
)

# List all environments
environments = workspace.list_environments()
for env in environments:
    print(f"Environment: {env.name} at {env.path}")

# Get a specific environment
env = workspace.get_environment("production")

# Set active environment (for CLI convenience, optional for library usage)
workspace.set_active_environment("production")
active = workspace.get_active_environment()

# Delete an environment
workspace.delete_environment("production")
```

**API Reference**: See `src/comfydock_core/core/workspace.py` for full `Workspace` API and `src/comfydock_core/factories/workspace_factory.py` for factory methods.

### Node Management

```python
# Add a node from ComfyUI registry
result = env.add_node("comfyui-akatz-nodes")

# Add a node from GitHub URL
result = env.add_node(
    "https://github.com/ltdrdata/ComfyUI-Impact-Pack",
    version="v5.0"  # optional: specify branch, tag, or commit
)

# Track a development node (your own node under development)
result = env.add_node(
    "/path/to/my-custom-node",
    dev=True  # marks as development node, preserved on removal
)

# List installed nodes
nodes = env.list_nodes()
for node in nodes:
    print(f"{node.name}: {node.source} ({node.version})")

# Remove a node
result = env.remove_node("comfyui-manager")

# Update a node to latest version
update_result = env.update_node("comfyui-impact-pack")
if update_result.updated:
    print(f"Updated from {update_result.old_version} to {update_result.new_version}")
```

**Node Sources**: Nodes can come from:
- `registry` - ComfyUI official registry
- `git` - GitHub/GitLab repositories
- `development` - Local nodes under development

**API Reference**: See `src/comfydock_core/core/environment.py` for node methods and `src/comfydock_core/managers/node_manager.py` for implementation details.

### Workflow Tracking and Resolution

```python
from pathlib import Path

# Track a workflow (registers it for monitoring)
env.track_workflow(Path("my-workflow.json"))

# List tracked workflows
workflows = env.list_workflows()

# Resolve workflow dependencies (finds missing nodes and models)
result = env.resolve_workflow(
    "my-workflow.json",
    node_strategy=my_node_strategy,  # custom strategy for ambiguous nodes
    model_strategy=my_model_strategy,  # custom strategy for missing models
    install_nodes=True  # automatically install missing nodes
)

# Check resolution results
if result.all_nodes_resolved:
    print("All nodes available")
else:
    print(f"Missing nodes: {result.unresolved_nodes}")

if result.all_models_found:
    print("All models found")
else:
    print(f"Missing models: {result.missing_models}")

# Untrack a workflow
env.untrack_workflow("my-workflow.json")
```

**Workflow Resolution Process**:
1. Parse workflow JSON for node types and model references
2. Match node types to installed nodes or registry entries
3. Match model references to indexed models by hash
4. Return detailed status with resolution results

**API Reference**: See `src/comfydock_core/managers/workflow_manager.py` for workflow operations and `src/comfydock_core/models/workflow.py` for data structures.

### Model Management

```python
# Set global models directory (workspace-wide)
workspace.set_models_directory(Path.home() / "my-models")

# Sync model index (scan directory and update database)
workspace.sync_model_index()

# Find models by hash, filename, or path
models = workspace.find_model("juggernaut")
for model in models:
    print(f"{model.filename}: {model.hash_quick}")

# Download a model from URL
download_result = workspace.download_model(
    url="https://civitai.com/api/download/models/12345",
    category="checkpoints",  # auto-path to checkpoints/
    filename="my-model.safetensors"  # optional override
)

# Add download source to existing model (for sharing)
workspace.add_model_source(
    model_hash="abc123...",
    url="https://civitai.com/models/..."
)

# Models are symlinked into environments automatically
# No duplication - all environments share the workspace model index
```

**Model Index**: Uses Blake3 quick hash (first/middle/last 15MB) for fast identification and full SHA256 hash for verification during export/import.

**API Reference**: See `src/comfydock_core/core/workspace.py` for model methods and `src/comfydock_core/repositories/model_repository.py` for database operations.

### Version Control (Commit/Rollback)

```python
# Commit current state (creates git snapshot in .cec/)
commit_result = env.commit(
    message="Added Impact Pack and configured workflows"
)

# View commit history
commits = env.get_commit_history()
for commit in commits:
    print(f"v{commit.version}: {commit.message} ({commit.timestamp})")

# Rollback to previous version
env.rollback(
    target="v2",  # version identifier, or None to discard uncommitted changes
    force=False  # if True, discard uncommitted changes without error
)

# Check for uncommitted changes
status = env.get_status()
if status.has_uncommitted_changes:
    print("Uncommitted changes detected")
```

**What Gets Committed**:
- `pyproject.toml` - Node metadata, model references, Python dependencies
- `uv.lock` - Locked Python dependency versions
- `.cec/workflows/` - Tracked workflow files

**What Doesn't Get Committed**:
- Node source code (tracked in metadata, downloaded on demand)
- Model files (too large, referenced by hash)
- `.venv/` - Python virtual environment (recreated from lock)

**API Reference**: See `src/comfydock_core/core/environment.py` for version control methods and `src/comfydock_core/managers/git_manager.py` for git operations.

### Export and Import

```python
from comfydock_core.models.protocols import ExportCallbacks, ImportCallbacks

# Export environment to tarball
class MyExportCallbacks(ExportCallbacks):
    def on_progress(self, step: str, current: int, total: int):
        print(f"{step}: {current}/{total}")

workspace.export_environment(
    env_name="production",
    output_path="production-env.tar.gz",
    callbacks=MyExportCallbacks()
)

# Import environment from tarball
class MyImportCallbacks(ImportCallbacks):
    def on_node_download_start(self, node_name: str):
        print(f"Downloading node: {node_name}")

    def on_model_download_progress(self, filename: str, progress: float):
        print(f"Model {filename}: {progress*100:.1f}%")

workspace.import_environment(
    source="production-env.tar.gz",
    name="imported-production",
    callbacks=MyImportCallbacks(),
    torch_backend="auto"
)

# Import from git repository
workspace.import_environment(
    source="https://github.com/user/my-comfyui-env.git",
    name="team-env",
    branch="main",  # optional: branch, tag, or commit
    callbacks=MyImportCallbacks()
)
```

**Export Contents**:
- Environment configuration (pyproject.toml, uv.lock)
- Tracked workflows
- Development node source code
- Node metadata (registry IDs, git URLs + commits)
- Model download sources (CivitAI/HuggingFace URLs)

**Import Process**:
1. Extract/clone environment configuration
2. Download missing custom nodes
3. Download missing models (if sources available)
4. Create Python virtual environment
5. Install dependencies from lock file

**API Reference**: See `src/comfydock_core/models/protocols.py` for callback protocols and `src/comfydock_core/managers/export_import_manager.py` for implementation.

### Git Remote Operations

```python
# Add a git remote (for environment sharing via git)
env.add_remote(name="origin", url="https://github.com/user/my-env.git")

# List remotes
remotes = env.list_remotes()

# Push to remote
env.push_to_remote(remote="origin", force=False)

# Pull from remote
env.pull_from_remote(remote="origin", force=False)

# Remove a remote
env.remove_remote(name="origin")
```

**Remote Collaboration**: Each environment's `.cec/` directory is a git repository. You can push to GitHub/GitLab and others can import from the URL.

**API Reference**: See `src/comfydock_core/core/environment.py` for remote methods.

### Python Dependency Management

```python
# Add Python packages to environment
env.add_python_dependencies(["opencv-python>=4.5.0", "pillow"])

# Add from requirements.txt
env.add_python_dependencies_from_file(Path("requirements.txt"))

# Remove Python packages
env.remove_python_dependencies(["opencv-python"])

# List dependencies
deps = env.list_python_dependencies()
```

**Dependency Isolation**: Each custom node gets its own dependency group in `pyproject.toml` to isolate conflicts.

**API Reference**: See `src/comfydock_core/core/environment.py` for Python dependency methods.

## Strategy Pattern (Custom UI Integration)

ComfyDock Core uses the **strategy pattern** to allow custom frontends to provide their own UI logic. No hardcoded prompts or dialogs.

### Node Resolution Strategy

When adding nodes with ambiguous names, provide a strategy to resolve:

```python
from comfydock_core.models.protocols import NodeResolutionStrategy
from comfydock_core.models.shared import NodeInfo

class CLINodeStrategy(NodeResolutionStrategy):
    """Interactive CLI node resolution."""

    def resolve_ambiguous(
        self,
        node_identifier: str,
        candidates: list[NodeInfo]
    ) -> NodeInfo:
        """User picks from multiple matches."""
        print(f"Multiple nodes match '{node_identifier}':")
        for i, node in enumerate(candidates, 1):
            print(f"  {i}. {node.name} ({node.source})")

        choice = int(input("Select: ")) - 1
        return candidates[choice]

    def resolve_optional(
        self,
        node_identifier: str,
        is_required: bool
    ) -> bool:
        """User decides whether to install optional node."""
        if is_required:
            return True

        response = input(f"Install optional node '{node_identifier}'? (y/N): ")
        return response.lower() == 'y'

# Use your strategy
env.add_node("comfyui", strategy=CLINodeStrategy())
```

### Model Resolution Strategy

When workflows reference missing models:

```python
from comfydock_core.models.protocols import ModelResolutionStrategy
from comfydock_core.models.shared import ModelDetails

class CLIModelStrategy(ModelResolutionStrategy):
    """Interactive CLI model resolution."""

    def resolve_missing_model(
        self,
        model_reference: str,
        candidates: list[ModelDetails]
    ) -> ModelDetails | None:
        """User picks from search results or skips."""
        if not candidates:
            print(f"No models found for '{model_reference}'")
            return None

        print(f"Found models for '{model_reference}':")
        for i, model in enumerate(candidates, 1):
            print(f"  {i}. {model.filename} ({model.size_mb:.1f} MB)")
        print(f"  {len(candidates)+1}. Skip")

        choice = int(input("Select: "))
        if choice == len(candidates) + 1:
            return None

        return candidates[choice - 1]

# Use your strategy
env.resolve_workflow(
    "my-workflow.json",
    model_strategy=CLIModelStrategy()
)
```

### Confirmation Strategy

For destructive operations (node removal, rollback):

```python
from comfydock_core.strategies.confirmation import ConfirmationStrategy

class CLIConfirmationStrategy(ConfirmationStrategy):
    """Interactive CLI confirmations."""

    def confirm_node_removal(self, node_name: str, is_dev: bool) -> bool:
        """User confirms node removal."""
        msg = f"Remove node '{node_name}'"
        if is_dev:
            msg += " (development node will be disabled, not deleted)"
        response = input(f"{msg}? (y/N): ")
        return response.lower() == 'y'

    def confirm_rollback(self, target_version: str, has_uncommitted: bool) -> bool:
        """User confirms rollback."""
        msg = f"Rollback to {target_version}"
        if has_uncommitted:
            msg += " (uncommitted changes will be lost)"
        response = input(f"{msg}? (y/N): ")
        return response.lower() == 'y'
```

### Auto Strategies (Non-Interactive)

For automated/CI environments, use auto-confirm strategies:

```python
from comfydock_core.strategies.auto import (
    AutoConfirmStrategy,
    AutoNodeStrategy,
    AutoModelStrategy
)

# Auto-confirm all operations
env.remove_node("some-node", strategy=AutoConfirmStrategy())

# Auto-select first match
env.add_node("ambiguous", strategy=AutoNodeStrategy())

# Auto-skip missing models
result = env.resolve_workflow(
    "workflow.json",
    model_strategy=AutoModelStrategy()
)
```

**Available Strategies**:
- `NodeResolutionStrategy` - Handle ambiguous node names
- `ModelResolutionStrategy` - Handle missing model resolution
- `ConfirmationStrategy` - Handle destructive operations
- `RollbackStrategy` - Handle rollback confirmations
- `ExportCallbacks` - Progress updates during export
- `ImportCallbacks` - Progress updates during import

**API Reference**: See `src/comfydock_core/models/protocols.py` for all strategy protocols and `src/comfydock_core/strategies/` for built-in implementations.

## Architecture Overview

ComfyDock Core uses a **layered architecture** separating concerns:

```
┌─────────────────────────────────────────────────────────────┐
│  API Layer (Workspace, Environment)                         │
│  - High-level operations                                    │
│  - Public API surface                                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│  Management Layer (Managers)                                │
│  - NodeManager: Node installation/removal                   │
│  - WorkflowManager: Workflow tracking/resolution            │
│  - ModelSymlinkManager: Model symlinking                    │
│  - GitManager: Git operations                               │
│  - PyprojectManager: pyproject.toml manipulation            │
│  - UVProjectManager: UV command execution                   │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│  Service Layer (Services)                                   │
│  - NodeLookupService: Find nodes across sources             │
│  - ModelDownloader: Download models from URLs               │
│  - RegistryDataManager: ComfyUI registry cache              │
│  - ImportAnalyzer: Preview imports                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│  Repository Layer (Data Access)                             │
│  - ModelRepository: SQLite model index                      │
│  - WorkflowRepository: Workflow caching                     │
│  - NodeMappingsRepository: Node-to-package mappings         │
│  - WorkspaceConfigRepository: Workspace configuration       │
└─────────────────────────────────────────────────────────────┘
```

### Component Organization

**Core (`core/`)**
- `workspace.py` - Multi-environment coordinator
- `environment.py` - Single environment abstraction

**Managers (`managers/`)** - Orchestrate operations, maintain state
- Depend on services and repositories
- Handle complex workflows (install node → update pyproject → sync venv)

**Services (`services/`)** - Stateless business logic
- Pure functions or stateless classes
- Reusable across different managers

**Repositories (`repositories/`)** - Data persistence
- Database access (SQLite)
- File I/O (JSON, TOML)
- Caching

**Analyzers (`analyzers/`)** - Parse and extract information
- Workflow dependency parsing
- Custom node scanning
- Status analysis

**Resolvers (`resolvers/`)** - Determine actions
- Map workflow nodes to packages
- Find model download sources

**Models (`models/`)** - Data structures
- Type definitions
- Dataclasses
- Protocols (strategy interfaces)

**Factories (`factories/`)** - Object construction
- Handle complex initialization
- Dependency injection

**Strategies (`strategies/`)** - Pluggable behavior
- Auto-confirm strategies
- Interactive strategies (in frontend)

## Use Cases

### Use Case 1: Building a GUI

```python
from PyQt6.QtWidgets import QProgressDialog
from comfydock_core.models.protocols import ImportCallbacks

class QtImportCallbacks(ImportCallbacks):
    """Qt-based progress UI for imports."""

    def __init__(self, parent):
        self.dialog = QProgressDialog(
            "Importing environment...",
            "Cancel",
            0, 100,
            parent
        )
        self.dialog.setWindowModality(Qt.WindowModal)

    def on_node_download_start(self, node_name: str):
        self.dialog.setLabelText(f"Downloading node: {node_name}")

    def on_model_download_progress(self, filename: str, progress: float):
        self.dialog.setValue(int(progress * 100))
        self.dialog.setLabelText(f"Downloading model: {filename}")

    def on_python_sync_start(self):
        self.dialog.setLabelText("Installing Python dependencies...")

# Use in your Qt application
workspace.import_environment(
    "shared-env.tar.gz",
    callbacks=QtImportCallbacks(self.mainwindow)
)
```

### Use Case 2: CI/CD Pipeline

```python
"""Validate workflow compatibility in CI pipeline."""
import sys
from comfydock_core.factories.workspace_factory import WorkspaceFactory
from comfydock_core.strategies.auto import AutoModelStrategy, AutoNodeStrategy

# Create test workspace
workspace = WorkspaceFactory.create("/tmp/ci-test-workspace")
env = workspace.create_environment("ci-test")

# Import workflow to test
env.track_workflow("workflow-to-test.json")

# Resolve with auto strategies (non-interactive)
result = env.resolve_workflow(
    "workflow-to-test.json",
    node_strategy=AutoNodeStrategy(),
    model_strategy=AutoModelStrategy(),
    install_nodes=True
)

# Check results
if not result.all_nodes_resolved:
    print(f"ERROR: Missing nodes: {result.unresolved_nodes}")
    sys.exit(1)

if not result.all_models_found:
    print(f"WARNING: Missing models: {result.missing_models}")
    # Could fail here or continue depending on requirements

print("✓ Workflow validation passed")
```

### Use Case 3: Batch Environment Creation

```python
"""Create multiple environments from templates."""
from pathlib import Path

workspace = WorkspaceFactory.find()

# Define environment templates
templates = [
    {"name": "video", "nodes": ["comfyui-animatediff", "comfyui-video-helper"]},
    {"name": "upscale", "nodes": ["comfyui-ultimate-upscale"]},
    {"name": "inpaint", "nodes": ["comfyui-inpaint-nodes"]},
]

for template in templates:
    print(f"Creating {template['name']} environment...")

    env = workspace.create_environment(
        name=template['name'],
        python_version="3.11"
    )

    # Add nodes
    for node_id in template['nodes']:
        env.add_node(node_id)

    # Commit initial setup
    env.commit(f"Initial {template['name']} environment setup")

    print(f"✓ {template['name']} environment ready")
```

### Use Case 4: Environment Replication Tool

```python
"""Clone production environment to staging."""
from pathlib import Path
import tempfile

workspace = WorkspaceFactory.find()

# Export production
with tempfile.TemporaryDirectory() as tmpdir:
    export_path = Path(tmpdir) / "production-snapshot.tar.gz"
    workspace.export_environment("production", export_path)

    # Import as staging
    workspace.import_environment(
        export_path,
        name="staging",
        torch_backend="auto"
    )

print("✓ Production cloned to staging")
```

## Error Handling

ComfyDock Core uses a custom exception hierarchy for precise error handling:

```python
from comfydock_core.models.exceptions import (
    ComfyDockError,         # Base exception
    CDWorkspaceError,       # Workspace-related errors
    CDEnvironmentError,     # Environment-related errors
    CDNodeConflictError,    # Node installation conflicts
    CDNodeNotFoundError,    # Node not found
    UVCommandError,         # UV command failures
)

try:
    env = workspace.create_environment("test")
except CDEnvironmentError as e:
    print(f"Environment error: {e}")
    # Handle environment-specific error
except CDWorkspaceError as e:
    print(f"Workspace error: {e}")
    # Handle workspace-specific error
except ComfyDockError as e:
    print(f"ComfyDock error: {e}")
    # Handle any ComfyDock error
```

**Exception Hierarchy**:
```
ComfyDockError
├── CDWorkspaceError
│   ├── CDWorkspaceNotFoundError
│   └── CDWorkspaceExistsError
├── CDEnvironmentError
│   ├── CDEnvironmentNotFoundError
│   ├── CDEnvironmentExistsError
│   └── CDNodeConflictError
├── CDNodeError
│   ├── CDNodeNotFoundError
│   └── CDNodeInstallError
└── UVCommandError
```

**API Reference**: See `src/comfydock_core/models/exceptions.py` for all exception types.

## Data Structures

Key data structures used throughout the API:

### NodeInfo
```python
from comfydock_core.models.shared import NodeInfo

# Returned by list_nodes(), node lookup, etc.
node = NodeInfo(
    name="comfyui-manager",
    identifier="comfyui-manager",
    source="registry",  # or "git", "development"
    version="1.0.0",
    url="https://github.com/...",
    installed=True
)
```

### EnvironmentStatus
```python
from comfydock_core.models.environment import EnvironmentStatus

# Returned by env.get_status()
status = EnvironmentStatus(
    has_uncommitted_changes=True,
    python_version="3.11.5",
    comfyui_version="abc123",
    installed_nodes=["comfyui-manager"],
    tracked_workflows=["workflow.json"],
    sync_issues=[]  # list of issues if any
)
```

### ResolutionResult
```python
from comfydock_core.models.workflow import ResolutionResult

# Returned by env.resolve_workflow()
result = ResolutionResult(
    all_nodes_resolved=True,
    all_models_found=False,
    unresolved_nodes=[],
    missing_models=["model.safetensors"],
    resolved_nodes=["node1", "node2"],
    found_models=["other-model.safetensors"]
)
```

**API Reference**: See `src/comfydock_core/models/` for all data structures.

## Design Principles

ComfyDock Core follows these principles for library design:

1. **No UI Coupling**: Zero `print()` or `input()` statements. All user interaction through callbacks.

2. **Stateless Services**: Services are pure functions or stateless classes. State lives in Managers and Core objects.

3. **Strategy Pattern**: Pluggable behavior via protocol interfaces. Frontends provide their own strategies.

4. **Dependency Injection**: Factories handle complex object construction. No singletons.

5. **Layered Architecture**: Clear separation between API, Management, Service, and Repository layers.

6. **Type Safety**: Full type hints. Use protocols for interfaces, dataclasses for data.

7. **Error Transparency**: Custom exception hierarchy. No silent failures.

8. **Content-Addressable**: Models identified by hash, not path. Enables flexible remapping.

## Development

### Running Tests

```bash
# All tests
uv run pytest tests/

# Integration tests only
uv run pytest tests/integration/

# Unit tests only
uv run pytest tests/unit/

# Specific test file
uv run pytest tests/integration/test_environment_basic.py

# With coverage
uv run pytest --cov=comfydock_core tests/

# Verbose output
uv run pytest tests/ -v
```

### Project Structure

```
comfydock-core/
├── src/comfydock_core/
│   ├── core/              # Workspace & Environment
│   ├── managers/          # Orchestration layer
│   ├── services/          # Business logic
│   ├── repositories/      # Data access
│   ├── analyzers/         # Parsing & extraction
│   ├── resolvers/         # Action determination
│   ├── models/            # Data structures
│   ├── factories/         # Object construction
│   ├── strategies/        # Built-in strategies
│   ├── clients/           # External API clients
│   ├── utils/             # Utilities
│   ├── caching/           # Caching layer
│   ├── configs/           # Static configuration
│   ├── infrastructure/    # SQLite, etc.
│   ├── validation/        # Testing utilities
│   └── logging/           # Logging setup
├── tests/
│   ├── integration/       # Integration tests
│   ├── unit/             # Unit tests
│   └── conftest.py       # Pytest fixtures
├── docs/
│   ├── codebase-map.md   # Architecture details
│   ├── prd.md            # Product requirements
│   └── layer-hierarchy.md # Layer dependencies
└── pyproject.toml        # Package metadata
```

### Contributing

This is an MVP project maintained by a single developer. APIs may change between versions.

- **Issues**: [GitHub Issues](https://github.com/ComfyDock/comfydock/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ComfyDock/comfydock/discussions)
- **Pull Requests**: Welcome, but discuss major changes first

## API Documentation

For detailed API documentation:
- **Full API Docs**: [www.comfydock.com/api](https://www.comfydock.com/api) (coming soon)
- **Architecture Details**: See `docs/codebase-map.md` in this repository
- **Source Code**: All source is in `src/comfydock_core/` with inline documentation

## Comparison to CLI

The CLI (`comfydock-cli` package) is built on top of this core library:

| Core Library | CLI Package |
|--------------|-------------|
| Programmatic Python API | Command-line interface |
| Strategy callbacks for UI | Interactive terminal UI |
| No user interaction | Prompts, progress bars, formatting |
| `workspace.create_environment()` | `cfd create <name>` |
| `env.add_node()` | `cfd node add <id>` |
| Returns data structures | Prints formatted output |

**Use the core library when:**
- Building a custom GUI (Qt, Electron, web UI)
- CI/CD automation
- Scripting bulk operations
- Integrating into larger tools

**Use the CLI when:**
- Interactive terminal usage
- Quick manual operations
- You want the pre-built UX

## License

ComfyDock Core is **dual-licensed**:

- **AGPL-3.0** for open-source use (free forever)
- **Commercial licenses** available for businesses requiring proprietary use

**For open-source projects:** Use freely under AGPL-3.0. Modifications must be open-sourced.

**For businesses:** Contact us for commercial licensing if you need to:
- Build proprietary applications without open-sourcing modifications
- Offer SaaS without disclosing source code
- Integrate into closed-source products

See [LICENSE.txt](../../LICENSE.txt) for the full AGPL-3.0 license text.

## Version & Stability

**Current Version**: 1.0.0

**Stability**: MVP - APIs may change between versions. Pin your dependencies:

```toml
# pyproject.toml
dependencies = [
    "comfydock-core>=1.0.0,<1.1.0"  # Pin to minor version
]
```

**Semantic Versioning**:
- Major (X.0.0): Breaking API changes
- Minor (0.X.0): New features, backward compatible
- Patch (0.0.X): Bug fixes, backward compatible

We will stabilize APIs as we approach 2.0.0 release.
