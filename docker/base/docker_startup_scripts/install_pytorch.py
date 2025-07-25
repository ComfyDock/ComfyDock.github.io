#!/usr/bin/env python3
"""
Python script to install PyTorch with correct CUDA version
"""

import os
import sys
import subprocess

from utils.base_utils import Logger, CommandRunner
from utils.package_utils import PackageManager, PyTorchInstaller


class PyTorchSetup:
    """Handles PyTorch installation"""
    
    def __init__(self):
        self.pytorch_version = os.environ.get('PYTORCH_VERSION', 'stable')
        self.pytorch_cuda_version = os.environ.get('PYTORCH_CUDA_VERSION', 'cu124')
        self.use_uv = os.environ.get('USE_UV', 'true').lower()
    
    def verify_installation(self) -> None:
        """Verify PyTorch installation"""
        Logger.log("Verifying PyTorch installation...")
        
        verification_script = """
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    try:
        print(f'GPU: {torch.cuda.get_device_name(0)}')
    except:
        print('GPU: Unable to get device name')
"""
        
        try:
            result = CommandRunner.run(['python', '-c', verification_script])
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            Logger.error(f"Verification failed: {e}")
            if e.stderr:
                Logger.log(f"Error: {e.stderr}")
    
    def run(self) -> None:
        """Main execution method"""
        Logger.log("Installing PyTorch...")
        Logger.log(f"   Version: {self.pytorch_version}")
        Logger.log(f"   CUDA: {self.pytorch_cuda_version}")
        
        # Determine index URL
        index_url = PyTorchInstaller.get_pytorch_index_url(
            self.pytorch_version, 
            self.pytorch_cuda_version
        )
        Logger.log(f"Using PyTorch index: {index_url}")
        
        try:
            # Create package manager
            package_manager = PackageManager(use_uv=(self.use_uv != 'false'))
            
            # Install PyTorch packages
            packages = ['torch', 'torchvision', 'torchaudio']
            package_manager.install_packages(
                packages, 
                index_url=index_url, 
                pre=(self.pytorch_version == 'nightly')
            )
            
            # Verify installation
            self.verify_installation()
            
            Logger.log("PyTorch installation completed")
        
        except subprocess.CalledProcessError as e:
            Logger.error(f"Error during PyTorch installation: {e}")
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
    setup = PyTorchSetup()
    setup.run()


if __name__ == '__main__':
    main()