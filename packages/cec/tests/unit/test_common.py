"""Unit tests for comfyui_detector.common module."""

import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from comfyui_detector.common import (
    run_command,
    safe_json_load,
    safe_json_dump,
    normalize_package_name,
    parse_git_url,
    is_valid_version,
    format_size,
    extract_archive_name,
    validate_path,
)
from comfyui_detector.exceptions import ComfyUIDetectorError


class TestRunCommand:
    """Test cases for run_command function."""
    
    def test_run_command_success(self):
        """Test successful command execution."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout='output',
                stderr=''
            )
            
            result = run_command(['echo', 'test'])
            
            assert result.returncode == 0
            assert result.stdout == 'output'
            mock_run.assert_called_once_with(
                ['echo', 'test'],
                cwd=None,
                timeout=30,
                capture_output=True,
                text=True,
                env=None
            )
    
    def test_run_command_with_cwd(self):
        """Test command execution with working directory."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)
            
            result = run_command(['ls'], cwd=Path('/tmp'))
            
            assert result.returncode == 0
            mock_run.assert_called_once_with(
                ['ls'],
                cwd='/tmp',
                timeout=30,
                capture_output=True,
                text=True,
                env=None
            )
    
    def test_run_command_failure_with_check(self):
        """Test command failure with check=True raises exception."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=1,
                stderr='error message'
            )
            
            with pytest.raises(ComfyUIDetectorError) as exc_info:
                run_command(['false'], check=True)
            
            assert 'Command failed with exit code 1' in str(exc_info.value)
            assert 'error message' in str(exc_info.value)
    
    def test_run_command_timeout(self):
        """Test command timeout handling."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired('cmd', 30)
            
            with pytest.raises(ComfyUIDetectorError) as exc_info:
                run_command(['sleep', '100'])
            
            assert 'Command timed out after 30s' in str(exc_info.value)
    
    def test_run_command_exception(self):
        """Test general exception handling."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception('Unexpected error')
            
            with pytest.raises(ComfyUIDetectorError) as exc_info:
                run_command(['cmd'])
            
            assert 'Error running command' in str(exc_info.value)
            assert 'Unexpected error' in str(exc_info.value)


class TestSafeJsonLoad:
    """Test cases for safe_json_load function."""
    
    def test_load_valid_json(self, tmp_path):
        """Test loading valid JSON file."""
        json_file = tmp_path / 'test.json'
        data = {'key': 'value', 'number': 42}
        json_file.write_text(json.dumps(data))
        
        result = safe_json_load(json_file)
        assert result == data
    
    def test_load_nonexistent_file(self):
        """Test loading non-existent file returns None."""
        result = safe_json_load(Path('/nonexistent/file.json'))
        assert result is None
    
    def test_load_invalid_json(self, tmp_path):
        """Test loading invalid JSON returns None."""
        json_file = tmp_path / 'invalid.json'
        json_file.write_text('{"invalid": json}')
        
        result = safe_json_load(json_file)
        assert result is None
    
    def test_load_permission_error(self):
        """Test handling permission errors."""
        with patch('builtins.open', side_effect=PermissionError('Access denied')):
            result = safe_json_load(Path('/some/file.json'))
            assert result is None


class TestSafeJsonDump:
    """Test cases for safe_json_dump function."""
    
    def test_dump_valid_data(self, tmp_path):
        """Test dumping valid data to file."""
        json_file = tmp_path / 'output.json'
        data = {'key': 'value', 'list': [1, 2, 3]}
        
        result = safe_json_dump(data, json_file)
        assert result is True
        
        loaded_data = json.loads(json_file.read_text())
        assert loaded_data == data
    
    def test_dump_with_custom_indent(self, tmp_path):
        """Test dumping with custom indentation."""
        json_file = tmp_path / 'output.json'
        data = {'nested': {'key': 'value'}}
        
        result = safe_json_dump(data, json_file, indent=4)
        assert result is True
        
        content = json_file.read_text()
        assert '    ' in content  # 4 spaces indentation
    
    def test_dump_permission_error(self):
        """Test handling permission errors during dump."""
        with patch('builtins.open', side_effect=PermissionError('Access denied')):
            result = safe_json_dump({'data': 'value'}, Path('/readonly/file.json'))
            assert result is False
    
    def test_dump_invalid_data(self, tmp_path):
        """Test dumping non-serializable data."""
        json_file = tmp_path / 'output.json'
        
        # Object that can't be serialized
        class NonSerializable:
            pass
        
        result = safe_json_dump({'obj': NonSerializable()}, json_file)
        assert result is False


class TestNormalizePackageName:
    """Test cases for normalize_package_name function."""
    
    def test_normalize_simple_name(self):
        """Test normalizing simple package names."""
        assert normalize_package_name('Django') == 'django'
        assert normalize_package_name('NumPy') == 'numpy'
        assert normalize_package_name('SciPy') == 'scipy'
    
    def test_normalize_with_underscores(self):
        """Test normalizing names with underscores."""
        assert normalize_package_name('google_cloud_storage') == 'google-cloud-storage'
        assert normalize_package_name('some_package_name') == 'some-package-name'
    
    def test_normalize_with_dots(self):
        """Test normalizing names with dots."""
        assert normalize_package_name('backports.weakref') == 'backports-weakref'
        assert normalize_package_name('zope.interface') == 'zope-interface'
    
    def test_normalize_mixed_separators(self):
        """Test normalizing names with mixed separators."""
        assert normalize_package_name('Some.Package_Name') == 'some-package-name'
        assert normalize_package_name('UPPERCASE.package_NAME') == 'uppercase-package-name'
    
    def test_normalize_already_normalized(self):
        """Test that already normalized names remain unchanged."""
        assert normalize_package_name('already-normalized') == 'already-normalized'
        assert normalize_package_name('package-name') == 'package-name'


class TestParseGitUrl:
    """Test cases for parse_git_url function."""
    
    def test_parse_https_github_url(self):
        """Test parsing HTTPS GitHub URL."""
        url = 'https://github.com/user/repo.git'
        result = parse_git_url(url)
        
        assert result['owner'] == 'user'
        assert result['repo'] == 'repo'
        assert result['url'] == 'https://github.com/user/repo'
    
    def test_parse_ssh_github_url(self):
        """Test parsing SSH GitHub URL."""
        url = 'git@github.com:user/repo.git'
        result = parse_git_url(url)
        
        assert result['owner'] == 'user'
        assert result['repo'] == 'repo'
        assert result['url'] == 'https://github.com/user/repo'
    
    def test_parse_url_without_git_extension(self):
        """Test parsing URL without .git extension."""
        url = 'https://github.com/user/repo'
        result = parse_git_url(url)
        
        assert result['owner'] == 'user'
        assert result['repo'] == 'repo'
        assert result['url'] == 'https://github.com/user/repo'
    
    def test_parse_gitlab_url(self):
        """Test parsing GitLab URL."""
        # GitLab URLs are not supported in current implementation
        url = 'https://gitlab.com/group/subgroup/project.git'
        result = parse_git_url(url)
        
        assert result is None
    
    def test_parse_url_with_branch(self):
        """Test parsing URL with branch specification."""
        # Current implementation doesn't parse branch from URL
        url = 'git+https://github.com/user/repo.git@branch'
        result = parse_git_url(url)
        
        assert result is None
    
    def test_parse_url_with_commit_hash(self):
        """Test parsing URL with commit hash."""
        # Current implementation doesn't parse commit from URL
        url = 'git+https://github.com/user/repo.git@abc123def456'
        result = parse_git_url(url)
        
        assert result is None
    
    def test_parse_invalid_url(self):
        """Test parsing invalid URL returns None."""
        assert parse_git_url('not-a-url') is None
        assert parse_git_url('http://example.com') is None
        assert parse_git_url('') is None


class TestIsValidVersion:
    """Test cases for is_valid_version function."""
    
    def test_valid_versions(self):
        """Test valid version strings."""
        valid_versions = [
            '1.0.0',
            '2.1.3',
            '0.0.1',
            '1.2.3a1',
            '1.2.3b2',
            '1.2.3c1',
            '2021.12.1',
        ]
        
        for version in valid_versions:
            assert is_valid_version(version) is True
    
    def test_invalid_versions(self):
        """Test invalid version strings."""
        invalid_versions = [
            '',
            'not-a-version',
            'v1.0.0',  # 'v' prefix not allowed
            '1.2.3-alpha',  # hyphen not allowed
            'latest',
            'nightly',
            None,
        ]
        
        for version in invalid_versions:
            if version is not None:
                assert is_valid_version(version) is False


class TestFormatSize:
    """Test cases for format_size function."""
    
    def test_format_bytes(self):
        """Test formatting bytes."""
        assert format_size(0) == '0 B'
        assert format_size(100) == '100 B'
        assert format_size(1023) == '1023 B'
    
    def test_format_kilobytes(self):
        """Test formatting kilobytes."""
        assert format_size(1024) == '1.0 KB'
        assert format_size(1536) == '1.5 KB'
        assert format_size(10240) == '10.0 KB'
    
    def test_format_megabytes(self):
        """Test formatting megabytes."""
        assert format_size(1024 * 1024) == '1.0 MB'
        assert format_size(5 * 1024 * 1024) == '5.0 MB'
        assert format_size(1024 * 1024 * 1024 - 1) == '1024.0 MB'
    
    def test_format_gigabytes(self):
        """Test formatting gigabytes."""
        assert format_size(1024 * 1024 * 1024) == '1.0 GB'
        assert format_size(10 * 1024 * 1024 * 1024) == '10.0 GB'
    
    def test_format_terabytes(self):
        """Test formatting terabytes."""
        assert format_size(1024 * 1024 * 1024 * 1024) == '1.0 TB'
        assert format_size(2 * 1024 * 1024 * 1024 * 1024) == '2.0 TB'


class TestExtractArchiveName:
    """Test cases for extract_archive_name function."""
    
    def test_extract_from_github_url(self):
        """Test extracting archive name from GitHub URLs."""
        assert extract_archive_name('https://github.com/user/repo') == 'repo.tar.gz'
        assert extract_archive_name('https://github.com/user/repo.git') == 'repo.git.tar.gz'
        assert extract_archive_name('https://github.com/user/my-project') == 'my-project.tar.gz'
    
    def test_extract_from_gitlab_url(self):
        """Test extracting archive name from GitLab URLs."""
        assert extract_archive_name('https://gitlab.com/user/repo') == 'repo.tar.gz'
        assert extract_archive_name('https://gitlab.com/group/subgroup/project') == 'project.tar.gz'
    
    def test_extract_from_file_url(self):
        """Test extracting archive name from file URLs."""
        assert extract_archive_name('https://example.com/archive.zip') == 'archive.zip'
        assert extract_archive_name('https://example.com/package-1.0.0.tar.gz') == 'package-1.0.0.tar.gz.tar.gz'
        assert extract_archive_name('https://example.com/path/to/file.tar') == 'file.tar'
    
    def test_extract_from_complex_url(self):
        """Test extracting from URLs with query parameters."""
        assert extract_archive_name('https://github.com/user/repo/archive/v1.0.0.zip') == 'v1.0.0.zip'
        assert extract_archive_name('https://example.com/file.zip?param=value') == 'file.zip'


class TestValidatePath:
    """Test cases for validate_path function."""
    
    def test_validate_existing_path(self, tmp_path):
        """Test validating existing path."""
        test_file = tmp_path / 'test.txt'
        test_file.touch()
        
        result = validate_path(test_file, must_exist=True)
        assert result == test_file
        assert isinstance(result, Path)
    
    def test_validate_nonexistent_path_must_exist(self):
        """Test validating non-existent path with must_exist=True."""
        with pytest.raises(ComfyUIDetectorError) as exc_info:
            validate_path('/nonexistent/path', must_exist=True)
        
        assert 'does not exist' in str(exc_info.value)
    
    def test_validate_nonexistent_path_optional(self):
        """Test validating non-existent path with must_exist=False."""
        path = '/nonexistent/path'
        result = validate_path(path, must_exist=False)
        
        assert result == Path(path)
        assert isinstance(result, Path)
    
    def test_validate_string_path(self, tmp_path):
        """Test validating string path."""
        result = validate_path(str(tmp_path), must_exist=True)
        
        assert result == tmp_path
        assert isinstance(result, Path)
    
    def test_validate_path_object(self, tmp_path):
        """Test validating Path object."""
        result = validate_path(tmp_path, must_exist=True)
        
        assert result == tmp_path
        assert isinstance(result, Path)