# Managing Workspaces

> Learn how to initialize, configure, and manage your ComfyDock workspace.

## What is a workspace?

A **workspace** is the top-level container for all your ComfyDock environments and shared resources. Typically, you have one workspace per machine located at `~/comfydock/`.

See [Core Concepts](../getting-started/concepts.md#workspace) for architectural details.

## Initializing a workspace

### Basic initialization

```bash
cfd init
```

Creates workspace at `~/comfydock/` with:

- `environments/` - Your ComfyUI environments
- `models/` - Shared models directory
- `comfydock_cache/` - Registry cache and model index
- `logs/` - Application logs
- `.metadata/` - Workspace configuration

### Custom location

```bash
cfd init /path/to/workspace
```

Creates workspace at custom path. You'll need to set `COMFYDOCK_HOME` environment variable:

```bash
export COMFYDOCK_HOME=/path/to/workspace
```

Add to `~/.bashrc` or `~/.zshrc` to persist across sessions.

### With existing models

```bash
cfd init --models-dir /path/to/existing/models
```

Points workspace to existing models directory and indexes them automatically.

### Non-interactive mode

```bash
cfd init --yes
```

Uses all defaults without prompts. Useful for scripting.

## Configuration management

### View configuration

```bash
cfd config --show
```

Shows current workspace configuration including:

- Active environment
- Models directory path
- CivitAI API key (masked)

### Set CivitAI API key

```bash
cfd config --civitai-key YOUR_API_KEY
```

Required for downloading models from CivitAI. Get your key from [https://civitai.com/user/account](https://civitai.com/user/account).

!!! tip "Why CivitAI API key?"
    ComfyDock uses the CivitAI API to resolve model hashes and find download URLs. Without an API key, you can still use CivitAI URLs directly but automatic resolution won't work.

### Clear CivitAI key

```bash
cfd config --civitai-key ""
```

## Registry management

ComfyDock uses the official ComfyUI registry to look up custom nodes.

### Check registry status

```bash
cfd registry status
```

Shows:

- Last update time
- Number of cached nodes
- Registry data location

### Update registry data

```bash
cfd registry update
```

Downloads latest registry data from GitHub. Run this periodically to get newly published nodes.

!!! note "When to update"
    - After installing ComfyDock (done automatically during `cfd init`)
    - When a node isn't found (registry might be outdated)
    - Monthly maintenance

## Logging and debugging

### View logs

```bash
# Show last 200 lines (default)
cfd logs

# Show last 50 lines
cfd logs -n 50

# Show all logs
cfd logs --full

# Filter by level
cfd logs --level ERROR

# Show workspace logs instead of environment logs
cfd logs --workspace
```

Logs are stored in `workspace/logs/` and include:

- Environment operations (create, delete, sync)
- Node installations
- Model operations
- Error stack traces

!!! tip "Debugging workflow"
    1. Run failing command
    2. Check logs: `cfd logs -n 100`
    3. Look for ERROR or WARNING entries
    4. Include relevant log lines in bug reports

## Workspace structure

After initialization, your workspace looks like:

```
~/comfydock/
├── environments/
│   ├── my-project/           # Environment 1
│   ├── testing/              # Environment 2
│   └── production/           # Environment 3
├── models/
│   ├── checkpoints/          # SD checkpoints
│   ├── loras/                # LoRA files
│   ├── vae/                  # VAE models
│   └── ...                   # Other model types
├── comfydock_cache/
│   ├── registry_cache.db     # Registry data
│   ├── model_index.db        # Model index
│   └── workflow_cache.db     # Workflow analysis cache
├── logs/
│   ├── workspace.log         # Workspace-level logs
│   └── environments/         # Per-environment logs
└── .metadata/
    └── workspace.json        # Workspace config
```

## Multiple workspaces

You can have multiple workspaces by using `COMFYDOCK_HOME`:

```bash
# Work workspace
export COMFYDOCK_HOME=~/comfydock-work
cfd init
cfd create client-project

# Personal workspace
export COMFYDOCK_HOME=~/comfydock-personal
cfd init
cfd create experiments
```

Switch between them by changing the environment variable.

## Best practices

!!! success "Recommended"
    - **One workspace per machine** - Simplifies management
    - **Point to existing models** - Avoid duplicating large files
    - **Update registry monthly** - Get latest node information
    - **Set CivitAI key early** - Enable automatic model resolution

!!! warning "Avoid"
    - **Multiple workspaces** - Unless you have specific isolation needs
    - **Nested workspaces** - Don't create workspace inside another workspace
    - **Manual .metadata edits** - Use `cfd config` commands instead

## Troubleshooting

### "Workspace not initialized"

**Problem**: Running commands shows workspace not found error

**Solution**:
```bash
# Initialize workspace
cfd init

# Or set COMFYDOCK_HOME to existing workspace
export COMFYDOCK_HOME=/path/to/workspace
```

### Registry data missing

**Problem**: Node resolution fails, workflow resolve doesn't work

**Solution**:
```bash
cfd registry update
```

### Models directory not found

**Problem**: Models aren't being indexed

**Solution**:
```bash
# Point to correct directory
cfd model index dir /path/to/models

# Sync index
cfd model index sync
```

## Next steps

- [Create environments](environments/creating-environments.md) (Coming soon)
- [Model management](models/model-index.md) (Coming soon)
- [Environment version control](environments/version-control.md) (Coming soon)
