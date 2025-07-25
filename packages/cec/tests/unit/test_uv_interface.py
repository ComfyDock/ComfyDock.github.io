"""Tests for UV interface module."""

import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch

from comfyui_detector.integrations.uv import UVInterface
from comfyui_detector.exceptions import UVNotInstalledError, UVCommandError


def create_mock_result(returncode: int, stdout: str, stderr: str = "") -> subprocess.CompletedProcess:
    """Helper to create mock subprocess.CompletedProcess objects."""
    result = subprocess.CompletedProcess([], returncode)
    result.stdout = stdout
    result.stderr = stderr
    return result


class TestUVInterface:
    """Test the UVInterface class."""
    
    def test_init_success(self):
        """Test successful initialization with UV installed."""
        with patch('shutil.which', return_value='/usr/bin/uv'):
            uv = UVInterface()
            assert uv._uv_binary == '/usr/bin/uv'
            assert uv.verbose is False
            assert uv.quiet is False
    
    def test_init_with_flags(self):
        """Test initialization with verbose and quiet flags."""
        with patch('shutil.which', return_value='/usr/bin/uv'):
            uv = UVInterface(verbose=True, quiet=True)
            assert uv.verbose is True
            assert uv.quiet is True
    
    def test_init_uv_not_installed(self):
        """Test initialization fails when UV is not installed."""
        with patch('shutil.which', return_value=None):
            with pytest.raises(UVNotInstalledError) as exc_info:
                UVInterface()
            assert "uv is not installed" in str(exc_info.value)
    
    def test_get_uv_version_success(self):
        """Test successful UV version retrieval."""
        mock_result = create_mock_result(0, "uv 0.1.45")
        
        with patch('shutil.which', return_value='/usr/bin/uv'):
            with patch('comfyui_detector.integrations.uv.run_command', return_value=mock_result):
                uv = UVInterface()
                version = uv.get_uv_version()
                assert version == "0.1.45"
    
    def test_get_uv_version_failure(self):
        """Test UV version retrieval failure."""
        mock_result = create_mock_result(1, "", "command not found")
        
        with patch('shutil.which', return_value='/usr/bin/uv'):
            with patch('comfyui_detector.integrations.uv.run_command', return_value=mock_result):
                uv = UVInterface()
                with pytest.raises(UVCommandError):
                    uv.get_uv_version()
    
    def test_list_packages_success(self):
        """Test successful package listing."""
        mock_result = create_mock_result(0, "package1==1.0.0\npackage2==2.0.0")
        venv_path = Path('/path/to/venv')
        
        with patch('shutil.which', return_value='/usr/bin/uv'):
            with patch('comfyui_detector.integrations.uv.run_command', return_value=mock_result) as mock_run:
                uv = UVInterface()
                result = uv.list_packages(venv_path, format="freeze")
                
                assert result.success is True
                assert result.output == "package1==1.0.0\npackage2==2.0.0"
                assert result.error is None
                
                # Verify command construction
                args, kwargs = mock_run.call_args
                cmd = args[0]
                assert 'uv' in cmd
                assert 'pip' in cmd
                assert 'list' in cmd
                assert '--format' in cmd
                assert 'freeze' in cmd
                assert '--python' in cmd
                # Check that the python path is passed correctly
                # Since the path doesn't exist, it will fall back to Windows path
                python_idx = cmd.index('--python')
                python_path = cmd[python_idx + 1]
                assert python_path in [
                    str(venv_path / "bin" / "python"),
                    str(venv_path / "Scripts" / "python.exe")
                ]
                
                # Verify environment
                assert 'env' in kwargs
                assert kwargs['env']['VIRTUAL_ENV'] == str(venv_path)
    
    def test_list_packages_failure(self):
        """Test package listing failure."""
        mock_result = create_mock_result(1, "", "permission denied")
        venv_path = Path('/path/to/venv')
        
        with patch('shutil.which', return_value='/usr/bin/uv'):
            with patch('comfyui_detector.integrations.uv.run_command', return_value=mock_result):
                uv = UVInterface()
                result = uv.list_packages(venv_path)
                
                assert result.success is False
                assert result.error == "permission denied"
                assert result.output is None
    
    def test_install_packages_simple(self):
        """Test simple package installation."""
        mock_result = create_mock_result(0, "Successfully installed package1")
        venv_path = Path('/path/to/venv')
        
        with patch('shutil.which', return_value='/usr/bin/uv'):
            with patch('comfyui_detector.integrations.uv.run_command', return_value=mock_result) as mock_run:
                uv = UVInterface()
                result = uv.install_packages(venv_path, ["package1"])
                
                assert result.success is True
                assert result.output == "Successfully installed package1"
                
                # Verify command construction
                args, kwargs = mock_run.call_args
                cmd = args[0]
                assert 'uv' in cmd
                assert 'pip' in cmd
                assert 'install' in cmd
                assert 'package1' in cmd
                assert '--python' in cmd
    
    def test_install_packages_with_options(self):
        """Test package installation with options."""
        mock_result = create_mock_result(0, "Successfully installed packages")
        venv_path = Path('/path/to/venv')
        uv_cache = Path('/path/to/cache')
        
        with patch('shutil.which', return_value='/usr/bin/uv'):
            with patch('comfyui_detector.integrations.uv.run_command', return_value=mock_result) as mock_run:
                uv = UVInterface()
                result = uv.install_packages(
                    venv_path,
                    ["package1", "package2"],
                    upgrade=True,
                    index_url="https://custom.pypi.org/simple/",
                    uv_cache=uv_cache
                )
                
                assert result.success is True
                
                # Verify command construction
                args, kwargs = mock_run.call_args
                cmd = args[0]
                assert '--upgrade' in cmd
                assert '--index-url' in cmd
                assert 'https://custom.pypi.org/simple/' in cmd
                assert 'package1' in cmd
                assert 'package2' in cmd
                
                # Verify environment
                assert kwargs['env']['UV_CACHE_DIR'] == str(uv_cache)
    
    def test_create_venv_success(self):
        """Test virtual environment creation."""
        mock_result = create_mock_result(0, "Created virtual environment")
        venv_path = Path('/path/to/venv')
        
        with patch('shutil.which', return_value='/usr/bin/uv'):
            with patch('comfyui_detector.integrations.uv.run_command', return_value=mock_result) as mock_run:
                uv = UVInterface()
                result = uv.create_venv(venv_path, python_version="3.11")
                
                assert result.success is True
                assert result.output == "Created virtual environment"
                
                # Verify command construction
                args, _ = mock_run.call_args
                cmd = args[0]
                assert 'uv' in cmd
                assert 'venv' in cmd
                assert str(venv_path) in cmd
                assert '--python' in cmd
                assert '3.11' in cmd
    
    def test_create_venv_with_options(self):
        """Test virtual environment creation with options."""
        mock_result = create_mock_result(0, "Created virtual environment")
        venv_path = Path('/path/to/venv')
        
        with patch('shutil.which', return_value='/usr/bin/uv'):
            with patch('comfyui_detector.integrations.uv.run_command', return_value=mock_result) as mock_run:
                uv = UVInterface()
                result = uv.create_venv(
                    venv_path,
                    system_site_packages=True,
                    seed=True
                )
                
                assert result.success is True
                
                # Verify command construction
                args, _ = mock_run.call_args
                cmd = args[0]
                assert '--system-site-packages' in cmd
                assert '--seed' in cmd
    
    def test_run_python_success(self):
        """Test running Python code."""
        mock_result = create_mock_result(0, "Hello World")
        venv_path = Path('/path/to/venv')
        
        with patch('shutil.which', return_value='/usr/bin/uv'):
            with patch('comfyui_detector.integrations.uv.run_command', return_value=mock_result) as mock_run:
                uv = UVInterface()
                result = uv.run_python(venv_path, "print('Hello World')")
                
                assert result.success is True
                assert result.output == "Hello World"
                
                # Verify command construction
                args, kwargs = mock_run.call_args
                cmd = args[0]
                assert 'uv' in cmd
                assert 'run' in cmd
                assert 'python' in cmd
                assert '-c' in cmd
                assert "print('Hello World')" in cmd
                
                # Verify environment
                assert kwargs['env']['VIRTUAL_ENV'] == str(venv_path)
    
    def test_install_requirements_success(self):
        """Test installing from requirements file."""
        mock_result = create_mock_result(0, "Successfully installed requirements")
        venv_path = Path('/path/to/venv')
        requirements_file = Path('/path/to/requirements.txt')
        
        with patch('shutil.which', return_value='/usr/bin/uv'):
            with patch('comfyui_detector.integrations.uv.run_command', return_value=mock_result) as mock_run:
                uv = UVInterface()
                result = uv.install_requirements(venv_path, requirements_file)
                
                assert result.success is True
                assert result.output == "Successfully installed requirements"
                
                # Verify command construction
                args, kwargs = mock_run.call_args
                cmd = args[0]
                assert 'uv' in cmd
                assert 'pip' in cmd
                assert 'install' in cmd
                assert '-r' in cmd
                assert str(requirements_file) in cmd
                assert '--python' in cmd
                
                # Verify timeout
                assert kwargs['timeout'] == 300
    
    def test_uninstall_packages_success(self):
        """Test package uninstallation."""
        mock_result = create_mock_result(0, "Successfully uninstalled package1")
        venv_path = Path('/path/to/venv')
        
        with patch('shutil.which', return_value='/usr/bin/uv'):
            with patch('comfyui_detector.integrations.uv.run_command', return_value=mock_result) as mock_run:
                uv = UVInterface()
                result = uv.uninstall_packages(venv_path, ["package1"])
                
                assert result.success is True
                assert result.output == "Successfully uninstalled package1"
                
                # Verify command construction
                args, kwargs = mock_run.call_args
                cmd = args[0]
                assert 'uv' in cmd
                assert 'pip' in cmd
                assert 'uninstall' in cmd
                assert 'package1' in cmd
                assert '--python' in cmd
                
                # Verify cwd
                assert kwargs['cwd'] == venv_path.parent
    
    def test_freeze_packages_success(self):
        """Test freezing packages."""
        mock_result = create_mock_result(0, "package1==1.0.0\npackage2==2.0.0")
        venv_path = Path('/path/to/venv')
        
        with patch('shutil.which', return_value='/usr/bin/uv'):
            with patch('comfyui_detector.integrations.uv.run_command', return_value=mock_result) as mock_run:
                uv = UVInterface()
                result = uv.freeze_packages(venv_path, all_packages=True)
                
                assert result.success is True
                assert "package1==1.0.0" in result.output
                assert "package2==2.0.0" in result.output
                
                # Verify command construction
                args, _ = mock_run.call_args
                cmd = args[0]
                assert 'uv' in cmd
                assert 'pip' in cmd
                assert 'freeze' in cmd
                assert '--all' in cmd
                assert '--python' in cmd
    
    def test_generate_lockfile_success(self):
        """Test lockfile generation."""
        mock_result = create_mock_result(0, "Lockfile generated")
        project_path = Path('/path/to/project')
        
        with patch('shutil.which', return_value='/usr/bin/uv'):
            with patch('comfyui_detector.integrations.uv.run_command', return_value=mock_result) as mock_run:
                uv = UVInterface()
                result = uv.generate_lockfile(
                    project_path,
                    upgrade=True,
                    upgrade_packages=["package1", "package2"]
                )
                
                assert result.success is True
                assert result.output == "Lockfile generated"
                
                # Verify command construction
                args, kwargs = mock_run.call_args
                cmd = args[0]
                assert 'uv' in cmd
                assert 'lock' in cmd
                assert '--upgrade' in cmd
                assert '--upgrade-package' in cmd
                assert 'package1' in cmd
                assert 'package2' in cmd
                
                # Verify cwd
                assert kwargs['cwd'] == project_path
    
    def test_sync_environment_success(self):
        """Test environment syncing."""
        mock_result = create_mock_result(0, "Environment synced")
        project_path = Path('/path/to/project')
        
        with patch('shutil.which', return_value='/usr/bin/uv'):
            with patch('comfyui_detector.integrations.uv.run_command', return_value=mock_result) as mock_run:
                uv = UVInterface()
                result = uv.sync_environment(project_path)
                
                assert result.success is True
                assert result.output == "Environment synced"
                
                # Verify command construction
                args, kwargs = mock_run.call_args
                cmd = args[0]
                assert 'uv' in cmd
                assert 'sync' in cmd
                
                # Verify cwd
                assert kwargs['cwd'] == project_path
    
    def test_parse_pip_list_output_freeze_format(self):
        """Test parsing pip list output in freeze format."""
        output = """package1==1.0.0
package2==2.0.0
-e /path/to/editable
# This is a comment
package3==3.0.0"""
        
        with patch('shutil.which', return_value='/usr/bin/uv'):
            uv = UVInterface()
            packages = uv._parse_pip_list_output(output, "freeze")
            
            assert len(packages) == 4
            
            assert packages[0].name == "package1"
            assert packages[0].version == "1.0.0"
            assert packages[0].is_editable is False
            
            assert packages[1].name == "package2"
            assert packages[1].version == "2.0.0"
            assert packages[1].is_editable is False
            
            assert packages[2].name == "editable"
            assert packages[2].version == "editable"
            assert packages[2].is_editable is True
            
            assert packages[3].name == "package3"
            assert packages[3].version == "3.0.0"
            assert packages[3].is_editable is False
    
    def test_extract_editable_name(self):
        """Test extracting package name from editable install line."""
        with patch('shutil.which', return_value='/usr/bin/uv'):
            uv = UVInterface()
            
            # Test with egg name
            name = uv._extract_editable_name("-e git+https://github.com/user/repo.git#egg=mypackage")
            assert name == "mypackage"
            
            # Test with path
            name = uv._extract_editable_name("-e /path/to/myproject")
            assert name == "myproject"
            
            # Test with simple string
            name = uv._extract_editable_name("-e somepackage")
            assert name == "somepackage"
    
    def test_install_packages_with_prerelease(self):
        """Test package installation with prerelease flag."""
        mock_result = create_mock_result(0, "Successfully installed package1")
        venv_path = Path('/path/to/venv')
        
        with patch('shutil.which', return_value='/usr/bin/uv'):
            with patch('comfyui_detector.integrations.uv.run_command', return_value=mock_result) as mock_run:
                uv = UVInterface()
                result = uv.install_packages(
                    venv_path, 
                    ["package1==1.0.0.dev0"], 
                    prerelease=True
                )
                
                assert result.success is True
                assert result.output == "Successfully installed package1"
                
                # Verify command construction includes prerelease flag
                args, kwargs = mock_run.call_args
                cmd = args[0]
                assert '/usr/bin/uv' in cmd or 'uv' in cmd  # Handle full path
                assert 'pip' in cmd
                assert 'install' in cmd
                assert '--prerelease=allow' in cmd
                assert 'package1==1.0.0.dev0' in cmd
                assert '--python' in cmd
                
                # Verify environment
                assert 'env' in kwargs
                assert kwargs['env']['VIRTUAL_ENV'] == str(venv_path)
    
    def test_install_packages_without_prerelease(self):
        """Test package installation without prerelease flag (default behavior)."""
        mock_result = create_mock_result(0, "Successfully installed package1")
        venv_path = Path('/path/to/venv')
        
        with patch('shutil.which', return_value='/usr/bin/uv'):
            with patch('comfyui_detector.integrations.uv.run_command', return_value=mock_result) as mock_run:
                uv = UVInterface()
                result = uv.install_packages(venv_path, ["package1==1.0.0"])
                
                assert result.success is True
                
                # Verify command construction does NOT include prerelease flag
                args, _ = mock_run.call_args
                cmd = args[0]
                assert '--prerelease=allow' not in cmd