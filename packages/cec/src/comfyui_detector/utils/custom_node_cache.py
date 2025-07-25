"""Custom node cache manager for storing and retrieving downloaded nodes."""

import hashlib
import json
import shutil
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import os

from ..models.models import CustomNodeSpec
from ..logging_config import get_logger
from ..common import format_size

logger = get_logger(__name__)


@dataclass
class CachedNodeInfo:
    """Information about a cached custom node."""
    cache_key: str
    name: str
    install_method: str
    url: str
    ref: Optional[str] = None
    cached_at: str = ""
    last_accessed: str = ""
    access_count: int = 0
    size_bytes: int = 0
    content_hash: Optional[str] = None
    source_info: Dict = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CachedNodeInfo':
        """Create from dictionary."""
        return cls(**data)


class CustomNodeCacheManager:
    """Manages caching of custom node downloads."""
    
    def __init__(self, cache_base_path: Optional[Path] = None):
        """Initialize the cache manager.
        
        Args:
            cache_base_path: Base path for cache storage (defaults to platform-specific location)
        """
        self.cache_base = cache_base_path or self._get_default_cache_path()
        self.nodes_cache_dir = self.cache_base / "custom_nodes"
        self.store_dir = self.nodes_cache_dir / "store"
        self.index_file = self.nodes_cache_dir / "index.json"
        self.lock_file = self.nodes_cache_dir / ".lock"
        
        # Ensure cache directories exist
        self._ensure_cache_dirs()
        
        # Load or initialize index
        self.index = self._load_index()
        
    def _get_default_cache_path(self) -> Path:
        """Get platform-specific cache directory."""
        import platform
        system = platform.system()
        
        if system == "Windows":
            base = os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local')
            return Path(base) / 'comfyui-detector'
        elif system == "Darwin":
            return Path.home() / 'Library' / 'Caches' / 'comfyui-detector'
        else:
            xdg_cache = os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache')
            return Path(xdg_cache) / 'comfyui-detector'
    
    def _ensure_cache_dirs(self):
        """Ensure all cache directories exist."""
        self.store_dir.mkdir(parents=True, exist_ok=True)
        
    def _load_index(self) -> Dict[str, CachedNodeInfo]:
        """Load the cache index from disk."""
        if not self.index_file.exists():
            return {}
            
        try:
            with open(self.index_file, 'r') as f:
                data = json.load(f)
                
            # Convert to CachedNodeInfo objects
            index = {}
            for key, info_dict in data.get('nodes', {}).items():
                try:
                    index[key] = CachedNodeInfo.from_dict(info_dict)
                except Exception as e:
                    logger.warning(f"Failed to load cache entry {key}: {e}")
                    
            return index
            
        except Exception as e:
            logger.error(f"Failed to load cache index: {e}")
            return {}
    
    def _save_index(self):
        """Save the cache index to disk."""
        try:
            # Convert to serializable format
            data = {
                'version': '1.0',
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'nodes': {k: v.to_dict() for k, v in self.index.items()}
            }
            
            # Write atomically
            temp_file = self.index_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            # Replace original
            temp_file.replace(self.index_file)
            
        except Exception as e:
            logger.error(f"Failed to save cache index: {e}")
    
    def _with_lock(self, func, *args, **kwargs):
        """Execute a function with file-based locking for cache operations."""
        import platform
        
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        
        if platform.system() == 'Windows':
            # Windows-specific locking
            import msvcrt
            import time
            
            max_attempts = 50  # 5 seconds total
            attempt = 0
            
            while attempt < max_attempts:
                try:
                    with open(self.lock_file, 'w') as lock:
                        # Try to acquire exclusive lock
                        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
                        try:
                            return func(*args, **kwargs)
                        finally:
                            # Release lock
                            msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
                except IOError:
                    # Lock is held by another process
                    time.sleep(0.1)
                    attempt += 1
                    
            raise RuntimeError("Could not acquire cache lock after 5 seconds")
        else:
            # Unix-like systems (Linux, macOS)
            import fcntl
            
            with open(self.lock_file, 'w') as lock:
                try:
                    # Acquire exclusive lock
                    fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
                    return func(*args, **kwargs)
                finally:
                    # Release lock
                    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    
    def generate_cache_key(self, node_spec: CustomNodeSpec) -> str:
        """Generate a unique cache key for a custom node.
        
        The key is based on:
        - URL
        - Ref (for git repos)
        - Install method
        """
        components = [
            node_spec.url,
            node_spec.install_method,
            node_spec.ref or ""
        ]
        
        key_string = "|".join(components)
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]
    
    def is_cached(self, node_spec: CustomNodeSpec) -> bool:
        """Check if a custom node is already cached."""
        cache_key = self.generate_cache_key(node_spec)
        
        # Check index
        if cache_key not in self.index:
            return False
            
        # Verify the actual files exist
        cache_dir = self.store_dir / cache_key
        content_dir = cache_dir / "content"
        
        return content_dir.exists() and any(content_dir.iterdir())
    
    def get_cached_path(self, node_spec: CustomNodeSpec) -> Optional[Path]:
        """Get the path to cached node content if it exists.
        
        Returns:
            Path to the cached content directory, or None if not cached
        """
        if not self.is_cached(node_spec):
            return None
            
        cache_key = self.generate_cache_key(node_spec)
        content_path = self.store_dir / cache_key / "content"
        
        # Update access time and count
        def update_access():
            if cache_key in self.index:
                self.index[cache_key].last_accessed = datetime.now(timezone.utc).isoformat()
                self.index[cache_key].access_count += 1
                self._save_index()
        
        self._with_lock(update_access)
        
        return content_path
    
    def cache_node(self, node_spec: CustomNodeSpec, source_path: Path, 
                   archive_path: Optional[Path] = None) -> Path:
        """Cache a custom node from a source directory.
        
        Args:
            node_spec: The node specification
            source_path: Path to the extracted node content
            archive_path: Optional path to the original archive
            
        Returns:
            Path to the cached content
        """
        cache_key = self.generate_cache_key(node_spec)
        cache_dir = self.store_dir / cache_key
        content_dir = cache_dir / "content"
        
        def do_cache():
            # Clean up any existing cache entry
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                
            cache_dir.mkdir(parents=True)
            
            # Copy content
            logger.info(f"Caching custom node: {node_spec.name}")
            shutil.copytree(source_path, content_dir)
            
            # Copy archive if provided
            if archive_path and archive_path.exists():
                archive_dest = cache_dir / "archive"
                shutil.copy2(archive_path, archive_dest)
            
            # Calculate size
            size_bytes = sum(f.stat().st_size for f in content_dir.rglob('*') if f.is_file())
            
            # Generate content hash for integrity checking
            content_hash = self._calculate_content_hash(content_dir)
            
            # Create metadata
            metadata = {
                'node_spec': asdict(node_spec),
                'cached_at': datetime.now(timezone.utc).isoformat(),
                'source_size_bytes': size_bytes,
                'content_hash': content_hash,
                'has_archive': archive_path is not None
            }
            
            # Save metadata
            metadata_file = cache_dir / "metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Update index
            self.index[cache_key] = CachedNodeInfo(
                cache_key=cache_key,
                name=node_spec.name,
                install_method=node_spec.install_method,
                url=node_spec.url,
                ref=node_spec.ref,
                cached_at=metadata['cached_at'],
                last_accessed=metadata['cached_at'],
                access_count=1,
                size_bytes=size_bytes,
                content_hash=content_hash,
                source_info=metadata
            )
            
            self._save_index()
            logger.info(f"Cached {node_spec.name} ({format_size(size_bytes)}) with key: {cache_key}")
            
            return content_dir
        
        return self._with_lock(do_cache)
    
    def copy_from_cache(self, node_spec: CustomNodeSpec, dest_path: Path) -> bool:
        """Copy a cached node to a destination.
        
        Args:
            node_spec: The node specification
            dest_path: Destination path for the node
            
        Returns:
            True if successfully copied, False otherwise
        """
        cached_path = self.get_cached_path(node_spec)
        if not cached_path:
            return False
            
        try:
            # Ensure destination parent exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Remove destination if it exists
            if dest_path.exists():
                shutil.rmtree(dest_path)
                
            # Copy the cached content
            logger.info(f"Copying {node_spec.name} from cache to {dest_path}")
            shutil.copytree(cached_path, dest_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to copy from cache: {e}")
            return False
    
    def _calculate_content_hash(self, content_dir: Path) -> str:
        """Calculate SHA256 hash of directory content for integrity checking."""
        hasher = hashlib.sha256()
        
        # Sort files for consistent hashing
        for file_path in sorted(content_dir.rglob('*')):
            if file_path.is_file():
                # Include relative path in hash
                rel_path = file_path.relative_to(content_dir)
                hasher.update(str(rel_path).encode())
                
                # Include file content
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(65536), b''):
                        hasher.update(chunk)
                        
        return hasher.hexdigest()
    
    def verify_cache_integrity(self, cache_key: str) -> bool:
        """Verify the integrity of a cached node."""
        if cache_key not in self.index:
            return False
            
        cache_dir = self.store_dir / cache_key
        content_dir = cache_dir / "content"
        
        if not content_dir.exists():
            return False
            
        # Recalculate hash
        current_hash = self._calculate_content_hash(content_dir)
        stored_hash = self.index[cache_key].content_hash
        
        return current_hash == stored_hash
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        total_size = 0
        total_nodes = len(self.index)
        
        for info in self.index.values():
            total_size += info.size_bytes
            
        return {
            'cache_directory': str(self.nodes_cache_dir),
            'total_nodes': total_nodes,
            'total_size_bytes': total_size,
            'total_size_human': format_size(total_size),
            'nodes_by_method': self._get_nodes_by_method(),
            'most_accessed': self._get_most_accessed_nodes(5),
            'recently_cached': self._get_recently_cached_nodes(5)
        }
    
    def _get_nodes_by_method(self) -> Dict[str, int]:
        """Get count of cached nodes by install method."""
        counts = {}
        for info in self.index.values():
            method = info.install_method
            counts[method] = counts.get(method, 0) + 1
        return counts
    
    def _get_most_accessed_nodes(self, limit: int) -> List[Dict]:
        """Get the most frequently accessed cached nodes."""
        sorted_nodes = sorted(
            self.index.values(),
            key=lambda x: x.access_count,
            reverse=True
        )[:limit]
        
        return [
            {
                'name': node.name,
                'access_count': node.access_count,
                'size': format_size(node.size_bytes)
            }
            for node in sorted_nodes
        ]
    
    def _get_recently_cached_nodes(self, limit: int) -> List[Dict]:
        """Get the most recently cached nodes."""
        sorted_nodes = sorted(
            self.index.values(),
            key=lambda x: x.cached_at,
            reverse=True
        )[:limit]
        
        return [
            {
                'name': node.name,
                'cached_at': node.cached_at,
                'size': format_size(node.size_bytes)
            }
            for node in sorted_nodes
        ]
    
    def clear_cache(self, node_name: Optional[str] = None) -> int:
        """Clear cache entries.
        
        Args:
            node_name: Specific node name to clear, or None to clear all
            
        Returns:
            Number of entries cleared
        """
        def do_clear():
            cleared = 0
            
            if node_name:
                # Clear specific node
                entries_to_clear = [
                    (k, v) for k, v in self.index.items() 
                    if v.name == node_name
                ]
            else:
                # Clear all
                entries_to_clear = list(self.index.items())
            
            for cache_key, info in entries_to_clear:
                cache_dir = self.store_dir / cache_key
                if cache_dir.exists():
                    shutil.rmtree(cache_dir)
                    
                del self.index[cache_key]
                cleared += 1
                
            self._save_index()
            
            return cleared
        
        return self._with_lock(do_clear)
    
    def list_cached_nodes(self) -> List[CachedNodeInfo]:
        """Get a list of all cached nodes."""
        return list(self.index.values())