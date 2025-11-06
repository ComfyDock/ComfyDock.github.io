"""Test graceful handling of optional dependency groups during sync.

Tests that optional dependency groups (prefixed with 'optional-') can fail
without breaking the entire sync operation, while non-optional groups must succeed.
"""

import pytest
from unittest.mock import Mock, patch
from comfydock_core.models.exceptions import UVCommandError


class TestOptionalDependencyGroups:
    """Test progressive dependency group installation with graceful fallback."""

    def test_sync_with_failing_optional_group_continues(self, test_env):
        """When optional group fails, sync should continue and track the failure."""
        # ARRANGE: Add optional and required groups to pyproject
        config = test_env.pyproject.load()

        # Add optional group (will simulate failure)
        config.setdefault("dependency-groups", {})
        config["dependency-groups"]["optional-cuda"] = ["sageattention>=2.2.0"]

        # Add node dependency group (must succeed)
        config["dependency-groups"]["comfyui-test-node"] = ["numpy>=1.20.0"]

        test_env.pyproject.save(config)

        # ACT: Mock uv.sync to fail for optional-cuda but succeed for others
        from comfydock_core.integrations.uv_command import CommandResult

        def mock_sync(verbose=False, **flags):
            # Fail if trying to sync optional-cuda group
            if flags.get('group') == 'optional-cuda':
                raise UVCommandError(
                    "Failed to install sageattention",
                    command=["uv", "sync", "--group", "optional-cuda"],
                    stderr="error: failed building wheel for sageattention",
                    stdout="",
                    returncode=1
                )
            # Otherwise return success
            return CommandResult(stdout="", stderr="", returncode=0, success=True)

        with patch.object(test_env.uv_manager.uv, 'sync', side_effect=mock_sync):
            result = test_env.sync()

        # ASSERT: Sync should succeed overall despite optional group failure
        assert result.success, "Sync should succeed despite optional group failure"
        assert result.packages_synced, "Base packages should be installed"

        # Failed optional groups should be tracked
        assert len(result.dependency_groups_failed) == 1
        assert result.dependency_groups_failed[0][0] == "optional-cuda"
        assert "sageattention" in result.dependency_groups_failed[0][1]

        # Required groups should succeed
        assert "comfyui-test-node" in result.dependency_groups_installed

    def test_sync_with_failing_required_group_fails(self, test_env):
        """When non-optional group fails, sync should fail entirely."""
        # ARRANGE: Add required node dependency group
        config = test_env.pyproject.load()
        config.setdefault("dependency-groups", {})
        config["dependency-groups"]["comfyui-critical-node"] = ["nonexistent-package>=1.0.0"]
        test_env.pyproject.save(config)

        # ACT: Mock to fail required group
        from comfydock_core.integrations.uv_command import CommandResult

        def mock_sync(verbose=False, **flags):
            if flags.get('group') == 'comfyui-critical-node':
                raise UVCommandError(
                    "Failed to install nonexistent-package",
                    command=["uv", "sync", "--group", "comfyui-critical-node"],
                    stderr="error: package not found: nonexistent-package",
                    stdout="",
                    returncode=1
                )
            return CommandResult(stdout="", stderr="", returncode=0, success=True)

        with patch.object(test_env.uv_manager.uv, 'sync', side_effect=mock_sync):
            result = test_env.sync()

        # ASSERT: Sync should fail (result.success = False)
        assert not result.success, "Sync should fail when required group fails"
        assert len(result.errors) > 0, "Should have error messages"
        assert any("nonexistent-package" in err for err in result.errors)

    def test_sync_installs_groups_progressively(self, test_env):
        """Groups should be installed one-by-one, not all-at-once."""
        # ARRANGE: Add multiple groups
        config = test_env.pyproject.load()
        config.setdefault("dependency-groups", {})
        config["dependency-groups"]["optional-accel"] = ["pillow>=9.0.0"]
        config["dependency-groups"]["optional-extra"] = ["pyyaml>=5.0"]
        config["dependency-groups"]["comfyui-node-a"] = ["requests>=2.0.0"]
        test_env.pyproject.save(config)

        # ACT: Track sync calls
        from comfydock_core.integrations.uv_command import CommandResult
        sync_calls = []

        def track_sync(verbose=False, **flags):
            sync_calls.append(flags.copy())
            return CommandResult(stdout="", stderr="", returncode=0, success=True)

        with patch.object(test_env.uv_manager.uv, 'sync', side_effect=track_sync):
            result = test_env.sync()

        # ASSERT: Should have separate sync calls for each group
        # 1. Base dependencies (no group flag)
        # 2. Each optional group individually
        # 3. Each required group individually
        assert len(sync_calls) >= 4, f"Expected at least 4 sync calls, got {len(sync_calls)}"

        # First call should be base deps
        assert sync_calls[0].get('group') is None, "First sync should be base dependencies"

        # Subsequent calls should have group flags
        group_calls = [call for call in sync_calls if call.get('group')]
        assert len(group_calls) >= 3, "Should have group-specific sync calls"

        groups_synced = {call['group'] for call in group_calls}
        assert 'optional-accel' in groups_synced
        assert 'optional-extra' in groups_synced
        assert 'comfyui-node-a' in groups_synced

    def test_sync_result_tracks_all_group_outcomes(self, test_env):
        """SyncResult should track which groups succeeded and failed."""
        # ARRANGE: Mix of optional and required groups
        config = test_env.pyproject.load()
        config.setdefault("dependency-groups", {})
        config["dependency-groups"]["optional-good"] = ["pyyaml>=5.0"]
        config["dependency-groups"]["optional-bad"] = ["fake-package>=1.0"]
        config["dependency-groups"]["comfyui-node"] = ["requests>=2.0.0"]
        test_env.pyproject.save(config)

        # ACT: Mock to fail optional-bad
        from comfydock_core.integrations.uv_command import CommandResult

        def selective_mock_sync(verbose=False, **flags):
            if flags.get('group') == 'optional-bad':
                raise UVCommandError(
                    "Failed to install fake-package",
                    command=["uv", "sync", "--group", "optional-bad"],
                    stderr="error: package not found",
                    stdout="",
                    returncode=1
                )
            return CommandResult(stdout="", stderr="", returncode=0, success=True)

        with patch.object(test_env.uv_manager.uv, 'sync', side_effect=selective_mock_sync):
            result = test_env.sync()

        # ASSERT: Should track both successes and failures
        assert result.success, "Overall sync should succeed"

        # Successful groups
        assert "optional-good" in result.dependency_groups_installed
        assert "comfyui-node" in result.dependency_groups_installed

        # Failed groups
        assert len(result.dependency_groups_failed) == 1
        failed_group, error = result.dependency_groups_failed[0]
        assert failed_group == "optional-bad"
        assert "fake-package" in error.lower() or "not found" in error.lower()

    def test_all_optional_groups_fail_sync_still_succeeds(self, test_env):
        """If all optional groups fail but base deps succeed, sync should succeed."""
        # ARRANGE: Only optional groups, all will fail
        config = test_env.pyproject.load()
        config.setdefault("dependency-groups", {})
        config["dependency-groups"]["optional-a"] = ["fake-a>=1.0"]
        config["dependency-groups"]["optional-b"] = ["fake-b>=1.0"]
        test_env.pyproject.save(config)

        # ACT: Mock to fail all optional groups
        from comfydock_core.integrations.uv_command import CommandResult

        def fail_optional_sync(verbose=False, **flags):
            if flags.get('group', '').startswith('optional-'):
                raise UVCommandError(
                    "Failed",
                    command=["uv", "sync"],
                    stderr="error",
                    stdout="",
                    returncode=1
                )
            return CommandResult(stdout="", stderr="", returncode=0, success=True)

        with patch.object(test_env.uv_manager.uv, 'sync', side_effect=fail_optional_sync):
            result = test_env.sync()

        # ASSERT
        assert result.success, "Sync should succeed even if all optional groups fail"
        assert len(result.dependency_groups_failed) == 2
        assert result.packages_synced, "Base dependencies should be installed"

    def test_empty_dependency_groups_works(self, test_env):
        """Sync should work fine with no dependency groups."""
        # ARRANGE: No dependency groups
        config = test_env.pyproject.load()
        config.pop("dependency-groups", None)
        test_env.pyproject.save(config)

        # ACT
        result = test_env.sync()

        # ASSERT
        assert result.success
        assert result.packages_synced
        assert len(result.dependency_groups_installed) == 0
        assert len(result.dependency_groups_failed) == 0
