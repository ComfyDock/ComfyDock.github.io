# ComfyDock Workflow Management Specification
Version 1.0 - MVP

## Overview

ComfyDock manages ComfyUI workflows as first-class project assets, enabling users to version control, share, and reproduce workflows with their complete dependency chains. Workflows remain fully compatible with vanilla ComfyUI while gaining portability and dependency tracking through ComfyDock.

## Core Concepts

### Workflow States

Workflows in a ComfyDock environment exist in one of three states:

1. **Tracked** - Workflow is version controlled in `.cec/workflows/` and listed in `pyproject.toml` with its dependencies
2. **Watched** - Workflow exists in `ComfyUI/user/workflows/` but is not tracked by ComfyDock
3. **Ignored** - Workflow is explicitly excluded from ComfyDock management via `.comfydockignore`

### Workflow Locations

- **Active Directory**: `ComfyUI/user/workflows/` - Where ComfyUI reads/writes workflows during operation
- **Tracked Directory**: `.cec/workflows/` - Version controlled copies with dependency tracking
- **Both directories are kept in sync for tracked workflows**

## Command Structure

### Environment-Level Import
- `comfydock import <bundle>` - Creates NEW environment from bundle

### Workflow-Level Operations  
- `comfydock workflow <command>` - Operations within CURRENT environment:
  - `status` - Show all workflows and changes
  - `track/untrack` - Manage workflow tracking
  - `sync` - Synchronize tracked workflows
  - `import` - Add workflow to current environment
  - `export` - Export workflow with dependencies

## Workflow Commands (Current Environment Operations)

### Discovery and Status

#### `comfydock workflow status`
Shows all workflows and their current state (tracked/watched/ignored). Indicates sync status for tracked workflows and automatically detects any new or modified workflows since last check.

### Tracking Management

#### `comfydock workflow track <name>`
Begins tracking a workflow:
1. Copies workflow from ComfyUI directory to `.cec/workflows/`
2. Analyzes workflow for dependencies (nodes and models used)
3. Adds workflow entry to `pyproject.toml` with detected dependencies
4. Sets up bi-directional sync

#### `comfydock workflow untrack <name>`
Stops tracking a workflow:
1. Removes workflow entry from `pyproject.toml`
2. Removes workflow from `.cec/workflows/`
3. Preserves workflow in ComfyUI directory (never deletes user content)

#### `comfydock workflow track --all`
Tracks all currently untracked workflows in the ComfyUI directory.

#### `comfydock workflow track --pattern <pattern>`
Tracks workflows matching a glob pattern (e.g., `prod-*`).

### Synchronization

#### `comfydock workflow sync`
Synchronizes tracked workflows between ComfyUI and `.cec/workflows/`:
- Updates `.cec/workflows/` if workflow modified in ComfyUI
- Updates ComfyUI directory if workflow modified in `.cec/workflows/`
- Prompts for resolution if workflow modified in both locations
- Never affects watched (untracked) workflows

### Import and Export

#### `comfydock workflow export <name> --with-deps`
Exports a single workflow with its dependencies:
1. Creates a bundle containing the workflow file
2. Generates a minimal `pyproject.toml` with only this workflow's dependencies
3. Packages as `.tar.gz` for sharing

#### `comfydock workflow import <file>`
Imports a workflow into the current environment:
1. If bundle contains `pyproject.toml`, reads dependency requirements
2. Analyzes compatibility with current environment
3. Reports any conflicts or missing dependencies
4. Adds workflow as tracked after successful import

## Sync Behavior Rules

### Protection Rules
1. **Never delete watched workflows** - Untracked workflows are preserved during all operations
2. **Never auto-delete tracked workflows** - Deletion requires explicit user confirmation
3. **Preserve user modifications** - Changes in ComfyUI directory are respected

### Sync Triggers
- Manual: `comfydock workflow sync` command
- Manual: `comfydock sync` command
- Automatic: Before `comfydock run` (if enabled in configuration)
- Never automatic for destructive operations

### Conflict Resolution
When a tracked workflow is modified in both locations:
1. Detect conflict via file hash comparison
2. Present differences to user
3. Offer options: Keep ComfyUI version, Keep tracked version, or Manual merge
4. Apply user's choice

## Dependency Management

### Dependency Tracking
Each tracked workflow maintains its specific dependencies in `pyproject.toml`:

```toml
[tool.comfydock.workflows.tracked.<workflow-name>]
file = "workflows/<name>.json"
requires = {
    nodes = ["node1", "node2"],
    models = ["model1-hash"],
    python = ["package>=version"]
}
```

### Dependency Analysis
When tracking a workflow:
1. Parse workflow JSON to identify used custom nodes
2. Detect model file references
3. Map nodes to their Python dependencies
4. Record all requirements in workflow's `requires` section

### Dependency Merging
When importing workflows into an existing environment (`workflow import`):
1. Compare required versions with installed versions
2. Identify new dependencies to add
3. Detect version conflicts
4. Present merge plan to user for approval
5. Update environment's dependencies after confirmation

When creating new environments (`import`):
1. Use exact dependencies from bundle
2. No merging needed (fresh environment)
3. Faster and conflict-free

## Import Scenarios

### Scenario 1: New Environment from Workflow
`comfydock import <bundle>` - Creates a fresh environment with exact dependencies from the workflow bundle. No conflicts possible.

### Scenario 2: Add Workflow to Current Environment  
`comfydock workflow import <bundle>` - Adds workflow to existing environment, merging dependencies intelligently and resolving conflicts.

### Scenario 3: New Environment from Full Export
`comfydock import <full-export>` - Creates complete replica of exported environment with all workflows and dependencies.

### Scenario 4: Selective Import
`comfydock workflow import <bundle> --interactive` - Choose which workflows to import from a multi-workflow bundle.

## Configuration

### Project-Level Settings
In `pyproject.toml`:
- `track_pattern`: Glob pattern for auto-tracking new workflows
- `sync_mode`: Behavior for sync operations (safe/strict/manual)

### Ignore Patterns
`.comfydockignore` file supports glob patterns for excluding workflows:
- Scratch/temporary workflows
- Test workflows
- Backup files

## Safety Guarantees

1. **Data Preservation**: User workflows are never deleted without explicit confirmation
2. **Dependency Safety**: Conflicts are reported before any changes
3. **Rollback Capability**: Git tracking enables reverting changes
4. **Clear Status**: Users always know what's tracked vs. watched
5. **Non-Destructive Defaults**: Safe operations by default, dangerous operations require flags

## User Experience Principles

1. **Progressive Disclosure**: Start simple (track/untrack), advanced features available when needed
2. **Clear Feedback**: Every operation reports what it did or will do
3. **Dry Run Options**: Preview changes before applying them
4. **Intelligent Defaults**: Smart behaviors that can be overridden
5. **Workflow Portability**: Maintain full ComfyUI compatibility

## Common Usage Examples

### Share a workflow with someone
```bash
comfydock workflow export my-workflow --with-deps
# Creates my-workflow.tar.gz they can import
```

### Try someone's workflow (isolated)
```bash
comfydock import shared-workflow.tar.gz
# Creates new environment with exact dependencies
```

### Add someone's workflow to your environment
```bash
comfydock workflow import shared-workflow.tar.gz
# Merges into current environment, handling conflicts
```

### Track your local workflows
```bash
comfydock workflow status          # See what you have
comfydock workflow track my-work   # Start tracking one
comfydock workflow track --all     # Track everything
```

## MVP Scope

### Included
- Track/untrack workflows with dependency detection
- Bi-directional sync for tracked workflows  
- Import workflows to current environment (`workflow import`)
- Create new environments from bundles (`import`)
- Export single workflows with dependencies
- Basic conflict detection and resolution
- Protection of untracked workflows
- Automatic change detection in `workflow status`

### Excluded (Post-MVP)
- Workflow collections/sets management
- Complex automated dependency resolution strategies
- Workflow versioning and branching
- Team collaboration features
- Cloud workflow registry