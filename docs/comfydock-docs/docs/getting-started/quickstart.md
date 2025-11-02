# Quickstart

> Get up and running with ComfyDock in 5 minutes. By the end, you'll have created an environment, added custom nodes, and understand the basics of version control for your ComfyUI workflows.

## Before you begin

Make sure you have:

* ComfyDock installed — [Installation guide](installation.md)
* A terminal or command prompt open
* Internet connection for downloading dependencies

## Step 1: Initialize your workspace

Create a ComfyDock workspace:

```bash
cfd init
```

This creates `~/comfydock/` with the following structure:

```
~/comfydock/
├── environments/          # Your ComfyUI environments
├── models/                # Shared models directory
└── .metadata/             # Workspace configuration
```

!!! tip "Custom workspace location"
    Use a different path: `cfd init /path/to/workspace`

## Step 2: Create your first environment

Create an isolated ComfyUI environment:

```bash
cfd create my-project --use
```

This will:

1. Create a new environment called `my-project`
2. Download and install ComfyUI
3. Install PyTorch with GPU support (auto-detected)
4. Set it as your active environment
5. Take 2-5 minutes depending on your internet speed

!!! note "What's happening?"
    ComfyDock is creating an isolated Python environment with UV, downloading ComfyUI from GitHub, and installing dependencies. The `--use` flag makes this your active environment.

**What you'll see:**

```
🚀 Creating environment: my-project
   This will download PyTorch and dependencies (may take a few minutes)...

✓ Environment created: my-project
✓ Active environment set to: my-project

Next steps:
  • Run ComfyUI: cfd run
  • Add nodes: cfd node add <node-name>
```

## Step 3: Run ComfyUI

Start ComfyUI in your environment:

```bash
cfd run
```

ComfyUI opens at `http://localhost:8188`

!!! tip "Run in background"
    ```bash
    cfd run &
    ```

    Or use screen/tmux to keep it running:
    ```bash
    screen -S comfy
    cfd run
    # Detach with Ctrl+A, D
    ```

## Step 4: Check environment status

Open a new terminal and check your environment's status:

```bash
cfd status
```

**Output:**

```
Environment: my-project
ComfyUI: v0.2.2
Python: 3.11

📦 Custom Nodes (0):
  No custom nodes installed

📊 Workflows (0):
  No workflows tracked

Git Status: ✓ Clean (no uncommitted changes)
```

## Step 5: Add custom nodes

Let's add a custom node from the ComfyUI registry:

```bash
cfd node add comfyui-manager
```

This will:

1. Look up the node in the ComfyUI registry
2. Clone the repository to `custom_nodes/`
3. Install Python dependencies
4. Update `pyproject.toml`

!!! tip "Adding nodes from GitHub"
    ```bash
    # Add by GitHub URL
    cfd node add https://github.com/ltdrdata/ComfyUI-Manager

    # Add specific version/branch
    cfd node add comfyui-manager@v2.1.0
    ```

**Try adding more nodes:**

```bash
# Popular nodes to try
cfd node add comfyui-impact-pack
cfd node add comfyui-controlnet-aux
```

## Step 6: Commit your changes

Save your environment's current state:

```bash
cfd commit -m "Initial setup with ComfyUI Manager"
```

This creates a git commit in the `.cec/` directory tracking:

- Custom nodes and their versions
- Python dependencies
- Model references
- Workflow files

**Check your commit history:**

```bash
cfd commit log
```

**Output:**

```
Version  Timestamp                  Message
-------  -------------------------  ----------------------------
v1       2025-11-02 10:30:15 PST    Initial setup with ComfyUI Manager
```

## Step 7: Experiment safely

Let's add another node and see how rollback works:

```bash
# Add a test node
cfd node add comfyui-video-helper-suite

# Check status
cfd status
```

Now roll back to remove that change:

```bash
cfd rollback v1
```

Your environment reverts to the state from your first commit—`comfyui-video-helper-suite` is removed automatically.

!!! tip "Discard uncommitted changes"
    ```bash
    # Discard all changes since last commit
    cfd rollback
    ```

## Step 8: Load a workflow

Let's resolve dependencies for a workflow. Download a sample workflow JSON file, then:

```bash
# Move workflow to ComfyUI/user/default/workflows/
cp /path/to/workflow.json ~/comfydock/environments/my-project/ComfyUI/user/default/workflows/

# Resolve dependencies
cfd workflow resolve workflow.json
```

ComfyDock will:

1. Analyze the workflow JSON
2. Identify required nodes
3. Prompt you to install missing nodes
4. Find required models
5. Suggest download sources

!!! info "Auto-install mode"
    ```bash
    cfd workflow resolve workflow.json --install
    ```

    Automatically installs all missing nodes without prompting.

## Common workflows

Now that you have the basics, here are some common tasks:

### Switch between environments

```bash
# Create another environment
cfd create testing --use

# List all environments
cfd list

# Switch back to my-project
cfd use my-project
```

### Update a custom node

```bash
# Update to latest version
cfd node update comfyui-manager

# View installed nodes
cfd node list
```

### Add Python dependencies

```bash
# Add a package
cfd py add requests

# Add from requirements.txt
cfd py add -r requirements.txt

# List installed packages
cfd py list
```

### Export your environment

Share your environment with others:

```bash
cfd export my-workflow-pack.tar.gz
```

This creates a tarball containing:

- Node metadata and versions
- Model download URLs
- Python dependencies
- Workflow files

**Import on another machine:**

```bash
cfd import my-workflow-pack.tar.gz --name imported-env
```

## Essential commands

Here are the most important commands for daily use:

| Command | What it does | Example |
|---------|-------------|---------|
| `cfd create` | Create new environment | `cfd create prod --use` |
| `cfd use` | Switch active environment | `cfd use testing` |
| `cfd list` | List all environments | `cfd list` |
| `cfd run` | Start ComfyUI | `cfd run` |
| `cfd status` | Show environment status | `cfd status` |
| `cfd node add` | Add custom node | `cfd node add comfyui-manager` |
| `cfd commit` | Save current state | `cfd commit -m "message"` |
| `cfd rollback` | Revert to previous state | `cfd rollback v1` |
| `cfd export` | Export environment | `cfd export my-pack.tar.gz` |
| `cfd import` | Import environment | `cfd import my-pack.tar.gz` |

See the [CLI reference](../cli-reference/environment-commands.md) for a complete list of commands.

## Pro tips for beginners

!!! tip "Use tab completion"
    Install shell completion for faster typing:
    ```bash
    cfd completion install
    ```

    Then use Tab to autocomplete environment names, node names, and commands.

!!! tip "Check logs when things fail"
    ```bash
    cfd logs -n 50
    ```

    Shows the last 50 log lines for debugging.

!!! tip "Start with a clean environment"
    Don't add too many nodes at once. Start minimal, add what you need, commit often.

!!! tip "Use descriptive commit messages"
    ```bash
    cfd commit -m "Added IPAdapter for style transfer"
    ```

    Makes it easy to find specific versions later.

!!! tip "Specify PyTorch backend manually"
    ```bash
    # For NVIDIA GPUs
    cfd create gpu-env --torch-backend cu128

    # For AMD GPUs
    cfd create amd-env --torch-backend rocm6.3

    # For CPU only
    cfd create cpu-env --torch-backend cpu
    ```

## What's next?

Now that you've learned the basics, explore more advanced features:

<div class="grid cards" markdown>

-   :material-book-open-variant: **[Core Concepts](concepts.md)**

    ---

    Understand workspaces, environments, and how ComfyDock works

-   :material-cube-outline: **[Managing Custom Nodes](../user-guide/custom-nodes/adding-nodes.md)**

    ---

    Learn about registry IDs, GitHub URLs, and local development

-   :material-file-image: **[Model Management](../user-guide/models/model-index.md)**

    ---

    How the global model index works and CivitAI integration

-   :material-export: **[Collaboration](../user-guide/collaboration/export-import.md)**

    ---

    Share environments via tarballs or Git remotes

</div>

## Getting help

* **In your terminal**: Run `cfd --help` or `cfd <command> --help`
* **Documentation**: You're here! Browse other guides
* **Issues**: Report bugs on [GitHub Issues](https://github.com/ComfyDock/comfydock/issues)
* **Discussions**: Ask questions on [GitHub Discussions](https://github.com/ComfyDock/comfydock/discussions)
