"""EnvironmentRecreator for recreating ComfyUI environments from manifests."""

import json
import os
import time
from pathlib import Path
from typing import Union, Optional

from ..setup.environment_setup import EnvironmentSetup
from ..package_installer import PackageInstaller
from ..setup.custom_node_installer import CustomNodeInstaller
from ..setup.environment_validator import EnvironmentValidator
from ..models.models import MigrationManifest, EnvironmentResult
from ..logging_config import get_logger
from ..exceptions import ValidationError
from ..progress import ProgressReporter

logger = get_logger(__name__)


class EnvironmentRecreator:
    """Recreates ComfyUI environments from captured manifests.
    
    This class handles the initialization and creation of directory structure
    for a new ComfyUI environment based on a migration manifest.
    """
    
    def __init__(
        self,
        manifest_path: Union[str, Path],
        target_path: Union[str, Path],
        uv_cache_path: Union[str, Path],
        python_install_path: Union[str, Path],
        progress_reporter: Optional[ProgressReporter] = None,
        enable_cache: bool = True
    ):
        """Initialize the EnvironmentRecreator.
        
        Args:
            manifest_path: Path to the migration manifest JSON file
            target_path: Target directory for the new environment
            uv_cache_path: UV cache directory path
            python_install_path: Python installation cache directory path
            progress_reporter: Optional progress reporter
            enable_cache: Whether to enable custom node caching
            
        Raises:
            ValidationError: If parameters are invalid or manifest is malformed
        """
        logger.info("Initializing EnvironmentRecreator")
        
        # Initialize paths and manifest
        self.manifest_path = Path(manifest_path)
        self.target_path = Path(target_path)
        self.uv_cache_path = Path(uv_cache_path)
        self.python_install_path = Path(python_install_path)
        self.progress = progress_reporter or ProgressReporter()
        self.enable_cache = enable_cache
        
        # Set UV environment variables for cache and python directories
        os.environ["UV_CACHE_DIR"] = str(self.uv_cache_path)
        os.environ["UV_PYTHON_INSTALL_DIR"] = str(self.python_install_path)
        logger.debug(f"Set UV_CACHE_DIR to: {self.uv_cache_path}")
        logger.debug(f"Set UV_PYTHON_INSTALL_DIR to: {self.python_install_path}")
        
        # Load and validate manifest
        self.manifest = self._load_manifest()
        
        # Initialize component recreators
        self.environment_setup = EnvironmentSetup(self.target_path)
        self.package_installer = PackageInstaller(
            self.target_path, 
            self.uv_cache_path,
            self.python_install_path
        )
        # Pass enable_cache to CustomNodeInstaller
        self.custom_node_installer = CustomNodeInstaller(
            self.target_path,
            enable_cache=self.enable_cache
        )
        self.environment_validator = EnvironmentValidator(self.target_path, self.manifest)
        
        logger.info(f"Successfully initialized EnvironmentRecreator for {self.target_path}")
        if not self.enable_cache:
            logger.info("Custom node caching is disabled")
    
    def _load_manifest(self) -> MigrationManifest:
        """Load and validate the migration manifest.
        
        Returns:
            Loaded and validated MigrationManifest
            
        Raises:
            ValidationError: If manifest cannot be loaded or is invalid
        """
        try:
            with open(self.manifest_path, 'r') as f:
                manifest_data = json.load(f)
            
            manifest = MigrationManifest.from_dict(manifest_data)
            manifest.validate()
            return manifest
            
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON in manifest file: {e}")
        except Exception as e:
            raise ValidationError(f"Invalid manifest: {e}")
    
    def recreate(self) -> EnvironmentResult:
        """Recreate the complete ComfyUI environment from the manifest.
        
        This is the main orchestration method that coordinates all recreation steps
        as specified in the PRD. It performs the complete environment setup in order:
        1. Create directory structure and virtual environment
        2. Install ComfyUI 
        3. Install all packages from manifest (PyTorch, regular, git, editable)
        4. Install custom nodes
        5. Validate recreated environment
        
        Returns:
            EnvironmentResult: Comprehensive result containing success status,
                paths, installed packages/nodes, warnings, errors, and duration
        
        Raises:
            ValidationError: If any recreation step fails critically
        """
        start_time = time.time()
        warnings = []
        errors = []
        
        logger.info(f"Starting environment recreation at {self.target_path}")
        if self.enable_cache:
            logger.info("Custom node caching is enabled")
        else:
            logger.info("Custom node caching is disabled")
            
        self.progress.start_phase("Environment Recreation")
        
        try:
            # Step 1: Create directory structure and virtual environment
            logger.info("Step 1/5: Setting up environment structure")
            self.progress.start_task("Creating directory structure and virtual environment")
            self.environment_setup.setup_all(self.manifest.system_info)
            self.progress.complete_task(f"Python {self.manifest.system_info.python_version}")
            
            # Step 2: Install ComfyUI
            logger.info("Step 2/5: Installing ComfyUI")
            self.progress.start_task("Installing ComfyUI")
            self.progress.update_task("Cloning repository")
            self.environment_setup.install_comfyui(self.manifest.system_info.comfyui_version)
            self.progress.complete_task(f"version {self.manifest.system_info.comfyui_version}")
            
            # Step 3: Install all packages
            logger.info("Step 3/5: Installing packages")
            total_packages = (
                len(self.manifest.dependencies.packages) +
                len(self.manifest.dependencies.pytorch.packages if self.manifest.dependencies.pytorch else {}) +
                len(self.manifest.dependencies.git_requirements) +
                len(self.manifest.dependencies.editable_installs)
            )
            
            self.progress.start_task("Installing Python packages", total_packages)
            self.package_installer.progress = self.progress  # Pass progress reporter
            package_results = self.package_installer.install_all(self.manifest.dependencies)
            self.progress.complete_task(f"{package_results.installed_count} packages installed")
            warnings.extend(package_results.warnings)
            errors.extend(package_results.errors)
            
            # Step 4: Install custom nodes
            logger.info("Step 4/5: Installing custom nodes")
            self.progress.start_task("Installing custom nodes", len(self.manifest.custom_nodes))
            self.custom_node_installer.progress = self.progress  # Pass progress reporter
            node_results = self.custom_node_installer.install_all(self.manifest.custom_nodes)
            self.progress.complete_task(f"{len(node_results.installed_nodes)} nodes installed")
            warnings.extend(node_results.warnings)
            errors.extend(node_results.errors)
            
            # Step 5: Validate environment
            logger.info("Step 5/5: Validating environment")
            self.progress.start_task("Validating environment")
            validation_results = self.environment_validator.validate_all()
            self.progress.complete_task("Validation complete")
            warnings.extend(validation_results.warnings)
            errors.extend(validation_results.errors)
            
            duration = time.time() - start_time
            success = len(errors) == 0
            
            logger.info(f"Environment recreation completed in {duration:.2f} seconds")
            
            return EnvironmentResult(
                success=success,
                environment_path=self.target_path,
                venv_path=self.target_path / ".venv",
                comfyui_path=self.target_path / "ComfyUI",
                installed_packages=validation_results.installed_packages,
                installed_nodes=validation_results.installed_nodes,
                warnings=warnings,
                errors=errors,
                duration_seconds=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Environment recreation failed: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
            
            return EnvironmentResult(
                success=False,
                environment_path=self.target_path,
                venv_path=self.target_path / ".venv",
                comfyui_path=self.target_path / "ComfyUI",
                installed_packages={},
                installed_nodes=[],
                warnings=warnings,
                errors=errors,
                duration_seconds=duration
            )