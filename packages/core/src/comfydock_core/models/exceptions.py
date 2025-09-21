# models/exceptions.py



class ComfyDockError(Exception):
    """Base exception for ComfyDock errors."""
    pass

# ====================================================
# Workspace exceptions
# ====================================================

class CDWorkspaceNotFoundError(ComfyDockError):
    """Workspace doesn't exist."""
    pass

class CDWorkspaceExistsError(ComfyDockError):
    """Workspace already exists."""
    pass

class CDWorkspaceError(ComfyDockError):
    """Workspace-related errors."""
    pass

# ===================================================
# Environment exceptions
# ===================================================

class CDEnvironmentError(ComfyDockError):
    """Environment-related errors."""
    pass

class CDEnvironmentNotFoundError(ComfyDockError):
    """Environment doesn't exist."""
    pass

class CDEnvironmentExistsError(ComfyDockError):
    """Environment already exists."""
    pass

# ===================================================
# Resolution exceptions
# ==================================================

class CDResolutionError(ComfyDockError):
    """Resolution errors."""
    pass

# ===================================================
# Node exceptions
# ===================================================

class CDNodeNotFoundError(ComfyDockError):
    """Raised when Node not found."""
    pass

class CDNodeConflictError(ComfyDockError):
    """Raised when Node has dependency conflicts."""
    pass

# ===================================================
# Registry exceptions
# ===================================================

class CDRegistryError(ComfyDockError):
    """Base class for registry errors."""
    pass

class CDRegistryAuthError(CDRegistryError):
    """Authentication/authorization errors with registry."""
    pass

class CDRegistryServerError(CDRegistryError):
    """Registry server errors (5xx)."""
    pass

class CDRegistryConnectionError(CDRegistryError):
    """Network/connection errors to registry."""
    pass

# ===================================================
# Pyproject exceptions
# ===================================================

class CDPyprojectError(ComfyDockError):
    """Errors related to pyproject.toml operations."""
    pass

class CDPyprojectNotFoundError(CDPyprojectError):
    """pyproject.toml file not found."""
    pass

class CDPyprojectInvalidError(CDPyprojectError):
    """pyproject.toml file is invalid or corrupted."""
    pass

# ===================================================
# Dependency exceptions
# ===================================================

class CDDependencyError(ComfyDockError):
    """Dependency-related errors."""
    pass

class CDPackageSyncError(CDDependencyError):
    """Package synchronization errors."""
    pass

# ===================================================
# Index exceptions
# ===================================================

class CDIndexError(ComfyDockError):
    """Index configuration errors."""
    pass

# ===================================================
# Process/Command exceptions
# ===================================================

class CDProcessError(ComfyDockError):
    """Raised when subprocess command execution fails."""

    def __init__(
        self,
        message: str,
        command: list[str] | None = None,
        stderr: str | None = None,
        stdout: str | None = None,
        returncode: int | None = None,
    ):
        super().__init__(message)
        self.command = command
        self.stderr = stderr
        self.stdout = stdout
        self.returncode = returncode


# ===================================================
# UV exceptions
# ==================================================

class UVNotInstalledError(ComfyDockError):
    """Raised when UV is not installed."""
    pass


class UVCommandError(ComfyDockError):
    """Raised when UV command execution fails."""

    def __init__(
        self,
        message: str,
        command: list[str] | None = None,
        stderr: str | None = None,
        stdout: str | None = None,
        returncode: int | None = None,
    ):
        super().__init__(message)
        self.command = command
        self.stderr = stderr
        self.stdout = stdout
        self.returncode = returncode
