"""Common utilities for ComfyUI Environment Capture."""

import json
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .exceptions import ComfyUIDetectorError
from .logging_config import get_logger

logger = get_logger(__name__)


def run_command(
    cmd: List[str],
    cwd: Optional[Path] = None,
    timeout: int = 30,
    capture_output: bool = True,
    text: bool = True,
    check: bool = False,
    env: Optional[dict] = None
) -> subprocess.CompletedProcess:
    """Run a subprocess command with proper error handling.
    
    Args:
        cmd: Command and arguments as a list
        cwd: Working directory for the command
        timeout: Command timeout in seconds
        capture_output: Whether to capture stdout/stderr
        text: Whether to decode output as text
        check: Whether to raise exception on non-zero exit code
        env: Environment variables to pass to subprocess
        
    Returns:
        CompletedProcess instance
        
    Raises:
        ComfyUIDetectorError: If command fails and check=True
    """
    try:
        logger.debug(f"Running command: {' '.join(cmd)}")
        if cwd:
            logger.debug(f"Working directory: {cwd}")
            
        result = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            timeout=timeout,
            capture_output=capture_output,
            text=text,
            env=env
        )
        
        if check and result.returncode != 0:
            error_msg = f"Command failed with exit code {result.returncode}: {' '.join(cmd)}"
            if result.stderr:
                error_msg += f"\nStderr: {result.stderr}"
            raise ComfyUIDetectorError(error_msg)
            
        return result
        
    except subprocess.TimeoutExpired as e:
        error_msg = f"Command timed out after {timeout}s: {' '.join(cmd)}"
        logger.error(error_msg)
        raise ComfyUIDetectorError(error_msg) from e
    except Exception as e:
        error_msg = f"Error running command {' '.join(cmd)}: {e}"
        logger.error(error_msg)
        raise ComfyUIDetectorError(error_msg) from e


def safe_json_load(file_path: Path) -> Optional[Dict[str, Any]]:
    """Safely load JSON from a file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Parsed JSON data or None if file doesn't exist or is invalid
    """
    if not file_path.exists():
        logger.debug(f"JSON file does not exist: {file_path}")
        return None
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.debug(f"Successfully loaded JSON from {file_path}")
        return data
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON in {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return None


def safe_json_dump(
    data: Any,
    file_path: Path,
    indent: int = 2,
    ensure_ascii: bool = False
) -> bool:
    """Safely write JSON to a file.
    
    Args:
        data: Data to serialize as JSON
        file_path: Output file path
        indent: JSON indentation
        ensure_ascii: Whether to escape non-ASCII characters
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
        
        logger.debug(f"Successfully wrote JSON to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error writing JSON to {file_path}: {e}")
        return False


def normalize_package_name(name: str) -> str:
    """Normalize package name according to PEP 503.
    
    Args:
        name: Package name to normalize
        
    Returns:
        Normalized package name (lowercase, with underscores/hyphens as hyphens)
    """
    # Convert to lowercase and replace underscores/dots with hyphens
    normalized = re.sub(r"[-_.]+", "-", name).lower()
    return normalized


def is_valid_version(version_str: str) -> bool:
    """Check if a version string is valid.
    
    Args:
        version_str: Version string to validate
        
    Returns:
        True if version is valid, False otherwise
    """
    if not version_str:
        return False
        
    # Basic version pattern: major.minor.patch with optional suffixes
    pattern = r'^\d+(?:\.\d+)*(?:[a-zA-Z]\d*)?(?:\+[a-zA-Z0-9.-]+)?$'
    return bool(re.match(pattern, version_str))


def format_size(size_bytes: int) -> str:
    """Format a size in bytes as human-readable string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Human-readable size string (e.g., "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"
        
    size_names = ["B", "KB", "MB", "GB", "TB"]
    size_index = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and size_index < len(size_names) - 1:
        size /= 1024.0
        size_index += 1
    
    if size_index == 0:
        return f"{int(size)} {size_names[size_index]}"
    else:
        return f"{size:.1f} {size_names[size_index]}"


def parse_git_url(url: str) -> Optional[Dict[str, str]]:
    """Parse a Git URL and extract owner/repo information.
    
    Args:
        url: Git URL (HTTPS or SSH format)
        
    Returns:
        Dict with 'owner', 'repo', and 'url' keys, or None if not parseable
    """
    # Handle GitHub URLs
    github_patterns = [
        r'https?://github\.com/([^/]+)/([^/\.]+?)(?:\.git)?/?$',
        r'git@github\.com:([^/]+)/([^/\.]+?)(?:\.git)?$'
    ]
    
    for pattern in github_patterns:
        match = re.match(pattern, url)
        if match:
            owner, repo = match.groups()
            return {
                'owner': owner,
                'repo': repo,
                'url': f"https://github.com/{owner}/{repo}"
            }
    
    # Could add support for other Git hosting services here
    return None


def extract_archive_name(url: str) -> str:
    """Extract a reasonable archive name from a URL.
    
    Args:
        url: Archive URL
        
    Returns:
        Suggested archive filename
    """
    # Try to get filename from URL
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        path = Path(parsed.path)
        
        if path.suffix in ['.zip', '.tar.gz', '.tgz', '.tar']:
            return path.name
        elif path.name:
            return f"{path.name}.tar.gz"
    except Exception:
        pass
    
    # Fallback: use last part of path or generate generic name
    try:
        parts = url.rstrip('/').split('/')
        if parts:
            return f"{parts[-1]}.tar.gz"
    except Exception:
        pass
    
    return "archive.tar.gz"


def validate_path(path: Union[str, Path], must_exist: bool = True) -> Path:
    """Validate and convert a path to Path object.
    
    Args:
        path: Path string or Path object
        must_exist: Whether the path must exist
        
    Returns:
        Validated Path object
        
    Raises:
        ComfyUIDetectorError: If path is invalid or doesn't exist when required
    """
    try:
        path_obj = Path(path).resolve()
    except Exception as e:
        raise ComfyUIDetectorError(f"Invalid path: {path}") from e
    
    if must_exist and not path_obj.exists():
        raise ComfyUIDetectorError(f"Path does not exist: {path_obj}")
    
    return path_obj