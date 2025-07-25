"""ComfyUI detector models package."""

from .models import (
    SystemInfo,
    CustomNodeSpec,
    PyTorchSpec,
    DependencySpec,
    MigrationManifest,
    EnvironmentResult,
    create_manifest_from_dict,
    create_system_info_from_detection,
    create_custom_node_spec,
    migrate_legacy_format,
)

__all__ = [
    'SystemInfo',
    'CustomNodeSpec',
    'PyTorchSpec',
    'DependencySpec',
    'MigrationManifest',
    'EnvironmentResult',
    'create_manifest_from_dict',
    'create_system_info_from_detection',
    'create_custom_node_spec',
    'migrate_legacy_format',
]