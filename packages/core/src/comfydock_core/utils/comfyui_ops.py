from pathlib import Path

from ..logging.logging_config import get_logger
from .common import run_command
from .git import git_clone

logger = get_logger(__name__)


def validate_comfyui_installation(comfyui_path: Path) -> bool:
    """Check if a directory contains a valid ComfyUI installation.

    Args:
        comfyui_path: Path to check

    Returns:
        True if valid ComfyUI installation, False otherwise
    """
    # Check for essential ComfyUI files
    required_files = ["main.py", "nodes.py", "folder_paths.py"]

    for file in required_files:
        if not (comfyui_path / file).exists():
            return False

    # Check for essential directories
    required_dirs = ["comfy", "models"]

    for dir_name in required_dirs:
        if not (comfyui_path / dir_name).is_dir():
            return False

    return True


def get_comfyui_version(comfyui_path: Path) -> str:
    """Detect ComfyUI version from git tags."""
    comfyui_version = "unknown"
    try:
        git_dir = comfyui_path / ".git"
        if git_dir.exists():
            result = run_command(
                ["git", "describe", "--tags", "--always"], cwd=comfyui_path
            )
            if result.returncode == 0:
                comfyui_version = result.stdout.strip()
    except Exception as e:
        logger.debug(f"Could not detect ComfyUI version from {comfyui_path}: {e}")

    return comfyui_version


def clone_comfyui(target_path: Path, version: str | None = None) -> str | None:
    """Clone ComfyUI repository to a target path.

    Args:
        target_path: Where to clone ComfyUI
        version: Optional specific version/tag/commit to checkout

    Returns:
        ComfyUI version string (commit hash or tag)

    Raises:
        RuntimeError: If cloning fails
    """
    # Clone the repository with shallow clone for speed
    git_clone(
        "https://github.com/comfyanonymous/ComfyUI.git",
        target_path,
        depth=1,
        ref=version,
        timeout=60,
    )
    return get_comfyui_version(target_path)
