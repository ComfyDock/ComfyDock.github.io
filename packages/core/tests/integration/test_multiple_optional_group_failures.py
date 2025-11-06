"""Test handling of multiple optional dependency group failures during sync."""
import pytest
from unittest.mock import MagicMock, patch

from comfydock_core.core.environment import Environment
from comfydock_core.models.exceptions import UVCommandError
from comfydock_core.models.sync import SyncResult


@pytest.fixture
def mock_environment(tmp_path):
    """Create a minimal environment mock for testing progressive sync."""
    env = MagicMock(spec=Environment)
    env.cec_path = tmp_path / ".cec"
    env.cec_path.mkdir()

    # Create a real pyproject manager mock
    env.pyproject = MagicMock()
    env.pyproject.dependencies = MagicMock()

    # Track removed groups
    removed_groups = []

    def mock_remove_group(group):
        removed_groups.append(group)

    def mock_get_groups():
        # Start with all groups, remove as we go
        all_groups = {
            'optional-cuda': ['sageattention>=2.2.0'],
            'optional-tensorrt': ['tensorrt>=8.0.0'],
            'optional-xformers': ['xformers>=0.0.20'],
            'working-group': ['httpx'],
        }
        for group in removed_groups:
            all_groups.pop(group, None)
        return all_groups

    env.pyproject.dependencies.remove_group.side_effect = mock_remove_group
    env.pyproject.dependencies.get_groups.side_effect = mock_get_groups

    # UV manager mock
    env.uv_manager = MagicMock()

    # Attach the real method
    env._sync_dependencies_progressive = Environment._sync_dependencies_progressive.__get__(env, Environment)

    return env, removed_groups


def test_multiple_optional_groups_fail_sequentially(mock_environment):
    """Test that multiple failing optional groups are handled iteratively."""
    env, removed_groups = mock_environment

    # Simulate three sequential failures, then success
    failure_sequence = [
        # First call fails on optional-cuda
        UVCommandError(
            "Build failed",
            command=['uv', 'sync'],
            stderr="help: `sageattention` was included because `test:optional-cuda` depends on sageattention"
        ),
        # Second call fails on optional-tensorrt
        UVCommandError(
            "Build failed",
            command=['uv', 'sync'],
            stderr="help: `tensorrt` was included because `test:optional-tensorrt` depends on tensorrt"
        ),
        # Third call fails on optional-xformers
        UVCommandError(
            "Build failed",
            command=['uv', 'sync'],
            stderr="help: `xformers` was included because `test:optional-xformers` depends on xformers"
        ),
        # Fourth call succeeds
        None,
    ]

    call_count = [0]

    def mock_sync(**kwargs):
        if kwargs.get('no_default_groups'):
            # Base dependency install
            if call_count[0] < len(failure_sequence):
                error = failure_sequence[call_count[0]]
                call_count[0] += 1
                if error:
                    raise error
        # Otherwise success

    env.uv_manager.sync_project.side_effect = mock_sync

    # Create lockfile (will be deleted on each retry)
    lockfile = env.cec_path / "uv.lock"
    lockfile.touch()

    result = SyncResult()
    env._sync_dependencies_progressive(result, dry_run=False, callbacks=None)

    # Verify all three optional groups were removed
    assert len(removed_groups) == 3
    assert 'optional-cuda' in removed_groups
    assert 'optional-tensorrt' in removed_groups
    assert 'optional-xformers' in removed_groups

    # Verify result tracks all failures
    assert len(result.dependency_groups_failed) == 3
    failed_group_names = [g for g, _ in result.dependency_groups_failed]
    assert 'optional-cuda' in failed_group_names
    assert 'optional-tensorrt' in failed_group_names
    assert 'optional-xformers' in failed_group_names

    # Verify base install succeeded
    assert result.packages_synced is True

    # Verify we made exactly 4 attempts (3 failures + 1 success)
    assert call_count[0] == 4


def test_max_retries_prevents_infinite_loop(mock_environment):
    """Test that we don't loop forever if groups keep failing."""
    env, removed_groups = mock_environment

    # Always fail with a different optional group
    optional_groups = [
        'optional-a', 'optional-b', 'optional-c', 'optional-d', 'optional-e',
        'optional-f', 'optional-g', 'optional-h', 'optional-i', 'optional-j',
        'optional-k'  # More than MAX_RETRIES
    ]

    call_count = [0]

    def mock_sync(**kwargs):
        if kwargs.get('no_default_groups'):
            group = optional_groups[min(call_count[0], len(optional_groups) - 1)]
            call_count[0] += 1
            raise UVCommandError(
                "Build failed",
                command=['uv', 'sync'],
                stderr=f"help: `pkg` was included because `test:{group}` depends on pkg"
            )

    env.uv_manager.sync_project.side_effect = mock_sync

    # Create lockfile
    lockfile = env.cec_path / "uv.lock"
    lockfile.touch()

    result = SyncResult()

    # Should raise RuntimeError after MAX_RETRIES (10)
    with pytest.raises(RuntimeError, match="Failed to install base dependencies after 10 attempts"):
        env._sync_dependencies_progressive(result, dry_run=False, callbacks=None)

    # Should have attempted exactly MAX_RETRIES times
    assert call_count[0] == 10


def test_non_optional_group_failure_stops_immediately(mock_environment):
    """Test that failures in non-optional groups fail immediately without retry."""
    env, removed_groups = mock_environment

    # Fail with a required group
    def mock_sync(**kwargs):
        if kwargs.get('no_default_groups'):
            raise UVCommandError(
                "Build failed",
                command=['uv', 'sync'],
                stderr="help: `pkg` was included because `test:required-node-group` depends on pkg"
            )

    env.uv_manager.sync_project.side_effect = mock_sync

    lockfile = env.cec_path / "uv.lock"
    lockfile.touch()

    result = SyncResult()

    # Should raise immediately without retry
    with pytest.raises(UVCommandError):
        env._sync_dependencies_progressive(result, dry_run=False, callbacks=None)

    # No groups should have been removed
    assert len(removed_groups) == 0

    # Lockfile should still exist (not deleted)
    assert lockfile.exists()


def test_lockfile_deleted_on_each_retry(mock_environment):
    """Test that uv.lock is deleted before each retry to force re-resolution."""
    env, removed_groups = mock_environment

    failure_then_success = [
        UVCommandError(
            "Build failed",
            command=['uv', 'sync'],
            stderr="help: `pkg` was included because `test:optional-fail` depends on pkg"
        ),
        None,  # Success
    ]

    call_count = [0]
    lockfile_deleted = [False]

    def mock_sync(**kwargs):
        if kwargs.get('no_default_groups'):
            # Check if lockfile exists before each call after first
            lockfile = env.cec_path / "uv.lock"
            if call_count[0] > 0 and not lockfile.exists():
                lockfile_deleted[0] = True

            if call_count[0] < len(failure_then_success):
                error = failure_then_success[call_count[0]]
                call_count[0] += 1
                if error:
                    raise error

    env.uv_manager.sync_project.side_effect = mock_sync

    # Create initial lockfile
    lockfile = env.cec_path / "uv.lock"
    lockfile.touch()

    result = SyncResult()
    env._sync_dependencies_progressive(result, dry_run=False, callbacks=None)

    # Verify lockfile was deleted during retry
    assert lockfile_deleted[0] is True
