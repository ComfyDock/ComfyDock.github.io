# Export and Import

Share complete ComfyUI environments as portable tarballs that include configuration, workflows, and development nodes.

## Overview

Export/import allows you to package an entire environment into a single `.tar.gz` file that can be shared offline. This is ideal for:

- **One-time sharing**: Send environments to colleagues or clients
- **Backup and archival**: Save environment snapshots for later restoration
- **CI/CD artifacts**: Deploy tested environments to production
- **Template distribution**: Share starter environments with the community

Unlike git remotes (which require continuous sync), export creates a self-contained package that works offline.

---

## Exporting an Environment

Export packages your environment configuration, workflows, and development nodes into a tarball.

### Basic Export

Export the active environment:

```bash
cfd export
```

**Output:**

```
📦 Exporting environment: my-env

✅ Export complete: my-env_export_20250109.tar.gz (2.3 MB)

Share this file to distribute your complete environment!
```

By default, the tarball is created in the current directory with a timestamp.

### Custom Output Path

Specify where to save the export:

```bash
cfd export ~/exports/my-workflow.tar.gz
```

### Export Specific Environment

Use the `-e` flag to export a non-active environment:

```bash
cfd -e production export production.tar.gz
```

---

## What Gets Exported

The tarball contains everything needed to recreate your environment:

```
environment_export.tar.gz
├── pyproject.toml          # Environment configuration
│                           # - ComfyUI version
│                           # - Custom nodes list
│                           # - Model metadata
│                           # - Workflow dependencies
├── uv.lock                 # Locked Python dependencies
├── .python-version         # Python version constraint
├── workflows/              # All committed workflows
│   ├── workflow1.json
│   └── workflow2.json
└── dev_nodes/              # Development node source code
    └── my-custom-node/     # (Only nodes with source="development")
```

!!! note "Only Committed Content"
    Export only includes committed workflows and configuration. Uncommitted changes are excluded to ensure consistency.

---

## Export Validation

ComfyDock validates your export to ensure recipients can recreate the environment successfully.

### Model Source Check

Before exporting, ComfyDock checks if all models have download sources:

```bash
cfd export
```

**Output:**

```
📦 Exporting environment: my-env

⚠️  Export validation:

3 model(s) have no source URLs.

  • sd_xl_base_1.0.safetensors
    Used by: txt2img, img2img

  • control_v11p_sd15_openpose.pth
    Used by: pose_workflow

  • vae-ft-mse-840000.safetensors
    Used by: txt2img

  ... and 0 more

⚠️  Recipients won't be able to download these models automatically.
   Add sources: comfydock model add-source

Continue export? (y/N):
```

**Options:**

- **Add sources first** (recommended): Use `cfd model add-source` to add download URLs
- **Continue anyway**: Recipients will need to manually provide the models
- **Skip validation**: Use `--allow-issues` to bypass the check

### Adding Model Sources

Add download URLs so recipients can auto-download models:

```bash
# Interactive mode - walks through all models without sources
cfd model add-source

# Direct mode - add source to specific model
cfd model add-source sd_xl_base <civitai-url>
```

!!! tip "Interactive Mode"
    Interactive mode is the fastest way to add sources for multiple models. It shows each model and prompts for a URL.

See [Adding Model Sources](../models/adding-sources.md) for details.

### Uncommitted Changes Check

Export fails if you have uncommitted workflows or git changes:

```
✗ Cannot export: uncommitted changes detected

📋 Uncommitted workflows:
  • new_workflow
  • modified_workflow

💡 Commit first:
   comfydock commit -m 'Pre-export checkpoint'
```

This ensures the export matches a specific version in your history.

**Fix:**

```bash
cfd commit -m "Prepare for export"
cfd export
```

---

## Importing an Environment

Import creates a new environment from a tarball or git repository.

### Import from Tarball

Import a local tarball file:

```bash
cfd import environment.tar.gz
```

**Interactive prompts:**

```
📦 Importing environment from environment.tar.gz

Environment name: my-imported-env

Model download strategy:
  1. all      - Download all models with sources
  2. required - Download only required models
  3. skip     - Skip all downloads (can resolve later)
Choice (1-3) [1]: 1

🔧 Initializing environment...
   Cloning ComfyUI v0.2.7
   Installing Python dependencies
   Installing dependency groups

📝 Setting up workflows...
   Copied: txt2img

📦 Syncing custom nodes...
   Installed: rgthree-comfy

🔄 Resolving models

⬇️  Downloading 3 model(s)...

[1/3] sd_xl_base_1.0.safetensors
Downloading... 6533.8 MB / 6633.5 MB (98%)  ✓ Complete

[2/3] control_v11p_sd15_openpose.pth
Downloading... 729.4 MB / 729.4 MB (100%)  ✓ Complete

✅ Downloaded 2 model(s)

✅ Import complete: my-imported-env
   Environment ready to use!

Activate with: comfydock use my-imported-env
```

### Import from Git Repository

Import directly from a git URL:

```bash
cfd import https://github.com/user/comfy-workflow
```

This clones the repository, analyzes the `.cec` configuration, and creates the environment.

**Specify branch or tag:**

```bash
cfd import https://github.com/user/comfy-workflow --branch v1.0
```

**Import from subdirectory:**

```bash
cfd import https://github.com/user/workflows#environments/production
```

The `#subdirectory` syntax imports only a specific path within the repository.

### Non-Interactive Import

Skip prompts by providing all options via flags:

```bash
cfd import environment.tar.gz \
    --name production \
    --torch-backend cu128 \
    --use
```

**Flags:**

- `--name NAME`: Environment name (skip prompt)
- `--torch-backend BACKEND`: PyTorch backend (auto, cpu, cu128, cu126, rocm6.3, xpu)
- `--use`: Set as active environment after import

---

## Model Download Strategies

During import, you choose how to handle model downloads:

### Strategy: All (Default)

Downloads all models that have source URLs:

```
Choice (1-3) [1]: 1
```

- **Downloads**: All models with sources
- **Skips**: Models without sources (creates download intents)
- **Best for**: Complete environment setup

### Strategy: Required

Downloads only models marked as "required":

```
Choice (1-3) [1]: 2
```

- **Downloads**: Required models only
- **Skips**: Flexible and optional models
- **Best for**: Quick setup, storage constraints

Model criticality is set using `cfd workflow model importance`.

### Strategy: Skip

Skips all downloads during import:

```
Choice (1-3) [1]: 3
```

- **Downloads**: None
- **Creates**: Download intents for all models
- **Best for**: Offline imports, manual model management

You can resolve downloads later:

```bash
cfd -e my-env workflow resolve --all
```

---

## Import Analysis Preview

Before importing, ComfyDock analyzes what will be installed.

### Import Breakdown

The import process shows what will be set up:

```
🔧 Initializing environment...
   Cloning ComfyUI v0.2.7
   Installing Python dependencies
   Installing dependency groups
      Installing main... ✓
      Installing torch-cu128... ✓
      Installing comfyui... ✓
      Installing optional (optional)... ✗

⚠️  Some optional dependency groups failed to install:
   ✗ optional

Some functionality may be degraded or some nodes may not work properly.
The environment will still function with reduced capabilities.
```

### Dependency Group Failures

Optional dependency groups may fail without breaking the import:

- **Main groups**: Must succeed (fails import if they fail)
- **Optional groups**: Allowed to fail (shows warning)

Common reasons for failures:

- Platform-specific packages not available
- Network issues downloading packages
- Version conflicts in optional dependencies

The environment remains usable with reduced functionality.

---

## Development Nodes

Export includes source code for development nodes (nodes with `source = "development"`).

### What Gets Included

Development node source code is bundled in the tarball:

```
dev_nodes/
└── my-custom-node/
    ├── __init__.py
    ├── nodes.py
    └── requirements.txt
```

**Filtering:**

- Excludes `__pycache__/` directories
- Excludes `.pyc` files
- Includes all other source files

### Import Behavior

During import, development nodes are:

1. Extracted to `.cec/dev_nodes/`
2. Symlinked to `ComfyUI/custom_nodes/`
3. Dependencies installed from `requirements.txt`

This allows sharing custom nodes under development without publishing to a registry.

---

## Troubleshooting

### Models Without Sources

**Problem:** Export warns about models without download URLs.

```
⚠️  3 model(s) have no source URLs.
```

**Solutions:**

1. **Add sources** (recommended):
   ```bash
   cfd model add-source
   ```

2. **Export anyway**:
   ```bash
   cfd export --allow-issues
   ```

   Recipients will need to manually provide the models.

3. **Document manual steps**: Include instructions for recipients to download models manually.

---

### CivitAI Authentication Errors

**Problem:** Import fails with `401 Unauthorized` for CivitAI downloads.

```
✗ Failed: 401 Unauthorized
```

**Solution:** Add your CivitAI API key:

```bash
cfd config --civitai-key <your-api-key>
```

Get your key from: [https://civitai.com/user/account](https://civitai.com/user/account)

Then retry the import or resolve manually:

```bash
cfd -e my-env workflow resolve --all
```

---

### Download Failures

**Problem:** Some models fail to download during import.

```
⚠️  2 model(s) failed:
   • sd_xl_base_1.0.safetensors: Connection timeout
   • controlnet.pth: 404 Not Found
```

**What Happens:**

- Failed downloads are saved as "download intents"
- Environment import continues
- Workflows may be incomplete

**Solutions:**

1. **Retry download**:
   ```bash
   cfd -e my-env workflow resolve <workflow-name>
   ```

2. **Check model sources**:
   ```bash
   cfd -e my-env model index show sd_xl_base
   ```

3. **Manual download**: Download the model manually and place it in the models directory, then sync:
   ```bash
   cfd model index sync
   ```

---

### Import Fails Mid-Process

**Problem:** Import fails during environment setup.

**What Happens:**

- Partial environment is created
- May have incomplete dependencies or nodes

**Solution:**

1. **Delete the failed environment**:
   ```bash
   cfd delete <env-name>
   ```

2. **Check error message** for specific cause (network, disk space, etc.)

3. **Retry import** after fixing the issue:
   ```bash
   cfd import environment.tar.gz
   ```

---

## Best Practices

### Before Exporting

1. **Commit all changes**: Ensure workflows are committed
   ```bash
   cfd commit -m "Finalize environment for export"
   ```

2. **Add model sources**: Use interactive mode to add all sources
   ```bash
   cfd model add-source
   ```

3. **Test the export**: Import it locally to verify completeness
   ```bash
   cfd export test.tar.gz
   cfd import test.tar.gz --name test-import
   ```

4. **Document custom setup**: If models can't be auto-downloaded, provide manual instructions

### For Recipients

1. **Review import analysis**: Check what will be installed during import preview

2. **Choose appropriate strategy**: Select model download strategy based on needs
   - **Full setup**: Use "all"
   - **Quick start**: Use "required"
   - **Offline/manual**: Use "skip"

3. **Verify hardware compatibility**: Check PyTorch backend matches your GPU
   ```bash
   cfd import env.tar.gz --torch-backend cu128
   ```

4. **Check disk space**: Imports can be large (models + dependencies)

### Naming Conventions

- **Descriptive names**: `project-v1.0-export.tar.gz`
- **Version tags**: Include version or date for clarity
- **Environment type**: Indicate purpose (dev, prod, test)

---

## Next Steps

- [Git Remotes](git-remotes.md) - Continuous collaboration with push/pull
- [Team Workflows](team-workflows.md) - Best practices for team collaboration
- [Adding Model Sources](../models/adding-sources.md) - Ensure models are downloadable
- [Workflow Resolution](../workflows/workflow-resolution.md) - Resolve missing dependencies

---

## Summary

Export/import enables offline environment sharing:

- **Export** packages environments as tarballs with validation
- **Import** creates environments from tarballs or git URLs
- **Model strategies** control download behavior during import
- **Development nodes** are bundled as source code
- **Validation** ensures recipients can recreate environments successfully

Use export/import for one-time sharing, backups, or template distribution. For continuous team collaboration, see [Git Remotes](git-remotes.md).
