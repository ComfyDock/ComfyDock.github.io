"""Comfy Registry API validation for custom nodes."""

import json
import urllib.request
import urllib.error
from typing import Dict, List, Optional
from packaging import version

from ..constants import DEFAULT_REGISTRY_URL
from ..logging_config import get_logger
from ..utils.cache import CacheManager
from ..utils.retry import retry_on_rate_limit, RetryConfig, RateLimitManager

logger = get_logger(__name__)


class ComfyRegistryValidator:
    """Validates custom nodes against the Comfy Registry API."""
    
    def __init__(self, base_url: str = DEFAULT_REGISTRY_URL, 
                 cache_manager: Optional[CacheManager] = None):
        self.base_url = base_url
        self.cache_manager = cache_manager or CacheManager()
        self.rate_limiter = RateLimitManager(min_interval=0.05)  # Slightly faster for registry
        # Configure retry for registry API
        self.retry_config = RetryConfig(
            max_retries=3,
            initial_delay=1.0,
            max_delay=30.0,
            exponential_base=2.0,
            jitter=True
        )
        
    def validate_node(self, node_name: str, version: Optional[str] = None) -> Dict:
        """
        Validate if a node exists in the registry and if the specific version is available.
        
        Returns:
            Dict with validation results including:
            - exists: bool - whether node exists in registry
            - version_available: bool - whether specific version is available
            - available_versions: List[str] - list of available versions
            - closest_version: str - closest available version if exact not found
            - registry_info: Dict - full registry info for the node
            - download_url: str - direct download URL if available
        """
        result = {
            'exists': False,
            'version_available': False,
            'available_versions': [],
            'closest_version': None,
            'registry_info': None,
            'registry_id': None,
            'download_url': None
        }
        
        # Normalize node name to potential registry ID
        # Common patterns: ComfyUI-Something -> comfyui-something
        registry_id = self.normalize_node_id(node_name)
        
        # Check if node exists in registry
        node_info = self.get_node_info(registry_id)
        if not node_info:
            # Try without 'comfyui-' prefix if it exists
            if registry_id.startswith('comfyui-'):
                alt_id = registry_id[8:]  # Remove 'comfyui-' prefix
                node_info = self.get_node_info(alt_id)
                if node_info:
                    registry_id = alt_id
        
        if not node_info:
            return result
            
        result['exists'] = True
        result['registry_info'] = node_info
        result['registry_id'] = registry_id
        
        # Get all available versions
        versions = self.get_node_versions(registry_id)
        if versions:
            result['available_versions'] = [v['version'] for v in versions]
            
            if version:
                # Check if specific version is available
                result['version_available'] = version in result['available_versions']
                
                if not result['version_available']:
                    # Find closest version
                    result['closest_version'] = self.find_closest_version(
                        version, result['available_versions']
                    )
            else:
                # No specific version requested, use latest
                result['closest_version'] = node_info.get('latest_version', {}).get('version')
        
        # Get download URL for the appropriate version
        target_version = None
        if version and result['version_available']:
            target_version = version
        elif result['closest_version']:
            target_version = result['closest_version']
        
        if target_version:
            install_info = self.get_install_info(registry_id, target_version)
            if install_info and install_info.get('downloadUrl'):
                result['download_url'] = install_info['downloadUrl']
        
        return result
    
    def normalize_node_id(self, node_name: str) -> str:
        """Normalize node name to registry ID format."""
        # Convert to lowercase and replace underscores with hyphens
        registry_id = node_name.lower().replace('_', '-')
        
        # Handle common patterns
        if not registry_id.startswith('comfyui-') and 'comfyui' not in registry_id:
            # Some nodes might not have comfyui prefix in registry
            pass
        
        return registry_id
    
    @retry_on_rate_limit(RetryConfig(max_retries=3, initial_delay=1.0, max_delay=30.0))
    def _make_registry_request(self, url: str) -> Optional[Dict]:
        """Make a request to Registry API with retry logic.
        
        Args:
            url: The API URL to request
            
        Returns:
            Parsed JSON response or None
        """
        # Rate limit ourselves
        self.rate_limiter.wait_if_needed('registry_api')
        
        req = urllib.request.Request(url)
        # Add user agent
        req.add_header('User-Agent', 'ComfyUI-Migration-Detector/1.0')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 200:
                return json.loads(response.read().decode('utf-8'))
        
        return None
        
    def get_node_info(self, node_id: str) -> Optional[Dict]:
        """Get node information from registry with caching."""
        cache_key = f"node:{node_id}"
        
        # Check cache first
        cached_data = self.cache_manager.get('registry', cache_key)
        if cached_data is not None:
            return cached_data
            
        url = f"{self.base_url}/nodes/{node_id}"
        
        try:
            data = self._make_registry_request(url)
            if data:
                # Remove status_reason from latest_version if present
                if 'latest_version' in data and 'status_reason' in data['latest_version']:
                    del data['latest_version']['status_reason']
                # Cache the result
                self.cache_manager.set('registry', cache_key, data)
                return data
        except urllib.error.HTTPError as e:
            if e.code == 404:
                logger.debug(f"Registry: Node '{node_id}' not found")
            else:
                logger.warning(f"Registry error for '{node_id}': HTTP {e.code}")
        except Exception as e:
            logger.error(f"Registry error for '{node_id}': {str(e)}")
            
        # Cache negative result too (with shorter TTL)
        self.cache_manager.set('registry', cache_key, None)
        return None
    
    def get_node_versions(self, node_id: str) -> Optional[List[Dict]]:
        """Get all versions of a node from registry with caching."""
        cache_key = f"versions:{node_id}"
        
        # Check cache first
        cached_data = self.cache_manager.get('registry', cache_key)
        if cached_data is not None:
            return cached_data
            
        url = f"{self.base_url}/nodes/{node_id}/versions"
        
        try:
            data = self._make_registry_request(url)
            if data:
                # Remove status_reason from each version entry
                for version_entry in data:
                    if 'status_reason' in version_entry:
                        del version_entry['status_reason']
                # Cache the result
                self.cache_manager.set('registry', cache_key, data)
                return data
        except Exception as e:
            logger.error(f"Registry error getting versions for '{node_id}': {str(e)}")
            
        # Cache negative result
        self.cache_manager.set('registry', cache_key, None)
        return None
    
    def get_install_info(self, node_id: str, version: Optional[str] = None) -> Optional[Dict]:
        """Get installation info including download URL for a node with caching."""
        cache_key = f"install:{node_id}:{version or 'latest'}"
        
        # Check cache first (use shorter TTL for install info as URLs might change)
        cached_data = self.cache_manager.get('registry', cache_key, ttl_seconds=3600)  # 1 hour
        if cached_data is not None:
            return cached_data
        
        # Build URL with optional version parameter
        url = f"{self.base_url}/nodes/{node_id}/install"
        if version:
            url += f"?version={version}"
        
        try:
            data = self._make_registry_request(url)
            if data:
                # Remove status_reason if present
                if 'status_reason' in data:
                    del data['status_reason']
                # Cache the result
                self.cache_manager.set('registry', cache_key, data)
                return data
        except urllib.error.HTTPError as e:
            if e.code == 404:
                logger.debug(f"Registry: Install info not found for '{node_id}' version '{version}'")
            else:
                logger.warning(f"Registry error getting install info for '{node_id}': HTTP {e.code}")
        except Exception as e:
            logger.error(f"Registry error getting install info for '{node_id}': {str(e)}")
        
        # Cache negative result
        self.cache_manager.set('registry', cache_key, None)
        return None
    
    def find_closest_version(self, target_version: str, available_versions: List[str]) -> Optional[str]:
        """Find the closest available version to the target version."""
        if not available_versions:
            return None
            
        try:
            target = version.parse(target_version)
            
            # Sort versions by how close they are to target
            version_distances = []
            for v in available_versions:
                try:
                    parsed = version.parse(v)
                    # Prefer same major version, then closest minor/patch
                    if parsed.major == target.major:
                        distance = abs(parsed.minor - target.minor) * 1000 + abs(parsed.micro - target.micro)
                    else:
                        distance = abs(parsed.major - target.major) * 1000000
                    version_distances.append((v, distance, parsed))
                except Exception:
                    continue
                    
            if version_distances:
                # Sort by distance, then by version (prefer newer if same distance)
                version_distances.sort(key=lambda x: (x[1], -x[2].major, -x[2].minor, -x[2].micro))
                return version_distances[0][0]
                
        except Exception as e:
            logger.error(f"Error finding closest version: {e}")
            
        # Fallback to latest version
        return available_versions[0] if available_versions else None