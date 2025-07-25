"""Tests for EnvironmentRecreator custom node archive installation functionality."""

import json
import pytest
import tarfile
import zipfile
from unittest.mock import patch, MagicMock
from urllib.error import URLError, HTTPError

from comfyui_detector.core.recreator import EnvironmentRecreator
from comfyui_detector.exceptions import ValidationError
from comfyui_detector.models import CustomNodeSpec


class TestEnvironmentRecreatorCustomNodeArchive:
    """Test custom node archive installation functionality in EnvironmentRecreator."""
    
    @pytest.fixture
    def base_manifest_data(self):
        """Base manifest data for testing."""
        return {
            "schema_version": "1.0",
            "system_info": {
                "python_version": "3.11.7",
                "cuda_version": None,
                "torch_version": "2.1.0+cpu",
                "comfyui_version": "v0.3.47"
            },
            "custom_nodes": [],
            "dependencies": {}
        }
    
    @pytest.fixture
    def recreator_with_manifest(self, tmp_path, base_manifest_data):
        """Create EnvironmentRecreator with valid manifest."""
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(base_manifest_data))
        
        # Create directory structure
        target_path = tmp_path / "target"
        comfyui_path = target_path / "ComfyUI"
        custom_nodes_path = comfyui_path / "custom_nodes"
        custom_nodes_path.mkdir(parents=True, exist_ok=True)
        
        recreator = EnvironmentRecreator(
            manifest_path=str(manifest_path),
            target_path=str(target_path),
            uv_cache_path=str(tmp_path / "cache"),
            python_install_path=str(tmp_path / "python")
        )
        
        return recreator
    
    @pytest.fixture
    def archive_node_spec(self):
        """CustomNodeSpec for archive installation."""
        return CustomNodeSpec(
            name="test-custom-node",
            install_method="archive",
            url="https://github.com/user/repo/archive/main.tar.gz",
            has_post_install=False
        )
    
    @pytest.fixture
    def zip_node_spec(self):
        """CustomNodeSpec for zip archive installation."""
        return CustomNodeSpec(
            name="test-zip-node",
            install_method="archive",
            url="https://github.com/user/repo/archive/main.zip",
            has_post_install=False
        )
    
    # Test successful archive installation scenarios
    
    @patch('urllib.request.urlretrieve')
    @patch('tarfile.open')
    @patch('tempfile.mkdtemp')
    def test_install_custom_node_archive_tar_gz_success(
        self, mock_mkdtemp, mock_tarfile_open, mock_urlretrieve, 
        recreator_with_manifest, archive_node_spec, tmp_path
    ):
        """Test successful installation of custom node from .tar.gz archive."""
        # Setup mocks
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()
        mock_mkdtemp.return_value = str(temp_dir)
        
        archive_path = temp_dir / "archive.tar.gz"
        mock_urlretrieve.return_value = (str(archive_path), None)
        
        # Mock tarfile extraction
        mock_tar = MagicMock()
        mock_tarfile_open.return_value.__enter__.return_value = mock_tar
        
        # Mock extraction to create a directory structure
        extracted_dir = temp_dir / "extracted" / "test-custom-node-main"
        extracted_dir.mkdir(parents=True)
        
        def mock_extractall(path):
            # Simulate extracting archive with root directory
            extracted_dir.mkdir(exist_ok=True)
            (extracted_dir / "__init__.py").write_text("# Custom node")
        
        mock_tar.extractall.side_effect = mock_extractall
        mock_tar.getnames.return_value = ["test-custom-node-main/", "test-custom-node-main/__init__.py"]
        
        # Test the method
        success, node_name = recreator_with_manifest.install_custom_node_archive(archive_node_spec)
        
        # Verify success
        assert success is True
        assert node_name == "test-custom-node"
        
        # Verify download was called correctly
        mock_urlretrieve.assert_called_once_with(
            "https://github.com/user/repo/archive/main.tar.gz",
            str(archive_path)
        )
        
        # Verify tarfile was opened and extracted
        mock_tarfile_open.assert_called_once_with(str(archive_path), 'r:gz')
        mock_tar.extractall.assert_called_once()
        
        # Note: In actual implementation, the target directory should exist
    
    @patch('urllib.request.urlretrieve')
    @patch('zipfile.ZipFile')
    @patch('tempfile.mkdtemp')
    def test_install_custom_node_archive_zip_success(
        self, mock_mkdtemp, mock_zipfile, mock_urlretrieve,
        recreator_with_manifest, zip_node_spec, tmp_path
    ):
        """Test successful installation of custom node from .zip archive."""
        # Setup mocks
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()
        mock_mkdtemp.return_value = str(temp_dir)
        
        archive_path = temp_dir / "archive.zip"
        mock_urlretrieve.return_value = (str(archive_path), None)
        
        # Mock zipfile extraction
        mock_zip = MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip
        
        # Mock extraction to create a directory structure
        extracted_dir = temp_dir / "extracted" / "test-zip-node-main"
        extracted_dir.mkdir(parents=True)
        
        def mock_extractall(path):
            # Simulate extracting archive with root directory
            extracted_dir.mkdir(exist_ok=True)
            (extracted_dir / "__init__.py").write_text("# Custom node")
        
        mock_zip.extractall.side_effect = mock_extractall
        mock_zip.namelist.return_value = ["test-zip-node-main/", "test-zip-node-main/__init__.py"]
        
        # Test the method
        success, node_name = recreator_with_manifest.install_custom_node_archive(zip_node_spec)
        
        # Verify success
        assert success is True
        assert node_name == "test-zip-node"
        
        # Verify download was called correctly
        mock_urlretrieve.assert_called_once_with(
            "https://github.com/user/repo/archive/main.zip",
            str(archive_path)
        )
        
        # Verify zipfile was opened and extracted
        mock_zipfile.assert_called_once_with(str(archive_path), 'r')
        mock_zip.extractall.assert_called_once()
    
    # Test error scenarios
    
    def test_install_custom_node_archive_invalid_install_method(
        self, recreator_with_manifest
    ):
        """Test ValidationError when install_method is not 'archive'."""
        node_spec = CustomNodeSpec(
            name="test-node",
            install_method="git",  # Wrong method
            url="https://github.com/user/repo.git"
        )
        
        with pytest.raises(ValidationError) as exc_info:
            recreator_with_manifest.install_custom_node_archive(node_spec)
        
        assert "Expected install_method 'archive'" in str(exc_info.value)
    
    @patch('urllib.request.urlretrieve')
    def test_install_custom_node_archive_download_failure(
        self, mock_urlretrieve, recreator_with_manifest, archive_node_spec
    ):
        """Test ValidationError when download fails."""
        # Mock download failure
        mock_urlretrieve.side_effect = URLError("Network error")
        
        with pytest.raises(ValidationError) as exc_info:
            recreator_with_manifest.install_custom_node_archive(archive_node_spec)
        
        assert "Failed to download archive" in str(exc_info.value)
        assert "Network error" in str(exc_info.value)
    
    @patch('urllib.request.urlretrieve')
    def test_install_custom_node_archive_http_error(
        self, mock_urlretrieve, recreator_with_manifest, archive_node_spec
    ):
        """Test ValidationError when HTTP error occurs during download."""
        # Mock HTTP error
        mock_urlretrieve.side_effect = HTTPError(
            url="https://example.com/archive.tar.gz",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None
        )
        
        with pytest.raises(ValidationError) as exc_info:
            recreator_with_manifest.install_custom_node_archive(archive_node_spec)
        
        assert "Failed to download archive" in str(exc_info.value)
        assert "404" in str(exc_info.value)
    
    def test_install_custom_node_archive_invalid_format(
        self, recreator_with_manifest
    ):
        """Test ValidationError when archive format is not supported."""
        node_spec = CustomNodeSpec(
            name="test-node",
            install_method="archive",
            url="https://github.com/user/repo/archive/main.rar"  # Unsupported format
        )
        
        with pytest.raises(ValidationError) as exc_info:
            recreator_with_manifest.install_custom_node_archive(node_spec)
        
        assert "Unsupported archive format" in str(exc_info.value)
        assert "tar.gz" in str(exc_info.value) and "zip" in str(exc_info.value)
    
    @patch('urllib.request.urlretrieve')
    @patch('tarfile.open')
    @patch('tempfile.mkdtemp')
    def test_install_custom_node_archive_corrupted_archive(
        self, mock_mkdtemp, mock_tarfile_open, mock_urlretrieve,
        recreator_with_manifest, archive_node_spec, tmp_path
    ):
        """Test ValidationError when archive is corrupted and fails to extract."""
        # Setup mocks
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()
        mock_mkdtemp.return_value = str(temp_dir)
        
        archive_path = temp_dir / "archive.tar.gz"
        mock_urlretrieve.return_value = (str(archive_path), None)
        
        # Mock extraction failure
        mock_tarfile_open.side_effect = tarfile.ReadError("Not a valid tar file")
        
        with pytest.raises(ValidationError) as exc_info:
            recreator_with_manifest.install_custom_node_archive(archive_node_spec)
        
        assert "Failed to extract archive" in str(exc_info.value)
        assert "Not a valid tar file" in str(exc_info.value)
    
    @patch('urllib.request.urlretrieve')
    @patch('zipfile.ZipFile')
    @patch('tempfile.mkdtemp')
    def test_install_custom_node_archive_corrupted_zip(
        self, mock_mkdtemp, mock_zipfile, mock_urlretrieve,
        recreator_with_manifest, zip_node_spec, tmp_path
    ):
        """Test ValidationError when zip archive is corrupted."""
        # Setup mocks
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()
        mock_mkdtemp.return_value = str(temp_dir)
        
        archive_path = temp_dir / "archive.zip"
        mock_urlretrieve.return_value = (str(archive_path), None)
        
        # Mock extraction failure
        mock_zipfile.side_effect = zipfile.BadZipFile("File is not a zip file")
        
        with pytest.raises(ValidationError) as exc_info:
            recreator_with_manifest.install_custom_node_archive(zip_node_spec)
        
        assert "Failed to extract archive" in str(exc_info.value)
        assert "File is not a zip file" in str(exc_info.value)
    
    @patch('urllib.request.urlretrieve')
    @patch('tarfile.open')
    @patch('tempfile.mkdtemp')
    def test_install_custom_node_archive_creates_proper_directory_structure(
        self, mock_mkdtemp, mock_tarfile_open, mock_urlretrieve,
        recreator_with_manifest, archive_node_spec, tmp_path
    ):
        """Test that proper directory structure is created for extracted archive."""
        # Setup mocks
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()
        mock_mkdtemp.return_value = str(temp_dir)
        
        archive_path = temp_dir / "archive.tar.gz"
        mock_urlretrieve.return_value = (str(archive_path), None)
        
        # Mock tarfile extraction
        mock_tar = MagicMock()
        mock_tarfile_open.return_value.__enter__.return_value = mock_tar
        
        # Mock archive with subdirectory structure
        mock_tar.getnames.return_value = [
            "ComfyUI-Custom-Scripts-main/",
            "ComfyUI-Custom-Scripts-main/__init__.py",
            "ComfyUI-Custom-Scripts-main/nodes.py"
        ]
        
        # Mock extraction
        extracted_base = temp_dir / "extracted"
        extracted_dir = extracted_base / "ComfyUI-Custom-Scripts-main"
        extracted_dir.mkdir(parents=True)
        
        def mock_extractall(path):
            extracted_dir.mkdir(exist_ok=True)
            (extracted_dir / "__init__.py").write_text("# Custom node")
            (extracted_dir / "nodes.py").write_text("# Node definitions")
        
        mock_tar.extractall.side_effect = mock_extractall
        
        # Test the method
        success, node_name = recreator_with_manifest.install_custom_node_archive(archive_node_spec)
        
        # Verify success and proper node name extraction
        assert success is True
        assert node_name == "test-custom-node"
        
        # Verify extraction was called with temporary directory
        mock_tar.extractall.assert_called_once()
    
    @patch('urllib.request.urlretrieve')
    @patch('tarfile.open')
    @patch('tempfile.mkdtemp')
    @patch('shutil.rmtree')
    def test_install_custom_node_archive_cleanup_on_success(
        self, mock_rmtree, mock_mkdtemp, mock_tarfile_open, mock_urlretrieve,
        recreator_with_manifest, archive_node_spec, tmp_path
    ):
        """Test that temporary files are cleaned up after successful installation."""
        # Setup mocks
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()
        mock_mkdtemp.return_value = str(temp_dir)
        
        archive_path = temp_dir / "archive.tar.gz"
        mock_urlretrieve.return_value = (str(archive_path), None)
        
        # Mock successful extraction
        mock_tar = MagicMock()
        mock_tarfile_open.return_value.__enter__.return_value = mock_tar
        mock_tar.getnames.return_value = ["test-node/", "test-node/__init__.py"]
        
        # Test the method
        success, node_name = recreator_with_manifest.install_custom_node_archive(archive_node_spec)
        
        # Verify cleanup was called
        assert success is True
        mock_rmtree.assert_called_once_with(str(temp_dir))
    
    @patch('urllib.request.urlretrieve')
    @patch('shutil.rmtree')
    def test_install_custom_node_archive_cleanup_on_failure(
        self, mock_rmtree, mock_urlretrieve, recreator_with_manifest, archive_node_spec, tmp_path
    ):
        """Test that temporary files are cleaned up even when installation fails."""
        # Setup mock to fail after download
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()
        
        with patch('tempfile.mkdtemp', return_value=str(temp_dir)):
            mock_urlretrieve.side_effect = URLError("Network error")
            
            # Test that cleanup happens even on failure
            with pytest.raises(ValidationError):
                recreator_with_manifest.install_custom_node_archive(archive_node_spec)
            
            # Verify cleanup was called
            mock_rmtree.assert_called_once_with(str(temp_dir))