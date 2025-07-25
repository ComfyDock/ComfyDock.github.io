"""Configuration management for ComfyDock Server.

This module provides a flexible configuration system that supports:
- Default configuration bundled with the library
- Per-client overrides for different applications (CLI, Pinokio, etc.)
- User-level configuration files
- Command-line argument overrides

Example usage:
    from comfydock_server.config import load_config
    
    config = load_config(
        client_defaults_path="my_client_defaults.json",
        user_config_path="~/.comfydock/config.json",
        cli_overrides={"backend": {"port": 8080}}
    )
"""

from .loader import load_config, _deep_update
from .schema import AppConfig, Frontend, Backend, Defaults, Advanced, Logging

__all__ = [
    'load_config',
    '_deep_update',
    'AppConfig',
    'Frontend',
    'Backend',
    'Defaults',
    'Advanced',
    'Logging',
]