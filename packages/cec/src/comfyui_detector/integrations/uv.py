"""UV package manager interface module.

This module provides a centralized interface for UV command operations,
including package management, virtual environment handling, and consistent
error handling across the codebase.
"""

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ..common import run_command
from ..exceptions import (
    UVNotInstalledError,
    UVCommandError
)
from ..logging_config import get_logger
from ..models.models import Package

logger = get_logger(__name__)

INSTALL_TIMEOUT = 300 # 5 minutes


@dataclass
class UVResult:
    """Result object for UV operations."""
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None


class UVInterface:
    """Interface for UV package manager operations."""
    
    def __init__(self, verbose: bool = False, quiet: bool = False):
        """Initialize UV interface.
        
        Args:
            verbose: Enable verbose output
            quiet: Suppress non-error output
        """
        self.verbose = verbose
        self.quiet = quiet
        self._uv_binary = None
        self._check_uv_installed()
    
    def _check_uv_installed(self) -> None:
        """Check if UV is installed and available."""
        if self._uv_binary is None:
            self._uv_binary = shutil.which("uv")
            if self._uv_binary is None:
                raise UVNotInstalledError(
                    "uv is not installed. Please install uv first: "
                    "curl -LsSf https://astral.sh/uv/install.sh | sh"
                )
    
    def get_uv_version(self) -> str:
        """Get the installed UV version.
        
        Returns:
            UV version string
            
        Raises:
            UVCommandError: If UV command fails
        """
        try:
            result = run_command([self._uv_binary, "--version"])
            if result.returncode == 0:
                # Extract version from output like "uv 0.1.0"
                version = result.stdout.strip().split()[-1]
                logger.debug(f"UV version: {version}")
                return version
            else:
                raise UVCommandError(f"Failed to get UV version: {result.stderr}")
        except Exception as e:
            raise UVCommandError(f"Error getting UV version: {e}")
    
    def list_packages(self, venv_path: Path = None, python: Path = None, 
                      format: str = "columns", outdated: bool = False) -> UVResult:
        """List installed packages.
        
        Args:
            venv_path: Path to the virtual environment (optional if python provided)
            python: Path to Python executable (takes precedence over venv_path)
            format: Output format ("columns", "freeze", "json")
            outdated: Only show outdated packages
            
        Returns:
            UVResult with package list
        """
        cmd = [self._uv_binary, "pip", "list"]
        
        # UV uses different format names
        uv_format_map = {
            "columns": "columns",
            "freeze": "freeze", 
            "json": "json"
        }
        cmd.extend(["--format", uv_format_map.get(format, "columns")])
        
        if outdated:
            cmd.append("--outdated")
        
        # Set up python path and environment
        env = {}
        if python:
            # Use provided python directly
            cmd.extend(["--python", str(python)])
        elif venv_path:
            # Derive python from venv path
            python_path = venv_path / "bin" / "python"
            if not python_path.exists():
                python_path = venv_path / "Scripts" / "python.exe"  # Windows
            cmd.extend(["--python", str(python_path)])
            env = {"VIRTUAL_ENV": str(venv_path)}
        else:
            raise ValueError("Either python or venv_path must be provided")
        
        try:
            result = run_command(cmd, env=env)
            if result.returncode == 0:
                return UVResult(success=True, output=result.stdout)
            else:
                return UVResult(success=False, error=result.stderr)
        except Exception as e:
            return UVResult(success=False, error=str(e))
    
    def install_packages(self, venv_path: Path, packages: List[str],
                        uv_cache: Optional[Path] = None,
                        index_url: Optional[str] = None,
                        upgrade: bool = False,
                        prerelease: bool = False) -> UVResult:
        """Install packages to a virtual environment.
        
        Args:
            venv_path: Path to the virtual environment
            packages: List of packages to install
            uv_cache: UV cache directory path
            index_url: Custom PyPI index URL
            upgrade: Whether to upgrade packages
            prerelease: Whether to allow pre-release versions
            
        Returns:
            UVResult with installation status
        """
        cmd = [self._uv_binary, "pip", "install"]
        
        # Set python path
        python_path = venv_path / "bin" / "python"
        if not python_path.exists():
            python_path = venv_path / "Scripts" / "python.exe"
        cmd.extend(["--python", str(python_path)])
        
        if upgrade:
            cmd.append("--upgrade")
        
        if prerelease:
            cmd.append("--prerelease=allow")
        
        if index_url:
            cmd.extend(["--index-url", index_url])
        
        # Add packages
        cmd.extend(packages)
        
        # Set environment variables for cache if specified
        env = {"VIRTUAL_ENV": str(venv_path)}
        if uv_cache:
            env["UV_CACHE_DIR"] = str(uv_cache)
        
        try:
            result = run_command(cmd, env=env, timeout=300)
            if result.returncode == 0:
                return UVResult(success=True, output=result.stdout)
            else:
                return UVResult(success=False, error=result.stderr)
        except Exception as e:
            return UVResult(success=False, error=str(e))
    
    
    def create_venv(self, path: Path, python_version: Optional[str] = None,
                    system_site_packages: bool = False, seed: bool = False) -> UVResult:
        """Create a virtual environment.
        
        Args:
            path: Path where to create the virtual environment
            python_version: Specific Python version to use
            system_site_packages: Give venv access to system packages
            seed: Install seed packages (pip, setuptools, wheel)
            
        Returns:
            UVResult with operation status
        """
        cmd = [self._uv_binary, "venv", str(path)]
        
        if python_version:
            cmd.extend(["--python", python_version])
        
        if system_site_packages:
            cmd.append("--system-site-packages")
            
        if seed:
            cmd.append("--seed")
        
        try:
            result = run_command(cmd)
            if result.returncode == 0:
                return UVResult(success=True, output=result.stdout)
            else:
                return UVResult(success=False, error=result.stderr)
        except Exception as e:
            return UVResult(success=False, error=str(e))
    
    def run_python(self, venv_path: Path, code: str, args: List[str] = None,
                   is_file: bool = False) -> UVResult:
        """Run Python code in a virtual environment.
        
        Args:
            venv_path: Path to the virtual environment
            code: Python code to execute (or script content if is_file=True)
            args: Additional arguments for the script
            is_file: Whether code represents a file that was read
            
        Returns:
            UVResult with execution output
        """
        cmd = [self._uv_binary, "run"]
        
        # set env to have VIRTUAL_ENV set to the venv_path
        env = {"VIRTUAL_ENV": str(venv_path)}
        
        # Add python command
        cmd.extend(["python", "-c", code])
        
        # Add any additional arguments
        if args:
            cmd.extend(args)
        
        try:
            result = run_command(cmd, env=env)
            if result.returncode == 0:
                return UVResult(success=True, output=result.stdout)
            else:
                return UVResult(success=False, error=result.stderr)
        except Exception as e:
            return UVResult(success=False, error=str(e))
    
    def install_requirements(self, venv_path: Path, requirements_file: Path,
                            uv_cache: Optional[Path] = None,
                            index_url: Optional[str] = None,
                            upgrade: bool = False) -> UVResult:
        """Install packages from requirements file.
        
        Args:
            venv_path: Path to the virtual environment
            requirements_file: Path to requirements.txt
            uv_cache: UV cache directory path
            index_url: Custom PyPI index URL
            upgrade: Whether to upgrade packages
            
        Returns:
            UVResult with installation status
        """
        cmd = [self._uv_binary, "pip", "install", "-r", str(requirements_file)]
        
        # Set python path
        python_path = venv_path / "bin" / "python"
        if not python_path.exists():
            python_path = venv_path / "Scripts" / "python.exe"
        cmd.extend(["--python", str(python_path)])
        
        if upgrade:
            cmd.append("--upgrade")
        
        if index_url:
            cmd.extend(["--index-url", index_url])
        
        # Set environment variables for cache if specified
        env = {"VIRTUAL_ENV": str(venv_path)}
        if uv_cache:
            env["UV_CACHE_DIR"] = str(uv_cache)
        
        try:
            result = run_command(cmd, env=env, timeout=INSTALL_TIMEOUT)
            if result.returncode == 0:
                return UVResult(success=True, output=result.stdout)
            else:
                return UVResult(success=False, error=result.stderr)
        except Exception as e:
            return UVResult(success=False, error=str(e))
    
    def uninstall_packages(self, venv_path: Path, packages: List[str]) -> UVResult:
        """Uninstall packages from virtual environment.
        
        Args:
            venv_path: Path to the virtual environment
            packages: List of packages to uninstall
            
        Returns:
            UVResult with uninstall status
        """
        cmd = [self._uv_binary, "pip", "uninstall"]
        
        # Set python path
        python_path = venv_path / "bin" / "python"
        if not python_path.exists():
            python_path = venv_path / "Scripts" / "python.exe"
        cmd.extend(["--python", str(python_path)])
        
        # Add packages
        cmd.extend(packages)
        
        try:
            cwd = venv_path.parent
            result = run_command(cmd, cwd=cwd)
            if result.returncode == 0:
                return UVResult(success=True, output=result.stdout)
            else:
                return UVResult(success=False, error=result.stderr)
        except Exception as e:
            return UVResult(success=False, error=str(e))
    
    def freeze_packages(self, venv_path: Path, all_packages: bool = False) -> UVResult:
        """Output installed packages in requirements format.
        
        Args:
            venv_path: Path to the virtual environment
            all_packages: Include all packages including pip, setuptools
            
        Returns:
            UVResult with frozen package list
        """
        cmd = [self._uv_binary, "pip", "freeze"]
        
        # Set python path
        python_path = venv_path / "bin" / "python"
        if not python_path.exists():
            python_path = venv_path / "Scripts" / "python.exe"
        cmd.extend(["--python", str(python_path)])
        
        if all_packages:
            cmd.append("--all")
        
        try:
            cwd = venv_path.parent
            result = run_command(cmd, cwd=cwd)
            if result.returncode == 0:
                return UVResult(success=True, output=result.stdout)
            else:
                return UVResult(success=False, error=result.stderr)
        except Exception as e:
            return UVResult(success=False, error=str(e))
    
    def generate_lockfile(self, project_path: Path, upgrade: bool = False,
                         upgrade_packages: Optional[List[str]] = None) -> UVResult:
        """Generate or update a lockfile for the project.
        
        Args:
            project_path: Path to project directory
            upgrade: Upgrade all dependencies
            upgrade_packages: Specific packages to upgrade
            
        Returns:
            UVResult with lockfile generation status
        """
        cmd = [self._uv_binary, "lock"]
        
        if upgrade:
            cmd.append("--upgrade")
        
        if upgrade_packages:
            for package in upgrade_packages:
                cmd.extend(["--upgrade-package", package])
        
        try:
            result = run_command(cmd, cwd=project_path)
            if result.returncode == 0:
                return UVResult(success=True, output=result.stdout)
            else:
                return UVResult(success=False, error=result.stderr)
        except Exception as e:
            return UVResult(success=False, error=str(e))
    
    def sync_environment(self, project_path: Path, 
                        venv_path: Optional[Path] = None) -> UVResult:
        """Sync environment with the lockfile.
        
        Args:
            project_path: Path to project directory
            venv_path: Optional specific venv path (otherwise uses default)
            
        Returns:
            UVResult with sync status
        """
        cmd = [self._uv_binary, "sync"]
        
        # If specific venv path provided, we need to set it
        # UV doesn't have a direct --venv flag for sync, so we use the project context
        
        try:
            result = run_command(cmd, cwd=project_path)
            if result.returncode == 0:
                return UVResult(success=True, output=result.stdout)
            else:
                return UVResult(success=False, error=result.stderr)
        except Exception as e:
            return UVResult(success=False, error=str(e))
    
    def _parse_pip_list_output(self, output: str, format: str) -> List[Package]:
        """Parse pip list output into Package objects.
        
        Args:
            output: Raw pip list output
            format: Output format used
            
        Returns:
            List of Package objects
        """
        packages = []
        
        if format == "freeze":
            for line in output.strip().split('\n'):
                if line and not line.startswith('#'):
                    if line.startswith('-e '):
                        # Handle editable installs
                        packages.append(Package(
                            name=self._extract_editable_name(line),
                            version="editable",
                            is_editable=True
                        ))
                    elif '==' in line:
                        try:
                            name, version = line.split('==', 1)
                            name = name.strip()
                            version = version.strip()
                            
                            # Safety check: ensure version doesn't contain '=='
                            if version.startswith('=='):
                                version = version[2:]
                                logger.warning(f"Removed == prefix from version: {version}")
                            
                            logger.debug(f"Parsed line '{line}' -> package='{name}', version='{version}'")
                            packages.append(Package(
                                name=name,
                                version=version,
                                is_editable=False
                            ))
                        except ValueError:
                            logger.warning(f"Could not parse package line: {line}")
        
        return packages
    
    def _extract_editable_name(self, editable_line: str) -> str:
        """Extract package name from editable install line.
        
        Args:
            editable_line: Line starting with '-e '
            
        Returns:
            Package name
        """
        # Handle various editable formats
        line = editable_line[3:]  # Remove '-e '
        
        if '#egg=' in line:
            return line.split('#egg=')[-1]
        
        # Try to extract from path
        if '/' in line:
            return Path(line).name
        
        return line

