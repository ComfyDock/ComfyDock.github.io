"""High-level Git workflow manager for ComfyDock environments.

This module provides higher-level git workflows that combine multiple git operations
with business logic. It builds on top of the low-level git utilities in git.py.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ..logging.logging_config import get_logger
from ..models.environment import GitStatus

if TYPE_CHECKING:
    from .pyproject_manager import PyprojectManager

from ..utils.git import (
    ensure_git_identity,
    get_workflow_git_changes,
    git_checkout,
    git_commit,
    git_diff,
    git_history,
    git_init,
    git_show,
)

logger = get_logger(__name__)


class GitManager:
    """Manages high-level git workflows for environment tracking."""

    def __init__(self, repo_path: Path):
        """Initialize GitManager for a specific repository.

        Args:
            repo_path: Path to the git repository (usually .cec directory)
        """
        self.repo_path = repo_path
        self.gitignore_content = """# Staging area
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

    def initialize_environment_repo(
        self, initial_message: str = "Initial environment setup"
    ) -> None:
        """Initialize a new environment repository with proper setup.

        This combines:
        - Git init
        - Identity setup
        - Gitignore creation
        - Initial commit

        Args:
            initial_message: Message for the initial commit
        """
        # Initialize git repository
        git_init(self.repo_path)

        # Ensure git identity is configured
        ensure_git_identity(self.repo_path)

        # Create standard .gitignore
        self._create_gitignore()

        # Initial commit (if there are files to commit)
        if any(self.repo_path.iterdir()):
            git_commit(self.repo_path, initial_message)
            logger.info(f"Created initial commit: {initial_message}")

    def commit_with_identity(self, message: str, add_all: bool = True) -> None:
        """Commit changes ensuring identity is set up.

        Args:
            message: Commit message
            add_all: Whether to stage all changes first
        """
        # Ensure identity before committing
        ensure_git_identity(self.repo_path)

        # Perform the commit
        git_commit(self.repo_path, message, add_all)

    def apply_version(self, version: str, leave_unstaged: bool = True) -> None:
        """Apply files from a specific version to working directory.

        This is a high-level rollback operation that:
        - Resolves version identifiers (v1, v2, etc.) to commits
        - Applies files from that commit
        - Optionally leaves them unstaged for review

        Args:
            version: Version identifier (e.g., "v1", "v2") or commit hash
            leave_unstaged: If True, files are left as uncommitted changes

        Raises:
            ValueError: If version doesn't exist
        """
        # Resolve version to commit hash
        commit_hash = self.resolve_version(version)

        logger.info(f"Applying files from version {version} (commit {commit_hash[:8]})")

        # Apply all files from that commit
        git_checkout(self.repo_path, commit_hash, files=["."], unstage=leave_unstaged)

    def discard_uncommitted(self) -> None:
        """Discard all uncommitted changes in the repository."""
        logger.info("Discarding uncommitted changes")
        git_checkout(self.repo_path, "HEAD", files=["."])

    def get_version_history(self, limit: int = 10) -> list[dict]:
        """Get simplified version history with v1, v2 labels.

        Args:
            limit: Maximum number of versions to return

        Returns:
            List of version info dicts
        """
        return self._get_commit_versions(limit)

    def resolve_version(self, version: str) -> str:
        """Resolve a version identifier to a commit hash.

        Args:
            version: Version identifier (e.g., "v1", "v2") or commit hash

        Returns:
            Full commit hash

        Raises:
            ValueError: If version doesn't exist
        """
        return self._resolve_version_to_commit(version)

    def get_pyproject_diff(self) -> str:
        """Get the git diff specifically for pyproject.toml.

        Returns:
            Diff output or empty string
        """
        pyproject_path = Path("pyproject.toml")
        return git_diff(self.repo_path, pyproject_path) or ""

    def get_pyproject_from_version(self, version: str) -> str:
        """Get pyproject.toml content from a specific version.

        Args:
            version: Version identifier or commit hash

        Returns:
            File content as string

        Raises:
            ValueError: If version or file doesn't exist
        """
        commit_hash = self.resolve_version(version)
        return git_show(self.repo_path, commit_hash, Path("pyproject.toml"))

    def get_workflow_changes(self) -> dict[str, str]:
        """Get git status for workflow files.

        Returns:
            Dict mapping workflow names to their git status
        """
        return get_workflow_git_changes(self.repo_path)

    def has_uncommitted_changes(self) -> bool:
        """Check if there are any uncommitted changes.

        Returns:
            True if there are uncommitted changes
        """
        from ..utils.git import get_uncommitted_changes

        return bool(get_uncommitted_changes(self.repo_path))

    def _create_gitignore(self) -> None:
        """Create standard .gitignore for environment tracking."""
        gitignore_path = self.repo_path / ".gitignore"
        gitignore_path.write_text(self.gitignore_content)

    def _get_commit_versions(self, limit: int = 10) -> list[dict]:
        """Get simplified version list from git history.
        
        Returns commits with simple identifiers instead of full hashes.
        
        Args:
            limit: Maximum number of commits to return
            
        Returns:
            List of commit info dicts with keys: version, hash, message, date
            
        Raises:
            OSError: If git command fails
        """
        # result = _git(["log", f"--max-count={limit}", "--pretty=format:%H|%s|%ai"], self.repo_path)
        result = git_history(self.repo_path, max_count=limit, pretty="format:%H|%s|%ai")

        commits = []
        for line in result.strip().split('\n'):
            if line:
                hash_val, message, date = line.split('|', 2)
                commits.append({
                    'hash': hash_val,
                    'message': message,
                    'date': date
                })

        # Reverse so oldest commit is first (chronological order)
        commits.reverse()

        # Now assign version numbers: oldest = v1, newest = v<highest>
        for i, commit in enumerate(commits):
            commit['version'] = f"v{i + 1}"

        return commits

    def _resolve_version_to_commit(self, version: str) -> str:
        """Resolve a simple version identifier to a git commit hash.
        
        Args:
            repo_path: Path to git repository
            version: Version identifier (e.g., "v1", "v2")
            
        Returns:
            Full commit hash
            
        Raises:
            ValueError: If version doesn't exist
            OSError: If git command fails
        """
        # If it's already a commit hash, return as-is
        if len(version) >= 7 and all(c in '0123456789abcdef' for c in version.lower()):
            return version

        commits = self._get_commit_versions(limit=100)

        for commit in commits:
            if commit['version'] == version:
                return commit['hash']

        raise ValueError(f"Version '{version}' not found")

    def get_status(self, pyproject_manager: PyprojectManager | None = None) -> GitStatus:
        """Get complete git status with optional change parsing.
        
        Args:
            pyproject_manager: Optional PyprojectManager for parsing changes
            
        Returns:
            GitStatus with all git information encapsulated
        """
        # Get basic git information
        diff = self.get_pyproject_diff()
        workflow_changes = self.get_workflow_changes()
        has_changes = bool(diff.strip()) or bool(workflow_changes)

        # Create status object
        status = GitStatus(
            has_changes=has_changes,
            diff=diff,
            workflow_changes=workflow_changes
        )

        # Parse changes if we have them and a pyproject manager
        if has_changes and pyproject_manager:
            from ..utils.git_change_parser import GitChangeParser
            parser = GitChangeParser(self.repo_path)
            current_config = pyproject_manager.load()

            # The parser updates the status object directly
            parser.update_git_status(status, current_config)

        return status

