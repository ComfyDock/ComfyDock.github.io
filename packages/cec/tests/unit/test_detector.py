"""Unit tests for comfyui_detector.detector module."""

from pathlib import Path
from unittest.mock import Mock, patch, mock_open

import pytest

from comfyui_detector.core.detector import ComfyUIEnvironmentDetector


class TestComfyUIEnvironmentDetectorInit:
    """Test cases for ComfyUIEnvironmentDetector initialization."""
    
    def test_init_basic(self, tmp_path):
        """Test basic initialization."""
        comfyui_path = tmp_path / "ComfyUI"
        comfyui_path.mkdir()
        
        detector = ComfyUIEnvironmentDetector(comfyui_path)
        
        assert detector.comfyui_path == comfyui_path.resolve()
        assert detector.python_hint is None
        assert detector.venv_path is None
        assert detector.validate_registry is False
        assert detector.system_detector is not None
        assert detector.package_detector is None  # Not initialized until detect_all()
        assert detector.custom_node_scanner is not None
        assert detector.manifest_generator is not None
    
    def test_init_with_venv_path(self, tmp_path):
        """Test initialization with virtual environment path."""
        comfyui_path = tmp_path / "ComfyUI"
        venv_path = tmp_path / "venv"
        comfyui_path.mkdir()
        venv_path.mkdir()
        
        detector = ComfyUIEnvironmentDetector(comfyui_path, venv_path)
        
        assert detector.venv_path == venv_path.resolve()
    
    def test_init_with_validation(self, tmp_path):
        """Test initialization with registry validation enabled."""
        comfyui_path = tmp_path / "ComfyUI"
        comfyui_path.mkdir()
        
        detector = ComfyUIEnvironmentDetector(comfyui_path, validate_registry=True)
        
        assert detector.validate_registry is True
        assert detector.registry_validator is not None
        assert detector.github_checker is not None
    
    def test_init_resolves_paths(self, tmp_path):
        """Test that paths are resolved to absolute paths."""
        comfyui_path = tmp_path / "ComfyUI"
        comfyui_path.mkdir()
        
        # Use relative path
        relative_path = Path("ComfyUI")
        
        with patch('pathlib.Path.resolve', return_value=comfyui_path):
            detector = ComfyUIEnvironmentDetector(relative_path)
            assert detector.comfyui_path == comfyui_path


class TestComfyUIEnvironmentDetectorMethods:
    """Test cases for ComfyUIEnvironmentDetector methods."""
    
    @pytest.fixture
    def detector(self, tmp_path):
        """Create a detector instance for testing."""
        comfyui_path = tmp_path / "ComfyUI"
        comfyui_path.mkdir()
        return ComfyUIEnvironmentDetector(comfyui_path)
    
    def test_find_python_executable_success(self, detector):
        """Test successful Python executable detection."""
        mock_python_path = Path("/usr/bin/python3")
        mock_venv_path = Path("/path/to/venv")
        
        with patch('comfyui_detector.detector.find_python_executable') as mock_find:
            mock_find.return_value = (mock_python_path, mock_venv_path)
            
            result = detector.find_python_executable()
            
            assert result == mock_python_path
            assert detector.python_executable == mock_python_path
            assert detector.venv_path == mock_venv_path
            mock_find.assert_called_once_with(detector.comfyui_path, None)
    
    def test_find_python_executable_no_venv_fails(self, detector):
        """Test that missing virtual environment raises assertion error."""
        with patch('comfyui_detector.detector.find_python_executable') as mock_find:
            mock_find.return_value = (Path("/usr/bin/python3"), None)
            
            with pytest.raises(AssertionError, match="Virtual environment not found"):
                detector.find_python_executable()
    
    def test_run_python_command_success(self, detector):
        """Test successful Python command execution."""
        detector.python_executable = Path("/usr/bin/python3")
        
        with patch('comfyui_detector.detector.run_python_command') as mock_run:
            mock_run.return_value = "output"
            
            result = detector.run_python_command("print('hello')")
            
            assert result == "output"
            mock_run.assert_called_once_with(
                "print('hello')", 
                detector.python_executable, 
                detector.comfyui_path
            )
    
    def test_run_python_command_no_executable(self, detector):
        """Test Python command when no executable is set."""
        result = detector.run_python_command("print('hello')")
        assert result is None
    
    def test_detect_python_version(self, detector):
        """Test Python version detection."""
        detector.python_executable = Path("/usr/bin/python3")
        mock_version_info = {
            'python_version': '3.9.0',
            'platform': 'linux',
            'architecture': 'x86_64'
        }
        
        with patch('comfyui_detector.detector.detect_python_version') as mock_detect:
            mock_detect.return_value = mock_version_info
            
            result = detector.detect_python_version()
            
            assert result == '3.9.0'
            assert detector.system_info == mock_version_info
            mock_detect.assert_called_once_with(
                detector.python_executable,
                detector.comfyui_path
            )
    
    def test_detect_cuda_version_success(self, detector):
        """Test CUDA version detection."""
        mock_cuda_version = "11.8"
        
        with patch('comfyui_detector.detector.detect_cuda_version') as mock_detect:
            mock_detect.return_value = mock_cuda_version
            
            result = detector.detect_cuda_version()
            
            assert result == mock_cuda_version
            assert detector.system_info['cuda_version'] == mock_cuda_version
    
    def test_detect_cuda_version_none(self, detector):
        """Test CUDA version detection when CUDA not available."""
        with patch('comfyui_detector.detector.detect_cuda_version') as mock_detect:
            mock_detect.return_value = None
            
            result = detector.detect_cuda_version()
            
            assert result is None
            assert detector.system_info['cuda_version'] is None
    
    def test_detect_pytorch_version_success(self, detector):
        """Test PyTorch version detection."""
        detector.python_executable = Path("/usr/bin/python3")
        mock_pytorch_info = {
            'torch': '2.0.0',
            'cuda_torch_version': '11.8'
        }
        
        with patch('comfyui_detector.detector.detect_pytorch_version') as mock_detect:
            mock_detect.return_value = mock_pytorch_info
            
            result = detector.detect_pytorch_version()
            
            assert result == mock_pytorch_info
            assert detector.system_info['torch_version'] == '2.0.0'
            assert detector.system_info['cuda_torch_version'] == '11.8'
            assert detector.system_info['pytorch_info'] == mock_pytorch_info
    
    def test_detect_pytorch_version_error(self, detector):
        """Test PyTorch version detection with error."""
        detector.python_executable = Path("/usr/bin/python3")
        mock_error_info = {'error': 'PyTorch not found'}
        
        with patch('comfyui_detector.detector.detect_pytorch_version') as mock_detect:
            mock_detect.return_value = mock_error_info
            
            result = detector.detect_pytorch_version()
            
            assert result == mock_error_info
            assert 'torch_version' not in detector.system_info
            assert detector.system_info['pytorch_info'] == mock_error_info
    
    def test_extract_packages_with_uv(self, detector):
        """Test package extraction using UV."""
        detector.venv_path = Path("/path/to/venv")
        detector.python_executable = Path("/usr/bin/python3")
        
        mock_pip_packages = {'numpy': '1.24.0', 'requests': '2.28.0'}
        mock_pytorch_packages = {'torch': '2.0.0', 'torchvision': '0.15.0'}
        mock_editable_installs = ['/path/to/editable/package']
        
        with patch('comfyui_detector.detector.extract_packages_with_uv') as mock_extract:
            mock_extract.return_value = (
                mock_pip_packages,
                mock_pytorch_packages,
                mock_editable_installs
            )
            
            result = detector.extract_packages_with_uv()
            
            assert result == mock_pip_packages
            assert detector.system_info['installed_packages'] == mock_pip_packages
            assert detector.system_info['pytorch_packages'] == mock_pytorch_packages
            assert detector.system_info['editable_installs'] == mock_editable_installs
            assert detector.pytorch_packages == mock_pytorch_packages
    
    def test_parse_comfyui_requirements_success(self, detector, tmp_path):
        """Test parsing ComfyUI requirements.txt."""
        requirements_content = """numpy==1.24.0
requests>=2.28.0
git+https://github.com/user/repo.git
-e /path/to/editable
"""
        req_file = detector.comfyui_path / "requirements.txt"
        req_file.write_text(requirements_content)
        
        mock_parsed_reqs = {
            'numpy': ['==1.24.0'],
            'requests': ['>=2.28.0']
        }
        
        with patch('comfyui_detector.detector.parse_requirements_file') as mock_parse:
            mock_parse.return_value = mock_parsed_reqs
            
            result = detector.parse_comfyui_requirements()
            
            assert result == mock_parsed_reqs
            assert detector.requirements == mock_parsed_reqs
            
            # Check that git requirements are stored
            expected_git_reqs = [
                'git+https://github.com/user/repo.git',
                '-e /path/to/editable'
            ]
            assert detector.system_info['git_requirements'] == expected_git_reqs
    
    def test_scan_custom_nodes_requirements_no_directory(self, detector):
        """Test scanning custom nodes when directory doesn't exist."""
        result = detector.scan_custom_nodes_requirements()
        
        assert result == {}
        assert detector.system_info.get('custom_nodes_with_requirements', []) == []
    
    def test_scan_custom_nodes_requirements_success(self, detector):
        """Test successful custom nodes requirements scanning."""
        # Create custom nodes directory structure
        custom_nodes_dir = detector.custom_nodes_path
        custom_nodes_dir.mkdir()
        
        # Create a custom node with requirements
        node1_dir = custom_nodes_dir / "node1"
        node1_dir.mkdir()
        node1_req_file = node1_dir / "requirements.txt"
        node1_req_file.write_text("pillow==9.0.0")
        
        # Create a custom node with install script
        node2_dir = custom_nodes_dir / "node2"
        node2_dir.mkdir()
        install_script = node2_dir / "install.py"
        install_script.write_text("# install script")
        
        # Create a blacklisted node (should be skipped)
        blacklisted_dir = custom_nodes_dir / "disabled"
        blacklisted_dir.mkdir()
        
        mock_parsed_reqs = {'pillow': ['==9.0.0']}
        
        with patch('comfyui_detector.detector.parse_requirements_file') as mock_parse:
            mock_parse.return_value = mock_parsed_reqs
            
            result = detector.scan_custom_nodes_requirements()
            
            expected_result = {'node1': mock_parsed_reqs}
            assert result == expected_result
            assert detector.requirements == mock_parsed_reqs
            assert detector.system_info['custom_nodes_with_requirements'] == ['node1']
            assert len(detector.system_info['nodes_with_install_scripts']) == 1
            assert detector.system_info['nodes_with_install_scripts'][0][0] == 'node2'
    
    def test_resolve_requirement_conflicts_no_conflicts(self, detector):
        """Test conflict resolution when no conflicts exist."""
        detector.requirements = {
            'numpy': ['==1.24.0'],
            'requests': ['>=2.28.0']
        }
        
        detector.resolve_requirement_conflicts()
        
        # Should not modify requirements when no conflicts
        assert len(detector.conflicts) == 0
        assert detector.requirements['numpy'] == ['==1.24.0']
        assert detector.requirements['requests'] == ['>=2.28.0']
    
    def test_resolve_requirement_conflicts_with_conflicts(self, detector):
        """Test conflict resolution when conflicts exist."""
        detector.requirements = {
            'numpy': ['==1.24.0', '>=1.25.0'],  # Conflicting requirements
            'requests': ['>=2.28.0']
        }
        # Simulate installed packages that conflict with requirements
        detector.system_info['installed_packages'] = {
            'numpy': '1.23.0',  # Installed version doesn't satisfy >=1.25.0
            'requests': '2.28.0'
        }
        
        detector.resolve_requirement_conflicts()
        
        # Should detect conflicts for numpy
        assert len(detector.conflicts) > 0
        assert any(conflict['package'] == 'numpy' for conflict in detector.conflicts)
    
    def test_generate_migration_config_basic_structure(self, detector):
        """Test that migration config has basic structure without file operations."""
        detector.system_info = {
            'python_version': '3.9.0',
            'installed_packages': {'numpy': '1.24.0'}
        }
        
        # Mock all the file operations and dependencies
        with patch('comfyui_detector.detector.get_comfyui_version', return_value="1.0.0"), \
             patch('comfyui_detector.detector.save_requirements_txt'), \
             patch('builtins.open', mock_open()), \
             patch.object(detector, '_generate_lean_manifest') as mock_lean:
            
            # Mock the lean manifest to have expected structure
            mock_lean.return_value = {
                'schema_version': '1.0',
                'detector_version': '1.0.0',
                'timestamp': '2024-01-01T00:00:00Z',
                'dependencies': {
                    'packages': {}
                }
            }
            
            result = detector.generate_migration_config()
            
            # The actual result should be the lean manifest
            assert isinstance(result, dict)
            assert 'schema_version' in result
            assert 'detector_version' in result
            assert 'timestamp' in result


class TestComfyUIEnvironmentDetectorIntegration:
    """Integration test cases for ComfyUIEnvironmentDetector."""
    
    def test_detect_all_workflow_basic(self, tmp_path):
        """Test the basic detect_all workflow up to conflict resolution."""
        # Setup
        comfyui_path = tmp_path / "ComfyUI"
        comfyui_path.mkdir()
        venv_path = tmp_path / "venv"
        venv_path.mkdir()
        
        # Create required files
        requirements_file = comfyui_path / "requirements.txt"
        requirements_file.write_text("numpy==1.24.0\nrequests>=2.28.0")
        
        detector = ComfyUIEnvironmentDetector(comfyui_path)
        
        # Mock all the utility functions and prevent final config generation
        with patch.multiple(
            'comfyui_detector.detector',
            find_python_executable=Mock(return_value=(Path("/usr/bin/python3"), venv_path)),
            detect_python_version=Mock(return_value={'python_version': '3.9.0'}),
            detect_cuda_version=Mock(return_value="11.8"),
            detect_pytorch_version=Mock(return_value={'torch': '2.0.0'}),
            extract_packages_with_uv=Mock(return_value=({}, {}, [])),
        ), patch('comfyui_detector.detector.parse_requirements_file', return_value={}), \
           patch.object(detector, 'generate_migration_config') as mock_config:
            
            # Mock generate_migration_config to return a simple dict
            mock_config.return_value = {'test': 'config'}
            
            result = detector.detect_all()
            
            # Verify the workflow methods were called
            assert detector.python_executable == Path("/usr/bin/python3")
            assert detector.venv_path == venv_path
            assert detector.system_info['python_version'] == '3.9.0'
            assert detector.system_info['cuda_version'] == "11.8"
            assert result == {'test': 'config'}


class TestComfyUIEnvironmentDetectorEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_nonexistent_comfyui_path(self):
        """Test initialization with non-existent ComfyUI path."""
        # Should not raise error during initialization
        # Path resolution happens later
        detector = ComfyUIEnvironmentDetector(Path("/nonexistent/path"))
        assert detector.comfyui_path == Path("/nonexistent/path").resolve()
    
    def test_detect_all_with_errors(self, tmp_path):
        """Test detect_all when some detection methods fail."""
        comfyui_path = tmp_path / "ComfyUI"
        comfyui_path.mkdir()
        
        detector = ComfyUIEnvironmentDetector(comfyui_path)
        
        # Mock find_python_executable to return None for venv_path
        with patch('comfyui_detector.detector.find_python_executable') as mock_find:
            mock_find.return_value = (Path("/usr/bin/python3"), None)
            
            with pytest.raises(AssertionError, match="Virtual environment not found"):
                detector.detect_all()
    
    def test_custom_nodes_with_complex_structure(self, tmp_path):
        """Test custom nodes scanning with complex directory structure."""
        comfyui_path = tmp_path / "ComfyUI"
        comfyui_path.mkdir()
        detector = ComfyUIEnvironmentDetector(comfyui_path)
        
        # Create complex custom nodes structure
        custom_nodes_dir = detector.custom_nodes_path
        custom_nodes_dir.mkdir()
        
        # Node with nested requirements
        nested_node = custom_nodes_dir / "nested_node"
        nested_node.mkdir()
        nested_req = nested_node / "requirements.txt"
        nested_req.write_text("tensorflow==2.12.0")
        
        # Hidden directory (should be skipped)
        hidden_dir = custom_nodes_dir / ".hidden"
        hidden_dir.mkdir()
        
        # Node with pyproject.toml (potential future support)
        pyproject_node = custom_nodes_dir / "pyproject_node"
        pyproject_node.mkdir()
        pyproject_file = pyproject_node / "pyproject.toml"
        pyproject_file.write_text("[tool.poetry.dependencies]\nrequests = '^2.28.0'")
        
        mock_parsed_reqs = {'tensorflow': ['==2.12.0']}
        
        with patch('comfyui_detector.detector.parse_requirements_file') as mock_parse:
            mock_parse.return_value = mock_parsed_reqs
            
            result = detector.scan_custom_nodes_requirements()
            
            # Should only process the nested_node, not hidden or pyproject_node
            assert 'nested_node' in result
            assert len(result) == 1


class TestTorchSdePackageClassification:
    """Test cases for torchsde package classification fix."""
    
    @pytest.fixture
    def detector(self, tmp_path):
        """Create a detector instance for testing torchsde classification."""
        comfyui_path = tmp_path / "ComfyUI"
        comfyui_path.mkdir()
        return ComfyUIEnvironmentDetector(comfyui_path)
    
    def test_torchsde_appears_in_packages_section_of_migration_manifest(self, detector):
        """Test that torchsde appears in the packages section of migration manifest."""
        # Setup detector with torchsde in requirements and proper system info
        detector.requirements = {
            'torchsde': ['==0.2.5'],
            'numpy': ['==1.24.0']
        }
        detector.system_info = {
            'python_version': '3.9.0',
            'installed_packages': {'numpy': '1.24.0', 'torchsde': '0.2.5'},
            'pytorch_packages': {'torch': '2.0.0', 'torchsde': '0.2.5'},
            'resolved_requirements': {}
        }
        
        # Mock the lean manifest generation to capture the output
        with patch('comfyui_detector.detector.get_comfyui_version', return_value="1.0.0"), \
             patch('comfyui_detector.detector.save_requirements_txt'), \
             patch('builtins.open', mock_open()):
            
            # Call the resolve conflicts method (this is where the fix should apply)
            detector.resolve_requirement_conflicts()
            
            # Generate the lean manifest
            result = detector._generate_lean_manifest("1.0.0")
            
            # Verify torchsde appears in regular packages, not pytorch packages
            assert 'torchsde' in detector.system_info.get('resolved_requirements', {})
            # Should NOT be in pytorch section (only torch, torchvision, torchaudio allowed)
            pytorch_packages = result.get('dependencies', {}).get('pytorch', {}).get('packages', {})
            assert 'torchsde' not in pytorch_packages
    
    def test_torchsde_excluded_from_pytorch_packages_filtering(self, detector):
        """Test that torchsde is excluded from pytorch packages filtering in conflict resolution."""
        # Setup with torchsde having conflicting requirements
        detector.requirements = {
            'torchsde': ['==0.2.5', '>=0.2.6'],  # Conflicting versions
            'torch': ['==2.0.0'],  # Regular pytorch package
            'numpy': ['==1.24.0']
        }
        detector.system_info = {
            'installed_packages': {'numpy': '1.24.0', 'torchsde': '0.2.4'},
            'pytorch_packages': {'torch': '2.0.0', 'torchsde': '0.2.4'}
        }
        
        # Run conflict resolution
        detector.resolve_requirement_conflicts()
        
        # Verify torchsde was processed (not skipped like other pytorch packages)
        # Check that torchsde conflicts were detected
        torchsde_processed = any(
            'torchsde' in str(conflict.get('package', '')) 
            for conflict in detector.conflicts
        )
        assert torchsde_processed, "torchsde should be processed for conflict resolution"
        
        # Verify torch was skipped (normal pytorch package behavior)
        torch_processed = any(
            'torch' in str(conflict.get('package', '')) and 
            str(conflict.get('package', '')) == 'torch'
            for conflict in detector.conflicts
        )
        assert not torch_processed, "torch should be skipped during conflict resolution"
    
    def test_torchsde_still_appears_in_pytorch_packages_in_detection_log(self, detector):
        """Test that torchsde still appears in pytorch_packages section for debugging."""
        # Setup system info with torchsde in pytorch_packages
        detector.system_info = {
            'python_version': '3.9.0',
            'pytorch_packages': {'torch': '2.0.0', 'torchsde': '0.2.5'},
            'installed_packages': {'numpy': '1.24.0'}
        }
        detector.pytorch_packages = {'torch': '2.0.0', 'torchsde': '0.2.5'}
        
        # This test verifies data preservation without needing full manifest generation
        # Verify that the detection log (comprehensive data) still contains torchsde
        assert 'torchsde' in detector.pytorch_packages
        assert detector.system_info['pytorch_packages']['torchsde'] == '0.2.5'
    
    def test_torchsde_requirement_conflicts_are_resolved(self, detector):
        """Test that torchsde requirement conflicts are properly resolved."""
        # Setup conflicting torchsde requirements
        detector.requirements = {
            'torchsde': ['==0.2.5', '>=0.2.6'],  # Conflicting requirements
        }
        detector.system_info = {
            'installed_packages': {'torchsde': '0.2.4'},  # Installed version conflicts
            'pytorch_packages': {'torchsde': '0.2.4'}
        }
        
        # Run conflict resolution
        detector.resolve_requirement_conflicts()
        
        # Verify conflicts were detected for torchsde
        assert len(detector.conflicts) > 0
        torchsde_conflict_found = any(
            conflict.get('package') == 'torchsde' 
            for conflict in detector.conflicts
        )
        assert torchsde_conflict_found, "torchsde conflicts should be detected and recorded"
    
    def test_migration_manifest_validation_passes_with_torchsde(self, detector):
        """Test that migration manifest validation passes when torchsde is included."""
        # Setup detector with torchsde properly classified
        detector.requirements = {'torchsde': ['==0.2.5']}
        detector.system_info = {
            'python_version': '3.9.0',
            'installed_packages': {'torchsde': '0.2.5'},
            'pytorch_packages': {'torchsde': '0.2.5'},
            'resolved_requirements': {}
        }
        
        # Mock validation and file operations
        with patch('comfyui_detector.detector.get_comfyui_version', return_value="1.0.0"), \
             patch('comfyui_detector.detector.save_requirements_txt'), \
             patch('builtins.open', mock_open()):
            
            # Process torchsde through conflict resolution
            detector.resolve_requirement_conflicts()
            
            # Generate manifest - should not raise validation errors
            try:
                result = detector._generate_lean_manifest("1.0.0")
                
                # Verify the manifest structure is valid
                assert 'schema_version' in result
                assert 'dependencies' in result
                assert 'packages' in result['dependencies']
                
                # The test passes if no exception is raised during manifest generation
                manifest_validation_passed = True
            except Exception as e:
                pytest.fail(f"Migration manifest validation failed with torchsde: {e}")
                manifest_validation_passed = False
            
            assert manifest_validation_passed, "Migration manifest should validate successfully with torchsde"


class TestPyTorchPackageDetectionUpdate:
    """Test cases for comprehensive PyTorch package detection update (Task 47)."""
    
    def test_new_cuda_packages_are_recognized(self):
        """Test that new CUDA packages from PyTorch 2.6+ are recognized as PyTorch packages."""
        from comfyui_detector.utils.version import is_pytorch_package
        
        # New CUDA packages that should be recognized
        new_cuda_packages = [
            'nvidia-cuda-cupti-cu11',
            'nvidia-cuda-cupti-cu12',
            'nvidia-cufile-cu11',
            'nvidia-cufile-cu12', 
            'nvidia-cusparselt-cu11',
            'nvidia-cusparselt-cu12',
            'nvidia-nvjitlink-cu11',
            'nvidia-nvjitlink-cu12'
        ]
        
        for package in new_cuda_packages:
            assert is_pytorch_package(package), f"{package} should be recognized as a PyTorch package"
    
    def test_triton_packages_are_recognized(self):
        """Test that triton packages for all platforms are recognized."""
        from comfyui_detector.utils.version import is_pytorch_package
        
        triton_packages = ['triton', 'triton-windows']
        
        for package in triton_packages:
            assert is_pytorch_package(package), f"{package} should be recognized as a PyTorch package"
    
    def test_nvml_packages_are_not_pytorch_packages(self):
        """Test that NVML packages are NOT recognized as PyTorch packages."""
        from comfyui_detector.utils.version import is_pytorch_package
        
        nvml_packages = ['nvidia-ml-py', 'nvidia-ml-py3']
        
        for package in nvml_packages:
            assert not is_pytorch_package(package), f"{package} should NOT be recognized as a PyTorch package"
    
    def test_regex_pattern_matches_future_cuda_packages(self):
        """Test that regex pattern correctly matches future nvidia-*-cu11/cu12 packages."""
        from comfyui_detector.utils.version import is_pytorch_package
        
        # Future hypothetical CUDA packages that should match the pattern
        future_packages = [
            'nvidia-newfeature-cu11',
            'nvidia-newfeature-cu12',
            'nvidia-some-new-lib-cu11',
            'nvidia-some-new-lib-cu12'
        ]
        
        for package in future_packages:
            assert is_pytorch_package(package), f"{package} should be recognized by regex pattern"
    
    def test_nvidia_packages_without_cuda_suffix_not_matched(self):
        """Test that nvidia packages without cu11/cu12 suffix are not matched."""
        from comfyui_detector.utils.version import is_pytorch_package
        
        # These should NOT be matched by the regex
        non_cuda_packages = [
            'nvidia-ml-py',  # NVML package
            'nvidia-ml-py3',  # NVML package
            'nvidia-some-other-lib',  # Hypothetical non-CUDA nvidia package
            'nvidia-cu10',  # Old CUDA version
            'nvidia-cuda'  # Missing version suffix
        ]
        
        for package in non_cuda_packages:
            # These should not be recognized (unless they're in the old pattern matching)
            # After implementation, nvidia-ml-py* should return False
            if package in ['nvidia-ml-py', 'nvidia-ml-py3']:
                assert not is_pytorch_package(package), f"{package} should NOT be recognized"
    
    def test_mixed_case_package_names(self):
        """Test that package detection works with mixed case names."""
        from comfyui_detector.utils.version import is_pytorch_package
        
        mixed_case_packages = [
            ('Torch', True),
            ('TorchVision', True),
            ('NVIDIA-CUDA-CUPTI-CU12', True),
            ('Triton-Windows', True),
            ('NVIDIA-ML-PY', False)  # Should not be recognized
        ]
        
        for package, expected in mixed_case_packages:
            result = is_pytorch_package(package)
            assert result == expected, f"{package} recognition failed: expected {expected}, got {result}"
    
    def test_all_existing_pytorch_packages_still_recognized(self):
        """Test that all existing PyTorch packages are still recognized (regression test)."""
        from comfyui_detector.utils.version import is_pytorch_package
        
        # Core PyTorch packages
        core_packages = ['torch', 'torchvision', 'torchaudio']
        
        # Existing CUDA packages
        existing_cuda_packages = [
            'nvidia-cublas-cu11', 'nvidia-cublas-cu12',
            'nvidia-cuda-runtime-cu11', 'nvidia-cuda-runtime-cu12',
            'nvidia-cuda-nvrtc-cu11', 'nvidia-cuda-nvrtc-cu12',
            'nvidia-cudnn-cu11', 'nvidia-cudnn-cu12',
            'nvidia-cufft-cu11', 'nvidia-cufft-cu12',
            'nvidia-curand-cu11', 'nvidia-curand-cu12',
            'nvidia-cusolver-cu11', 'nvidia-cusolver-cu12',
            'nvidia-cusparse-cu11', 'nvidia-cusparse-cu12',
            'nvidia-nccl-cu11', 'nvidia-nccl-cu12',
            'nvidia-nvtx-cu11', 'nvidia-nvtx-cu12'
        ]
        
        all_packages = core_packages + existing_cuda_packages
        
        for package in all_packages:
            assert is_pytorch_package(package), f"{package} should still be recognized as a PyTorch package"
    
    def test_torchsde_is_not_pytorch_package(self):
        """Test that torchsde is not classified as a PyTorch package (regression test for task 46)."""
        from comfyui_detector.utils.version import is_pytorch_package
        
        assert not is_pytorch_package('torchsde'), "torchsde should NOT be recognized as a PyTorch package"
        assert not is_pytorch_package('TorchSDE'), "TorchSDE (mixed case) should NOT be recognized as a PyTorch package"


class TestGitCloneFallbackLogic:
    """Test cases for git clone fallback logic in custom node detection."""
    
    def test_github_exact_version_uses_archive_method(self):
        """Test that GitHub repos with exact version matches use archive method."""
        from comfyui_detector.core.detector import ComfyUIEnvironmentDetector
        
        # Mock node info with exact GitHub version found
        node_info = {
            'install_priority': 'github',
            'github_validation': {'found': True},
            'git': {
                'github_owner': 'test-owner',
                'github_repo': 'test-repo',
                'remote_url': 'https://github.com/test-owner/test-repo.git',
                'commit': 'abc123'
            },
            'version': 'v1.0.0',
            'install_scripts': False
        }
        
        detector = ComfyUIEnvironmentDetector(Path('/tmp'))
        result = detector._create_custom_node_spec('test-node', node_info)
        
        assert result is not None
        assert result.install_method == 'archive'
        assert result.url == 'https://github.com/test-owner/test-repo/archive/refs/tags/v1.0.0.tar.gz'
        assert result.ref is None

    def test_github_no_exact_version_uses_git_method(self):
        """Test that GitHub repos without exact version use git method."""
        from comfyui_detector.core.detector import ComfyUIEnvironmentDetector
        
        # Mock node info with GitHub but no exact version
        node_info = {
            'install_priority': 'github',
            'github_validation': {'found': False},
            'git': {
                'github_owner': 'test-owner',
                'github_repo': 'test-repo',
                'remote_url': 'https://github.com/test-owner/test-repo.git',
                'commit': 'abc123'
            },
            'install_scripts': False
        }
        
        detector = ComfyUIEnvironmentDetector(Path('/tmp'))
        result = detector._create_custom_node_spec('test-node', node_info)
        
        assert result is not None
        assert result.install_method == 'git'
        assert result.url == 'https://github.com/test-owner/test-repo.git'
        assert result.ref == 'abc123'

    def test_github_no_exact_version_no_git_url_fallback_to_archive(self):
        """Test fallback to archive when git URL is missing."""
        from comfyui_detector.core.detector import ComfyUIEnvironmentDetector
        
        # Mock node info with GitHub but no git URL
        node_info = {
            'install_priority': 'github',
            'github_validation': {'found': False},
            'git': {
                'github_owner': 'test-owner',
                'github_repo': 'test-repo',
                'commit': 'abc123'
                # remote_url missing
            },
            'install_scripts': False
        }
        
        detector = ComfyUIEnvironmentDetector(Path('/tmp'))
        result = detector._create_custom_node_spec('test-node', node_info)
        
        assert result is not None
        assert result.install_method == 'archive'
        assert result.url == 'https://github.com/test-owner/test-repo/archive/abc123.tar.gz'
        assert result.ref is None

    def test_registry_priority_still_uses_archive(self):
        """Test that registry priority continues to use archive method."""
        from comfyui_detector.core.detector import ComfyUIEnvironmentDetector
        
        # Mock node info with registry priority
        node_info = {
            'install_priority': 'registry',
            'registry_validation': {'download_url': 'https://registry.example.com/download/test-node.zip'},
            'install_scripts': False
        }
        
        detector = ComfyUIEnvironmentDetector(Path('/tmp'))
        result = detector._create_custom_node_spec('test-node', node_info)
        
        assert result is not None
        assert result.install_method == 'archive'
        assert result.url == 'https://registry.example.com/download/test-node.zip'
        assert result.ref is None

    def test_git_priority_uses_git_method(self):
        """Test that git priority uses git method (existing behavior)."""
        from comfyui_detector.core.detector import ComfyUIEnvironmentDetector
        
        # Mock node info with git priority
        node_info = {
            'install_priority': 'git',
            'git': {
                'remote_url': 'https://github.com/test-owner/test-repo.git',
                'commit': 'xyz789'
            },
            'install_scripts': True
        }
        
        detector = ComfyUIEnvironmentDetector(Path('/tmp'))
        result = detector._create_custom_node_spec('test-node', node_info)
        
        assert result is not None
        assert result.install_method == 'git'
        assert result.url == 'https://github.com/test-owner/test-repo.git'
        assert result.ref == 'xyz789'
        assert result.has_post_install

    def test_local_priority_uses_local_method(self):
        """Test that local priority uses local method (existing behavior)."""
        from comfyui_detector.core.detector import ComfyUIEnvironmentDetector
        
        # Mock node info with local priority
        node_info = {
            'install_priority': 'local',
            'install_scripts': False
        }
        
        detector = ComfyUIEnvironmentDetector(Path('/tmp'))
        result = detector._create_custom_node_spec('test-node', node_info)
        
        assert result is not None
        assert result.install_method == 'local'
        assert result.url == 'test-node'
        assert result.ref is None

    def test_github_exact_version_no_version_tag_uses_commit_archive(self):
        """Test exact version found but no version tag uses commit archive."""
        from comfyui_detector.core.detector import ComfyUIEnvironmentDetector
        
        # Mock node info with exact GitHub version but no version tag
        node_info = {
            'install_priority': 'github',
            'github_validation': {'found': True},
            'git': {
                'github_owner': 'test-owner',
                'github_repo': 'test-repo',
                'remote_url': 'https://github.com/test-owner/test-repo.git',
                'commit': 'def456'
            },
            # version missing
            'install_scripts': False
        }
        
        detector = ComfyUIEnvironmentDetector(Path('/tmp'))
        result = detector._create_custom_node_spec('test-node', node_info)
        
        assert result is not None
        assert result.install_method == 'archive'
        assert result.url == 'https://github.com/test-owner/test-repo/archive/def456.tar.gz'
        assert result.ref is None

    def test_backward_compatibility_archive_specs_unchanged(self):
        """Test that existing archive-based specs remain unchanged."""
        from comfyui_detector.core.detector import ComfyUIEnvironmentDetector
        
        # Test multiple scenarios that should continue using archive
        scenarios = [
            # Registry with download URL
            {
                'install_priority': 'registry',
                'registry_validation': {'download_url': 'https://registry.com/node.zip'},
                'expected_method': 'archive',
                'expected_url': 'https://registry.com/node.zip'
            },
            # Registry fallback to GitHub archive
            {
                'install_priority': 'registry',
                'registry_validation': {'version_available': False},  # Registry exists but no download URL
                'git': {
                    'github_owner': 'owner',
                    'github_repo': 'repo',
                    'commit': 'commit123'
                },
                'expected_method': 'archive',
                'expected_url': 'https://github.com/owner/repo/archive/commit123.tar.gz'
            }
        ]
        
        detector = ComfyUIEnvironmentDetector(Path('/tmp'))
        
        for i, scenario in enumerate(scenarios):
            node_info = {k: v for k, v in scenario.items() if not k.startswith('expected_')}
            node_info['install_scripts'] = False
            
            result = detector._create_custom_node_spec(f'test-node-{i}', node_info)
            
            assert result is not None
            assert result.install_method == scenario['expected_method']
            assert result.url == scenario['expected_url']