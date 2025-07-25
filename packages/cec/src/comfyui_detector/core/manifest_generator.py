"""Manifest generator for creating migration manifests."""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from ..constants import SCHEMA_VERSION, DETECTOR_VERSION
from ..models import (
    SystemInfo, CustomNodeSpec, PyTorchSpec, DependencySpec, MigrationManifest
)
from ..utils import get_comfyui_version, save_requirements_txt, get_pytorch_index_url
from ..logging_config import get_logger


class ManifestGenerator:
    """Generates migration manifests from detected environment data."""
    
    def __init__(self, comfyui_path: Path):
        self.logger = get_logger(__name__)
        self.comfyui_path = Path(comfyui_path).resolve()
        
    def generate(self, system_info: Dict, custom_nodes_info: Dict, 
                 package_info: Dict, conflicts: List[Dict]) -> Dict:
        """Generate the final migration configuration."""
        # Detect ComfyUI version if possible
        comfyui_version = get_comfyui_version(self.comfyui_path)
        
        # First, save the full detailed log for debugging
        full_config = self._generate_full_config(
            comfyui_version, system_info, custom_nodes_info, package_info, conflicts
        )
        log_path = Path("comfyui_detection_log.json")
        with open(log_path, 'w') as f:
            json.dump(full_config, f, indent=2)
        self.logger.info(f"Detailed detection log saved to {log_path}")
        
        # Now generate the lean manifest
        lean_manifest = self._generate_lean_manifest(
            comfyui_version, system_info, custom_nodes_info, package_info
        )
        
        # Save lean manifest
        manifest_path = Path("comfyui_migration.json")
        with open(manifest_path, 'w') as f:
            json.dump(lean_manifest, f, indent=2)
        self.logger.info(f"Migration manifest saved to {manifest_path}")
        
        # Save requirements.txt
        save_requirements_txt(
            lean_manifest['dependencies']['packages'],
            system_info,
            self.comfyui_path
        )
        
        return lean_manifest
    
    def _generate_lean_manifest(self, comfyui_version: str, system_info: Dict,
                               custom_nodes_info: Dict, package_info: Dict) -> Dict:
        """Generate the lean migration manifest using dataclass models."""
        # Create SystemInfo model
        system_info_model = SystemInfo(
            python_version=system_info.get('python_version', ''),
            cuda_version=system_info.get('cuda_version'),
            torch_version=system_info.get('torch_version'),
            comfyui_version=comfyui_version
        )
        
        # Build custom nodes array using CustomNodeSpec
        custom_nodes = []
        for node_name, node_info in custom_nodes_info.items():
            node_spec = self._create_custom_node_spec(node_name, node_info)
            if node_spec and node_spec.url:
                custom_nodes.append(node_spec)
        
        # Determine PyTorch index URL
        pytorch_index_url = get_pytorch_index_url(
            system_info.get('torch_version', ''),
            system_info.get('cuda_torch_version')
        )
        
        # Build PyTorchSpec if we have PyTorch packages
        pytorch_spec = None
        pytorch_packages = package_info.get('pytorch_packages', {})
        if pytorch_packages and pytorch_index_url:
            # Filter to just the main PyTorch packages
            main_pytorch_packages = {}
            for pkg, version in pytorch_packages.items():
                if pkg in ['torch', 'torchvision', 'torchaudio']:
                    main_pytorch_packages[pkg] = version
            
            if main_pytorch_packages:
                pytorch_spec = PyTorchSpec(
                    index_url=pytorch_index_url,
                    packages=main_pytorch_packages
                )
        
        # Build DependencySpec
        dependencies = DependencySpec(
            packages=package_info.get('resolved_requirements', {}),
            pytorch=pytorch_spec,
            editable_installs=package_info.get('editable_installs', []),
            git_requirements=package_info.get('git_requirements', [])
        )
        
        # Create MigrationManifest
        manifest = MigrationManifest(
            schema_version=SCHEMA_VERSION,
            system_info=system_info_model,
            custom_nodes=custom_nodes,
            dependencies=dependencies
        )
        
        # Validate the manifest
        manifest.validate()
        
        # Return as dict for JSON serialization
        return manifest.to_dict()
    
    def _create_custom_node_spec(self, node_name: str, node_info: Dict) -> Optional[CustomNodeSpec]:
        """Create a CustomNodeSpec dataclass for the manifest."""
        install_method = None
        url = None
        ref = None
        has_post_install = bool(node_info.get('install_scripts'))
        
        # Determine install method and URL based on priority
        priority = node_info.get('install_priority', 'local')
        
        if priority == 'github' and node_info.get('github_validation'):
            git_info = node_info.get('git', {})
            owner = git_info.get('github_owner')
            repo = git_info.get('github_repo')
            
            if owner and repo:
                # Check if exact version was found
                if node_info['github_validation'].get('found'):
                    # Exact version found - use archive for reliability
                    install_method = "archive"
                    version = node_info.get('version')
                    if version:
                        url = f"https://github.com/{owner}/{repo}/archive/refs/tags/{version}.tar.gz"
                    else:
                        # Fallback to commit archive
                        commit = git_info.get('commit')
                        if commit:
                            url = f"https://github.com/{owner}/{repo}/archive/{commit}.tar.gz"
                else:
                    # No exact version - prefer git clone to preserve history
                    git_url = git_info.get('remote_url')
                    if git_url:
                        install_method = "git"
                        url = git_url
                        commit = git_info.get('commit')
                        if commit:
                            ref = commit
                    else:
                        # Fallback to archive if no git URL
                        install_method = "archive"
                        commit = git_info.get('commit')
                        if commit:
                            url = f"https://github.com/{owner}/{repo}/archive/{commit}.tar.gz"
        
        elif priority == 'registry' and node_info.get('registry_validation'):
            # Use registry download URL if available
            registry_validation = node_info['registry_validation']
            download_url = registry_validation.get('download_url')
            
            if download_url:
                # We have a direct download URL from the registry
                install_method = "archive"
                url = download_url
            else:
                # Fallback to git URL if available
                git_info = node_info.get('git', {})
                if git_info and git_info.get('github_owner') and git_info.get('github_repo'):
                    install_method = "archive"
                    owner = git_info['github_owner']
                    repo = git_info['github_repo']
                    commit = git_info.get('commit')
                    if commit:
                        url = f"https://github.com/{owner}/{repo}/archive/{commit}.tar.gz"
                else:
                    # No download URL available - mark as local
                    install_method = "local"
                    url = node_name
        
        elif priority == 'git' and node_info.get('git'):
            # Use git clone
            git_url = node_info['git'].get('remote_url')
            if git_url:
                install_method = "git"
                url = git_url
                # Add ref if we have a specific commit
                commit = node_info['git'].get('commit')
                if commit:
                    ref = commit
        
        else:
            # Local only
            install_method = "local"
            url = node_name  # Just use the directory name
        
        # Create and return the CustomNodeSpec if we have valid data
        if install_method and url:
            return CustomNodeSpec(
                name=node_name,
                install_method=install_method,
                url=url,
                ref=ref,
                has_post_install=has_post_install
            )
        
        return None
    
    def _generate_full_config(self, comfyui_version: str, system_info: Dict,
                             custom_nodes_info: Dict, package_info: Dict,
                             conflicts: List[Dict]) -> Dict:
        """Generate the full detailed configuration for logging."""
        # This is essentially the original format with all the detailed info
        registry_nodes = []
        git_nodes = []
        github_nodes = []
        local_nodes = []
        
        for node_name, node_info in custom_nodes_info.items():
            base_info = {
                'name': node_name,
                'install_priority': node_info.get('install_priority', 'unknown'),
                'priority_reason': node_info.get('priority_reason', ''),
                'version': node_info.get('version')
            }
            
            # Categorize based on install priority
            if node_info.get('install_priority') == 'github':
                github_entry = {
                    **base_info,
                    'github_owner': node_info['git']['github_owner'],
                    'github_repo': node_info['git']['github_repo'],
                    'github_url': node_info['git']['github_url'],
                    'exact_version_found': node_info.get('github_validation', {}).get('found', False),
                    'github_version': (node_info.get('github_validation', {}).get('data', {}).get('tag_name') 
                                    if node_info.get('github_validation', {}).get('found') 
                                    else node_info.get('github_validation', {}).get('closest_version')),
                    'commit': node_info['git'].get('commit'),
                    'has_uncommitted_changes': node_info['git'].get('has_uncommitted_changes', False)
                }
                github_nodes.append(github_entry)
                
            elif node_info.get('install_priority') == 'registry' or (node_info.get('registry_validated') and node_info.get('install_priority') != 'git'):
                validation = node_info['registry_validation']
                registry_entry = {
                    **base_info,
                    'project_name': node_info.get('project_name', node_name),
                    'registry_id': node_info.get('registry_id'),
                    'version_available': validation['version_available'],
                    'available_versions': validation['available_versions'],
                    'closest_version': validation['closest_version'],
                    'source': 'registry'
                }
                
                if node_info.get('git'):
                    registry_entry['git_info'] = {
                        'git_url': node_info['git'].get('remote_url'),
                        'commit': node_info['git'].get('commit'),
                        'tag': node_info['git'].get('tag'),
                        'has_uncommitted_changes': node_info['git'].get('has_uncommitted_changes', False)
                    }
                
                registry_nodes.append(registry_entry)
                
            elif node_info.get('git'):
                git_nodes.append({
                    **base_info,
                    'git_url': node_info['git'].get('remote_url'),
                    'commit': node_info['git'].get('commit'),
                    'tag': node_info['git'].get('tag'),
                    'has_uncommitted_changes': node_info['git'].get('has_uncommitted_changes', False)
                })
            else:
                local_nodes.append({
                    **base_info,
                    'has_requirements': node_info['has_requirements'],
                    'install_scripts': node_info['install_scripts']
                })
        
        # Find nodes with requirements and install scripts
        custom_nodes_with_requirements = []
        nodes_with_install_scripts = []
        
        for node_name, node_info in custom_nodes_info.items():
            if node_info.get('has_requirements'):
                custom_nodes_with_requirements.append(node_name)
            if node_info.get('install_scripts'):
                for script in node_info['install_scripts']:
                    nodes_with_install_scripts.append((node_name, script))
        
        return {
            'detection_metadata': {
                'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'detector_version': DETECTOR_VERSION,
                'registry_validation_enabled': any(n.get('registry_validated') for n in custom_nodes_info.values())
            },
            'system_info': {
                'python_version': system_info.get('python_version'),
                'python_major_minor': system_info.get('python_major_minor'),
                'cuda_version': system_info.get('cuda_version'),
                'torch_version': system_info.get('torch_version'),
                'cuda_torch_version': system_info.get('cuda_torch_version'),
                'platform': system_info.get('platform'),
                'architecture': system_info.get('architecture'),
                'comfyui_version': comfyui_version,
                'pytorch_info': system_info.get('pytorch_info', {})
            },
            'paths': {
                'comfyui_path': str(self.comfyui_path),
                'venv_path': str(system_info.get('venv_path')) if system_info.get('venv_path') else None,
                'python_executable': str(system_info.get('python_executable')) if system_info.get('python_executable') else None,
            },
            'custom_nodes': {
                'total': len(custom_nodes_info),
                'with_requirements': custom_nodes_with_requirements,
                'with_install_scripts': nodes_with_install_scripts,
                'registry_nodes': registry_nodes,
                'github_nodes': github_nodes,
                'git_nodes': git_nodes,
                'local_nodes': local_nodes,
                'registry_validation_enabled': any(n.get('registry_validated') for n in custom_nodes_info.values()),
                'detailed_info': custom_nodes_info
            },
            'dependencies': {
                'resolved_requirements': package_info.get('resolved_requirements', {}),
                'pytorch_packages': package_info.get('pytorch_packages', {}),
                'editable_installs': package_info.get('editable_installs', []),
                'git_requirements': package_info.get('git_requirements', []),
                'conflicts': conflicts,
                'installed_packages': package_info.get('installed_packages', {})
            }
        }