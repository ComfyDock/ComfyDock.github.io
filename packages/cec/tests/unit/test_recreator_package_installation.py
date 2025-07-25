"""Tests for EnvironmentRecreator package installation functionality."""

import json
import pytest
from unittest.mock import patch, MagicMock, call

from comfyui_detector.core.recreator import EnvironmentRecreator
from comfyui_detector.exceptions import ValidationError, UVCommandError
from comfyui_detector.models import PyTorchSpec
from comfyui_detector.integrations.uv import UVResult


class TestEnvironmentRecreatorPackageInstallation:
    """Test package installation functionality in EnvironmentRecreator."""
    
    @pytest.fixture
    def base_manifest_data(self):
        """Base manifest data for testing."""
        return {
            "schema_version": "1.0",
            "system_info": {
                "python_version": "3.11.7",
                "cuda_version": "12.1",
                "torch_version": "2.1.0+cu121",
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
        
        return EnvironmentRecreator(
            manifest_path=str(manifest_path),
            target_path=str(tmp_path / "target"),
            uv_cache_path=str(tmp_path / "cache"),
            python_install_path=str(tmp_path / "python")
        )
    
    # PyTorch Package Installation Tests
    
    def test_install_pytorch_packages_with_index_url(self, recreator_with_manifest, tmp_path):
        """Test PyTorch package installation with correct index URL."""
        # Add PyTorch dependencies to manifest
        recreator_with_manifest.manifest.dependencies.pytorch = PyTorchSpec(
            packages={"torch": "2.1.0+cu121", "torchvision": "0.16.0+cu121"},
            index_url="https://download.pytorch.org/whl/cu121"
        )
        
        # Create target directory structure
        venv_path = tmp_path / "target" / ".venv"
        venv_path.mkdir(parents=True)
        
        with patch('comfyui_detector.recreator.UVInterface') as mock_uv_class:
            mock_uv = MagicMock()
            mock_uv_class.return_value = mock_uv
            # Mock successful install
            mock_uv.install_packages.return_value = UVResult(success=True, output="Installed packages")
            
            recreator_with_manifest.install_pytorch_packages()
            
            # Verify UV interface was created
            mock_uv_class.assert_called_once()
            
            # Verify install_packages was called with correct parameters
            expected_packages = ["torch==2.1.0+cu121", "torchvision==0.16.0+cu121"]
            mock_uv.install_packages.assert_called_once_with(
                venv_path=venv_path,
                packages=expected_packages,
                uv_cache=recreator_with_manifest.uv_cache_path,
                index_url="https://download.pytorch.org/whl/cu121"
            )
    
    def test_install_pytorch_packages_no_pytorch_in_manifest(self, recreator_with_manifest):
        """Test PyTorch installation when no PyTorch packages in manifest."""
        # Ensure no PyTorch packages in manifest
        assert recreator_with_manifest.manifest.dependencies.pytorch is None
        
        with patch('comfyui_detector.recreator.UVInterface') as mock_uv_class:
            mock_uv = MagicMock()
            mock_uv_class.return_value = mock_uv
            
            recreator_with_manifest.install_pytorch_packages()
            
            # Verify no UV commands were executed
            mock_uv_class.assert_not_called()
            mock_uv.install_packages.assert_not_called()
    
    def test_install_pytorch_packages_uv_command_error(self, recreator_with_manifest, tmp_path):
        """Test PyTorch installation when UV command fails."""
        # Add PyTorch dependencies
        recreator_with_manifest.manifest.dependencies.pytorch = PyTorchSpec(
            packages={"torch": "2.1.0+cu121"},
            index_url="https://download.pytorch.org/whl/cu121"
        )
        
        # Create target directory structure
        venv_path = tmp_path / "target" / ".venv"
        venv_path.mkdir(parents=True)
        
        with patch('comfyui_detector.recreator.UVInterface') as mock_uv_class:
            mock_uv = MagicMock()
            mock_uv_class.return_value = mock_uv
            mock_uv.install_packages.side_effect = UVCommandError("UV install failed")
            
            with pytest.raises(ValidationError, match="Failed to install PyTorch packages"):
                recreator_with_manifest.install_pytorch_packages()
    
    # Regular Package Installation Tests
    
    def test_install_packages_with_exact_versions(self, recreator_with_manifest, tmp_path):
        """Test regular package installation with exact versions."""
        # Add regular packages to manifest
        recreator_with_manifest.manifest.dependencies.packages = {
            "numpy": "1.24.3",
            "pillow": "10.0.1",
            "requests": "2.31.0"
        }
        
        # Create target directory structure
        venv_path = tmp_path / "target" / ".venv"
        venv_path.mkdir(parents=True)
        
        with patch('comfyui_detector.recreator.UVInterface') as mock_uv_class:
            mock_uv = MagicMock()
            mock_uv_class.return_value = mock_uv
            # Mock successful install
            mock_uv.install_packages.return_value = UVResult(success=True, output="Installed packages")
            
            recreator_with_manifest.install_packages()
            
            # Verify UV interface was created without path parameters
            mock_uv_class.assert_called_once_with()
            
            # Verify install_packages was called with correct packages
            expected_packages = ["numpy==1.24.3", "pillow==10.0.1", "requests==2.31.0"]
            mock_uv.install_packages.assert_called_once_with(
                venv_path=venv_path,
                packages=expected_packages,
                uv_cache=recreator_with_manifest.uv_cache_path
            )
    
    def test_install_packages_empty_package_list(self, recreator_with_manifest):
        """Test regular package installation when no packages in manifest."""
        # Ensure no regular packages in manifest
        assert not recreator_with_manifest.manifest.dependencies.packages
        
        with patch('comfyui_detector.recreator.UVInterface') as mock_uv_class:
            mock_uv = MagicMock()
            mock_uv_class.return_value = mock_uv
            
            recreator_with_manifest.install_packages()
            
            # Verify no UV commands were executed
            mock_uv_class.assert_not_called()
            mock_uv.install_packages.assert_not_called()
    
    def test_install_packages_uv_command_error(self, recreator_with_manifest, tmp_path):
        """Test regular package installation when UV command fails."""
        # Add regular packages
        recreator_with_manifest.manifest.dependencies.packages = {"numpy": "1.24.3"}
        
        # Create target directory structure
        venv_path = tmp_path / "target" / ".venv"
        venv_path.mkdir(parents=True)
        
        with patch('comfyui_detector.recreator.UVInterface') as mock_uv_class:
            mock_uv = MagicMock()
            mock_uv_class.return_value = mock_uv
            mock_uv.install_packages.side_effect = UVCommandError("UV install failed")
            
            with pytest.raises(ValidationError, match="Failed to install packages"):
                recreator_with_manifest.install_packages()
    
    # Editable Package Installation Tests
    
    def test_install_editable_packages_local_paths(self, recreator_with_manifest, tmp_path):
        """Test editable package installation with local paths."""
        # Add editable packages to manifest
        recreator_with_manifest.manifest.dependencies.editable_installs = [
            "-e /path/to/local/package",
            "-e /another/local/package"
        ]
        
        # Create target directory structure
        venv_path = tmp_path / "target" / ".venv"
        venv_path.mkdir(parents=True)
        
        with patch('comfyui_detector.recreator.UVInterface') as mock_uv_class:
            mock_uv = MagicMock()
            mock_uv_class.return_value = mock_uv
            # Mock successful install
            mock_uv.install_packages.return_value = UVResult(success=True, output="Installed packages")
            
            recreator_with_manifest.install_editable_packages()
            
            # Verify UV interface was created without path parameters
            mock_uv_class.assert_called_once_with()
            
            # Verify install_packages was called with editable packages
            expected_packages = ["-e /path/to/local/package", "-e /another/local/package"]
            mock_uv.install_packages.assert_called_once_with(
                venv_path=venv_path,
                packages=expected_packages,
                uv_cache=recreator_with_manifest.uv_cache_path
            )
    
    def test_install_editable_packages_git_urls(self, recreator_with_manifest, tmp_path):
        """Test editable package installation with git URLs."""
        # Add git-based editable packages
        recreator_with_manifest.manifest.dependencies.editable_installs = [
            "-e git+https://github.com/user/repo.git@main#egg=package"
        ]
        
        # Create target directory structure
        venv_path = tmp_path / "target" / ".venv"
        venv_path.mkdir(parents=True)
        
        with patch('comfyui_detector.recreator.UVInterface') as mock_uv_class:
            mock_uv = MagicMock()
            mock_uv_class.return_value = mock_uv
            
            recreator_with_manifest.install_editable_packages()
            
            # Verify install_packages was called with git editable package
            expected_packages = ["-e git+https://github.com/user/repo.git@main#egg=package"]
            mock_uv.install_packages.assert_called_once_with(
                venv_path=venv_path,
                packages=expected_packages,
                uv_cache=recreator_with_manifest.uv_cache_path
            )
    
    def test_install_editable_packages_empty_list(self, recreator_with_manifest):
        """Test editable package installation when no editable packages in manifest."""
        # Ensure no editable packages in manifest
        assert not recreator_with_manifest.manifest.dependencies.editable_installs
        
        with patch('comfyui_detector.recreator.UVInterface') as mock_uv_class:
            mock_uv = MagicMock()
            mock_uv_class.return_value = mock_uv
            
            recreator_with_manifest.install_editable_packages()
            
            # Verify no UV commands were executed
            mock_uv_class.assert_not_called()
            mock_uv.install_packages.assert_not_called()
    
    def test_install_editable_packages_uv_command_error(self, recreator_with_manifest, tmp_path):
        """Test editable package installation when UV command fails."""
        # Add editable packages
        recreator_with_manifest.manifest.dependencies.editable_installs = ["-e /path/to/package"]
        
        # Create target directory structure
        venv_path = tmp_path / "target" / ".venv"
        venv_path.mkdir(parents=True)
        
        with patch('comfyui_detector.recreator.UVInterface') as mock_uv_class:
            mock_uv = MagicMock()
            mock_uv_class.return_value = mock_uv
            mock_uv.install_packages.side_effect = UVCommandError("UV install failed")
            
            with pytest.raises(ValidationError, match="Failed to install editable packages"):
                recreator_with_manifest.install_editable_packages()
    
    # Git Requirements Installation Tests
    
    def test_install_git_requirements_github_repos(self, recreator_with_manifest, tmp_path):
        """Test git requirements installation with GitHub repositories."""
        # Add git requirements to manifest
        recreator_with_manifest.manifest.dependencies.git_requirements = [
            "git+https://github.com/user/repo1.git",
            "git+https://github.com/user/repo2.git@v1.0.0"
        ]
        
        # Create target directory structure
        venv_path = tmp_path / "target" / ".venv"
        venv_path.mkdir(parents=True)
        
        with patch('comfyui_detector.recreator.UVInterface') as mock_uv_class:
            mock_uv = MagicMock()
            mock_uv_class.return_value = mock_uv
            
            recreator_with_manifest.install_git_requirements()
            
            # Verify UV interface was created
            mock_uv_class.assert_called_once()
            
            # Verify install_packages was called with git requirements
            expected_packages = [
                "git+https://github.com/user/repo1.git",
                "git+https://github.com/user/repo2.git@v1.0.0"
            ]
            mock_uv.install_packages.assert_called_once_with(
                venv_path=venv_path,
                packages=expected_packages,
                uv_cache=recreator_with_manifest.uv_cache_path
            )
    
    def test_install_git_requirements_with_branch_tag(self, recreator_with_manifest, tmp_path):
        """Test git requirements installation with specific branches and tags."""
        # Add git requirements with branch/tag specifications
        recreator_with_manifest.manifest.dependencies.git_requirements = [
            "git+https://github.com/user/repo.git@develop",
            "git+https://github.com/user/repo.git@v2.1.0#egg=package"
        ]
        
        # Create target directory structure
        venv_path = tmp_path / "target" / ".venv"
        venv_path.mkdir(parents=True)
        
        with patch('comfyui_detector.recreator.UVInterface') as mock_uv_class:
            mock_uv = MagicMock()
            mock_uv_class.return_value = mock_uv
            
            recreator_with_manifest.install_git_requirements()
            
            # Verify install_packages was called with correct git requirements
            expected_packages = [
                "git+https://github.com/user/repo.git@develop",
                "git+https://github.com/user/repo.git@v2.1.0#egg=package"
            ]
            mock_uv.install_packages.assert_called_once_with(
                venv_path=venv_path,
                packages=expected_packages,
                uv_cache=recreator_with_manifest.uv_cache_path
            )
    
    def test_install_git_requirements_empty_list(self, recreator_with_manifest):
        """Test git requirements installation when no git requirements in manifest."""
        # Ensure no git requirements in manifest
        assert not recreator_with_manifest.manifest.dependencies.git_requirements
        
        with patch('comfyui_detector.recreator.UVInterface') as mock_uv_class:
            mock_uv = MagicMock()
            mock_uv_class.return_value = mock_uv
            
            recreator_with_manifest.install_git_requirements()
            
            # Verify no UV commands were executed
            mock_uv_class.assert_not_called()
            mock_uv.install_packages.assert_not_called()
    
    def test_install_git_requirements_uv_command_error(self, recreator_with_manifest, tmp_path):
        """Test git requirements installation when UV command fails."""
        # Add git requirements
        recreator_with_manifest.manifest.dependencies.git_requirements = [
            "git+https://github.com/user/repo.git"
        ]
        
        # Create target directory structure
        venv_path = tmp_path / "target" / ".venv"
        venv_path.mkdir(parents=True)
        
        with patch('comfyui_detector.recreator.UVInterface') as mock_uv_class:
            mock_uv = MagicMock()
            mock_uv_class.return_value = mock_uv
            mock_uv.install_packages.side_effect = UVCommandError("UV install failed")
            
            with pytest.raises(ValidationError, match="Failed to install git requirements"):
                recreator_with_manifest.install_git_requirements()
    
    # Integration Tests
    
    def test_install_packages_from_manifest_full_workflow(self, recreator_with_manifest, tmp_path):
        """Test complete package installation workflow with all package types."""
        # Add all types of packages to manifest
        recreator_with_manifest.manifest.dependencies.pytorch = PyTorchSpec(
            packages={"torch": "2.1.0+cu121"},
            index_url="https://download.pytorch.org/whl/cu121"
        )
        recreator_with_manifest.manifest.dependencies.packages = {"numpy": "1.24.3"}
        recreator_with_manifest.manifest.dependencies.editable_installs = ["-e /path/to/package"]
        recreator_with_manifest.manifest.dependencies.git_requirements = ["git+https://github.com/user/repo.git"]
        
        # Create target directory structure
        venv_path = tmp_path / "target" / ".venv"
        venv_path.mkdir(parents=True)
        
        with patch('comfyui_detector.recreator.UVInterface') as mock_uv_class:
            mock_uv = MagicMock()
            mock_uv_class.return_value = mock_uv
            
            with patch.object(recreator_with_manifest, 'create_virtual_environment') as mock_create_venv:
                recreator_with_manifest.install_packages_from_manifest()
                
                # Verify virtual environment was created first
                mock_create_venv.assert_called_once()
                
                # Verify all package types were installed in correct order
                assert mock_uv.install_packages.call_count == 4
                
                # Check call order and arguments
                calls = mock_uv.install_packages.call_args_list
                
                # Get the venv path
                venv_path = recreator_with_manifest.target_path / ".venv"
                
                # Get the uv_cache path for assertions
                uv_cache_path = recreator_with_manifest.uv_cache_path
                
                # PyTorch packages first
                assert calls[0] == call(venv_path=venv_path, packages=["torch==2.1.0+cu121"], uv_cache=uv_cache_path, index_url="https://download.pytorch.org/whl/cu121")
                # Regular packages second
                assert calls[1] == call(venv_path=venv_path, packages=["numpy==1.24.3"], uv_cache=uv_cache_path)
                # Git requirements third
                assert calls[2] == call(venv_path=venv_path, packages=["git+https://github.com/user/repo.git"], uv_cache=uv_cache_path)
                # Editable installs last
                assert calls[3] == call(venv_path=venv_path, packages=["-e /path/to/package"], uv_cache=uv_cache_path)
    
    def test_install_packages_from_manifest_partial_manifest(self, recreator_with_manifest, tmp_path):
        """Test package installation with partially populated manifest."""
        # Add only regular packages to manifest
        recreator_with_manifest.manifest.dependencies.packages = {"numpy": "1.24.3"}
        
        # Create target directory structure
        venv_path = tmp_path / "target" / ".venv"
        venv_path.mkdir(parents=True)
        
        with patch('comfyui_detector.recreator.UVInterface') as mock_uv_class:
            mock_uv = MagicMock()
            mock_uv_class.return_value = mock_uv
            
            with patch.object(recreator_with_manifest, 'create_virtual_environment') as mock_create_venv:
                recreator_with_manifest.install_packages_from_manifest()
                
                # Verify virtual environment was created
                mock_create_venv.assert_called_once()
                
                # Verify only regular packages were installed
                venv_path = recreator_with_manifest.target_path / ".venv"
                mock_uv.install_packages.assert_called_once_with(
                    venv_path=venv_path,
                    packages=["numpy==1.24.3"],
                    uv_cache=recreator_with_manifest.uv_cache_path
                )
    
    def test_install_packages_from_manifest_venv_creation_error(self, recreator_with_manifest):
        """Test package installation when virtual environment creation fails."""
        with patch.object(recreator_with_manifest, 'create_virtual_environment') as mock_create_venv:
            mock_create_venv.side_effect = ValidationError("Failed to create venv")
            
            with pytest.raises(ValidationError, match="Failed to create venv"):
                recreator_with_manifest.install_packages_from_manifest()