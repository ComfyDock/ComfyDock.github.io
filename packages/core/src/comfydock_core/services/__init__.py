"""External service integrations for ComfyDock."""

from .github_client import GitHubClient
from .registry_client import ComfyRegistryClient

__all__ = ["ComfyRegistryClient", "GitHubClient"]
