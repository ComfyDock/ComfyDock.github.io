# Version Control

> Use git-based version control to track, commit, and rollback changes to your environment configuration. Every environment is a git repository.

## Overview

ComfyDock gives each environment its own git repository in the `.cec/` directory. This tracks:

* **Custom nodes** — Which nodes are installed and their versions
* **Python dependencies** — Packages from `pyproject.toml`
* **Workflows** — Workflow JSON files you've created or modified
* **Model references** — Model download URLs and importance settings
* **Constraints** — Version pins and dependency constraints

Changes are tracked automatically — you just commit when ready.

## The .cec directory

Each environment has a `.cec/` directory:

```
~/comfydock/environments/my-env/.cec/
├── .git/                   # Git repository
├── pyproject.toml          # Dependencies and nodes
├── uv.lock                 # Locked dependency versions
├── workflows/              # Tracked workflow files
└── .python-version         # Python version pin
```

This entire directory is version controlled. When you commit, you're committing changes to these files.

## Checking for changes

See what's changed since your last commit:

```bash
cfd status
```

**Clean environment:**

```
Environment: my-env ✓

✓ No workflows
✓ No uncommitted changes
```

**With uncommitted changes:**

```
Environment: my-env

⚠ Uncommitted changes:

  Custom Nodes:
    + comfyui-impact-pack

  Python Packages:
    + ultralytics (any)

💡 Next:
  Commit changes: cfd commit -m "<message>"
```

## Committing changes

### Basic commit

Save your current environment state:

```bash
cfd commit -m "Added impact pack for face detailing"
```

**Output:**

```
📋 Analyzing workflows...
✅ Commit successful: Added impact pack for face detailing
  • Added 1 workflow(s)
```

### Auto-generated commit message

Let ComfyDock generate a message:

```bash
cfd commit
```

Generates messages like:

* "Update workflows"
* "Add custom nodes"
* "Update dependencies"

!!! tip "Descriptive messages"
    Use descriptive commit messages for easier version navigation:
    ```bash
    cfd commit -m "Added IPAdapter nodes for style transfer"
    cfd commit -m "Pinned torch to 2.4.1 for stability"
    cfd commit -m "Removed unused video nodes"
    ```

### What gets committed

A commit captures:

1. **Node changes** — Additions, removals, updates
2. **Dependency changes** — Python packages added/removed/updated
3. **Workflow changes** — New, modified, or deleted workflow files
4. **Constraint changes** — Version pins added/removed
5. **Model metadata** — Download URLs and importance settings

**Example commit:**

```bash
# Add a node
cfd node add comfyui-impact-pack

# Check status
cfd status
# Shows: + comfyui-impact-pack under Custom Nodes

# Commit
cfd commit -m "Added impact pack"
```

### Workflow issues and commits

ComfyDock blocks commits if workflows have unresolved issues:

**Blocked commit:**

```bash
cfd commit -m "Update workflow"
```

**Output:**

```
📋 Analyzing workflows...

⚠ Cannot commit - workflows have unresolved issues:

  • portrait.json: 2 nodes unresolved, 1 models not found

💡 Options:
  1. Resolve issues: cfd workflow resolve "portrait"
  2. Force commit: cfd commit -m 'msg' --allow-issues
```

**Option 1: Resolve first (recommended)**

```bash
# Fix the issues
cfd workflow resolve portrait

# Then commit
cfd commit -m "Updated portrait workflow"
```

**Option 2: Force commit**

```bash
# Commit anyway (not recommended)
cfd commit -m "WIP: portrait workflow" --allow-issues
```

!!! warning "Allow issues flag"
    Using `--allow-issues` commits broken workflows. Only use this for work-in-progress commits. Fix issues before sharing the environment.

## Viewing commit history

### Compact format (default)

```bash
cfd commit log
```

**Output:**

```
Version history for environment 'my-env':

v3: Removed unused video nodes
v2: Added IPAdapter for style transfer
v1: Added impact pack for face detailing

Use 'cfd rollback <version>' to restore to a specific version
```

### Verbose format

See full details:

```bash
cfd commit log --verbose
```

**Output:**

```
Version history for environment 'my-env':

Version: v3
Message: Removed unused video nodes
Date:    2025-11-03 14:23:45
Commit:  a1b2c3d4


Version: v2
Message: Added IPAdapter for style transfer
Date:    2025-11-03 12:10:33
Commit:  e5f6g7h8


Version: v1
Message: Added impact pack for face detailing
Date:    2025-11-03 09:15:22
Commit:  i9j0k1l2

Use 'cfd rollback <version>' to restore to a specific version
```

## Rolling back changes

### Discard uncommitted changes

Undo all changes since last commit:

```bash
cfd rollback
```

**Confirmation prompt:**

```
⏮ Discarding uncommitted changes in environment 'my-env'

This will discard all changes since your last commit:
  • Custom nodes added/removed
  • Dependencies changed
  • Workflows modified

Continue? (y/N):
```

Type `y` and press Enter.

**Output:**

```
✓ Rollback complete

Uncommitted changes have been discarded
• Environment is now clean and matches the last commit
• Run 'cfd commit log' to see version history
```

**Skip confirmation:**

```bash
cfd rollback --yes
```

### Rollback to specific version

Restore environment to a previous commit:

```bash
# Rollback to v2
cfd rollback v2
```

**Confirmation prompt:**

```
⏮ Rolling back environment 'my-env' to v2

This will:
  • Restore pyproject.toml to v2
  • Reset workflows to v2 state
  • Update environment to match v2 dependencies

Current state will be lost unless committed first.

Continue? (y/N):
```

**Output:**

```
✓ Rollback complete

Environment is now at version v2
• Run 'cfd commit -m "message"' to save any new changes
• Run 'cfd commit log' to see version history
```

**What happens:**

1. Git checks out the specified version in `.cec/`
2. `pyproject.toml` is restored to that version
3. Workflows are restored to that version
4. Environment is auto-repaired to match the restored configuration

**Skip confirmation:**

```bash
cfd rollback v2 --yes
```

## Pushing to remotes

Share your environment with others via git remotes.

### Adding a remote

```bash
# Add a remote repository
cfd remote add origin https://github.com/username/my-env.git
```

### Pushing commits

```bash
cfd push origin
```

**Pre-flight checks:**

```
✗ You have uncommitted changes

💡 Commit first:
   cfd commit -m 'your message'
```

After committing:

```bash
cfd push origin
```

**Output:**

```
📤 Pushing to origin...
   ✓ Pushed commits to origin

💾 Remote: https://github.com/username/my-env.git
```

### Force push

Overwrite remote history (use with caution):

```bash
cfd push origin --force
```

!!! warning "Force push"
    Only force push if you're sure. This rewrites history and can cause issues for collaborators.

## Pulling from remotes

Update your environment from a remote repository.

### Basic pull

```bash
cfd pull origin
```

**Pre-flight checks:**

```
✗ You have uncommitted changes

💡 Options:
  • Commit: cfd commit -m 'message'
  • Discard: cfd rollback
  • Force: cfd pull origin --force
```

After committing or discarding:

```bash
cfd pull origin
```

**Output:**

```
📥 Pulling from origin...
  [1/2] Installing comfyui-controlnet-aux... ✓
  [2/2] Installing comfyui-ipadapter-plus... ✓

✓ Pulled changes from origin
   • Installed 2 node(s)

⚙️  Environment synced successfully
```

**What happens:**

1. Pulls latest commits from remote
2. Merges changes into `.cec/`
3. Automatically runs `cfd repair` to sync environment
4. Installs missing nodes
5. Downloads missing models (if configured)

### Force pull

Discard local changes and pull:

```bash
cfd pull origin --force
```

### Handling merge conflicts

If both you and a remote have changes:

```
✗ Merge conflict detected

💡 To resolve:
   1. cd ~/comfydock/environments/my-env/.cec
   2. git status  # See conflicted files
   3. Edit conflicts and resolve
   4. git add <resolved-files>
   5. git commit
   6. cfd repair  # Sync environment
```

**Resolution steps:**

```bash
# Navigate to .cec
cd ~/comfydock/environments/my-env/.cec

# See conflicts
git status

# Edit conflicted files (usually pyproject.toml)
# Look for conflict markers: <<<<<<<, =======, >>>>>>>
# Keep the changes you want

# Stage resolved files
git add pyproject.toml

# Commit the merge
git commit -m "Merged remote changes"

# Return to workspace
cd ~/comfydock

# Sync environment
cfd repair
```

## Repairing environments

Sync environment filesystem to match `pyproject.toml`:

```bash
cfd repair
```

**When to use:**

* After manual edits to `pyproject.toml`
* After `git pull` or `rollback`
* When nodes aren't loading
* After resolving git conflicts

**Example:**

```bash
# Manually edit .cec/pyproject.toml
# Add a dependency or change a node URL

# Sync environment
cfd repair
```

**Output:**

```
🔧 Syncing environment to pyproject.toml...

Preview:
  Nodes to install:
    + comfyui-manager

  Python packages to install:
    + requests (>=2.31.0)

Continue? (y/N): y

  [1/1] Installing comfyui-manager... ✓

✅ Environment synced successfully
   • Installed 1 node(s)
   • Installed 1 package(s)
```

**Skip confirmation:**

```bash
cfd repair --yes
```

## Common workflows

### Experiment and commit

```bash
# Make changes
cfd node add experimental-node

# Test it
cfd run
# Try it out...

# Good? Commit
cfd commit -m "Added experimental node - works great"

# Bad? Rollback
cfd rollback
```

### Feature branch workflow

```bash
# Create environment for feature
cfd create feature-xyz --use

# Make changes
cfd node add new-feature-node
cfd commit -m "Added feature node"

# More changes
cfd node add another-node
cfd commit -m "Added supporting node"

# Test
cfd run

# Good? Push
cfd remote add origin https://github.com/me/feature-xyz.git
cfd push origin

# Share link with team
```

### Safe experimentation

```bash
# Current state
cfd commit -m "Stable state before experiment"

# Try something risky
cfd node add untested-node
cfd run
# Doesn't work...

# Rollback
cfd rollback

# Back to stable state
```

### Team collaboration

**Team member 1:**

```bash
# Create environment
cfd create project-x

# Add nodes
cfd node add comfyui-ipadapter-plus
cfd commit -m "Initial setup with IPAdapter"

# Push
cfd remote add origin https://github.com/team/project-x.git
cfd push origin
```

**Team member 2:**

```bash
# Import from git
cfd import https://github.com/team/project-x.git --name project-x

# Make changes
cfd node add comfyui-controlnet-aux
cfd commit -m "Added ControlNet support"

# Push
cfd push origin
```

**Team member 1:**

```bash
# Pull changes
cfd pull origin

# Nodes are auto-installed
# Continue working...
```

## Version control best practices

### Commit early and often

```bash
# After each logical change
cfd node add some-node
cfd commit -m "Added some-node for X feature"

# Not after 10 changes
cfd node add node1
cfd node add node2
# ... 8 more changes
cfd commit -m "Updated everything"  # Bad!
```

### Use descriptive messages

**Good:**

* "Added ComfyUI-Manager for node management"
* "Pinned PyTorch to 2.4.1 for CUDA 12.8 compatibility"
* "Removed deprecated ControlNet nodes"
* "Updated portrait workflow with better face detailing"

**Bad:**

* "Update"
* "Changes"
* "WIP"
* "asdf"

### Test before committing

```bash
# Make changes
cfd node add new-node

# Test
cfd run
# Verify it works...

# Good? Commit
cfd commit -m "Added new-node"

# Bad? Fix first or rollback
```

### Commit workflow changes separately

```bash
# Bad: mixing concerns
cfd node add ipadapter
# Edit workflow in ComfyUI...
cfd commit -m "Updated everything"

# Good: separate commits
cfd node add ipadapter
cfd commit -m "Added IPAdapter node"
# Edit workflow...
cfd commit -m "Updated portrait workflow to use IPAdapter"
```

## Troubleshooting

### Can't commit - no changes detected

**Symptom:** `✓ No changes to commit`

**Cause:** Nothing has changed in `.cec/` since last commit

**Check:**

```bash
cfd status
# Should show uncommitted changes if any exist
```

### Rollback doesn't work

**Symptom:** Rollback command fails or doesn't restore properly

**Solutions:**

```bash
# Check git status manually
cd ~/comfydock/environments/my-env/.cec
git status

# Force clean
git reset --hard HEAD

# Return and repair
cd ~/comfydock
cfd repair
```

### Push rejected

**Symptom:** Remote rejects push

**Cause:** Remote has commits you don't have locally

**Solution:**

```bash
# Pull first
cfd pull origin

# Resolve conflicts if any
# Then push
cfd push origin
```

### Lost changes after rollback

**Symptom:** Rolled back but want changes back

**Solution:**

```bash
# Git never forgets - find your commit
cd ~/comfydock/environments/my-env/.cec
git reflog

# Find the commit hash
# Restore it
git checkout <commit-hash>

# Or cherry-pick specific changes
git cherry-pick <commit-hash>

# Return to comfydock
cd ~/comfydock
cfd repair
```

## Next steps

Master version control, then explore:

* **[Custom Nodes](../custom-nodes/adding-nodes.md)** — Install and manage extensions
* **[Workflows](../workflows/workflow-resolution.md)** — Resolve dependencies automatically
* **[Collaboration](../collaboration/git-remotes.md)** — Share environments with team

## See also

* [Git Remotes](../collaboration/git-remotes.md) — Detailed remote management
* [Export & Import](../collaboration/export-import.md) — Tarball-based sharing
* [CLI Reference](../../cli-reference/environment-commands.md) — Complete command docs
