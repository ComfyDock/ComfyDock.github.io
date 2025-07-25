"""Custom node scanner for node discovery and analysis."""

import logging
from pathlib import Path
from typing import Dict, List

from ..constants import CUSTOM_NODES_BLACKLIST
from ..validators import GitHubReleaseChecker, ComfyRegistryValidator
from ..utils import get_git_info, parse_requirements_file, parse_pyproject_toml
from ..utils.cache import CacheManager
from ..logging_config import get_logger


class CustomNodeScanner:
    """Scans and analyzes custom nodes in ComfyUI."""

    def __init__(self, comfyui_path: Path, validate_registry: bool = False):
        self.logger = get_logger(__name__)
        self.comfyui_path = Path(comfyui_path).resolve()
        self.custom_nodes_path = self.comfyui_path / "custom_nodes"
        self.custom_nodes_blacklist = CUSTOM_NODES_BLACKLIST
        self.validate_registry = validate_registry
        
        # Create shared cache manager
        self.cache_manager = CacheManager() if validate_registry else None
        
        # Initialize validators with shared cache manager
        self.registry_validator = ComfyRegistryValidator(cache_manager=self.cache_manager) if validate_registry else None
        self.github_checker = GitHubReleaseChecker(cache_manager=self.cache_manager) if validate_registry else None
        
        self.custom_nodes_info = {}

    def scan_all(self) -> Dict[str, Dict]:
        """Scan all custom nodes for detailed information."""
        if not self.custom_nodes_path.exists():
            self.logger.warning("No custom_nodes directory found")
            return {}

        self.logger.info("Scanning custom nodes for detailed information...")
        if self.validate_registry:
            self.logger.info("Registry validation enabled")
            # Clean up expired cache entries at the start
            if self.cache_manager:
                self.cache_manager.cleanup_expired()

        # Count valid nodes first
        valid_nodes = [d for d in self.custom_nodes_path.iterdir() 
                       if d.is_dir() and not d.name.startswith('.') 
                       and d.name not in self.custom_nodes_blacklist]
        
        if hasattr(self, 'progress'):
            self.progress.start_task("Scanning custom nodes", len(valid_nodes))
        
        skipped_dirs = []
        for i, node_dir in enumerate(valid_nodes, 1):
            if hasattr(self, 'progress'):
                self.progress.update_task(f"Scanning {node_dir.name}", i)
                
            node_info = self._scan_single_custom_node(node_dir)
            self.custom_nodes_info[node_dir.name] = node_info
        
        # Handle skipped dirs separately
        for node_dir in self.custom_nodes_path.iterdir():
            if node_dir.is_dir() and node_dir not in valid_nodes:
                # Track skipped directories for logging
                if node_dir.name.startswith('.'):
                    skipped_dirs.append(f"{node_dir.name} (hidden)")
                elif node_dir.name in self.custom_nodes_blacklist:
                    skipped_dirs.append(f"{node_dir.name} (blacklisted)")
                else:
                    skipped_dirs.append(f"{node_dir.name} (other)")
        
        if hasattr(self, 'progress'):
            self.progress.complete_task(f"{len(self.custom_nodes_info)} nodes scanned")

        self._print_custom_nodes_summary(skipped_dirs)

        return self.custom_nodes_info

    def scan_requirements(self) -> Dict[str, Dict[str, List[str]]]:
        """Scan all custom nodes for requirements.txt files."""
        custom_node_reqs = {}
        missing_packages = set()  # Track all missing packages

        if not self.custom_nodes_path.exists():
            self.logger.warning("No custom_nodes directory found")
            return {'requirements': custom_node_reqs, 'missing_packages': list(missing_packages)}

        self.logger.info(f"Scanning custom nodes in {self.custom_nodes_path}")

        # Also check for install.py files that might install dependencies
        nodes_with_install_scripts = []

        for node_dir in self.custom_nodes_path.iterdir():
            if (node_dir.is_dir() and 
                not node_dir.name.startswith('.') and 
                node_dir.name not in self.custom_nodes_blacklist):
                # Check for requirements.txt
                req_path = node_dir / "requirements.txt"
                if req_path.exists():
                    node_reqs = parse_requirements_file(req_path)
                    if node_reqs:
                        custom_node_reqs[node_dir.name] = node_reqs
                        
                        # Track missing packages (don't print them individually)
                        for package in node_reqs.keys():
                            # This is where the "required but not installed" messages were coming from
                            # Just collect them instead of printing
                            missing_packages.add(package)

                # Check for install.py or other installation scripts
                install_scripts = ['install.py', 'setup.py', 'install.sh']
                for script in install_scripts:
                    if (node_dir / script).exists():
                        nodes_with_install_scripts.append((node_dir.name, script))

        self.logger.info(f"Found requirements in {len(custom_node_reqs)} custom nodes")
        
        # Print summary of missing packages if needed
        if missing_packages and self.logger.isEnabledFor(logging.INFO):
            self.logger.info(f"Found {len(missing_packages)} unique packages required by custom nodes")
            self.logger.debug(f"Missing packages: {', '.join(sorted(missing_packages))}")
        
        if nodes_with_install_scripts:
            self.logger.info(f"Found {len(nodes_with_install_scripts)} nodes with install scripts:")
            for node, script in nodes_with_install_scripts[:5]:  # Show first 5
                self.logger.info(f"  - {node}: {script}")
            if len(nodes_with_install_scripts) > 5:
                self.logger.info(f"  ... and {len(nodes_with_install_scripts) - 5} more")

        return {
            'requirements': custom_node_reqs,
            'nodes_with_install_scripts': nodes_with_install_scripts,
            'missing_packages': list(missing_packages)
        }

    def _scan_single_custom_node(self, node_dir: Path) -> Dict:
        """Scan a single custom node directory."""
        node_info = {
            'name': node_dir.name,
            'path': str(node_dir),
            'source': 'unknown',
            'version': None,
            'has_requirements': (node_dir / "requirements.txt").exists(),
            'has_pyproject': (node_dir / "pyproject.toml").exists(),
            'install_scripts': [],
            'registry_validated': False,
            'registry_validation': None,
            'github_validation': None
        }

        # Check for install scripts
        install_scripts = ['install.py', 'setup.py', 'install.sh']
        for script in install_scripts:
            if (node_dir / script).exists():
                node_info['install_scripts'].append(script)

        # Try to get info from pyproject.toml first
        pyproject_path = node_dir / "pyproject.toml"
        if pyproject_path.exists():
            project_info = parse_pyproject_toml(pyproject_path)
            if project_info:
                node_info['source'] = 'pyproject'
                node_info['project_name'] = project_info.get('name', node_dir.name)
                node_info['version'] = project_info.get('version')
                node_info['description'] = project_info.get('description', '')
                node_info['authors'] = project_info.get('authors', [])
                node_info['urls'] = project_info.get('urls', {})
                if project_info.get('dependencies'):
                    node_info['pyproject_dependencies'] = project_info['dependencies']

        # Get git information
        git_info = get_git_info(node_dir)
        if git_info:
            node_info['git'] = git_info
            if node_info['source'] == 'unknown':
                node_info['source'] = 'git'
            # Use git tag as version if no pyproject version
            if not node_info['version'] and git_info.get('tag'):
                node_info['version'] = git_info['tag']

        # Validate against registry and GitHub if enabled
        if self.validate_registry:
            self._validate_custom_node(node_info, node_dir)

        # Determine installation priority
        self._determine_install_priority(node_info, node_dir.name)

        return node_info

    def _validate_custom_node(self, node_info: Dict, node_dir: Path):
        """Validate a custom node against registry and GitHub."""
        self.logger.debug(f"Validating '{node_dir.name}' against registry...")

        # Remove the manual sleep - rate limiting is now handled by the validators
        # time.sleep(0.1)  # <-- REMOVE THIS LINE

        # Try with project name first, then directory name
        names_to_try = []
        if node_info.get('project_name'):
            names_to_try.append(node_info['project_name'])
        names_to_try.append(node_dir.name)

        validation_result = None
        for name in names_to_try:
            validation_result = self.registry_validator.validate_node(
                name, 
                node_info.get('version')
            )
            if validation_result['exists']:
                break

        if validation_result and validation_result['exists']:
            node_info['registry_validated'] = True
            node_info['registry_validation'] = validation_result
            node_info['registry_id'] = validation_result['registry_id']

            if validation_result['version_available']:
                self.logger.info(f"  {node_dir.name}: Found in registry with exact version {node_info.get('version')}")
            elif validation_result['closest_version']:
                self.logger.info(f"  {node_dir.name}: Found in registry, closest version: {validation_result['closest_version']}")
            else:
                self.logger.info(f"  {node_dir.name}: Found in registry")

            # Print download URL if available
            if validation_result.get('download_url'):
                self.logger.debug(f"  {node_dir.name}: Registry download URL available")
        else:
            self.logger.debug(f"  {node_dir.name}: Not found in registry")

        # Check GitHub releases if we have git info and registry doesn't have exact version
        git_info = node_info.get('git', {})
        if (git_info and git_info.get('github_owner') and git_info.get('github_repo') and 
            node_info.get('version') and self.github_checker and
            (not validation_result or not validation_result.get('version_available'))):

            try:
                self.logger.debug(f"  {node_dir.name}: Checking GitHub releases for exact version...")
                github_result = self.github_checker.find_version_in_github(
                    git_info['github_owner'],
                    git_info['github_repo'],
                    node_info['version']
                )

                node_info['github_validation'] = github_result

                if github_result['found']:
                    self.logger.info(f"  {node_dir.name}: Found exact version {node_info['version']} in GitHub {github_result['type']}s")
                elif github_result.get('closest_version'):
                    self.logger.info(f"  {node_dir.name}: Found in GitHub, closest version: {github_result['closest_version']}")
                else:
                    self.logger.debug(f"  {node_dir.name}: Version not found in GitHub releases/tags")
            except Exception as e:
                # The retry logic in the validators will handle rate limits,
                # so this will only catch other types of errors
                self.logger.debug(f"GitHub validation error for {node_dir.name}: {e}")

    def _calculate_priority_score(self, node_info: Dict) -> tuple[int, str, str]:
        """Calculate priority score for a custom node.
        
        Returns:
            tuple: (score, priority_type, reason)
        """
        # Define scoring weights
        PRIORITY_SCORES = {
            'registry_exact': 100,    # Exact version match in registry
            'github_exact': 90,       # Exact version match in GitHub
            'registry_close': 70,     # Close version match in registry
            'github_close': 60,       # Close version match in GitHub
            'registry_only': 50,      # Registry available but no version
            'git_only': 40,           # Git repository available
            'pyproject_only': 30,     # Has pyproject.toml
            'local': 10               # Local only
        }

        # Check for exact version matches first
        if node_info.get('registry_validated') and node_info['registry_validation']['version_available']:
            return PRIORITY_SCORES['registry_exact'], 'registry', 'exact version match in registry'

        if node_info.get('github_validation') and node_info['github_validation']['found']:
            return (
                PRIORITY_SCORES['github_exact'], 
                'github', 
                f"exact version match in GitHub {node_info['github_validation']['type']}"
            )

        # Check for close version matches
        registry_closest = (
            node_info.get("registry_validation", {}).get("closest_version")
            if node_info.get("registry_validated")
            else None
        )
        github_closest = (
            node_info.get("github_validation", {}).get("closest_version")
            if node_info.get("github_validation")
            else None
        )

        if registry_closest and github_closest and node_info.get('version'):
            # Compare version distances when both sources have versions
            registry_distance = self.github_checker.calculate_version_distance(
                node_info['version'], registry_closest
            )
            github_distance = self.github_checker.calculate_version_distance(
                node_info['version'], github_closest
            )

            # Prefer source with significantly closer version
            if github_distance < registry_distance / 10:
                return (
                    PRIORITY_SCORES['github_close'], 
                    'github',
                    f"GitHub version {github_closest} is much closer than registry {registry_closest}"
                )
            elif registry_distance < github_distance / 10:
                return (
                    PRIORITY_SCORES['registry_close'],
                    'registry',
                    f"Registry version {registry_closest} is much closer than GitHub {github_closest}"
                )
            else:
                # Similar distances, prefer registry for stability
                return (
                    PRIORITY_SCORES['registry_close'],
                    'registry',
                    f"Registry version {registry_closest} (similar distance to GitHub {github_closest})"
                )

        # Single source with version
        if registry_closest:
            return (
                PRIORITY_SCORES['registry_close'],
                'registry',
                f"closest version: {registry_closest}"
            )

        if github_closest:
            return (
                PRIORITY_SCORES['github_close'],
                'github',
                f"GitHub version: {github_closest}"
            )

        # Check for sources without specific versions
        if node_info.get('registry_validated'):
            return PRIORITY_SCORES['registry_only'], 'registry', 'found in registry (no version)'

        if node_info.get('git'):
            return PRIORITY_SCORES['git_only'], 'git', 'git repository available (no releases)'

        if node_info.get('source') == 'pyproject' and not self.validate_registry:
            return PRIORITY_SCORES['pyproject_only'], 'registry', 'has pyproject.toml (registry not validated)'

        # Default to local
        return PRIORITY_SCORES['local'], 'local', 'no remote source found'

    def _determine_install_priority(self, node_info: Dict, node_name: str = ''):
        """Determine installation priority for a custom node using scoring system."""
        # Calculate priority score
        score, priority_type, reason = self._calculate_priority_score(node_info)

        # Set node info
        node_info['install_priority'] = priority_type
        node_info['priority_reason'] = reason
        node_info['priority_score'] = score

        # Log priority if enabled
        if self.validate_registry and priority_type != 'local' and node_name:
            self.logger.debug(f"  {node_name}: Install priority: {priority_type} (score: {score}, {reason})")

        # Heuristic: Check if likely in ComfyUI Manager registry
        git_info = node_info.get('git', {})
        if git_info and git_info.get('github_owner') and git_info.get('github_repo'):
            if 'comfy' in git_info['github_repo'].lower():
                node_info['likely_in_registry'] = True

    def _print_custom_nodes_summary(self, skipped_dirs: List[str]):
        """Print summary statistics for custom nodes."""
        total_nodes = len(self.custom_nodes_info)
        pyproject_nodes = sum(1 for n in self.custom_nodes_info.values() if n['source'] == 'pyproject')
        git_nodes = sum(1 for n in self.custom_nodes_info.values() if 'git' in n)
        versioned_nodes = sum(1 for n in self.custom_nodes_info.values() if n['version'])
        registry_validated = sum(1 for n in self.custom_nodes_info.values() if n['registry_validated'])
        github_checked = sum(1 for n in self.custom_nodes_info.values() if n.get('github_validation'))

        self.logger.info(f"Scanned {total_nodes} custom nodes:")
        self.logger.info(f"  - {pyproject_nodes} have pyproject.toml")
        self.logger.info(f"  - {git_nodes} are git repositories")
        self.logger.info(f"  - {versioned_nodes} have detectable versions")
        if self.validate_registry:
            self.logger.info(f"  - {registry_validated} validated in registry")
            self.logger.info(f"  - {github_checked} checked against GitHub releases")

        if skipped_dirs:
            self.logger.info(f"Skipped {len(skipped_dirs)} directories:")
            for skipped in skipped_dirs[:10]:  # Show first 10 skipped directories
                self.logger.debug(f"  - {skipped}")
            if len(skipped_dirs) > 10:
                self.logger.debug(f"  ... and {len(skipped_dirs) - 10} more")
