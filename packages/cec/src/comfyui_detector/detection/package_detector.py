"""Package detector for requirements and dependencies."""

from pathlib import Path
from typing import Dict, List, Optional

from packaging.requirements import Requirement

from ..constants import PYTORCH_PACKAGE_NAMES
from ..utils import (
    extract_packages_with_uv, parse_requirements_file,
    is_pytorch_package, get_pytorch_index_url
)
from ..logging_config import get_logger


class PackageDetector:
    """Detects and manages package requirements and dependencies."""
    
    def __init__(self, comfyui_path: Path, python_executable: Path):
        self.logger = get_logger(__name__)
        self.comfyui_path = Path(comfyui_path).resolve()
        self.python_executable = python_executable
        self.requirements = {}  # package_name: version
        self.pytorch_packages = {}  # Separate PyTorch packages
        self.conflicts = []
        self.pytorch_package_names = PYTORCH_PACKAGE_NAMES
        
    def detect_all(self) -> Dict:
        """Detect all package information."""
        result = {}
        
        # Extract packages with uv
        self.extract_packages()
        
        # Parse ComfyUI requirements
        self.parse_comfyui_requirements()
        
        # Resolve conflicts
        resolved_requirements = self.resolve_requirement_conflicts()
        
        # Build result
        result['installed_packages'] = self.installed_packages
        result['pytorch_packages'] = self.pytorch_packages
        result['resolved_requirements'] = resolved_requirements
        result['conflicts'] = self.conflicts
        
        if hasattr(self, 'editable_installs') and self.editable_installs:
            result['editable_installs'] = self.editable_installs
            
        if hasattr(self, 'git_requirements') and self.git_requirements:
            result['git_requirements'] = self.git_requirements
            
        return result
    
    def extract_packages(self) -> Dict[str, str]:
        """Extract installed packages using uv from the detected virtual environment."""
        pip_packages, pytorch_packages, editable_installs = extract_packages_with_uv(
            self.python_executable, self.comfyui_path, self.pytorch_package_names
        )
        
        self.installed_packages = pip_packages
        self.pytorch_packages = pytorch_packages
        self.editable_installs = editable_installs
        
        return pip_packages
    
    def parse_comfyui_requirements(self) -> Dict[str, List[str]]:
        """Parse ComfyUI's main requirements.txt."""
        req_path = self.comfyui_path / "requirements.txt"
        self.logger.info(f"Parsing ComfyUI requirements from {req_path}")
        
        comfyui_reqs = parse_requirements_file(req_path)
        
        # Store git requirements if found
        git_reqs = []
        with open(req_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and ('git+' in line or line.startswith('-e')):
                    git_reqs.append(line)
        
        if git_reqs:
            self.git_requirements = git_reqs
        
        # Merge into main requirements
        for package, versions in comfyui_reqs.items():
            if package not in self.requirements:
                self.requirements[package] = []
            self.requirements[package].extend(versions)
            
        self.logger.info(f"Found {len(comfyui_reqs)} requirements in ComfyUI")
        return comfyui_reqs
    
    def add_custom_node_requirements(self, package: str, versions: List[str]):
        """Add requirements from a custom node."""
        if package not in self.requirements:
            self.requirements[package] = []
        self.requirements[package].extend(versions)
    
    def resolve_requirement_conflicts(self) -> Dict[str, str]:
        """Resolve conflicts between different requirement versions."""
        resolved_requirements = {}
        
        self.logger.info("Resolving requirement conflicts...")
        
        for package, version_specs in self.requirements.items():
            # Skip PyTorch packages
            if is_pytorch_package(package):
                continue
                
            # Remove duplicates and empty specs
            unique_specs = [s for s in set(version_specs) if s]
            
            # If package is installed, prefer the installed version
            if package in self.installed_packages:
                resolved_requirements[package] = self.installed_packages[package]
                
                # Check if installed version satisfies all requirements
                installed_ver = self.installed_packages[package]
                for spec in unique_specs:
                    try:
                        req = Requirement(f"{package}{spec}")
                        if not req.specifier.contains(installed_ver):
                            self.conflicts.append({
                                'package': package,
                                'installed': installed_ver,
                                'required': spec,
                                'resolved_to': installed_ver
                            })
                    except Exception:
                        pass
            else:
                # Package not installed but required
                if unique_specs:
                    # Use the most specific version spec
                    resolved_requirements[package] = unique_specs[0] if unique_specs[0] else ""
                    self.logger.warning(f"{package} required but not installed")
                    
        self.logger.info(f"Resolved {len(resolved_requirements)} package requirements")
        if self.conflicts:
            self.logger.warning(f"Found {len(self.conflicts)} potential conflicts")
            
        return resolved_requirements
    
    def get_pytorch_index_url(self, torch_version: str, cuda_torch_version: Optional[str]) -> Optional[str]:
        """Get the PyTorch index URL based on the detected versions."""
        return get_pytorch_index_url(torch_version, cuda_torch_version)