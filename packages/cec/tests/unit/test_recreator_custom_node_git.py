"""Tests for EnvironmentRecreator custom node git installation functionality."""

import json
import pytest
from unittest.mock import patch

from comfyui_detector.core.recreator import EnvironmentRecreator
from comfyui_detector.exceptions import ValidationError, ComfyUIDetectorError
from comfyui_detector.models import CustomNodeSpec


class TestEnvironmentRecreatorCustomNodeGit:
    """Test custom node git installation functionality in EnvironmentRecreator."""
    
    @pytest.fixture
    def base_manifest_data(self):
        """Base manifest data for testing."""
        return {
            "schema_version": "1.0",
            "system_info": {
                "python_version": "3.11.7",
                "cuda_version": None,
                "torch_version": "2.1.0+cpu",
                "comfyui_version": "v0.3.47"
            },
            "custom_nodes": [],
            "dependencies": {}
        }
    
    @pytest.fixture
    def recreator_with_manifest(self, tmp_path, base_manifest_data):
        """Create EnvironmentRecreator with valid manifest."""
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(base_manifest_data))
        
        # Create directory structure
        target_path = tmp_path / "target"
        comfyui_path = target_path / "ComfyUI"
        custom_nodes_path = comfyui_path / "custom_nodes"
        custom_nodes_path.mkdir(parents=True, exist_ok=True)
        
        recreator = EnvironmentRecreator(
            manifest_path=str(manifest_path),
            target_path=str(target_path),
            uv_cache_path=str(tmp_path / "cache"),
            python_install_path=str(tmp_path / "python")
        )
        
        return recreator
    
    @pytest.fixture
    def git_node_spec(self):
        """CustomNodeSpec for git installation."""
        return CustomNodeSpec(
            name="test-custom-node",
            install_method="git",
            url="https://github.com/user/test-custom-node.git",
            has_post_install=False
        )
    
    @pytest.fixture
    def git_node_spec_with_ref(self):
        """CustomNodeSpec for git installation with specific ref."""
        return CustomNodeSpec(
            name="test-custom-node",
            install_method="git",
            url="https://github.com/user/test-custom-node.git",
            ref="v1.0.0",
            has_post_install=False
        )
    
    @pytest.fixture
    def git_node_spec_with_commit(self):
        """CustomNodeSpec for git installation with commit hash."""
        return CustomNodeSpec(
            name="test-custom-node",
            install_method="git",
            url="https://github.com/user/test-custom-node.git",
            ref="abc123def456",
            has_post_install=False
        )
    
    # Test successful git installation scenarios
    
    @patch('comfyui_detector.recreator.run_command')
    def test_install_custom_node_git_success_no_ref(
        self, mock_run_command, recreator_with_manifest, git_node_spec, tmp_path
    ):
        """Test successful installation of custom node via git clone without ref."""
        # Expected target directory path
        target_path = tmp_path / "target" / "ComfyUI" / "custom_nodes" / "test-custom-node"
        
        # Mock successful git clone - create directory when clone is called
        def mock_git_clone(cmd, **kwargs):
            if "clone" in cmd:
                target_path.mkdir(parents=True)
                (target_path / "__init__.py").write_text("# Custom node")
            return None
        
        mock_run_command.side_effect = mock_git_clone
        
        # Test the method
        success, node_name = recreator_with_manifest.install_custom_node_git(git_node_spec)
        
        # Verify success
        assert success is True
        assert node_name == "test-custom-node"
        
        # Verify git clone was called correctly
        mock_run_command.assert_called_once_with(
            ["git", "clone", "https://github.com/user/test-custom-node.git", str(target_path)],
            check=True,
            timeout=300
        )
    
    @patch('comfyui_detector.recreator.run_command')
    def test_install_custom_node_git_success_with_ref(
        self, mock_run_command, recreator_with_manifest, git_node_spec_with_ref, tmp_path
    ):
        """Test successful installation of custom node via git clone with ref."""
        # Expected target directory path
        target_path = tmp_path / "target" / "ComfyUI" / "custom_nodes" / "test-custom-node"
        
        # Mock successful git clone and checkout - create directory when clone is called
        def mock_git_commands(cmd, **kwargs):
            if "clone" in cmd:
                target_path.mkdir(parents=True)
                (target_path / "__init__.py").write_text("# Custom node")
            return None
        
        mock_run_command.side_effect = mock_git_commands
        
        # Test the method
        success, node_name = recreator_with_manifest.install_custom_node_git(git_node_spec_with_ref)
        
        # Verify success
        assert success is True
        assert node_name == "test-custom-node"
        
        # Verify git commands were called correctly
        expected_calls = [
            (["git", "clone", "https://github.com/user/test-custom-node.git", str(target_path)], {"check": True, "timeout": 300}),
            (["git", "checkout", "v1.0.0"], {"cwd": target_path, "check": True, "timeout": 60})
        ]
        
        actual_calls = [
            (call.args[0], call.kwargs) for call in mock_run_command.call_args_list
        ]
        
        assert len(actual_calls) == 2
        assert actual_calls[0] == expected_calls[0]
        assert actual_calls[1] == expected_calls[1]
    
    @patch('comfyui_detector.recreator.run_command')
    def test_install_custom_node_git_success_with_commit_hash(
        self, mock_run_command, recreator_with_manifest, git_node_spec_with_commit, tmp_path
    ):
        """Test successful installation of custom node via git clone with commit hash."""
        # Expected target directory path
        target_path = tmp_path / "target" / "ComfyUI" / "custom_nodes" / "test-custom-node"
        
        # Mock successful git clone and checkout - create directory when clone is called
        def mock_git_commands(cmd, **kwargs):
            if "clone" in cmd:
                target_path.mkdir(parents=True)
                (target_path / "__init__.py").write_text("# Custom node")
            return None
        
        mock_run_command.side_effect = mock_git_commands
        
        # Test the method
        success, node_name = recreator_with_manifest.install_custom_node_git(git_node_spec_with_commit)
        
        # Verify success
        assert success is True
        assert node_name == "test-custom-node"
        
        # Verify git commands were called correctly
        expected_calls = [
            (["git", "clone", "https://github.com/user/test-custom-node.git", str(target_path)], {"check": True, "timeout": 300}),
            (["git", "checkout", "abc123def456"], {"cwd": target_path, "check": True, "timeout": 60})
        ]
        
        actual_calls = [
            (call.args[0], call.kwargs) for call in mock_run_command.call_args_list
        ]
        
        assert len(actual_calls) == 2
        assert actual_calls[0] == expected_calls[0]
        assert actual_calls[1] == expected_calls[1]
    
    # Test node name extraction from various URL formats
    
    @patch('comfyui_detector.recreator.run_command')
    def test_install_custom_node_git_name_extraction_https_git(
        self, mock_run_command, recreator_with_manifest, tmp_path
    ):
        """Test node name extraction from HTTPS .git URL."""
        node_spec = CustomNodeSpec(
            name="ComfyUI-Custom-Scripts",
            install_method="git",
            url="https://github.com/pythongosssss/ComfyUI-Custom-Scripts.git",
            has_post_install=False
        )
        
        # Expected target directory
        target_path = tmp_path / "target" / "ComfyUI" / "custom_nodes" / "ComfyUI-Custom-Scripts"
        
        # Mock successful git clone - create directory when clone is called
        def mock_git_clone(cmd, **kwargs):
            if "clone" in cmd:
                target_path.mkdir(parents=True)
                (target_path / "__init__.py").write_text("# Custom node")
            return None
        
        mock_run_command.side_effect = mock_git_clone
        
        success, node_name = recreator_with_manifest.install_custom_node_git(node_spec)
        
        assert success is True
        assert node_name == "ComfyUI-Custom-Scripts"
    
    @patch('comfyui_detector.recreator.run_command')
    def test_install_custom_node_git_name_extraction_https_no_git(
        self, mock_run_command, recreator_with_manifest, tmp_path
    ):
        """Test node name extraction from HTTPS URL without .git suffix."""
        node_spec = CustomNodeSpec(
            name="ComfyUI-Manager",
            install_method="git",
            url="https://github.com/ltdrdata/ComfyUI-Manager",
            has_post_install=False
        )
        
        # Expected target directory
        target_path = tmp_path / "target" / "ComfyUI" / "custom_nodes" / "ComfyUI-Manager"
        
        # Mock successful git clone - create directory when clone is called
        def mock_git_clone(cmd, **kwargs):
            if "clone" in cmd:
                target_path.mkdir(parents=True)
                (target_path / "__init__.py").write_text("# Custom node")
            return None
        
        mock_run_command.side_effect = mock_git_clone
        
        success, node_name = recreator_with_manifest.install_custom_node_git(node_spec)
        
        assert success is True
        assert node_name == "ComfyUI-Manager"
    
    @patch('comfyui_detector.recreator.run_command')
    def test_install_custom_node_git_name_extraction_ssh(
        self, mock_run_command, recreator_with_manifest, tmp_path
    ):
        """Test node name extraction from SSH URL."""
        node_spec = CustomNodeSpec(
            name="some-node",
            install_method="git",
            url="git@github.com:user/some-node.git",
            has_post_install=False
        )
        
        # Expected target directory
        target_path = tmp_path / "target" / "ComfyUI" / "custom_nodes" / "some-node"
        
        # Mock successful git clone - create directory when clone is called
        def mock_git_clone(cmd, **kwargs):
            if "clone" in cmd:
                target_path.mkdir(parents=True)
                (target_path / "__init__.py").write_text("# Custom node")
            return None
        
        mock_run_command.side_effect = mock_git_clone
        
        success, node_name = recreator_with_manifest.install_custom_node_git(node_spec)
        
        assert success is True
        assert node_name == "some-node"
    
    # Test error scenarios
    
    def test_install_custom_node_git_invalid_install_method(
        self, recreator_with_manifest
    ):
        """Test ValidationError when install_method is not 'git'."""
        node_spec = CustomNodeSpec(
            name="test-node",
            install_method="archive",  # Wrong method
            url="https://github.com/user/repo.git"
        )
        
        with pytest.raises(ValidationError) as exc_info:
            recreator_with_manifest.install_custom_node_git(node_spec)
        
        assert "Expected install_method 'git'" in str(exc_info.value)
    
    @patch('comfyui_detector.recreator.run_command')
    def test_install_custom_node_git_clone_failure(
        self, mock_run_command, recreator_with_manifest, git_node_spec
    ):
        """Test ValidationError when git clone fails."""
        # Mock git clone failure
        mock_run_command.side_effect = ComfyUIDetectorError("fatal: repository 'https://github.com/user/test-custom-node.git' not found")
        
        with pytest.raises(ValidationError) as exc_info:
            recreator_with_manifest.install_custom_node_git(git_node_spec)
        
        assert "Failed to clone custom node repository" in str(exc_info.value)
        assert "repository 'https://github.com/user/test-custom-node.git' not found" in str(exc_info.value)
    
    @patch('comfyui_detector.recreator.run_command')
    def test_install_custom_node_git_checkout_failure(
        self, mock_run_command, recreator_with_manifest, git_node_spec_with_ref, tmp_path
    ):
        """Test ValidationError when git checkout fails."""
        # Expected target directory
        target_path = tmp_path / "target" / "ComfyUI" / "custom_nodes" / "test-custom-node"
        
        # Mock successful clone but failed checkout
        def mock_command_side_effect(cmd, **kwargs):
            if "clone" in cmd:
                # Create target directory to simulate successful clone
                target_path.mkdir(parents=True)
                (target_path / "__init__.py").write_text("# Custom node")
                return None
            elif "checkout" in cmd:
                raise ComfyUIDetectorError("error: pathspec 'v1.0.0' did not match any file(s) known to git")
            return None
        
        mock_run_command.side_effect = mock_command_side_effect
        
        with pytest.raises(ValidationError) as exc_info:
            recreator_with_manifest.install_custom_node_git(git_node_spec_with_ref)
        
        assert "Failed to checkout ref 'v1.0.0'" in str(exc_info.value)
        assert "pathspec 'v1.0.0' did not match any file(s) known to git" in str(exc_info.value)
    
    @patch('comfyui_detector.recreator.run_command')
    def test_install_custom_node_git_directory_not_created(
        self, mock_run_command, recreator_with_manifest, git_node_spec
    ):
        """Test ValidationError when git clone doesn't create expected directory."""
        # Mock git clone "success" but directory doesn't exist
        mock_run_command.return_value = None
        
        with pytest.raises(ValidationError) as exc_info:
            recreator_with_manifest.install_custom_node_git(git_node_spec)
        
        assert "Git clone completed but target directory does not exist" in str(exc_info.value)
    
    def test_install_custom_node_git_empty_url(self, recreator_with_manifest):
        """Test ValidationError when URL is empty."""
        node_spec = CustomNodeSpec(
            name="test-node",
            install_method="git",
            url="",
            has_post_install=False
        )
        
        with pytest.raises(ValidationError) as exc_info:
            recreator_with_manifest.install_custom_node_git(node_spec)
        
        assert "Git URL is required" in str(exc_info.value)
    
    def test_install_custom_node_git_invalid_url_format(self, recreator_with_manifest):
        """Test ValidationError when URL format is invalid."""
        node_spec = CustomNodeSpec(
            name="test-node",
            install_method="git",
            url="not-a-valid-url",
            has_post_install=False
        )
        
        with pytest.raises(ValidationError) as exc_info:
            recreator_with_manifest.install_custom_node_git(node_spec)
        
        assert "Invalid git URL format" in str(exc_info.value)
    
    # Test edge cases
    
    @patch('comfyui_detector.recreator.run_command')
    def test_install_custom_node_git_target_directory_exists(
        self, mock_run_command, recreator_with_manifest, git_node_spec, tmp_path
    ):
        """Test behavior when target directory already exists."""
        # Create target directory that already exists
        target_path = tmp_path / "target" / "ComfyUI" / "custom_nodes" / "test-custom-node"
        target_path.mkdir(parents=True)
        (target_path / "existing_file.py").write_text("# Existing content")
        
        with pytest.raises(ValidationError) as exc_info:
            recreator_with_manifest.install_custom_node_git(git_node_spec)
        
        assert "Target directory already exists" in str(exc_info.value)
        # Verify git clone was not called
        mock_run_command.assert_not_called()
    
    @patch('comfyui_detector.recreator.run_command')
    def test_install_custom_node_git_complex_url_with_subdirectory(
        self, mock_run_command, recreator_with_manifest, tmp_path
    ):
        """Test git installation with complex URL containing subdirectories."""
        node_spec = CustomNodeSpec(
            name="sub-project",
            install_method="git",
            url="https://github.com/organization/mono-repo.git",
            has_post_install=False
        )
        
        # Expected target directory
        target_path = tmp_path / "target" / "ComfyUI" / "custom_nodes" / "mono-repo"
        
        # Mock successful git clone - create directory when clone is called
        def mock_git_clone(cmd, **kwargs):
            if "clone" in cmd:
                target_path.mkdir(parents=True)
                (target_path / "__init__.py").write_text("# Custom node")
            return None
        
        mock_run_command.side_effect = mock_git_clone
        
        success, node_name = recreator_with_manifest.install_custom_node_git(node_spec)
        
        assert success is True
        assert node_name == "mono-repo"