# ComfyDock CLI Usage Guide

## Command Structure

The ComfyDock CLI uses a hierarchical command structure with a global `-e` option for specifying target environments.

```bash
comfydock [global-options] <command> [command-args]
```

## Global Options

- `-e, --env NAME` - Target environment (uses active if not specified)
- `-v, --verbose` - Verbose output
- `--help` - Show help

## Workspace Commands

These commands operate at the workspace level and don't require an environment:

```bash
# Initialize workspace
comfydock init [--path DIR]

# Update the config interactively, add any API keys (civitai, huggingface, etc)
comfydock config
```

## Environment Management

Commands that operate ON environments (create, delete, use):

```bash
# Create new environment
comfydock create my-env

# Delete environment
comfydock delete my-env

# Set active environment
comfydock use my-env

# List all environments
comfydock list

# Scan and import existing ComfyUI instance
comfydock migrate SOURCE ENV_NAME

# Import ComfyDock environment (packed in .tar.gz usually)
comfydock import [path to input]

# Export ComfyDock environment (include relevant files from .cec)
comfydock export [path to output]
```

Commands that operate IN environments (require `-e` flag or active environment):

```bash
# Run ComfyUI (automatically sync changes in pyproject.toml unless run with --no-sync)
comfydock run [--no-sync][comfyui-args]

# Show status (both "sync" and "git" status)
comfydock status

# Apply changes from pyproject.toml to current environment
comfydock sync [--dry-run]

# Commit unsaved changes to pyproject.toml
comfydock commit [message]

# Show commit history
comfydock log

# Revert to previous commit or discard uncommitted changes
comfydock rollback [target]
```

## Node Management

Custom node operations (workspace-level):

```bash
# Search for a custom node in registry
comfydock node search <query>
```

Environment-based (require -e flag or active environment):

```bash
# Add a custom node
comfydock node add <node-registry-id|git-url>

# Remove a node
comfydock node remove <node-name>

# List nodes in environment
comfydock node list
```

## Model Management

### Model Directory Tracking (workspace-level)

```bash
# Add directory to model tracking (scans and indexes models)
comfydock model dir add <path>

# Remove directory from tracking
comfydock model dir remove <path|id>

# List tracked directories
comfydock model dir list
```

### Model Index Operations (workspace-level)

```bash
# Search models by hash prefix or filename
comfydock model index find <query>

# List all indexed models
comfydock model index list [--type TYPE]

# Show model index statistics
comfydock model index status

# Sync tracked directories (update index for changes)
comfydock model index sync [directory-id]
```

### Environment Model Management (require -e flag or active environment)

```bash
# Add model to environment manifest
# From index: comfydock model add <hash>
# From URL: comfydock model add <url>
# As optional: comfydock model add <hash|url> --optional
# To specific workflow: comfydock model add <hash|url> --workflow <name>
comfydock model add <hash|url> [--optional] [--workflow NAME]

# Remove model from manifest
comfydock model remove <hash>

# List models in environment manifest (reports if models are present locally, need to be downloaded, etc.)
comfydock model list
```

## Workflow Management

Workflow Operations (environment-based, require -e flag or active environment):

```bash
# Show workflow status
comfydock workflow list

# Track workflow (auto-detects models and nodes)
comfydock workflow track <name> [--all]

# Stop tracking workflow
comfydock workflow untrack <name>

# Sync tracked workflows between ComfyUI and .cec/workflows/
comfydock workflow sync

# Import workflow file
comfydock workflow import <file>

# Export workflow with dependencies
comfydock workflow export <name>
```

## Python Dependency Management

Environment-based (require -e flag or active environment):

```bash
# Add constraint dependency
comfydock constraint add <package-spec>

# List constraint dependencies
comfydock constraint list

# Remove constraint dependency
comfydock constraint remove <package-name>
```

## Developer Commands (WIP)

```bash
# Opens new shell in current environment (python/docker)
comfydock shell

# Bug found related to specific environment (will gather log details + report text)
comfydock bug <report>
```

## Typical Workflows

### Setting Up a New Project

```bash
# 1. Initialize workspace (one-time)
comfydock init

# 2. Add model directories to tracking (performs initial scan)
comfydock model dir add ~/ComfyUI/models

# 3. Create and activate environment
comfydock create my-project
comfydock use my-project

# 4. Add custom nodes
comfydock node add comfyui-animatediff

# 5. Build workflow in ComfyUI
comfydock run

# 6. Track workflow (auto-detects models)
comfydock workflow track my-animation
# Shows which models were detected and if any are missing from index

# 7. Add optional models for variety
comfydock model add abc123  # By hash from index
comfydock model add 'cool_lora_1234.ckpt' --optional  # By name from index and optional (asks user if multiple models have same name)
comfydock model add https://civitai.com/models/12345 --optional --workflow my-animation  # Download and add to workflow

# 8. Commit and export
comfydock commit "Animation workflow with optional styles"
comfydock export my-project.tar.gz
```

### Importing a Shared Project

```bash
# 1. Import environment
comfydock import animation-project.tar.gz
# Shows model resolution:
#   ✓ Found locally
#   ? Similar name found (confirm)
#   ✗ Missing (download available)

# 2. Run (automatically syncs)
comfydock -e animation-project run
```

### Managing Models Across Projects

```bash
# Check what models you have
comfydock model index status
# Shows: 124 models indexed, 3 tracked directories

# Find specific model
comfydock model index find "sd_xl"
# Shows matches with hash, size, which environments use it

# Update index when you manually download + add new models to a tracked model directory
comfydock model dir sync
# Only processes changed files (by mtime)

# See what models a project uses
comfydock -e my-project model list
# Shows required and optional models
```

## Example Status Output

```bash
comfydock status
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
   
Next: Run 'comfydock sync' to apply changes
      Run 'comfydock commit "message"' to save changes
```