# ComfyUI Environment Detector

This module detects and captures all system dependencies and requirements from an existing ComfyUI setup for migration to containerized environments.

## Module Structure

```
comfyui_detector/
├── __init__.py          # Package initialization
├── cli.py               # Command-line interface and main entry point
├── detector.py          # Main ComfyUIEnvironmentDetector class
├── constants.py         # Configuration constants
├── validators/          # External validation modules
│   ├── __init__.py
│   ├── github.py        # GitHub release/tag validation
│   └── registry.py      # Comfy Registry API validation
├── utils/               # Utility functions
│   ├── __init__.py
│   ├── version.py       # Version comparison utilities
│   ├── git.py           # Git repository utilities
│   ├── requirements.py  # Requirements parsing utilities
│   └── system.py        # System detection utilities
└── models/              # Data models (future expansion)
    └── __init__.py
```

## Key Components

### detector.py
- `ComfyUIEnvironmentDetector`: Main class that orchestrates the detection process
- Handles custom node scanning, package detection, and manifest generation

### validators/
- `GitHubReleaseChecker`: Validates custom nodes against GitHub releases and tags
- `ComfyRegistryValidator`: Validates custom nodes against the Comfy Registry API

### utils/
- `version.py`: PyTorch package detection and version utilities
- `git.py`: Git repository information extraction
- `requirements.py`: Requirements.txt and pyproject.toml parsing
- `system.py`: Python/CUDA/PyTorch version detection, package extraction

### constants.py
- PyTorch package names for special handling
- Custom node directory blacklist
- Default configuration values

## Usage

```python
from comfyui_detector import ComfyUIEnvironmentDetector

# Basic usage
detector = ComfyUIEnvironmentDetector("/path/to/comfyui")
config = detector.detect_all()

# With registry validation
detector = ComfyUIEnvironmentDetector("/path/to/comfyui", validate_registry=True)
config = detector.detect_all()
```

## Command Line

```bash
# Basic detection
python -m comfyui_detector /path/to/comfyui

# With registry validation
python -m comfyui_detector /path/to/comfyui --validate-registry

# Custom output directory
python -m comfyui_detector /path/to/comfyui --output-dir ./results
```

## Output Files

- `comfyui_migration.json`: Lean manifest for environment recreation
- `comfyui_detection_log.json`: Detailed analysis for debugging
- `comfyui_requirements.txt`: Python package requirements