"""models/environment.py - Environment models for ComfyDock."""

from dataclasses import dataclass, field


@dataclass
class PackageSyncStatus:
    """Status of package synchronization."""
    in_sync: bool
    message: str
    details: str | None = None

@dataclass
class GitStatus:
    """Encapsulated git status information."""
    has_changes: bool
    diff: str
    workflow_changes: dict[str, str] = field(default_factory=dict)

    # Git change details (populated by parser if needed)
    nodes_added: list[str] = field(default_factory=list)
    nodes_removed: list[str] = field(default_factory=list)
    dependencies_added: list[dict] = field(default_factory=list)
    dependencies_removed: list[dict] = field(default_factory=list)
    dependencies_updated: list[dict] = field(default_factory=list)
    constraints_added: list[str] = field(default_factory=list)
    constraints_removed: list[str] = field(default_factory=list)
    workflows_tracked: list[str] = field(default_factory=list)
    workflows_untracked: list[str] = field(default_factory=list)


@dataclass
class WorkflowStatus:
    """Encapsulated workflow status information."""
    in_sync: bool
    sync_status: dict[str, str] = field(default_factory=dict)
    tracked: list[str] = field(default_factory=list)
    watched: list[str] = field(default_factory=list)
    changes_needed: list[dict] = field(default_factory=list)  # {name, status}


@dataclass
class EnvironmentComparison:
    """Comparison between current and expected environment states."""
    missing_nodes: list[str] = field(default_factory=list)
    extra_nodes: list[str] = field(default_factory=list)
    version_mismatches: list[dict] = field(default_factory=list)  # {name, expected, actual}
    packages_in_sync: bool = True
    package_sync_message: str = ""

    @property
    def is_synced(self) -> bool:
        """Check if environment is fully synced."""
        return (not self.missing_nodes and
                not self.extra_nodes and
                not self.version_mismatches and
                self.packages_in_sync)


@dataclass
class EnvironmentStatus:
    """Complete environment status including comparison and git/workflow state."""
    comparison: EnvironmentComparison
    git: GitStatus
    workflow: WorkflowStatus

    @classmethod
    def create(cls, comparison: EnvironmentComparison, git_status: GitStatus, workflow_status: WorkflowStatus) -> "EnvironmentStatus":
        """Factory method to create EnvironmentStatus from components."""
        return cls(
            comparison=comparison,
            git=git_status,
            workflow=workflow_status
        )

    @property
    def is_synced(self) -> bool:
        """Check if environment is fully synced."""
        return self.comparison.is_synced and self.workflow.in_sync

