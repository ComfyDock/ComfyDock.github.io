# ComfyDock Architecture v2.0

## Core Philosophy
pyproject.toml is the environment. Every operation directly modifies this file. Git tracks changes. UV applies them. No intermediate staging, no duplicate metadata, no complex state management.

### Design Principles
1. **Fail Fast, Fail Clear** - Validate operations before modifying pyproject.toml
2. **Cross-Platform First** - Use pathlib.Path everywhere, UV handles platform differences  
3. **Developer-Friendly Defaults** - Sensible defaults with escape hatches for power users
4. **Incremental Sync** - Only touch what changed, preserve working state
5. **Content-Addressed Assets** - Models and workflows identified by hash, not names

## Workspace Directory Structure
```
~/.comfydock_workspace/             # Workspace root
├── .metadata/
│   ├── workspace.json              # Active environment + workspace config
│   ├── api_cache.db                # SQLite database for caching API requests/responses
│   ├── node_index.db               # SQLite database for looking up custom nodes saved locally
│   └── model_index.db              # SQLite database for model hashes
├── comfydock_cache/                # Shared cache
│   ├── custom_nodes/               # Downloaded node cache
│   │    └── store/                 # Downloaded node cache (actual hash-named node data)
│   └── models/                     # Default model storage location (if none configured)
├── environments/
│   └── my-env/                    # Individual environment
│       ├── .cec/                  # Config & tracking (git repo)
│       │   ├── .git/              # Tracks pyproject.toml, uv.lock, workflows
│       │   ├── workflows/         # Tracked workflow files
│       │   ├── .comfydockignore   # Workflow ignore patterns
│       │   ├── uv.lock            # Resolved python deps
│       │   └── pyproject.toml    # THE source of truth
│       ├── .venv/                 # Python virtual environment
│       └── ComfyUI/               # ComfyUI installation
│           ├── custom_nodes/      # Where nodes get installed
│           ├── models/            # Model files (or symlinks)
│           └── user/workflows/    # Active workflow directory
├── logs/                          # Environment-specific logs
│   └── my-env.log                 
├── uv_cache/                      # Shared UV cache
└── uv/python/                     # UV-managed Python versions
```

## Component Architecture

### Core Components

#### 1. WorkspaceManager
**Purpose:** Manage multiple environments and workspace-level resources

**Responsibilities:**
- Create/delete environments
- Track active environment
- Initialize workspace
- Manage workspace configuration

**Interface:**
```python
create(path: Path) -> WorkspaceManager
create_environment(name: str, python: str, comfyui: str) -> Environment
delete_environment(name: str) -> None
get_environment(name: str) -> Environment
list_environments() -> List[Environment]
set_active_environment(name: str) -> None
get_active_environment() -> Optional[Environment]
get_config() -> WorkspaceConfig
update_config(config: dict) -> None
```

#### 2. Environment
**Purpose:** Complete ownership of a single environment

**Responsibilities:**
- Directly modify .cec/pyproject.toml
- Run git commands on .cec/
- Delegate to UV for package operations
- Coordinate with other managers

**Interface:**
```python
# Core operations
create(name: str, path: Path, workspace_path: Path) -> Environment
add_node(identifier: str) -> NodeInfo
remove_node(name: str) -> None
status() -> EnvironmentStatus
sync(dry_run: bool = False) -> None
commit(message: str) -> None
rollback(commit: str = None) -> None
run(args: list) -> subprocess.Result

# Extended operations
validate() -> ValidationResult
diff() -> EnvironmentDiff
update_comfyui(version: str = None) -> None
repair() -> RepairResult
get_pyproject() -> PyprojectManager
```

### Service Components

#### 3. NodeRegistry
**Purpose:** Stateless service for finding and managing custom nodes

**Responsibilities:**
- Search ComfyUI Registry (primary source)
- Parse git URLs (secondary source)
- Cache node downloads
- Scan for requirements

**Interface:**
```python
get_node(identifier: str, is_local: bool = False) -> NodeInfo
download_node(node_info: NodeInfo, target_path: Path) -> None
get_node_requirements(node_info: NodeInfo) -> List[str]
search_nodes(query: str, limit: int = 10) -> List[NodeInfo]
validate_node(identifier: str) -> ValidationResult
```

#### 4. ModelIndex
**Purpose:** Content-addressed model management via hashing

**Responsibilities:**
- Scan and hash model files
- Maintain SQLite index of model locations
- Resolve models by hash or name
- Generate model hints for workflows

**Interface:**
```python
# Discovery and indexing
scan_directory(path: Path, recursive: bool = True) -> List[ModelInfo]
scan_standard_locations() -> List[ModelInfo]
register_model(path: Path, metadata: dict = None) -> ModelInfo
update_index() -> None

# Resolution and lookup
resolve_by_hash(hash: str) -> Optional[ModelInfo]
resolve_by_name(name: str) -> List[ModelInfo]
search_models(query: str) -> List[ModelInfo]
get_model_info(identifier: str) -> Optional[ModelInfo]

# Workflow integration
extract_workflow_models(workflow: dict) -> List[ModelReference]
inject_model_hashes(workflow: dict) -> dict
resolve_workflow_models(workflow: dict) -> ResolutionResult
```

#### 5. WorkflowManager
**Purpose:** Manage workflow lifecycle and synchronization

**Responsibilities:**
- Track/untrack workflows
- Sync between ComfyUI and .cec/workflows
- Analyze workflow dependencies
- Import/export with dependencies

**Interface:**
```python
# Discovery and status
scan_workflows(env: Environment) -> WorkflowStatus
get_workflow_state(name: str) -> WorkflowState  # tracked/watched/ignored

# Tracking management
track_workflow(env: Environment, name: str) -> None
untrack_workflow(env: Environment, name: str) -> None
track_all(env: Environment, pattern: str = None) -> int

# Synchronization
sync_workflows(env: Environment) -> SyncResult
resolve_conflicts(workflow: str, strategy: str) -> None

# Import/Export
export_workflow(env: Environment, name: str, with_deps: bool) -> Path
import_workflow(env: Environment, bundle: Path) -> ImportResult
analyze_dependencies(workflow: dict) -> WorkflowDependencies
```

### Utility Components

#### 6. PyprojectManager (existing)
**Purpose:** TOML file operations - keep as-is

#### 7. UVInterface (existing)  
**Purpose:** UV command wrapper - keep as-is

#### 8. ConfigManager (new)
**Purpose:** Manage workspace and user configuration

**Interface:**
```python
get_workspace_config() -> dict
set_workspace_config(key: str, value: Any) -> None
get_user_config() -> dict
set_user_config(key: str, value: Any) -> None
get_api_keys() -> dict
set_api_key(service: str, key: str) -> None
```

#### 9. BundleManager (new)
**Purpose:** Handle import/export of environments and workflows

**Interface:**
```python
create_env_bundle(env: Environment) -> Path
create_workflow_bundle(workflow: Path, deps: dict) -> Path
extract_bundle(bundle: Path) -> BundleInfo
validate_bundle(bundle: Path) -> ValidationResult
```

## Data Models

### pyproject.toml Structure
```toml
[project]
name = "my-env"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = []  # From ComfyUI requirements

[dependency-groups]
# Node-specific dependencies
comfyui-manager = ["gitpython>=3.1", "rich>=12.0"]
efficiency-nodes = ["opencv-python>=4.5"]

[tool.uv]
constraint-dependencies = ["torch==2.4.1"]
[[tool.uv.index]]
name = "pytorch"
url = "https://download.pytorch.org/whl/cu121"
explicit = true

[tool.uv.sources]
torch = { index = "pytorch" }
torchvision = { index = "pytorch" }

[tool.comfydock]
version = "1.0.0"
comfyui_version = "v0.31.0"
python_version = "3.12"

# Custom nodes
[tool.comfydock.nodes.comfyui-manager]
name = "ComfyUI-Manager"
registry_id = "comfyui-manager"
version = "3.0.1"
repository = "https://github.com/ltdrdata/ComfyUI-Manager"
source = "registry"

# Models used in workspace
[tool.comfydock.models.sd15_base]
name = "SD 1.5 Base"
hash = "blake3:7c4971d1f05847a1b44b61f2f35e4c698a565f83b372cf891a92a44f65f47961"
size = 4265146304
sources = [
    { type = "huggingface", repo = "runwayml/stable-diffusion-v1-5", file = "v1-5-pruned.safetensors" },
    { type = "civitai", model_id = "6431", version_id = "7425" },
    { type = "url", url = "https://example.com/models/sd15.safetensors" }
]
local_path = "models/checkpoints/sd15_base.safetensors"  # Optional

# Tracked workflows
[tool.comfydock.workflows.tracked.my_workflow]
file = "workflows/my_workflow.json"
version = "1.0.0"
description = "My production workflow"
requires = {
    nodes = ["comfyui-manager", "efficiency-nodes"],
    models = ["sd15_base", "vae_ft_mse"],
    python = ["opencv-python>=4.5"]
}
```

### Model Index Schema (SQLite)
Flexible for adding hash types later (MD5, SHA-1, etc.)
```sql
CREATE TABLE models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    size INTEGER,
    local_path TEXT,
    original_name TEXT,
    last_seen TIMESTAMP,
    metadata JSON
);

CREATE TABLE model_hashes (
    model_id INTEGER,
    hash_type TEXT,  -- 'blake3' or 'sha256'
    hash_value TEXT,
    PRIMARY KEY (hash_type, hash_value),
    FOREIGN KEY (model_id) REFERENCES models(id)
);

CREATE INDEX idx_models_name ON models(name);
CREATE INDEX idx_models_path ON models(local_path);
CREATE INDEX idx_hash_value ON model_hashes(hash_value);
```
Single query can find model by any hash: 
```sql
SELECT m.* FROM models m JOIN model_hashes h ON m.id = h.model_id WHERE h.hash_value = ?
```

## Critical Operations

### Environment Sync Flow
```
1. User modifies pyproject.toml (add/remove nodes)
2. User runs 'comfydock sync'
3. System validates changes (resolution test)
4. Git commits pyproject.toml
5. UV syncs Python packages
6. NodeRegistry downloads/removes custom nodes
7. WorkflowManager updates workflow dependencies
8. System reports success/failure
```

### Model Resolution Flow
```
1. User imports workflow
2. WorkflowManager extracts model references
3. ModelIndex attempts hash resolution
4. For unresolved models:
   - Check filename hints
   - Prompt user for location
   - Offer to skip
5. Update workflow with resolved paths
6. Copy to ComfyUI/user/workflows/
```

### Workflow Tracking Flow
```
1. User runs 'workflow track <name>'
2. Copy from ComfyUI/user/workflows/ to .cec/workflows/
3. Parse workflow JSON for dependencies
4. Update pyproject.toml [tool.comfydock.workflows.tracked]
5. Git add and commit
6. Set up file watcher for sync
```

## Error Handling Strategy

### Validation Layers
1. **Pre-validation** - Check before any modifications
2. **Resolution testing** - Dry-run dependency resolution
3. **Atomic operations** - Complete or rollback entirely
4. **Clear messaging** - Actionable error messages

### Recovery Mechanisms
- Git reset for configuration rollback
- UV sync --frozen for package recovery
- Model index rebuild for corrupt database
- Workflow sync conflict resolution

## CLI Command Mapping

### Workspace Level
- `init` → WorkspaceManager.create()
- `config` → ConfigManager.interactive_setup()
- `list` → WorkspaceManager.list_environments()

### Environment Management
- `create` → WorkspaceManager.create_environment()
- `delete` → WorkspaceManager.delete_environment()
- `use` → WorkspaceManager.set_active_environment()
- `import` → BundleManager.import_environment()
- `export` → BundleManager.export_environment()

### Environment Operations
- `run` → Environment.run()
- `status` → Environment.status() + WorkflowManager.scan_workflows()
- `sync` → Environment.sync()
- `commit` → Environment.commit()

### Node Management
- `node find` → NodeRegistry.search_nodes()
- `node add` → Environment.add_node()
- `node remove` → Environment.remove_node()
- `node list` → Environment.list_nodes()

### Model Management
- `model scan` → ModelIndex.scan_directory()
- `model find` → ModelIndex.search_models()
- `model add` → ModelIndex.register_model() + Environment.add_model()
- `model remove` → Environment.remove_model()
- `model list` → Environment.list_models()

### Workflow Management
- `workflow status` → WorkflowManager.scan_workflows()
- `workflow track` → WorkflowManager.track_workflow()
- `workflow untrack` → WorkflowManager.untrack_workflow()
- `workflow sync` → WorkflowManager.sync_workflows()
- `workflow import` → WorkflowManager.import_workflow()
- `workflow export` → WorkflowManager.export_workflow()

## Implementation Priority

### Phase 1: Core (Current)
✅ WorkspaceManager
✅ Environment base
✅ NodeRegistry
✅ PyprojectManager
✅ UVInterface

### Phase 2: Model Management
- [ ] ModelIndex with SQLite
- [ ] Model scanning and hashing
- [ ] Model resolution in workflows
- [ ] Model commands in CLI

### Phase 3: Workflow Management
- [ ] WorkflowManager
- [ ] Workflow tracking/sync
- [ ] Dependency analysis
- [ ] Import/export with deps

### Phase 4: Polish
- [ ] ConfigManager
- [ ] BundleManager
- [ ] Interactive conflict resolution
- [ ] Progress reporting improvements

## Success Metrics

- Environment creation < 30 seconds
- Node addition < 10 seconds
- Model scanning < 1 second per GB
- Workflow sync < 1 second
- Model resolution success > 80%
- Zero data loss operations