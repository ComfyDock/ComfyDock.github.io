#!/usr/bin/env python3
"""
Python script to install ComfyUI at runtime
"""

import os
import sys
import subprocess
from pathlib import Path

from utils.base_utils import Logger, CommandRunner, EnvironmentManager, PathManager
from utils.git_utils import GitManager


class ComfyUIInstaller:
    """Handles ComfyUI installation"""
    
    def __init__(self, install_manager: bool = True):
        self.comfyui_version = os.environ.get('COMFYUI_VERSION', 'master')
        self.container_id = EnvironmentManager.get_container_id()
        self.comfyui_path = os.environ.get('COMFYUI_PATH', f'/env/{self.container_id}/ComfyUI')
        self.install_manager = install_manager
        
    def install_or_update_comfyui(self) -> None:
        """Install or update ComfyUI"""
        repo_url = "https://github.com/comfyanonymous/ComfyUI.git"
        
        Logger.log(f"install_or_update_comfyui called with install_manager: {self.install_manager}")
        
        if Path(self.comfyui_path, '.git').exists():
            Logger.log(f"ComfyUI already exists at {self.comfyui_path}")
            
            git_manager = GitManager(self.comfyui_path)
            
            # Fetch latest changes
            git_manager.fetch_all()
            
            # Get current version
            current_version = git_manager.get_current_version()
            if current_version:
                Logger.log(f"Current version: {current_version}")
            
            # Check if we need to switch versions
            if self.comfyui_version != current_version:
                Logger.log(f"Switching to version: {self.comfyui_version}")
                
                if not git_manager.checkout_version(self.comfyui_version):
                    Logger.warning(f"Version {self.comfyui_version} not found, staying on current version")
            else:
                Logger.log("Already on requested version")
        
        else:
            Logger.log("Cloning ComfyUI...")
            
            # Create parent directory
            Path(self.comfyui_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Clone repository
            GitManager.clone(repo_url, self.comfyui_path)
            
            git_manager = GitManager(self.comfyui_path)
            
            # Fetch all branches and tags
            git_manager.fetch_all()
            
            # Checkout specific version
            if not git_manager.checkout_version(self.comfyui_version):
                if self.comfyui_version != 'master':
                    Logger.log(f"Version {self.comfyui_version} not found, using master")
                CommandRunner.run(['git', 'checkout', '-b', 'master', 'origin/master'], cwd=self.comfyui_path)
    
            # Install ComfyUI-Manager if requested
            if self.install_manager:
                Logger.log("ComfyUI installer: Installing ComfyUI-Manager...")
                self.install_comfyui_manager()
                
    def install_comfyui_manager(self) -> None:
        """Install ComfyUI-Manager"""
        Logger.log(f"install_comfyui_manager called with install_manager: {self.install_manager}")
        
        manager_path = Path(self.comfyui_path) / 'custom_nodes' / 'ComfyUI-Manager'
        manager_url = "https://github.com/ltdrdata/ComfyUI-Manager.git"
        
        if not manager_path.exists():
            Logger.log("ComfyUI manager: Installing ComfyUI-Manager...")
            manager_path.parent.mkdir(parents=True, exist_ok=True)
            GitManager.clone(manager_url, str(manager_path))
        else:
            Logger.log("ComfyUI-Manager already installed")
            try:
                CommandRunner.run(['git', 'pull', 'origin', 'main'], cwd=str(manager_path), check=False)
            except subprocess.SubprocessError:
                Logger.warning("Failed to update ComfyUI-Manager")
    
    def create_symlink(self) -> None:
        """Create symlink from /app/ComfyUI to actual installation"""
        PathManager.ensure_symlink(self.comfyui_path, '/app/ComfyUI')
    
    def run(self) -> None:
        """Main execution method"""
        Logger.log(f"Installing ComfyUI version: {self.comfyui_version}")
        Logger.log(f"Installation path: {self.comfyui_path}")
        
        try:
            # Install or update ComfyUI
            self.install_or_update_comfyui()
            
            # Create symlink
            self.create_symlink()
            
            Logger.log("ComfyUI installation completed")
        
        except subprocess.CalledProcessError as e:
            Logger.error(f"Error during installation: {e}")
            if e.stdout:
                Logger.log(f"stdout: {e.stdout}")
            if e.stderr:
                Logger.log(f"stderr: {e.stderr}")
            sys.exit(1)
        
        except Exception as e:
            Logger.error(f"Unexpected error: {e}")
            sys.exit(1)


def main():
    """Main function"""
    installer = ComfyUIInstaller()
    installer.run()


if __name__ == '__main__':
    main()