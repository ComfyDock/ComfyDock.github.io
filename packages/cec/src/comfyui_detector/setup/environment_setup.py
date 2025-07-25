"""Environment setup for directory structure and base installations."""

from pathlib import Path

from ..models.models import SystemInfo
from ..integrations.uv import UVInterface
from ..common import run_command
from ..exceptions import ValidationError, UVCommandError
from ..logging_config import get_logger

logger = get_logger(__name__)


class EnvironmentSetup:
    """Handles environment directory structure and base setup."""
    
    def __init__(self, target_path: Path):
        self.target_path = target_path
        self.uv_interface = UVInterface()
    
    def setup_all(self, system_info: SystemInfo) -> None:
        """Set up complete environment structure."""
        self.create_directory_structure()
        self.create_virtual_environment(system_info.python_version)
    
    def create_directory_structure(self) -> None:
        """Create the required directory structure for the environment.
        
        Creates:
            - target_path/ComfyUI/  (main ComfyUI installation directory)
            - target_path/.venv/    (virtual environment directory)
            
        Raises:
            ValidationError: If directories cannot be created
        """
        logger.info(f"Creating directory structure at {self.target_path}")
        
        try:
            # Create target directory if it doesn't exist
            self.target_path.mkdir(parents=True, exist_ok=True)
            
            # Create ComfyUI directory
            comfyui_dir = self.target_path / "ComfyUI"
            comfyui_dir.mkdir(exist_ok=True)
            logger.debug(f"Created ComfyUI directory: {comfyui_dir}")
            
            # Create .venv directory
            venv_dir = self.target_path / ".venv"
            venv_dir.mkdir(exist_ok=True)
            logger.debug(f"Created .venv directory: {venv_dir}")
            
            logger.info("Directory structure created successfully")
            
        except PermissionError as e:
            raise ValidationError(f"Failed to create directory due to permissions: {e}")
        except OSError as e:
            raise ValidationError(f"Failed to create directory: {e}")
    
    def create_virtual_environment(self, python_version: str) -> None:
        """Create Python virtual environment using UV with manifest Python version.
        
        Creates a virtual environment at target_path/.venv using the exact Python 
        version specified in the manifest. The directory structure is created 
        first if it doesn't exist.
        
        Args:
            python_version: Python version to use for the virtual environment
        
        Raises:
            ValidationError: If virtual environment creation fails or Python version is invalid
        """
        logger.info("Creating virtual environment")
        
        # Ensure directory structure exists first
        self.create_directory_structure()
        
        # Validate Python version
        if not python_version or not python_version.strip():
            raise ValidationError("Invalid Python version in manifest: empty or missing")
        
        # Create virtual environment path
        venv_path = self.target_path / ".venv"
        
        try:
            # Create virtual environment
            result = self.uv_interface.create_venv(path=venv_path, python_version=python_version)
            
            if not result.success:
                raise UVCommandError(f"Failed to create virtual environment: {result.error}")
            
            logger.info(f"Successfully created virtual environment at {venv_path} with Python {python_version}")
            
        except UVCommandError as e:
            raise ValidationError(f"Failed to create virtual environment: {e}")
        except Exception as e:
            raise ValidationError(f"Unexpected error creating virtual environment: {e}")
    
    def install_comfyui(self, comfyui_version: str) -> None:
        """Install ComfyUI at the version specified in the manifest.
        
        Clones ComfyUI from the official repository and checks out the
        specified version/tag/commit from manifest.system_info.comfyui_version.
        
        The method:
        1. Ensures directory structure exists
        2. Clones ComfyUI repository to target_path/ComfyUI
        3. Checks out the specified version/tag/commit
        4. Validates the installation was successful
        
        Args:
            comfyui_version: ComfyUI version/tag/commit to install
        
        Raises:
            ValidationError: If ComfyUI installation fails
        """
        logger.info("Installing ComfyUI")
        
        # Ensure directory structure exists first
        self.create_directory_structure()
        
        # Validate ComfyUI version
        if not comfyui_version or not comfyui_version.strip():
            raise ValidationError("Invalid ComfyUI version in manifest: empty or missing")
        
        # ComfyUI repository URL and target path
        comfyui_repo_url = "https://github.com/comfyanonymous/ComfyUI"
        comfyui_path = self.target_path / "ComfyUI"
        
        try:
            # Clone ComfyUI repository (with longer timeout for large repos)
            logger.info(f"Cloning ComfyUI from {comfyui_repo_url}")
            run_command(
                ["git", "clone", comfyui_repo_url, str(comfyui_path)],
                check=True,
                timeout=300  # 5 minutes for git clone
            )
            
            # Checkout specific version/tag/commit
            logger.info(f"Checking out ComfyUI version: {comfyui_version}")
            run_command(
                ["git", "checkout", comfyui_version],
                cwd=comfyui_path,
                check=True,
                timeout=60  # 1 minute for checkout
            )
            
            # Validate installation
            self._validate_comfyui_installation(comfyui_path)
            
            logger.info(f"Successfully installed ComfyUI version {comfyui_version} at {comfyui_path}")
            
        except Exception as e:
            error_msg = str(e)
            if "clone" in error_msg:
                raise ValidationError(f"Failed to clone ComfyUI: {e}")
            elif "checkout" in error_msg:
                raise ValidationError(f"Failed to checkout ComfyUI version '{comfyui_version}': {e}")
            else:
                raise ValidationError(f"Git command failed during ComfyUI installation: {e}")
    
    def _validate_comfyui_installation(self, comfyui_path: Path) -> None:
        """Validate that ComfyUI was installed correctly.
        
        Checks for the existence of key ComfyUI files and directories.
        
        Args:
            comfyui_path: Path to the ComfyUI installation directory
            
        Raises:
            ValidationError: If validation fails
        """
        logger.debug(f"Validating ComfyUI installation at {comfyui_path}")
        
        # Check for essential ComfyUI files
        essential_files = [
            comfyui_path / "main.py",
            comfyui_path / "nodes.py"
        ]
        
        # Check for essential directories
        essential_dirs = [
            comfyui_path / "custom_nodes"
        ]
        
        missing_files = []
        for file_path in essential_files:
            if not file_path.exists():
                missing_files.append(str(file_path))
        
        missing_dirs = []
        for dir_path in essential_dirs:
            if not dir_path.exists():
                missing_dirs.append(str(dir_path))
        
        if missing_files or missing_dirs:
            error_parts = []
            if missing_files:
                error_parts.append(f"Missing files: {', '.join(missing_files)}")
            if missing_dirs:
                error_parts.append(f"Missing directories: {', '.join(missing_dirs)}")
            
            raise ValidationError(f"ComfyUI installation validation failed. {'; '.join(error_parts)}")
        
        logger.debug("ComfyUI installation validation passed")