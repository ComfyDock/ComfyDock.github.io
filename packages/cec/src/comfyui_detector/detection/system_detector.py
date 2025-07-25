"""System detector for Python, CUDA, and PyTorch detection."""

import platform
from pathlib import Path
from typing import Dict, Optional

from ..utils import (
    find_python_executable, run_python_command, detect_python_version,
    detect_cuda_version, detect_pytorch_version
)
from ..logging_config import get_logger


class SystemDetector:
    """Detects system-level dependencies like Python, CUDA, and PyTorch."""
    
    def __init__(self, comfyui_path: Path, python_hint: Path = None):
        self.logger = get_logger(__name__)
        self.comfyui_path = Path(comfyui_path).resolve()
        self.python_hint = Path(python_hint) if python_hint else None
        self.python_executable = None
        self.system_info = {}
        
        # Log the python hint for debugging
        if self.python_hint:
            self.logger.info(f"System detector initialized with python hint: {self.python_hint}")
            print(f"System detector python hint: {self.python_hint}")
        else:
            self.logger.info("System detector initialized without python hint")
        
    def detect_all(self) -> Dict:
        """Detect all system information."""
        self.logger.info("Starting system detection...")
        
        # Find Python executable
        self.find_python_executable()
        
        # Detect versions
        self.detect_python_version()
        self.detect_cuda_version()
        self.detect_pytorch_version()
        
        # Add platform info
        self.system_info['platform'] = platform.platform()
        self.system_info['architecture'] = platform.machine()
        
        return self.system_info
    
    def find_python_executable(self) -> Optional[Path]:
        """Find the Python executable and virtual environment used by ComfyUI."""
        self.python_executable = find_python_executable(
            self.comfyui_path, 
            python_hint=self.python_hint
        )
        # Remove assertion - we can work without a venv if we have a valid python executable
        if not self.python_executable:
            raise RuntimeError("Could not find a Python executable that can run ComfyUI")
        return self.python_executable
    
    def run_python_command(self, code: str) -> Optional[str]:
        """Run Python code in the ComfyUI environment and return output."""
        if not self.python_executable:
            return None
        return run_python_command(code, self.python_executable, self.comfyui_path)
    
    def detect_python_version(self) -> str:
        """Detect the Python version being used by ComfyUI."""
        version_info = detect_python_version(self.python_executable, self.comfyui_path)
        self.system_info.update(version_info)
        return version_info['python_version']
    
    def detect_cuda_version(self) -> Optional[str]:
        """Detect CUDA version using nvidia-smi."""
        cuda_version = detect_cuda_version()
        self.system_info['cuda_version'] = cuda_version
        return cuda_version
    
    def detect_pytorch_version(self) -> Optional[Dict]:
        """Detect PyTorch and related library versions in ComfyUI environment."""
        pytorch_info = detect_pytorch_version(self.python_executable, self.comfyui_path)
        
        if pytorch_info and 'error' not in pytorch_info:
            self.system_info['torch_version'] = pytorch_info.get('torch')
            self.system_info['cuda_torch_version'] = pytorch_info.get('cuda_torch_version')
        
        self.system_info['pytorch_info'] = pytorch_info
        return pytorch_info