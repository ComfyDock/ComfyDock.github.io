"""Tests for EnvironmentResult model."""

import pytest
from pathlib import Path

from comfyui_detector.models.models import EnvironmentResult
from comfyui_detector.exceptions import ValidationError


class TestEnvironmentResult:
    """Tests for EnvironmentResult dataclass."""
    
    def test_environment_result_creation(self):
        """Test basic EnvironmentResult creation."""
        result = EnvironmentResult(
            success=True,
            environment_path=Path("/test/env"),
            venv_path=Path("/test/env/.venv"),
            comfyui_path=Path("/test/env/ComfyUI"),
            installed_packages={"numpy": "1.26.0", "torch": "2.1.0"},
            installed_nodes=["ComfyUI-Manager", "ComfyUI-Impact-Pack"],
            warnings=["Version mismatch for some-package"],
            errors=[],
            duration_seconds=120.5
        )
        
        assert result.success is True
        assert result.environment_path == Path("/test/env")
        assert result.venv_path == Path("/test/env/.venv")
        assert result.comfyui_path == Path("/test/env/ComfyUI")
        assert len(result.installed_packages) == 2
        assert len(result.installed_nodes) == 2
        assert len(result.warnings) == 1
        assert len(result.errors) == 0
        assert result.duration_seconds == 120.5
    
    def test_environment_result_validation_success(self):
        """Test validation of valid EnvironmentResult."""
        result = EnvironmentResult(
            success=True,
            environment_path=Path("/test/env"),
            venv_path=Path("/test/env/.venv"),
            comfyui_path=Path("/test/env/ComfyUI"),
            installed_packages={},
            installed_nodes=[],
            warnings=[],
            errors=[],
            duration_seconds=0.0
        )
        # Should not raise any exception
        result.validate()
    
    def test_environment_result_validation_invalid_success_type(self):
        """Test validation fails with invalid success type."""
        result = EnvironmentResult(
            success="yes",  # Should be bool
            environment_path=Path("/test/env"),
            venv_path=Path("/test/env/.venv"),
            comfyui_path=Path("/test/env/ComfyUI"),
            installed_packages={},
            installed_nodes=[],
            warnings=[],
            errors=[],
            duration_seconds=0.0
        )
        with pytest.raises(ValidationError, match="success must be a boolean"):
            result.validate()
    
    def test_environment_result_validation_invalid_duration(self):
        """Test validation fails with negative duration."""
        result = EnvironmentResult(
            success=True,
            environment_path=Path("/test/env"),
            venv_path=Path("/test/env/.venv"),
            comfyui_path=Path("/test/env/ComfyUI"),
            installed_packages={},
            installed_nodes=[],
            warnings=[],
            errors=[],
            duration_seconds=-10.0
        )
        with pytest.raises(ValidationError, match="duration_seconds must be non-negative"):
            result.validate()
    
    def test_environment_result_validation_invalid_path_types(self):
        """Test validation fails with non-Path types for paths."""
        result = EnvironmentResult(
            success=True,
            environment_path="/test/env",  # Should be Path
            venv_path=Path("/test/env/.venv"),
            comfyui_path=Path("/test/env/ComfyUI"),
            installed_packages={},
            installed_nodes=[],
            warnings=[],
            errors=[],
            duration_seconds=0.0
        )
        with pytest.raises(ValidationError, match="environment_path must be a Path object"):
            result.validate()
    
    def test_environment_result_serialization(self):
        """Test to_dict method."""
        result = EnvironmentResult(
            success=True,
            environment_path=Path("/test/env"),
            venv_path=Path("/test/env/.venv"),
            comfyui_path=Path("/test/env/ComfyUI"),
            installed_packages={"numpy": "1.26.0"},
            installed_nodes=["ComfyUI-Manager"],
            warnings=["Warning message"],
            errors=["Error message"],
            duration_seconds=120.5
        )
        
        data = result.to_dict()
        assert data["success"] is True
        assert data["environment_path"] == "/test/env"
        assert data["venv_path"] == "/test/env/.venv"
        assert data["comfyui_path"] == "/test/env/ComfyUI"
        assert data["installed_packages"] == {"numpy": "1.26.0"}
        assert data["installed_nodes"] == ["ComfyUI-Manager"]
        assert data["warnings"] == ["Warning message"]
        assert data["errors"] == ["Error message"]
        assert data["duration_seconds"] == 120.5
    
    def test_environment_result_deserialization(self):
        """Test from_dict method."""
        data = {
            "success": True,
            "environment_path": "/test/env",
            "venv_path": "/test/env/.venv", 
            "comfyui_path": "/test/env/ComfyUI",
            "installed_packages": {"numpy": "1.26.0"},
            "installed_nodes": ["ComfyUI-Manager"],
            "warnings": ["Warning message"],
            "errors": [],
            "duration_seconds": 120.5
        }
        
        result = EnvironmentResult.from_dict(data)
        assert result.success is True
        assert result.environment_path == Path("/test/env")
        assert result.venv_path == Path("/test/env/.venv")
        assert result.comfyui_path == Path("/test/env/ComfyUI")
        assert result.installed_packages == {"numpy": "1.26.0"}
        assert result.installed_nodes == ["ComfyUI-Manager"]
        assert result.warnings == ["Warning message"]
        assert result.errors == []
        assert result.duration_seconds == 120.5
    
    def test_environment_result_serialization_roundtrip(self):
        """Test serialization and deserialization roundtrip."""
        original = EnvironmentResult(
            success=False,
            environment_path=Path("/test/env"),
            venv_path=Path("/test/env/.venv"),
            comfyui_path=Path("/test/env/ComfyUI"),
            installed_packages={"numpy": "1.26.0", "torch": "2.1.0"},
            installed_nodes=["ComfyUI-Manager", "ComfyUI-Impact-Pack"],
            warnings=["Warning 1", "Warning 2"],
            errors=["Error 1"],
            duration_seconds=456.78
        )
        
        # Serialize and deserialize
        data = original.to_dict()
        reconstructed = EnvironmentResult.from_dict(data)
        
        # Verify all fields match
        assert reconstructed.success == original.success
        assert reconstructed.environment_path == original.environment_path
        assert reconstructed.venv_path == original.venv_path
        assert reconstructed.comfyui_path == original.comfyui_path
        assert reconstructed.installed_packages == original.installed_packages
        assert reconstructed.installed_nodes == original.installed_nodes
        assert reconstructed.warnings == original.warnings
        assert reconstructed.errors == original.errors
        assert reconstructed.duration_seconds == original.duration_seconds
    
    def test_environment_result_empty_collections(self):
        """Test EnvironmentResult with empty collections."""
        result = EnvironmentResult(
            success=True,
            environment_path=Path("/test/env"),
            venv_path=Path("/test/env/.venv"),
            comfyui_path=Path("/test/env/ComfyUI"),
            installed_packages={},
            installed_nodes=[],
            warnings=[],
            errors=[],
            duration_seconds=0.0
        )
        
        result.validate()
        assert len(result.installed_packages) == 0
        assert len(result.installed_nodes) == 0
        assert len(result.warnings) == 0
        assert len(result.errors) == 0