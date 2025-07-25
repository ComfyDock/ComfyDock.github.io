#!/usr/bin/env python3
"""
Test environment builder for ComfyUI migration testing
"""

import os
import subprocess
import shutil
import logging
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import tempfile


class TestEnvironmentBuilder:
    """Builds test ComfyUI environments"""
    
    def __init__(self):
        self.logger = logging.getLogger('migration_test.builder')
        # TODO: Make this configurable via args
        self.base_dir = Path(os.environ.get('COMFYUI_TEST_DIR', 
                                          '/home/akatzfey/projects/comfydock/testing/comfyui_repos'))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Load custom nodes configuration
        self.custom_nodes_config = self._load_custom_nodes_config()
        
    def _load_custom_nodes_config(self) -> Dict:
        """Load custom nodes configuration"""
        config_path = Path(__file__).parent.parent / 'config' / 'custom_nodes.yaml'
        if config_path.exists():
            try:
                import yaml
                with open(config_path, 'r') as f:
                    return yaml.safe_load(f).get('custom_nodes', {})
            except ImportError:
                self.logger.warning("PyYAML not installed, using empty custom nodes config")
                return {}
        return {}
        
    def _set_uv_environment(self, venv_path: Path, base_dir: Path) -> Dict[str, str]:
        """Set up UV environment variables"""
        env = os.environ.copy()
        env['UV_LINK_MODE'] = 'hardlink'
        env['UV_CACHE_DIR'] = str(base_dir / "uv_cache")
        env['UV_PYTHON_INSTALL_DIR'] = str(base_dir / "uv" / "python")
        env['VIRTUAL_ENV'] = str(venv_path)
        env['UV_PROJECT_ENVIRONMENT'] = str(venv_path)
        # Also set PATH to include venv bin directory
        bin_dir = venv_path / "bin"
        if not bin_dir.exists():
            bin_dir = venv_path / "Scripts"  # Windows
        env['PATH'] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"
        return env
        
    def create_environment(self, comfyui_version: Dict, python_version: str,
                          custom_nodes: List[str]) -> Path:
        """Create a complete test environment"""
        # Generate unique directory name
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        env_name = f"test_{timestamp}_{comfyui_version['version']}"
        env_dir = self.base_dir / env_name
        
        self.logger.info(f"Creating test environment: {env_dir}")
        
        try:
            # Create directory structure
            env_dir.mkdir(parents=True, exist_ok=True)
            
            # Clone ComfyUI
            self._clone_comfyui(env_dir, comfyui_version)
            
            # Create virtual environment with UV
            venv_path = self._create_venv_with_uv(env_dir, python_version)
            
            # Set up UV environment for all subsequent operations
            self.uv_env = self._set_uv_environment(venv_path, self.base_dir)
            
            # Install ComfyUI requirements
            self._install_comfyui_requirements(venv_path, env_dir)
            
            # Install custom nodes
            for node in custom_nodes:
                self._install_custom_node(venv_path, env_dir, node)
                
            # Verify installation
            self._verify_installation(venv_path, env_dir)
            
            self.logger.info(f"Environment created successfully: {env_dir}")
            return env_dir
            
        except Exception as e:
            self.logger.error(f"Failed to create environment: {e}", exc_info=True)
            # Clean up on failure
            if env_dir.exists():
                shutil.rmtree(env_dir, ignore_errors=True)
            raise
            
    def _clone_comfyui(self, env_dir: Path, comfyui_version: Dict):
        """Clone ComfyUI repository"""
        self.logger.info(f"Cloning ComfyUI {comfyui_version['version']}")
        
        comfyui_dir = env_dir / "ComfyUI"
        
        # Clone repository
        cmd = [
            'git', 'clone',
            '--depth', '1',
            '--branch', comfyui_version['git_ref'],
            'https://github.com/comfyanonymous/ComfyUI.git',
            str(comfyui_dir)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            # If cloning a tag failed, try without --branch
            if comfyui_version['git_ref'] != 'master':
                self.logger.warning("Tag clone failed, trying full clone...")
                cmd = [
                    'git', 'clone',
                    'https://github.com/comfyanonymous/ComfyUI.git',
                    str(comfyui_dir)
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise RuntimeError(f"Failed to clone ComfyUI: {result.stderr}")
                    
                # Checkout specific version
                result = subprocess.run(
                    ['git', 'checkout', comfyui_version['git_ref']],
                    cwd=str(comfyui_dir),
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    raise RuntimeError(f"Failed to checkout version: {result.stderr}")
            else:
                raise RuntimeError(f"Failed to clone ComfyUI: {result.stderr}")
                
    def _create_venv_with_uv(self, env_dir: Path, python_version: str) -> Path:
        """Create virtual environment using UV"""
        venv_path = env_dir / ".venv"
        
        self.logger.info(f"Creating virtual environment with UV and Python {python_version} at path {venv_path}")
        
        # Create venv with UV
        # TODO: This assumes the user env has uv installed
        cmd = ['uv', 'venv', '--python', python_version, str(venv_path)]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            # If specific version fails, try without version specification
            self.logger.warning(f"Failed to create venv with Python {python_version}, trying default Python")
            # TODO: This assumes the user env has uv installed
            cmd = ['uv', 'venv', str(venv_path)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"Failed to create venv with UV: {result.stderr}")
        
        # UV automatically manages pip, so no need to upgrade it
        self.logger.info(f"Virtual environment created at {venv_path}")
        
        return venv_path
        
    def _install_comfyui_requirements(self, venv_path: Path, env_dir: Path):
        """Install ComfyUI base requirements using UV"""
        self.logger.info("Installing ComfyUI requirements")
        
        req_file = env_dir / "ComfyUI" / "requirements.txt"
        
        if req_file.exists():
            # TODO: This assumes the user env has uv installed
            cmd = ['uv', 'pip', 'install', '-r', str(req_file)]
            result = subprocess.run(cmd, capture_output=True, text=True, env=self.uv_env)
            if result.returncode != 0:
                self.logger.error(f"Failed to install requirements: {result.stderr}")
                # Don't fail completely, some packages might be optional
                
    def _install_custom_node(self, venv_path: Path, env_dir: Path, node_name: str):
        """Install a single custom node with error handling"""
        self.logger.info(f"Installing custom node: {node_name}")
        
        node_config = self.custom_nodes_config.get(node_name, {})
        if not node_config:
            self.logger.warning(f"No configuration found for {node_name}, skipping")
            return
            
        custom_nodes_dir = env_dir / "ComfyUI" / "custom_nodes"
        custom_nodes_dir.mkdir(exist_ok=True)
        
        try:
            # Clone repository
            node_path = self._clone_node_repo(custom_nodes_dir, node_name, node_config)
            
            # Install based on method
            install_method = node_config.get('install_method', 'requirements')
            
            if install_method == 'requirements':
                self._install_node_requirements(venv_path, node_path)
            elif install_method == 'install_script':
                script = node_config.get('install_script', 'install.py')
                self._run_install_script(venv_path, node_path, script)
                
            # Install extra dependencies if specified
            extra_deps = node_config.get('extra_deps', [])
            if extra_deps:
                self._install_extra_deps(venv_path, extra_deps)
                
        except Exception as e:
            self.logger.error(f"Failed to install {node_name}: {e}")
            # Continue with other nodes
            
    def _clone_node_repo(self, custom_nodes_dir: Path, node_name: str, 
                        node_config: Dict) -> Path:
        """Clone custom node repository"""
        repo_url = node_config.get('repo')
        branch = node_config.get('branch', 'main')
        
        if not repo_url:
            raise ValueError(f"No repository URL for {node_name}")
            
        node_path = custom_nodes_dir / node_name
        
        cmd = [
            'git', 'clone',
            '--depth', '1',
            '--branch', branch,
            repo_url,
            str(node_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            # Try without branch specification
            cmd = ['git', 'clone', '--depth', '1', repo_url, str(node_path)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"Failed to clone {node_name}: {result.stderr}")
                
        return node_path
        
    def _install_node_requirements(self, venv_path: Path, node_path: Path):
        """Install requirements.txt from custom node using UV"""
        req_file = node_path / "requirements.txt"
        
        if not req_file.exists():
            self.logger.debug(f"No requirements.txt found in {node_path}")
            return
            
        cmd = ['uv', 'pip', 'install', '-r', str(req_file)]
        result = subprocess.run(cmd, capture_output=True, text=True, env=self.uv_env)
        
        if result.returncode != 0:
            self.logger.warning(f"Some requirements failed to install: {result.stderr}")
            
    def _run_install_script(self, venv_path: Path, node_path: Path, script_name: str):
        """Run custom install script using UV"""
        script_path = node_path / script_name
        
        if not script_path.exists():
            self.logger.warning(f"Install script not found: {script_path}")
            return
            
        # Run install script with UV
        cmd = ['uv', 'run', 'python', str(script_path)]
        result = subprocess.run(
            cmd,
            cwd=str(node_path),
            capture_output=True,
            text=True,
            env=self.uv_env
        )
        
        if result.returncode != 0:
            self.logger.warning(f"Install script failed: {result.stderr}")
            
    def _install_extra_deps(self, venv_path: Path, deps: List[str]):
        """Install extra system dependencies"""
        for dep in deps:
            if dep == 'ffmpeg':
                # Check if ffmpeg is available
                result = subprocess.run(['which', 'ffmpeg'], capture_output=True)
                if result.returncode != 0:
                    self.logger.warning("ffmpeg not found in system, some features may not work")
            else:
                self.logger.warning(f"Unknown system dependency: {dep}")
                
    def _verify_installation(self, venv_path: Path, env_dir: Path):
        """Verify the installation is working using UV"""
        self.logger.info("Verifying installation")
        
        # Try to import ComfyUI
        test_code = """
import sys
sys.path.insert(0, 'ComfyUI')
try:
    import main
    print("ComfyUI import successful")
except Exception as e:
    print(f"ComfyUI import failed: {e}")
    sys.exit(1)
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            test_file = f.name
            
        try:
            # Run with UV
            # cmd = ['uv', 'run', 'python', test_file]
            # result = subprocess.run(
            #     cmd,
            #     cwd=str(env_dir),
            #     capture_output=True,
            #     text=True,
            #     env=self.uv_env
            # )
            cmd = ['uv', 'run', 'python', 'ComfyUI/main.py', '--quick-test-for-ci']
            result = subprocess.run(
                cmd,
                cwd=str(env_dir),
                capture_output=True,
                text=True,
                env=self.uv_env
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Installation verification failed: {result.stdout} {result.stderr}")
                
        finally:
            os.unlink(test_file)
            
    def cleanup_old_environments(self, keep_last: int = 5):
        """Clean up old test environments"""
        self.logger.info(f"Cleaning up old environments (keeping last {keep_last})")
        
        # Get all test directories
        test_dirs = sorted(
            [d for d in self.base_dir.iterdir() if d.is_dir() and d.name.startswith('test_')],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        # Remove old directories
        for old_dir in test_dirs[keep_last:]:
            self.logger.info(f"Removing old environment: {old_dir}")
            shutil.rmtree(old_dir, ignore_errors=True)