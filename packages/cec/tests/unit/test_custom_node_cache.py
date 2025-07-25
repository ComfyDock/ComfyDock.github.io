"""Tests for custom node cache functionality."""

import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch

from src.comfyui_detector.utils.custom_node_cache import CustomNodeCacheManager, CachedNodeInfo
from src.comfyui_detector.models.models import CustomNodeSpec


@pytest.fixture
def temp_cache_dir():
    """Create a temporary directory for cache testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def cache_manager(temp_cache_dir):
    """Create a cache manager with temporary directory."""
    return CustomNodeCacheManager(cache_base_path=temp_cache_dir)


@pytest.fixture
def sample_node_spec():
    """Create a sample node specification for testing."""
    return CustomNodeSpec(
        name="test-node",
        url="https://github.com/test/test-node.git",
        install_method="git",
        ref="main"
    )


@pytest.fixture
def sample_content_dir(temp_cache_dir):
    """Create a sample content directory with some files."""
    content_dir = temp_cache_dir / "sample_content"
    content_dir.mkdir(parents=True)
    
    # Create some sample files
    (content_dir / "node.py").write_text("# Sample node code")
    (content_dir / "requirements.txt").write_text("torch>=2.0.0")
    
    return content_dir


class TestCustomNodeCacheManager:
    """Tests for CustomNodeCacheManager."""

    def test_initialization(self, cache_manager, temp_cache_dir):
        """Test cache manager initialization."""
        assert cache_manager.cache_base == temp_cache_dir
        assert cache_manager.nodes_cache_dir.exists()
        assert cache_manager.store_dir.exists()

    def test_generate_cache_key(self, cache_manager, sample_node_spec):
        """Test cache key generation."""
        key1 = cache_manager.generate_cache_key(sample_node_spec)
        key2 = cache_manager.generate_cache_key(sample_node_spec)
        
        # Same spec should generate same key
        assert key1 == key2
        assert len(key1) == 16  # Should be 16 characters
        
        # Different spec should generate different key
        different_spec = CustomNodeSpec(
            name="different-node",
            url="https://github.com/test/different-node.git", 
            install_method="git"
        )
        key3 = cache_manager.generate_cache_key(different_spec)
        assert key1 != key3

    def test_cache_node(self, cache_manager, sample_node_spec, sample_content_dir):
        """Test caching a node."""
        # Initially not cached
        assert not cache_manager.is_cached(sample_node_spec)
        
        # Cache the node
        cache_manager.cache_node(sample_node_spec, sample_content_dir)
        
        # Should now be cached
        assert cache_manager.is_cached(sample_node_spec)
        
        # Should be in index
        cache_key = cache_manager.generate_cache_key(sample_node_spec)
        assert cache_key in cache_manager.index
        
        # Check cached content exists
        cached_path = cache_manager.get_cached_path(sample_node_spec)
        assert cached_path is not None
        assert cached_path.exists()
        assert (cached_path / "node.py").exists()
        assert (cached_path / "requirements.txt").exists()

    def test_copy_from_cache(self, cache_manager, sample_node_spec, sample_content_dir, temp_cache_dir):
        """Test copying from cache."""
        # Cache the node first
        cache_manager.cache_node(sample_node_spec, sample_content_dir)
        
        # Create destination directory
        dest_dir = temp_cache_dir / "destination"
        
        # Copy from cache
        success = cache_manager.copy_from_cache(sample_node_spec, dest_dir)
        assert success
        assert dest_dir.exists()
        assert (dest_dir / "node.py").exists()
        assert (dest_dir / "requirements.txt").exists()

    def test_verify_cache_integrity(self, cache_manager, sample_node_spec, sample_content_dir):
        """Test cache integrity verification."""
        # Cache the node
        cache_manager.cache_node(sample_node_spec, sample_content_dir)
        
        cache_key = cache_manager.generate_cache_key(sample_node_spec)
        
        # Should be valid initially
        assert cache_manager.verify_cache_integrity(cache_key)
        
        # Corrupt the cache by modifying a file
        cached_path = cache_manager.get_cached_path(sample_node_spec)
        corrupted_file = cached_path / "node.py"
        corrupted_file.write_text("# Corrupted content")
        
        # Should now be invalid
        assert not cache_manager.verify_cache_integrity(cache_key)

    def test_clear_cache(self, cache_manager, sample_node_spec, sample_content_dir):
        """Test clearing cache."""
        # Cache the node
        cache_manager.cache_node(sample_node_spec, sample_content_dir)
        assert cache_manager.is_cached(sample_node_spec)
        
        # Clear specific node
        cleared = cache_manager.clear_cache(sample_node_spec.name)
        assert cleared == 1
        assert not cache_manager.is_cached(sample_node_spec)

    def test_get_cache_stats(self, cache_manager, sample_node_spec, sample_content_dir):
        """Test getting cache statistics."""
        # Initially empty
        stats = cache_manager.get_cache_stats()
        assert stats['total_nodes'] == 0
        assert stats['total_size_bytes'] == 0
        
        # Cache a node
        cache_manager.cache_node(sample_node_spec, sample_content_dir)
        
        # Should have stats
        stats = cache_manager.get_cache_stats()
        assert stats['total_nodes'] == 1
        assert stats['total_size_bytes'] > 0
        assert 'git' in stats['nodes_by_method']
        assert stats['nodes_by_method']['git'] == 1

    def test_list_cached_nodes(self, cache_manager, sample_node_spec, sample_content_dir):
        """Test listing cached nodes."""
        # Initially empty
        nodes = cache_manager.list_cached_nodes()
        assert len(nodes) == 0
        
        # Cache a node
        cache_manager.cache_node(sample_node_spec, sample_content_dir)
        
        # Should list the node
        nodes = cache_manager.list_cached_nodes()
        assert len(nodes) == 1
        assert nodes[0].name == sample_node_spec.name
        assert nodes[0].install_method == sample_node_spec.install_method
        assert nodes[0].url == sample_node_spec.url


class TestCachedNodeInfo:
    """Tests for CachedNodeInfo data class."""

    def test_to_dict_from_dict(self):
        """Test serialization and deserialization."""
        info = CachedNodeInfo(
            cache_key="test123",
            name="test-node", 
            install_method="git",
            url="https://github.com/test/node.git",
            ref="main",
            cached_at="2023-01-01T00:00:00",
            last_accessed="2023-01-01T00:00:00",
            access_count=5,
            size_bytes=1024,
            content_hash="abc123",
            source_info={"test": "data"}
        )
        
        # Convert to dict and back
        data = info.to_dict()
        restored = CachedNodeInfo.from_dict(data)
        
        assert restored.cache_key == info.cache_key
        assert restored.name == info.name
        assert restored.install_method == info.install_method
        assert restored.url == info.url
        assert restored.ref == info.ref
        assert restored.access_count == info.access_count
        assert restored.size_bytes == info.size_bytes


class TestCacheIntegration:
    """Integration tests for cache functionality."""

    @patch('src.comfyui_detector.utils.custom_node_cache.CustomNodeCacheManager._with_lock')
    def test_concurrent_access_simulation(self, mock_with_lock, cache_manager, sample_node_spec, sample_content_dir):
        """Test that locking mechanism is called for concurrent operations."""
        # Mock the lock to just call the function directly
        mock_with_lock.side_effect = lambda func, *args, **kwargs: func(*args, **kwargs)
        
        # Perform cache operations
        cache_manager.cache_node(sample_node_spec, sample_content_dir)
        cache_manager.get_cached_path(sample_node_spec)
        cache_manager.clear_cache()
        
        # Verify lock was called
        assert mock_with_lock.call_count >= 3

    def test_platform_specific_cache_paths(self, temp_cache_dir):
        """Test that platform-specific cache paths are generated correctly."""
        with patch('platform.system') as mock_system:
            # Test Windows
            mock_system.return_value = "Windows"
            windows_cache = temp_cache_dir / "windows"
            with patch.dict('os.environ', {'LOCALAPPDATA': str(windows_cache)}):
                manager = CustomNodeCacheManager()
                assert str(manager.cache_base).startswith(str(windows_cache))
            
            # Test macOS
            mock_system.return_value = "Darwin"
            with patch('pathlib.Path.home') as mock_home:
                mock_home.return_value = temp_cache_dir / "macos_home"
                manager = CustomNodeCacheManager()
                assert 'Library/Caches' in str(manager.cache_base)
            
            # Test Linux
            mock_system.return_value = "Linux"
            with patch('pathlib.Path.home') as mock_home:
                mock_home.return_value = temp_cache_dir / "linux_home"
                manager = CustomNodeCacheManager()
                assert '.cache' in str(manager.cache_base)