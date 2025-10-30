"""Unit tests for py add/remove/list commands."""
from unittest.mock import MagicMock, patch
from argparse import Namespace

import pytest

from comfydock_cli.env_commands import EnvironmentCommands
from comfydock_core.models.exceptions import UVCommandError


class TestPyAdd:
    """Test 'cfd py add' command handler."""

    @patch('comfydock_cli.env_commands.get_workspace_or_exit')
    def test_add_single_package(self, mock_workspace):
        """Should call add_dependencies with single package."""
        # Setup mocks
        mock_env = MagicMock()
        mock_workspace.return_value.get_active_environment.return_value = mock_env
        mock_env.name = "test-env"
        mock_env.add_dependencies.return_value = "Added: requests"

        # Create command handler
        cmd = EnvironmentCommands()

        # Create args
        args = Namespace(
            packages=["requests"],
            requirements=None,
            upgrade=False,
            target_env=None
        )

        # Execute
        with patch('builtins.print'):
            cmd.py_add(args)

        # Verify
        mock_env.add_dependencies.assert_called_once_with(
            packages=["requests"],
            requirements_file=None,
            upgrade=False
        )

    @patch('comfydock_cli.env_commands.get_workspace_or_exit')
    def test_add_multiple_packages(self, mock_workspace):
        """Should call add_dependencies with multiple packages."""
        mock_env = MagicMock()
        mock_workspace.return_value.get_active_environment.return_value = mock_env
        mock_env.name = "test-env"
        mock_env.add_dependencies.return_value = "Added: 3 packages"

        cmd = EnvironmentCommands()
        args = Namespace(
            packages=["requests", "pillow", "tqdm"],
            requirements=None,
            upgrade=False,
            target_env=None
        )

        with patch('builtins.print'):
            cmd.py_add(args)

        mock_env.add_dependencies.assert_called_once_with(
            packages=["requests", "pillow", "tqdm"],
            requirements_file=None,
            upgrade=False
        )

    @patch('comfydock_cli.env_commands.get_workspace_or_exit')
    def test_add_with_upgrade_flag(self, mock_workspace):
        """Should pass upgrade=True when --upgrade is specified."""
        mock_env = MagicMock()
        mock_workspace.return_value.get_active_environment.return_value = mock_env
        mock_env.name = "test-env"
        mock_env.add_dependencies.return_value = "Upgraded: requests"

        cmd = EnvironmentCommands()
        args = Namespace(
            packages=["requests"],
            requirements=None,
            upgrade=True,
            target_env=None
        )

        with patch('builtins.print'):
            cmd.py_add(args)

        mock_env.add_dependencies.assert_called_once_with(
            packages=["requests"],
            requirements_file=None,
            upgrade=True
        )

    @patch('comfydock_cli.env_commands.get_workspace_or_exit')
    def test_add_handles_uv_error(self, mock_workspace):
        """Should handle UVCommandError gracefully."""
        mock_env = MagicMock()
        mock_workspace.return_value.get_active_environment.return_value = mock_env
        mock_env.name = "test-env"
        mock_env.add_dependencies.side_effect = UVCommandError(
            "Package not found",
            command=["uv", "add", "nonexistent"]
        )

        cmd = EnvironmentCommands()
        args = Namespace(
            packages=["nonexistent"],
            requirements=None,
            upgrade=False,
            target_env=None
        )

        with patch('builtins.print'):
            with pytest.raises(SystemExit) as exc_info:
                cmd.py_add(args)

        assert exc_info.value.code == 1

    @patch('comfydock_cli.env_commands.get_workspace_or_exit')
    def test_add_from_requirements_file(self, mock_workspace, tmp_path):
        """Should add packages from requirements.txt file."""
        from pathlib import Path

        # Create a real temporary requirements file
        reqs_file = tmp_path / "requirements.txt"
        reqs_file.write_text("requests>=2.0.0\npillow\n")

        mock_env = MagicMock()
        mock_workspace.return_value.get_active_environment.return_value = mock_env
        mock_env.name = "test-env"
        mock_env.add_dependencies.return_value = "Added packages from requirements"

        cmd = EnvironmentCommands()
        args = Namespace(
            packages=[],
            requirements=reqs_file,
            upgrade=False,
            target_env=None
        )

        with patch('builtins.print'):
            cmd.py_add(args)

        # Should call with absolute path to requirements_file
        mock_env.add_dependencies.assert_called_once_with(
            packages=None,
            requirements_file=reqs_file.resolve(),
            upgrade=False
        )

    @patch('comfydock_cli.env_commands.get_workspace_or_exit')
    def test_add_requirements_with_upgrade(self, mock_workspace, tmp_path):
        """Should support --upgrade with requirements file."""
        from pathlib import Path

        # Create a real temporary requirements file
        reqs_file = tmp_path / "requirements.txt"
        reqs_file.write_text("requests>=2.0.0\npillow\n")

        mock_env = MagicMock()
        mock_workspace.return_value.get_active_environment.return_value = mock_env
        mock_env.name = "test-env"
        mock_env.add_dependencies.return_value = "Upgraded packages from requirements"

        cmd = EnvironmentCommands()
        args = Namespace(
            packages=[],
            requirements=reqs_file,
            upgrade=True,
            target_env=None
        )

        with patch('builtins.print'):
            cmd.py_add(args)

        mock_env.add_dependencies.assert_called_once_with(
            packages=None,
            requirements_file=reqs_file.resolve(),
            upgrade=True
        )

    @patch('comfydock_cli.env_commands.get_workspace_or_exit')
    def test_add_errors_with_both_packages_and_requirements(self, mock_workspace, tmp_path):
        """Should error when both packages and requirements file are specified."""
        from pathlib import Path

        # Create a real temporary requirements file
        reqs_file = tmp_path / "requirements.txt"
        reqs_file.write_text("requests>=2.0.0\n")

        mock_env = MagicMock()
        mock_workspace.return_value.get_active_environment.return_value = mock_env
        mock_env.name = "test-env"

        cmd = EnvironmentCommands()
        args = Namespace(
            packages=["requests"],
            requirements=reqs_file,
            upgrade=False,
            target_env=None
        )

        with pytest.raises(SystemExit) as exc_info:
            with patch('builtins.print'):
                cmd.py_add(args)

        assert exc_info.value.code == 1

    @patch('comfydock_cli.env_commands.get_workspace_or_exit')
    def test_add_errors_with_neither_packages_nor_requirements(self, mock_workspace):
        """Should error when neither packages nor requirements file are specified."""
        mock_env = MagicMock()
        mock_workspace.return_value.get_active_environment.return_value = mock_env
        mock_env.name = "test-env"

        cmd = EnvironmentCommands()
        args = Namespace(
            packages=[],
            requirements=None,
            upgrade=False,
            target_env=None
        )

        with pytest.raises(SystemExit) as exc_info:
            with patch('builtins.print'):
                cmd.py_add(args)

        assert exc_info.value.code == 1

    @patch('comfydock_cli.env_commands.get_workspace_or_exit')
    def test_add_errors_with_nonexistent_requirements_file(self, mock_workspace):
        """Should error when requirements file doesn't exist."""
        from pathlib import Path

        mock_env = MagicMock()
        mock_workspace.return_value.get_active_environment.return_value = mock_env
        mock_env.name = "test-env"

        cmd = EnvironmentCommands()
        args = Namespace(
            packages=[],
            requirements=Path("nonexistent.txt"),
            upgrade=False,
            target_env=None
        )

        with pytest.raises(SystemExit) as exc_info:
            with patch('builtins.print'):
                cmd.py_add(args)

        assert exc_info.value.code == 1


class TestPyRemove:
    """Test 'cfd py remove' command handler."""

    @patch('comfydock_cli.env_commands.get_workspace_or_exit')
    def test_remove_single_package(self, mock_workspace):
        """Should call remove_dependencies with single package."""
        mock_env = MagicMock()
        mock_workspace.return_value.get_active_environment.return_value = mock_env
        mock_env.name = "test-env"
        mock_env.remove_dependencies.return_value = {
            'removed': ['requests'],
            'skipped': []
        }

        cmd = EnvironmentCommands()
        args = Namespace(
            packages=["requests"],
            target_env=None
        )

        with patch('builtins.print'):
            cmd.py_remove(args)

        mock_env.remove_dependencies.assert_called_once_with(["requests"])

    @patch('comfydock_cli.env_commands.get_workspace_or_exit')
    def test_remove_multiple_packages(self, mock_workspace):
        """Should call remove_dependencies with multiple packages."""
        mock_env = MagicMock()
        mock_workspace.return_value.get_active_environment.return_value = mock_env
        mock_env.name = "test-env"
        mock_env.remove_dependencies.return_value = {
            'removed': ['requests', 'pillow', 'tqdm'],
            'skipped': []
        }

        cmd = EnvironmentCommands()
        args = Namespace(
            packages=["requests", "pillow", "tqdm"],
            target_env=None
        )

        with patch('builtins.print'):
            cmd.py_remove(args)

        mock_env.remove_dependencies.assert_called_once_with(
            ["requests", "pillow", "tqdm"]
        )

    @patch('comfydock_cli.env_commands.get_workspace_or_exit')
    def test_remove_handles_uv_error(self, mock_workspace):
        """Should handle UVCommandError gracefully."""
        mock_env = MagicMock()
        mock_workspace.return_value.get_active_environment.return_value = mock_env
        mock_env.name = "test-env"
        mock_env.remove_dependencies.side_effect = UVCommandError(
            "Package resolution error",
            command=["uv", "remove", "requests"]
        )

        cmd = EnvironmentCommands()
        args = Namespace(
            packages=["requests"],
            target_env=None
        )

        with patch('builtins.print'):
            with pytest.raises(SystemExit) as exc_info:
                cmd.py_remove(args)

        assert exc_info.value.code == 1

    @patch('comfydock_cli.env_commands.get_workspace_or_exit')
    def test_remove_missing_package_succeeds(self, mock_workspace):
        """Should succeed gracefully when package doesn't exist."""
        mock_env = MagicMock()
        mock_workspace.return_value.get_active_environment.return_value = mock_env
        mock_env.name = "test-env"
        mock_env.remove_dependencies.return_value = {
            'removed': [],
            'skipped': ['nonexistent']
        }

        cmd = EnvironmentCommands()
        args = Namespace(
            packages=["nonexistent"],
            target_env=None
        )

        with patch('builtins.print') as mock_print:
            cmd.py_remove(args)

        # Should call remove_dependencies (which handles the filtering)
        mock_env.remove_dependencies.assert_called_once_with(["nonexistent"])

        # Should print informative message
        printed = ' '.join(str(call) for call in mock_print.call_args_list)
        assert "not in dependencies" in printed

    @patch('comfydock_cli.env_commands.get_workspace_or_exit')
    def test_remove_mixed_existing_and_missing(self, mock_workspace):
        """Should remove existing packages and skip missing ones."""
        mock_env = MagicMock()
        mock_workspace.return_value.get_active_environment.return_value = mock_env
        mock_env.name = "test-env"
        mock_env.remove_dependencies.return_value = {
            'removed': ['requests', 'pillow'],
            'skipped': ['nonexistent']
        }

        cmd = EnvironmentCommands()
        args = Namespace(
            packages=["requests", "nonexistent", "pillow"],
            target_env=None
        )

        with patch('builtins.print') as mock_print:
            cmd.py_remove(args)

        # Should call remove_dependencies with all packages (filtering happens in core)
        mock_env.remove_dependencies.assert_called_once_with(["requests", "nonexistent", "pillow"])

        # Should mention skipped packages
        printed = ' '.join(str(call) for call in mock_print.call_args_list)
        assert "Skipped" in printed
        assert "nonexistent" in printed


class TestPyList:
    """Test 'cfd py list' command handler."""

    @patch('comfydock_cli.env_commands.get_workspace_or_exit')
    def test_list_empty_dependencies(self, mock_workspace):
        """Should display message when no dependencies exist."""
        mock_env = MagicMock()
        mock_workspace.return_value.get_active_environment.return_value = mock_env
        mock_env.name = "test-env"
        mock_env.list_dependencies.return_value = {"dependencies": []}

        cmd = EnvironmentCommands()
        args = Namespace(target_env=None, all=False)

        with patch('builtins.print') as mock_print:
            cmd.py_list(args)

        # Verify "No project dependencies" was printed
        calls = [str(call) for call in mock_print.call_args_list]
        assert any("No project dependencies" in call for call in calls)

    @patch('comfydock_cli.env_commands.get_workspace_or_exit')
    def test_list_shows_dependencies(self, mock_workspace):
        """Should display all dependencies."""
        mock_env = MagicMock()
        mock_workspace.return_value.get_active_environment.return_value = mock_env
        mock_env.name = "test-env"
        mock_env.list_dependencies.return_value = {
            "dependencies": [
                "requests>=2.0.0",
                "pillow",
                "tqdm>=4.0.0"
            ]
        }

        cmd = EnvironmentCommands()
        args = Namespace(target_env=None, all=False)

        with patch('builtins.print') as mock_print:
            cmd.py_list(args)

        # Verify packages were printed
        calls = [str(call) for call in mock_print.call_args_list]
        output = "\n".join(calls)
        assert "requests>=2.0.0" in output
        assert "pillow" in output
        assert "tqdm>=4.0.0" in output

    @patch('comfydock_cli.env_commands.get_workspace_or_exit')
    def test_list_with_all_flag(self, mock_workspace):
        """Should display all dependencies including groups when --all is used."""
        mock_env = MagicMock()
        mock_workspace.return_value.get_active_environment.return_value = mock_env
        mock_env.name = "test-env"
        mock_env.list_dependencies.return_value = {
            "dependencies": ["requests>=2.0.0", "pillow"],
            "test-group": ["pytest", "pytest-cov"],
            "dev-group": ["black", "ruff"]
        }

        cmd = EnvironmentCommands()
        args = Namespace(target_env=None, all=True)

        with patch('builtins.print') as mock_print:
            cmd.py_list(args)

        # Verify all packages were printed
        calls = [str(call) for call in mock_print.call_args_list]
        output = "\n".join(calls)
        assert "requests>=2.0.0" in output
        assert "pillow" in output
        assert "pytest" in output
        assert "pytest-cov" in output
        assert "black" in output
        assert "ruff" in output
        # Verify group names appear
        assert "test-group" in output
        assert "dev-group" in output
