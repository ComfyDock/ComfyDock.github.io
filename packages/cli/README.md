# ComfyDock CLI Usage Guide

## Command Structure

The ComfyDock CLI uses a hierarchical command structure with a global `-e` option for specifying target environments.

```bash
cfd [global-options] <command> [command-args]
```

## Global Options

- `-e, --env NAME` - Target environment (uses active if not specified)
- `-v, --verbose` - Verbose output
- `--help` - Show help

## Workspace Commands

These commands operate at the workspace level and don't require an environment:

```bash
# Initialize workspace
cfd init [--path DIR]

# Update the config interactively, add any API keys (civitai, huggingface, etc)
cfd config
```

## Environment Management

Commands that operate ON environments (create, delete, use):

```bash
# Create new environment
cfd create my-env

# Delete environment
cfd delete my-env

# Set active environment
cfd use my-env

# List all environments
cfd list

# Scan and import existing ComfyUI instance
cfd migrate SOURCE ENV_NAME

# Import ComfyDock environment (packed in .tar.gz usually)
cfd import [path to input]

# Export ComfyDock environment (include relevant files from .cec)
cfd export [path to output]
```

Commands that operate IN environments (require `-e` flag or active environment):

```bash
# Run ComfyUI (automatically sync changes in pyproject.toml unless run with --no-sync)
cfd run [--no-sync][comfyui-args]

# Show status (both "sync" and "git" status)
cfd status

# Apply changes from pyproject.toml to current environment
cfd sync [--dry-run]

# Commit unsaved changes to pyproject.toml
cfd commit [message]

# Show commit history
cfd log

# Revert to previous commit or discard uncommitted changes
cfd rollback [target]
```

## Node Management

Custom node operations (workspace-level):

```bash
# Search for a custom node in registry
cfd node search <query>
```

Environment-based (require -e flag or active environment):

```bash
# Add a custom node
cfd node add <node-registry-id|git-url>

# Remove a node
cfd node remove <node-name>

# List nodes in environment
cfd node list
```

## Model Management

### Model Directory Tracking (workspace-level)

```bash
# Add directory to model tracking (scans and indexes models)
cfd model dir add <path>

# Remove directory from tracking
cfd model dir remove <path|id>

# List tracked directories
cfd model dir list
```

### Model Index Operations (workspace-level)

```bash
# Search models by hash prefix or filename
cfd model index find <query>

# List all indexed models
cfd model index list [--type TYPE]

# Show model index statistics
cfd model index status

# Sync tracked directories (update index for changes)
cfd model index sync [directory-id]
```

### Environment Model Management (require -e flag or active environment)

```bash
# Add model to environment manifest
# From index: cfd model add <hash>
# From URL: cfd model add <url>
# As optional: cfd model add <hash|url> --optional
# To specific workflow: cfd model add <hash|url> --workflow <name>
cfd model add <hash|url> [--optional] [--workflow NAME]

# Remove model from manifest
cfd model remove <hash>

# List models in environment manifest (reports if models are present locally, need to be downloaded, etc.)
cfd model list
```

## Workflow Management

Workflow Operations (environment-based, require -e flag or active environment):

```bash
# Show workflow status
cfd workflow list

# Track workflow (auto-detects models and nodes)
cfd workflow track <name> [--all]

# Stop tracking workflow
cfd workflow untrack <name>

# Sync tracked workflows between ComfyUI and .cec/workflows/
cfd workflow sync

# Import workflow file
cfd workflow import <file>

# Export workflow with dependencies
cfd workflow export <name>
```

## Python Dependency Management

Environment-based (require -e flag or active environment):

```bash
# Add constraint dependency
cfd constraint add <package-spec>

# List constraint dependencies
cfd constraint list

# Remove constraint dependency
cfd constraint remove <package-name>
```

## Developer Commands (WIP)

```bash
# Opens new shell in current environment (python/docker)
cfd shell

# Bug found related to specific environment (will gather log details + report text)
cfd bug <report>
```

## Typical Workflows

### Setting Up a New Project

```bash
# 1. Initialize workspace (one-time)
cfd init

# 2. Add model directories to tracking (performs initial scan)
cfd model dir add ~/ComfyUI/models

# 3. Create and activate environment
cfd create my-project
cfd use my-project

# 4. Add custom nodes
cfd node add comfyui-animatediff

# 5. Build workflow in ComfyUI
cfd run

# 6. Track workflow (auto-detects models)
cfd workflow track my-animation
# Shows which models were detected and if any are missing from index

# 7. Add optional models for variety
cfd model add abc123  # By hash from index
cfd model add 'cool_lora_1234.ckpt' --optional  # By name from index and optional (asks user if multiple models have same name)
cfd model add https://civitai.com/models/12345 --optional --workflow my-animation  # Download and add to workflow

# 8. Commit and export
cfd commit "Animation workflow with optional styles"
cfd export my-project.tar.gz
```

### Importing a Shared Project

```bash
# 1. Import environment
cfd import animation-project.tar.gz
# Shows model resolution:
#   ✓ Found locally
#   ? Similar name found (confirm)
#   ✗ Missing (download available)

# 2. Run (automatically syncs)
cfd -e animation-project run
```

### Managing Models Across Projects

```bash
# Check what models you have
cfd model index status
# Shows: 124 models indexed, 3 tracked directories

# Find specific model
cfd model index find "sd_xl"
# Shows matches with hash, size, which environments use it

# Update index when you manually download + add new models to a tracked model directory
cfd model dir sync
# Only processes changed files (by mtime)

# See what models a project uses
cfd -e my-project model list
# Shows required and optional models
```

## Example Status Output

```bash
cfd status
```
```
Environment: my-project
Path: ~/comfydock/environments/my-project
─────────────────────────────────────

📝 Sync Status: ✗ Out of sync
   
   Custom Nodes:
   + comfyui-animatediff (to be installed)
   
   Workflows:
   ✓ my-animation (tracked, 3 models detected)
   
   Models:
   ✓ All required models available

📦 Git Status: Modified
   
   Changes to be committed:
   + Added: comfyui-animatediff
   + Added workflow: my-animation
   + Added 3 required models
   
Next: Run 'cfd sync' to apply changes
      Run 'cfd commit "message"' to save changes
```