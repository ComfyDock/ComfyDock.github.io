#!/usr/bin/env python3
"""
Test configuration loader for migration tests
"""

from pathlib import Path
from typing import Dict, Optional

try:
    import yaml
except ImportError:
    yaml = None


def load_test_config(config_path: Optional[Path] = None) -> Dict:
    """Load test configuration from YAML file"""
    
    if config_path is None:
        config_path = Path(__file__).parent / 'test_config.yaml'
    
    if not config_path.exists():
        # Return default configuration if file doesn't exist
        return get_default_config()
    
    if yaml is None:
        # PyYAML not available, use default config
        return get_default_config()
        
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            return config or get_default_config()
    except Exception:
        # Return default config if loading fails
        return get_default_config()


def get_default_config() -> Dict:
    """Get default test configuration"""
    return {
        'test_scenarios': [
            {
                'name': 'basic_comfyui',
                'comfyui_version': {
                    'version': 'master',
                    'git_ref': 'master'
                },
                'python_version': '3.10',
                'custom_nodes': []
            },
            {
                'name': 'with_controlnet',
                'comfyui_version': {
                    'version': 'master',
                    'git_ref': 'master'
                },
                'python_version': '3.10',
                'custom_nodes': ['ComfyUI_ControlNet_Aux']
            }
        ],
        'cleanup_after_test': True,
        'validation_thresholds': {
            'overall_accuracy': 0.8,
            'custom_nodes_accuracy': 0.9,
            'package_detection_threshold': 10
        }
    }