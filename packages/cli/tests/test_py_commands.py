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
            upgrade=False,
            target_env=None
        )

        # Execute
        with patch('builtins.print'):
            cmd.py_add(args)

        # Verify
        mock_env.add_dependencies.assert_called_once_with(
            ["requests"],
            upgrade=False
        )

    @patch('comfydock_cli.env_commands.get_workspace_or_exit')
    def test_add_multiple_packages(self, mock_workspace):
        """Should call add_dependencies with multiple packages."""
        mock_env = MagicMock()
        mock_workspace.return_value.get_active_environment.return_value = mock_env
        mock_env.name = "test-env"

        cmd = EnvironmentCommands()
        args = Namespace(
            packages=["requests", "pillow", "tqdm"],
            upgrade=False,
            target_env=None
        )

        with patch('builtins.print'):
            cmd.py_add(args)

        mock_env.add_dependencies.assert_called_once_with(
            ["requests", "pillow", "tqdm"],
            upgrade=False
        )

    @patch('comfydock_cli.env_commands.get_workspace_or_exit')
    def test_add_with_upgrade_flag(self, mock_workspace):
        """Should pass upgrade=True when --upgrade is specified."""
        mock_env = MagicMock()
        mock_workspace.return_value.get_active_environment.return_value = mock_env
        mock_env.name = "test-env"

        cmd = EnvironmentCommands()
        args = Namespace(
            packages=["requests"],
            upgrade=True,
            target_env=None
        )

        with patch('builtins.print'):
            cmd.py_add(args)

        mock_env.add_dependencies.assert_called_once_with(
            ["requests"],
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
            upgrade=False,
            target_env=None
        )

        with patch('builtins.print'):
            with pytest.raises(SystemExit) as exc_info:
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
        mock_env.remove_dependencies.return_value = "Removed: requests"

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
            "Package not installed",
            command=["uv", "remove", "nonexistent"]
        )

        cmd = EnvironmentCommands()
        args = Namespace(
            packages=["nonexistent"],
            target_env=None
        )

        with patch('builtins.print'):
            with pytest.raises(SystemExit) as exc_info:
                cmd.py_remove(args)

        assert exc_info.value.code == 1


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
