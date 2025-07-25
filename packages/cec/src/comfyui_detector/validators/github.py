"""GitHub release and tag validation for custom nodes."""

import json
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Tuple
from packaging import version

from ..constants import GITHUB_API_BASE
from ..logging_config import get_logger
from ..utils.cache import CacheManager
from ..utils.retry import retry_on_rate_limit, RetryConfig, RateLimitManager

logger = get_logger(__name__)


class GitHubReleaseChecker:
    """Check GitHub releases for custom nodes."""
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.api_base = GITHUB_API_BASE
        self.cache_manager = cache_manager or CacheManager()
        self.rate_limiter = RateLimitManager(min_interval=0.1)
        # Configure retry with GitHub-appropriate settings
        self.retry_config = RetryConfig(
            max_retries=5,
            initial_delay=2.0,
            max_delay=120.0,
            exponential_base=2.0,
            jitter=True
        )
        
    @retry_on_rate_limit(RetryConfig(max_retries=5, initial_delay=2.0, max_delay=120.0))
    def _make_github_request(self, url: str) -> Optional[Dict]:
        """Make a request to GitHub API with retry logic.
        
        Args:
            url: The API URL to request
            
        Returns:
            Parsed JSON response or None
        """
        # Rate limit ourselves
        self.rate_limiter.wait_if_needed('github_api')
        
        req = urllib.request.Request(url)
        # Add user agent to avoid rate limiting
        req.add_header('User-Agent', 'ComfyUI-Migration-Detector/1.0')
        # Add Accept header for GitHub API v3
        req.add_header('Accept', 'application/vnd.github.v3+json')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 200:
                # Check rate limit headers
                remaining = response.headers.get('X-RateLimit-Remaining')
                if remaining:
                    logger.debug(f"GitHub API rate limit remaining: {remaining}")
                    if int(remaining) < 10:
                        logger.warning(f"GitHub API rate limit low: {remaining} requests remaining")
                        
                return json.loads(response.read().decode('utf-8'))
        
        return None
        
    def get_releases(self, owner: str, repo: str, limit: int = 100) -> List[Dict]:
        """Get releases from GitHub API with caching."""
        cache_key = f"releases:{owner}/{repo}"
        
        # Check cache first
        cached_data = self.cache_manager.get('github', cache_key)
        if cached_data is not None:
            return cached_data[:limit]
            
        releases = []
        page = 1
        per_page = min(100, limit)  # GitHub max is 100 per page
        
        while len(releases) < limit:
            url = f"{self.api_base}/repos/{owner}/{repo}/releases?page={page}&per_page={per_page}"
            
            try:
                page_data = self._make_github_request(url)
                if not page_data:
                    break
                    
                releases.extend(page_data)
                if len(page_data) < per_page:
                    # No more pages
                    break
                    
                page += 1
                
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    logger.debug(f"GitHub repository not found: {owner}/{repo}")
                else:
                    logger.warning(f"GitHub API error for {owner}/{repo}: HTTP {e.code}")
                break
            except Exception as e:
                logger.error(f"Error fetching GitHub releases: {str(e)}")
                break
                
        # Cache the results
        if releases:
            self.cache_manager.set('github', cache_key, releases)
            
        return releases[:limit]
    
    def get_tags(self, owner: str, repo: str, limit: int = 100) -> List[Dict]:
        """Get tags from GitHub API with caching."""
        cache_key = f"tags:{owner}/{repo}"
        
        # Check cache first
        cached_data = self.cache_manager.get('github', cache_key)
        if cached_data is not None:
            return cached_data[:limit]
            
        tags = []
        page = 1
        per_page = min(100, limit)
        
        while len(tags) < limit:
            url = f"{self.api_base}/repos/{owner}/{repo}/tags?page={page}&per_page={per_page}"
            
            try:
                page_data = self._make_github_request(url)
                if not page_data:
                    break
                    
                tags.extend(page_data)
                if len(page_data) < per_page:
                    # No more pages
                    break
                    
                page += 1
                
            except Exception as e:
                logger.debug(f"Error fetching tags for {owner}/{repo}: {e}")
                break
                
        # Cache the results
        if tags:
            self.cache_manager.set('github', cache_key, tags)
            
        return tags[:limit]
    
    def find_version_in_github(self, owner: str, repo: str, target_version: str) -> Dict:
        """
        Find a specific version in GitHub releases or tags.
        
        Returns:
            Dict with:
            - found: bool
            - type: 'release' or 'tag'
            - data: release or tag data
            - available_versions: list of all versions found
        """
        # Use a composite cache key for version lookups
        cache_key = f"version_lookup:{owner}/{repo}:{target_version}"
        
        # Check cache first
        cached_result = self.cache_manager.get('github', cache_key, ttl_seconds=3600)  # 1 hour TTL for version lookups
        if cached_result is not None:
            return cached_result
            
        result = {
            'found': False,
            'type': None,
            'data': None,
            'available_versions': [],
            'closest_version': None,
            'closest_data': None
        }
        
        # Normalize version string (remove 'v' prefix if present)
        target_clean = target_version.lstrip('v')
        
        # Check releases first
        releases = self.get_releases(owner, repo)
        release_versions = []
        
        for release in releases:
            tag_name = release.get('tag_name', '')
            if tag_name:
                # Clean version for comparison
                version_clean = tag_name.lstrip('v')
                release_versions.append((version_clean, tag_name, release))
                
                # Check for exact match
                if version_clean == target_clean or tag_name == target_version:
                    result['found'] = True
                    result['type'] = 'release'
                    result['data'] = release
                    result['available_versions'] = [v[1] for v in release_versions]
                    # Cache and return
                    self.cache_manager.set('github', cache_key, result)
                    return result
        
        # Check tags if not found in releases
        tags = self.get_tags(owner, repo)
        tag_versions = []
        
        for tag in tags:
            tag_name = tag.get('name', '')
            if tag_name:
                version_clean = tag_name.lstrip('v')
                tag_versions.append((version_clean, tag_name, tag))
                
                # Check for exact match
                if version_clean == target_clean or tag_name == target_version:
                    result['found'] = True
                    result['type'] = 'tag'
                    result['data'] = tag
                    result['available_versions'] = [v[1] for v in release_versions] + [v[1] for v in tag_versions]
                    # Cache and return
                    self.cache_manager.set('github', cache_key, result)
                    return result
        
        # If no exact match, find closest version
        all_versions = release_versions + [(v[0], v[1], {'type': 'tag', **v[2]}) for v in tag_versions]
        result['available_versions'] = list(set([v[1] for v in all_versions]))
        
        if all_versions:
            closest = self.find_closest_version(target_version, all_versions)
            if closest:
                result['closest_version'] = closest[1]  # Original tag name
                result['closest_data'] = closest[2]
        
        # Cache the result
        self.cache_manager.set('github', cache_key, result)
        return result
    
    def find_closest_version(self, target_version: str, version_tuples: List[Tuple[str, str, Dict]]) -> Optional[Tuple[str, str, Dict]]:
        """Find the closest version from a list of (clean_version, original_tag, data) tuples."""
        if not version_tuples:
            return None
            
        try:
            target = version.parse(target_version.lstrip('v'))
            
            version_distances = []
            for clean_ver, orig_tag, data in version_tuples:
                try:
                    parsed = version.parse(clean_ver)
                    
                    # Calculate distance with strong preference for same major version
                    if parsed.major == target.major:
                        if parsed.minor == target.minor:
                            # Same major.minor - very close
                            distance = abs(parsed.micro - target.micro)
                        else:
                            # Same major, different minor
                            distance = abs(parsed.minor - target.minor) * 1000 + abs(parsed.micro - target.micro)
                    else:
                        # Different major version - much less preferred
                        distance = abs(parsed.major - target.major) * 1000000
                    
                    version_distances.append((clean_ver, orig_tag, data, distance, parsed))
                except Exception:
                    continue
            
            if version_distances:
                # Sort by distance, then by version (prefer newer if same distance)
                version_distances.sort(key=lambda x: (x[3], -x[4].major, -x[4].minor, -x[4].micro))
                return (version_distances[0][0], version_distances[0][1], version_distances[0][2])
                
        except Exception:
            pass
            
        return None
    
    def calculate_version_distance(self, version1: str, version2: str) -> float:
        """Calculate the distance between two versions (lower is closer)."""
        try:
            v1 = version.parse(version1.lstrip('v'))
            v2 = version.parse(version2.lstrip('v'))
            
            # Calculate distance with emphasis on major/minor versions
            if v1.major != v2.major:
                return abs(v1.major - v2.major) * 1000000
            elif v1.minor != v2.minor:
                return abs(v1.minor - v2.minor) * 1000
            else:
                return abs(v1.micro - v2.micro)
        except Exception:
            return float('inf')