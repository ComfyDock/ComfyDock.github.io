"""Tests for EnvironmentRecreator validation methods."""

import json
import pytest

from comfyui_detector.core.recreator import EnvironmentRecreator
from comfyui_detector.models.models import PyTorchSpec, CustomNodeSpec


class TestEnvironmentRecreatorValidation:
    """Tests for EnvironmentRecreator validation methods."""
    
    @pytest.fixture
    def mock_manifest_path(self, tmp_path):
        """Create a minimal valid manifest file."""
        manifest_data = {
            "schema_version": "1.0",
            "system_info": {
                "python_version": "3.12.0"
            },
            "custom_nodes": [],
            "dependencies": {
                "packages": {"numpy": "1.26.0"}
            }
        }
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))
        return manifest_path
    
    @pytest.fixture
    def recreator(self, mock_manifest_path, tmp_path):
        """Create EnvironmentRecreator instance for testing."""
        target_path = tmp_path / "target"
        uv_cache_path = tmp_path / "uv_cache"
        return EnvironmentRecreator(mock_manifest_path, target_path, uv_cache_path, tmp_path / "python")
    
    def test_validate_packages_all_match(self, recreator):
        """Test successful package validation when all packages match."""
        # Setup manifest with expected packages
        recreator.manifest.dependencies.packages = {
            "numpy": "1.26.0",
            "torch": "2.1.0"
        }
        
        # Simulate installed packages that match
        installed_packages = {
            "numpy": "1.26.0",
            "torch": "2.1.0",
            "other-package": "1.0.0"  # Extra packages are OK
        }
        
        warnings, errors = recreator._validate_packages(installed_packages)
        
        assert len(warnings) == 0
        assert len(errors) == 0
    
    def test_validate_packages_missing_required(self, recreator):
        """Test package validation detects missing required packages."""
        # Setup manifest with expected packages
        recreator.manifest.dependencies.packages = {
            "numpy": "1.26.0",
            "torch": "2.1.0",
            "missing-package": "1.0.0"
        }
        
        # Simulate installed packages with some missing
        installed_packages = {
            "numpy": "1.26.0",
            "torch": "2.1.0"
            # missing-package is not installed
        }
        
        warnings, errors = recreator._validate_packages(installed_packages)
        
        assert len(warnings) == 0
        assert len(errors) == 1
        assert "Missing required package: missing-package==1.0.0" in errors[0]
    
    def test_validate_packages_version_mismatch(self, recreator):
        """Test package validation detects version mismatches."""
        # Setup manifest with expected packages
        recreator.manifest.dependencies.packages = {
            "numpy": "1.26.0",
            "torch": "2.1.0"
        }
        
        # Simulate installed packages with wrong versions
        installed_packages = {
            "numpy": "1.25.0",  # Wrong version
            "torch": "2.1.0"    # Correct version
        }
        
        warnings, errors = recreator._validate_packages(installed_packages)
        
        assert len(warnings) == 1
        assert len(errors) == 0
        assert "Version mismatch for numpy: expected 1.26.0, got 1.25.0" in warnings[0]
    
    def test_validate_packages_pytorch_missing(self, recreator):
        """Test validation of missing PyTorch packages."""
        # Clear regular packages to focus on PyTorch only
        recreator.manifest.dependencies.packages = {}
        
        # Setup manifest with PyTorch packages
        recreator.manifest.dependencies.pytorch = PyTorchSpec(
            index_url="https://download.pytorch.org/whl/cu121",
            packages={"torch": "2.1.0", "torchvision": "0.16.0"}
        )
        
        # Simulate installed packages without PyTorch
        installed_packages = {
            "numpy": "1.26.0"
        }
        
        warnings, errors = recreator._validate_packages(installed_packages)
        
        assert len(errors) == 2
        assert "Missing PyTorch package: torch==2.1.0" in errors[0]
        assert "Missing PyTorch package: torchvision==0.16.0" in errors[1]
    
    def test_validate_packages_pytorch_version_mismatch(self, recreator):
        """Test validation of PyTorch version mismatches."""
        # Clear regular packages to focus on PyTorch only
        recreator.manifest.dependencies.packages = {}
        
        # Setup manifest with PyTorch packages
        recreator.manifest.dependencies.pytorch = PyTorchSpec(
            index_url="https://download.pytorch.org/whl/cu121",
            packages={"torch": "2.1.0", "torchvision": "0.16.0"}
        )
        
        # Simulate installed PyTorch with wrong versions
        installed_packages = {
            "torch": "2.0.0",      # Wrong version
            "torchvision": "0.16.0" # Correct version
        }
        
        warnings, errors = recreator._validate_packages(installed_packages)
        
        assert len(warnings) == 1
        assert len(errors) == 0
        assert "PyTorch version mismatch for torch: expected 2.1.0, got 2.0.0" in warnings[0]
    
    def test_validate_custom_nodes_all_present(self, recreator):
        """Test successful custom node validation when all nodes are present."""
        # Setup manifest with custom nodes
        recreator.manifest.custom_nodes = [
            CustomNodeSpec(
                name="ComfyUI-Manager",
                install_method="git",
                url="https://github.com/ltdrdata/ComfyUI-Manager.git"
            ),
            CustomNodeSpec(
                name="ComfyUI-Impact-Pack",
                install_method="git", 
                url="https://github.com/ltdrdata/ComfyUI-Impact-Pack.git"
            )
        ]
        
        # Simulate all nodes are installed
        installed_nodes = ["ComfyUI-Manager", "ComfyUI-Impact-Pack"]
        
        warnings, errors = recreator._validate_custom_nodes(installed_nodes)
        
        assert len(warnings) == 0
        assert len(errors) == 0
    
    def test_validate_custom_nodes_missing(self, recreator):
        """Test custom node validation detects missing nodes."""
        # Setup manifest with custom nodes
        recreator.manifest.custom_nodes = [
            CustomNodeSpec(
                name="ComfyUI-Manager",
                install_method="git",
                url="https://github.com/ltdrdata/ComfyUI-Manager.git"
            ),
            CustomNodeSpec(
                name="Missing-Node",
                install_method="git",
                url="https://github.com/user/Missing-Node.git"
            )
        ]
        
        # Simulate only one node is installed
        installed_nodes = ["ComfyUI-Manager"]
        
        warnings, errors = recreator._validate_custom_nodes(installed_nodes)
        
        assert len(warnings) == 0
        assert len(errors) == 1
        assert "Missing custom node: Missing-Node" in errors[0]
    
    def test_validate_custom_nodes_unexpected(self, recreator):
        """Test custom node validation detects unexpected nodes."""
        # Setup manifest with custom nodes
        recreator.manifest.custom_nodes = [
            CustomNodeSpec(
                name="ComfyUI-Manager",
                install_method="git",
                url="https://github.com/ltdrdata/ComfyUI-Manager.git"
            )
        ]
        
        # Simulate extra nodes are installed
        installed_nodes = ["ComfyUI-Manager", "Unexpected-Node"]
        
        warnings, errors = recreator._validate_custom_nodes(installed_nodes)
        
        assert len(warnings) == 1
        assert len(errors) == 0
        assert "Unexpected custom node found: Unexpected-Node" in warnings[0]
    
    def test_validate_environment_comprehensive(self, recreator):
        """Test comprehensive environment validation combining packages and nodes."""
        # Setup manifest with packages and custom nodes
        recreator.manifest.dependencies.packages = {"numpy": "1.26.0"}
        recreator.manifest.custom_nodes = [
            CustomNodeSpec(
                name="ComfyUI-Manager",
                install_method="git",
                url="https://github.com/ltdrdata/ComfyUI-Manager.git"
            )
        ]
        
        # Simulate partially correct installation
        installed_packages = {"numpy": "1.25.0"}  # Wrong version
        installed_nodes = []  # Missing node
        
        warnings, errors = recreator.validate_environment(installed_packages, installed_nodes)
        
        # Should have both package version warning and missing node error
        assert len(warnings) == 1
        assert len(errors) == 1
        assert "Version mismatch for numpy" in warnings[0]
        assert "Missing custom node: ComfyUI-Manager" in errors[0]
    
    def test_validate_environment_empty_manifest(self, recreator):
        """Test validation with empty manifest (no packages or nodes)."""
        # Empty manifest
        recreator.manifest.dependencies.packages = {}
        recreator.manifest.custom_nodes = []
        
        # Empty installation
        installed_packages = {}
        installed_nodes = []
        
        warnings, errors = recreator.validate_environment(installed_packages, installed_nodes)
        
        assert len(warnings) == 0
        assert len(errors) == 0