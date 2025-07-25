import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union
from importlib import resources

from .schema import AppConfig


def _expand_paths_in_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively expand ~ and ${ENV_VAR} in all string values in a dict."""
    result = {}
    for k, v in d.items():
        if isinstance(v, dict):
            result[k] = _expand_paths_in_dict(v)
        elif isinstance(v, str):
            # Expand both ~ and environment variables
            result[k] = os.path.expandvars(os.path.expanduser(v))
        else:
            result[k] = v
    return result


def _deep_update(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge b into a (b wins)."""
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict):
            a[k] = _deep_update(a[k], v)
        else:
            a[k] = v
    return a


def load_config(
    *,
    client_defaults_path: Optional[Union[str, Path]] = None,
    user_config_path: Optional[Union[str, Path]] = None,
    cli_overrides: Optional[Dict[str, Any]] = None,
    client_defaults_dict: Optional[Dict[str, Any]] = None,
    user_config_dict: Optional[Dict[str, Any]] = None,
) -> AppConfig:
    """Return a fully-merged, validated AppConfig."""
    # 1) library defaults (packaged)
    try:
        base = json.loads(
            resources.files("comfydock_server.config")
            .joinpath("default_config.json")
            .read_text()
        )
    except Exception as e:
        raise RuntimeError(f"Failed to load default config: {e}")

    # 2) optional per-client overrides (ship in the client repo)
    if client_defaults_dict:
        base = _deep_update(base, client_defaults_dict)
    elif client_defaults_path and Path(client_defaults_path).exists():
        try:
            with open(client_defaults_path, 'r') as f:
                client_config = json.load(f)
            base = _deep_update(base, client_config)
        except Exception as e:
            raise RuntimeError(f"Failed to load client config from {client_defaults_path}: {e}")

    # 3) optional user-level overrides (e.g. ~/.comfydock/config.json)
    if user_config_dict:
        base = _deep_update(base, user_config_dict)
    elif user_config_path and Path(user_config_path).exists():
        try:
            with open(user_config_path, 'r') as f:
                user_config = json.load(f)
            base = _deep_update(base, user_config)
        except Exception as e:
            raise RuntimeError(f"Failed to load user config from {user_config_path}: {e}")

    # 4) CLI / environment variable overrides (already parsed)
    if cli_overrides:
        base = _deep_update(base, cli_overrides)

    # 5) Expand all paths in the merged config before validation
    base = _expand_paths_in_dict(base)

    try:
        return AppConfig(**base)
    except Exception as e:
        raise RuntimeError(f"Failed to validate configuration: {e}")