# ComfyUI Environment Capture (CEC) Tool - Product Requirements Document

## 1. Executive Summary

The ComfyUI Environment Capture (CEC) Tool is a comprehensive environment detection and reproduction system designed to capture existing ComfyUI installations and recreate them in any target environment - whether containerized, local, or cloud-based. By leveraging UV's modern package management capabilities and implementing intelligent dependency resolution strategies, this tool enables users to capture complex ComfyUI setups—including custom nodes, specific package versions, and platform-specific dependencies—into a canonical environment definition that can be reliably reproduced anywhere.

The tool follows a minimalist philosophy, generating a compact migration manifest (typically <5KB) that contains only the essential installation instructions, while preserving comprehensive analysis data in separate files for debugging purposes. The same codebase handles both environment capture and recreation, ensuring consistency and code reuse.

## 2. Problem Statement

### Current Challenges

1. **Environment Complexity**: ComfyUI installations evolve organically over time, accumulating:

   - Mixed installation methods (pip, git, manual copies)
   - Conflicting dependency versions between custom nodes
   - Platform-specific packages and binaries
   - Undocumented or implicit dependencies
   - Editable installations and local development packages

2. **Reproduction Barriers**:

   - Loss of functionality when recreating environments
   - Inability to capture the full dependency tree accurately
   - Custom nodes with complex installation scripts
   - Git-based dependencies at specific commits
   - System-level dependencies not captured by pip

3. **Reproducibility Issues**:

   - "Works on my machine" syndrome
   - Inconsistent environments between team members
   - Difficulty sharing complete working environments
   - Platform-specific dependencies breaking cross-platform compatibility

4. **Technical Debt**:
   - No standardized format for environment definitions
   - Lack of validation for captured environments
   - Missing dependency resolution conflict handling
   - Separate tools for capture vs reproduction

## 3. Solution Overview

The ComfyUI Environment Capture Tool provides a comprehensive solution through:

### 3.1 Intelligent Environment Detection

- Multi-stage detection process analyzing virtual environments, system packages, and custom nodes
- Dependency tree analysis using UV and native pip APIs
- Git repository state capture for development installations
- Platform-specific dependency identification and mapping

#### Python Executable vs Virtual Environment Path

The tool focuses on the Python executable path rather than virtual environment paths for greater flexibility:
- Users can specify any Python executable (system, venv, conda, etc.)
- The tool validates that the Python can actually run ComfyUI
- UV handles package operations using the `--python` parameter consistently
- This approach supports more diverse Python setups including system-wide installations

### 3.2 Canonical Environment Definition

The tool generates a consistent environment definition format that enables reproduction anywhere:

#### 3.2.1 Core Output Files

- **comfyui_migration.json**: Minimal manifest (<5KB) with exact installation instructions
- **comfyui_detection_log.json**: Comprehensive analysis data for debugging and advanced use
- **comfyui_requirements.txt**: Standard pip format for compatibility and manual verification
- **uv.lock** (optional): Complete dependency resolution state for exact reproduction

#### 3.2.2 Reproduction Targets

The same manifest supports multiple reproduction scenarios:

- **Container Environments**: Docker, Podman, or other container runtimes
- **Local Environments**: Direct installation on host systems
- **Cloud Environments**: AWS, GCP, or other cloud platforms
- **Development Environments**: Local development with editable installs

### 3.3 Integrated Reproduction Engine

- Same codebase for detection and reproduction
- Direct UV integration for all package operations
- Shared utility functions and validation logic
- Consistent error handling and logging

### 3.4 Environment-Agnostic Design

- No assumptions about target environment type
- Orchestration layer (e.g., ComfyDock) handles environment-specific setup
- CEC focuses solely on Python/ComfyUI environment management
- Clean API for external tools to consume

## 4. Core Features and Requirements

### 4.1 Environment Detection

#### 4.1.1 Python Environment Analysis

- **Requirement**: Automatically detect Python interpreter and virtual environment
- **Implementation**: Already implemented in `utils/system.py`
  ```python
  def find_python_executable(comfyui_path: Path, python_hint: Path = None) -> Optional[Path]:
      # Find the Python executable used by ComfyUI
      # 1. If user provided python path, validate it works with ComfyUI
      # 2. Check for virtual environments in standard locations
      # 3. Check .venv file pointing to venv location
      # 4. Fall back to system Python if it can run ComfyUI
  ```
- **Acceptance Criteria**:
  - Detects 95%+ of standard virtual environment setups
  - Handles venv, virtualenv, and conda environments
  - Gracefully falls back to system Python when appropriate

#### 4.1.2 Comprehensive Package Detection

- **Requirement**: Capture all installed packages with full metadata using UV
- **Implementation**: Already implemented in `utils/system.py` using `UVInterface`
  ```python
  def extract_packages_with_uv(python_executable: Path, 
                            comfyui_path: Path, pytorch_package_names: set) -> Tuple[Dict[str, str], Dict[str, str], List[str]]:
      # Uses UV to extract packages from the Python environment
      # Uses python parameter instead of venv_path for more flexibility
      # Separates PyTorch packages
      # Identifies editable installations
  ```
- **Acceptance Criteria**:
  - Captures 100% of pip-installed packages via UV
  - Preserves exact versions
  - Identifies installation sources (PyPI, Git, local)
  - Handles editable installations correctly

#### 4.1.3 Custom Node Intelligence

- **Requirement**: Deep analysis of custom nodes beyond basic detection
- **Implementation**: Already implemented in `detector.py`
  ```python
  def _scan_single_custom_node(self, node_dir: Path) -> Dict:
      # Detects installation method
      # Parses requirements.txt, pyproject.toml
      # Identifies post-install scripts
      # Validates against registry and GitHub
  ```
- **Acceptance Criteria**:
  - Identifies 95%+ of custom node installation methods
  - Captures all Python dependencies from various formats
  - Detects post-installation scripts

### 4.2 Environment Reproduction (NEW)

#### 4.2.1 Environment Recreation Engine

- **Requirement**: Recreate ComfyUI environments from captured manifests
- **Implementation Plan**:
  ```python
  class EnvironmentRecreator:
      def __init__(self,
                   manifest_path: Path,
                   target_path: Path,
                   uv_cache_path: Path,
                   python_install_path: Path):
          """Initialize recreator with paths for UV operations."""
          self.manifest = MigrationManifest.from_json(manifest_path.read_text())
          self.target_path = target_path
          self.uv_cache_path = uv_cache_path
          self.python_install_path = python_install_path

      def recreate(self) -> EnvironmentResult:
          # 1. Create directory structure
          # 2. Set up Python virtual environment via UV
          # 3. Clone/install ComfyUI
          # 4. Install PyTorch packages
          # 5. Install regular packages
          # 6. Install custom nodes
          # 7. Run post-install scripts
          # 8. Validate installation
  ```

#### 4.2.2 Directory Structure

- **Requirement**: Consistent environment layout
- **Structure**:
  ```
  target_environment/
  ├── ComfyUI/          # ComfyUI installation
  │   ├── models/
  │   ├── input/
  │   ├── output/
  │   └── custom_nodes/
  └── .venv/            # Python virtual environment
  ```

#### 4.2.3 UV-Driven Package Management

- **Requirement**: All package operations through UV
- **Implementation**: Leverage existing `UVInterface` class

  ```python
  # Create venv with specific Python version
  uv.venv_create(venv_path, python_version=manifest.system_info.python_version)
  # Note: UV uses 'python' parameter consistently across all operations

  # Install PyTorch with correct index
  if manifest.dependencies.pytorch:
      uv.pip_install(
          packages=[f"{k}=={v}" for k, v in manifest.dependencies.pytorch.packages.items()],
          index_url=manifest.dependencies.pytorch.index_url
      )

  # Install regular packages
  uv.pip_install(packages=[f"{k}=={v}" for k, v in manifest.dependencies.packages.items()])
  ```

#### 4.2.4 Custom Node Installation

- **Requirement**: Support all installation methods
- **Installation Methods**:
  1. **Archive**: Download and extract from URL
  2. **Git**: Clone repository at specific ref
  3. **Local**: Copy from local path (with warnings)
- **Post-Installation**: Execute install.py/setup.py if flagged

### 4.3 Validation and Testing

#### 4.3.1 Environment Validation

- **Requirement**: Verify recreated environments match source
- **Validation Steps**:
  1. Package version verification
  2. Custom node import testing
  3. ComfyUI startup validation
  4. Dependency conflict checking

#### 4.3.2 Cross-Platform Support

- **Requirement**: Handle platform differences gracefully
- **Implementation**:
  - Platform-specific package handling
  - Path normalization
  - Binary dependency warnings
  - CUDA/CPU variant management

## 5. Technical Architecture

### 5.1 Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI / API Interface                       │
├─────────────────────────────────────────────────────────────┤
│                  Core CEC Library                            │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │  Detection   │  │ Reproduction │  │   Validation    │   │
│  │   Engine     │  │   Engine     │  │     Engine      │   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                    Shared Services                           │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │  Package     │  │ Custom Node  │  │   Dependency    │   │
│  │  Analyzer    │  │   Manager    │  │    Resolver     │   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                 Integration Layer                            │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │     UV       │  │   GitHub     │  │    Registry     │   │
│  │  Interface   │  │     API      │  │      API        │   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Data Flow

```
Detection Flow:
Source Environment → Detector → Analyzer → Manifest Generator
                                              ↓
                                    ┌─────────────────────┐
                                    │ comfyui_migration.json │
                                    └─────────────────────┘
                                              ↓
Reproduction Flow:                            ↓
Target Path + Manifest → Recreator → UV Operations → Validation
                            ↓
                    ┌─────────────────────┐
                    │ New Environment     │
                    │ ├── ComfyUI/       │
                    │ └── .venv/         │
                    └─────────────────────┘
```

### 5.3 API Design

```python
# Public API for orchestration tools
from comfyui_detector import ComfyUIEnvironmentDetector, EnvironmentRecreator

# Detection
detector = ComfyUIEnvironmentDetector(
    comfyui_path=Path("/path/to/comfyui"),
    venv_path=Path("/path/to/venv"),  # Optional, auto-detected if not provided
    validate_registry=True
)
manifest = detector.detect_all()

# Reproduction
recreator = EnvironmentRecreator(
    manifest_path=Path("comfyui_migration.json"),
    target_path=Path("/new/environment"),
    uv_cache_path=Path("/shared/uv_cache"),
    python_install_path=Path("/shared/uv/python")
)
result = recreator.recreate()
```

## 6. User Journey and Workflows

### 6.1 Environment Capture Flow

1. **Initiation**

   ```bash
   cec detect /path/to/comfyui --python /path/to/python --output-dir ./capture
   # Note: --python parameter is optional and specifies the Python executable, not venv path
   ```

2. **Detection Phase**

   - "Detecting Python environment... ✓"
   - "Analyzing 247 packages with UV... ✓"
   - "Scanning 15 custom nodes... ✓"

3. **Analysis Phase**

   - "Resolving dependencies..."
   - "Validating against registry..."
   - "Generating manifest files..."

4. **Output Generation**
   - `comfyui_migration.json` (2KB) - Minimal manifest
   - `comfyui_detection_log.json` (150KB) - Full analysis
   - `comfyui_requirements.txt` (1KB) - Package list

### 6.2 Environment Recreation Flow

1. **Initiation**

   ```bash
   cec recreate ./capture/comfyui_migration.json --target ./new_env
   ```

2. **Setup Phase**

   - "Creating environment structure... ✓"
   - "Setting up Python 3.11.7 with UV... ✓"
   - "Cloning ComfyUI... ✓"

3. **Installation Phase**

   - "Installing PyTorch 2.1.0+cu121... ✓"
   - "Installing 150 packages... ✓"
   - "Installing 15 custom nodes... ✓"

4. **Validation Phase**
   - "Verifying package versions... ✓"
   - "Testing custom node imports... ✓"
   - "Environment ready at: ./new_env"

### 6.3 Integration with Orchestration Tools

```python
# Example: ComfyDock integration
from comfyui_detector import ComfyUIEnvironmentDetector, EnvironmentRecreator

class ComfyDockEnvironmentManager:
    def capture_to_container(self, source_path: Path):
        # Use CEC to capture
        detector = ComfyUIEnvironmentDetector(source_path)
        manifest = detector.detect_all()

        # Create container with captured environment
        recreator = EnvironmentRecreator(
            manifest_path=manifest.manifest_path,
            target_path=self.container_path,
            uv_cache_path=self.uv_cache,
            python_install_path=self.python_cache
        )
        recreator.recreate()
```

## 7. Data Models and Schemas

### 7.1 Migration Manifest Schema (v1.0)

Already implemented in `models/models.py`:

```python
@dataclass
class MigrationManifest:
    system_info: SystemInfo
    custom_nodes: List[CustomNodeSpec]
    dependencies: DependencySpec
    schema_version: str = "1.0"
```

### 7.2 Recreation Result Model (NEW)

```python
@dataclass
class EnvironmentResult:
    """Result of environment recreation."""
    success: bool
    environment_path: Path
    venv_path: Path
    comfyui_path: Path
    installed_packages: Dict[str, str]
    installed_nodes: List[str]
    warnings: List[str]
    errors: List[str]
    duration_seconds: float
```

## 8. Testing Strategy

### 8.1 Test-Driven Development (TDD) Approach

The CEC project follows strict TDD methodology, building functionality incrementally with comprehensive unit tests before implementation.

#### 8.1.1 TDD Workflow

1. **Write failing test** → Define expected behavior
2. **Implement minimal code** → Make test pass
3. **Refactor** → Improve code quality while maintaining tests
4. **Repeat** → Build functionality incrementally

#### 8.1.2 Unit Test Focus Areas for Recreator

**Test Structure for Recreator:**

```python
class TestEnvironmentRecreator:
    """Unit tests for environment recreation."""

    def test_creates_directory_structure(self):
        """Should create ComfyUI/ and .venv/ directories."""

    def test_validates_manifest_before_recreation(self):
        """Should validate manifest schema and content."""

    def test_handles_missing_python_version(self):
        """Should handle unavailable Python versions gracefully."""

    def test_installs_pytorch_with_correct_index(self):
        """Should use correct PyTorch index URL."""

    def test_handles_custom_node_archive_install(self):
        """Should download and extract archive nodes."""

    def test_handles_custom_node_git_install(self):
        """Should clone git repositories at correct ref."""

    def test_runs_post_install_scripts(self):
        """Should execute install.py when flagged."""

    def test_validates_recreated_environment(self):
        """Should verify all packages installed correctly."""
```

**Implementation Priorities:**

1. **Basic Structure** (Week 1)

   - Directory creation
   - UV venv setup
   - ComfyUI cloning

2. **Package Installation** (Week 2)

   - PyTorch index handling
   - Regular package installation
   - Editable installs
   - Git requirements

3. **Custom Nodes** (Week 3)

   - Archive extraction
   - Git cloning
   - Post-install scripts
   - Error recovery

4. **Validation** (Week 4)
   - Package verification
   - Import testing
   - Performance optimization

### 8.2 Unit Testing Framework

```
tests/
├── unit/
│   ├── detector/          # Existing detector tests
│   ├── recreator/         # New recreator tests
│   │   ├── test_environment_setup.py
│   │   ├── test_package_installation.py
│   │   ├── test_custom_node_installation.py
│   │   ├── test_validation.py
│   │   └── test_error_recovery.py
│   └── shared/            # Tests for shared utilities
├── fixtures/
│   ├── manifests/         # Test manifests
│   ├── mock_environments/ # Mock env structures
│   └── mock_packages/     # Mock package data
└── conftest.py
```

### 8.3 Integration Testing (Future)

After core functionality is complete:

- End-to-end capture → recreate workflows
- Cross-platform testing
- Performance benchmarking
- Error recovery scenarios

## 9. Success Metrics

### 9.1 Technical Metrics

- **Capture Success Rate**: >95% for standard environments
- **Recreation Success Rate**: >90% from valid manifests
- **Package Match Accuracy**: >98% version match
- **Performance**: <5 minutes for average recreation
- **Manifest Size**: <5KB for migration.json

### 9.2 Code Quality Metrics

- **Test Coverage**: >90% for all modules
- **Shared Code**: >60% code reuse between detector/recreator
- **UV Integration**: 100% package operations via UV
- **Error Messages**: Clear, actionable error messages

### 9.3 User Experience Metrics

- **First-Time Success**: >90% succeed without intervention
- **Cross-Platform**: Works on Linux, macOS, Windows
- **Documentation**: Complete API docs and examples
- **Integration**: Easy integration with orchestration tools

## 10. Implementation Phases

### Phase 1: Core Detection (Complete)

- ✓ Environment detection
- ✓ Package capture with UV
- ✓ Custom node analysis
- ✓ Manifest generation

### Phase 2: Recreation Engine (Months 1-2)

- Environment setup with UV
- Package installation
- Custom node installation
- Basic validation

### Phase 3: Advanced Features (Month 3)

- Cross-platform handling
- Error recovery
- Performance optimization
- Comprehensive validation

### Phase 4: Polish & Integration (Month 4)

- API refinement
- Documentation
- Example integrations
- Performance tuning

## 11. Risk Mitigation

### 11.1 Technical Risks

- **Risk**: UV command failures

  - **Mitigation**: Comprehensive error handling, fallback strategies

- **Risk**: Platform-specific packages

  - **Mitigation**: Platform detection, conditional installation

- **Risk**: Missing custom node sources
  - **Mitigation**: Multiple fallback URLs, local directory support

### 11.2 Integration Risks

- **Risk**: Breaking API changes

  - **Mitigation**: Versioned API, deprecation notices

- **Risk**: Performance bottlenecks
  - **Mitigation**: Parallel operations where possible, caching

## 12. Future Considerations

### 12.1 Advanced Features

- Incremental environment updates
- Environment comparison tools
- Automated migration testing
- Custom node dependency resolution

### 12.2 Ecosystem Integration

- Plugin system for custom handlers
- Registry API enhancements
- Workflow compatibility checking
- Model management integration

## 13. Conclusion

The ComfyUI Environment Capture Tool provides a complete solution for capturing and reproducing ComfyUI environments across any target platform. By maintaining a single codebase for both detection and recreation, leveraging UV for all package operations, and providing a clean API for orchestration tools, CEC enables reliable environment management while remaining agnostic to the final deployment target.

The tool's focus on canonical environment definitions, comprehensive testing through TDD, and shared code between detection and recreation ensures maintainability and reliability. Success will be measured by the tool's ability to accurately capture diverse ComfyUI installations and reliably reproduce them anywhere, making ComfyUI environment management predictable and accessible for all users.
