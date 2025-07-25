"""Tests for EnvironmentRecreator API alignment with PRD specifications."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, Mock

from comfyui_detector.core.recreator import EnvironmentRecreator
from comfyui_detector.models import EnvironmentResult


class TestEnvironmentRecreatorAPIAlignment:
    """Test cases for PRD API alignment requirements."""
    
    @pytest.fixture
    def valid_manifest_data(self):
        """Provides valid manifest data for testing."""
        return {
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
    
    @pytest.fixture
    def manifest_file(self, tmp_path, valid_manifest_data):
        """Creates a temporary manifest file."""
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(valid_manifest_data))
        return manifest_path
    
    def test_constructor_accepts_python_install_path_parameter(self, manifest_file, tmp_path):
        """Test that constructor accepts python_install_path parameter as per PRD."""
        target_path = tmp_path / "target"
        uv_cache_path = tmp_path / "cache"
        python_install_path = tmp_path / "python"
        
        # This should work with the new API
        recreator = EnvironmentRecreator(
            manifest_path=manifest_file,
            target_path=target_path,
            uv_cache_path=uv_cache_path,
            python_install_path=python_install_path
        )
        
        assert recreator.python_install_path == python_install_path
    
    def test_constructor_stores_python_install_path_correctly(self, manifest_file, tmp_path):
        """Test that python_install_path is stored as Path object."""
        target_path = tmp_path / "target"
        uv_cache_path = tmp_path / "cache"
        python_install_path = tmp_path / "python"
        
        recreator = EnvironmentRecreator(
            manifest_path=str(manifest_file),  # string input
            target_path=str(target_path),      # string input
            uv_cache_path=str(uv_cache_path),  # string input
            python_install_path=str(python_install_path)  # string input
        )
        
        # Should be converted to Path objects
        assert isinstance(recreator.python_install_path, Path)
        assert recreator.python_install_path == Path(python_install_path)
    
    def test_recreate_method_exists_and_returns_environment_result(self, manifest_file, tmp_path):
        """Test that recreate() method exists and returns EnvironmentResult."""
        target_path = tmp_path / "target"
        uv_cache_path = tmp_path / "cache"
        python_install_path = tmp_path / "python"
        
        recreator = EnvironmentRecreator(
            manifest_path=manifest_file,
            target_path=target_path,
            uv_cache_path=uv_cache_path,
            python_install_path=python_install_path
        )
        
        # Mock all the internal methods that recreate() will call
        with patch.object(recreator, 'validate_manifest') as mock_validate, \
             patch.object(recreator, 'create_directory_structure') as mock_create_dirs, \
             patch.object(recreator, 'create_virtual_environment') as mock_create_venv, \
             patch.object(recreator, 'install_comfyui') as mock_install_comfyui, \
             patch.object(recreator, 'install_packages_from_manifest') as mock_install_packages, \
             patch.object(recreator, 'validate_environment') as mock_validate_env:
            
            # Configure mocks
            mock_validate_env.return_value = ({}, [])  # (installed_packages, installed_nodes)
            
            # Call recreate method
            result = recreator.recreate()
            
            # Verify return type
            assert isinstance(result, EnvironmentResult)
            
            # Verify all steps were called in order
            mock_validate.assert_called_once()
            mock_create_dirs.assert_called_once()
            mock_create_venv.assert_called_once()
            mock_install_comfyui.assert_called_once()
            mock_install_packages.assert_called_once()
            mock_validate_env.assert_called_once()
    
    def test_recreate_method_has_correct_signature(self, manifest_file, tmp_path):
        """Test that recreate() method has the correct signature as per PRD."""
        target_path = tmp_path / "target"
        uv_cache_path = tmp_path / "cache"
        python_install_path = tmp_path / "python"
        
        recreator = EnvironmentRecreator(
            manifest_path=manifest_file,
            target_path=target_path,
            uv_cache_path=uv_cache_path,
            python_install_path=python_install_path
        )
        
        # Check that method exists and is callable
        assert hasattr(recreator, 'recreate')
        assert callable(getattr(recreator, 'recreate'))
        
        # Check method signature (no parameters, returns EnvironmentResult)
        import inspect
        sig = inspect.signature(recreator.recreate)
        assert len(sig.parameters) == 0  # No parameters besides self
        assert sig.return_annotation == EnvironmentResult
    
    def test_recreate_populates_environment_result_correctly(self, manifest_file, tmp_path):
        """Test that recreate() populates EnvironmentResult with correct data."""
        target_path = tmp_path / "target"
        uv_cache_path = tmp_path / "cache"
        python_install_path = tmp_path / "python"
        
        recreator = EnvironmentRecreator(
            manifest_path=manifest_file,
            target_path=target_path,
            uv_cache_path=uv_cache_path,
            python_install_path=python_install_path
        )
        
        # Mock internal methods with specific return values
        mock_installed_packages = {"torch": "2.1.0", "numpy": "1.24.3"}
        mock_installed_nodes = ["test_node"]
        
        with patch.object(recreator, 'validate_manifest'), \
             patch.object(recreator, 'create_directory_structure'), \
             patch.object(recreator, 'create_virtual_environment'), \
             patch.object(recreator, 'install_comfyui'), \
             patch.object(recreator, 'install_packages_from_manifest'), \
             patch.object(recreator, 'get_installed_packages') as mock_get_packages, \
             patch.object(recreator, 'validate_environment') as mock_validate_env:
            
            # Mock the methods that collect installed packages and nodes
            mock_get_packages.return_value = mock_installed_packages
            mock_validate_env.return_value = ([], [])  # (warnings, errors)
            
            # Mock the custom nodes directory to contain our test node
            with patch('pathlib.Path.exists') as mock_exists, \
                 patch('pathlib.Path.iterdir') as mock_iterdir:
                
                # Mock custom_nodes directory exists
                mock_exists.return_value = True
                
                # Mock directory listing to return our test node
                mock_node_dir = Mock()
                mock_node_dir.is_dir.return_value = True
                mock_node_dir.name = "test_node"
                mock_iterdir.return_value = [mock_node_dir]
                
                result = recreator.recreate()
                
                # Verify EnvironmentResult is populated correctly
                assert result.success is True
                assert result.environment_path == target_path
                assert result.venv_path == target_path / ".venv"
                assert result.comfyui_path == target_path / "ComfyUI"
                assert result.installed_packages == mock_installed_packages
                assert result.installed_nodes == mock_installed_nodes
                assert isinstance(result.duration_seconds, float)
                assert result.duration_seconds >= 0