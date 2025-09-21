# ComfyDock Model Management Implementation Plan

## Overview

This document outlines the complete implementation plan for ComfyDock's model management system, building on the existing codebase to provide:
- **Model indexing** across multiple directories with deduplication ✅ (Already implemented)
- **Workflow-based model detection** during workflow tracking 🚧 (Needs implementation)
- **Smart model resolution** using multiple hash types 🚧 (Partial - needs SHA256)
- **Source tracking** for redownloading models ❌ (Not implemented)
- **Environment manifests** that reference models without duplication ❌ (Not implemented)

## Current Implementation Status

### Already Implemented
- **ModelManager** with smart scanning, short hash (BLAKE3 chunks), and duplicate detection
- **ModelIndexManager** with SQLite database and indexing operations
- **Workspace-level model commands** for directory tracking and searching
- **Basic workflow tracking** (without model extraction)

### Gaps to Fill
1. Model source tracking for re-downloading
2. SHA256 hash support for compatibility
3. Workflow model extraction
4. Model manifest in pyproject.toml
5. Environment-level model commands
6. Model download from URLs
7. Model resolution for import/export

## Architecture Decisions

### 1. Database Design
- **Existing**: SQLite `models.db` with models table using short_hash
- **To Add**: `model_sources` table for tracking download URLs
- **To Add**: SHA256 hash column (computed on demand)

### 2. Model Identification
- **Primary**: Short-hash = BLAKE3-based hash using 5MB chunks from start, middle, and end (already implemented)
- **Secondary**: Full BLAKE3 hash (already implemented for collision resolution)
- **Tertiary**: SHA256 hash (to be added for repository compatibility)
- **Fallback**: Filename matching with user confirmation (partially implemented)

### 3. Workflow Integration
- Model detection happens automatically during `workflow track` (to be implemented)
- Workflows reference models by short hash in pyproject.toml (to be implemented)
- Missing models are reported but don't block workflow tracking

## Database Schema

### Existing Schema (in ModelIndexManager)
```sql
-- Current models table (ALREADY EXISTS)
CREATE TABLE IF NOT EXISTS models (
    hash TEXT PRIMARY KEY,        -- Uses short_hash currently
    path TEXT NOT NULL,
    filename TEXT NOT NULL,
    model_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    last_seen INTEGER NOT NULL,
    metadata TEXT DEFAULT '{}',   -- Stores duplicates info
    short_hash TEXT,              -- The BLAKE3 chunk hash
    mtime REAL,                   -- File modification time
    tracked_dir TEXT              -- Links to tracked directories
);

-- Index (ALREADY EXISTS)
CREATE INDEX IF NOT EXISTS idx_short_hash ON models(short_hash);
```

### To Be Added
```sql
-- 1. Extend models table with new columns (via migration)
ALTER TABLE models ADD COLUMN blake3_hash TEXT;  -- Full BLAKE3 (computed on demand)
ALTER TABLE models ADD COLUMN sha256_hash TEXT;  -- SHA256 (computed on demand)

-- 2. New table for model sources
CREATE TABLE IF NOT EXISTS model_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hash TEXT NOT NULL,           -- References models.hash
    source_type TEXT NOT NULL,    -- 'civitai', 'huggingface', 'url'
    source_url TEXT NOT NULL,
    source_data TEXT,             -- JSON with type-specific metadata
    added_at INTEGER NOT NULL,
    FOREIGN KEY (hash) REFERENCES models(hash) ON DELETE CASCADE,
    UNIQUE(hash, source_url)
);

-- 3. New indexes for performance
CREATE INDEX IF NOT EXISTS idx_models_blake3 ON models(blake3_hash);
CREATE INDEX IF NOT EXISTS idx_models_sha256 ON models(sha256_hash);
CREATE INDEX IF NOT EXISTS idx_sources_hash ON model_sources(hash);
```

Note: Tracked directories are already managed in workspace.json metadata, not in the database.

## pyproject.toml Structure

```toml
[tool.comfydock.models.required]
# Models required for workflows to function
"abc123de..." = {  # short hash as key
    filename = "sd_xl_base_1.0.safetensors",
    type = "checkpoint",
    size = 6946838366,
    blake3 = "abc123def456789...",  # Full BLAKE3 
    sha256 = "123456789abcdef...",  # Full SHA256 (optional)
    sources = [
        { type = "civitai", url = "https://civitai.com/api/download/models/101055" },
        { type = "huggingface", repo = "stabilityai/stable-diffusion-xl-base-1.0" }
    ]
}

[tool.comfydock.models.optional]
# Models that enhance workflows but aren't required
"def456gh..." = {
    filename = "pixel_art_xl.safetensors",
    type = "lora",
    size = 234567890,
    ...
}

[tool.comfydock.workflows.tracked.my_workflow]
file = "workflows/my_workflow.json"
requires = {
    nodes = ["comfyui-animatediff", "comfyui-controlnet"],
    models = ["abc123de", "def456gh"],  # References by short hash
    python = []
}
```

## Core Components

### 1. Extend ModelIndexManager (`managers/model_index_manager.py`) ✅ Exists

**Current Implementation:**
- Basic CRUD operations for models table
- Find by hash prefix and filename
- Support for tracked directories

**To Add:**
```python
def find_by_source_url(self, url: str) -> ModelIndex | None:
    """Check if we have a model from this source."""
    query = "SELECT m.* FROM models m JOIN model_sources s ON m.hash = s.hash WHERE s.source_url = ?"
    
def add_source(self, hash: str, source_type: str, url: str, metadata: dict = None):
    """Add a download source for a model."""
    
def compute_sha256(self, file_path: Path) -> str:
    """Compute SHA256 hash for external compatibility."""
```

### 2. Create WorkflowParser (`utils/workflow_parser.py`) ❌ New File

```python
class WorkflowParser:
    """Extract model and node references from ComfyUI workflows."""
    
    def __init__(self, workflow_path: Path):
        self.workflow = self._load_workflow_json(workflow_path)
    
    def extract_model_references(self) -> dict[str, list[str]]:
        """Extract all model references from workflow JSON.
        
        Returns dict of model_type -> [filenames]
        """
        models = {
            'checkpoint': [],
            'lora': [],
            'vae': [],
            'controlnet': [],
            'upscale_model': [],
            'clip': [],
            'unet': [],
            'embedding': []
        }
        
        # Node type to model field mapping
        NODE_MODEL_MAPPING = {
            'CheckpointLoaderSimple': ('checkpoint', 'ckpt_name'),
            'CheckpointLoader': ('checkpoint', 'ckpt_name'),
            'LoraLoader': ('lora', 'lora_name'),
            'VAELoader': ('vae', 'vae_name'),
            'VAEEncode': ('vae', 'vae_name'),
            'VAEDecode': ('vae', 'vae_name'),
            'ControlNetLoader': ('controlnet', 'control_net_name'),
            'UpscaleModelLoader': ('upscale_model', 'model_name'),
            'CLIPLoader': ('clip', 'clip_name'),
            'UNETLoader': ('unet', 'unet_name'),
            'GLIGENLoader': ('gligen', 'gligen_name'),
            'HypernetworkLoader': ('hypernetwork', 'hypernetwork_name'),
            'StyleModelLoader': ('style', 'style_model_name'),
            'CLIPVisionLoader': ('clip_vision', 'clip_name'),
        }
        
        # Scan all nodes
        for node_id, node_data in self.workflow.items():
            if not isinstance(node_data, dict):
                continue
                
            class_type = node_data.get('class_type', '')
            inputs = node_data.get('inputs', {})
            
            # Check if this node type loads models
            if class_type in NODE_MODEL_MAPPING:
                model_type, field_name = NODE_MODEL_MAPPING[class_type]
                if model_name := inputs.get(field_name):
                    models.setdefault(model_type, []).append(model_name)
        
        # Remove duplicates
        for model_type in models:
            models[model_type] = list(dict.fromkeys(models[model_type]))
        
        return models
```

### 3. Create ModelDownloadManager (`managers/model_download_manager.py`) ❌ New File

Builds on existing `utils/download.py`:

```python
class ModelDownloadManager:
    """Handle model downloads from various sources."""
    
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.cache_dir = model_manager.workspace_path / "models"
        
    def download_from_url(self, url: str) -> ModelIndex:
        """Download model from URL and add to index.
        
        Checks if already downloaded via source tracking.
        """
        # Check if we already have this URL
        if existing := self.model_manager.index_manager.find_by_source_url(url):
            logger.info(f"Model already indexed from {url}")
            return existing
        
        # Parse URL for metadata
        source_type, metadata = self._parse_source_url(url)
        
        # Determine filename
        filename = self._extract_filename_from_url(url)
        target_path = self.cache_dir / filename
        
        # Download if not exists
        if not target_path.exists():
            from ..utils.download import download_file
            temp_file = download_file(url)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(temp_file, target_path)
        
        # Add to index with source
        model_info = self.model_manager._create_model_info(target_path)
        self.model_manager.index_manager.add_model(model_info, target_path, "downloads")
        self.model_manager.index_manager.add_source(
            model_info.short_hash, source_type, url, metadata
        )
        
        return self.model_manager.index_manager.find_by_hash(model_info.short_hash)[0]
```

### 4. Model Resolver (`managers/model_resolver.py`)

Resolves model requirements when importing environments.

```python
class ModelResolver:
    """Resolve model requirements for environments."""
    
    def resolve_models(self, manifest: dict, index_manager: ModelIndexManager) -> ResolutionResult:
        """Resolve all models in environment manifest.
        
        Tries multiple resolution strategies:
        1. Short hash (exact match)
        2. Full BLAKE3 hash
        3. SHA256 hash
        4. Filename with user confirmation
        """
        result = ResolutionResult()
        
        all_models = {
            **manifest.get('required', {}),
            **manifest.get('optional', {})
        }
        
        for short_hash, model_spec in all_models.items():
            # Try short hash first
            if matches := index_manager.find_by_hash(short_hash):
                result.resolved[short_hash] = matches[0]
                continue
            
            # Try full hashes
            if blake3 := model_spec.get('blake3'):
                if matches := index_manager.find_by_hash(blake3):
                    result.resolved[short_hash] = matches[0]
                    continue
            
            if sha256 := model_spec.get('sha256'):
                if matches := index_manager.find_by_sha256(sha256):
                    result.resolved[short_hash] = matches[0]
                    continue
            
            # Check if downloadable
            if sources := model_spec.get('sources'):
                result.downloadable[short_hash] = model_spec
            else:
                # Try filename matching as last resort
                if matches := index_manager.find_by_filename(model_spec['filename']):
                    result.needs_confirmation[short_hash] = matches
                else:
                    result.missing[short_hash] = model_spec
        
        return result
```

### 4. Extend PyprojectManager with ModelHandler ❌ To Add

Add model management to `managers/pyproject_manager.py`:

```python
class ModelHandler:
    """Handle model configuration in pyproject.toml."""
    
    def __init__(self, pyproject: dict):
        self.pyproject = pyproject
        self._ensure_structure()
    
    def _ensure_structure(self):
        """Ensure tool.comfydock.models exists."""
        if "tool" not in self.pyproject:
            self.pyproject["tool"] = {}
        if "comfydock" not in self.pyproject["tool"]:
            self.pyproject["tool"]["comfydock"] = {}
        if "models" not in self.pyproject["tool"]["comfydock"]:
            self.pyproject["tool"]["comfydock"]["models"] = {
                "required": {},
                "optional": {}
            }
    
    def add_model(self, model: ModelIndex, category: str = "required"):
        """Add a model to the manifest."""
        models_section = self.pyproject["tool"]["comfydock"]["models"][category]
        models_section[model.hash] = {
            "filename": model.filename,
            "type": model.model_type,
            "size": model.file_size,
            # Additional hashes will be computed on export
        }
    
    def get_all(self) -> dict:
        """Get all models in manifest."""
        return self.pyproject["tool"]["comfydock"]["models"]
```

### 5. Update WorkflowManager (`managers/workflow_manager.py`) ✅ Exists

Replace the TODO in `_parse_workflow_dependencies`:

```python
def _parse_workflow_dependencies(self, workflow_path: Path) -> dict:
    """Parse workflow JSON to extract dependencies."""
    try:
        # Use new WorkflowParser utility
        from ..utils.workflow_parser import WorkflowParser
        parser = WorkflowParser(workflow_path)
        
        # Extract model references
        model_refs = parser.extract_model_references()
        
        # Resolve against workspace model index
        from ..core.workspace import Workspace
        workspace = Workspace.from_path(self.env_path.parent.parent)
        
        resolved_models = []
        missing_models = []
        
        for model_type, filenames in model_refs.items():
            for filename in filenames:
                matches = workspace.model_manager.index_manager.find_by_filename(filename)
                if matches:
                    resolved_models.append(matches[0].hash)
                else:
                    missing_models.append((model_type, filename))
        
        # Report missing models but don't fail
        if missing_models:
            logger.warning(f"Workflow uses {len(missing_models)} models not in index")
            for model_type, filename in missing_models:
                logger.warning(f"  - {filename} ({model_type})")
        
        # Extract nodes (existing code)
        nodes = set()
        with open(workflow_path) as f:
            data = json.load(f)
        for _node_id, node_data in data.items():
            if isinstance(node_data, dict) and "class_type" in node_data:
                class_type = node_data["class_type"]
                if not class_type.startswith(("Load", "Save", "Preview", "primitive")):
                    nodes.add(class_type)
        
        return {
            "nodes": sorted(nodes),
            "models": resolved_models,  # Now populated!
            "python": []
        }
        
    except Exception as e:
        logger.warning(f"Failed to parse workflow dependencies: {e}")
        return {"nodes": [], "models": [], "python": []}
```

## CLI Command Implementation

### Command Structure Alignment

Per the CLI plan, we need the following model commands:

#### Workspace-Level Commands (in `cli/global_commands.py`)

**Model Directory Commands:**
- ✅ `model dir add <path>` - Already implemented
- ✅ `model dir remove <path|id>` - Already implemented  
- ✅ `model dir list` - Already implemented

**Model Index Commands:**
- ❌ `model index find <query>` - Currently at wrong level (is `model find`)
- ❌ `model index list [--type TYPE]` - Currently at wrong level (is `model list`)
- ❌ `model index status` - Currently at wrong level (is `model status`)
- ❌ `model index sync [directory-id]` - Currently at wrong level (is `model sync`)

#### Environment-Level Commands (in `cli/env_commands.py`)
- ❌ `model add <hash|url>` - Not implemented
- ❌ `model remove <hash>` - Not implemented
- ❌ `model list` - Not implemented (different from index list)

### Required CLI Structure Changes

1. **Move existing commands under `model index` subcommand:**
   - `model find` → `model index find`
   - `model list` → `model index list`
   - `model status` → `model index status`
   - `model sync` → `model index sync`

2. **Add new environment-level model commands:**
   - `model add` - Add to environment manifest
   - `model remove` - Remove from manifest
   - `model list` - List manifest models

### To Implement: Environment Model Commands (in `cli/env_commands.py`)

```python
@with_env_logging("model add")
def model_add(self, args):
    """Add model to environment manifest."""
    env = self._get_env(args)
    workspace = self.workspace
    
    if args.identifier.startswith('http'):
        # Download from URL
        print(f"Downloading from {args.identifier}...")
        download_manager = ModelDownloadManager(workspace.model_manager)
        model = download_manager.download_from_url(args.identifier)
    else:
        # Look up in index by hash or filename
        matches = workspace.search_models(args.identifier)
        if not matches:
            print(f"✗ Model not found: {args.identifier}")
            return
        elif len(matches) > 1:
            # Interactive selection
            print(f"Found {len(matches)} models:")
            for i, m in enumerate(matches):
                print(f"  {i+1}. {m.filename} [{m.hash[:8]}...]")
            choice = input("Select [1]: ").strip() or "1"
            model = matches[int(choice) - 1]
        else:
            model = matches[0]
    
    # Add to manifest
    category = 'optional' if args.optional else 'required'
    env.pyproject.models.add_model(model, category)
    
    # Link to workflow if specified
    if args.workflow:
        workflow_config = env.pyproject.workflows.get_tracked().get(args.workflow)
        if workflow_config:
            workflow_config['requires']['models'].append(model.hash)
            env.pyproject.save()
    
    print(f"✓ Added {category} model: {model.filename}")

@with_env_logging("model remove")
def model_remove(self, args):
    """Remove model from environment manifest."""
    env = self._get_env(args)
    
    # Remove from both required and optional
    removed = False
    for category in ['required', 'optional']:
        if env.pyproject.models.remove_model(args.hash, category):
            removed = True
            print(f"✓ Removed model from {category}")
            break
    
    if not removed:
        print(f"✗ Model not in manifest: {args.hash}")

@with_env_logging("model list")  
def model_list(self, args):
    """List models in environment manifest."""
    env = self._get_env(args)
    manifest = env.pyproject.models.get_all()
    
    # Check which models are available locally
    workspace = self.workspace
    
    print("Required Models:")
    for hash, spec in manifest.get('required', {}).items():
        local = workspace.model_manager.index_manager.find_by_hash(hash)
        status = "✓" if local else "✗"
        print(f"  {status} {spec['filename']} [{hash[:8]}...]")
        if not local and spec.get('sources'):
            print(f"      Download from: {spec['sources'][0]['type']}")
    
    if manifest.get('optional'):
        print("\nOptional Models:")
        for hash, spec in manifest['optional'].items():
            local = workspace.model_manager.index_manager.find_by_hash(hash)
            status = "✓" if local else "○"
            print(f"  {status} {spec['filename']} [{hash[:8]}...]")
```

## Implementation Roadmap

### Phase 0: CLI Structure Refactoring (1 day)
**Goal**: Align CLI commands with the planned structure

1. **Restructure workspace-level model commands in `cli/cli.py`:**
   - Create `model index` subparser group
   - Move `find`, `list`, `status`, `sync` under `model index`
   - Keep `model dir` subparser group as-is

2. **Update `cli/global_commands.py`:**
   - Rename methods to match new structure:
     - `model_list` → `model_index_list`
     - `model_find` → `model_index_find`
     - `model_status` → `model_index_status`
     - `model_sync` → `model_index_sync`

3. **Add environment model commands to `cli/cli.py`:**
   - Add `model add`, `model remove`, `model list` parsers under environment commands
   - These will call new methods in `env_commands.py`

### Phase 1: Core Model Infrastructure (3-4 days)
**Goal**: Extend existing model system with source tracking and SHA256 support

1. **Extend ModelIndexManager** 
   - Add `model_sources` table via schema migration
   - Implement `find_by_source_url()` method
   - Add `add_source()` and `get_sources()` methods
   - Add SHA256 hash computation (on-demand)

2. **Create WorkflowParser utility**
   - New file: `utils/workflow_parser.py`
   - Extract model references from workflow JSON
   - Map ComfyUI node types to model fields
   - Return dict of model_type -> [filenames]

3. **Update WorkflowManager**
   - Replace TODO in `_parse_workflow_dependencies()`
   - Use WorkflowParser to extract models
   - Resolve models against workspace index
   - Store model hashes in pyproject.toml

### Phase 2: Model Manifest System (2-3 days)
**Goal**: Add environment-level model tracking in pyproject.toml

1. **Extend PyprojectManager**
   - Add `ModelHandler` class (like existing NodeHandler)
   - Support required/optional model categories
   - Store model metadata (filename, type, size, hashes)

2. **Add Environment Model Commands**
   - `model add <hash|url>` - Add to manifest
   - `model remove <hash>` - Remove from manifest
   - `model list` - Show manifest with local status

3. **Create ModelDownloadManager**
   - New file: `managers/model_download_manager.py`
   - Parse URLs (CivitAI, HuggingFace, direct)
   - Download to cache directory
   - Add to index with source tracking

### Phase 3: Model Resolution & Import/Export (2-3 days)
**Goal**: Smart model resolution for environment sharing

1. **Create ModelResolver**
   - New file: `managers/model_resolver.py`
   - Try multiple resolution strategies (short hash, BLAKE3, SHA256, filename)
   - Interactive confirmation for ambiguous matches
   - Track downloadable vs missing models

2. **Enhance Export**
   - Compute full hashes for all models in manifest
   - Include all known sources
   - Package lightweight metadata (no actual model files)

3. **Enhance Import**
   - Resolve models using ModelResolver
   - Interactive selection for similar models
   - Offer to download from sources
   - Report resolution status

### Phase 4: Testing & Polish (1-2 days)
**Goal**: Ensure robustness and good UX

1. **Add Tests**
   - Test workflow model extraction
   - Test model resolution strategies
   - Test download and source tracking

2. **Improve UX**
   - Clear progress indicators for scanning
   - Helpful error messages for missing models
   - Status reports showing what's resolved/missing

3. **Documentation**
   - Update CLI help text
   - Add examples to documentation
   - Create troubleshooting guide

## Key Implementation Notes

### Working with Existing Code
- **ModelManager** already handles scanning and hashing - extend, don't replace
- **Workspace** already has model directory tracking - build on it
- **CLI structure** is established - follow existing patterns
- **Database** exists - use migrations to add new tables/columns

### Simplifications for MVP
- No direct API integration (just URL downloads)
- No model pruning or garbage collection
- No symlink mode (just references)
- No automatic model conversion
- Basic source tracking (URL only, no version info)

### Critical Path Items
1. **WorkflowParser** - Enables automatic model detection
2. **ModelHandler in PyprojectManager** - Enables manifest storage
3. **Source tracking** - Enables re-downloading
4. **SHA256 support** - Enables compatibility with external services

## Success Metrics
- ✅ Workflows automatically detect models during tracking
- ✅ Models are referenced in pyproject.toml by hash
- ✅ Missing models are reported with actionable next steps
- ✅ Models can be downloaded from URLs and tracked
- ✅ Environments can be exported with model metadata
- ✅ Imported environments can resolve models locally or download

## Risk Mitigation
- **Hash collisions**: Already handled with full BLAKE3 fallback
- **Large model files**: Use streaming for hash computation
- **Network failures**: Add retry logic for downloads
- **Corrupt downloads**: Verify size/hash after download
- **Missing models**: Don't block workflow tracking, just warn

## Final Command Structure Summary

After implementation, the model management commands will be:

### Workspace-Level (Global)
```bash
# Model directory tracking
comfydock model dir add <path>           ✅ Already exists
comfydock model dir remove <path|id>     ✅ Already exists
comfydock model dir list                 ✅ Already exists

# Model index operations
comfydock model index find <query>       ⚠️ Needs restructure (currently model find)
comfydock model index list [--type]      ⚠️ Needs restructure (currently model list)
comfydock model index status             ⚠️ Needs restructure (currently model status)
comfydock model index sync [dir-id]      ⚠️ Needs restructure (currently model sync)
```

### Environment-Level (requires -e or active environment)
```bash
# Environment model manifest
comfydock model add <hash|url> [--optional] [--workflow NAME]  ❌ New
comfydock model remove <hash>                                   ❌ New
comfydock model list                                           ❌ New
```

The key distinction:
- **`model index`** commands work with the workspace-wide model database
- **`model`** commands (in environment context) work with the environment's manifest
- **`model dir`** commands manage which directories are tracked for models