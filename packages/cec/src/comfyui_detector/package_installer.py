"""Package installer for all dependency types."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from .models.models import DependencySpec, PyTorchSpec
from .integrations.uv import UVInterface, UVResult
from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class PackageInstallResult:
    """Result of package installation operations."""
    success: bool
    installed_count: int
    failed_packages: List[str]
    warnings: List[str]
    errors: List[str]


class PackageInstaller:
    """Handles all package installation operations."""
    
    def __init__(self, target_path: Path, uv_cache_path: Path, python_install_path: Path):
        self.target_path = target_path
        self.uv_cache_path = uv_cache_path
        self.python_install_path = python_install_path
        self.venv_path = target_path / ".venv"
        self.uv_interface = UVInterface()
    
    def install_all(self, dependencies: DependencySpec) -> PackageInstallResult:
        """Install all dependencies in the correct order."""
        warnings = []
        errors = []
        installed_count = 0
        failed_packages = []
        current = 0
        
        # 1. PyTorch packages first
        if dependencies.pytorch:
            if hasattr(self, 'progress'):
                self.progress.update_task("Installing PyTorch packages", current)
            result = self.install_pytorch_packages(dependencies.pytorch)
            installed_count += result.installed_count
            failed_packages.extend(result.failed_packages)
            warnings.extend(result.warnings)
            errors.extend(result.errors)
            current += len(dependencies.pytorch.packages) if dependencies.pytorch else 0
        
        # 2. Regular packages
        if dependencies.packages:
            if hasattr(self, 'progress'):
                self.progress.update_task("Installing regular packages", current)
            result = self.install_regular_packages(dependencies.packages)
            installed_count += result.installed_count
            failed_packages.extend(result.failed_packages)
            warnings.extend(result.warnings)
            errors.extend(result.errors)
            current += len(dependencies.packages)
        
        # 3. Git requirements
        if dependencies.git_requirements:
            if hasattr(self, 'progress'):
                self.progress.update_task("Installing git requirements", current)
            result = self.install_git_requirements(dependencies.git_requirements)
            installed_count += result.installed_count
            failed_packages.extend(result.failed_packages)
            warnings.extend(result.warnings)
            errors.extend(result.errors)
            current += len(dependencies.git_requirements)
        
        # 4. Editable installs
        if dependencies.editable_installs:
            if hasattr(self, 'progress'):
                self.progress.update_task("Installing editable packages", current)
            result = self.install_editable_packages(dependencies.editable_installs)
            installed_count += result.installed_count
            failed_packages.extend(result.failed_packages)
            warnings.extend(result.warnings)
            errors.extend(result.errors)
            current += len(dependencies.editable_installs)
        
        return PackageInstallResult(
            success=len(errors) == 0,
            installed_count=installed_count,
            failed_packages=failed_packages,
            warnings=warnings,
            errors=errors
        )
    
    def install_pytorch_packages(self, pytorch_spec: PyTorchSpec) -> PackageInstallResult:
        """Install PyTorch packages with correct index URL.
        
        Installs PyTorch packages specified in the manifest using the 
        appropriate index URL for the CUDA version or CPU variant.
        
        Args:
            pytorch_spec: PyTorchSpec containing packages and index URL
        
        Returns:
            PackageInstallResult with installation results
        """
        logger.info("Installing PyTorch packages")
        
        try:
            # Extract packages and index URL from PyTorchSpec
            packages = []
            for name, version in pytorch_spec.packages.items():
                # Check if version already contains constraint operators
                if any(op in version for op in ['>=', '<=', '==', '!=', '~=', '>', '<']):
                    # Version already has constraints, use as-is
                    packages.append(f"{name}{version}")
                else:
                    # Plain version number, add == for exact match
                    packages.append(f"{name}=={version}")
            
            # Install PyTorch packages with index URL
            result = self.uv_interface.install_packages(
                venv_path=self.venv_path,
                packages=packages,
                uv_cache=self.uv_cache_path,
                index_url=pytorch_spec.index_url
            )
            
            if not result.success:
                logger.error(f"Failed to install PyTorch packages: {result.error}")
                return PackageInstallResult(
                    success=False,
                    installed_count=0,
                    failed_packages=packages,
                    warnings=[],
                    errors=[f"Failed to install PyTorch packages: {result.error}"]
                )
            
            logger.info(f"Successfully installed {len(packages)} PyTorch packages")
            return PackageInstallResult(
                success=True,
                installed_count=len(packages),
                failed_packages=[],
                warnings=[],
                errors=[]
            )
            
        except Exception as e:
            error_msg = f"Unexpected error installing PyTorch packages: {e}"
            logger.error(error_msg)
            return PackageInstallResult(
                success=False,
                installed_count=0,
                failed_packages=list(pytorch_spec.packages.keys()),
                warnings=[],
                errors=[error_msg]
            )
    
    def install_regular_packages(self, packages: Dict[str, str]) -> PackageInstallResult:
        """Install regular packages with exact versions.
        
        Installs regular Python packages specified in the manifest with 
        their exact versions to ensure reproducible environments.
        
        Args:
            packages: Dictionary of package_name -> version
        
        Returns:
            PackageInstallResult with installation results
        """
        logger.info("Installing regular packages")
        
        try:
            # Convert package dict to list format: ["package==version", ...]
            package_list = []
            for name, version in packages.items():
                # Check if version already contains constraint operators
                if any(op in version for op in ['>=', '<=', '==', '!=', '~=', '>', '<']):
                    # Version already has constraints, use as-is
                    package_list.append(f"{name}{version}")
                else:
                    # Plain version number, add == for exact match
                    package_list.append(f"{name}=={version}")
            
            # Try to install all packages at once first (more efficient)
            result = self.uv_interface.install_packages(
                venv_path=self.venv_path,
                packages=package_list,
                uv_cache=self.uv_cache_path
            )
            
            if result.success:
                logger.info(f"Successfully installed {len(package_list)} regular packages")
                return PackageInstallResult(
                    success=True,
                    installed_count=len(package_list),
                    failed_packages=[],
                    warnings=[],
                    errors=[]
                )
            
            # If batch installation failed, try individual package installation
            logger.warning(f"Batch installation failed: {result.error}")
            logger.info("Falling back to individual package installation...")
            
            installed_count = 0
            failed_packages = []
            warnings = []
            errors = []
            
            for package_spec in package_list:
                try:
                    # Try installing individual package
                    individual_result = self._install_single_package(package_spec)
                    
                    if individual_result.success:
                        installed_count += 1
                        logger.debug(f"✅ Installed: {package_spec}")
                    else:
                        failed_packages.append(package_spec)
                        error_msg = f"Failed to install {package_spec}: {individual_result.error}"
                        errors.append(error_msg)
                        logger.warning(f"❌ {error_msg}")
                        
                        # Try with pre-release flag for dev packages
                        if any(marker in package_spec.lower() for marker in ['.dev', 'dev0', 'alpha', 'beta', 'rc']):
                            logger.info(f"Retrying {package_spec} with pre-release flag...")
                            prerelease_result = self._install_single_package(package_spec, allow_prerelease=True)
                            if prerelease_result.success:
                                installed_count += 1
                                failed_packages.remove(package_spec)
                                errors.remove(error_msg)
                                warnings.append(f"Installed {package_spec} with pre-release flag")
                                logger.info(f"✅ Installed with pre-release: {package_spec}")
                            
                except Exception as e:
                    error_msg = f"Unexpected error installing {package_spec}: {e}"
                    failed_packages.append(package_spec)
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            # Report results
            success_rate = installed_count / len(package_list) if package_list else 1.0
            overall_success = success_rate >= 0.8  # Consider successful if 80%+ packages installed
            
            if failed_packages:
                logger.warning(f"Failed to install {len(failed_packages)}/{len(package_list)} packages")
                for pkg in failed_packages[:5]:  # Show first 5 failures
                    logger.warning(f"  - {pkg}")
                if len(failed_packages) > 5:
                    logger.warning(f"  ... and {len(failed_packages) - 5} more")
            
            if installed_count > 0:
                logger.info(f"Successfully installed {installed_count}/{len(package_list)} regular packages")
            
            return PackageInstallResult(
                success=overall_success,
                installed_count=installed_count,
                failed_packages=failed_packages,
                warnings=warnings,
                errors=errors
            )
            
        except Exception as e:
            error_msg = f"Unexpected error installing packages: {e}"
            logger.error(error_msg)
            return PackageInstallResult(
                success=False,
                installed_count=0,
                failed_packages=list(packages.keys()),
                warnings=[],
                errors=[error_msg]
            )
    
    def _install_single_package(self, package_spec: str, allow_prerelease: bool = False) -> UVResult:
        """Install a single package with optional pre-release support.
        
        Args:
            package_spec: Package specification (e.g., "package==1.0.0")
            allow_prerelease: Whether to allow pre-release versions
            
        Returns:
            UVResult with installation status
        """
        try:
            # Build command for single package installation
            packages = [package_spec]
            
            # Use the existing uv_interface with prerelease support
            return self.uv_interface.install_packages(
                venv_path=self.venv_path,
                packages=packages,
                uv_cache=self.uv_cache_path,
                prerelease=allow_prerelease
            )
                
        except Exception as e:
            return UVResult(success=False, output="", error=str(e))
    
    def install_git_requirements(self, git_requirements: List[str]) -> PackageInstallResult:
        """Install git-based package requirements.
        
        Installs packages from git repositories specified in the manifest,
        including specific branches, tags, or commits.
        
        Args:
            git_requirements: List of git requirement strings (already in "git+https://..." format)
        
        Returns:
            PackageInstallResult with installation results
        """
        logger.info("Installing git requirements")
        
        try:
            # Process each git requirement (already in "git+https://..." format)
            packages = git_requirements.copy()
            
            # Install git requirements
            result = self.uv_interface.install_packages(
                venv_path=self.venv_path,
                packages=packages,
                uv_cache=self.uv_cache_path
            )
            
            if not result.success:
                logger.error(f"Failed to install git requirements: {result.error}")
                return PackageInstallResult(
                    success=False,
                    installed_count=0,
                    failed_packages=packages,
                    warnings=[],
                    errors=[f"Failed to install git requirements: {result.error}"]
                )
            
            logger.info(f"Successfully installed {len(packages)} git requirements")
            return PackageInstallResult(
                success=True,
                installed_count=len(packages),
                failed_packages=[],
                warnings=[],
                errors=[]
            )
            
        except Exception as e:
            error_msg = f"Unexpected error installing git requirements: {e}"
            logger.error(error_msg)
            return PackageInstallResult(
                success=False,
                installed_count=0,
                failed_packages=git_requirements,
                warnings=[],
                errors=[error_msg]
            )
    
    def install_editable_packages(self, editable_installs: List[str]) -> PackageInstallResult:
        """Install editable packages from manifest.
        
        Installs editable/development packages specified in the manifest,
        which are typically local packages or git repositories in development mode.
        
        Args:
            editable_installs: List of editable install strings (already in "-e path" format)
        
        Returns:
            PackageInstallResult with installation results
        """
        logger.info("Installing editable packages")
        
        try:
            # Process each editable install (already in "-e path" format)
            packages = editable_installs.copy()
            
            # Install editable packages
            result = self.uv_interface.install_packages(
                venv_path=self.venv_path,
                packages=packages,
                uv_cache=self.uv_cache_path
            )
            
            if not result.success:
                logger.error(f"Failed to install editable packages: {result.error}")
                return PackageInstallResult(
                    success=False,
                    installed_count=0,
                    failed_packages=packages,
                    warnings=[],
                    errors=[f"Failed to install editable packages: {result.error}"]
                )
            
            logger.info(f"Successfully installed {len(packages)} editable packages")
            return PackageInstallResult(
                success=True,
                installed_count=len(packages),
                failed_packages=[],
                warnings=[],
                errors=[]
            )
            
        except Exception as e:
            error_msg = f"Unexpected error installing editable packages: {e}"
            logger.error(error_msg)
            return PackageInstallResult(
                success=False,
                installed_count=0,
                failed_packages=editable_installs,
                warnings=[],
                errors=[error_msg]
            )