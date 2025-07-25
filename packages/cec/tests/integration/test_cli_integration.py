"""
Integration tests using CLI commands.

Tests the full workflow by calling the CLI commands directly as subprocess calls.
"""
import json
import pytest
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any


class TestCLIIntegration:
    """Integration tests using CLI commands."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture 
    def original_environment_path(self):
        """Path to the original test environment."""
        return Path("test_data/environments/original/test_1/ComfyUI")
    
    @pytest.fixture
    def uv_cache_path(self):
        """Path to UV cache directory.""" 
        return Path("test_data/environments/uv_cache")
    
    @pytest.fixture
    def python_install_path(self):
        """Path to Python installation cache."""
        return Path("test_data/environments/uv/python")
    
    def normalize_manifest_for_comparison(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize manifest for comparison by removing CUDA suffixes from PyTorch versions.
        
        This handles the expected difference where original environments may have
        torch==2.7.1 but recreated environments have torch==2.7.1+cu126.
        """
        normalized = manifest.copy()
        
        # Normalize PyTorch versions by removing CUDA suffixes
        if "dependencies" in normalized and "pytorch" in normalized["dependencies"]:
            pytorch_packages = normalized["dependencies"]["pytorch"]["packages"]
            for package, version in pytorch_packages.items():
                # Remove CUDA suffix (e.g., "2.7.1+cu126" -> "2.7.1")
                if "+" in version:
                    pytorch_packages[package] = version.split("+")[0]
        
        return normalized
    
    def run_cec_command(self, args: list, cwd: Path = None) -> subprocess.CompletedProcess:
        """Run a cec CLI command and return the result."""
        cmd = ["uv", "run", "cec"] + args
        result = subprocess.run(
            cmd,
            cwd=cwd or Path.cwd(),
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        return result
    
    def test_detect_recreate_detect_cycle(
        self,
        temp_dir: Path,
        original_environment_path: Path,
        uv_cache_path: Path,
        python_install_path: Path
    ):
        """
        Test the full environment replication cycle using CLI commands:
        1. cec detect original environment -> generate manifest1
        2. cec recreate environment from manifest1 
        3. cec detect recreated environment -> generate manifest2
        4. Compare manifest1 and manifest2 (should be equivalent)
        """
        # Ensure original environment exists
        assert original_environment_path.exists(), f"Original environment not found at {original_environment_path}"
        
        # Step 1: Detect original environment
        print(f"Step 1: Detecting original environment at {original_environment_path}")
        
        original_manifest_dir = temp_dir / "original_manifest"
        original_manifest_dir.mkdir()
        
        detect_args = [
            "detect",
            str(original_environment_path),
            "--output-dir", str(original_manifest_dir)
        ]
        
        result = self.run_cec_command(detect_args)
        assert result.returncode == 0, f"Detection failed: {result.stderr}"
        
        original_manifest_path = original_manifest_dir / "comfyui_migration.json"
        assert original_manifest_path.exists(), "Original manifest was not generated"
        
        # Load original manifest
        with open(original_manifest_path, 'r') as f:
            original_manifest = json.load(f)
        
        print(f"✓ Original manifest generated with {len(original_manifest['dependencies']['packages'])} packages")
        
        # Step 2: Recreate environment from manifest
        print("Step 2: Recreating environment from manifest")
        
        recreated_env_path = temp_dir / "recreated_environment"
        
        recreate_args = [
            "recreate",
            str(original_manifest_path),
            str(recreated_env_path),
            "--uv-cache-path", str(uv_cache_path),
            "--python-install-path", str(python_install_path)
        ]
        
        result = self.run_cec_command(recreate_args)
        assert result.returncode == 0, f"Recreation failed: {result.stderr}"
        
        # Check that ComfyUI was installed
        recreated_comfyui_path = recreated_env_path / "ComfyUI"
        assert recreated_comfyui_path.exists(), "ComfyUI was not installed in recreated environment"
        assert (recreated_comfyui_path / "main.py").exists(), "ComfyUI main.py not found"
        
        print("✓ Environment recreated successfully")
        
        # Step 3: Detect recreated environment  
        print("Step 3: Detecting recreated environment")
        
        recreated_manifest_dir = temp_dir / "recreated_manifest"
        recreated_manifest_dir.mkdir()
        
        detect_recreated_args = [
            "detect", 
            str(recreated_comfyui_path),
            "--output-dir", str(recreated_manifest_dir)
        ]
        
        result = self.run_cec_command(detect_recreated_args)
        assert result.returncode == 0, f"Recreated environment detection failed: {result.stderr}"
        
        recreated_manifest_path = recreated_manifest_dir / "comfyui_migration.json"
        assert recreated_manifest_path.exists(), "Recreated environment manifest was not generated"
        
        # Load recreated manifest
        with open(recreated_manifest_path, 'r') as f:
            recreated_manifest = json.load(f)
        
        print(f"✓ Recreated manifest generated with {len(recreated_manifest['dependencies']['packages'])} packages")
        
        # Step 4: Compare manifests
        print("Step 4: Comparing manifests")
        
        # Normalize both manifests for comparison (removes CUDA suffixes)
        normalized_original = self.normalize_manifest_for_comparison(original_manifest)
        normalized_recreated = self.normalize_manifest_for_comparison(recreated_manifest)
        
        # Compare key fields
        assert normalized_original["schema_version"] == normalized_recreated["schema_version"]
        
        # System info should be mostly the same (Python, CUDA versions)
        orig_system = normalized_original["system_info"]
        rec_system = normalized_recreated["system_info"]
        
        assert orig_system["python_version"] == rec_system["python_version"]
        assert orig_system["cuda_version"] == rec_system["cuda_version"]
        assert orig_system["comfyui_version"] == rec_system["comfyui_version"]
        
        # Dependencies should match after normalization
        orig_deps = normalized_original["dependencies"]
        rec_deps = normalized_recreated["dependencies"]
        
        assert orig_deps["packages"] == rec_deps["packages"], "Regular packages don't match"
        assert orig_deps["pytorch"]["packages"] == rec_deps["pytorch"]["packages"], "PyTorch packages don't match after normalization"
        
        # Custom nodes should match (should be empty for this test)
        assert normalized_original["custom_nodes"] == normalized_recreated["custom_nodes"]
        
        print("✓ Manifests match after normalization - environment replication successful!")
        print("🎉 Integration test passed: Environment replication cycle completed successfully!")


if __name__ == "__main__":
    # Allow running the test directly
    pytest.main([__file__, "-v"])