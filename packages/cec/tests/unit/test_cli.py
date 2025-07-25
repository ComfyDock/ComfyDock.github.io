"""Unit tests for CLI commands."""

import json
from unittest.mock import Mock, patch
import pytest
from comfyui_detector.models.models import EnvironmentResult


class TestCLIRecreateCommand:
    """Test cases for the recreate CLI command."""
    
    def test_recreate_command_help(self, capsys):
        """Test that recreate command shows help text."""
        with patch('sys.argv', ['cec', 'recreate', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                from comfyui_detector.cli import main
                main()
            
            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            assert 'recreate' in captured.out
            assert 'manifest_path' in captured.out
            assert 'target_path' in captured.out
    
    def test_recreate_missing_arguments(self, capsys):
        """Test that recreate command requires both arguments."""
        with patch('sys.argv', ['cec', 'recreate']):
            with pytest.raises(SystemExit) as exc_info:
                from comfyui_detector.cli import main
                main()
            
            assert exc_info.value.code == 2
            captured = capsys.readouterr()
            assert 'required' in captured.err
    
    def test_recreate_manifest_not_found(self, capsys):
        """Test error when manifest file doesn't exist."""
        with patch('sys.argv', ['cec', 'recreate', '/nonexistent/manifest.json', '/target']):
            with patch('pathlib.Path.exists', return_value=False):
                with pytest.raises(SystemExit) as exc_info:
                    from comfyui_detector.cli import main
                    main()
                
                assert exc_info.value.code == 1
                captured = capsys.readouterr()
                assert 'Manifest file not found' in captured.err
    
    def test_recreate_invalid_manifest_json(self, capsys, tmp_path):
        """Test error when manifest contains invalid JSON."""
        manifest_path = tmp_path / "invalid.json"
        manifest_path.write_text("invalid json content")
        
        with patch('sys.argv', ['cec', 'recreate', str(manifest_path), str(tmp_path / 'target')]):
            with pytest.raises(SystemExit) as exc_info:
                from comfyui_detector.cli import main
                main()
            
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert 'Invalid JSON' in captured.err or 'Failed to parse' in captured.err
    
    def test_recreate_target_already_exists_nonempty(self, capsys, tmp_path):
        """Test error when target directory exists and is not empty."""
        manifest_path = tmp_path / "manifest.json"
        manifest_data = {
            "schema_version": "1.0",
            "system_info": {
                "python_version": "3.11.7",
                "comfyui_version": "v1.0.0"
            },
            "dependencies": {
                "packages": {}
            },
            "custom_nodes": []
        }
        manifest_path.write_text(json.dumps(manifest_data))
        
        target_path = tmp_path / "target"
        target_path.mkdir()
        (target_path / "existing_file.txt").write_text("content")
        
        with patch('sys.argv', ['cec', 'recreate', str(manifest_path), str(target_path)]):
            with pytest.raises(SystemExit) as exc_info:
                from comfyui_detector.cli import main
                main()
            
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert 'already exists' in captured.err or 'not empty' in captured.err
    
    @patch('comfyui_detector.cli.EnvironmentRecreator')
    def test_recreate_successful(self, mock_recreator_class, capsys, tmp_path):
        """Test successful recreation."""
        # Setup paths
        manifest_path = tmp_path / "manifest.json"
        manifest_data = {
            "schema_version": "1.0",
            "system_info": {
                "python_version": "3.11.7",
                "comfyui_version": "v1.0.0"
            },
            "dependencies": {
                "packages": {}
            },
            "custom_nodes": []
        }
        manifest_path.write_text(json.dumps(manifest_data))
        
        target_path = tmp_path / "target"
        
        # Mock recreator
        mock_recreator = Mock()
        mock_result = EnvironmentResult(
            success=True,
            environment_path=target_path,
            venv_path=target_path / ".venv",
            comfyui_path=target_path / "ComfyUI",
            installed_packages={"numpy": "1.24.0"},
            installed_nodes=["ComfyUI-Manager"],
            warnings=[],
            errors=[],
            duration_seconds=30.5
        )
        mock_recreator.recreate.return_value = mock_result
        mock_recreator_class.return_value = mock_recreator
        
        with patch('sys.argv', ['cec', 'recreate', str(manifest_path), str(target_path)]):
            with pytest.raises(SystemExit) as exc_info:
                from comfyui_detector.cli import main
                main()
            
            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            assert 'Successfully recreated' in captured.out or 'Environment ready' in captured.out
            assert str(target_path) in captured.out
    
    @patch('comfyui_detector.cli.EnvironmentRecreator')  
    def test_recreate_with_optional_paths(self, mock_recreator_class, capsys, tmp_path):
        """Test recreation with optional uv-cache and python-install paths."""
        manifest_path = tmp_path / "manifest.json"
        manifest_data = {
            "schema_version": "1.0",
            "system_info": {
                "python_version": "3.11.7",
                "comfyui_version": "v1.0.0"
            },
            "dependencies": {
                "packages": {}
            },
            "custom_nodes": []
        }
        manifest_path.write_text(json.dumps(manifest_data))
        
        target_path = tmp_path / "target"
        uv_cache = tmp_path / "uv_cache"
        python_install = tmp_path / "python"
        
        mock_recreator = Mock()
        mock_result = EnvironmentResult(
            success=True,
            environment_path=target_path,
            venv_path=target_path / ".venv",
            comfyui_path=target_path / "ComfyUI",
            installed_packages={},
            installed_nodes=[],
            warnings=[],
            errors=[],
            duration_seconds=10.0
        )
        mock_recreator.recreate.return_value = mock_result
        mock_recreator_class.return_value = mock_recreator
        
        with patch('sys.argv', ['cec', 'recreate', str(manifest_path), str(target_path),
                                '--uv-cache-path', str(uv_cache),
                                '--python-install-path', str(python_install)]):
            with pytest.raises(SystemExit) as exc_info:
                from comfyui_detector.cli import main
                main()
            
            assert exc_info.value.code == 0
            
            # Verify recreator was initialized with correct paths
            mock_recreator_class.assert_called_once()
            call_args = mock_recreator_class.call_args
            assert call_args[1]['uv_cache_path'] == uv_cache
            assert call_args[1]['python_install_path'] == python_install
    
    @patch('comfyui_detector.cli.EnvironmentRecreator')
    def test_recreate_failure(self, mock_recreator_class, capsys, tmp_path):
        """Test handling of recreation failure."""
        manifest_path = tmp_path / "manifest.json"
        manifest_data = {
            "schema_version": "1.0",
            "system_info": {
                "python_version": "3.11.7",
                "comfyui_version": "v1.0.0"
            },
            "dependencies": {
                "packages": {}
            },
            "custom_nodes": []
        }
        manifest_path.write_text(json.dumps(manifest_data))
        
        target_path = tmp_path / "target"
        
        # Mock recreator to return failure
        mock_recreator = Mock()
        mock_result = EnvironmentResult(
            success=False,
            environment_path=target_path,
            venv_path=target_path / ".venv", 
            comfyui_path=target_path / "ComfyUI",
            installed_packages={},
            installed_nodes=[],
            warnings=["Some packages failed to install"],
            errors=["Failed to create virtual environment: Python 3.11.7 not available"],
            duration_seconds=5.0
        )
        mock_recreator.recreate.return_value = mock_result
        mock_recreator_class.return_value = mock_recreator
        
        with patch('sys.argv', ['cec', 'recreate', str(manifest_path), str(target_path)]):
            with pytest.raises(SystemExit) as exc_info:
                from comfyui_detector.cli import main
                main()
            
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert 'Failed' in captured.err or 'Error' in captured.err
            assert 'Python 3.11.7 not available' in captured.err
    
    @patch('comfyui_detector.cli.EnvironmentRecreator')
    def test_recreate_with_warnings(self, mock_recreator_class, capsys, tmp_path):
        """Test that warnings are displayed but don't cause failure."""
        manifest_path = tmp_path / "manifest.json"
        manifest_data = {
            "schema_version": "1.0",
            "system_info": {
                "python_version": "3.11.7",
                "comfyui_version": "v1.0.0"
            },
            "dependencies": {
                "packages": {}
            },
            "custom_nodes": []
        }
        manifest_path.write_text(json.dumps(manifest_data))
        
        target_path = tmp_path / "target"
        
        mock_recreator = Mock()
        mock_result = EnvironmentResult(
            success=True,
            environment_path=target_path,
            venv_path=target_path / ".venv",
            comfyui_path=target_path / "ComfyUI",
            installed_packages={},
            installed_nodes=[],
            warnings=["Some custom nodes may require manual configuration"],
            errors=[],
            duration_seconds=15.0
        )
        mock_recreator.recreate.return_value = mock_result
        mock_recreator_class.return_value = mock_recreator
        
        with patch('sys.argv', ['cec', 'recreate', str(manifest_path), str(target_path)]):
            with pytest.raises(SystemExit) as exc_info:
                from comfyui_detector.cli import main  
                main()
            
            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            assert 'Warning' in captured.out or 'manual configuration' in captured.out