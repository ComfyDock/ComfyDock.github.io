"""Git-related utilities for ComfyUI detection."""

import re
from pathlib import Path
from typing import Dict, Optional

from ..common import run_command
from ..logging_config import get_logger

logger = get_logger(__name__)


def get_git_info(node_path: Path) -> Optional[Dict]:
    """Get git repository information for a custom node."""
    git_info = {}
    
    try:
        # Check if it's a git repository
        git_dir = node_path / ".git"
        if not git_dir.exists():
            return None
            
        # Get current commit hash
        result = run_command(["git", "rev-parse", "HEAD"], cwd=node_path)
        if result.returncode == 0:
            git_info['commit'] = result.stdout.strip()
        
        # Try to get current tag/version
        result = run_command(["git", "describe", "--tags", "--exact-match"], cwd=node_path)
        if result.returncode == 0:
            git_info['tag'] = result.stdout.strip()
        else:
            # Try to get the most recent tag
            result = run_command(["git", "describe", "--tags", "--abbrev=0"], cwd=node_path)
            if result.returncode == 0:
                git_info['latest_tag'] = result.stdout.strip()
                
        # Get remote URL
        result = run_command(["git", "remote", "get-url", "origin"], cwd=node_path)
        if result.returncode == 0:
            remote_url = result.stdout.strip()
            git_info['remote_url'] = remote_url
            
            # Extract GitHub info if it's a GitHub URL
            github_match = re.match(r'(?:https?://github\.com/|git@github\.com:)([^/]+)/([^/\.]+)', remote_url)
            if github_match:
                git_info['github_owner'] = github_match.group(1)
                git_info['github_repo'] = github_match.group(2).replace('.git', '')
                git_info['github_url'] = f"https://github.com/{git_info['github_owner']}/{git_info['github_repo']}"
                
        # Check if there are uncommitted changes
        result = run_command(["git", "status", "--porcelain"], cwd=node_path)
        if result.returncode == 0:
            git_info['has_uncommitted_changes'] = bool(result.stdout.strip())
            
        return git_info if git_info else None
        
    except Exception as e:
        logger.warning(f"Error getting git info for {node_path}: {e}")
        return None


def get_comfyui_version(comfyui_path: Path) -> str:
    """Detect ComfyUI version from git tags."""
    comfyui_version = "unknown"
    try:
        git_dir = comfyui_path / ".git"
        if git_dir.exists():
            result = run_command(["git", "describe", "--tags", "--always"], cwd=comfyui_path)
            if result.returncode == 0:
                comfyui_version = result.stdout.strip()
    except Exception as e:
        logger.debug(f"Could not detect ComfyUI version from {comfyui_path}: {e}")
    
    return comfyui_version