# Codebase Map

## File Structure

```
src/comfydock_core/
├── 🎯 constants.py - Global constants and package definitions [→](#constants-py)
├── cli/
│   ├── 🎯 __main__.py - CLI entry point [→](#cli-main-py)
│   ├── 🎯 cli.py - Main CLI argument parser and routing [→](#cli-cli-py)
│   ├── 🌐 global_commands.py - Workspace-level commands [→](#cli-global-commands-py)
│   └── 🌐 env_commands.py - Environment-specific commands [→](#cli-env-commands-py)
├── core/
│   ├── 🎯 environment.py - Core environment management class [→](#core-environment-py)
│   └── 🎯 workspace_manager.py - Workspace and multi-environment management [→](#core-workspace-manager-py)
├── managers/
│   ├── 🧱 node_coordinator.py - Coordinates node addition with UV and pyproject [→](#managers-node-coordinator-py)
│   ├── 🧱 pyproject_manager.py - PyProject.toml file operations [→](#managers-pyproject-manager-py)
│   ├── 🧱 uv_project_manager.py - UV package manager orchestration [→](#managers-uv-project-manager-py)
│   ├── 🧱 status_scanner.py - Environment state scanning and comparison [→](#managers-status-scanner-py)
│   ├── 🧱 resolution_tester.py - UV resolution testing [→](#managers-resolution-tester-py)
│   ├── 🧱 git_manager.py - Git repository management [→](#managers-git-manager-py)
│   ├── 🧱 environment_version_manager.py - Environment versioning and rollback [→](#managers-environment-version-manager-py)
│   └── 🧱 workflow_manager.py - Workflow tracking and synchronization [→](#managers-workflow-manager-py)
├── factories/
│   ├── 🏭 environment_factory.py - Environment creation factory [→](#factories-environment-factory-py)
│   └── 🏭 uv_factory.py - UV interface factory [→](#factories-uv-factory-py)
├── models/
│   ├── 🗂️ shared.py - Core data models and manifest definitions [→](#models-shared-py)
│   ├── 🗂️ environment.py - Environment status and result models [→](#models-environment-py)
│   ├── 🗂️ detection.py - Detection result models and data structures [→](#models-detection-py)
│   ├── 🗂️ protocols.py - Type protocols and interfaces [→](#models-protocols-py)
│   └── 🚨 exceptions.py - Custom exception hierarchy [→](#models-exceptions-py)
├── integrations/
│   └── ⚙️ uv_command.py - Low-level UV command wrapper [→](#integrations-uv-command-py)
├── services/
│   ├── 🌐 registry_client.py - ComfyUI registry API client [→](#services-registry-client-py)
│   ├── 🌐 github_client.py - GitHub API integration [→](#services-github-client-py)
│   └── 🌐 node_registry.py - Node discovery and download service [→](#services-node-registry-py)
├── caching/
│   ├── 🗄️ api_cache.py - Generic API response caching [→](#caching-api-cache-py)
│   └── 🗄️ custom_node_cache.py - Custom node download caching [→](#caching-custom-node-cache-py)
├── logging/
│   └── 📝 logging_config.py - Centralized logging configuration [→](#logging-logging-config-py)
└── utils/
    ├── 🛠️ common.py - Common utilities and helpers [→](#utils-common-py)
    ├── 🛠️ progress.py - Progress tracking utilities [→](#utils-progress-py)
    ├── 🔍 custom_node_scanner.py - Node requirement scanning [→](#utils-custom-node-scanner-py)
    ├── 📦 dependency_parser.py - Dependency parsing utilities [→](#utils-dependency-parser-py)
    ├── 📦 conflict_parser.py - Dependency conflict analysis [→](#utils-conflict-parser-py)
    ├── 📦 requirements.py - Requirements.txt parsing [→](#utils-requirements-py)
    ├── 🌐 download.py - File download utilities [→](#utils-download-py)
    ├── 📁 filesystem.py - File system utilities [→](#utils-filesystem-py)
    ├── 🔧 git.py - Git operations wrapper [→](#utils-git-py)
    ├── 🔧 comfyui_ops.py - ComfyUI specific operations [→](#utils-comfyui-ops-py)
    ├── 📝 environment_logger.py - Environment-specific logging [→](#utils-environment-logger-py)
    ├── 🔄 retry.py - Retry and rate limiting utilities [→](#utils-retry-py)
    ├── 📊 version.py - Version parsing utilities [→](#utils-version-py)
    ├── 🔍 system_detector.py - System information detection [→](#utils-system-detector-py)
    └── 🔍 git_change_parser.py - Git change parsing utilities [→](#utils-git-change-parser-py)
```

## File Details

### constants.py

**Purpose:** Defines global constants including PyTorch package names and ComfyUI configuration defaults.

**Dependencies:**
- Imports: None (constants only)
- Imported by: Multiple modules throughout the codebase

**Exports:**
- `PYTORCH_PACKAGE_NAMES: set[str]` - Set of PyTorch and CUDA packages
- `CUSTOM_NODES_BLACKLIST: set[str]` - Directory names to ignore as custom nodes  
- `DEFAULT_REGISTRY_URL: str` - Default ComfyUI registry URL
- `SCHEMA_VERSION: str` - Current manifest schema version
- `DETECTOR_VERSION: str` - Current detector version

### core/environment.py

**Purpose:** Core Environment class that manages a single ComfyUI environment through composed managers and factories.

**Dependencies:**
- Imports: factories.uv_factory, managers.*, services.node_registry, models.environment, models.exceptions, utils.common
- Imported by: core.workspace_manager, factories.environment_factory, cli.env_commands

**Exports:**
- `Environment` - Main environment management class with methods:
  - `add_node(identifier: str, is_local: bool, no_test: bool) -> NodeInfo` - Add custom node with conflict checking
  - `remove_node(identifier: str) -> None` - Remove custom node  
  - `status() -> EnvironmentStatus` - Get current environment state
  - `sync(dry_run: bool) -> None` - Apply staged changes
  - `rollback(target: str) -> None` - Rollback to previous state
  - `get_versions(limit: int) -> list[dict]` - Get version history
  - `run(args: list[str]) -> subprocess.CompletedProcess` - Run ComfyUI

### core/workspace_manager.py

**Purpose:** Manages ComfyDock workspaces and multiple environments within them using factories and simplified structure.

**Dependencies:**
- Imports: factories.environment_factory, models.exceptions, utils.environment_logger
- Imported by: cli.global_commands, cli.env_commands

**Exports:**
- `WorkspacePaths` - Dataclass for workspace directory structure
- `WorkspaceManager` - Main workspace management class with methods:
  - `create(path: Path) -> WorkspaceManager` - Initialize new workspace
  - `list_environments() -> list[Environment]` - List all environments
  - `get_environment(name: str) -> Environment` - Get environment by name
  - `create_environment(name: str, python_version: str, comfyui_version: str) -> Environment` - Create new environment
  - `delete_environment(name: str) -> None` - Delete environment
  - `get_active_environment() -> Environment` - Get currently active environment
  - `set_active_environment(name: str) -> None` - Set active environment

### managers/node_coordinator.py

**Purpose:** Coordinates node addition between UV and PyprojectManager with collision-resistant naming and source tracking.

**Dependencies:**
- Imports: managers.pyproject_manager, managers.uv_project_manager, models.shared
- Imported by: core.environment

**Exports:**
- `NodeCoordinator` - Node coordination class with methods:
  - `add_node_package(node_package: NodePackage) -> None` - Add complete node package with requirements and source tracking

### managers/pyproject_manager.py

**Purpose:** Comprehensive pyproject.toml file operations with specialized handlers for different configuration sections.

**Dependencies:**
- Imports: tomlkit, utils.dependency_parser, models.exceptions, logging_config
- Imported by: managers.uv_project_manager, managers.node_coordinator, core.environment

**Exports:**
- `PyprojectManager` - Main pyproject file manager with handlers:
  - `dependencies: DependencyHandler` - Dependency groups management
  - `nodes: NodeHandler` - Custom node management  
  - `uv_config: UVConfigHandler` - UV configuration management
  - `workflows: WorkflowHandler` - Workflow tracking management
- `DependencyHandler` - Handles dependency groups
- `UVConfigHandler` - Handles UV sources, indexes, and constraints
- `NodeHandler` - Handles custom node configuration
- `WorkflowHandler` - Handles workflow tracking configuration

### managers/uv_project_manager.py

**Purpose:** High-level UV project management with smart workflows, requirements parsing, and pyproject.toml coordination.

**Dependencies:**
- Imports: integrations.uv_command, managers.pyproject_manager, models.exceptions, logging_config
- Imported by: core.environment, factories.uv_factory

**Exports:**
- `UVProjectManager` - UV orchestration class with methods:
  - `add_requirements_with_sources(requirements: Path|list[str], group: str) -> None` - Smart requirements handling
  - `sync_project(**flags) -> str` - Sync environment
  - `lock_project(**flags) -> str` - Generate/update lockfile
  - `add_constraint_dependency(package: str) -> None` - Add constraint
  - `create_index(name: str, url: str, explicit: bool) -> None` - Create index
  - `add_source_index(package_name: str, index: str) -> None` - Add source mapping

### managers/status_scanner.py

**Purpose:** Scans environment state including custom nodes, packages, and Python version with comparison capabilities.

**Dependencies:**
- Imports: managers.uv_project_manager, managers.pyproject_manager, utils.git, logging_config
- Imported by: core.environment

**Exports:**
- `StatusScanner` - Environment state scanning class with methods:
  - `get_full_comparison(comfyui_path: Path, venv_path: Path, uv: UVProjectManager, pyproject: PyprojectManager) -> ComparisonResult` - Full environment comparison

### managers/resolution_tester.py

**Purpose:** Tests UV dependency resolution for conflict detection using temporary environments.

**Dependencies:**
- Imports: integrations.uv_command, models.shared, logging_config
- Imported by: core.environment

**Exports:**
- `ResolutionTester` - Resolution testing class with methods:
  - `test_resolution(pyproject_path: Path) -> UVResult` - Test if resolution succeeds
  - `format_conflicts(result: UVResult) -> str` - Format conflict messages

### managers/git_manager.py

**Purpose:** Git repository management for environment versioning and change tracking.

**Dependencies:**
- Imports: utils.git, models.exceptions, logging_config
- Imported by: core.environment, managers.environment_version_manager, factories.environment_factory

**Exports:**
- `GitManager` - Git operations manager with methods:
  - `initialize_environment_repo(initial_message: str) -> None` - Initialize git repo
  - `get_status(pyproject: PyprojectManager) -> GitStatus` - Get git status
  - `get_version_history(limit: int) -> list[dict]` - Get commit history

### managers/environment_version_manager.py

**Purpose:** Environment versioning and rollback capabilities using git operations.

**Dependencies:**
- Imports: managers.git_manager, logging_config
- Imported by: core.environment

**Exports:**
- `EnvironmentVersionManager` - Version management class with methods:
  - `rollback_to(target: str) -> None` - Rollback to specific version

### managers/workflow_manager.py

**Purpose:** Workflow tracking and synchronization between active and tracked workflows.

**Dependencies:**
- Imports: managers.pyproject_manager, models.shared, logging_config
- Imported by: core.environment

**Exports:**
- `WorkflowManager` - Workflow management class with methods:
  - `get_full_status() -> WorkflowStatus` - Get workflow synchronization status
  - `sync_workflows() -> dict[str, str]` - Sync workflows between active and tracked

### factories/environment_factory.py

**Purpose:** Factory for creating new environments with ComfyUI setup and initial configuration.

**Dependencies:**
- Imports: core.environment, managers.git_manager, utils.comfyui_ops, models.exceptions
- Imported by: core.workspace_manager

**Exports:**
- `EnvironmentFactory` - Environment creation factory with methods:
  - `create(name: str, env_path: Path, workspace_path: Path, python_version: str, comfyui_version: str, cache_path: Path) -> Environment` - Create complete new environment

### factories/uv_factory.py

**Purpose:** Factory for creating configured UV project manager instances.

**Dependencies:**
- Imports: integrations.uv_command, managers.uv_project_manager, managers.pyproject_manager
- Imported by: core.environment

**Exports:**
- `create_uv_for_environment(workspace_path: Path, cec_path: Path, venv_path: Path) -> UVProjectManager` - Create configured UV manager

### services/node_registry.py

**Purpose:** Stateless service for finding, downloading, and analyzing custom nodes from registry or git with caching support.

**Dependencies:**
- Imports: services.registry_client, services.github_client, caching.*, utils.custom_node_scanner, utils.download, utils.git, models.shared, models.exceptions
- Imported by: core.environment

**Exports:**
- `NodeRegistry` - Node discovery and management service with methods:
  - `prepare_node(identifier: str, is_local: bool) -> NodePackage` - Get complete node package with requirements
  - `get_node(identifier: str, is_local: bool) -> NodeInfo` - Find node by ID or URL (raises if not found)
  - `find_node(identifier: str, is_local: bool) -> NodeInfo|None` - Find node (returns None if not found)
  - `download_node(node_info: NodeInfo, target_path: Path) -> None` - Download node to path
  - `get_node_requirements(node_info: NodeInfo) -> list[str]|None` - Get node requirements by scanning
  - `sync_nodes_to_filesystem(expected_nodes: dict, custom_nodes_dir: Path) -> None` - Sync nodes to match expected state
  - `search_nodes(query: str, limit: int) -> list[NodeInfo]|None` - Search registry for nodes
  - `parse_expected_nodes(pyproject_config: dict) -> dict[str, NodeInfo]` - Parse expected nodes from pyproject

### services/registry_client.py

**Purpose:** Client for ComfyUI registry API with caching and rate limiting.

**Dependencies:**
- Imports: json, urllib, models.shared, caching.api_cache, utils.retry, constants, logging_config
- Imported by: services.node_registry

**Exports:**
- `ComfyRegistryClient` - Registry API client with methods:
  - `get_node(node_id: str) -> RegistryNodeInfo` - Get node by ID
  - `install_node(node_id: str, version: str) -> RegistryNodeVersion` - Get install info
  - `search_nodes(query: str, limit: int) -> list[RegistryNodeInfo]` - Search nodes
  - `get_node_requirements(node_id: str) -> list[str]` - Get node requirements

### services/github_client.py

**Purpose:** GitHub API integration for repository validation and metadata with caching.

**Dependencies:**
- Imports: caching.api_cache, utils.retry, logging_config
- Imported by: services.node_registry

**Exports:**
- `GitHubClient` - GitHub API client for repository operations

### models/shared.py

**Purpose:** Core data models including manifest schema, node information, and system requirements.

**Dependencies:**
- Imports: json, re, dataclasses, pathlib, typing, urllib.parse, models.exceptions
- Imported by: services.node_registry, services.registry_client, caching.custom_node_cache, managers.*

**Exports:**
- `RegistryNodeVersion` - Registry node version information
- `RegistryNodeInfo` - Registry node metadata  
- `NodeInfo` - Generic node information with factory methods
- `NodePackage` - Complete package for a node including info and requirements
- `Package` - Python package representation
- `SystemRequirements` - System requirements specification
- `CustomNodeSpec` - Custom node installation specification
- `PyTorchSpec` - PyTorch configuration specification
- `EnvironmentManifest` - Complete environment manifest
- `SystemInfo` - Detected system information
- `UVResult` - UV operation result
- `CachedNodeInfo` - Cached node metadata
- `ProgressContext` - Context for nested progress tracking

### models/environment.py

**Purpose:** Data models for environment status and operation results.

**Dependencies:**
- Imports: dataclasses, typing
- Imported by: core.environment, managers.*

**Exports:**
- `EnvironmentStatus` - Environment change status with sync information
- `NodeAddResult` - Result of node addition operation

### models/detection.py

**Purpose:** Detection result models and data structures for custom node scanning and validation.

**Dependencies:**
- Imports: dataclasses, field
- Imported by: utils.custom_node_scanner

**Exports:**
- `GitInfo` - Git repository information with serialization methods
- `RegistryValidation` - Registry validation results with available versions
- `GitHubValidation` - GitHub validation results for releases and tags
- `CustomNodeInfo` - Comprehensive custom node information with metadata
- `CustomNodesInfo` - Collection of all detected custom nodes
- `DetectedPackages` - Package detection results with PyTorch configuration

### models/protocols.py

**Purpose:** Type protocols and interfaces for dependency injection and type checking.

**Dependencies:**
- Imports: typing.Protocol
- Imported by: Various modules for type checking

**Exports:**
- Protocol interfaces for type safety

### models/exceptions.py

**Purpose:** Comprehensive custom exception hierarchy for ComfyDock error handling.

**Dependencies:**
- Imports: typing
- Imported by: Most modules throughout the codebase

**Exports:**
- `ComfyDockError` - Base exception class
- `CDWorkspaceNotFoundError` - Workspace not found
- `CDWorkspaceError` - General workspace errors
- `CDEnvironmentError` - General environment errors
- `CDEnvironmentNotFoundError` - Environment not found
- `CDEnvironmentExistsError` - Environment already exists
- `CDPyprojectError` - PyProject.toml operation errors
- `CDPyprojectNotFoundError` - PyProject.toml file not found
- `CDPyprojectInvalidError` - PyProject.toml invalid format
- `CDRegistryError` - Registry API errors
- `CDNodeNotFoundError` - Node not found
- `CDNodeConflictError` - Node has dependency conflicts
- `CDProcessError` - Subprocess command execution failed
- `UVNotInstalledError` - UV not installed
- `UVCommandError` - UV command execution failed

### integrations/uv_command.py

**Purpose:** Low-level UV command wrapper with subprocess management and error handling.

**Dependencies:**
- Imports: subprocess, pathlib, models.exceptions, utils.common, logging_config
- Imported by: managers.uv_project_manager, managers.resolution_tester

**Exports:**
- `UVCommand` - Low-level UV command interface with methods:
  - `init(**flags) -> CompletedProcess` - Initialize UV project
  - `add(packages: list[str], **flags) -> CompletedProcess` - Add dependencies
  - `remove(packages: list[str], **flags) -> CompletedProcess` - Remove dependencies
  - `sync(**flags) -> CompletedProcess` - Sync project
  - `lock(**flags) -> CompletedProcess` - Generate lockfile
  - `run(command: list[str], **flags) -> CompletedProcess` - Run command
  - `pip_install(**flags) -> CompletedProcess` - Install packages
  - `pip_list(python: Path) -> CompletedProcess` - List packages
  - `version() -> str` - Get UV version

### caching/api_cache.py

**Purpose:** Generic API response caching system with TTL support and JSON serialization.

**Dependencies:**
- Imports: json, pathlib, time, logging_config
- Imported by: services.registry_client, services.github_client

**Exports:**
- `APICacheManager` - API caching with methods:
  - `get(category: str, key: str) -> Any` - Get cached data
  - `set(category: str, key: str, data: Any, ttl: int) -> None` - Cache data with TTL
  - `clear(category: str) -> None` - Clear cache category

### caching/custom_node_cache.py

**Purpose:** Custom node download caching with content validation and metadata tracking.

**Dependencies:**
- Imports: json, pathlib, shutil, hashlib, models.shared, logging_config
- Imported by: services.node_registry

**Exports:**
- `CustomNodeCacheManager` - Node download caching with methods:
  - `get_cached_path(node_info: NodeInfo) -> Path|None` - Get cached node path
  - `cache_node(node_info: NodeInfo, source_path: Path) -> None` - Cache downloaded node
  - `clear_cache() -> None` - Clear all cached nodes

### cli/__main__.py

**Purpose:** Python module entry point for CLI execution via python -m comfydock_core.cli.

**Dependencies:**
- Imports: cli.cli
- Imported by: Python interpreter when running module

**Exports:**
- Executes `main()` when module is run directly

### cli/cli.py

**Purpose:** Main CLI entry point with hierarchical command structure and special ComfyUI argument handling.

**Dependencies:**
- Imports: argparse, sys, pathlib, cli.global_commands, cli.env_commands, logging_config
- Imported by: cli.__main__

**Exports:**
- `main() -> None` - Main CLI entry point with error handling and argument passthrough
- `create_parser() -> argparse.ArgumentParser` - Create hierarchical argument parser
- `_add_global_commands(subparsers)` - Add workspace commands (init, list, migrate, import, export)
- `_add_env_commands(subparsers)` - Add environment commands (create, use, delete, run, status, sync, commit, log, rollback, node, workflow, constraint)

### cli/global_commands.py

**Purpose:** Implementation of workspace-level CLI commands.

**Dependencies:**
- Imports: core.workspace_manager, logging_config
- Imported by: cli.cli

**Exports:**
- `GlobalCommands` - Workspace command implementations for init, list, migrate, import, export

### cli/env_commands.py

**Purpose:** Implementation of environment-specific CLI commands with comprehensive environment operations.

**Dependencies:**
- Imports: core.workspace_manager, logging_config
- Imported by: cli.cli

**Exports:**
- `EnvironmentCommands` - Environment command implementations for create, use, delete, run, status, sync, commit, log, rollback, node management, workflow management, constraint management

### logging/logging_config.py

**Purpose:** Centralized logging configuration with file rotation and multiple handlers.

**Dependencies:**
- Imports: logging, sys, pathlib
- Imported by: Most modules throughout the codebase

**Exports:**
- `setup_logging(level: str, log_file: Path, simple_format: bool, console_level: str) -> None` - Configure logging
- `get_logger(name: str) -> logging.Logger` - Get module logger

### utils/common.py

**Purpose:** Common utilities and helpers for subprocess execution and general operations.

**Dependencies:**
- Imports: subprocess, pathlib, models.exceptions, logging_config
- Imported by: integrations.uv_command, core.environment, various utilities

**Exports:**
- `run_command(cmd: list[str], **kwargs) -> subprocess.CompletedProcess` - Execute subprocess with error handling
- Common utility functions

### utils/progress.py

**Purpose:** Progress tracking utilities for long-running operations.

**Dependencies:**
- Imports: time, models.shared, logging_config
- Imported by: Various modules for progress tracking

**Exports:**
- Progress tracking classes and context managers

### utils/custom_node_scanner.py

**Purpose:** Scans custom node directories for requirements and dependencies.

**Dependencies:**
- Imports: pathlib, utils.requirements, utils.filesystem, models.detection, logging_config
- Imported by: services.node_registry

**Exports:**
- `CustomNodeScanner` - Node scanning functionality with methods:
  - `scan_node(node_path: Path) -> NodeRequirements|None` - Scan single node for requirements

### utils/dependency_parser.py

**Purpose:** Dependency parsing utilities for various package specification formats.

**Dependencies:**
- Imports: re, logging_config
- Imported by: managers.pyproject_manager, managers.uv_project_manager

**Exports:**
- `parse_dependency_string(spec: str) -> tuple[str, str|None]` - Parse package specifications
- Dependency parsing utilities

### utils/conflict_parser.py

**Purpose:** Dependency conflict analysis and parsing utilities.

**Dependencies:**
- Imports: re, logging_config
- Imported by: managers.resolution_tester

**Exports:**
- Conflict parsing and analysis functions

### utils/requirements.py

**Purpose:** Requirements.txt file parsing utilities.

**Dependencies:**
- Imports: pathlib, re, logging_config
- Imported by: utils.custom_node_scanner, managers.uv_project_manager

**Exports:**
- Requirements file parsing functions

### utils/download.py

**Purpose:** File download utilities with progress tracking and extraction.

**Dependencies:**
- Imports: urllib, pathlib, tempfile, zipfile, tarfile, logging_config
- Imported by: services.node_registry

**Exports:**
- `download_and_extract_archive(url: str, target_path: Path) -> None` - Download and extract archives
- File download utilities

### utils/filesystem.py

**Purpose:** File system utilities and operations.

**Dependencies:**
- Imports: pathlib, shutil, logging_config
- Imported by: utils.custom_node_scanner, caching modules

**Exports:**
- File system operation utilities

### utils/git.py

**Purpose:** Git operations wrapper with error handling.

**Dependencies:**
- Imports: subprocess, pathlib, models.exceptions, logging_config
- Imported by: managers.git_manager, services.node_registry, utils.comfyui_ops

**Exports:**
- `git_clone(url: str, target_path: Path, **kwargs) -> None` - Clone git repository
- Git operation utilities

### utils/comfyui_ops.py

**Purpose:** ComfyUI specific operations including cloning and version management.

**Dependencies:**
- Imports: utils.git, logging_config
- Imported by: factories.environment_factory

**Exports:**
- `clone_comfyui(target_path: Path, version: str|None) -> str|None` - Clone ComfyUI repository
- ComfyUI-specific operations

### utils/environment_logger.py

**Purpose:** Environment-specific logging configuration and management.

**Dependencies:**
- Imports: logging, pathlib, logging_config
- Imported by: core.workspace_manager

**Exports:**
- `EnvironmentLogger` - Environment-specific logging utilities

### utils/retry.py

**Purpose:** Retry and rate limiting utilities for network operations.

**Dependencies:**
- Imports: time, functools, logging_config
- Imported by: services.registry_client, services.github_client

**Exports:**
- Retry decorators and rate limiting utilities

### utils/version.py

**Purpose:** Version parsing and comparison utilities.

**Dependencies:**
- Imports: re, typing
- Imported by: Various modules for version handling

**Exports:**
- Version parsing and comparison functions

### utils/system_detector.py

**Purpose:** System information detection including Python version and platform.

**Dependencies:**
- Imports: platform, subprocess, pathlib, models.shared, logging_config
- Imported by: Migration and system detection operations

**Exports:**
- `SystemDetector` - System information detection

### utils/git_change_parser.py

**Purpose:** Git change parsing utilities for tracking modifications.

**Dependencies:**
- Imports: re, pathlib, logging_config
- Imported by: managers.git_manager

**Exports:**
- Git change parsing and analysis functions