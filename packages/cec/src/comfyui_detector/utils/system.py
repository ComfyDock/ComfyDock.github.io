"""System detection utilities."""

import json
import platform
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .version import is_pytorch_package, normalize_package_name
from ..logging_config import get_logger
from ..common import run_command
from ..exceptions import PackageDetectionError
from ..integrations.uv import UVInterface

logger = get_logger(__name__)


def validate_python_runs_comfyui(python_exe: Path, comfyui_path: Path) -> bool:
    """Validate that a Python executable can run ComfyUI."""
    try:
        # First, just check if we can run Python and it's a valid executable
        result = run_command(
            [str(python_exe), "-c", "import sys; print(sys.version)"],
            timeout=5
        )
        if result.returncode != 0:
            logger.debug(f"Python executable not valid: {python_exe}")
            return False
            
        # Try to import torch as a proxy for ComfyUI compatibility
        # This is more reliable than trying to run main.py which might have other dependencies
        result = run_command(
            [str(python_exe), "-c", "import torch; print('torch ok')"],
            cwd=comfyui_path,
            timeout=10
        )
        
        if result.returncode == 0:
            logger.info(f"Python executable can import torch: {python_exe}")
            return True
        else:
            # If torch import fails, still accept the Python if it's in a venv near ComfyUI
            # as packages might not be installed yet
            python_path = Path(python_exe).resolve()
            comfyui_parent = comfyui_path.parent
            
            # Check if the python is in a virtual environment related to ComfyUI
            if any(parent in str(python_path) for parent in [str(comfyui_path), str(comfyui_parent)]):
                logger.info(f"Python executable is in ComfyUI-related venv: {python_exe}")
                return True
                
            logger.debug(f"Python executable cannot import torch and not in ComfyUI venv: {python_exe}")
            return False
            
    except Exception as e:
        logger.debug(f"Python validation failed: {e}")
        return False


def find_python_executable(comfyui_path: Path, python_hint: Path = None) -> Optional[Path]:
    """
    Find the Python executable and virtual environment used by ComfyUI.
    
    Args:
        comfyui_path: Path to ComfyUI directory
        python_hint: Direct path to Python executable (if provided by user)
    
    Returns:
        Path to python_executable
    """
    # 1. If user provided python path, validate and use it
    if python_hint and python_hint.exists():
        logger.info(f"Validating user-provided Python executable: {python_hint}")
        # For user-provided path, be more lenient - just check it's a valid Python
        try:
            result = run_command(
                [str(python_hint), "-c", "import sys; print(sys.executable)"],
                timeout=5
            )
            if result.returncode == 0:
                logger.info(f"User-provided Python executable is valid: {python_hint}")
                return python_hint
            else:
                logger.warning(f"User-provided Python executable failed validation: {python_hint}")
        except Exception as e:
            logger.warning(f"Error validating user-provided Python: {e}")
    
    # 2. Check for virtual environments in standard locations relative to ComfyUI
    # Check common venv locations
    venv_candidates = [
        comfyui_path / "venv",
        comfyui_path / ".venv", 
        comfyui_path / "env",
        comfyui_path.parent / "venv",
        comfyui_path.parent / ".venv",
    ]

    for venv_path in venv_candidates:
        # Check for Python in different locations based on OS
        if platform.system() == "Windows":
            python_paths = [
                venv_path / "Scripts" / "python.exe",
                venv_path / "python.exe",
            ]
        else:
            python_paths = [
                venv_path / "bin" / "python",
                venv_path / "bin" / "python3",
            ]
        
        for python_path in python_paths:
            if python_path.exists():
                logger.info(f"Found Python executable: {python_path}")
                logger.info(f"Found virtual environment: {venv_path}")
                return python_path
    
    # Check if there's a .venv file pointing to a venv
    venv_file = comfyui_path / ".venv"
    if venv_file.exists() and venv_file.is_file():
        try:
            venv_path = Path(venv_file.read_text().strip())
            if venv_path.exists():
                if platform.system() == "Windows":
                    python_executable = venv_path / "Scripts" / "python.exe"
                else:
                    python_executable = venv_path / "bin" / "python"
                if python_executable.exists():
                    logger.info(f"Found Python executable via .venv file: {python_executable}")
                    logger.info(f"Found virtual environment: {venv_path}")
                    return python_executable
        except Exception:
            pass
    
    # If no venv found, check if ComfyUI can run with system Python
    logger.warning("No virtual environment found, checking system Python...")
    
    # Try to run ComfyUI's main.py with --help to see if it works
    try:
        result = run_command(
            [sys.executable, str(comfyui_path / "main.py"), "--help"],
            timeout=5
        )
        if result.returncode == 0:
            python_executable = Path(sys.executable)
            logger.info(f"ComfyUI appears to work with system Python: {sys.executable}")
            return python_executable
    except Exception:
        pass
    
    logger.warning("Could not determine Python executable for ComfyUI")
    return Path(sys.executable)


def run_python_command(code: str, python_executable: Path, comfyui_path: Path) -> Optional[str]:
    """Run Python code in the ComfyUI environment and return output."""
    try:
        result = run_command(
            [str(python_executable), "-c", code],
            cwd=comfyui_path,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            logger.error(f"Error running Python command: {result.stderr}")
            return None
    except Exception as e:
        logger.error(f"Exception running Python command: {e}")
        return None


def detect_python_version(python_executable: Path, comfyui_path: Path) -> Dict[str, str]:
    """Detect the Python version being used by ComfyUI."""
    code = "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
    python_version = run_python_command(code, python_executable, comfyui_path)
    
    if python_version:
        major_minor = '.'.join(python_version.split('.')[:2])
        logger.info(f"Python version: {python_version}")
    else:
        # Fallback to current Python
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        major_minor = f"{sys.version_info.major}.{sys.version_info.minor}"
        logger.warning(f"Using fallback Python version: {python_version}")
    
    return {
        'python_version': python_version,
        'python_major_minor': major_minor
    }


def detect_cuda_version() -> Optional[str]:
    """Detect CUDA version using nvidia-smi."""
    try:
        result = run_command(['nvidia-smi'])
        if result.returncode == 0:
            # Parse CUDA version from nvidia-smi output
            match = re.search(r'CUDA Version:\s*(\d+\.\d+)', result.stdout)
            if match:
                cuda_version = match.group(1)
                logger.info(f"CUDA version: {cuda_version}")
                return cuda_version
    except Exception as e:
        logger.debug(f"Could not detect CUDA: {e}")
    
    logger.info("No CUDA detected (CPU-only mode)")
    return None


def detect_pytorch_version(python_executable: Path, comfyui_path: Path) -> Optional[Dict]:
    """Detect PyTorch and related library versions in ComfyUI environment."""
    # Check if PyTorch is installed in the ComfyUI environment
    code = """
import json
try:
    import torch
    info = {
        'torch': torch.__version__,
        'cuda_available': torch.cuda.is_available(),
        'cuda_torch_version': torch.version.cuda if torch.cuda.is_available() else None
    }
    
    # Try to detect torchvision and torchaudio
    try:
        import torchvision
        info['torchvision'] = torchvision.__version__
    except ImportError:
        pass
        
    try:
        import torchaudio
        info['torchaudio'] = torchaudio.__version__
    except ImportError:
        pass
        
    print(json.dumps(info))
except ImportError:
    print(json.dumps({'error': 'PyTorch not installed'}))
"""
    
    output = run_python_command(code, python_executable, comfyui_path)
    if output:
        try:
            pytorch_info = json.loads(output)
            if 'error' not in pytorch_info:
                logger.info(f"PyTorch version: {pytorch_info.get('torch')}")
                if pytorch_info.get('cuda_torch_version'):
                    logger.info(f"PyTorch CUDA: {pytorch_info.get('cuda_torch_version')}")
            else:
                logger.warning("PyTorch not found in ComfyUI environment")
            return pytorch_info
        except json.JSONDecodeError:
            logger.warning("Could not parse PyTorch information")
    
    return None


def extract_packages_with_uv(python_executable: Path, 
                           comfyui_path: Path, pytorch_package_names: set) -> Tuple[Dict[str, str], Dict[str, str], List[str]]:
    """
    Extract installed packages using uv from the Python environment.
    
    Returns:
        Tuple of (pip_packages, pytorch_packages, editable_installs)
    """
    pip_packages = {}
    pytorch_packages = {}
    editable_installs = []
    
    if not python_executable or not python_executable.exists():
        logger.warning("No valid Python executable found, cannot extract packages")
        return pip_packages, pytorch_packages, editable_installs
    
    logger.info(f"Using uv to extract packages from Python: {python_executable}")
    
    try:
        # Use the new UVInterface
        logger.debug(f"python_executable: {python_executable}")
        logger.debug(f"comfyui_path: {comfyui_path}")
        
        uv = UVInterface()
        # Use python parameter instead of venv_path for more flexibility
        result = uv.list_packages(python=python_executable, format="freeze")
        
        logger.debug(f"result.output: {result.output}")
        
        if not result.success:
            raise Exception(f"Failed to list packages: {result.error}")
        
        # Parse the output to get package list
        packages = uv._parse_pip_list_output(result.output, "freeze")
        
        for package in packages:
            if package.is_editable:
                # Construct editable install line format
                editable_installs.append(f"-e {package.name}")
            else:
                # Clean up package name
                clean_name = normalize_package_name(package.name)
                
                # Separate PyTorch packages
                if is_pytorch_package(clean_name, pytorch_package_names):
                    pytorch_packages[clean_name] = package.version
                else:
                    pip_packages[clean_name] = package.version
        
        logger.info(f"Found {len(pip_packages)} regular packages")
        logger.info(f"Found {len(pytorch_packages)} PyTorch-related packages")
        if editable_installs:
            logger.info(f"Found {len(editable_installs)} editable installs")
            
    except Exception as e:
        # Fallback to direct pip if UV interface fails
        logger.warning(f"UV interface failed: {e}")
        logger.info("Falling back to pip...")
        
        try:
            result = run_command(
                [str(python_executable), "-m", "pip", "freeze"],
                cwd=comfyui_path
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line and '==' in line and not line.startswith('#'):
                        if line.startswith('-e '):
                            editable_installs.append(line)
                        else:
                            package, version = line.split('==', 1)
                            package = normalize_package_name(package.strip())
                            version = version.strip()
                            
                            # Safety check: ensure version doesn't contain '=='
                            if version.startswith('=='):
                                version = version[2:]
                                logger.warning(f"Removed == prefix from version for {package}: {version}")
                            
                            logger.debug(f"Parsed line '{line}' -> package='{package}', version='{version}'")
                            
                            if is_pytorch_package(package, pytorch_package_names):
                                pytorch_packages[package] = version
                            else:
                                pip_packages[package] = version
                
                logger.info(f"Found {len(pip_packages)} regular packages using pip fallback")
                logger.info(f"Found {len(pytorch_packages)} PyTorch-related packages using pip fallback")
            else:
                raise PackageDetectionError(f"Failed to run pip freeze: {result.stderr}")
                
        except Exception as fallback_error:
            # Check if the error is because pip is not installed
            if "No module named pip" in str(fallback_error):
                logger.info("pip is not installed in the target environment, attempting to install it with uv...")
                try:
                    # Use direct uv command to install pip in the target environment  
                    uv_temp = UVInterface()
                    install_cmd = [uv_temp._uv_binary, "pip", "install", "--python", str(python_executable), "pip"]
                    install_result = run_command(install_cmd, cwd=comfyui_path)
                    
                    if install_result.returncode == 0:
                        logger.info("Successfully installed pip using uv, retrying package detection...")
                        # Retry pip freeze after installing pip
                        result = run_command(
                            [str(python_executable), "-m", "pip", "freeze"],
                            cwd=comfyui_path
                        )
                        
                        if result.returncode == 0:
                            for line in result.stdout.strip().split('\n'):
                                if line and '==' in line and not line.startswith('#'):
                                    if line.startswith('-e '):
                                        editable_installs.append(line)
                                    else:
                                        package, version = line.split('==', 1)
                                        package = normalize_package_name(package.strip())
                                        version = version.strip()
                                        
                                        # Safety check: ensure version doesn't contain '=='
                                        if version.startswith('=='):
                                            version = version[2:]
                                            logger.warning(f"Removed == prefix from version for {package}: {version}")
                                        
                                        logger.debug(f"Parsed line '{line}' -> package='{package}', version='{version}'")
                                        
                                        if is_pytorch_package(package, pytorch_package_names):
                                            pytorch_packages[package] = version
                                        else:
                                            pip_packages[package] = version
                            
                            logger.info(f"Found {len(pip_packages)} regular packages after installing pip")
                            logger.info(f"Found {len(pytorch_packages)} PyTorch-related packages after installing pip")
                            return pip_packages, pytorch_packages, editable_installs
                        else:
                            raise PackageDetectionError(f"Failed to run pip freeze after installing pip: {result.stderr}")
                    else:
                        logger.error(f"Failed to install pip using uv: {install_result.stderr}")
                        error_msg = f"UV failed, pip not installed, and could not install pip: {install_result.stderr}"
                        logger.error(error_msg)
                        raise PackageDetectionError(error_msg)
                        
                except Exception as pip_install_error:
                    error_msg = f"UV failed, pip not installed, and failed to install pip: {pip_install_error}"
                    logger.error(error_msg)
                    raise PackageDetectionError(error_msg)
            else:
                error_msg = f"Both UV and pip fallback failed: {fallback_error}"
                logger.error(error_msg)
                raise PackageDetectionError(error_msg)
    
    return pip_packages, pytorch_packages, editable_installs