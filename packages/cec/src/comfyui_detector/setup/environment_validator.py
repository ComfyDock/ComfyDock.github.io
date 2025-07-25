"""Environment validator for recreated ComfyUI environments."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from ..models.models import MigrationManifest
from ..integrations.uv import UVInterface
from ..logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of environment validation."""
    valid: bool
    installed_packages: Dict[str, str]
    installed_nodes: List[str]
    warnings: List[str]
    errors: List[str]


class EnvironmentValidator:
    """Validates recreated environments against manifests."""
    
    def __init__(self, target_path: Path, manifest: MigrationManifest):
        self.target_path = target_path
        self.manifest = manifest
        self.venv_path = target_path / ".venv"
        self.comfyui_path = target_path / "ComfyUI"
        self.uv_interface = UVInterface()
    
    def validate_all(self) -> ValidationResult:
        """Perform complete environment validation."""
        warnings = []
        errors = []
        
        # Get installed packages
        installed_packages = self.get_installed_packages()
        
        # Get installed custom nodes
        installed_nodes = self.get_installed_custom_nodes()
        
        # Validate packages
        pkg_warnings, pkg_errors = self.validate_packages(installed_packages)
        warnings.extend(pkg_warnings)
        errors.extend(pkg_errors)
        
        # Validate custom nodes
        node_warnings, node_errors = self.validate_custom_nodes(installed_nodes)
        warnings.extend(node_warnings)
        errors.extend(node_errors)
        
        # Validate ComfyUI installation
        comfyui_warnings, comfyui_errors = self.validate_comfyui_installation()
        warnings.extend(comfyui_warnings)
        errors.extend(comfyui_errors)
        
        return ValidationResult(
            valid=len(errors) == 0,
            installed_packages=installed_packages,
            installed_nodes=installed_nodes,
            warnings=warnings,
            errors=errors
        )
    
    def get_installed_packages(self) -> Dict[str, str]:
        """Get list of installed packages in the virtual environment."""
        try:
            result = self.uv_interface.list_packages(self.venv_path, format="freeze")
            if result.success and result.output:
                packages = {}
                for line in result.output.strip().split('\n'):
                    if '==' in line:
                        name, version = line.split('==', 1)
                        # Keep full version including CUDA suffixes
                        packages[name] = version
                return packages
            return {}
        except Exception as e:
            logger.error(f"Failed to get installed packages: {e}")
            return {}
    
    def get_installed_custom_nodes(self) -> List[str]:
        """Get list of installed custom nodes from ComfyUI/custom_nodes directory."""
        custom_nodes_dir = self.comfyui_path / "custom_nodes"
        installed_nodes = []
        
        if custom_nodes_dir.exists():
            for item in custom_nodes_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.') and not item.name.startswith('__'):
                    installed_nodes.append(item.name)
        
        return installed_nodes
    
    def validate_packages(self, installed: Dict[str, str]) -> Tuple[List[str], List[str]]:
        """Validate installed packages against manifest.
        
        Args:
            installed: Dictionary of package_name -> version from environment
            
        Returns:
            Tuple of (warnings, errors)
        """
        warnings = []
        errors = []
        
        # Check expected regular packages
        if self.manifest.dependencies.packages:
            manifest_packages = self.manifest.dependencies.packages
            for pkg_name, expected_version in manifest_packages.items():
                if pkg_name not in installed:
                    errors.append(f"Missing required package: {pkg_name}=={expected_version}")
                elif installed[pkg_name] != expected_version:
                    warnings.append(f"Version mismatch for {pkg_name}: "
                                  f"expected {expected_version}, got {installed[pkg_name]}")
        
        # Check PyTorch packages separately
        if self.manifest.dependencies.pytorch:
            pytorch_packages = self.manifest.dependencies.pytorch.packages
            for pkg_name, expected_version in pytorch_packages.items():
                if pkg_name not in installed:
                    errors.append(f"Missing PyTorch package: {pkg_name}=={expected_version}")
                elif installed[pkg_name] != expected_version:
                    warnings.append(f"PyTorch version mismatch for {pkg_name}: "
                                  f"expected {expected_version}, got {installed[pkg_name]}")
        
        return warnings, errors
    
    def validate_custom_nodes(self, installed: List[str]) -> Tuple[List[str], List[str]]:
        """Validate installed custom nodes against manifest.
        
        Args:
            installed: List of installed custom node names
            
        Returns:
            Tuple of (warnings, errors)
        """
        warnings = []
        errors = []
        
        expected_nodes = set(node.name for node in self.manifest.custom_nodes)
        installed_set = set(installed)
        
        missing_nodes = expected_nodes - installed_set
        for node in missing_nodes:
            errors.append(f"Missing custom node: {node}")
        
        extra_nodes = installed_set - expected_nodes
        for node in extra_nodes:
            warnings.append(f"Unexpected custom node found: {node}")
        
        return warnings, errors
    
    def validate_comfyui_installation(self) -> Tuple[List[str], List[str]]:
        """Validate ComfyUI installation integrity.
        
        Returns:
            Tuple of (warnings, errors)
        """
        warnings = []
        errors = []
        
        # Check if ComfyUI directory exists
        if not self.comfyui_path.exists():
            errors.append(f"ComfyUI directory not found: {self.comfyui_path}")
            return warnings, errors
        
        # Check for essential ComfyUI files
        essential_files = [
            self.comfyui_path / "main.py",
            self.comfyui_path / "nodes.py"
        ]
        
        # Check for essential directories
        essential_dirs = [
            self.comfyui_path / "custom_nodes"
        ]
        
        missing_files = []
        for file_path in essential_files:
            if not file_path.exists():
                missing_files.append(str(file_path))
        
        missing_dirs = []
        for dir_path in essential_dirs:
            if not dir_path.exists():
                missing_dirs.append(str(dir_path))
        
        if missing_files:
            for missing_file in missing_files:
                errors.append(f"Missing essential ComfyUI file: {missing_file}")
        
        if missing_dirs:
            for missing_dir in missing_dirs:
                errors.append(f"Missing essential ComfyUI directory: {missing_dir}")
        
        # Validate ComfyUI version if possible
        if self.manifest.system_info.comfyui_version:
            git_warnings, git_errors = self._validate_comfyui_version()
            warnings.extend(git_warnings)
            errors.extend(git_errors)
        
        return warnings, errors
    
    def _validate_comfyui_version(self) -> Tuple[List[str], List[str]]:
        """Validate that ComfyUI is at the expected version/commit.
        
        Returns:
            Tuple of (warnings, errors)
        """
        warnings = []
        errors = []
        
        expected_version = self.manifest.system_info.comfyui_version
        
        try:
            # Check current git commit/tag in ComfyUI directory
            from ..common import run_command
            
            # Get current commit hash
            result = run_command(
                ["git", "rev-parse", "HEAD"],
                cwd=self.comfyui_path,
                check=True,
                timeout=30
            )
            
            if result.returncode == 0:
                current_commit = result.stdout.strip()
                
                # Try to resolve expected version to commit hash
                try:
                    expected_result = run_command(
                        ["git", "rev-parse", expected_version],
                        cwd=self.comfyui_path,
                        check=True,
                        timeout=30
                    )
                    
                    if expected_result.returncode == 0:
                        expected_commit = expected_result.stdout.strip()
                        
                        if current_commit != expected_commit:
                            warnings.append(
                                f"ComfyUI version mismatch: expected {expected_version} "
                                f"({expected_commit[:8]}), got {current_commit[:8]}"
                            )
                    else:
                        warnings.append(f"Could not resolve expected ComfyUI version: {expected_version}")
                        
                except Exception as e:
                    warnings.append(f"Could not validate ComfyUI version: {e}")
            else:
                warnings.append("Could not determine current ComfyUI version")
                
        except Exception as e:
            warnings.append(f"Error validating ComfyUI version: {e}")
        
        return warnings, errors