# ComfyDock CEC - Codebase Map

```
.
├── CLAUDE.md                           # 📝 Project instructions and environment setup
├── README.md                           # 📚 Project overview and basic usage
├── pyproject.toml                      # ⚙️ Python project configuration with UV
├── uv.lock                             # 🔒 UV dependency lock file
├── docs/
│   ├── prd.md                          # 📋 Product Requirements Document
│   ├── UV-docs.md                      # 📖 UV package manager documentation
│   └── codebase-map.md                 # 🗺️ This file - codebase navigation guide
├── scripts/
│   ├── run_migration_tests.py          # 🧪 Migration test runner script
│   └── uv-cli.py                       # 🔧 UV command line interface
├── src/
│   └── comfyui_detector/               # 🏗️ Main application package
│       ├── __init__.py                 # 📦 Package initialization
│       ├── __main__.py                 # 🎯 Module entry point (python -m)
│       ├── cli.py                      # 🎮 CLI interface with detect/recreate commands
│       ├── detector.py                 # 🔍 Main ComfyUIEnvironmentDetector orchestrator
│       ├── recreator.py                # 🔄 EnvironmentRecreator for rebuilding environments
│       ├── system_detector.py          # 🖥️ Python/CUDA/PyTorch system detection
│       ├── package_detector.py         # 📦 Package and dependency analysis
│       ├── custom_node_scanner.py      # 🔌 Custom node discovery and analysis
│       ├── manifest_generator.py       # 📄 Migration manifest generation
│       ├── constants.py                # 📊 Configuration constants and defaults
│       ├── common.py                   # 🔄 Shared utilities and common functions
│       ├── exceptions.py               # ⚠️ Custom exception classes
│       ├── logging_config.py           # 📝 Logging configuration setup
│       ├── integrations/
│       │   ├── __init__.py             
│       │   └── uv.py                   # 🔧 UV package manager interface
│       ├── models/
│       │   ├── __init__.py
│       │   └── models.py               # 🏗️ Pydantic data models for type safety
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── git.py                  # 🌿 Git repository utilities
│       │   ├── requirements.py         # 📋 Requirements parsing utilities
│       │   ├── system.py               # 🖥️ System detection and analysis
│       │   └── version.py              # 🔢 Version comparison and PyTorch utilities
│       └── validators/
│           ├── __init__.py
│           ├── github.py               # 🐙 GitHub release/tag validation
│           └── registry.py             # 🗃️ Comfy Registry API validation
├── tests/
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── README.md                   # 📚 Integration testing documentation
│   │   └── test_cli_integration.py     # 🧪 End-to-end CLI integration tests
│   ├── migration/                      # 🔄 Advanced migration testing infrastructure
│   │   ├── llm.md                      # 🤖 LLM integration documentation
│   │   ├── migration-test-llm-context.md # 📖 LLM testing context
│   │   ├── builders/
│   │   │   ├── __init__.py
│   │   │   └── environment_builder.py  # 🏗️ Test environment construction
│   │   ├── config/
│   │   │   ├── custom_nodes.yaml       # ⚙️ Custom node test configurations
│   │   │   ├── test_config.py          # 🔧 Test configuration management
│   │   │   └── test_config.yaml        # 📄 YAML test settings
│   │   ├── metrics/
│   │   │   ├── __init__.py
│   │   │   └── collector.py            # 📊 Test metrics collection
│   │   ├── phases/                     # 📁 Migration phase test organization
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── docker_utils.py         # 🐳 Docker testing utilities
│   │   │   ├── error_handler.py        # ⚠️ Test error handling
│   │   │   ├── log_parser.py           # 📝 Log parsing for tests
│   │   │   └── pydantic_classes.py     # 🏗️ Test data models
│   │   └── validators/
│   │       ├── __init__.py
│   │       └── migration_validator.py  # ✅ Migration validation logic
│   └── unit/                           # 🧪 Comprehensive unit test suite
│       ├── test_cli.py                 # 🎮 CLI interface unit tests
│       ├── test_common.py              # 🔄 Common utilities tests
│       ├── test_detector.py            # 🔍 Main detector logic tests
│       ├── test_environment_result.py  # 📊 Environment result model tests
│       ├── test_exceptions.py          # ⚠️ Exception handling tests
│       ├── test_models.py              # 🏗️ Data model validation tests
│       ├── test_recreator.py           # 🔄 Environment recreation tests
│       ├── test_recreator_api_alignment.py # 🔌 API alignment tests
│       ├── test_recreator_custom_node_archive.py # 📦 Archive node tests
│       ├── test_recreator_custom_node_git.py # 🌿 Git node installation tests
│       ├── test_recreator_package_installation.py # 📦 Package install tests
│       ├── test_recreator_validation.py # ✅ Recreation validation tests
│       ├── test_uv_interface.py        # 🔧 UV interface unit tests
│       └── test_uvinterface_refactor_usage.py # 🔄 UV refactoring tests
└── comfydock_cec.egg-info/             # 🥚 Package metadata (auto-generated)
```

## Key Components

### 🎯 Entry Points
- **CLI Command**: `cec detect <path>` - Analyze existing ComfyUI installation
- **CLI Command**: `cec recreate <manifest> <target>` - Recreate environment from manifest  
- **Module**: `python -m comfyui_detector` - Alternative execution method

### 🏗️ Core Architecture

#### Detection Pipeline
1. **cli.py:15** - Main entry point and argument parsing
2. **detector.py:ComfyUIEnvironmentDetector** - Orchestrates detection process
3. **system_detector.py** - Analyzes Python/CUDA/PyTorch environment
4. **package_detector.py** - Extracts package dependencies via UV
5. **custom_node_scanner.py** - Discovers and analyzes custom nodes
6. **manifest_generator.py** - Creates migration-ready JSON manifest

#### Recreation Pipeline  
1. **cli.py:174** - Recreation command handling
2. **recreator.py:EnvironmentRecreator** - Environment setup and package installation
3. **integrations/uv.py:UVInterface** - All package operations via UV
4. **validators/** - Validates recreation against manifest

### 🔧 Key Classes & Functions

| File | Key Components | Purpose |
|------|----------------|---------|
| `cli.py` | `main()`, `run_detect()`, `run_recreate()` | CLI interface and command routing |
| `detector.py` | `ComfyUIEnvironmentDetector.detect_all()` | Main detection orchestration |
| `recreator.py` | `EnvironmentRecreator.recreate()` | Environment recreation from manifest |
| `system_detector.py` | `find_python_executable()`, `extract_packages_with_uv()` | System environment analysis |
| `custom_node_scanner.py` | `_scan_single_custom_node()` | Custom node metadata extraction |
| `integrations/uv.py` | `UVInterface` | UV package manager operations |
| `models/models.py` | `MigrationManifest`, `EnvironmentResult` | Type-safe data structures |

### 📊 Data Flow

```
Source ComfyUI → Detector → Analyzer → Manifest Generator
                                           ↓
                              comfyui_migration.json
                                           ↓
Target Path + Manifest → Recreator → UV Operations → Validation
                            ↓
                   New Environment
                   ├── ComfyUI/
                   └── .venv/
```

### 🧪 Testing Strategy

- **Unit Tests** (15 files): Comprehensive coverage of all components
- **Integration Tests**: End-to-end detect→recreate→validate cycles  
- **Migration Tests**: Advanced scenarios with Docker and metrics collection
- **TDD Approach**: Tests written before implementation for new features

### 🔄 Key Workflows

1. **Environment Capture**: `cec detect /path/to/comfyui --output-dir ./capture`
2. **Environment Recreation**: `cec recreate ./capture/comfyui_migration.json --target ./new_env`
3. **Registry Validation**: `--validate-registry` flag for custom node verification
4. **Cross-Platform**: Handles platform-specific dependencies and paths

### 📝 Configuration Files

- **pyproject.toml:14** - Entry point: `cec = "comfyui_detector.cli:main"`
- **constants.py** - PyTorch packages, custom node blacklists, defaults
- **CLAUDE.md** - Development environment and testing instructions
- **UV-docs.md** - UV package manager integration details

This codebase implements a complete environment capture and recreation system for ComfyUI installations, with strong emphasis on reliability, testing, and UV integration for modern Python package management.