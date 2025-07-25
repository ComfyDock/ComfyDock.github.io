"""ComfyUI Environment Detector Package."""

# Import core classes and exceptions
from .core import ComfyUIEnvironmentDetector, EnvironmentRecreator, ManifestGenerator
from .detection import SystemDetector, PackageDetector, CustomNodeScanner
from .exceptions import (
    ComfyUIDetectorError,
    EnvironmentError,
    PythonNotFoundError,
    VirtualEnvNotFoundError,
    PackageDetectionError,
    UVNotInstalledError,
    CustomNodeError,
    ValidationError,
    ManifestError,
    DependencyResolutionError
)
from .logging_config import setup_logging, get_logger
from .common import (
    run_command,
    safe_json_load,
    safe_json_dump,
    normalize_package_name,
    is_valid_version,
    format_size,
    parse_git_url,
    extract_archive_name,
    validate_path
)

__all__ = [
    # Core classes
    'ComfyUIEnvironmentDetector',
    'EnvironmentRecreator',
    'SystemDetector',
    'PackageDetector',
    'CustomNodeScanner',
    'ManifestGenerator',
    
    # Exceptions
    'ComfyUIDetectorError',
    'EnvironmentError',
    'PythonNotFoundError',
    'VirtualEnvNotFoundError',
    'PackageDetectionError',
    'UVNotInstalledError',
    'CustomNodeError',
    'ValidationError',
    'ManifestError',
    'DependencyResolutionError',
    
    # Logging
    'setup_logging',
    'get_logger',
    
    # Common utilities
    'run_command',
    'safe_json_load',
    'safe_json_dump',
    'normalize_package_name',
    'is_valid_version',
    'format_size',
    'parse_git_url',
    'extract_archive_name',
    'validate_path'
]