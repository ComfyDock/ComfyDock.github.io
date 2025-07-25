"""Tests for EnvironmentRecreator class."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from comfyui_detector.core.recreator import EnvironmentRecreator
from comfyui_detector.exceptions import ValidationError, UVCommandError, ComfyUIDetectorError
from comfyui_detector.models import MigrationManifest


class TestEnvironmentRecreatorInit:
    """Test cases for EnvironmentRecreator initialization."""
    
    def test_valid_initialization(self, tmp_path):
        """Test successful initialization with valid parameters."""
        # Create a valid manifest file
        manifest_data = {
            "schema_version": "1.0",
            "system_info": {
                "python_version": "3.11.7",
                "cuda_version": None,
                "torch_version": "2.1.0+cpu",
                "comfyui_version": "v0.3.47"
            },
            "custom_nodes": [],
            "dependencies": {
                "packages": {
                    "torch": "2.1.0",
                    "numpy": "1.24.3"
                }
            }
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))
        
        target_path = tmp_path / "target"
        uv_cache_path = tmp_path / "cache"
        
        recreator = EnvironmentRecreator(
            manifest_path=str(manifest_path),
            target_path=str(target_path), 
            uv_cache_path=str(uv_cache_path),
            python_install_path=str(tmp_path / "python")
        )
        
        assert recreator.manifest_path == Path(manifest_path)
        assert recreator.target_path == Path(target_path)
        assert recreator.uv_cache_path == Path(uv_cache_path)
        assert recreator.python_install_path == Path(tmp_path / "python")
        assert isinstance(recreator.manifest, MigrationManifest)
    
    def test_nonexistent_manifest_path(self, tmp_path):
        """Test initialization with nonexistent manifest file."""
        manifest_path = tmp_path / "nonexistent.json"
        target_path = tmp_path / "target"
        uv_cache_path = tmp_path / "cache"
        
        with pytest.raises(ValidationError, match="Manifest file does not exist"):
            EnvironmentRecreator(
                manifest_path=str(manifest_path),
                target_path=str(target_path),
                uv_cache_path=str(uv_cache_path),
                python_install_path=str(tmp_path / "python")
            )
    
    def test_invalid_manifest_content(self, tmp_path):
        """Test initialization with invalid manifest content."""
        # Create invalid manifest file
        manifest_path = tmp_path / "invalid.json"
        manifest_path.write_text('{"invalid": "manifest"}')
        
        target_path = tmp_path / "target"
        uv_cache_path = tmp_path / "cache"
        
        with pytest.raises(ValidationError, match="Invalid manifest"):
            EnvironmentRecreator(
                manifest_path=str(manifest_path),
                target_path=str(target_path),
                uv_cache_path=str(uv_cache_path),
                python_install_path=str(tmp_path / "python")
            )
    
    def test_invalid_target_path_type(self, tmp_path):
        """Test initialization with invalid target path type."""
        manifest_data = {
            "schema_version": "1.0",
            "system_info": {
                "python_version": "3.11.7",
                "cuda_version": None,
                "torch_version": "2.1.0+cpu",
                "comfyui_version": "v0.3.47"
            },
            "custom_nodes": [],
            "dependencies": {"packages": {}}
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))
        
        with pytest.raises(ValidationError, match="target_path must be a string or Path"):
            EnvironmentRecreator(
                manifest_path=str(manifest_path),
                target_path=123,  # Invalid type
                uv_cache_path=str(tmp_path / "cache"),
                python_install_path=str(tmp_path / "python")
            )


class TestEnvironmentRecreatorDirectorySetup:
    """Test cases for directory structure creation."""
    
    def test_create_directory_structure_success(self, tmp_path):
        """Test successful directory structure creation."""
        # Create valid manifest
        manifest_data = {
            "schema_version": "1.0",
            "system_info": {
                "python_version": "3.11.7",
                "cuda_version": None,
                "torch_version": "2.1.0+cpu",
                "comfyui_version": "v0.3.47"
            },
            "custom_nodes": [],
            "dependencies": {"packages": {}}
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))
        
        target_path = tmp_path / "target"
        uv_cache_path = tmp_path / "cache"
        
        recreator = EnvironmentRecreator(
            manifest_path=str(manifest_path),
            target_path=str(target_path),
            uv_cache_path=str(uv_cache_path),
            python_install_path=str(tmp_path / "python")
        )
        
        recreator.create_directory_structure()
        
        # Verify directories were created
        assert (target_path / "ComfyUI").exists()
        assert (target_path / "ComfyUI").is_dir()
        assert (target_path / ".venv").exists()
        assert (target_path / ".venv").is_dir()
    
    def test_create_directory_structure_target_exists(self, tmp_path):
        """Test directory creation when target already exists."""
        # Create valid manifest
        manifest_data = {
            "schema_version": "1.0", 
            "system_info": {
                "python_version": "3.11.7",
                "cuda_version": None,
                "torch_version": "2.1.0+cpu",
                "comfyui_version": "v0.3.47"
            },
            "custom_nodes": [],
            "dependencies": {"packages": {}}
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))
        
        target_path = tmp_path / "target"
        target_path.mkdir()  # Pre-create target directory
        
        uv_cache_path = tmp_path / "cache"
        
        recreator = EnvironmentRecreator(
            manifest_path=str(manifest_path),
            target_path=str(target_path),
            uv_cache_path=str(uv_cache_path),
            python_install_path=str(tmp_path / "python")
        )
        
        recreator.create_directory_structure()
        
        # Should still create subdirectories successfully
        assert (target_path / "ComfyUI").exists()
        assert (target_path / ".venv").exists()
    
    @patch('pathlib.Path.mkdir')
    def test_create_directory_structure_permission_error(self, mock_mkdir, tmp_path):
        """Test directory creation with permission error."""
        # Create valid manifest
        manifest_data = {
            "schema_version": "1.0",
            "system_info": {
                "python_version": "3.11.7",
                "cuda_version": None, 
                "torch_version": "2.1.0+cpu",
                "comfyui_version": "v0.3.47"
            },
            "custom_nodes": [],
            "dependencies": {"packages": {}}
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))
        
        target_path = tmp_path / "target"
        uv_cache_path = tmp_path / "cache"
        
        # Mock mkdir to raise PermissionError
        mock_mkdir.side_effect = PermissionError("Permission denied")
        
        recreator = EnvironmentRecreator(
            manifest_path=str(manifest_path),
            target_path=str(target_path),
            uv_cache_path=str(uv_cache_path),
            python_install_path=str(tmp_path / "python")
        )
        
        with pytest.raises(ValidationError, match="Failed to create directory"):
            recreator.create_directory_structure()


class TestEnvironmentRecreatorValidation:
    """Test cases for manifest validation."""
    
    def test_validate_manifest_success(self, tmp_path):
        """Test successful manifest validation."""
        manifest_data = {
            "schema_version": "1.0",
            "system_info": {
                "python_version": "3.11.7",
                "cuda_version": "12.1",
                "torch_version": "2.1.0+cu121", 
                "comfyui_version": "v0.3.47"
            },
            "custom_nodes": [
                {
                    "name": "ComfyUI-Manager",
                    "install_method": "git",
                    "url": "https://github.com/ltdrdata/ComfyUI-Manager.git"
                }
            ],
            "dependencies": {
                "packages": {
                    "torch": "2.1.0",
                    "numpy": "1.24.3"
                }
            }
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))
        
        target_path = tmp_path / "target"
        uv_cache_path = tmp_path / "cache"
        
        recreator = EnvironmentRecreator(
            manifest_path=str(manifest_path),
            target_path=str(target_path),
            uv_cache_path=str(uv_cache_path),
            python_install_path=str(tmp_path / "python")
        )
        
        # Should not raise any exception
        recreator.validate_manifest()
    
    def test_validate_manifest_invalid_schema(self, tmp_path):
        """Test manifest validation with invalid schema version."""
        manifest_data = {
            "schema_version": "2.0",  # Invalid version
            "system_info": {
                "python_version": "3.11.7",
                "cuda_version": None,
                "torch_version": "2.1.0+cpu",
                "comfyui_version": "v0.3.47"
            },
            "custom_nodes": [],
            "dependencies": {"packages": {}}
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))
        
        target_path = tmp_path / "target"
        uv_cache_path = tmp_path / "cache"
        
        # Schema validation happens during initialization
        with pytest.raises(ValidationError, match="Unsupported schema version"):
            EnvironmentRecreator(
                manifest_path=str(manifest_path),
                target_path=str(target_path),
                uv_cache_path=str(uv_cache_path),
                python_install_path=str(tmp_path / "python")
            )


class TestEnvironmentRecreatorVirtualEnvironment:
    """Test cases for virtual environment creation."""
    
    def test_create_virtual_environment_success(self, tmp_path):
        """Test successful virtual environment creation with specific Python version."""
        # Create valid manifest with Python version
        manifest_data = {
            "schema_version": "1.0",
            "system_info": {
                "python_version": "3.11.7",
                "cuda_version": None,
                "torch_version": "2.1.0+cpu",
                "comfyui_version": "v0.3.47"
            },
            "custom_nodes": [],
            "dependencies": {"packages": {}}
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))
        
        target_path = tmp_path / "target"
        uv_cache_path = tmp_path / "cache"
        
        recreator = EnvironmentRecreator(
            manifest_path=str(manifest_path),
            target_path=str(target_path),
            uv_cache_path=str(uv_cache_path),
            python_install_path=str(tmp_path / "python")
        )
        
        # Mock the UV interface
        with patch('comfyui_detector.recreator.UVInterface') as mock_uv_class:
            mock_uv_instance = MagicMock()
            mock_uv_class.return_value = mock_uv_instance
            
            recreator.create_virtual_environment()
            
            # Verify UV interface was created with cache path
            mock_uv_class.assert_called_once()
            
            # Verify create_venv was called with correct parameters
            expected_venv_path = target_path / ".venv"
            mock_uv_instance.create_venv.assert_called_once_with(
                path=expected_venv_path,
                python_version="3.11.7"
            )
    
    def test_create_virtual_environment_uv_command_error(self, tmp_path):
        """Test virtual environment creation handling UV command errors."""
        # Create valid manifest
        manifest_data = {
            "schema_version": "1.0",
            "system_info": {
                "python_version": "3.12.1",
                "cuda_version": None,
                "torch_version": "2.1.0+cpu",
                "comfyui_version": "v0.3.47"
            },
            "custom_nodes": [],
            "dependencies": {"packages": {}}
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))
        
        target_path = tmp_path / "target"
        uv_cache_path = tmp_path / "cache"
        
        recreator = EnvironmentRecreator(
            manifest_path=str(manifest_path),
            target_path=str(target_path),
            uv_cache_path=str(uv_cache_path),
            python_install_path=str(tmp_path / "python")
        )
        
        # Mock UV interface to raise error
        with patch('comfyui_detector.recreator.UVInterface') as mock_uv_class:
            mock_uv_instance = MagicMock()
            mock_uv_class.return_value = mock_uv_instance
            mock_uv_instance.create_venv.side_effect = UVCommandError("Python 3.12.1 not found")
            
            with pytest.raises(ValidationError, match="Failed to create virtual environment"):
                recreator.create_virtual_environment()
    
    def test_create_virtual_environment_with_directory_structure(self, tmp_path):
        """Test virtual environment creation creates directory structure if needed."""
        # Create valid manifest
        manifest_data = {
            "schema_version": "1.0",
            "system_info": {
                "python_version": "3.10.12",
                "cuda_version": "12.1",
                "torch_version": "2.1.0+cu121",
                "comfyui_version": "v0.3.47"
            },
            "custom_nodes": [],
            "dependencies": {"packages": {}}
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))
        
        target_path = tmp_path / "target"
        uv_cache_path = tmp_path / "cache"
        
        recreator = EnvironmentRecreator(
            manifest_path=str(manifest_path),
            target_path=str(target_path),
            uv_cache_path=str(uv_cache_path),
            python_install_path=str(tmp_path / "python")
        )
        
        # Mock UV interface
        with patch('comfyui_detector.recreator.UVInterface') as mock_uv_class:
            mock_uv_instance = MagicMock()
            mock_uv_class.return_value = mock_uv_instance
            
            # Mock the create_directory_structure method
            with patch.object(recreator, 'create_directory_structure') as mock_create_dirs:
                recreator.create_virtual_environment()
                
                # Verify directory structure is created first
                mock_create_dirs.assert_called_once()
                
                # Verify venv creation happens after
                mock_uv_instance.create_venv.assert_called_once_with(
                    path=target_path / ".venv",
                    python_version="3.10.12"
                )
    
    def test_create_virtual_environment_missing_python_version(self, tmp_path):
        """Test virtual environment creation with missing Python version in manifest."""
        # Create manifest without python_version (should not happen with validation, but test edge case)
        manifest_data = {
            "schema_version": "1.0",
            "system_info": {
                "python_version": "",  # Empty string
                "cuda_version": None,
                "torch_version": "2.1.0+cpu",
                "comfyui_version": "v0.3.47"
            },
            "custom_nodes": [],
            "dependencies": {"packages": {}}
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))
        
        target_path = tmp_path / "target"
        uv_cache_path = tmp_path / "cache"
        
        # This should fail during manifest validation, but let's test the edge case
        try:
            recreator = EnvironmentRecreator(
                manifest_path=str(manifest_path),
                target_path=str(target_path),
                uv_cache_path=str(uv_cache_path),
                python_install_path=str(tmp_path / "python")
            )
            
            # Mock UV interface
            with patch('comfyui_detector.recreator.UVInterface') as mock_uv_class:
                mock_uv_instance = MagicMock()
                mock_uv_class.return_value = mock_uv_instance
                
                with pytest.raises(ValidationError, match="Invalid Python version"):
                    recreator.create_virtual_environment()
        
        except ValidationError:
            # If it fails during init due to validation, that's expected
            pytest.skip("Manifest validation prevents empty Python version")
    
    def test_create_virtual_environment_uv_cache_path_used(self, tmp_path):
        """Test that UV cache path is properly utilized during venv creation."""
        # Create valid manifest
        manifest_data = {
            "schema_version": "1.0",
            "system_info": {
                "python_version": "3.11.7",
                "cuda_version": None,
                "torch_version": "2.1.0+cpu",
                "comfyui_version": "v0.3.47"
            },
            "custom_nodes": [],
            "dependencies": {"packages": {}}
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))
        
        target_path = tmp_path / "target"
        uv_cache_path = tmp_path / "uv_cache"
        
        recreator = EnvironmentRecreator(
            manifest_path=str(manifest_path),
            target_path=str(target_path),
            uv_cache_path=str(uv_cache_path),
            python_install_path=str(tmp_path / "python")
        )
        
        # Mock UV interface and verify cache path is considered
        with patch('comfyui_detector.recreator.UVInterface') as mock_uv_class:
            mock_uv_instance = MagicMock()
            mock_uv_class.return_value = mock_uv_instance
            
            recreator.create_virtual_environment()
            
            # The UVInterface should be created (cache path handling is internal to UV)
            mock_uv_class.assert_called_once()
            mock_uv_instance.create_venv.assert_called_once()


class TestComfyUIInstallation:
    """Test cases for ComfyUI installation."""
    
    def test_install_comfyui_with_valid_tag(self, tmp_path):
        """Test ComfyUI installation with valid tag version."""
        # Create valid manifest with tag version
        manifest_data = {
            "schema_version": "1.0",
            "system_info": {
                "python_version": "3.11.7",
                "cuda_version": None,
                "torch_version": "2.1.0+cpu",
                "comfyui_version": "v0.3.47"
            },
            "custom_nodes": [],
            "dependencies": {"packages": {}}
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))
        
        target_path = tmp_path / "target"
        uv_cache_path = tmp_path / "cache"
        
        recreator = EnvironmentRecreator(
            manifest_path=str(manifest_path),
            target_path=str(target_path),
            uv_cache_path=str(uv_cache_path),
            python_install_path=str(tmp_path / "python")
        )
        
        # Mock git commands
        with patch('comfyui_detector.recreator.run_command') as mock_run_command:
            # Mock successful git clone and checkout
            mock_run_command.return_value = None
            
            # Mock the ComfyUI files existing after installation
            with patch('pathlib.Path.exists', return_value=True):
                
                recreator.install_comfyui()
                
                # Verify git clone was called
                expected_clone_call = call(
                    ["git", "clone", "https://github.com/comfyanonymous/ComfyUI", str(target_path / "ComfyUI")],
                    check=True,
                    timeout=300
                )
                # Verify git checkout was called
                expected_checkout_call = call(
                    ["git", "checkout", "v0.3.47"],
                    cwd=target_path / "ComfyUI",
                    check=True,
                    timeout=60
                )
                
                mock_run_command.assert_has_calls([expected_clone_call, expected_checkout_call])
    
    def test_install_comfyui_with_commit_hash(self, tmp_path):
        """Test ComfyUI installation with commit hash."""
        # Create valid manifest with commit hash
        manifest_data = {
            "schema_version": "1.0",
            "system_info": {
                "python_version": "3.11.7",
                "cuda_version": None,
                "torch_version": "2.1.0+cpu",
                "comfyui_version": "a1b2c3d4e5f6789012345678901234567890abcd"
            },
            "custom_nodes": [],
            "dependencies": {"packages": {}}
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))
        
        target_path = tmp_path / "target"
        uv_cache_path = tmp_path / "cache"
        
        recreator = EnvironmentRecreator(
            manifest_path=str(manifest_path),
            target_path=str(target_path),
            uv_cache_path=str(uv_cache_path),
            python_install_path=str(tmp_path / "python")
        )
        
        # Mock git commands
        with patch('comfyui_detector.recreator.run_command') as mock_run_command:
            mock_run_command.return_value = None
            
            # Mock the ComfyUI files existing after installation
            with patch('pathlib.Path.exists', return_value=True):
                
                recreator.install_comfyui()
                
                # Verify git checkout was called with commit hash
                expected_checkout_call = call(
                    ["git", "checkout", "a1b2c3d4e5f6789012345678901234567890abcd"],
                    cwd=target_path / "ComfyUI",
                    check=True,
                    timeout=60
                )
                
                assert expected_checkout_call in mock_run_command.call_args_list
    
    def test_install_comfyui_with_branch_name(self, tmp_path):
        """Test ComfyUI installation with branch name."""
        # Create valid manifest with branch name
        manifest_data = {
            "schema_version": "1.0",
            "system_info": {
                "python_version": "3.11.7",
                "cuda_version": None,
                "torch_version": "2.1.0+cpu",
                "comfyui_version": "master"
            },
            "custom_nodes": [],
            "dependencies": {"packages": {}}
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))
        
        target_path = tmp_path / "target"
        uv_cache_path = tmp_path / "cache"
        
        recreator = EnvironmentRecreator(
            manifest_path=str(manifest_path),
            target_path=str(target_path),
            uv_cache_path=str(uv_cache_path),
            python_install_path=str(tmp_path / "python")
        )
        
        # Mock git commands
        with patch('comfyui_detector.recreator.run_command') as mock_run_command:
            mock_run_command.return_value = None
            
            # Mock the ComfyUI files existing after installation
            with patch('pathlib.Path.exists', return_value=True):
                
                recreator.install_comfyui()
                
                # Verify git checkout was called with branch name
                expected_checkout_call = call(
                    ["git", "checkout", "master"],
                    cwd=target_path / "ComfyUI",
                    check=True,
                    timeout=60
                )
                
                assert expected_checkout_call in mock_run_command.call_args_list
    
    def test_install_comfyui_git_clone_failure(self, tmp_path):
        """Test ComfyUI installation handling git clone failure."""
        # Create valid manifest
        manifest_data = {
            "schema_version": "1.0",
            "system_info": {
                "python_version": "3.11.7",
                "cuda_version": None,
                "torch_version": "2.1.0+cpu",
                "comfyui_version": "v0.3.47"
            },
            "custom_nodes": [],
            "dependencies": {"packages": {}}
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))
        
        target_path = tmp_path / "target"
        uv_cache_path = tmp_path / "cache"
        
        recreator = EnvironmentRecreator(
            manifest_path=str(manifest_path),
            target_path=str(target_path),
            uv_cache_path=str(uv_cache_path),
            python_install_path=str(tmp_path / "python")
        )
        
        # Mock git clone to fail
        with patch('comfyui_detector.recreator.run_command') as mock_run_command:
            mock_run_command.side_effect = ComfyUIDetectorError("Failed to clone repository")
            
            with pytest.raises(ValidationError, match="Failed to clone ComfyUI"):
                recreator.install_comfyui()
    
    def test_install_comfyui_git_checkout_failure(self, tmp_path):
        """Test ComfyUI installation handling git checkout failure."""
        # Create valid manifest
        manifest_data = {
            "schema_version": "1.0",
            "system_info": {
                "python_version": "3.11.7",
                "cuda_version": None,
                "torch_version": "2.1.0+cpu",
                "comfyui_version": "invalid-tag"
            },
            "custom_nodes": [],
            "dependencies": {"packages": {}}
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))
        
        target_path = tmp_path / "target"
        uv_cache_path = tmp_path / "cache"
        
        recreator = EnvironmentRecreator(
            manifest_path=str(manifest_path),
            target_path=str(target_path),
            uv_cache_path=str(uv_cache_path),
            python_install_path=str(tmp_path / "python")
        )
        
        # Mock git clone to succeed but checkout to fail
        with patch('comfyui_detector.common.run_command') as mock_run_command:
            def run_command_side_effect(cmd, **kwargs):
                if "clone" in cmd:
                    return None  # Clone succeeds
                elif "checkout" in cmd:
                    raise ComfyUIDetectorError("Failed to checkout version")  # Checkout fails
                return None
            
            mock_run_command.side_effect = run_command_side_effect
            
            with pytest.raises(ValidationError, match="Failed to checkout ComfyUI version"):
                recreator.install_comfyui()
    
    def test_install_comfyui_validates_installation(self, tmp_path):
        """Test ComfyUI installation validates structure after installation."""
        # Create valid manifest
        manifest_data = {
            "schema_version": "1.0",
            "system_info": {
                "python_version": "3.11.7",
                "cuda_version": None,
                "torch_version": "2.1.0+cpu",
                "comfyui_version": "v0.3.47"
            },
            "custom_nodes": [],
            "dependencies": {"packages": {}}
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))
        
        target_path = tmp_path / "target"
        uv_cache_path = tmp_path / "cache"
        
        recreator = EnvironmentRecreator(
            manifest_path=str(manifest_path),
            target_path=str(target_path),
            uv_cache_path=str(uv_cache_path),
            python_install_path=str(tmp_path / "python")
        )
        
        # Mock git commands to succeed
        with patch('comfyui_detector.recreator.run_command') as mock_run_command:
            mock_run_command.return_value = None
            
            # Mock missing ComfyUI files (installation validation should fail)
            with patch('pathlib.Path.exists') as mock_exists:
                mock_exists.return_value = False  # No files exist
                
                with pytest.raises(ValidationError, match="ComfyUI installation validation failed"):
                    recreator.install_comfyui()
    
    def test_install_comfyui_creates_directory_structure(self, tmp_path):
        """Test ComfyUI installation creates directory structure if needed."""
        # Create valid manifest
        manifest_data = {
            "schema_version": "1.0",
            "system_info": {
                "python_version": "3.11.7",
                "cuda_version": None,
                "torch_version": "2.1.0+cpu",
                "comfyui_version": "v0.3.47"
            },
            "custom_nodes": [],
            "dependencies": {"packages": {}}
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))
        
        target_path = tmp_path / "target"
        uv_cache_path = tmp_path / "cache"
        
        recreator = EnvironmentRecreator(
            manifest_path=str(manifest_path),
            target_path=str(target_path),
            uv_cache_path=str(uv_cache_path),
            python_install_path=str(tmp_path / "python")
        )
        
        # Mock git commands
        with patch('comfyui_detector.recreator.run_command') as mock_run_command:
            mock_run_command.return_value = None
            
            # Mock the ComfyUI files existing after installation
            with patch('pathlib.Path.exists', return_value=True):
                
                # Mock create_directory_structure method to verify it's called
                with patch.object(recreator, 'create_directory_structure') as mock_create_dirs:
                    recreator.install_comfyui()
                    
                    # Verify directory structure is created first
                    mock_create_dirs.assert_called_once()
    
    def test_install_comfyui_missing_comfyui_version(self, tmp_path):
        """Test ComfyUI installation with missing version in manifest."""
        # Create manifest without comfyui_version
        manifest_data = {
            "schema_version": "1.0",
            "system_info": {
                "python_version": "3.11.7",
                "cuda_version": None,
                "torch_version": "2.1.0+cpu",
                "comfyui_version": ""  # Empty version
            },
            "custom_nodes": [],
            "dependencies": {"packages": {}}
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))
        
        target_path = tmp_path / "target"
        uv_cache_path = tmp_path / "cache"
        
        recreator = EnvironmentRecreator(
            manifest_path=str(manifest_path),
            target_path=str(target_path),
            uv_cache_path=str(uv_cache_path),
            python_install_path=str(tmp_path / "python")
        )
        
        with pytest.raises(ValidationError, match="Invalid ComfyUI version"):
            recreator.install_comfyui()