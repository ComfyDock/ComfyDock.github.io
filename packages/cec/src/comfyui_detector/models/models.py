"""Core data models for ComfyUI migration manifest schema v1.0.

This module provides type-safe dataclasses for representing ComfyUI environment
detection results and migration manifests. All models include validation,
serialization helpers, and proper type hints for IDE support.
"""

import json
import re
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
from pathlib import Path

import requirements

from ..exceptions import ValidationError


@dataclass
class Package:
    """Represents an installed Python package."""
    
    name: str
    version: str
    is_editable: bool = False
    
    def validate(self) -> None:
        """Validate package information."""
        if not self.name:
            raise ValidationError("Package name cannot be empty")
        if not self.version:
            raise ValidationError("Package version cannot be empty")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Package':
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class SystemInfo:
    """System and version information for the detected environment."""
    
    python_version: str
    cuda_version: Optional[str] = None
    torch_version: Optional[str] = None
    comfyui_version: Optional[str] = None
    
    def validate(self) -> None:
        """Validate system info fields."""
        if not self._is_valid_version(self.python_version):
            raise ValidationError(f"Invalid Python version format: {self.python_version}")
        
        if self.cuda_version and not self._is_valid_cuda_version(self.cuda_version):
            raise ValidationError(f"Invalid CUDA version format: {self.cuda_version}")
        
        if self.torch_version and not self._is_valid_torch_version(self.torch_version):
            raise ValidationError(f"Invalid PyTorch version format: {self.torch_version}")
    
    @staticmethod
    def _is_valid_version(version: str) -> bool:
        """Check if version follows M.m.p format."""
        pattern = r'^\d+\.\d+\.\d+$'
        return bool(re.match(pattern, version))
    
    @staticmethod
    def _is_valid_cuda_version(version: str) -> bool:
        """Check if CUDA version is valid (M.m format)."""
        pattern = r'^\d+\.\d+$'
        return bool(re.match(pattern, version))
    
    @staticmethod
    def _is_valid_torch_version(version: str) -> bool:
        """Check if PyTorch version is valid (includes +cu/cpu suffixes and dev builds)."""
        # Updated pattern to handle:
        # - Regular versions: 2.1.0
        # - With CUDA: 2.1.0+cu121
        # - Dev/nightly builds: 2.8.0.dev20250627+cu128
        # - CPU versions: 2.1.0+cpu
        # - Complex dev builds: 2.1.0a0+gitunknown
        pattern = r'^\d+\.\d+\.\d+(?:\.\w+)?(?:\+[\w\d]+)?$'
        return bool(re.match(pattern, version))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemInfo':
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class CustomNodeSpec:
    """Specification for a custom node installation."""
    
    name: str
    install_method: str  # archive|git|local
    url: str
    ref: Optional[str] = None
    has_post_install: Optional[bool] = None
    
    def validate(self) -> None:
        """Validate custom node specification."""
        if not self.name:
            raise ValidationError("Custom node name cannot be empty")
        
        valid_methods = {'archive', 'git', 'local'}
        if self.install_method not in valid_methods:
            raise ValidationError(
                f"Invalid install method: {self.install_method}. "
                f"Must be one of: {', '.join(valid_methods)}"
            )
        
        if not self._is_valid_url(self.url):
            raise ValidationError(f"Invalid URL: {self.url}")
        
        if self.install_method == 'git' and self.ref and not self._is_valid_git_ref(self.ref):
            raise ValidationError(f"Invalid git ref: {self.ref}")
    
    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """Check if URL is absolute with scheme."""
        try:
            result = urlparse(url)
            return bool(result.scheme and result.netloc)
        except Exception:
            return False
    
    @staticmethod
    def _is_valid_git_ref(ref: str) -> bool:
        """Basic validation for git ref (commit hash or branch/tag name)."""
        # Allow alphanumeric, dash, underscore, slash, dot
        pattern = r'^[a-zA-Z0-9\-_/\.]+$'
        return bool(re.match(pattern, ref))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            'name': self.name,
            'install_method': self.install_method,
            'url': self.url
        }
        if self.ref is not None:
            result['ref'] = self.ref
        if self.has_post_install is not None:
            result['has_post_install'] = self.has_post_install
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomNodeSpec':
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class PyTorchSpec:
    """PyTorch packages configuration with index URL."""
    
    index_url: str
    packages: Dict[str, str] = field(default_factory=dict)
    
    def validate(self) -> None:
        """Validate PyTorch specification."""
        if not self._is_valid_url(self.index_url):
            raise ValidationError(f"Invalid PyTorch index URL: {self.index_url}")
        
        if not self.packages:
            raise ValidationError("PyTorch packages cannot be empty")
        
        for package, version in self.packages.items():
            if not self._is_valid_package_name(package):
                raise ValidationError(f"Invalid package name: {package}")
            if not self._is_valid_version(version):
                raise ValidationError(f"Invalid version for {package}: {version}")
    
    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """Check if URL is absolute with scheme."""
        try:
            result = urlparse(url)
            return bool(result.scheme and result.netloc)
        except Exception:
            return False
    
    @staticmethod
    def _is_valid_package_name(name: str) -> bool:
        """Check if package name follows PEP 508."""
        # Basic validation: alphanumeric with dash, underscore, dot
        pattern = r'^[a-zA-Z0-9\-_\.]+$'
        return bool(re.match(pattern, name))
    
    @staticmethod
    def _is_valid_version(version: str) -> bool:
        """Check if version is valid (basic semver with optional suffix like +cu126)."""
        pattern = r'^\d+\.\d+(\.\d+)?(\+[a-zA-Z0-9]+)?$'
        return bool(re.match(pattern, version))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PyTorchSpec':
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class DependencySpec:
    """All dependency types for the migration."""
    
    packages: Dict[str, str] = field(default_factory=dict)
    pytorch: Optional[PyTorchSpec] = None
    editable_installs: List[str] = field(default_factory=list)
    git_requirements: List[str] = field(default_factory=list)
    
    def validate(self) -> None:
        """Validate dependency specification."""
        # Validate regular packages
        for package, version in self.packages.items():
            if not self._is_valid_package_name(package):
                raise ValidationError(f"Invalid package name: {package}")
            if not self._is_valid_version(version):
                raise ValidationError(f"Invalid version for {package}: {version}")
        
        # Validate PyTorch spec if present
        if self.pytorch:
            self.pytorch.validate()
        
        # Validate editable installs
        for install in self.editable_installs:
            if not install.startswith('-e '):
                raise ValidationError(f"Editable install must start with '-e ': {install}")
        
        # Validate git requirements
        for req in self.git_requirements:
            if not req.startswith('git+'):
                raise ValidationError(f"Git requirement must start with 'git+': {req}")
    
    @staticmethod
    def _is_valid_package_name(name: str) -> bool:
        """Check if package name follows PEP 508."""
        pattern = r'^[a-zA-Z0-9\-_\.]+$'
        return bool(re.match(pattern, name))
    
    @staticmethod
    def _is_valid_version(version: str) -> bool:
        """Check if version constraint is valid using requirements parser."""
        if not version or not version.strip():
            # Empty version is allowed (means any version)
            return True
            
        try:
            # Try to parse as a version constraint first
            dummy_req = f"dummy{version}"
            parsed_reqs = list(requirements.parse(dummy_req))
            
            if parsed_reqs:
                req = parsed_reqs[0]
                # Check if it parsed successfully with a valid specifier
                if req.name == "dummy" and req.specifier:
                    return True
            
            # If no specifier, try parsing as a plain version with ==
            dummy_req_exact = f"dummy=={version}"
            parsed_reqs_exact = list(requirements.parse(dummy_req_exact))
            
            if parsed_reqs_exact:
                req = parsed_reqs_exact[0]
                if req.name == "dummy" and req.specifier:
                    return True
                    
        except Exception:
            pass
            
        # If requirements parser fails, fall back to basic regex validation
        # This handles simple version numbers without constraints
        pattern = r'^\d+(\.\d+)*([a-zA-Z0-9\-\.\+]+)?$'
        return bool(re.match(pattern, version))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: Dict[str, Any] = {}
        
        if self.packages:
            result['packages'] = self.packages
        
        if self.pytorch:
            result['pytorch'] = self.pytorch.to_dict()
        
        if self.editable_installs:
            result['editable_installs'] = self.editable_installs
        
        if self.git_requirements:
            result['git_requirements'] = self.git_requirements
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DependencySpec':
        """Create instance from dictionary."""
        kwargs = {}
        
        if 'packages' in data:
            kwargs['packages'] = data['packages']
        
        if 'pytorch' in data:
            kwargs['pytorch'] = PyTorchSpec.from_dict(data['pytorch'])
        
        if 'editable_installs' in data:
            kwargs['editable_installs'] = data['editable_installs']
        
        if 'git_requirements' in data:
            kwargs['git_requirements'] = data['git_requirements']
        
        return cls(**kwargs)


@dataclass
class MigrationManifest:
    """Primary migration manifest (minimal)."""
    
    system_info: SystemInfo
    custom_nodes: List[CustomNodeSpec] = field(default_factory=list)
    dependencies: DependencySpec = field(default_factory=DependencySpec)
    schema_version: str = "1.0"
    
    def validate(self) -> None:
        """Validate the entire manifest."""
        # Validate schema version
        if self.schema_version != "1.0":
            raise ValidationError(f"Unsupported schema version: {self.schema_version}")
        
        # Validate system info
        self.system_info.validate()
        
        # Validate each custom node
        for node in self.custom_nodes:
            node.validate()
        
        # Validate dependencies
        self.dependencies.validate()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'schema_version': self.schema_version,
            'system_info': self.system_info.to_dict(),
            'custom_nodes': [node.to_dict() for node in self.custom_nodes],
            'dependencies': self.dependencies.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MigrationManifest':
        """Create instance from dictionary."""
        return cls(
            schema_version=data.get('schema_version', '1.0'),
            system_info=SystemInfo.from_dict(data['system_info']),
            custom_nodes=[
                CustomNodeSpec.from_dict(node) 
                for node in data.get('custom_nodes', [])
            ],
            dependencies=DependencySpec.from_dict(data.get('dependencies', {}))
        )
    
    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MigrationManifest':
        """Parse from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


# Factory functions for creating models from existing data

def create_manifest_from_dict(data: Dict[str, Any]) -> MigrationManifest:
    """Create a MigrationManifest from a dictionary with validation."""
    manifest = MigrationManifest.from_dict(data)
    manifest.validate()
    return manifest


def create_system_info_from_detection(
    python_version: str,
    cuda_version: Optional[str] = None,
    torch_version: Optional[str] = None,
    comfyui_version: Optional[str] = None
) -> SystemInfo:
    """Create SystemInfo from detection results."""
    info = SystemInfo(
        python_version=python_version,
        cuda_version=cuda_version,
        torch_version=torch_version,
        comfyui_version=comfyui_version
    )
    info.validate()
    return info


def create_custom_node_spec(
    name: str,
    install_method: str,
    url: str,
    ref: Optional[str] = None,
    has_post_install: Optional[bool] = None
) -> CustomNodeSpec:
    """Create a CustomNodeSpec with validation."""
    spec = CustomNodeSpec(
        name=name,
        install_method=install_method,
        url=url,
        ref=ref,
        has_post_install=has_post_install
    )
    spec.validate()
    return spec


def migrate_legacy_format(legacy_data: Dict[str, Any]) -> MigrationManifest:
    """Convert legacy dict format to new dataclass format."""
    # Extract system info
    system_info = SystemInfo(
        python_version=legacy_data.get('python_version', ''),
        cuda_version=legacy_data.get('cuda_version'),
        torch_version=legacy_data.get('torch_version'),
        comfyui_version=legacy_data.get('comfyui_version')
    )
    
    # Extract custom nodes
    custom_nodes = []
    for node_data in legacy_data.get('custom_nodes', []):
        custom_nodes.append(CustomNodeSpec.from_dict(node_data))
    
    # Extract dependencies
    deps_data = legacy_data.get('dependencies', {})
    dependencies = DependencySpec.from_dict(deps_data)
    
    # Create manifest
    manifest = MigrationManifest(
        schema_version=legacy_data.get('schema_version', '1.0'),
        system_info=system_info,
        custom_nodes=custom_nodes,
        dependencies=dependencies
    )
    
    manifest.validate()
    return manifest


@dataclass
class EnvironmentResult:
    """Result of environment recreation with validation details."""
    
    success: bool
    environment_path: Path
    venv_path: Path
    comfyui_path: Path
    installed_packages: Dict[str, str] = field(default_factory=dict)
    installed_nodes: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    
    def validate(self) -> None:
        """Validate the result data."""
        if not isinstance(self.success, bool):
            raise ValidationError("success must be a boolean")
        
        if not isinstance(self.environment_path, Path):
            raise ValidationError("environment_path must be a Path object")
        
        if not isinstance(self.venv_path, Path):
            raise ValidationError("venv_path must be a Path object")
        
        if not isinstance(self.comfyui_path, Path):
            raise ValidationError("comfyui_path must be a Path object")
        
        if not isinstance(self.installed_packages, dict):
            raise ValidationError("installed_packages must be a dictionary")
        
        if not isinstance(self.installed_nodes, list):
            raise ValidationError("installed_nodes must be a list")
        
        if not isinstance(self.warnings, list):
            raise ValidationError("warnings must be a list")
        
        if not isinstance(self.errors, list):
            raise ValidationError("errors must be a list")
        
        if not isinstance(self.duration_seconds, (int, float)) or self.duration_seconds < 0:
            raise ValidationError("duration_seconds must be non-negative")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'success': self.success,
            'environment_path': str(self.environment_path),
            'venv_path': str(self.venv_path),
            'comfyui_path': str(self.comfyui_path),
            'installed_packages': self.installed_packages.copy(),
            'installed_nodes': self.installed_nodes.copy(),
            'warnings': self.warnings.copy(),
            'errors': self.errors.copy(),
            'duration_seconds': self.duration_seconds
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnvironmentResult':
        """Create instance from dictionary."""
        return cls(
            success=data['success'],
            environment_path=Path(data['environment_path']),
            venv_path=Path(data['venv_path']),
            comfyui_path=Path(data['comfyui_path']),
            installed_packages=data.get('installed_packages', {}),
            installed_nodes=data.get('installed_nodes', []),
            warnings=data.get('warnings', []),
            errors=data.get('errors', []),
            duration_seconds=data.get('duration_seconds', 0.0)
        )