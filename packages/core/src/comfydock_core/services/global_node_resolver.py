"""Global node resolver using prebuilt mappings."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse


if TYPE_CHECKING:
    from comfydock_core.models.workflow import WorkflowNode, NodeInput

from ..logging.logging_config import get_logger
from ..utils.input_signature import create_node_key, normalize_workflow_inputs

logger = get_logger(__name__)


@dataclass
class NodeMatch:
    """A potential match for an unknown node."""
    package_id: str
    versions: List[str]
    match_type: str  # "exact", "type_only", "fuzzy"


@dataclass
class PackageSuggestion:
    """A package suggestion with installation details."""
    package_id: str
    suggested_version: str
    available_versions: List[str]
    github_url: Optional[str] = None
    display_name: Optional[str] = None


@dataclass
class ResolutionResult:
    """Result of resolving unknown nodes."""
    resolved: Dict[str, NodeMatch] = field(default_factory=dict)  # node_type -> match
    unresolved: List[str] = field(default_factory=list)
    suggested_packages: List[PackageSuggestion] = field(default_factory=list)


class GlobalNodeResolver:
    """Resolves unknown nodes using global mappings file."""

    def __init__(self, mappings_path: Optional[Path] = None):
        if mappings_path is None:
            # Default path relative to this file
            mappings_path = Path(__file__).parent.parent / "data" / "node_mappings.json"

        self.mappings_path = mappings_path
        self.mappings = {}
        self.packages = {}
        self.github_to_registry = {}
        self.loaded = False

    def load_mappings(self) -> bool:
        """Load global mappings from file."""
        if not self.mappings_path.exists():
            logger.warning(f"Global mappings file not found: {self.mappings_path}")
            return False

        try:
            with open(self.mappings_path, 'r') as f:
                data = json.load(f)

            self.mappings = data.get("mappings", {})
            self.packages = data.get("packages", {})
            self._build_github_to_registry_map()
            self.loaded = True

            stats = data.get("stats", {})
            logger.info(f"Loaded global mappings: {stats.get('signatures', 0)} signatures "
                       f"from {stats.get('packages', 0)} packages, "
                       f"{len(self.github_to_registry)} GitHub URLs")

            return True

        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load global mappings: {e}")
            return False

    def _normalize_github_url(self, url: str) -> str:
        """Normalize GitHub URL to canonical form."""
        if not url:
            return ""

        # Remove .git suffix
        url = re.sub(r'\.git$', '', url)

        # Parse URL
        parsed = urlparse(url)

        # Handle different GitHub URL formats
        if parsed.hostname in ('github.com', 'www.github.com'):
            # Extract owner/repo from path
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) >= 2:
                owner, repo = path_parts[0], path_parts[1]
                return f"https://github.com/{owner}/{repo}"

        # For SSH URLs like git@github.com:owner/repo
        if url.startswith('git@github.com:'):
            repo_path = url.replace('git@github.com:', '')
            repo_path = re.sub(r'\.git$', '', repo_path)
            return f"https://github.com/{repo_path}"

        # For SSH URLs like ssh://git@github.com/owner/repo
        if url.startswith('ssh://git@github.com/'):
            repo_path = url.replace('ssh://git@github.com/', '')
            repo_path = re.sub(r'\.git$', '', repo_path)
            return f"https://github.com/{repo_path}"

        return url

    def _build_github_to_registry_map(self):
        """Build reverse mapping from GitHub URLs to registry IDs."""
        self.github_to_registry = {}

        for package_id, package_data in self.packages.items():
            if repo_url := package_data.get('repository'):
                normalized_url = self._normalize_github_url(repo_url)
                if normalized_url:
                    self.github_to_registry[normalized_url] = {
                        'package_id': package_id,
                        'data': package_data
                    }

    def resolve_github_url(self, github_url: str) -> Optional[Tuple[str, Dict]]:
        """Resolve GitHub URL to registry ID and package data."""
        if not self.loaded and not self.load_mappings():
            return None

        normalized = self._normalize_github_url(github_url)
        if mapping := self.github_to_registry.get(normalized):
            return mapping['package_id'], mapping['data']
        return None

    def get_github_url_for_package(self, package_id: str) -> Optional[str]:
        """Get GitHub URL for a package ID."""
        if package_info := self.get_package_info(package_id):
            return package_info.get('repository')
        return None

    def resolve_workflow_nodes(self, custom_nodes: List[WorkflowNode]) -> ResolutionResult:
        """Resolve unknown/custom nodes from workflow.

        Args:
            custom_nodes: List of WorkflowNode that are not builtin nodes.

        Returns:
            Resolution result with matches and suggestions
        """
        if not self.loaded and not self.load_mappings():
            logger.warning("No global mappings available, cannot resolve nodes")
            return ResolutionResult(unresolved=[node.type for node in custom_nodes])

        result = ResolutionResult()

        for node in custom_nodes:
            node_type = node.type
            inputs = node.inputs
            
            match = self._resolve_single_node(node_type, inputs)

            if match:
                result.resolved[node_type] = match
            else:
                result.unresolved.append(node_type)

        # Build suggested packages from resolved nodes
        result.suggested_packages = self._build_package_suggestions(result.resolved)

        return result

    def _resolve_single_node(self, node_type: str, inputs: List[NodeInput]) -> Optional[NodeMatch]:
        """Resolve a single node type."""

        # Strategy 1: Try exact match with input signature
        if inputs:
            input_signature = normalize_workflow_inputs(inputs)
            logger.debug(f"Input signature for {node_type}: {input_signature}")
            if input_signature:
                exact_key = create_node_key(node_type, input_signature)
                logger.debug(f"Exact key for {node_type}: {exact_key}")
                if exact_key in self.mappings:
                    mapping = self.mappings[exact_key]
                    logger.debug(f"Exact match for {node_type}: {mapping['package_id']}")
                    return NodeMatch(
                        package_id=mapping["package_id"],
                        versions=mapping["versions"],
                        match_type="exact"
                    )

        # Strategy 2: Try type-only match
        type_only_key = create_node_key(node_type, "_")
        if type_only_key in self.mappings:
            mapping = self.mappings[type_only_key]
            logger.debug(f"Type-only match for {node_type}: {mapping['package_id']}")
            return NodeMatch(
                package_id=mapping["package_id"],
                versions=mapping["versions"],
                match_type="type_only"
            )

        # Strategy 3: Fuzzy search (simple substring matching)
        fuzzy_matches = self._fuzzy_search(node_type)
        if fuzzy_matches:
            # Just return the first fuzzy match
            best_match = fuzzy_matches[0]
            logger.debug(f"Fuzzy match for {node_type}: {best_match.package_id}")
            return best_match

        logger.debug(f"No match found for {node_type}")
        return None

    def _fuzzy_search(self, node_type: str) -> List[NodeMatch]:
        """Simple fuzzy search for node types."""
        matches = []
        node_type_lower = node_type.lower()

        for key, mapping in self.mappings.items():
            mapped_node_type = key.split("::")[0]

            # Simple substring matching
            if (node_type_lower in mapped_node_type.lower() or
                mapped_node_type.lower() in node_type_lower):

                matches.append(NodeMatch(
                    package_id=mapping["package_id"],
                    versions=mapping["versions"],
                    match_type="fuzzy"
                ))

        return matches

    def _build_package_suggestions(self, resolved: Dict[str, NodeMatch]) -> List[PackageSuggestion]:
        """Build suggested package installations from resolved nodes."""
        package_versions = {}  # package_id -> set of versions

        for node_type, match in resolved.items():
            package_id = match.package_id
            if package_id not in package_versions:
                package_versions[package_id] = set()

            # Add all compatible versions
            package_versions[package_id].update(match.versions)

        # Convert to PackageSuggestion objects
        suggestions = []
        for package_id, versions in package_versions.items():
            version_list = sorted(versions, reverse=True)
            suggested_version = version_list[0] if version_list else "latest"

            # Get package metadata
            package_info = self.get_package_info(package_id)
            github_url = package_info.get('repository') if package_info else None
            display_name = package_info.get('display_name') if package_info else None

            suggestions.append(PackageSuggestion(
                package_id=package_id,
                suggested_version=suggested_version,
                available_versions=version_list,
                github_url=github_url,
                display_name=display_name
            ))

        return suggestions

    def search_by_node_type(self, node_type: str) -> List[NodeMatch]:
        """Search for all packages that provide a specific node type."""
        if not self.loaded and not self.load_mappings():
            return []

        matches = []

        for key, mapping in self.mappings.items():
            mapped_node_type = key.split("::")[0]

            if mapped_node_type == node_type:
                matches.append(NodeMatch(
                    package_id=mapping["package_id"],
                    versions=mapping["versions"],
                    match_type="exact" if "::_" not in key else "type_only"
                ))

        return matches

    def get_package_info(self, package_id: str) -> Optional[Dict]:
        """Get package metadata."""
        if not self.loaded and not self.load_mappings():
            return None

        return self.packages.get(package_id)

    def is_synthetic_package(self, package_id: str) -> bool:
        """Check if a package is synthetic (from Manager, not registry)."""
        package_info = self.get_package_info(package_id)
        return package_info.get('synthetic', False) if package_info else False

    def get_synthetic_packages(self) -> List[str]:
        """Get list of synthetic package IDs."""
        if not self.loaded and not self.load_mappings():
            return []

        return [
            pkg_id for pkg_id, pkg_info in self.packages.items()
            if pkg_info.get('synthetic', False)
        ]

    def get_stats(self) -> Dict:
        """Get mapping statistics."""
        if not self.loaded:
            return {}

        synthetic_count = len(self.get_synthetic_packages())
        return {
            "total_mappings": len(self.mappings),
            "total_packages": len(self.packages),
            "synthetic_packages": synthetic_count,
            "registry_packages": len(self.packages) - synthetic_count,
            "exact_signatures": len([k for k in self.mappings.keys() if not k.endswith("::_")]),
            "type_only_mappings": len([k for k in self.mappings.keys() if k.endswith("::_")])
        }