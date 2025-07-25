"""Tests for ComfyUI detector models."""

import json
import pytest

from comfyui_detector.models import (
    SystemInfo,
    CustomNodeSpec,
    PyTorchSpec,
    DependencySpec,
    MigrationManifest,
    create_manifest_from_dict,
    create_system_info_from_detection,
    create_custom_node_spec,
    migrate_legacy_format,
)
from comfyui_detector.exceptions import ValidationError


class TestSystemInfo:
    """Tests for SystemInfo dataclass."""
    
    def test_valid_system_info(self):
        """Test creating valid system info."""
        info = SystemInfo(
            python_version="3.12.8",
            cuda_version="12.6",
            torch_version="2.7.1+cu126",
            comfyui_version="v0.3.42"
        )
        info.validate()
        assert info.python_version == "3.12.8"
        assert info.cuda_version == "12.6"
        assert info.torch_version == "2.7.1+cu126"
        assert info.comfyui_version == "v0.3.42"
    
    def test_cpu_only_system(self):
        """Test system info without CUDA."""
        info = SystemInfo(
            python_version="3.11.0",
            cuda_version=None,
            torch_version="2.7.1+cpu"
        )
        info.validate()
        assert info.cuda_version is None
    
    def test_invalid_python_version(self):
        """Test validation of invalid Python version."""
        info = SystemInfo(python_version="3.12")
        with pytest.raises(ValidationError, match="Invalid Python version"):
            info.validate()
    
    def test_invalid_cuda_version(self):
        """Test validation of invalid CUDA version."""
        info = SystemInfo(
            python_version="3.12.0",
            cuda_version="12.6.1"  # Should be M.m format
        )
        with pytest.raises(ValidationError, match="Invalid CUDA version"):
            info.validate()
    
    def test_serialization(self):
        """Test to_dict and from_dict methods."""
        info = SystemInfo(
            python_version="3.12.8",
            cuda_version="12.6",
            torch_version="2.7.1+cu126"
        )
        
        # Test to_dict
        data = info.to_dict()
        assert data["python_version"] == "3.12.8"
        assert data["cuda_version"] == "12.6"
        assert "comfyui_version" not in data  # None values excluded
        
        # Test from_dict
        info2 = SystemInfo.from_dict(data)
        assert info2.python_version == info.python_version
        assert info2.cuda_version == info.cuda_version


class TestCustomNodeSpec:
    """Tests for CustomNodeSpec dataclass."""
    
    def test_valid_archive_node(self):
        """Test creating valid archive custom node."""
        node = CustomNodeSpec(
            name="ComfyUI-Manager",
            install_method="archive",
            url="https://github.com/ltdrdata/ComfyUI-Manager/archive/main.tar.gz",
            has_post_install=True
        )
        node.validate()
        assert node.name == "ComfyUI-Manager"
        assert node.install_method == "archive"
        assert node.has_post_install is True
    
    def test_valid_git_node(self):
        """Test creating valid git custom node."""
        node = CustomNodeSpec(
            name="ComfyUI-Impact-Pack",
            install_method="git",
            url="https://github.com/ltdrdata/ComfyUI-Impact-Pack.git",
            ref="abc123def"
        )
        node.validate()
        assert node.ref == "abc123def"
    
    def test_invalid_install_method(self):
        """Test validation of invalid install method."""
        node = CustomNodeSpec(
            name="Test",
            install_method="pip",  # Invalid
            url="https://example.com"
        )
        with pytest.raises(ValidationError, match="Invalid install method"):
            node.validate()
    
    def test_invalid_url(self):
        """Test validation of invalid URL."""
        node = CustomNodeSpec(
            name="Test",
            install_method="archive",
            url="not-a-url"
        )
        with pytest.raises(ValidationError, match="Invalid URL"):
            node.validate()
    
    def test_optional_fields_serialization(self):
        """Test that optional fields are handled correctly."""
        node = CustomNodeSpec(
            name="Test",
            install_method="archive",
            url="https://example.com/archive.tar.gz"
        )
        data = node.to_dict()
        assert "ref" not in data
        assert "has_post_install" not in data


class TestPyTorchSpec:
    """Tests for PyTorchSpec dataclass."""
    
    def test_valid_pytorch_spec(self):
        """Test creating valid PyTorch specification."""
        spec = PyTorchSpec(
            index_url="https://download.pytorch.org/whl/cu126",
            packages={
                "torch": "2.7.1",
                "torchvision": "0.22.1",
                "torchaudio": "2.7.1"
            }
        )
        spec.validate()
        assert len(spec.packages) == 3
    
    def test_invalid_index_url(self):
        """Test validation of invalid index URL."""
        spec = PyTorchSpec(
            index_url="not-a-url",
            packages={"torch": "2.7.1"}
        )
        with pytest.raises(ValidationError, match="Invalid PyTorch index URL"):
            spec.validate()
    
    def test_empty_packages(self):
        """Test validation with empty packages."""
        spec = PyTorchSpec(
            index_url="https://download.pytorch.org/whl/cu126",
            packages={}
        )
        with pytest.raises(ValidationError, match="PyTorch packages cannot be empty"):
            spec.validate()
    
    def test_invalid_package_name(self):
        """Test validation of invalid package name."""
        spec = PyTorchSpec(
            index_url="https://download.pytorch.org/whl/cu126",
            packages={"torch@123": "2.7.1"}  # Invalid character
        )
        with pytest.raises(ValidationError, match="Invalid package name"):
            spec.validate()


class TestDependencySpec:
    """Tests for DependencySpec dataclass."""
    
    def test_minimal_dependencies(self):
        """Test minimal dependency specification."""
        deps = DependencySpec(
            packages={"numpy": "1.26.0", "pillow": "10.0.0"}
        )
        deps.validate()
        assert len(deps.packages) == 2
        assert deps.pytorch is None
    
    def test_full_dependencies(self):
        """Test full dependency specification."""
        deps = DependencySpec(
            packages={"numpy": "1.26.0"},
            pytorch=PyTorchSpec(
                index_url="https://download.pytorch.org/whl/cu126",
                packages={"torch": "2.7.1"}
            ),
            editable_installs=["-e /path/to/package"],
            git_requirements=["git+https://github.com/user/repo.git@main#egg=package"]
        )
        deps.validate()
        assert deps.pytorch is not None
        assert len(deps.editable_installs) == 1
        assert len(deps.git_requirements) == 1
    
    def test_invalid_editable_install(self):
        """Test validation of invalid editable install."""
        deps = DependencySpec(
            editable_installs=["/path/to/package"]  # Missing -e
        )
        with pytest.raises(ValidationError, match="Editable install must start with '-e '"):
            deps.validate()
    
    def test_invalid_git_requirement(self):
        """Test validation of invalid git requirement."""
        deps = DependencySpec(
            git_requirements=["https://github.com/user/repo.git"]  # Missing git+
        )
        with pytest.raises(ValidationError, match="Git requirement must start with 'git\\+'"):
            deps.validate()
    
    def test_serialization_excludes_empty(self):
        """Test that empty fields are excluded from serialization."""
        deps = DependencySpec(packages={"numpy": "1.26.0"})
        data = deps.to_dict()
        assert "packages" in data
        assert "pytorch" not in data
        assert "editable_installs" not in data
        assert "git_requirements" not in data


class TestMigrationManifest:
    """Tests for MigrationManifest dataclass."""
    
    def test_minimal_manifest(self):
        """Test creating minimal valid manifest."""
        manifest = MigrationManifest(
            system_info=SystemInfo(python_version="3.12.0"),
            custom_nodes=[],
            dependencies=DependencySpec()
        )
        manifest.validate()
        assert manifest.schema_version == "1.0"
    
    def test_full_manifest(self):
        """Test creating full manifest with all fields."""
        manifest = MigrationManifest(
            system_info=SystemInfo(
                python_version="3.12.8",
                cuda_version="12.6",
                torch_version="2.7.1+cu126",
                comfyui_version="v0.3.42"
            ),
            custom_nodes=[
                CustomNodeSpec(
                    name="ComfyUI-Manager",
                    install_method="archive",
                    url="https://github.com/ltdrdata/ComfyUI-Manager/archive/main.tar.gz"
                )
            ],
            dependencies=DependencySpec(
                packages={"numpy": "1.26.0"},
                pytorch=PyTorchSpec(
                    index_url="https://download.pytorch.org/whl/cu126",
                    packages={"torch": "2.7.1"}
                )
            )
        )
        manifest.validate()
        assert len(manifest.custom_nodes) == 1
        assert manifest.dependencies.pytorch is not None
    
    def test_json_serialization_roundtrip(self):
        """Test JSON serialization and deserialization."""
        manifest = MigrationManifest(
            system_info=SystemInfo(
                python_version="3.12.8",
                cuda_version="12.6"
            ),
            custom_nodes=[
                CustomNodeSpec(
                    name="Test",
                    install_method="git",
                    url="https://github.com/test/repo.git",
                    ref="main"
                )
            ],
            dependencies=DependencySpec(
                packages={"numpy": "1.26.0"}
            )
        )
        
        # Serialize to JSON
        json_str = manifest.to_json()
        data = json.loads(json_str)
        
        # Check structure
        assert data["schema_version"] == "1.0"
        assert data["system_info"]["python_version"] == "3.12.8"
        assert len(data["custom_nodes"]) == 1
        assert data["dependencies"]["packages"]["numpy"] == "1.26.0"
        
        # Deserialize back
        manifest2 = MigrationManifest.from_json(json_str)
        assert manifest2.system_info.python_version == "3.12.8"
        assert manifest2.custom_nodes[0].name == "Test"
        assert manifest2.dependencies.packages["numpy"] == "1.26.0"
    
    def test_invalid_schema_version(self):
        """Test validation of unsupported schema version."""
        manifest = MigrationManifest(
            schema_version="2.0",  # Unsupported
            system_info=SystemInfo(python_version="3.12.0")
        )
        with pytest.raises(ValidationError, match="Unsupported schema version"):
            manifest.validate()


class TestFactoryFunctions:
    """Tests for factory functions."""
    
    def test_create_manifest_from_dict(self):
        """Test creating manifest from dictionary."""
        data = {
            "schema_version": "1.0",
            "system_info": {
                "python_version": "3.12.8",
                "cuda_version": "12.6"
            },
            "custom_nodes": [],
            "dependencies": {
                "packages": {"numpy": "1.26.0"}
            }
        }
        manifest = create_manifest_from_dict(data)
        assert manifest.system_info.python_version == "3.12.8"
        assert manifest.dependencies.packages["numpy"] == "1.26.0"
    
    def test_create_system_info_from_detection(self):
        """Test creating system info from detection results."""
        info = create_system_info_from_detection(
            python_version="3.12.8",
            cuda_version="12.6",
            torch_version="2.7.1+cu126"
        )
        assert info.python_version == "3.12.8"
        assert info.cuda_version == "12.6"
    
    def test_create_custom_node_spec(self):
        """Test creating custom node spec."""
        spec = create_custom_node_spec(
            name="Test",
            install_method="archive",
            url="https://example.com/archive.tar.gz",
            has_post_install=True
        )
        assert spec.name == "Test"
        assert spec.has_post_install is True
    
    def test_migrate_legacy_format(self):
        """Test migrating from legacy dict format."""
        legacy_data = {
            "schema_version": "1.0",
            "python_version": "3.12.8",
            "cuda_version": "12.6",
            "torch_version": "2.7.1+cu126",
            "comfyui_version": "v0.3.42",
            "custom_nodes": [
                {
                    "name": "ComfyUI-Manager",
                    "install_method": "archive",
                    "url": "https://github.com/ltdrdata/ComfyUI-Manager/archive/main.tar.gz"
                }
            ],
            "dependencies": {
                "packages": {"numpy": "1.26.0"},
                "pytorch": {
                    "index_url": "https://download.pytorch.org/whl/cu126",
                    "packages": {"torch": "2.7.1"}
                }
            }
        }
        
        manifest = migrate_legacy_format(legacy_data)
        assert manifest.system_info.python_version == "3.12.8"
        assert manifest.system_info.cuda_version == "12.6"
        assert len(manifest.custom_nodes) == 1
        assert manifest.dependencies.pytorch is not None