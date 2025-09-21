
from ..logging.logging_config import get_logger
from .git_manager import GitManager

logger = get_logger(__name__)

class EnvironmentVersionManager:
    """Specialized version management for ComfyDock environments.

    This provides a higher-level interface specifically for environment
    version management, with concepts like "rollback" and "checkpoint".
    """

    def __init__(self, git_manager: GitManager):
        """Initialize with a GitManager instance.

        Args:
            git_manager: GitManager for the environment repository
        """
        self.git = git_manager

    def create_checkpoint(self, description: str | None = None) -> str:
        """Create a version checkpoint of the current state.

        Args:
            description: Optional description for the checkpoint

        Returns:
            Version identifier (e.g., "v3")
        """
        # Generate automatic message if not provided
        if not description:
            from datetime import datetime

            description = f"Checkpoint created at {datetime.now().isoformat()}"

        # Commit current state
        self.git.commit_with_identity(description)

        # Get the new version number
        versions = self.git.get_version_history(limit=1)
        if versions:
            return versions[-1]["version"]
        return "v1"

    def rollback_to(self, version: str, safe: bool = True) -> None:
        """Rollback environment to a previous version.

        Args:
            version: Version to rollback to
            safe: If True, leaves changes unstaged for review

        Raises:
            ValueError: If version doesn't exist
        """
        if safe:
            # Check for uncommitted changes first
            if self.git.has_uncommitted_changes():
                logger.warning("Uncommitted changes will be lost during rollback")

        # Discard any uncommitted changes
        self.git.discard_uncommitted()

        # Apply the target version
        self.git.apply_version(version, leave_unstaged=safe)

        if safe:
            logger.info(f"Rolled back to {version} (changes are unstaged for review)")
        else:
            logger.info(f"Rolled back to {version}")

    def get_version_summary(self) -> dict:
        """Get a summary of the version state.

        Returns:
            Dict with current version, has_changes, total_versions
        """
        versions = self.git.get_version_history(limit=100)
        has_changes = self.git.has_uncommitted_changes()

        current_version = versions[-1]["version"] if versions else None

        return {
            "current_version": current_version,
            "has_uncommitted_changes": has_changes,
            "total_versions": len(versions),
            "latest_message": versions[-1]["message"] if versions else None,
        }
