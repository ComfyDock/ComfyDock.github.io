"""Integration tests for version-specific node add and replacement behavior.

Tests the following scenarios:
1. Adding a new node with specific version (should install that version)
2. Adding same node, same version (should fail - already exists)
3. Adding same node, different version for regular nodes (should auto-replace)
4. Adding same node, different version for dev nodes (should require confirmation)
5. Adding same node, different version for dev nodes with --force (should auto-replace)
6. Using node update without version (should update to latest)
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from comfydock_core.models.shared import NodeInfo
from comfydock_core.models.exceptions import CDNodeConflictError


class TestNodeVersionReplacement:
    """Test version-specific node installation and replacement."""

    def test_add_new_node_with_specific_version(self, test_env):
        """Test adding a new node with specific version installs that version.

        Given: No node is installed
        When: User runs `cfd node add pkg@1.0.0`
        Then: Node pkg version 1.0.0 is installed
        """
        # Mock node info for version 1.0.0
        node_info_v1 = NodeInfo(
            name="test-node",
            registry_id="test-node",
            source="registry",
            version="1.0.0",
            download_url="https://example.com/v1.zip"
        )

        cache_path = test_env.workspace_paths.cache / "custom_nodes" / "store" / "test-hash-v1" / "content"
        cache_path.mkdir(parents=True, exist_ok=True)
        (cache_path / "__init__.py").write_text("# Test node v1.0.0")

        with patch.object(test_env.node_manager.node_lookup, 'get_node') as mock_get_node, \
             patch.object(test_env.node_manager.node_lookup, 'download_to_cache') as mock_download, \
             patch.object(test_env.node_manager.node_lookup, 'scan_requirements') as mock_scan:

            mock_get_node.return_value = node_info_v1
            mock_download.return_value = cache_path
            mock_scan.return_value = []

            # ACT: Add node with specific version
            result = test_env.node_manager.add_node("test-node@1.0.0", no_test=True)

            # ASSERT: Node is installed with correct version
            assert result.name == "test-node"
            assert result.version == "1.0.0"

            # Verify in pyproject.toml
            nodes = test_env.pyproject.nodes.get_existing()
            assert "test-node" in nodes
            assert nodes["test-node"].version == "1.0.0"

            # Verify on filesystem
            node_path = test_env.custom_nodes_path / "test-node"
            assert node_path.exists()

    def test_add_same_node_same_version_fails(self, test_env):
        """Test adding a node with same version as installed fails.

        Given: Node pkg version 1.0.0 is installed
        When: User runs `cfd node add pkg@1.0.0`
        Then: Error raised indicating node already exists
        """
        # Install initial version
        node_info = NodeInfo(
            name="test-node",
            registry_id="test-node",
            source="registry",
            version="1.0.0"
        )

        cache_path = test_env.workspace_paths.cache / "custom_nodes" / "store" / "test-hash" / "content"
        cache_path.mkdir(parents=True, exist_ok=True)
        (cache_path / "__init__.py").write_text("# Test node")

        with patch.object(test_env.node_manager.node_lookup, 'get_node') as mock_get_node, \
             patch.object(test_env.node_manager.node_lookup, 'download_to_cache') as mock_download, \
             patch.object(test_env.node_manager.node_lookup, 'scan_requirements') as mock_scan:

            mock_get_node.return_value = node_info
            mock_download.return_value = cache_path
            mock_scan.return_value = []

            # Install first time
            test_env.node_manager.add_node("test-node@1.0.0", no_test=True)

            # ACT & ASSERT: Try to install same version again
            with pytest.raises(CDNodeConflictError) as exc_info:
                test_env.node_manager.add_node("test-node@1.0.0", no_test=True)

            assert "already installed" in str(exc_info.value).lower()

    def test_add_different_version_regular_node_auto_replaces(self, test_env):
        """Test adding different version of regular node auto-replaces.

        Given: Node pkg version 1.0.0 is installed (regular node from registry)
        When: User runs `cfd node add pkg@2.0.0`
        Then: Version 1.0.0 is removed and version 2.0.0 is installed automatically
        """
        # Install initial version 1.0.0
        node_info_v1 = NodeInfo(
            name="test-node",
            registry_id="test-node",
            source="registry",
            version="1.0.0"
        )

        cache_path_v1 = test_env.workspace_paths.cache / "custom_nodes" / "store" / "hash-v1" / "content"
        cache_path_v1.mkdir(parents=True, exist_ok=True)
        (cache_path_v1 / "__init__.py").write_text("# v1.0.0")

        with patch.object(test_env.node_manager.node_lookup, 'get_node') as mock_get_node, \
             patch.object(test_env.node_manager.node_lookup, 'download_to_cache') as mock_download, \
             patch.object(test_env.node_manager.node_lookup, 'scan_requirements') as mock_scan:

            mock_get_node.return_value = node_info_v1
            mock_download.return_value = cache_path_v1
            mock_scan.return_value = []

            test_env.node_manager.add_node("test-node@1.0.0", no_test=True)

        # Verify v1.0.0 is installed
        nodes = test_env.pyproject.nodes.get_existing()
        assert nodes["test-node"].version == "1.0.0"

        # Now install version 2.0.0
        node_info_v2 = NodeInfo(
            name="test-node",
            registry_id="test-node",
            source="registry",
            version="2.0.0"
        )

        cache_path_v2 = test_env.workspace_paths.cache / "custom_nodes" / "store" / "hash-v2" / "content"
        cache_path_v2.mkdir(parents=True, exist_ok=True)
        (cache_path_v2 / "__init__.py").write_text("# v2.0.0")

        with patch.object(test_env.node_manager.node_lookup, 'get_node') as mock_get_node, \
             patch.object(test_env.node_manager.node_lookup, 'download_to_cache') as mock_download, \
             patch.object(test_env.node_manager.node_lookup, 'scan_requirements') as mock_scan:

            mock_get_node.return_value = node_info_v2
            mock_download.return_value = cache_path_v2
            mock_scan.return_value = []

            # ACT: Install different version (should auto-replace)
            result = test_env.node_manager.add_node("test-node@2.0.0", no_test=True)

            # ASSERT: Version 2.0.0 is now installed
            assert result.version == "2.0.0"

            nodes = test_env.pyproject.nodes.get_existing()
            assert nodes["test-node"].version == "2.0.0"

            # Only one version exists
            assert len([k for k in nodes.keys() if "test-node" in k]) == 1

    def test_add_different_version_dev_node_requires_confirmation(self, test_env):
        """Test adding different version of dev node requires confirmation.

        Given: Node pkg is installed as dev node (source='development')
        When: User runs `cfd node add pkg@1.0.0` (without --force)
        Then: User is prompted for confirmation before replacement
        """
        # Manually create a dev node
        node_path = test_env.custom_nodes_path / "test-node"
        node_path.mkdir(parents=True)
        (node_path / "__init__.py").write_text("# Dev node")

        # Track as dev node
        test_env.node_manager.add_node("test-node", is_development=True, no_test=True)

        # Verify it's tracked as dev
        nodes = test_env.pyproject.nodes.get_existing()
        assert nodes["test-node"].source == "development"
        assert nodes["test-node"].version == "dev"

        # Try to install a registry version
        node_info_registry = NodeInfo(
            name="test-node",
            registry_id="test-node",
            source="registry",
            version="1.0.0"
        )

        cache_path = test_env.workspace_paths.cache / "custom_nodes" / "store" / "hash" / "content"
        cache_path.mkdir(parents=True, exist_ok=True)
        (cache_path / "__init__.py").write_text("# v1.0.0")

        # Mock a confirmation strategy that denies
        mock_strategy = MagicMock()
        mock_strategy.confirm_replace_dev_node.return_value = False

        with patch.object(test_env.node_manager.node_lookup, 'get_node') as mock_get_node, \
             patch.object(test_env.node_manager.node_lookup, 'download_to_cache') as mock_download, \
             patch.object(test_env.node_manager.node_lookup, 'scan_requirements') as mock_scan:

            mock_get_node.return_value = node_info_registry
            mock_download.return_value = cache_path
            mock_scan.return_value = []

            # ACT & ASSERT: Should raise error when user denies confirmation
            with pytest.raises(CDNodeConflictError) as exc_info:
                test_env.node_manager.add_node(
                    "test-node@1.0.0",
                    no_test=True,
                    confirmation_strategy=mock_strategy
                )

            # Verify confirmation was requested
            mock_strategy.confirm_replace_dev_node.assert_called_once()

            # Verify dev node is still there
            nodes = test_env.pyproject.nodes.get_existing()
            assert nodes["test-node"].source == "development"

    def test_add_different_version_dev_node_with_force_auto_replaces(self, test_env):
        """Test adding different version of dev node with --force auto-replaces.

        Given: Node pkg is installed as dev node
        When: User runs `cfd node add pkg@1.0.0 --force`
        Then: Dev node is replaced without confirmation
        """
        # Create dev node
        node_path = test_env.custom_nodes_path / "test-node"
        node_path.mkdir(parents=True)
        (node_path / "__init__.py").write_text("# Dev node")
        test_env.node_manager.add_node("test-node", is_development=True, no_test=True)

        # Install registry version with force=True
        node_info_registry = NodeInfo(
            name="test-node",
            registry_id="test-node",
            source="registry",
            version="1.0.0"
        )

        cache_path = test_env.workspace_paths.cache / "custom_nodes" / "store" / "hash" / "content"
        cache_path.mkdir(parents=True, exist_ok=True)
        (cache_path / "__init__.py").write_text("# v1.0.0")

        with patch.object(test_env.node_manager.node_lookup, 'get_node') as mock_get_node, \
             patch.object(test_env.node_manager.node_lookup, 'download_to_cache') as mock_download, \
             patch.object(test_env.node_manager.node_lookup, 'scan_requirements') as mock_scan:

            mock_get_node.return_value = node_info_registry
            mock_download.return_value = cache_path
            mock_scan.return_value = []

            # ACT: Force replace dev node
            result = test_env.node_manager.add_node("test-node@1.0.0", no_test=True, force=True)

            # ASSERT: Registry version is installed
            assert result.version == "1.0.0"

            nodes = test_env.pyproject.nodes.get_existing()
            assert nodes["test-node"].source == "registry"
            assert nodes["test-node"].version == "1.0.0"

    def test_add_without_version_on_existing_node_fails(self, test_env):
        """Test adding a node without version when already installed fails.

        Given: Node pkg version 1.0.0 is installed
        When: User runs `cfd node add pkg` (no version specified, latest is 2.0.0)
        Then: Error raised - node already exists (doesn't auto-upgrade)

        This validates that 'add' without version means "install new" not "upgrade to latest".
        Users should use 'node update' for upgrading.
        """
        # Install version 1.0.0
        node_info_v1 = NodeInfo(
            name="test-node",
            registry_id="test-node",
            source="registry",
            version="1.0.0"
        )

        cache_path_v1 = test_env.workspace_paths.cache / "custom_nodes" / "store" / "hash-v1" / "content"
        cache_path_v1.mkdir(parents=True, exist_ok=True)
        (cache_path_v1 / "__init__.py").write_text("# v1.0.0")

        with patch.object(test_env.node_manager.node_lookup, 'get_node') as mock_get_node, \
             patch.object(test_env.node_manager.node_lookup, 'download_to_cache') as mock_download, \
             patch.object(test_env.node_manager.node_lookup, 'scan_requirements') as mock_scan:

            mock_get_node.return_value = node_info_v1
            mock_download.return_value = cache_path_v1
            mock_scan.return_value = []

            test_env.node_manager.add_node("test-node@1.0.0", no_test=True)

        # Verify v1.0.0 is installed
        nodes = test_env.pyproject.nodes.get_existing()
        assert nodes["test-node"].version == "1.0.0"

        # Try to add again without version (registry would return latest = 2.0.0)
        node_info_v2_latest = NodeInfo(
            name="test-node",
            registry_id="test-node",
            source="registry",
            version="2.0.0"  # Latest version from registry
        )

        with patch.object(test_env.node_manager.node_lookup, 'get_node') as mock_get_node:
            mock_get_node.return_value = node_info_v2_latest

            # ACT & ASSERT: Should fail - node already exists
            # Even though latest is 2.0.0, we don't auto-upgrade
            with pytest.raises(CDNodeConflictError) as exc_info:
                test_env.node_manager.add_node("test-node", no_test=True)

            error_msg = str(exc_info.value).lower()
            assert "already installed" in error_msg or "already exists" in error_msg

        # Verify version didn't change
        nodes = test_env.pyproject.nodes.get_existing()
        assert nodes["test-node"].version == "1.0.0", "Version should not have changed"
