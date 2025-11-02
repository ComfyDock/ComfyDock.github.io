# Installation

> Get ComfyDock installed and ready to use in just a few minutes.

## Prerequisites

Before installing ComfyDock, make sure you have:

* **Python 3.10 or newer** — Check with `python --version` or `python3 --version`
* **Operating system** — Windows 10/11, macOS 10.15+, or Linux (any modern distribution)
* **Internet connection** — For downloading dependencies and models

!!! tip "GPU Support"
    ComfyDock automatically detects your GPU (NVIDIA CUDA, AMD ROCm, Intel XPU) and installs the appropriate PyTorch backend. You can also specify backends manually with the `--torch-backend` flag.

## Step 1: Install UV

UV is a fast Python package manager that ComfyDock uses to manage environments and dependencies.

=== "macOS/Linux"
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

    After installation, restart your terminal or run:
    ```bash
    source $HOME/.cargo/env
    ```

=== "Windows PowerShell"
    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

    After installation, restart PowerShell.

=== "Windows CMD"
    ```cmd
    curl -LsSf https://astral.sh/uv/install.cmd -o install.cmd && install.cmd && del install.cmd
    ```

    After installation, restart CMD.

**Verify UV installation:**

```bash
uv --version
```

You should see output like `uv 0.4.x` or newer.

!!! info "Alternative: Install via pip"
    If you prefer pip:
    ```bash
    pip install uv
    ```

## Step 2: Install ComfyDock CLI

With UV installed, install the ComfyDock CLI tool:

```bash
uv tool install comfydock-cli
```

This installs the `cfd` command globally, making it available from anywhere in your terminal.

**Verify ComfyDock installation:**

```bash
cfd --version
```

You should see the ComfyDock version number.

!!! tip "Shell Completion"
    Install tab completion for your shell:
    ```bash
    cfd completion install
    ```

    Supports bash, zsh, and fish. Restart your shell after installing.

## Step 3: Initialize your workspace

Create a ComfyDock workspace directory:

```bash
# Initialize in default location (~/comfydock)
cfd init

# Or specify a custom path
cfd init /path/to/my/workspace
```

The workspace is where ComfyDock stores:

- Environments (isolated ComfyUI installations)
- Global model index
- Cache and logs

!!! note "Workspace Structure"
    ```
    ~/comfydock/
    ├── environments/          # Your ComfyUI environments
    ├── models/                # Shared models directory
    ├── comfydock_cache/       # Registry cache
    ├── logs/                  # Application logs
    └── .metadata/             # Workspace configuration
    ```

## Alternative installation methods

### Install from pip

If you don't want to use UV tool isolation:

```bash
pip install comfydock-cli
```

This makes `cfd` available in your current Python environment.

### Install from source

For development or testing:

```bash
# Clone the repository
git clone https://github.com/ComfyDock/comfydock.git
cd comfydock

# Install in development mode
uv pip install -e packages/cli/
```

## Verifying your installation

Check that everything is working:

```bash
# Check versions
cfd --version
uv --version

# Initialize workspace (if not done)
cfd init

# List environments (should be empty)
cfd list
```

You should see:

```
No environments found. Create one with: cfd create <name>
```

## Platform-specific notes

### Windows

* **WSL2 recommended** — For best performance, use ComfyDock in WSL2 (Windows Subsystem for Linux)
* **Long path support** — Enable long paths in Windows if you encounter path length errors:
    ```powershell
    New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
    ```

### macOS

* **Xcode Command Line Tools** — May be required for some dependencies:
    ```bash
    xcode-select --install
    ```

### Linux

* **System dependencies** — Most distributions work out of the box. If you encounter build errors, install development tools:

    === "Ubuntu/Debian"
        ```bash
        sudo apt-get update
        sudo apt-get install build-essential python3-dev
        ```

    === "Fedora/RHEL"
        ```bash
        sudo dnf install gcc gcc-c++ python3-devel
        ```

    === "Arch"
        ```bash
        sudo pacman -S base-devel python
        ```

## Updating ComfyDock

To update to the latest version:

```bash
uv tool upgrade comfydock-cli
```

Or with pip:

```bash
pip install --upgrade comfydock-cli
```

## Uninstalling

To remove ComfyDock:

```bash
# Remove the CLI tool
uv tool uninstall comfydock-cli

# Optionally remove your workspace
rm -rf ~/comfydock
```

!!! warning
    Removing the workspace deletes all your environments and configuration. Export any important environments first with `cfd export`.

## Troubleshooting installation

### UV not found after installation

**Problem:** Running `uv` shows "command not found"

**Solution:** Restart your terminal or manually source the environment:

=== "macOS/Linux"
    ```bash
    source $HOME/.cargo/env
    ```

=== "Windows PowerShell"
    Restart PowerShell or add to PATH manually via System Properties → Environment Variables

### Permission errors on Linux/macOS

**Problem:** Permission denied when installing

**Solution:** Don't use `sudo` with UV or pip. If needed, fix permissions:

```bash
# Fix UV permissions
chown -R $USER:$USER ~/.cargo

# For pip (if using system Python)
pip install --user comfydock-cli
```

### Python version too old

**Problem:** ComfyDock requires Python 3.10+

**Solution:** Install a newer Python version:

=== "Ubuntu/Debian"
    ```bash
    sudo add-apt-repository ppa:deadsnakes/ppa
    sudo apt-get update
    sudo apt-get install python3.11
    ```

=== "macOS (Homebrew)"
    ```bash
    brew install python@3.11
    ```

=== "Windows"
    Download from [python.org](https://www.python.org/downloads/)

### Windows installation fails

**Problem:** PowerShell execution policy blocks the install script

**Solution:** Run PowerShell as Administrator:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try the installation again.

## Next steps

Now that ComfyDock is installed:

* [Quickstart guide](quickstart.md) — Create your first environment in 5 minutes
* [Core concepts](concepts.md) — Understand workspaces, environments, and .cec
* [CLI reference](../cli-reference/environment-commands.md) — Explore all available commands

## Getting help

If you encounter issues during installation:

* Check the [troubleshooting guide](../troubleshooting/common-issues.md)
* Search [GitHub Issues](https://github.com/ComfyDock/comfydock/issues)
* Ask on [GitHub Discussions](https://github.com/ComfyDock/comfydock/discussions)
