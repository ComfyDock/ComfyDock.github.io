"""Git-related utilities for ComfyUI detection."""

import os
import re
import socket
import subprocess
from pathlib import Path

from comfydock_core.models.exceptions import CDProcessError

from ..logging.logging_config import get_logger
from .common import run_command

logger = get_logger(__name__)


# =============================================================================
# Error Handling Utilities
# =============================================================================

def _is_not_found_error(error: CDProcessError) -> bool:
    """Check if a git error indicates something doesn't exist.
    
    Args:
        error: The CDProcessError from a git command
        
    Returns:
        True if this is a "not found" type error
    """
    not_found_messages = [
        "does not exist",
        "invalid object",
        "bad revision",
        "path not in",
        "unknown revision",
        "not a valid object",
        "pathspec"
    ]
    error_text = ((error.stderr or "") + str(error)).lower()
    return any(msg in error_text for msg in not_found_messages)


def _git(cmd: list[str], repo_path: Path,
         check: bool = True,
         not_found_msg: str | None = None,
         capture_output: bool = True,
         text: bool = True) -> subprocess.CompletedProcess:
    """Run git command with consistent error handling.
    
    Args:
        cmd: Git command arguments (without 'git' prefix)
        repo_path: Path to git repository
        check: Whether to raise exception on non-zero exit
        not_found_msg: Custom message for "not found" errors
        capture_output: Whether to capture stdout/stderr
        text: Whether to return text output
        
    Returns:
        CompletedProcess result
        
    Raises:
        ValueError: For "not found" type errors
        OSError: For other git command failures
    """
    try:
        return run_command(
            ["git"] + cmd,
            cwd=repo_path,
            check=check,
            capture_output=capture_output,
            text=text
        )
    except CDProcessError as e:
        if _is_not_found_error(e):
            raise ValueError(not_found_msg or "Git object not found") from e
        raise OSError(f"Git command failed: {e}") from e

# =============================================================================
# Configuration & Setup
# =============================================================================

def ensure_git_identity(repo_path: Path) -> None:
    """Ensure git has a user identity configured for commits.

    Sets up local git config (not global) with sensible defaults.

    Args:
        repo_path: Path to the git repository
    """
    # Check if identity is already configured
    check_name = run_command(
        ["git", "config", "user.name"], cwd=repo_path, capture_output=True, text=True
    )

    check_email = run_command(
        ["git", "config", "user.email"], cwd=repo_path, capture_output=True, text=True
    )

    # If both are set, we're good
    if check_name.stdout.strip() and check_email.stdout.strip():
        return

    # Determine git identity using fallback chain
    git_name = get_git_identity()
    git_email = get_git_email()

    # Set identity locally for this repository only
    run_command(["git", "config", "user.name", git_name], cwd=repo_path, check=True)

    run_command(["git", "config", "user.email", git_email], cwd=repo_path, check=True)

    logger.info(f"Set local git identity: {git_name} <{git_email}>")


def get_git_identity() -> str:
    """Get a suitable git user name with smart fallbacks.

    Returns:
        Git user name
    """
    # Try environment variables first
    git_name = os.environ.get("GIT_AUTHOR_NAME")
    if git_name:
        return git_name

    # Try to get system username as fallback for name
    try:
        import pwd

        git_name = (
            pwd.getpwuid(os.getuid()).pw_gecos or pwd.getpwuid(os.getuid()).pw_name
        )
        if git_name:
            return git_name
    except:
        pass

    try:
        git_name = os.getlogin()
        if git_name:
            return git_name
    except:
        pass

    return "ComfyDock User"


def get_git_email() -> str:
    """Get a suitable git email with smart fallbacks.

    Returns:
        Git email address
    """
    # Try environment variables first
    git_email = os.environ.get("GIT_AUTHOR_EMAIL")
    if git_email:
        return git_email

    # Try to construct from username and hostname
    try:
        hostname = socket.gethostname()
        username = os.getlogin()
        return f"{username}@{hostname}"
    except:
        pass

    return "user@comfydock.local"


def create_environment_gitignore(repo_path: Path) -> None:
    """Create a standard .gitignore for environment tracking.

    Args:
        repo_path: Path to the git repository
    """
    gitignore_content = """# Staging area
staging/

# Staging metadata
metadata/

# logs
logs/

# Python cache
__pycache__/
*.pyc

# Temporary files
*.tmp
*.bak
"""
    (repo_path / ".gitignore").write_text(gitignore_content)

# =============================================================================
# Repository Information
# =============================================================================

def parse_github_url(url: str) -> tuple[str, str, str | None] | None:
    """Parse GitHub URL to extract owner, repo name, and optional commit/ref.
    
    Args:
        url: GitHub repository URL
        
    Returns:
        Tuple of (owner, repo, commit) or None if invalid.
        commit will be None if no specific commit is specified.
    """
    # Handle URLs with commit/tree/blob paths like:
    # https://github.com/owner/repo/tree/commit-hash
    # https://github.com/owner/repo/commit/commit-hash
    github_match = re.match(
        r"(?:https?://github\.com/|git@github\.com:)([^/]+)/([^/\.]+)(?:\.git)?(?:/(?:tree|commit|blob)/([^/]+))?",
        url,
    )
    if github_match:
        owner = github_match.group(1)
        repo = github_match.group(2)
        commit = github_match.group(3)  # Will be None if not present
        return (owner, repo, commit)
    return None

def get_git_info(node_path: Path) -> dict | None:
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
            git_info["commit"] = result.stdout.strip()

        # Get current branch
        result = run_command(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=node_path
        )
        if result.returncode == 0:
            branch = result.stdout.strip()
            # Don't set branch if we're in detached HEAD state
            if branch != "HEAD":
                git_info["branch"] = branch

        # Try to get current tag/version
        result = run_command(
            ["git", "describe", "--tags", "--exact-match"], cwd=node_path
        )
        if result.returncode == 0:
            git_info["tag"] = result.stdout.strip()
        else:
            # Try to get the most recent tag
            result = run_command(
                ["git", "describe", "--tags", "--abbrev=0"], cwd=node_path
            )
            if result.returncode == 0:
                # Store as 'tag' since GitInfo model expects 'tag', not 'latest_tag'
                git_info["tag"] = result.stdout.strip()

        # Get remote URL
        result = run_command(["git", "remote", "get-url", "origin"], cwd=node_path)
        if result.returncode == 0:
            remote_url = result.stdout.strip()
            git_info["remote_url"] = remote_url

            # Extract GitHub info if it's a GitHub URL
            github_match = re.match(
                r"(?:https?://github\.com/|git@github\.com:)([^/]+)/([^/\.]+)",
                remote_url,
            )
            if github_match:
                git_info["github_owner"] = github_match.group(1)
                git_info["github_repo"] = github_match.group(2).replace(".git", "")
                # Don't add github_url as it's not in GitInfo model

        # Check if there are uncommitted changes
        result = run_command(["git", "status", "--porcelain"], cwd=node_path)
        if result.returncode == 0:
            # Use 'is_dirty' to match GitInfo model field name
            git_info["is_dirty"] = bool(result.stdout.strip())

        return git_info if git_info else None

    except Exception as e:
        logger.warning(f"Error getting git info for {node_path}: {e}")
        return None


# =============================================================================
# Basic Git Operations
# =============================================================================

def git_init(repo_path: Path) -> None:
    """Initialize a git repository.
    
    Args:
        repo_path: Path to initialize as git repository
        
    Raises:
        OSError: If git initialization fails
    """
    _git(["init"], repo_path)

def git_diff(repo_path: Path, file_path: Path) -> str:
    """Get git diff for a specific file.
    
    Args:
        repo_path: Path to git repository
        file_path: Path to file to diff
        
    Returns:
        Git diff output as string
        
    Raises:
        OSError: If git diff command fails
    """
    result = _git(["diff", str(file_path)], repo_path)
    return result.stdout

def git_commit(repo_path: Path, message: str, add_all: bool = True) -> None:
    """Commit changes with optional staging.
    
    Args:
        repo_path: Path to git repository
        message: Commit message
        add_all: Whether to stage all changes first
        
    Raises:
        OSError: If git commands fail
    """
    if add_all:
        _git(["add", "."], repo_path)
    _git(["commit", "-m", message], repo_path)

# =============================================================================
# Advanced Git Operations
# =============================================================================

def git_show(repo_path: Path, ref: str, file_path: Path, is_text: bool = True) -> str:
    """Show file content from a specific git ref.
    
    Args:
        repo_path: Path to git repository
        ref: Git reference (commit, branch, tag)
        file_path: Path to file to show
        is_text: Whether to treat file as text
        
    Returns:
        File content as string
        
    Raises:
        OSError: If git show command fails
        ValueError: If ref or file doesn't exist
    """
    cmd = ["show", f"{ref}:{file_path}"]
    if is_text:
        cmd.append("--text")
    result = _git(cmd, repo_path, not_found_msg=f"Git ref '{ref}' or file '{file_path}' does not exist")
    return result.stdout


def git_history(
    repo_path: Path,
    file_path: Path | None = None,
    pretty: str | None = None,
    max_count: int | None = None,
    follow: bool = False,
    oneline: bool = False,
) -> str:
    """Get git history for a specific file.

    Args:
        repo_path: Path to git repository
        file_path: Path to file to get history for
        oneline: Whether to show one-line format
        follow: Whether to follow renames
        max_count: Maximum number of commits to return
        pretty: Git pretty format

    Returns:
        Git log output as string

    Raises:
        OSError: If git log command fails
    """
    cmd = ["log"]
    if follow:
        cmd.append("--follow")
    if oneline:
        cmd.append("--oneline")
    if max_count:
        cmd.append(f"--max-count={max_count}")
    if pretty:
        cmd.append(f"--pretty={pretty}")
    if file_path:
        cmd.append("--")
        cmd.append(str(file_path))
    result = _git(cmd, repo_path)
    return result.stdout


def git_clone(
    url: str,
    target_path: Path,
    depth: int = 1,
    ref: str | None = None,
    timeout: int = 30,
) -> None:
    """Clone a git repository to a target path.

    Args:
        url: Git repository URL
        target_path: Directory to clone to
        depth: Clone depth (1 for shallow clone)
        ref: Optional specific ref (branch/tag/commit) to checkout
        timeout: Command timeout in seconds
        
    Raises:
        OSError: If git clone or checkout fails
        ValueError: If URL is invalid or ref doesn't exist
    """
    # Build clone command
    cmd = ["clone"]

    # For commit hashes, we need to clone without --depth and then checkout
    # For branches/tags, we can use --branch with depth
    is_commit_hash = ref and len(ref) == 40 and all(c in '0123456789abcdef' for c in ref.lower())

    if depth > 0 and not is_commit_hash:
        cmd.extend(["--depth", str(depth)])

    if ref and not is_commit_hash and not ref.startswith("refs/"):
        # If a specific branch/tag is requested, clone it directly
        cmd.extend(["--branch", ref])

    cmd.extend([url, str(target_path)])

    # Execute clone
    _git(cmd, Path.cwd(), not_found_msg=f"Git repository URL '{url}' does not exist")

    # If a specific commit hash was requested, checkout to it
    if is_commit_hash and ref:
        _git(["checkout", ref], target_path, not_found_msg=f"Commit '{ref}' does not exist")
    elif ref and ref.startswith("refs/"):
        # Handle refs/ style references
        _git(["checkout", ref], target_path, not_found_msg=f"Reference '{ref}' does not exist")

    logger.info(f"Successfully cloned {url} to {target_path}")

def git_checkout(repo_path: Path,
                target: str = "HEAD",
                files: list[str] | None = None,
                unstage: bool = False) -> None:
    """Universal checkout function for commits, branches, or specific files.
    
    Args:
        repo_path: Path to git repository
        target: What to checkout (commit, branch, tag)
        files: Specific files to checkout (None for all)
        unstage: Whether to unstage files after checkout
        
    Raises:
        OSError: If git command fails
        ValueError: If target doesn't exist
    """
    cmd = ["checkout", target]
    if files:
        cmd.extend(["--"] + files)

    _git(cmd, repo_path, not_found_msg=f"Git target '{target}' does not exist")

    # Optionally unstage files to leave them as uncommitted changes
    if unstage and files:
        _git(["reset", "HEAD"] + files, repo_path)
    elif unstage and not files:
        _git(["reset", "HEAD", "."], repo_path)

# =============================================================================
# Status & Change Tracking
# =============================================================================

def get_staged_changes(repo_path: Path) -> list[str]:
    """Get list of files that are staged (git added) but not committed.
    
    Args:
        repo_path: Path to the git repository
        
    Returns:
        List of file paths that are staged
        
    Raises:
        OSError: If git command fails
    """
    result = _git(["diff", "--cached", "--name-only"], repo_path)

    if result.stdout:
        return result.stdout.strip().split('\n')

    return []

def get_workflow_git_changes(repo_path: Path) -> dict[str, str]:
    """Get git status for workflow files specifically.
    
    Args:
        repo_path: Path to the git repository
        
    Returns:
        Dict mapping workflow names to their git status:
        - 'modified' for modified files  
        - 'added' for new/untracked files
        - 'deleted' for deleted files
    """
    result = _git(["status", "--porcelain"], repo_path)
    workflow_changes = {}

    if result.stdout:
        for line in result.stdout.strip().split('\n'):
            if line and len(line) >= 3:
                # Git status --porcelain format: "XY filename"
                index_status = line[0]  # Staged status
                working_status = line[1]  # Working tree status
                filename = line[2:].lstrip()

                # Handle quoted filenames (git quotes filenames with spaces/special chars)
                if filename.startswith('"') and filename.endswith('"'):
                    # Remove quotes and unescape
                    filename = filename[1:-1].encode().decode('unicode_escape')

                logger.debug(f"index status: {index_status}, working status: {working_status}, filename: {filename}")

                # Only process workflow files
                if filename.startswith('workflows/') and filename.endswith('.json'):
                    # Extract workflow name from path (keep spaces as-is)
                    workflow_name = Path(filename).stem
                    logger.debug(f"Workflow name: {workflow_name}")

                    # Determine status (prioritize working tree status)
                    if working_status == 'M' or index_status == 'M':
                        workflow_changes[workflow_name] = 'modified'
                    elif working_status == 'D' or index_status == 'D':
                        workflow_changes[workflow_name] = 'deleted'
                    elif working_status == '?' or index_status == 'A':
                        workflow_changes[workflow_name] = 'added'

    logger.debug(f"Workflow changes: {str(workflow_changes)}")
    return workflow_changes

def get_uncommitted_changes(repo_path: Path) -> list[str]:
    """Get list of files that have uncommitted changes (staged or unstaged).
    
    Args:
        repo_path: Path to the git repository
        
    Returns:
        List of file paths with uncommitted changes
        
    Raises:
        OSError: If git command fails
    """
    result = _git(["status", "--porcelain"], repo_path)

    if result.stdout:
        changes = []
        for line in result.stdout.strip().split('\n'):
            if line and len(line) >= 3:
                # Git status --porcelain format: "XY filename"
                # X = index status, Y = working tree status
                # But the spacing varies based on content:
                # "M  filename" = staged (M + space + space + filename)
                # " M filename" = unstaged (space + M + space + filename)
                # "MM filename" = both staged and unstaged

                # The first 2 characters are always status flags
                # Everything after position 2 contains spaces + filename
                remaining = line[2:]    # Everything after status characters

                # Skip any leading whitespace to get to filename
                filename = remaining.lstrip()
                if filename:  # Make sure filename is not empty
                    changes.append(filename)
        return changes

    return []
