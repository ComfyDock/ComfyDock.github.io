"""Unit tests for comfyui_detector.exceptions module."""

import pytest

from comfyui_detector.exceptions import (
    ComfyUIDetectorError,
    EnvironmentError,
    PythonNotFoundError,
    VirtualEnvNotFoundError,
    PackageDetectionError,
    UVNotInstalledError,
    UVCommandError,
    CustomNodeError,
    ValidationError,
    ManifestError,
    DependencyResolutionError,
)


class TestExceptionHierarchy:
    """Test cases for exception class hierarchy."""
    
    def test_base_exception(self):
        """Test ComfyUIDetectorError is the base exception."""
        exc = ComfyUIDetectorError("test message")
        assert str(exc) == "test message"
        assert isinstance(exc, Exception)
    
    def test_environment_error_inheritance(self):
        """Test EnvironmentError inherits from base."""
        exc = EnvironmentError("environment error")
        assert isinstance(exc, ComfyUIDetectorError)
        assert isinstance(exc, Exception)
        assert str(exc) == "environment error"
    
    def test_python_not_found_error_inheritance(self):
        """Test PythonNotFoundError inherits correctly."""
        exc = PythonNotFoundError("python not found")
        assert isinstance(exc, EnvironmentError)
        assert isinstance(exc, ComfyUIDetectorError)
        assert isinstance(exc, Exception)
        assert str(exc) == "python not found"
    
    def test_virtual_env_not_found_error_inheritance(self):
        """Test VirtualEnvNotFoundError inherits correctly."""
        exc = VirtualEnvNotFoundError("venv not found")
        assert isinstance(exc, EnvironmentError)
        assert isinstance(exc, ComfyUIDetectorError)
        assert isinstance(exc, Exception)
        assert str(exc) == "venv not found"
    
    def test_package_detection_error_inheritance(self):
        """Test PackageDetectionError inherits from base."""
        exc = PackageDetectionError("package detection failed")
        assert isinstance(exc, ComfyUIDetectorError)
        assert isinstance(exc, Exception)
        assert str(exc) == "package detection failed"
    
    def test_uv_not_installed_error_inheritance(self):
        """Test UVNotInstalledError inherits correctly."""
        exc = UVNotInstalledError("uv not installed")
        assert isinstance(exc, PackageDetectionError)
        assert isinstance(exc, ComfyUIDetectorError)
        assert isinstance(exc, Exception)
        assert str(exc) == "uv not installed"
    
    def test_uv_command_error_inheritance(self):
        """Test UVCommandError inherits correctly."""
        exc = UVCommandError("uv command failed")
        assert isinstance(exc, PackageDetectionError)
        assert isinstance(exc, ComfyUIDetectorError)
        assert isinstance(exc, Exception)
        assert str(exc) == "uv command failed"
    
    def test_custom_node_error_inheritance(self):
        """Test CustomNodeError inherits from base."""
        exc = CustomNodeError("custom node error")
        assert isinstance(exc, ComfyUIDetectorError)
        assert isinstance(exc, Exception)
        assert str(exc) == "custom node error"
    
    def test_validation_error_inheritance(self):
        """Test ValidationError inherits from base."""
        exc = ValidationError("validation failed")
        assert isinstance(exc, ComfyUIDetectorError)
        assert isinstance(exc, Exception)
        assert str(exc) == "validation failed"
    
    def test_manifest_error_inheritance(self):
        """Test ManifestError inherits from base."""
        exc = ManifestError("manifest generation failed")
        assert isinstance(exc, ComfyUIDetectorError)
        assert isinstance(exc, Exception)
        assert str(exc) == "manifest generation failed"
    
    def test_dependency_resolution_error_inheritance(self):
        """Test DependencyResolutionError inherits from base."""
        exc = DependencyResolutionError("dependency resolution failed")
        assert isinstance(exc, ComfyUIDetectorError)
        assert isinstance(exc, Exception)
        assert str(exc) == "dependency resolution failed"


class TestExceptionUsage:
    """Test cases for typical exception usage patterns."""
    
    def test_raise_and_catch_base_exception(self):
        """Test raising and catching base exception."""
        with pytest.raises(ComfyUIDetectorError) as exc_info:
            raise ComfyUIDetectorError("base error")
        
        assert str(exc_info.value) == "base error"
    
    def test_catch_specific_with_base(self):
        """Test that specific exceptions can be caught by base class."""
        with pytest.raises(ComfyUIDetectorError):
            raise PackageDetectionError("specific error")
    
    def test_catch_environment_errors(self):
        """Test catching environment-related errors."""
        # Test PythonNotFoundError can be caught as EnvironmentError
        with pytest.raises(EnvironmentError):
            raise PythonNotFoundError("python error")
        
        # Test VirtualEnvNotFoundError can be caught as EnvironmentError
        with pytest.raises(EnvironmentError):
            raise VirtualEnvNotFoundError("venv error")
    
    def test_catch_package_detection_errors(self):
        """Test catching package detection errors."""
        # Test UVNotInstalledError can be caught as PackageDetectionError
        with pytest.raises(PackageDetectionError):
            raise UVNotInstalledError("uv error")
        
        # Test UVCommandError can be caught as PackageDetectionError
        with pytest.raises(PackageDetectionError):
            raise UVCommandError("uv command error")
    
    def test_exception_with_none_message(self):
        """Test exceptions with None message."""
        exc = ComfyUIDetectorError(None)
        assert str(exc) == "None"
    
    def test_exception_with_empty_message(self):
        """Test exceptions with empty message."""
        exc = ComfyUIDetectorError("")
        assert str(exc) == ""
    
    def test_exception_with_complex_message(self):
        """Test exceptions with complex message."""
        complex_msg = "Error occurred in file /path/to/file.py at line 123: Invalid data format"
        exc = ValidationError(complex_msg)
        assert str(exc) == complex_msg
    
    def test_exception_args(self):
        """Test that exception args are preserved."""
        exc = ComfyUIDetectorError("message", "extra_arg", 123)
        assert exc.args == ("message", "extra_arg", 123)
        assert str(exc) == "('message', 'extra_arg', 123)"
    
    def test_exception_chaining(self):
        """Test exception chaining with raise from."""
        original_error = ValueError("original error")
        
        try:
            raise ComfyUIDetectorError("detector error") from original_error
        except ComfyUIDetectorError as e:
            assert e.__cause__ is original_error
            assert str(e) == "detector error"
            assert str(e.__cause__) == "original error"


class TestExceptionDocstrings:
    """Test that all exceptions have proper docstrings."""
    
    def test_all_exceptions_have_docstrings(self):
        """Test that all exception classes have docstrings."""
        exceptions = [
            ComfyUIDetectorError,
            EnvironmentError,
            PythonNotFoundError,
            VirtualEnvNotFoundError,
            PackageDetectionError,
            UVNotInstalledError,
            UVCommandError,
            CustomNodeError,
            ValidationError,
            ManifestError,
            DependencyResolutionError,
        ]
        
        for exc_class in exceptions:
            assert exc_class.__doc__ is not None
            assert exc_class.__doc__.strip() != ""
            assert exc_class.__doc__.endswith(".")  # Proper sentence format
    
    def test_exception_names_match_purpose(self):
        """Test that exception names clearly indicate their purpose."""
        # Test that names follow consistent patterns
        assert "Error" in ComfyUIDetectorError.__name__
        assert "Error" in EnvironmentError.__name__
        assert "NotFound" in PythonNotFoundError.__name__
        assert "NotFound" in VirtualEnvNotFoundError.__name__
        assert "Detection" in PackageDetectionError.__name__
        assert "NotInstalled" in UVNotInstalledError.__name__
        assert "Command" in UVCommandError.__name__
        assert "Node" in CustomNodeError.__name__
        assert "Validation" in ValidationError.__name__
        assert "Manifest" in ManifestError.__name__
        assert "Resolution" in DependencyResolutionError.__name__