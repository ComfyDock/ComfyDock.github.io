# Resolving Node Conflicts

> Understand and fix dependency conflicts when adding or updating custom nodes.

## Overview

Node conflicts occur when two or more custom nodes require incompatible versions of the same Python package. ComfyDock uses UV's dependency resolver to detect these conflicts early and provide actionable solutions.

## What are dependency conflicts?

### Example conflict scenario

Imagine you have:

- **Node A** requires `torch>=2.1.0`
- **Node B** requires `torch==2.0.0`

These requirements are **incompatible** - you can't satisfy both in the same Python environment. ComfyDock detects this during installation and prevents broken environments.

### Why conflicts happen

Common causes:

- **PyTorch version differences** - Nodes built for different CUDA versions
- **Pinned dependencies** - Node hardcodes `package==1.0.0` instead of `package>=1.0.0`
- **Outdated requirements** - Node hasn't updated its `requirements.txt`
- **Conflicting sub-dependencies** - Package A needs X v1, Package B needs X v2

## How ComfyDock detects conflicts

When you run `cfd node add` or `cfd node update`, ComfyDock:

1. **Parses requirements.txt** - Reads the node's dependencies
2. **Runs UV resolution** - Attempts to resolve all dependencies together
3. **Detects conflicts** - UV reports incompatibilities
4. **Displays error** - Shows conflict details with suggested fixes

By default, ComfyDock **prevents** installing nodes that would break your environment.

## Reading conflict error messages

### Basic conflict error

```
✗ Cannot add node 'problematic-node'
  Dependency conflict detected

  torch==2.0.0 (required by problematic-node)
  conflicts with torch>=2.1.0 (required by existing-node)
```

This tells you:

- **What conflicts**: `torch` versions
- **Who needs what**: Each node's requirement
- **Where it comes from**: Which nodes require which versions

### Detailed conflict error

More complex conflicts show:

```
✗ Cannot add node 'complex-node'
  opencv-python conflicts with opencv-python-headless
  pillow>=9.0 conflicts with pillow<9.0

Suggested actions:
  1. Update existing node to compatible version
     → cfd node update existing-node

  2. Remove conflicting node
     → cfd node remove existing-node

  3. Add with conflict override (advanced)
     → cfd node add complex-node --no-test
```

ComfyDock suggests actionable steps based on the conflict type.

## Common conflict types

### PyTorch version conflicts

**Most common conflict** - Different CUDA backends or PyTorch versions.

**Example:**

```
✗ Failed to add node 'cuda-node'
  torch==2.0.1+cu117 conflicts with torch==2.1.0+cu121
```

**Solutions:**

1. **Check your PyTorch backend:**
   ```bash
   # View current PyTorch version
   cfd py list | grep torch
   ```

2. **Recreate environment with matching backend:**
   ```bash
   # If node needs CUDA 11.7
   cfd create new-env --torch-backend cu117
   cfd -e new-env node add cuda-node
   ```

3. **Update the node** (if newer version supports your PyTorch):
   ```bash
   cfd node update cuda-node
   ```

4. **Use constraints** to pin PyTorch version:
   ```bash
   cfd constraint add "torch==2.1.0"
   cfd node add cuda-node
   ```

### Package pinning conflicts

**Example:**

```
✗ Failed to add node 'old-node'
  pillow==8.0.0 (required by old-node)
  conflicts with pillow>=9.0.0 (required by another-node)
```

**Solutions:**

1. **Check if node has updates:**
   ```bash
   # Try adding latest version
   cfd node add old-node@main
   ```

2. **Manually edit requirements.txt** (for development nodes):
   ```bash
   cd custom_nodes/old-node
   # Change pillow==8.0.0 to pillow>=8.0.0
   nano requirements.txt
   cfd node update old-node
   ```

3. **Remove conflicting node:**
   ```bash
   cfd node remove another-node
   cfd node add old-node
   ```

### Directory name conflicts

**Example:**

```
✗ Cannot add node 'comfyui-impact-pack'
  Directory custom_nodes/ComfyUI-Impact-Pack already exists
  Filesystem: https://github.com/yourfork/ComfyUI-Impact-Pack
  Registry:   https://github.com/ltdrdata/ComfyUI-Impact-Pack

Suggested actions:
  1. Remove existing node
     → cfd node remove comfyui-impact-pack

  2. Force overwrite existing directory
     → cfd node add comfyui-impact-pack --force

  3. Rename existing directory
     → mv custom_nodes/ComfyUI-Impact-Pack custom_nodes/ComfyUI-Impact-Pack-old
```

**Solutions:**

Choose based on what you want:

- **Use the registry version:** Follow suggestion 1 (remove) or 2 (force)
- **Keep your fork:** Remove from pyproject.toml, then re-add as git URL:
  ```bash
  cfd node remove comfyui-impact-pack
  cfd node add https://github.com/yourfork/ComfyUI-Impact-Pack --dev
  ```
- **Keep both:** Manually rename one directory (suggestion 3)

### Sub-dependency conflicts

**Example:**

```
✗ Failed to add node 'node-x'
  Package 'requests' requires urllib3>=1.26
  Package 'boto3' requires urllib3<1.27
```

This is a **transitive dependency conflict** - neither node directly requires urllib3, but their dependencies do.

**Solutions:**

1. **Use constraints to force a compatible version:**
   ```bash
   cfd constraint add "urllib3>=1.26,<1.27"
   cfd node add node-x
   ```

2. **Update existing nodes** - newer versions may have relaxed constraints:
   ```bash
   cfd node update boto3-node
   cfd node add node-x
   ```

3. **Skip resolution testing** (risky):
   ```bash
   cfd node add node-x --no-test
   ```

## Resolution strategies

### Interactive resolution (default)

When conflicts occur, ComfyDock shows suggestions:

```
✗ Cannot add node 'new-node'
  torch==2.0.0 conflicts with torch>=2.1.0

Suggested actions:
  1. Update conflicting node
     → cfd node update old-node

  2. Remove conflicting node
     → cfd node remove old-node

What would you like to do? [1/2/cancel]:
```

Choose the appropriate action or cancel.

### Force overwrite (--force)

Override directory conflicts:

```bash
cfd node add comfyui-pack --force
```

This **deletes** the existing directory and re-downloads/re-installs the node. Use when:

- You want the registry version instead of a fork
- The directory is corrupted
- You're okay losing local changes

!!! warning "Destructive operation"
    `--force` permanently deletes the existing directory. Any uncommitted changes are lost.

### Skip resolution testing (--no-test)

Bypass dependency conflict detection:

```bash
cfd node add problematic-node --no-test
```

ComfyDock will:

- **Not** test if dependencies can resolve
- **Still install** the node and its dependencies
- **Hope** UV can handle it at runtime

Use when:

- You know the conflict is a false positive
- The node's requirements.txt is incorrect but the code works
- You'll manually fix dependencies later

!!! danger "Risk of broken environment"
    `--no-test` can result in an environment where `cfd repair` fails. Use carefully and test thoroughly.

## Using constraints to prevent conflicts

Constraints are UV-specific dependency pins that apply globally to your environment.

### What are constraints?

Think of constraints as "meta-dependencies" that restrict what versions UV can choose:

```bash
# Prevent PyTorch from updating past 2.1.x
cfd constraint add "torch>=2.1.0,<2.2.0"

# Pin NumPy to a specific version
cfd constraint add "numpy==1.24.0"
```

Now, any node that requires incompatible versions will be rejected **before** installation.

### Common constraint patterns

**Pin PyTorch backend:**

```bash
# Lock to CUDA 12.1
cfd constraint add "torch==2.1.0+cu121"
```

**Prevent major version updates:**

```bash
# Stay on Pillow 9.x
cfd constraint add "pillow>=9.0.0,<10.0.0"
```

**Force minimum versions:**

```bash
# Ensure modern numpy
cfd constraint add "numpy>=1.24.0"
```

### Managing constraints

**List active constraints:**

```bash
cfd constraint list
```

**Remove a constraint:**

```bash
cfd constraint remove torch
```

See [Python Dependencies: Constraints](../python-dependencies/constraints.md) for more details.

## Practical conflict resolution workflow

### Step 1: Identify the conflict

```bash
cfd node add new-node
```

Read the error message carefully to understand:

- Which packages conflict
- Which nodes require them
- What versions are needed

### Step 2: Check existing nodes

```bash
cfd node list
```

Identify if the conflicting node is:

- **Essential** - Keep it, reject the new node or find alternatives
- **Unused** - Remove it with `cfd node remove`
- **Outdated** - Update it with `cfd node update`

### Step 3: Try suggested actions

ComfyDock's suggested actions are usually the best path:

```
Suggested actions:
  1. Update existing node to compatible version
     → cfd node update old-node
```

Follow the suggestions in order.

### Step 4: Use constraints if needed

For persistent conflicts:

```bash
# Pin the problematic package to a compatible version
cfd constraint add "package>=1.0,<2.0"
cfd node add new-node
```

### Step 5: Test the resolution

After resolving conflicts:

```bash
# Verify environment is consistent
cfd status

# Test ComfyUI loads
cfd run
```

Ensure no errors appear when ComfyUI starts.

## Advanced techniques

### Dependency conflict debugging

**View full UV error output:**

```bash
cfd logs -n 100
```

This shows the complete UV resolution error, not just the summary.

**Manually test resolution:**

```bash
cd ~/comfydock/environments/my-env/.cec
uv pip compile pyproject.toml
```

This runs UV's resolver directly and shows detailed conflict traces.

### Creating conflict-free environments

**Start with a constraint file:**

```bash
# constraints.txt
torch==2.1.0+cu121
pillow>=9.0.0,<10.0.0
numpy>=1.24.0

# Add constraints before adding nodes
cfd constraint add -r constraints.txt
cfd node add node-a node-b node-c
```

This establishes a "compatibility baseline" before installing nodes.

### Splitting environments by compatibility

If nodes are fundamentally incompatible:

```bash
# Environment 1: PyTorch 2.0 nodes
cfd create torch20-env --torch-backend cu117
cfd -e torch20-env node add old-node

# Environment 2: PyTorch 2.1 nodes
cfd create torch21-env --torch-backend cu121
cfd -e torch21-env node add new-node
```

Use separate environments for incompatible node ecosystems.

## When conflicts can't be resolved

### Fundamental incompatibilities

Some nodes simply **cannot** coexist:

- Different major PyTorch versions (1.x vs 2.x)
- CPU-only vs GPU-specific packages
- Conflicting C extensions (opencv-python vs opencv-python-headless)

**Solution:** Use separate environments or choose one node over the other.

### Reporting upstream issues

If a node has overly restrictive requirements:

1. Check the node's GitHub issues for existing reports
2. Test if relaxing the constraint works:
   ```bash
   # Edit custom_nodes/node-name/requirements.txt
   # Change torch==2.0.0 to torch>=2.0.0
   cfd node update node-name
   ```
3. If it works, open a PR to the node's repository
4. Track it as a development node with your fix:
   ```bash
   cfd node add node-name --dev
   ```

## Troubleshooting common scenarios

### "Package not found" after conflict resolution

Sometimes UV can't find a package version that satisfies all constraints.

**Example:**

```
✗ Failed to resolve dependencies
  No version of 'obscure-package' satisfies constraints
```

**Solutions:**

1. **Remove the overly restrictive constraint:**
   ```bash
   cfd constraint list
   cfd constraint remove obscure-package
   ```

2. **Add the package manually with a broader range:**
   ```bash
   cfd py add "obscure-package>=1.0"
   ```

### Environment becomes unsynced after conflict

After resolving conflicts, you might see:

```bash
cfd status
```

```
Environment: my-env ⚠

⚠ Environment out of sync (2 changes)
```

**Solution:**

```bash
cfd repair
```

This synchronizes the environment to match pyproject.toml.

### Circular dependency errors

UV reports circular dependencies:

```
✗ Circular dependency detected: A → B → C → A
```

**Solutions:**

1. **Update all involved nodes** - one may have fixed it:
   ```bash
   cfd node update node-a node-b node-c
   ```

2. **Remove one node** from the cycle:
   ```bash
   cfd node remove node-c
   ```

3. **Report to node maintainers** - this is a packaging bug

## Next steps

<div class="grid cards" markdown>

-   :material-plus-circle: **[Adding Nodes](adding-nodes.md)**

    ---

    Install nodes from registry, GitHub, or local development

-   :material-format-list-bulleted: **[Managing Nodes](managing-nodes.md)**

    ---

    List, update, remove, and prune installed nodes

-   :material-package-variant: **[Python Dependencies](../python-dependencies/py-commands.md)**

    ---

    Manage Python packages and constraints

-   :material-hammer-wrench: **[Environment Repair](../environments/version-control.md#repairing-environments)**

    ---

    Fix sync issues with the repair command

</div>
