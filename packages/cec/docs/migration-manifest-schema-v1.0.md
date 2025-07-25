# ComfyUI Migration Manifest Schema v1.0 - Design Specification

## 1. Overview

The ComfyUI Migration Manifest (`comfyui_migration.json`) is a minimal, action-oriented JSON file designed to contain exactly the information needed to recreate a ComfyUI environment. Every field maps directly to UV commands, ensuring straightforward implementation and maintaining a file size under 5KB.

## 2. Design Principles

1. **Minimalism**: Only include data that directly affects environment recreation
2. **Actionability**: Every field must map to a specific UV command or action
3. **Determinism**: Given a manifest, the resulting environment must be predictable
4. **Size Efficiency**: Target <3KB typical size, hard limit 5KB
5. **Forward Compatibility**: Design allows additions without breaking v1.0 parsers

## 3. Complete Schema Definition

### 3.1 Root Object

```typescript
interface ComfyUIMigrationManifest {
  schema_version: "1.0";                    // REQUIRED: Exact string "1.0"
  metadata?: ManifestMetadata;              // OPTIONAL: Capture metadata
  system_info: SystemInfo;                  // REQUIRED: Runtime requirements
  custom_nodes: CustomNode[];               // REQUIRED: Array (can be empty)
  dependencies: Dependencies;               // REQUIRED: Package specifications
  platform_overrides?: PlatformOverrides;   // OPTIONAL: Platform-specific settings
}
```

### 3.2 Metadata Section (Optional)

```typescript
interface ManifestMetadata {
  generated_at?: string;        // ISO 8601 timestamp (e.g., "2025-01-15T10:30:00Z")
  generator_version?: string;   // Version of capture tool (e.g., "1.0.0")
  source_path?: string;         // Original ComfyUI path (informational only)
  capture_duration_ms?: number; // Time taken to capture (debugging)
}
```

**Size Impact**: ~200 bytes when included
**UV Mapping**: None (informational only)

### 3.3 System Info Section (Required)

```typescript
interface SystemInfo {
  python_version: string;        // REQUIRED: Exact M.m.p (e.g., "3.11.7")
  cuda_version: string | null;   // REQUIRED: null for CPU, "12.1" format for GPU
  torch_version: string;         // REQUIRED: Full version string (e.g., "2.1.0+cu121")
  comfyui_version: string;       // REQUIRED: Git tag or commit (e.g., "v0.3.47" or "abc1234")
  platform?: string;             // OPTIONAL: "linux", "darwin", "win32"
  architecture?: string;         // OPTIONAL: "x86_64", "arm64"
}
```

**Validation Rules**:
- `python_version`: Must match regex `^\d+\.\d+\.\d+$`
- `cuda_version`: If not null, must match regex `^\d+\.\d+$`
- `torch_version`: Must include base version, may include build suffix
- `comfyui_version`: Prefer tags (v-prefixed) over commits

**UV Mapping**:
- `python_version` → `uv venv --python {version}`
- `cuda_version` + `torch_version` → Determines PyTorch index URL

### 3.4 Custom Nodes Section (Required Array)

```typescript
interface CustomNode {
  name: string;                  // REQUIRED: Directory name in custom_nodes/
  install_method: InstallMethod; // REQUIRED: How to install
  url: string;                   // REQUIRED: Installation source
  ref?: string;                  // OPTIONAL: Git ref (branch/tag/commit)
  has_post_install?: boolean;    // OPTIONAL: Has install.py or setup.py
  has_requirements?: boolean;    // OPTIONAL: Has requirements.txt
  fallback_url?: string;         // OPTIONAL: Alternative source
  install_order?: number;        // OPTIONAL: Priority (lower = earlier)
}

type InstallMethod = "archive" | "git" | "local" | "managed";
```

**Field Details**:

- **name**: Exact directory name as it appears in `custom_nodes/`
  - Examples: "ComfyUI-Manager", "ComfyUI-Impact-Pack"
  - Validation: No path separators, valid directory name

- **install_method**:
  - `"archive"`: Direct download and extract (tar.gz, zip)
  - `"git"`: Git clone installation
  - `"local"`: Local directory copy (path in url)
  - `"managed"`: Installed via ComfyUI-Manager

- **url**: Source location based on install_method
  - archive: `"https://github.com/owner/repo/archive/commit.tar.gz"`
  - git: `"https://github.com/owner/repo.git"`
  - local: `"/absolute/path/to/node"` (migration warning)
  - managed: Registry identifier or GitHub URL

- **ref**: Git reference (only used with git method)
  - Examples: `"main"`, `"v1.0.0"`, `"abc1234"`

- **has_post_install**: Indicates post-installation scripts
  - UV Action: Run `install.py` or `setup.py` after extraction

- **has_requirements**: Indicates requirements.txt presence
  - UV Action: `uv pip install -r custom_nodes/{name}/requirements.txt`

### 3.5 Dependencies Section (Required)

```typescript
interface Dependencies {
  packages: PackageMap;                // REQUIRED: PyPI packages
  pytorch?: PyTorchSpec;               // OPTIONAL: PyTorch packages
  git_packages?: GitPackage[];         // OPTIONAL: Git dependencies  
  editable?: EditablePackage[];        // OPTIONAL: Development installs
  local_packages?: LocalPackage[];     // OPTIONAL: Local wheel/sdist files
  index_urls?: string[];               // OPTIONAL: Additional package indices
}

interface PackageMap {
  [packageName: string]: string;       // Package name → exact version
}

interface PyTorchSpec {
  index_url: string;                   // PyTorch index URL
  packages: PackageMap;                // torch, torchvision, torchaudio
}

interface GitPackage {
  url: string;                         // Git repository URL
  ref?: string;                        // Git ref (branch/tag/commit)
  subdirectory?: string;               // Subdirectory containing setup.py
  egg_name?: string;                   // Package name for pip
}

interface EditablePackage {
  path: string;                        // Absolute or relative path
  egg_name?: string;                   // Package name
}

interface LocalPackage {
  path: string;                        // Path to .whl or .tar.gz
  hash?: string;                       // SHA256 hash for verification
}
```

**Examples**:

```json
{
  "packages": {
    "numpy": "1.24.3",
    "pillow": "10.0.0",
    "opencv-python": "4.8.0.74"
  },
  "pytorch": {
    "index_url": "https://download.pytorch.org/whl/cu121",
    "packages": {
      "torch": "2.1.0",
      "torchvision": "0.16.0",
      "torchaudio": "2.1.0"
    }
  },
  "git_packages": [
    {
      "url": "https://github.com/user/repo.git",
      "ref": "main",
      "egg_name": "mypackage"
    }
  ]
}
```

**UV Mapping**:
- `packages` → `uv pip install {package}=={version}`
- `pytorch` → `uv pip install --index-url {index_url} {packages}`
- `git_packages` → `uv pip install git+{url}@{ref}#egg={egg_name}`
- `editable` → `uv pip install -e {path}`

### 3.6 Platform Overrides Section (Optional)

```typescript
interface PlatformOverrides {
  [platform: string]: PlatformSpecific;
}

interface PlatformSpecific {
  packages?: PackageMap;               // Platform-specific packages
  exclude_packages?: string[];         // Packages to skip
  environment?: EnvironmentVars;       // Environment variables
}

interface EnvironmentVars {
  [key: string]: string;
}
```

**Platform Keys**: 
- `"linux"`, `"darwin"`, `"win32"`
- `"linux-x86_64"`, `"linux-aarch64"` (architecture-specific)

**Example**:
```json
{
  "win32": {
    "packages": {
      "windows-curses": "2.3.1"
    }
  },
  "darwin": {
    "exclude_packages": ["nvidia-cudnn-cu11"]
  }
}
```

## 4. Size Optimization Strategies

### 4.1 Field Minimization Rules

1. **Omit null/empty values**: Don't include empty arrays or null fields
2. **Use short keys**: Internal keys can be shortened in v2.0 if needed
3. **Version deduplication**: Consider version patterns for common versions
4. **URL patterns**: Use templates for common GitHub URLs (future)

### 4.2 Typical Size Breakdown

```
Base structure:           ~100 bytes
System info:              ~150 bytes
10 packages:              ~300 bytes
5 custom nodes:           ~800 bytes
PyTorch spec:             ~200 bytes
------------------------
Typical total:            ~1,550 bytes
```

## 5. Validation Rules

### 5.1 Required Field Validation

```python
def validate_manifest(manifest: dict) -> ValidationResult:
    errors = []
    
    # Check required root fields
    if manifest.get("schema_version") != "1.0":
        errors.append("Invalid or missing schema_version")
    
    if "system_info" not in manifest:
        errors.append("Missing system_info")
    else:
        # Validate system_info subfields
        validate_system_info(manifest["system_info"], errors)
    
    if "dependencies" not in manifest:
        errors.append("Missing dependencies")
    elif "packages" not in manifest["dependencies"]:
        errors.append("Missing dependencies.packages")
    
    if "custom_nodes" not in manifest:
        errors.append("Missing custom_nodes array")
    
    return ValidationResult(errors)
```

### 5.2 Version Format Validation

- **Python version**: `^\d+\.\d+\.\d+$`
- **Package versions**: Exact versions only (no ranges, no wildcards)
- **Git refs**: Valid Git reference format
- **URLs**: Must include scheme (https://, git://, file://)

### 5.3 Size Constraints

- **Total file size**: Must not exceed 5,120 bytes (5KB)
- **URL length**: Individual URLs should not exceed 500 characters
- **Package count**: Warn if >500 packages (unusual)

## 6. UV Command Generation

### 6.1 Installation Order

```python
def generate_uv_commands(manifest: dict) -> List[str]:
    commands = []
    
    # 1. Create venv with specific Python
    commands.append(f"uv venv --python {manifest['system_info']['python_version']}")
    
    # 2. Install PyTorch if specified
    if pytorch := manifest['dependencies'].get('pytorch'):
        packages = [f"{k}=={v}" for k, v in pytorch['packages'].items()]
        commands.append(f"uv pip install --index-url {pytorch['index_url']} {' '.join(packages)}")
    
    # 3. Install regular packages
    packages = [f"{k}=={v}" for k, v in manifest['dependencies']['packages'].items()]
    if packages:
        commands.append(f"uv pip install {' '.join(packages)}")
    
    # 4. Install git packages
    for git_pkg in manifest['dependencies'].get('git_packages', []):
        cmd = f"uv pip install git+{git_pkg['url']}"
        if ref := git_pkg.get('ref'):
            cmd += f"@{ref}"
        if egg := git_pkg.get('egg_name'):
            cmd += f"#egg={egg}"
        commands.append(cmd)
    
    # 5. Install custom nodes
    nodes = sorted(manifest['custom_nodes'], 
                   key=lambda n: n.get('install_order', 999))
    for node in nodes:
        commands.extend(generate_node_install_commands(node))
    
    return commands
```

## 7. Example Manifests

### 7.1 Minimal CPU Environment

```json
{
  "schema_version": "1.0",
  "system_info": {
    "python_version": "3.11.7",
    "cuda_version": null,
    "torch_version": "2.1.0+cpu",
    "comfyui_version": "v0.3.47"
  },
  "custom_nodes": [],
  "dependencies": {
    "packages": {
      "torch": "2.1.0",
      "torchvision": "0.16.0",
      "numpy": "1.24.3",
      "pillow": "10.0.0"
    }
  }
}
```
**Size**: ~400 bytes

### 7.2 Standard GPU Environment

```json
{
  "schema_version": "1.0",
  "system_info": {
    "python_version": "3.11.7",
    "cuda_version": "12.1",
    "torch_version": "2.1.0+cu121",
    "comfyui_version": "v0.3.47"
  },
  "custom_nodes": [
    {
      "name": "ComfyUI-Manager",
      "install_method": "archive",
      "url": "https://github.com/ltdrdata/ComfyUI-Manager/archive/2f377ef.tar.gz",
      "has_post_install": true
    }
  ],
  "dependencies": {
    "pytorch": {
      "index_url": "https://download.pytorch.org/whl/cu121",
      "packages": {
        "torch": "2.1.0",
        "torchvision": "0.16.0",
        "torchaudio": "2.1.0"
      }
    },
    "packages": {
      "numpy": "1.24.3",
      "opencv-python": "4.8.0.74",
      "pillow": "10.0.0",
      "scipy": "1.11.4"
    }
  }
}
```
**Size**: ~850 bytes

### 7.3 Complex Development Environment

```json
{
  "schema_version": "1.0",
  "metadata": {
    "generated_at": "2025-01-15T10:30:00Z",
    "generator_version": "1.0.0"
  },
  "system_info": {
    "python_version": "3.11.7",
    "cuda_version": "12.1",
    "torch_version": "2.1.0+cu121",
    "comfyui_version": "abc1234",
    "platform": "linux",
    "architecture": "x86_64"
  },
  "custom_nodes": [
    {
      "name": "ComfyUI-Manager",
      "install_method": "git",
      "url": "https://github.com/ltdrdata/ComfyUI-Manager.git",
      "ref": "main",
      "has_post_install": true
    },
    {
      "name": "ComfyUI-Impact-Pack",
      "install_method": "archive",
      "url": "https://github.com/ltdrdata/ComfyUI-Impact-Pack/archive/4d52e84.tar.gz",
      "has_requirements": true,
      "install_order": 1
    }
  ],
  "dependencies": {
    "pytorch": {
      "index_url": "https://download.pytorch.org/whl/cu121",
      "packages": {
        "torch": "2.1.0",
        "torchvision": "0.16.0",
        "torchaudio": "2.1.0"
      }
    },
    "packages": {
      "numpy": "1.24.3",
      "scipy": "1.11.4",
      "opencv-python": "4.8.0.74",
      "transformers": "4.35.2",
      "accelerate": "0.24.1"
    },
    "git_packages": [
      {
        "url": "https://github.com/myuser/private-nodes.git",
        "ref": "dev",
        "egg_name": "my_nodes"
      }
    ],
    "editable": [
      {
        "path": "/home/user/dev/custom-sampler",
        "egg_name": "custom_sampler"
      }
    ]
  },
  "platform_overrides": {
    "win32": {
      "packages": {
        "windows-curses": "2.3.1"
      }
    }
  }
}
```
**Size**: ~1,800 bytes

## 8. Migration Guidelines

### 8.1 From Manifest to Container

1. Parse and validate manifest
2. Set up base container with matching Python version
3. Configure UV with any custom indices
4. Install dependencies in order: PyTorch → packages → git → editable
5. Install custom nodes with proper methods
6. Run post-install scripts
7. Generate uv.lock for reproducibility

### 8.2 Platform Considerations

- **Linux → Windows**: Check for Linux-only packages
- **GPU → CPU**: Adjust PyTorch packages and index
- **Different CUDA**: Validate compatible PyTorch builds exist

## 9. Future Compatibility

### 9.1 Adding Fields (Non-Breaking)

New optional fields can be added at any level without breaking v1.0 parsers:
- Additional metadata fields
- New dependency types
- Extended platform overrides

### 9.2 Version 2.0 Considerations

Future major version might include:
- Compressed package lists (pattern matching)
- Built-in URL templates
- Dependency groups
- Workflow-specific requirements
- Model specifications

## 10. Implementation Checklist

- [ ] JSON schema validation library
- [ ] Size validation (< 5KB)
- [ ] Version format validators
- [ ] URL validation and normalization
- [ ] Platform detection logic
- [ ] UV command generator
- [ ] Manifest minimizer (remove empty/null)
- [ ] Schema migration tools (future)

This specification provides the complete blueprint for implementing the ComfyUI Migration Manifest v1.0, ensuring consistent, minimal, and effective environment replication across all supported scenarios.