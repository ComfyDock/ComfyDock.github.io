"""Custom node installer for ComfyUI custom nodes."""

import hashlib
import re
import shutil
import tarfile
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional
from urllib.error import URLError, HTTPError

from ..models.models import CustomNodeSpec
from ..integrations.uv import UVInterface
from ..common import run_command
from ..exceptions import ValidationError, ComfyUIDetectorError
from ..logging_config import get_logger
from ..utils.custom_node_cache import CustomNodeCacheManager

logger = get_logger(__name__)


@dataclass
class CustomNodeInstallResult:
    """Result of custom node installation operations."""
    success: bool
    installed_nodes: List[str]
    failed_nodes: List[str]
    warnings: List[str]
    errors: List[str]


class CustomNodeInstaller:
    """Handles custom node installation operations."""
    
    def __init__(self, target_path: Path, enable_cache: bool = True):
        self.target_path = target_path
        self.comfyui_path = target_path / "ComfyUI"
        self.custom_nodes_path = self.comfyui_path / "custom_nodes"
        self.venv_path = target_path / ".venv"
        self.uv_interface = UVInterface()
        
        # Initialize cache manager
        self.enable_cache = enable_cache
        self.cache_manager = CustomNodeCacheManager() if enable_cache else None
    
    def install_all(self, custom_nodes: List[CustomNodeSpec]) -> CustomNodeInstallResult:
        """Install all custom nodes from the manifest."""
        installed_nodes = []
        failed_nodes = []
        warnings = []
        errors = []
        
        # Sort custom nodes by install_order if present
        sorted_nodes = sorted(custom_nodes, key=lambda n: getattr(n, 'install_order', 999))
        
        for i, node_spec in enumerate(sorted_nodes, 1):
            if hasattr(self, 'progress'):
                self.progress.update_task(f"Installing {node_spec.name}", i)
                
            try:
                success, node_name = self._install_single_node(node_spec)
                
                if success:
                    installed_nodes.append(node_name)
                    
                    # Handle post-install scripts
                    if node_spec.has_post_install:
                        self._run_post_install_scripts(node_name)
                    
                    # Install node requirements
                    self._install_node_requirements(node_name)
                else:
                    failed_nodes.append(node_spec.name)
                    warnings.append(f"Failed to install custom node: {node_spec.name}")
                    
            except Exception as e:
                logger.error(f"Error installing {node_spec.name}: {e}")
                failed_nodes.append(node_spec.name)
                errors.append(f"Failed to install {node_spec.name}: {str(e)}")
        
        return CustomNodeInstallResult(
            success=len(errors) == 0,
            installed_nodes=installed_nodes,
            failed_nodes=failed_nodes,
            warnings=warnings,
            errors=errors
        )
    
    def _install_single_node(self, node_spec: CustomNodeSpec) -> Tuple[bool, str]:
        """Install a single custom node based on its install method."""
        # Check cache first if enabled
        if self.enable_cache and self.cache_manager:
            cached_path = self.cache_manager.get_cached_path(node_spec)
            if cached_path:
                logger.info(f"Found {node_spec.name} in cache")
                target_dir = self.custom_nodes_path / node_spec.name
                
                # Copy from cache
                if self.cache_manager.copy_from_cache(node_spec, target_dir):
                    logger.info(f"Successfully installed {node_spec.name} from cache")
                    return True, node_spec.name
                else:
                    logger.warning(f"Failed to copy {node_spec.name} from cache, downloading fresh")
        
        # Proceed with normal installation
        if node_spec.install_method == "archive":
            return self.install_from_archive(node_spec)
        elif node_spec.install_method == "git":
            return self.install_from_git(node_spec)
        elif node_spec.install_method == "local":
            return self.install_local(node_spec)
        else:
            raise ValidationError(f"Unknown install method: {node_spec.install_method}")
    
    def install_from_archive(self, node_spec: CustomNodeSpec) -> Tuple[bool, str]:
        """Install custom node from archive URL.
        
        Args:
            node_spec: CustomNodeSpec with install_method='archive'
            
        Returns:
            Tuple of (success: bool, node_name: str)
            
        Raises:
            ValidationError: On download/extraction failures or invalid parameters
        """
        logger.debug(f"Installing custom node from archive: {node_spec.name}")
        
        # Validate install method
        if node_spec.install_method != 'archive':
            raise ValidationError(
                f"Expected install_method 'archive', got '{node_spec.install_method}'"
            )
        
        # Get URL - we'll determine the actual archive type after download
        url = node_spec.url
        
        # Create temporary directory for download and extraction
        temp_dir = tempfile.mkdtemp()
        try:
            logger.debug(f"Created temporary directory: {temp_dir}")
            
            # Download archive with a generic name first
            archive_path = Path(temp_dir) / "archive"
            
            logger.info(f"Downloading archive from: {url}")
            try:
                urllib.request.urlretrieve(url, str(archive_path))
                logger.debug(f"Archive downloaded to: {archive_path}")
            except (URLError, HTTPError) as e:
                # Try fallback URL if available
                if hasattr(node_spec, 'fallback_url') and node_spec.fallback_url:
                    logger.warning(f"Primary URL failed, trying fallback: {node_spec.fallback_url}")
                    try:
                        urllib.request.urlretrieve(node_spec.fallback_url, str(archive_path))
                        logger.debug(f"Archive downloaded from fallback URL to: {archive_path}")
                    except (URLError, HTTPError) as fallback_e:
                        raise ValidationError(f"Failed to download archive from both primary and fallback URLs: {e}, {fallback_e}")
                else:
                    raise ValidationError(f"Failed to download archive from {url}: {e}")
            
            # Detect actual archive type by examining file content
            archive_type = self._detect_archive_type(archive_path)
            logger.debug(f"Detected archive type: {archive_type}")
            
            if archive_type == 'unknown':
                raise ValidationError(f"Unsupported or corrupted archive format for {node_spec.name}")
            
            # Verify hash if provided
            if hasattr(node_spec, 'hash') and node_spec.hash:
                logger.debug("Verifying archive hash...")
                if not self._verify_file_hash(archive_path, node_spec.hash):
                    raise ValidationError(f"Archive hash verification failed for {node_spec.name}")
                logger.debug("Archive hash verified successfully")
            
            # Extract archive
            extract_dir = Path(temp_dir) / "extracted"
            extract_dir.mkdir(exist_ok=True)
            
            logger.debug(f"Extracting archive to: {extract_dir}")
            try:
                if archive_type in ['tar.gz', 'tar']:
                    # For tar.gz files, use r:gz mode; for tar files, use r mode
                    mode = 'r:gz' if archive_type == 'tar.gz' else 'r'
                    with tarfile.open(str(archive_path), mode) as tar:
                        tar.extractall(str(extract_dir))
                        extracted_items = tar.getnames()
                elif archive_type == 'zip':
                    with zipfile.ZipFile(str(archive_path), 'r') as zip_file:
                        zip_file.extractall(str(extract_dir))
                        extracted_items = zip_file.namelist()
                else:
                    raise ValidationError(f"Unsupported archive type: {archive_type}")
                
                logger.debug(f"Archive extracted. Items: {extracted_items[:5]}...")  # Log first 5 items
            except (tarfile.ReadError, zipfile.BadZipFile) as e:
                raise ValidationError(f"Failed to extract archive {archive_path}: {e}")
            
            # Determine source directory from extracted contents
            source_dir = self._find_archive_source_directory(extract_dir, extracted_items)
            
            # Cache the node if caching is enabled
            if self.enable_cache and self.cache_manager:
                try:
                    self.cache_manager.cache_node(
                        node_spec, 
                        source_dir,
                        archive_path
                    )
                    logger.info(f"Cached {node_spec.name} for future use")
                except Exception as e:
                    logger.warning(f"Failed to cache {node_spec.name}: {e}")
            
            # Create target directory in custom_nodes
            target_dir = self.custom_nodes_path / node_spec.name
            
            logger.info(f"Moving custom node to: {target_dir}")
            
            # Move the extracted content to target directory
            if target_dir.exists():
                shutil.rmtree(target_dir)
            shutil.move(str(source_dir), str(target_dir))
            
            logger.info(f"Successfully installed custom node: {node_spec.name}")
            return True, node_spec.name
            
        finally:
            # Clean up temporary directory
            try:
                shutil.rmtree(temp_dir)
                logger.debug(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temporary directory {temp_dir}: {e}")
    
    def _find_archive_source_directory(self, extract_dir: Path, extracted_items: List[str]) -> Path:
        """Find the source directory from extracted archive contents.
        
        Args:
            extract_dir: Directory where archive was extracted
            extracted_items: List of extracted file/directory paths
            
        Returns:
            Path to the source directory to move
            
        Raises:
            ValidationError: If archive structure is invalid
        """
        # Check if all items are under a single root directory
        root_dirs = set()
        for item in extracted_items:
            if '/' in item:
                root_dir = item.split('/')[0]
                root_dirs.add(root_dir)
            else:
                # File in root of archive
                return extract_dir
        
        if len(root_dirs) == 1:
            # Single root directory - use it
            root_dir = root_dirs.pop()
            source_path = extract_dir / root_dir
            if source_path.is_dir():
                return source_path
        
        # Multiple root directories or no directories - use extract_dir itself
        return extract_dir
    
    def _detect_archive_type(self, file_path: Path) -> str:
        """Detect the actual archive type by examining file headers.
        
        Args:
            file_path: Path to the downloaded file
            
        Returns:
            Archive type: 'zip', 'tar.gz', or 'unknown'
        """
        with open(file_path, 'rb') as f:
            header = f.read(512)  # Read more data for tar signature check
        
        # Check for ZIP file signature
        if header.startswith(b'PK\x03\x04') or header.startswith(b'PK\x05\x06') or header.startswith(b'PK\x07\x08'):
            return 'zip'
        
        # Check for gzip signature (tar.gz files start with gzip signature)
        if header.startswith(b'\x1f\x8b'):
            return 'tar.gz'
        
        # Check for raw tar signature (at offset 257)
        if len(header) >= 262 and header[257:262] == b'ustar':
            return 'tar'
        
        return 'unknown'

    def _verify_file_hash(self, file_path: Path, expected_hash: str) -> bool:
        """Verify file hash against expected SHA256 hash.
        
        Args:
            file_path: Path to file to verify
            expected_hash: Expected SHA256 hash (hex string)
            
        Returns:
            True if hash matches, False otherwise
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        computed_hash = sha256_hash.hexdigest()
        return computed_hash.lower() == expected_hash.lower()
    
    def install_from_git(self, node_spec: CustomNodeSpec) -> Tuple[bool, str]:
        """Install custom node from git repository.
        
        Args:
            node_spec: CustomNodeSpec with install_method='git'
            
        Returns:
            Tuple of (success: bool, node_name: str)
            
        Raises:
            ValidationError: On git command failures or invalid parameters
        """
        logger.debug(f"Installing custom node from git: {node_spec.name}")
        
        # Validate install method
        if node_spec.install_method != 'git':
            raise ValidationError(
                f"Expected install_method 'git', got '{node_spec.install_method}'"
            )
        
        # Validate URL
        url = node_spec.url
        if not url or not url.strip():
            raise ValidationError("Git URL is required for git installation method")
        
        # Validate URL format (basic validation for git URLs)
        git_url_patterns = [
            r'^https://[^/]+/[^/]+/[^/]+$',  # https://github.com/user/repo
            r'^https://[^/]+/[^/]+/[^/]+\.git$',  # https://github.com/user/repo.git
            r'^git@[^:]+:[^/]+/[^/]+\.git$',  # git@github.com:user/repo.git
            r'^git@[^:]+:[^/]+/[^/]+$',  # git@github.com:user/repo
        ]
        
        if not any(re.match(pattern, url) for pattern in git_url_patterns):
            raise ValidationError(f"Invalid git URL format: {url}")
        
        # Extract node name from URL
        node_name = self._extract_node_name_from_git_url(url)
        
        # Create target directory path
        target_dir = self.custom_nodes_path / node_name
        
        # Check if target directory already exists
        if target_dir.exists():
            logger.warning(f"Target directory already exists, will be replaced: {target_dir}")
        
        # Clone to temporary directory first
        temp_dir = tempfile.mkdtemp()
        temp_clone_dir = Path(temp_dir) / node_name
        
        try:
            # Clone repository
            logger.info(f"Cloning git repository: {url}")
            try:
                run_command(
                    ["git", "clone", url, str(temp_clone_dir)],
                    check=True,
                    timeout=300  # 5 minutes for git clone
                )
            except ComfyUIDetectorError as e:
                raise ValidationError(f"Failed to clone custom node repository: {e}")
            
            # If ref is specified, checkout the specific branch/tag/commit
            if node_spec.ref and node_spec.ref.strip():
                logger.info(f"Checking out ref: {node_spec.ref}")
                try:
                    run_command(
                        ["git", "checkout", node_spec.ref],
                        cwd=temp_clone_dir,
                        check=True,
                        timeout=60
                    )
                except ComfyUIDetectorError as e:
                    raise ValidationError(f"Failed to checkout ref '{node_spec.ref}': {e}")
            
            # Validate that the directory was created successfully
            if not temp_clone_dir.exists():
                raise ValidationError(
                    f"Git clone completed but directory does not exist: {temp_clone_dir}"
                )
            
            # Cache the node if caching is enabled
            if self.enable_cache and self.cache_manager:
                try:
                    self.cache_manager.cache_node(
                        node_spec,
                        temp_clone_dir
                    )
                    logger.info(f"Cached {node_spec.name} for future use")
                except Exception as e:
                    logger.warning(f"Failed to cache {node_spec.name}: {e}")
            
            # Move to target location
            if target_dir.exists():
                shutil.rmtree(target_dir)
            shutil.move(str(temp_clone_dir), str(target_dir))
            
            logger.info(f"Successfully installed custom node via git: {node_name}")
            return True, node_name
            
        except Exception as e:
            raise ValidationError(f"Unexpected error during git installation: {e}")
            
        finally:
            # Clean up temporary directory
            try:
                if Path(temp_dir).exists():
                    shutil.rmtree(temp_dir)
                    logger.debug(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup directory {temp_dir}: {cleanup_error}")
    
    def _extract_node_name_from_git_url(self, url: str) -> str:
        """Extract repository name from git URL to use as node directory name.
        
        Args:
            url: Git URL
            
        Returns:
            Repository name to use as directory name
        """
        # Handle different URL formats
        # https://github.com/user/repo.git -> repo
        # https://github.com/user/repo -> repo  
        # git@github.com:user/repo.git -> repo
        
        # Remove .git suffix if present
        if url.endswith('.git'):
            url = url[:-4]
        
        # Extract last part of path
        if url.startswith('git@'):
            # SSH format: git@github.com:user/repo
            repo_part = url.split(':')[-1]
            # For SSH URLs, need to get just the repo name after the last '/'
            repo_name = repo_part.split('/')[-1]
        else:
            # HTTPS format: https://github.com/user/repo
            repo_name = url.split('/')[-1]
        
        return repo_name
    
    def install_local(self, node_spec: CustomNodeSpec) -> Tuple[bool, str]:
        """Handle local custom nodes.
        
        Args:
            node_spec: CustomNodeSpec with install_method='local'
            
        Returns:
            Tuple of (success: bool, node_name: str)
        
        Note:
            Local custom nodes are assumed to already exist in the target environment
            or be copied from a source location. This is a placeholder for future
            implementation if needed.
        """
        logger.debug(f"Handling local custom node: {node_spec.name}")
        
        # For now, assume local nodes are already present
        # This could be extended in the future to copy from a source location
        target_dir = self.custom_nodes_path / node_spec.name
        
        if target_dir.exists():
            logger.info(f"Local custom node already exists: {node_spec.name}")
            return True, node_spec.name
        else:
            logger.warning(f"Local custom node not found: {node_spec.name}")
            return False, node_spec.name
    
    def _run_post_install_scripts(self, node_name: str) -> None:
        """Run post-installation scripts for a custom node.
        
        Args:
            node_name: Name of the custom node
        
        Note:
            Looks for common post-install script files and executes them.
            This is a basic implementation that can be extended as needed.
        """
        logger.debug(f"Running post-install scripts for: {node_name}")
        
        node_dir = self.custom_nodes_path / node_name
        if not node_dir.exists():
            logger.warning(f"Custom node directory not found: {node_dir}")
            return
        
        # Common post-install script names
        script_names = ['install.py', 'setup.py', 'post_install.py']
        
        for script_name in script_names:
            script_path = node_dir / script_name
            if script_path.exists():
                logger.info(f"Running post-install script: {script_path}")
                try:
                    # Use the virtual environment python to run the script
                    python_exe = self.venv_path / "bin" / "python"
                    if not python_exe.exists():
                        # Windows path
                        python_exe = self.venv_path / "Scripts" / "python.exe"
                    
                    run_command(
                        [str(python_exe), str(script_path)],
                        cwd=node_dir,
                        check=True,
                        timeout=300  # 5 minutes for post-install script
                    )
                    logger.info(f"Post-install script completed successfully: {script_name}")
                except Exception as e:
                    logger.warning(f"Post-install script failed for {node_name}/{script_name}: {e}")
                    # Don't fail the entire installation for post-install script failures
                break  # Only run the first script found
    
    def _install_node_requirements(self, node_name: str) -> None:
        """Install requirements.txt for a custom node.
        
        Args:
            node_name: Name of the custom node
        """
        logger.debug(f"Installing requirements for custom node: {node_name}")
        
        node_dir = self.custom_nodes_path / node_name
        if not node_dir.exists():
            logger.warning(f"Custom node directory not found: {node_dir}")
            return
        
        requirements_path = node_dir / "requirements.txt"
        if requirements_path.exists():
            logger.info(f"Installing requirements from: {requirements_path}")
            try:
                # Use UV to install requirements
                result = self.uv_interface.install_requirements(
                    venv_path=self.venv_path,
                    requirements_file=requirements_path
                )
                
                if not result.success:
                    logger.warning(f"Failed to install requirements for {node_name}: {result.error}")
                else:
                    logger.info(f"Successfully installed requirements for {node_name}")
                    
            except Exception as e:
                logger.warning(f"Error installing requirements for {node_name}: {e}")
        else:
            logger.debug(f"No requirements.txt found for {node_name}")
    
    def get_cache_stats(self) -> Optional[dict]:
        """Get cache statistics if caching is enabled."""
        if self.enable_cache and self.cache_manager:
            return self.cache_manager.get_cache_stats()
        return None

    def clear_cache(self, node_name: Optional[str] = None) -> int:
        """Clear cache for a specific node or all nodes.
        
        Args:
            node_name: Specific node name to clear, or None to clear all
            
        Returns:
            Number of cache entries cleared
        """
        if self.enable_cache and self.cache_manager:
            return self.cache_manager.clear_cache(node_name)
        return 0