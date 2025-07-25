"""Custom exceptions for ComfyUI Environment Capture."""


class ComfyUIDetectorError(Exception):
    """Base exception for all detector errors."""
    pass


class EnvironmentError(ComfyUIDetectorError):
    """Raised when environment detection fails."""
    pass


class PythonNotFoundError(EnvironmentError):
    """Raised when Python executable cannot be found."""
    pass


class VirtualEnvNotFoundError(EnvironmentError):
    """Raised when virtual environment cannot be detected."""
    pass


class PackageDetectionError(ComfyUIDetectorError):
    """Raised when package detection fails."""
    pass


class UVNotInstalledError(PackageDetectionError):
    """Raised when UV is not installed."""
    pass


class UVCommandError(PackageDetectionError):
    """Raised when UV command execution fails."""
    pass


class CustomNodeError(ComfyUIDetectorError):
    """Raised when custom node analysis fails."""
    pass


class ValidationError(ComfyUIDetectorError):
    """Raised when validation fails."""
    pass


class ManifestError(ComfyUIDetectorError):
    """Raised when manifest generation fails."""
    pass


class DependencyResolutionError(ComfyUIDetectorError):
    """Raised when dependency resolution fails."""
    pass