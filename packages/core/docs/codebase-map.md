# ComfyDock Core Package - Codebase Map

## Core Architecture

### Core Components (`core/`)
- **workspace.py** - Multi-environment workspace manager, coordinates all environments within a validated workspace
- **environment.py** - Single ComfyUI environment abstraction, owns nodes, models, workflows, and dependencies

## Data Models (`models/`)
Type definitions and data structures used throughout the package:
- **environment.py** - EnvironmentStatus, GitStatus, PackageSyncStatus data classes for environment state
- **workflow.py** - WorkflowNode, WorkflowDependencies, DetailedWorkflowStatus, ResolutionResult structures
- **shared.py** - Common models (NodeInfo, NodePackage, ModelSourceResult) shared across modules
- **sync.py** - SyncResult model for environment sync operation results
- **exceptions.py** - Custom exception hierarchy (ComfyDockError, CDNodeConflictError, etc.)
- **workspace_config.py** - Workspace configuration schema and validation
- **manifest.py** - Environment manifest for serialization and loading
- **registry.py** - Node registry and package mapping structures
- **civitai.py** - CivitAI API response models and types
- **commit.py** - Git commit tracking models
- **node_mapping.py** - Node to package mapping structures
- **system.py** - System information and capability models
- **protocols.py** - Type protocols for strategies and callback patterns

## Management Layer

### Managers (`managers/`)
Orchestrate operations on environments and their components:
- **node_manager.py** - Install/update/remove custom nodes with conflict detection and resolution
- **workflow_manager.py** - Workflow loading, parsing, and dependency extraction
- **model_symlink_manager.py** - Symlink models from global cache to environment directories
- **model_download_manager.py** - Download models from sources (CivitAI, HuggingFace, direct URLs)
- **pyproject_manager.py** - Read/write pyproject.toml dependencies and manage Python package specs
- **uv_project_manager.py** - Execute uv commands for Python environment management
- **git_manager.py** - Git operations (clone, checkout, status, diff parsing)
- **export_import_manager.py** - Bundle and extract environment configurations for portability

### Services (`services/`)
Stateless, reusable business logic modules:
- **node_lookup_service.py** - Find nodes across registries, GitHub, and local cache
- **registry_data_manager.py** - Load, cache, and manage the official ComfyUI node registry
- **model_downloader.py** - Coordinate model downloads from multiple sources and track download intents
- **import_analyzer.py** - Analyze and preview environment imports before applying changes

## Resolution & Analysis

### Analyzers (`analyzers/`)
Parse and extract information from workflows and environments:
- **workflow_dependency_parser.py** - Extract node and model dependencies from workflow JSON files
- **custom_node_scanner.py** - Scan custom node directories for metadata and input schemas
- **model_scanner.py** - Scan models directory for available models and categorize by type
- **node_classifier.py** - Classify nodes (builtin vs custom, categorize builtin subtypes)
- **git_change_parser.py** - Parse git diffs for node additions/removals in repositories
- **node_git_analyzer.py** - Extract git repository info and commit hashes from node URLs
- **status_scanner.py** - Analyze environment status (sync state, missing dependencies, conflicts)

### Resolvers (`resolvers/`)
Determine what packages to install and where to get models:
- **global_node_resolver.py** - Map unknown workflow nodes to known packages using embeddings and scoring
- **model_resolver.py** - Resolve model references to download sources and paths

### Repositories (`repositories/`)
Data access and persistence layer:
- **node_mappings_repository.py** - Access prebuilt node-to-package mappings database
- **workflow_repository.py** - Load and cache workflow files with context-aware hashing
- **workspace_config_repository.py** - Persist/load workspace configuration from disk
- **model_repository.py** - Index, query, and manage models across environments with SQLite
- **migrate_paths.py** - One-time migration utility for normalizing path separators in databases

## External Integration

### Clients (`clients/`)
API communication and external service integration:
- **civitai_client.py** - Search and query CivitAI for models, metadata, and file information
- **github_client.py** - Query GitHub API for custom node repository info and releases
- **registry_client.py** - Fetch official ComfyUI node registry with async support

### Factories (`factories/`)
Object construction and dependency injection:
- **workspace_factory.py** - Create Workspace instances with fully initialized dependencies
- **environment_factory.py** - Create Environment instances for existing ComfyUI installations
- **uv_factory.py** - Create uv command executors with environment setup

## Utilities & Infrastructure

### Core Utilities (`utils/`)
General-purpose helper functions:
- **requirements.py** - Parse requirements.txt and pyproject.toml for dependencies
- **dependency_parser.py** - Parse Python dependency version constraints and specifications
- **conflict_parser.py** - Detect and analyze dependency conflicts
- **version.py** - Version comparison, parsing, and compatibility checking
- **git.py** - Git URL manipulation, validation, and parsing
- **input_signature.py** - Parse node input signatures for matching and compatibility
- **download.py** - File downloading with retry logic and progress tracking
- **filesystem.py** - File and directory operations with cross-platform support
- **system_detector.py** - Detect OS, Python version, CUDA/GPU availability
- **uv_error_handler.py** - Parse and handle uv command errors with helpful messages
- **comfyui_ops.py** - ComfyUI-specific operations and path management
- **common.py** - General utilities (subprocess execution, logging helpers, etc)
- **model_categories.py** - ComfyUI model category mappings and classifications
- **retry.py** - Retry decorators and exponential backoff strategies
- **pytorch.py** - PyTorch-specific utilities for backend detection and index URL generation
- **environment_cleanup.py** - Cross-platform directory cleanup for damaged environments
- **workflow_hash.py** - Hash workflows for caching and change detection

### Caching (`caching/`)
Persistent and in-memory caching layer:
- **base.py** - Base classes for caching infrastructure with TTL and validation
- **api_cache.py** - Generic API response caching with time-to-live expiration
- **custom_node_cache.py** - Specialized cache for custom node metadata and input schemas
- **workflow_cache.py** - Persistent SQLite cache for workflow analysis and resolution results
- **comfyui_cache.py** - Cache for ComfyUI installations by version to avoid re-downloading

### Configuration (`configs/`)
Static configuration data:
- **comfyui_builtin_nodes.py** - Registry of ComfyUI builtin node classes and mappings
- **comfyui_models.py** - Model information, paths, and category definitions
- **model_config.py** - Model configuration and loading strategies

### Infrastructure (`infrastructure/`)
External system interfaces and persistence:
- **sqlite_manager.py** - SQLite database operations, schema management, and migrations

### Strategies (`strategies/`)
Pluggable behavior patterns for customizable behavior:
- **confirmation.py** - Node/model conflict resolution strategies (auto-confirm, manual, etc)
- **auto.py** - Automatic resolution strategies for non-interactive operations

### Validation (`validation/`)
Testing and verification utilities:
- **resolution_tester.py** - Test that resolved dependencies are valid and compatible

### Integrations (`integrations/`)
External tool integration layer:
- **uv_command.py** - Execute uv commands with proper environment setup and error handling

### Logging (`logging/`)
Structured logging configuration:
- **logging_config.py** - Configure logging for the package with file and console handlers

### Package Constants (`__init__.py`, `constants.py`)
- **constants.py** - Global constants for PyTorch packages, index URLs, and configuration values

## Key Entry Points

- **Workspace** - Top-level API, manages multiple environments and coordinates operations
- **Environment** - Single environment API for node/model/workflow operations
- **GlobalNodeResolver** - Resolve unknown nodes to packages using scoring
- **NodeLookupService** - Find nodes across all sources (builtin, custom, GitHub, registry)
- **WorkspaceFactory** - Create workspace instances with all dependencies initialized

## Architecture Notes

- **Library-first Design**: Core is decoupled from presentation concerns (no CLI imports or print statements)
- **Stateless Services**: Managers and services are stateless for testability and composability
- **Pluggable Strategies**: Confirmation and resolution behavior can be customized via strategy implementations
- **Persistent Caching**: SQLite-backed caching reduces API calls and improves performance
- **Error Handling**: Custom exception hierarchy for precise error handling and user guidance
- **Cross-platform Support**: All utilities handle Windows/Linux/macOS path and system differences
