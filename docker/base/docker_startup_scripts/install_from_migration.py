#!/usr/bin/env python3
"""
Python script to install ComfyUI environment from migration config v1.0
"""

import os
import sys
import json
import subprocess
import tarfile
import zipfile
import tempfile
import shutil
from typing import Dict, Any, Optional, Tuple, List
from urllib.request import urlretrieve

from utils.base_utils import Logger, CommandRunner, EnvironmentManager, PathManager
from utils.package_utils import PackageManager, PyTorchInstaller
from utils.git_utils import GitManager

# Import other installers directly
from install_comfyui import ComfyUIInstaller
from install_pytorch import PyTorchSetup


class MigrationInstaller:
    """Handles installation from migration configuration v1.0"""
    
    SCHEMA_VERSION = "1.0"
    
    def __init__(self, install_manager: bool = True):
        self.install_manager = install_manager
        self.container_id = EnvironmentManager.get_container_id()
        self.comfyui_directory = EnvironmentManager.get_comfyui_directory()
        self.config_path = self._find_migration_config()
    
    def _find_migration_config(self) -> Optional[str]:
        """Find migration config file"""
        # Priority: container-specific location, then general migration mount
        locations = [
            f"/env/{self.container_id}/comfyui_migration.json",
            "/migration/comfyui_migration.json"
        ]
        
        for config_path in locations:
            if os.path.exists(config_path):
                return config_path
        
        return None
    
    def load_migration_config(self) -> Dict[str, Any]:
        """Load and validate migration configuration"""
        if not self.config_path:
            raise RuntimeError("No migration config found")
            
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                
            # Validate schema version
            if config.get('schema_version') != self.SCHEMA_VERSION:
                raise ValueError(f"Unsupported schema version: {config.get('schema_version')}")
                
            return config
        except (json.JSONDecodeError, IOError) as e:
            Logger.error(f"Error loading migration config: {e}")
            sys.exit(1)
    
    def extract_system_info(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Extract system information from config"""
        system_info = config.get('system_info', {})
        
        # Extract Python major.minor version from full version
        python_version = system_info.get('python_version', '3.12.8')
        python_major_minor = '.'.join(python_version.split('.')[:2])
        
        # Determine CUDA version for PyTorch index
        cuda_version = system_info.get('cuda_version')
        torch_version = system_info.get('torch_version', '')
        
        # Extract CUDA version from torch version string if present
        pytorch_cuda_version = 'cpu'
        if cuda_version and 'cu' in torch_version:
            # Extract cuXXX from torch version
            import re
            match = re.search(r'cu(\d+)', torch_version)
            if match:
                pytorch_cuda_version = f"cu{match.group(1)}"
        
        # Determine if nightly or stable
        pytorch_version = 'nightly' if 'dev' in torch_version else 'stable'
        
        return {
            'python_version': python_version,
            'python_major_minor': python_major_minor,
            'cuda_version': cuda_version or 'CPU-only',
            'torch_version': torch_version,
            'comfyui_version': system_info.get('comfyui_version', 'master'),
            'pytorch_cuda_version': pytorch_cuda_version,
            'pytorch_version': pytorch_version
        }
    
    def check_comfyui_exists(self) -> Tuple[bool, str]:
        """Check if ComfyUI already exists and return location"""
        # Check configured directory
        if (os.path.exists(self.comfyui_directory) and 
            os.path.exists(os.path.join(self.comfyui_directory, 'main.py'))):
            return True, self.comfyui_directory
        
        # Check symlink location
        if (os.path.islink('/app/ComfyUI') and 
            os.path.exists('/app/ComfyUI/main.py')):
            return True, '/app/ComfyUI'
        
        return False, ''
    
    def handle_existing_comfyui(self, location: str, expected_version: str) -> None:
        """Handle existing ComfyUI installation"""
        Logger.log(f"ComfyUI found at {location}")
        Logger.log("ComfyUI already exists (likely mounted from host)")
        Logger.log("Skipping ComfyUI installation")
        
        # Get version info
        git_dir = os.path.join(location, '.git')
        if os.path.exists(git_dir):
            git_manager = GitManager(location)
            current_version = git_manager.get_current_version()
            if current_version:
                Logger.log(f"Current ComfyUI version: {current_version}")
                
                # Warn about version mismatch
                if current_version != expected_version:
                    Logger.warning(f"Existing ComfyUI version ({current_version}) "
                                 f"differs from migration config ({expected_version})")
        
        # Ensure ComfyUI-Manager is installed if requested
        if self.install_manager:
            Logger.log("Checking for ComfyUI-Manager...")
            self._ensure_comfyui_manager(location)
        
        # Ensure symlink exists
        if not os.path.islink('/app/ComfyUI') and location != '/app/ComfyUI':
            PathManager.ensure_symlink(self.comfyui_directory, '/app/ComfyUI')
    
    def _ensure_comfyui_manager(self, comfyui_location: str) -> None:
        """Ensure ComfyUI-Manager is installed"""
        manager_path = os.path.join(comfyui_location, 'custom_nodes', 'ComfyUI-Manager')
        
        if not os.path.exists(manager_path):
            Logger.log("Installing ComfyUI-Manager...")
            try:
                GitManager.clone(
                    'https://github.com/ltdrdata/ComfyUI-Manager.git', 
                    manager_path
                )
            except subprocess.CalledProcessError:
                Logger.warning("Failed to install ComfyUI-Manager")
    
    def install_pytorch(self, config: Dict[str, Any], package_manager: PackageManager) -> None:
        """Install PyTorch packages from migration config"""
        pytorch_config = config.get('dependencies', {}).get('pytorch', {})
        
        if not pytorch_config:
            Logger.log("No PyTorch configuration found in migration config")
            Logger.log("Falling back to default PyTorch installation")
            pytorch_setup = PyTorchSetup()
            pytorch_setup.run()
            return
        
        index_url = pytorch_config.get('index_url', '')
        packages = pytorch_config.get('packages', {})
        
        if not packages:
            Logger.log("No PyTorch packages specified")
            return
        
        Logger.log(f"Installing PyTorch from: {index_url}")
        Logger.log(f"Packages: {', '.join(packages.keys())}")
        
        # Build package specifications with versions
        package_specs = [f"{name}=={version}" for name, version in packages.items()]
        
        # Install using the specified index URL
        if index_url:
            package_manager.install_packages(package_specs, index_url=index_url)
        else:
            package_manager.install_packages(package_specs)
        
        Logger.log("PyTorch packages installed successfully")
    
    def install_packages(self, config: Dict[str, Any], package_manager: PackageManager) -> None:
        """Install regular PyPI packages"""
        packages = config.get('dependencies', {}).get('packages', {})
        
        if not packages:
            Logger.log("No additional packages to install")
            return
        
        Logger.log(f"Installing {len(packages)} packages from PyPI...")
        
        # Build package specifications with versions
        package_specs = [f"{name}=={version}" for name, version in packages.items()]
        
        # Install in batches to avoid command line length limits
        batch_size = 50
        for i in range(0, len(package_specs), batch_size):
            batch = package_specs[i:i + batch_size]
            package_manager.install_packages(batch)
        
        Logger.log("PyPI packages installed successfully")
    
    def install_editable_packages(self, config: Dict[str, Any], package_manager: PackageManager) -> None:
        """Install editable packages"""
        editable_installs = config.get('dependencies', {}).get('editable_installs', [])
        
        if not editable_installs:
            return
        
        Logger.log(f"Installing {len(editable_installs)} editable packages...")
        
        for editable in editable_installs:
            try:
                package_manager.install_packages([editable])
            except subprocess.CalledProcessError:
                Logger.warning(f"Failed to install editable package: {editable}")
    
    def install_git_requirements(self, config: Dict[str, Any], package_manager: PackageManager) -> None:
        """Install git-based requirements"""
        git_requirements = config.get('dependencies', {}).get('git_requirements', [])
        
        if not git_requirements:
            return
        
        Logger.log(f"Installing {len(git_requirements)} git-based packages...")
        
        for git_req in git_requirements:
            try:
                package_manager.install_packages([git_req])
            except subprocess.CalledProcessError:
                Logger.warning(f"Failed to install git requirement: {git_req}")
    
    def download_and_extract_archive(self, url: str, destination: str) -> None:
        """Download and extract archive (tar.gz or zip)"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            Logger.log(f"Downloading {url}...")
            urlretrieve(url, tmp_file.name)
            
            # Determine archive type and extract
            if url.endswith('.tar.gz') or url.endswith('.tgz'):
                with tarfile.open(tmp_file.name, 'r:gz') as tar:
                    # Get the root directory name from the archive
                    members = tar.getmembers()
                    if members:
                        root_dir = members[0].name.split('/')[0]
                        
                        # Extract to temp directory
                        with tempfile.TemporaryDirectory() as extract_dir:
                            tar.extractall(extract_dir)
                            
                            # Move contents to destination
                            extracted_path = os.path.join(extract_dir, root_dir)
                            if os.path.exists(extracted_path):
                                shutil.move(extracted_path, destination)
                            else:
                                # If no root directory, move all contents
                                for item in os.listdir(extract_dir):
                                    shutil.move(os.path.join(extract_dir, item), destination)
            
            elif url.endswith('.zip'):
                with zipfile.ZipFile(tmp_file.name, 'r') as zip_file:
                    # Similar logic for zip files
                    namelist = zip_file.namelist()
                    if namelist:
                        root_dir = namelist[0].split('/')[0]
                        
                        with tempfile.TemporaryDirectory() as extract_dir:
                            zip_file.extractall(extract_dir)
                            
                            extracted_path = os.path.join(extract_dir, root_dir)
                            if os.path.exists(extracted_path):
                                shutil.move(extracted_path, destination)
                            else:
                                for item in os.listdir(extract_dir):
                                    shutil.move(os.path.join(extract_dir, item), destination)
            else:
                raise ValueError(f"Unsupported archive format: {url}")
            
            os.unlink(tmp_file.name)
    
    def install_custom_nodes(self, config: Dict[str, Any], package_manager: PackageManager) -> None:
        """Install custom nodes according to their install methods"""
        custom_nodes = config.get('custom_nodes', [])
        
        if not custom_nodes:
            Logger.log("No custom nodes to install")
            return
        
        Logger.log(f"Installing {len(custom_nodes)} custom nodes...")
        custom_nodes_dir = '/app/ComfyUI/custom_nodes'
        os.makedirs(custom_nodes_dir, exist_ok=True)
        
        for node in custom_nodes:
            name = node.get('name')
            install_method = node.get('install_method')
            url = node.get('url')
            
            if not all([name, install_method, url]):
                Logger.warning(f"Invalid custom node configuration: {node}")
                continue
            
            node_path = os.path.join(custom_nodes_dir, name)
            
            # Skip if already exists
            if os.path.exists(node_path):
                Logger.log(f"   - {name} already exists, skipping")
                continue
            
            Logger.log(f"   - Installing {name} via {install_method}")
            
            try:
                if install_method == 'archive':
                    # Download and extract archive
                    self.download_and_extract_archive(url, node_path)
                
                elif install_method == 'git':
                    # Clone git repository
                    ref = node.get('ref')
                    GitManager.clone(url, node_path)
                    
                    if ref:
                        # Checkout specific ref
                        git_manager = GitManager(node_path)
                        CommandRunner.run(['git', 'checkout', ref], cwd=node_path)
                
                elif install_method == 'local':
                    # Copy from local path
                    if os.path.exists(url):
                        shutil.copytree(url, node_path)
                    else:
                        Logger.warning(f"Local path not found: {url}")
                        continue
                
                else:
                    Logger.warning(f"Unknown install method: {install_method}")
                    continue
                
                # Run post-install script if specified
                if node.get('has_post_install'):
                    self.run_post_install(node_path, package_manager)
                
                # Install requirements if present
                req_file = os.path.join(node_path, 'requirements.txt')
                if os.path.exists(req_file):
                    Logger.log(f"     Installing requirements for {name}")
                    try:
                        package_manager.install_requirements(req_file)
                    except subprocess.CalledProcessError:
                        Logger.warning(f"Failed to install requirements for {name}")
                
            except Exception as e:
                Logger.warning(f"Failed to install {name}: {e}")
    
    def run_post_install(self, node_path: str, package_manager: PackageManager) -> None:
        """Run post-install script for a custom node"""
        # Check for install.py first, then setup.py
        for script in ['install.py', 'setup.py']:
            script_path = os.path.join(node_path, script)
            if os.path.exists(script_path):
                Logger.log(f"     Running {script}")
                try:
                    if package_manager.use_uv:
                        CommandRunner.run(['uv', 'run', 'python', script_path], cwd=node_path)
                    else:
                        CommandRunner.run(['python', script_path], cwd=node_path)
                    return
                except subprocess.CalledProcessError:
                    Logger.warning(f"Post-install script failed: {script}")
    
    def install_default_requirements(self, package_manager: PackageManager) -> None:
        """Install default ComfyUI requirements as fallback"""
        Logger.log("Installing default ComfyUI requirements...")
        
        # Install ComfyUI requirements
        comfyui_req = '/app/ComfyUI/requirements.txt'
        if os.path.exists(comfyui_req):
            # Filter out PyTorch packages if using uv
            if package_manager.use_uv:
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                    with open(comfyui_req, 'r') as orig:
                        for line in orig:
                            line = line.strip()
                            if line and not any(pkg in line.lower() for pkg in 
                                              ['torch', 'torchvision', 'torchaudio', 'torchsde', 'nvidia-', 'triton']):
                                f.write(line + '\n')
                    temp_req = f.name
                
                try:
                    if os.path.getsize(temp_req) > 0:
                        package_manager.install_requirements(temp_req)
                finally:
                    os.unlink(temp_req)
            else:
                package_manager.install_requirements(comfyui_req)
        
        # Install Manager requirements if present
        manager_req = '/app/ComfyUI/custom_nodes/ComfyUI-Manager/requirements.txt'
        if os.path.exists(manager_req):
            Logger.log("Installing ComfyUI-Manager requirements...")
            package_manager.install_requirements(manager_req)
    
    def verify_installation(self, use_uv: bool = True) -> None:
        """Verify the installation"""
        Logger.log("Verifying installation...")
        os.chdir('/app/ComfyUI')
        
        # Determine Python command
        if use_uv:
            python_cmd = ['uv', 'run', 'python']
        else:
            python_cmd = ['python3'] if CommandRunner.command_exists('python3') else ['python']
        
        # Test ComfyUI imports
        Logger.log(f"Testing ComfyUI imports with: {' '.join(python_cmd)}")
        
        try:
            import_test = "import sys; sys.path.insert(0, '.'); import folder_paths"
            CommandRunner.run(python_cmd + ['-c', import_test])
            Logger.log("✓ ComfyUI imports successfully")
        except subprocess.CalledProcessError:
            Logger.warning("✗ ComfyUI import test failed")
        
        # Check PyTorch
        try:
            pytorch_test = "import torch; print(f'✓ PyTorch {torch.__version__} installed')"
            result = CommandRunner.run(python_cmd + ['-c', pytorch_test])
            print(result.stdout.strip())
        except subprocess.CalledProcessError:
            Logger.warning("✗ PyTorch not installed")
    
    def run(self) -> None:
        """Main execution method"""
        Logger.log("=== ComfyUI Migration Installer ===")
        Logger.log("Checking for migration config...")
        
        # Check if migration config exists
        if not self.config_path:
            Logger.log("No migration config found")
            Logger.log("Falling back to default installation")
            return
        
        Logger.log(f"Found migration config: {self.config_path}")
        
        try:
            # Load and validate config
            config = self.load_migration_config()
            system_info = self.extract_system_info(config)
            
            # Display migration details
            Logger.log("\nMigration Configuration:")
            Logger.log(f"  Schema Version: {config.get('schema_version')}")
            Logger.log(f"  Python: {system_info['python_version']}")
            Logger.log(f"  CUDA: {system_info['cuda_version']}")
            Logger.log(f"  PyTorch: {system_info['torch_version']}")
            Logger.log(f"  ComfyUI: {system_info['comfyui_version']}")
            
            # Set environment variables
            os.environ.update({
                'PYTHON_VERSION': system_info['python_major_minor'],
                'COMFYUI_VERSION': system_info['comfyui_version'],
                'COMFYUI_PATH': self.comfyui_directory,
                'PYTORCH_CUDA_VERSION': system_info['pytorch_cuda_version'],
                'PYTORCH_VERSION': system_info['pytorch_version']
            })
            
            # Determine package manager (default to uv)
            use_uv = os.environ.get('USE_UV', 'true').lower() == 'true'
            package_manager = PackageManager(use_uv=use_uv)
            
            # Check if ComfyUI already exists
            comfyui_exists, comfyui_location = self.check_comfyui_exists()
            
            if comfyui_exists:
                self.handle_existing_comfyui(comfyui_location, system_info['comfyui_version'])
            else:
                # Install ComfyUI
                Logger.log("\nInstalling ComfyUI...")
                comfyui_installer = ComfyUIInstaller()
                comfyui_installer.run()
            
            # Install dependencies in order
            Logger.log("\n=== Installing Dependencies ===")
            
            # 1. Install PyTorch
            self.install_pytorch(config, package_manager)
            
            # 2. Install regular packages
            self.install_packages(config, package_manager)
            
            # 3. Install editable packages
            self.install_editable_packages(config, package_manager)
            
            # 4. Install git requirements
            self.install_git_requirements(config, package_manager)
            
            # 5. Install custom nodes
            self.install_custom_nodes(config, package_manager)
            
            # 6. Install default requirements if no packages were specified
            if not config.get('dependencies', {}).get('packages'):
                self.install_default_requirements(package_manager)
            
            # Verify installation
            Logger.log("\n=== Verification ===")
            self.verify_installation(use_uv)
            
            Logger.log("\n✓ Migration-based installation completed successfully!")
        
        except subprocess.CalledProcessError as e:
            Logger.error(f"Error during installation: {e}")
            if e.stdout:
                Logger.log(f"stdout: {e.stdout}")
            if e.stderr:
                Logger.log(f"stderr: {e.stderr}")
            sys.exit(1)
        
        except Exception as e:
            Logger.error(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """Main function"""
    installer = MigrationInstaller()
    installer.run()


if __name__ == '__main__':
    main()