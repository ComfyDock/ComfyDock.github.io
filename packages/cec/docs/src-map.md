# ComfyDock CEC Source Code Map

This document provides a comprehensive map of the ComfyUI Environment Capture (CEC) tool source code structure, detailing all important files and their purposes.

## Project Overview
The ComfyUI Environment Capture (CEC) tool is a Python package that can detect existing ComfyUI installations and recreate them in any target environment. It uses UV for modern package management and generates compact migration manifests for reliable environment reproduction.

## Root Directory Structure

```
/home/akatzfey/projects/comfydock/comfydock-cec-1/
├── CLAUDE.md                    # Project instructions for AI assistants
├── README.md                    # Basic project documentation  
├── pyproject.toml              # Python project configuration
├── uv.lock                     # UV dependency lock file
├── docs/                       # Documentation
├── src/                        # Main source code
├── tests/                      # Test suites
└── scripts/                    # Utility scripts
```

## Source Code Structure (`src/comfyui_detector/`)

### Core Application Files

| File | Purpose | Key Classes/Functions |
|------|---------|----------------------|
| `__init__.py` | Package initialization and exports | All public API exports |
| `__main__.py` | Allow running as `python -m comfyui_detector` | Entry point |
| `cli.py` | Command-line interface | `main()`, `run_detect()`, `run_recreate()` |
| `constants.py` | Configuration constants | `PYTORCH_PACKAGE_NAMES`, `CUSTOM_NODES_BLACKLIST` |
| `exceptions.py` | Custom exception hierarchy | `ComfyUIDetectorError` and subclasses |
| `common.py` | Shared utility functions | `run_command()`, `safe_json_*()` |
| `logging_config.py` | Logging configuration | `setup_logging()`, `get_logger()` |

### Core Detection & Recreation Classes

| File | Purpose | Key Classes |
|------|---------|-------------|
| `detector.py` | Main environment detector orchestration | `ComfyUIEnvironmentDetector` |
| `recreator.py` | Environment recreation from manifests | `EnvironmentRecreator` |
| `system_detector.py` | System-level detection (Python, CUDA, PyTorch) | `SystemDetector` |
| `package_detector.py` | Package and dependency detection | `PackageDetector` |
| `custom_node_scanner.py` | Custom node analysis and scanning | `CustomNodeScanner` |
| `manifest_generator.py` | Migration manifest generation | `ManifestGenerator` |

### Utility Modules (`utils/`)

| File | Purpose | Key Functions |
|------|---------|---------------|
| `system.py` | System detection utilities | `find_python_executable()`, `detect_*_version()` |
| `requirements.py` | Requirements file parsing | `parse_requirements_file()`, `parse_pyproject_toml()` |
| `git.py` | Git repository utilities | `get_git_info()`, `parse_git_url()` |
| `version.py` | Version handling utilities | `is_pytorch_package()`, `get_pytorch_index_url()` |

### Integration Modules (`integrations/`)

| File | Purpose | Key Classes |
|------|---------|-------------|
| `uv.py` | UV package manager interface | `UVInterface`, `UVResult` |

### Validation Modules (`validators/`)

| File | Purpose | Key Classes |
|------|---------|-------------|
| `registry.py` | Comfy Registry API validation | `ComfyRegistryValidator` |
| `github.py` | GitHub release/tag validation | `GitHubReleaseChecker` |

### Data Models (`models/`)

| File | Purpose | Key Classes |
|------|---------|-------------|
| `models.py` | Data models and schema definitions | `MigrationManifest`, `CustomNodeSpec`, `SystemInfo`, `Package`, `EnvironmentResult` |

## Test Structure (`tests/`)

### Unit Tests (`tests/unit/`)
Comprehensive unit tests for all major components:

| Test File | Tests Module | Purpose |
|-----------|--------------|---------|
| `test_cli.py` | `cli.py` | CLI command testing |
| `test_detector.py` | `detector.py` | Main detector class testing |
| `test_recreator.py` | `recreator.py` | Environment recreation testing |
| `test_models.py` | `models/models.py` | Data model validation testing |
| `test_common.py` | `common.py` | Utility function testing |
| `test_exceptions.py` | `exceptions.py` | Exception handling testing |
| `test_uv_interface.py` | `integrations/uv.py` | UV interface testing |
| `test_recreator_*.py` | Various recreator components | Specialized recreator tests |

### Integration Tests (`tests/integration/`)

| File | Purpose |
|------|---------|
| `test_cli_integration.py` | Full detect → recreate → detect cycle testing |
| `README.md` | Integration testing documentation |

### Migration Tests (`tests/migration/`)
Advanced testing infrastructure for migration scenarios:

| Directory/File | Purpose |
|----------------|---------|
| `builders/` | Environment building utilities |
| `config/` | Test configuration files |
| `metrics/` | Performance and metrics collection |
| `utils/` | Migration testing utilities |
| `validators/` | Migration validation logic |

## Documentation (`docs/`)

| File | Purpose |
|------|---------|
| `prd.md` | Product Requirements Document - comprehensive project specification |
| `UV-docs.md` | UV package manager documentation and usage |
| `src-map.md` | This source code map document |

## Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Python project configuration, dependencies, and build settings |
| `uv.lock` | UV dependency lock file for reproducible builds |
| `CLAUDE.md` | Instructions for AI assistants working on the project |

## Key Architecture Patterns

### 1. Detector Pattern
The main `ComfyUIEnvironmentDetector` orchestrates specialized detector classes:
- `SystemDetector` → System information (Python, CUDA, PyTorch)
- `PackageDetector` → Installed packages and dependencies  
- `CustomNodeScanner` → Custom node analysis
- `ManifestGenerator` → Final manifest creation

### 2. Recreation Pattern
The `EnvironmentRecreator` handles environment setup:
- Manifest validation and parsing
- Virtual environment creation via UV
- Package installation with conflict resolution
- Custom node installation from various sources

### 3. Validation Pattern
External validation through specialized classes:
- `ComfyRegistryValidator` → Validates against Comfy Registry API
- `GitHubReleaseChecker` → Validates GitHub releases and tags

### 4. Data Flow
```
ComfyUI Environment → Detection → Migration Manifest → Recreation → New Environment
```

## Entry Points

| Entry Point | Command | Purpose |
|-------------|---------|---------|
| `cec detect <path>` | CLI detection | Analyze existing ComfyUI installation |
| `cec recreate <manifest> <target>` | CLI recreation | Recreate environment from manifest |
| `python -m comfyui_detector` | Module execution | Alternative execution method |

## Key Dependencies

| Package | Purpose |
|---------|---------|
| `packaging` | Version parsing and comparison |
| `pipdeptree` | Python package dependency tree analysis |
| `requests` | HTTP requests for API validation |
| `toml` | TOML file parsing for pyproject.toml |

## Output Files

The tool generates several output files:

| File | Purpose |
|------|---------|
| `comfyui_migration.json` | Lean migration manifest for recreation |
| `comfyui_detection_log.json` | Detailed analysis data for debugging |
| `comfyui_requirements.txt` | Traditional requirements.txt format |

This source map provides a comprehensive overview of the codebase structure and can be used as a reference for understanding, maintaining, and extending the ComfyUI Environment Capture tool.