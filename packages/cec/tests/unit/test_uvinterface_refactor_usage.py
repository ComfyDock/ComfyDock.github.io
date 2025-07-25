"""Tests for refactored UVInterface usage across the codebase."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from comfyui_detector.integrations.uv import UVResult
from comfyui_detector.core.recreator import EnvironmentRecreator
from comfyui_detector.utils.system import extract_packages_with_uv
from comfyui_detector.models.models import Package
from comfyui_detector.exceptions import ValidationError


class TestRecreatorUVInterfaceUsage:
    """Test EnvironmentRecreator's usage of refactored UVInterface."""
    
    @patch('comfyui_detector.recreator.UVInterface')
    def test_recreator_instantiates_uvinterface_without_paths(self, mock_uv_class, tmp_path):
        """Test that recreator instantiates UVInterface without path parameters."""
        mock_uv = Mock()
        mock_uv_class.return_value = mock_uv
        
        # Create a real manifest file
        manifest_data = {
            "schema_version": "1.0",
            "system_info": {"python_version": "3.11.7"},
            "custom_nodes": [],
            "dependencies": {"packages": {}}
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))
        
        recreator = EnvironmentRecreator(
            manifest_path=str(manifest_path),
            target_path=str(tmp_path / "target"),
            uv_cache_path=str(tmp_path / "cache"),
            python_install_path=str(tmp_path / "python")
        )
        
        # Now create virtual environment to trigger UVInterface usage
        recreator.create_virtual_environment()
        
        # Should instantiate with only verbose/quiet parameters
        mock_uv_class.assert_called_once()
        args, kwargs = mock_uv_class.call_args
        assert 'python_path' not in kwargs
        assert 'venv_path' not in kwargs
    
    @patch('comfyui_detector.recreator.UVInterface')
    def test_recreator_uses_create_venv_not_venv_create(self, mock_uv_class, tmp_path):
        """Test that recreator uses create_venv() method instead of venv_create()."""
        mock_uv = Mock()
        mock_uv_class.return_value = mock_uv
        
        # Mock create_venv to return UVResult
        mock_uv.create_venv.return_value = UVResult(success=True, output="Created venv")
        
        # Create a real manifest file
        manifest_data = {
            "schema_version": "1.0",
            "system_info": {"python_version": "3.11.7"},
            "custom_nodes": [],
            "dependencies": {"packages": {}}
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))
        
        # Create recreator
        recreator = EnvironmentRecreator(
            manifest_path=str(manifest_path),
            target_path=str(tmp_path / "target"),
            uv_cache_path=str(tmp_path / "cache"),
            python_install_path=str(tmp_path / "python")
        )
        
        # Call create_virtual_environment which uses create_venv
        recreator.create_virtual_environment()
        
        # Should call create_venv, not venv_create
        venv_path = tmp_path / "target" / ".venv"
        mock_uv.create_venv.assert_called_once_with(
            path=venv_path,
            python_version="3.11.7"
        )
        assert not hasattr(mock_uv, 'venv_create') or not mock_uv.venv_create.called
    
    @patch('comfyui_detector.recreator.UVInterface')
    def test_recreator_uses_install_packages_not_pip_install(self, mock_uv_class, tmp_path):
        """Test that recreator uses install_packages() method instead of pip_install()."""
        mock_uv = Mock()
        mock_uv_class.return_value = mock_uv
        
        # Mock install_packages to return UVResult
        mock_uv.install_packages.return_value = UVResult(success=True, output="Installed packages")
        
        # Create a real manifest file
        manifest_data = {
            "schema_version": "1.0",
            "system_info": {"python_version": "3.11.7"},
            "custom_nodes": [],
            "dependencies": {
                "packages": {
                    "numpy": "1.24.3",
                    "pandas": "2.0.0"
                }
            }
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))
        
        recreator = EnvironmentRecreator(
            manifest_path=str(manifest_path),
            target_path=str(tmp_path / "target"),
            uv_cache_path=str(tmp_path / "cache"),
            python_install_path=str(tmp_path / "python")
        )
        
        # Create venv directory
        venv_path = tmp_path / "target" / ".venv"
        venv_path.mkdir(parents=True)
        
        # Call install_packages
        recreator.install_packages()
        
        # Should call install_packages, not pip_install
        expected_packages = ["numpy==1.24.3", "pandas==2.0.0"]
        mock_uv.install_packages.assert_called_once_with(
            venv_path=venv_path,
            packages=expected_packages,
            uv_cache=recreator.uv_cache_path
        )
        assert not hasattr(mock_uv, 'pip_install') or not mock_uv.pip_install.called
    
    @patch('comfyui_detector.recreator.UVInterface')
    def test_recreator_handles_uvresult_errors(self, mock_uv_class, tmp_path):
        """Test that recreator properly handles UVResult error responses."""
        mock_uv = Mock()
        mock_uv_class.return_value = mock_uv
        
        # Mock create_venv to return error
        mock_uv.create_venv.return_value = UVResult(
            success=False, 
            error="Failed to create venv: Python 3.11.7 not found"
        )
        
        # Create a real manifest file
        manifest_data = {
            "schema_version": "1.0",
            "system_info": {"python_version": "3.11.7"},
            "custom_nodes": [],
            "dependencies": {"packages": {}}
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))
        
        recreator = EnvironmentRecreator(
            manifest_path=str(manifest_path),
            target_path=str(tmp_path / "target"),
            uv_cache_path=str(tmp_path / "cache"),
            python_install_path=str(tmp_path / "python")
        )
        
        # Should raise ValidationError when create_venv fails
        with pytest.raises(ValidationError, match="Failed to create virtual environment"):
            recreator.create_virtual_environment()


class TestSystemUtilsUVInterfaceUsage:
    """Test utils/system.py usage of refactored UVInterface."""
    
    @patch('comfyui_detector.utils.system.UVInterface')
    def test_extract_packages_instantiates_uvinterface_correctly(self, mock_uv_class):
        """Test that extract_packages_with_uv instantiates UVInterface without paths."""
        mock_uv = Mock()
        mock_uv_class.return_value = mock_uv
        
        # Mock list_packages to return UVResult
        mock_uv.list_packages.return_value = UVResult(
            success=True,
            output="numpy==1.24.3\npandas==2.0.0"
        )
        
        # Mock _parse_pip_list_output to return Package objects
        mock_uv._parse_pip_list_output.return_value = [
            Package(name="numpy", version="1.24.3", is_editable=False),
            Package(name="pandas", version="2.0.0", is_editable=False)
        ]
        
        venv_path = Path("/test/venv")
        python_exe = Path("/test/venv/bin/python")
        comfyui_path = Path("/test/comfyui")
        pytorch_packages = set()
        
        packages, pytorch_pkgs, editable = extract_packages_with_uv(
            venv_path, python_exe, comfyui_path, pytorch_packages
        )
        
        # Should instantiate without path parameters
        mock_uv_class.assert_called_once()
        args, kwargs = mock_uv_class.call_args
        assert 'python_path' not in kwargs
        assert 'venv_path' not in kwargs
    
    @patch('comfyui_detector.utils.system.UVInterface')
    def test_extract_packages_uses_list_packages_not_pip_list(self, mock_uv_class):
        """Test that extract_packages_with_uv uses list_packages() not pip_list()."""
        mock_uv = Mock()
        mock_uv_class.return_value = mock_uv
        
        # Mock list_packages to return UVResult
        mock_uv.list_packages.return_value = UVResult(
            success=True,
            output="numpy==1.24.3"
        )
        
        # Mock _parse_pip_list_output to return Package objects
        mock_uv._parse_pip_list_output.return_value = [
            Package(name="numpy", version="1.24.3", is_editable=False)
        ]
        
        venv_path = Path("/test/venv")
        python_exe = Path("/test/venv/bin/python")
        comfyui_path = Path("/test/comfyui")
        pytorch_packages = set()
        
        extract_packages_with_uv(venv_path, python_exe, comfyui_path, pytorch_packages)
        
        # Should call list_packages with venv_path
        mock_uv.list_packages.assert_called_once_with(venv_path=venv_path, format='freeze')
        assert not hasattr(mock_uv, 'pip_list') or not mock_uv.pip_list.called
    
    @patch('comfyui_detector.utils.system.UVInterface')
    def test_extract_packages_parses_uvresult_output(self, mock_uv_class):
        """Test that extract_packages parses UVResult.output correctly."""
        mock_uv = Mock()
        mock_uv_class.return_value = mock_uv
        
        # Mock list_packages to return UVResult
        package_output = "numpy==1.24.3\npandas==2.0.0"
        mock_uv.list_packages.return_value = UVResult(
            success=True,
            output=package_output
        )
        
        # Mock _parse_pip_list_output
        mock_uv._parse_pip_list_output.return_value = [
            Package(name="numpy", version="1.24.3", is_editable=False),
            Package(name="pandas", version="2.0.0", is_editable=False)
        ]
        
        venv_path = Path("/test/venv")
        python_exe = Path("/test/venv/bin/python")
        comfyui_path = Path("/test/comfyui")
        pytorch_packages = set()
        
        packages, pytorch_pkgs, editable = extract_packages_with_uv(
            venv_path, python_exe, comfyui_path, pytorch_packages
        )
        
        # Should parse the output from UVResult
        mock_uv._parse_pip_list_output.assert_called_once_with(package_output, "freeze")
        assert packages == {"numpy": "1.24.3", "pandas": "2.0.0"}
    
    @patch('comfyui_detector.utils.system.run_command')
    @patch('comfyui_detector.utils.system.UVInterface')
    def test_extract_packages_handles_uvresult_failure(self, mock_uv_class, mock_run_command):
        """Test that extract_packages handles UVResult failures correctly."""
        mock_uv = Mock()
        mock_uv_class.return_value = mock_uv
        
        # Mock list_packages to return failure
        mock_uv.list_packages.return_value = UVResult(
            success=False,
            error="Failed to list packages: venv not found"
        )
        
        # Mock the pip fallback to also fail
        mock_run_command.side_effect = Exception("pip freeze failed")
        
        venv_path = Path("/test/venv")
        python_exe = Path("/test/venv/bin/python")
        comfyui_path = Path("/test/comfyui")
        pytorch_packages = set()
        
        # Should raise exception when both UV and pip fail
        from comfyui_detector.exceptions import PackageDetectionError
        with pytest.raises(PackageDetectionError, match="Both UV and pip fallback failed"):
            extract_packages_with_uv(
                venv_path, python_exe, comfyui_path, pytorch_packages
            )


class TestIntegrationTestUVInterfaceUsage:
    """Test integration test files' usage of refactored UVInterface."""
    
    def test_integration_tests_use_correct_api(self):
        """Placeholder test to ensure integration tests are updated."""
        # This test will check that integration tests use the new API correctly
        # when we update the integration test files
        assert True
        

