#!/usr/bin/env python3
"""
Error handling and recovery strategies for migration testing
"""

import logging
import subprocess
from typing import Dict
from pathlib import Path


class ErrorRecoveryHandler:
    """Implements fallback strategies for common errors"""
    
    def __init__(self):
        self.logger = logging.getLogger('migration_test.recovery')
        
        # Recovery strategy mapping
        self.recovery_strategies = {
            'package_installation_error': [
                self._try_without_version_pin,
                self._try_alternative_source,
                self._try_with_pip_upgrade,
                self._skip_optional_dependency
            ],
            'git_clone_error': [
                self._try_alternative_branch,
                self._try_shallow_clone,
                self._try_archive_download
            ],
            'import_error': [
                self._install_missing_dependency,
                self._downgrade_conflicting_package,
                self._rebuild_package
            ],
            'permission_error': [
                self._fix_permissions,
                self._run_as_user
            ],
            'cuda_error': [
                self._reinstall_cuda_packages,
                self._fallback_to_cpu
            ]
        }
        
    def handle_error(self, error_type: str, error_context: Dict) -> bool:
        """Try to recover from an error using available strategies"""
        strategies = self.recovery_strategies.get(error_type, [])
        
        self.logger.info(f"Attempting recovery for {error_type} with {len(strategies)} strategies")
        
        for i, strategy in enumerate(strategies):
            try:
                self.logger.info(f"Trying recovery strategy {i+1}/{len(strategies)}: {strategy.__name__}")
                success = strategy(error_context)
                if success:
                    self.logger.info(f"Recovery successful with strategy: {strategy.__name__}")
                    return True
                else:
                    self.logger.warning(f"Recovery strategy failed: {strategy.__name__}")
            except Exception as e:
                self.logger.error(f"Recovery strategy error: {e}")
                continue
                
        self.logger.error(f"All recovery strategies failed for {error_type}")
        return False
        
    def _try_without_version_pin(self, context: Dict) -> bool:
        """Try installing package without specific version"""
        package_name = context.get('package_name')
        if not package_name:
            return False
            
        # Remove version specifier
        base_package = package_name.split('==')[0].split('>=')[0].split('<=')[0]
        
        try:
            result = subprocess.run(
                ['pip', 'install', base_package],
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode == 0
        except Exception:
            return False
            
    def _try_alternative_source(self, context: Dict) -> bool:
        """Try installing from alternative package sources"""
        package_name = context.get('package_name')
        if not package_name:
            return False
            
        # Try different sources
        sources = [
            ['pip', 'install', '--index-url', 'https://pypi.org/simple/', package_name],
            ['pip', 'install', '--extra-index-url', 'https://download.pytorch.org/whl/cu121', package_name],
            ['conda', 'install', '-y', package_name],
        ]
        
        for source_cmd in sources:
            try:
                result = subprocess.run(source_cmd, capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    self.logger.info(f"Successfully installed {package_name} from alternative source")
                    return True
            except Exception:
                continue
                
        return False
        
    def _try_with_pip_upgrade(self, context: Dict) -> bool:
        """Try installing with pip upgrade flags"""
        package_name = context.get('package_name')
        if not package_name:
            return False
            
        try:
            result = subprocess.run(
                ['pip', 'install', '--upgrade', '--force-reinstall', package_name],
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode == 0
        except Exception:
            return False
            
    def _skip_optional_dependency(self, context: Dict) -> bool:
        """Skip optional dependency if it's not critical"""
        package_name = context.get('package_name')
        optional_packages = {
            'opencv-python', 'opencv-contrib-python', 'mediapipe',
            'insightface', 'onnxruntime-gpu', 'xformers'
        }
        
        if package_name and any(opt in package_name.lower() for opt in optional_packages):
            self.logger.info(f"Skipping optional dependency: {package_name}")
            return True
            
        return False
        
    def _try_alternative_branch(self, context: Dict) -> bool:
        """Try cloning from alternative git branch"""
        repo_url = context.get('repo_url')
        target_dir = context.get('target_dir')
        
        if not repo_url or not target_dir:
            return False
            
        # Try common alternative branches
        branches = ['main', 'master', 'develop', 'dev']
        
        for branch in branches:
            try:
                result = subprocess.run(
                    ['git', 'clone', '--branch', branch, '--depth', '1', repo_url, target_dir],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                if result.returncode == 0:
                    self.logger.info(f"Successfully cloned from branch: {branch}")
                    return True
            except Exception:
                continue
                
        return False
        
    def _try_shallow_clone(self, context: Dict) -> bool:
        """Try shallow clone without specific branch"""
        repo_url = context.get('repo_url')
        target_dir = context.get('target_dir')
        
        if not repo_url or not target_dir:
            return False
            
        try:
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', repo_url, target_dir],
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode == 0
        except Exception:
            return False
            
    def _try_archive_download(self, context: Dict) -> bool:
        """Try downloading repository as archive"""
        repo_url = context.get('repo_url')
        target_dir = context.get('target_dir')
        
        if not repo_url or not target_dir:
            return False
            
        # Convert GitHub URL to archive URL
        if 'github.com' in repo_url:
            archive_url = repo_url.replace('.git', '') + '/archive/refs/heads/main.zip'
            try:
                result = subprocess.run(
                    ['wget', '-O', '/tmp/repo.zip', archive_url],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                if result.returncode == 0:
                    # Extract archive
                    result = subprocess.run(
                        ['unzip', '/tmp/repo.zip', '-d', str(Path(target_dir).parent)],
                        capture_output=True,
                        text=True
                    )
                    return result.returncode == 0
            except Exception:
                pass
                
        return False
        
    def _install_missing_dependency(self, context: Dict) -> bool:
        """Install missing dependency causing import error"""
        error_message = context.get('error_message', '')
        
        # Extract module name from import error
        import_patterns = [
            r"No module named '(.+)'",
            r"cannot import name '(.+)'",
            r"ImportError: (.+)"
        ]
        
        import re
        for pattern in import_patterns:
            match = re.search(pattern, error_message)
            if match:
                module_name = match.group(1)
                
                # Common module to package mapping
                module_to_package = {
                    'cv2': 'opencv-python',
                    'PIL': 'Pillow',
                    'skimage': 'scikit-image',
                    'yaml': 'PyYAML',
                    'requests': 'requests',
                    'numpy': 'numpy',
                    'torch': 'torch',
                    'torchvision': 'torchvision',
                }
                
                package_name = module_to_package.get(module_name, module_name)
                
                try:
                    result = subprocess.run(
                        ['pip', 'install', package_name],
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    return result.returncode == 0
                except Exception:
                    pass
                    
        return False
        
    def _downgrade_conflicting_package(self, context: Dict) -> bool:
        """Downgrade package causing conflict"""
        package_name = context.get('package_name')
        if not package_name:
            return False
            
        # Try common stable versions
        versions = ['==1.0.0', '==0.9.0', '==0.8.0']
        
        for version in versions:
            try:
                result = subprocess.run(
                    ['pip', 'install', f'{package_name}{version}'],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                if result.returncode == 0:
                    return True
            except Exception:
                continue
                
        return False
        
    def _rebuild_package(self, context: Dict) -> bool:
        """Rebuild package from source"""
        package_name = context.get('package_name')
        if not package_name:
            return False
            
        try:
            # Uninstall and reinstall
            subprocess.run(['pip', 'uninstall', '-y', package_name], capture_output=True)
            result = subprocess.run(
                ['pip', 'install', '--no-binary', package_name, package_name],
                capture_output=True,
                text=True,
                timeout=600
            )
            return result.returncode == 0
        except Exception:
            return False
            
    def _fix_permissions(self, context: Dict) -> bool:
        """Fix file permissions"""
        file_path = context.get('file_path')
        if not file_path:
            return False
            
        try:
            result = subprocess.run(
                ['chmod', '-R', '755', file_path],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
            
    def _run_as_user(self, context: Dict) -> bool:
        """Run command as different user"""
        # This would need container-specific implementation
        return False
        
    def _reinstall_cuda_packages(self, context: Dict) -> bool:
        """Reinstall CUDA packages"""
        cuda_packages = ['torch', 'torchvision', 'torchaudio']
        
        try:
            # Uninstall CUDA packages
            for package in cuda_packages:
                subprocess.run(['pip', 'uninstall', '-y', package], capture_output=True)
                
            # Reinstall with CUDA support
            result = subprocess.run(
                ['pip', 'install', 'torch', 'torchvision', 'torchaudio', 
                 '--index-url', 'https://download.pytorch.org/whl/cu121'],
                capture_output=True,
                text=True,
                timeout=600
            )
            return result.returncode == 0
        except Exception:
            return False
            
    def _fallback_to_cpu(self, context: Dict) -> bool:
        """Fallback to CPU-only packages"""
        cuda_packages = ['torch', 'torchvision', 'torchaudio']
        
        try:
            # Uninstall CUDA packages
            for package in cuda_packages:
                subprocess.run(['pip', 'uninstall', '-y', package], capture_output=True)
                
            # Install CPU-only versions
            result = subprocess.run(
                ['pip', 'install', 'torch', 'torchvision', 'torchaudio', '--index-url', 
                 'https://download.pytorch.org/whl/cpu'],
                capture_output=True,
                text=True,
                timeout=600
            )
            return result.returncode == 0
        except Exception:
            return False