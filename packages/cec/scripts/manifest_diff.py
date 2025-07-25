#!/usr/bin/env python3

"""
Script to compare ComfyUI migration manifest files
Usage: python scripts/manifest_diff.py <test_env1> <test_env2>
Example: python scripts/manifest_diff.py test_1 test_2
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List


def load_manifest(test_env: str) -> Dict[str, Any]:
    """Load a ComfyUI migration manifest file"""
    manifest_path = Path(f".test_data/manifests/{test_env}/comfyui_migration.json")
    
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        return json.load(f)


def compare_system_info(info1: Dict, info2: Dict) -> List[str]:
    """Compare system info sections"""
    differences = []
    
    for key in set(info1.keys()) | set(info2.keys()):
        if key not in info1:
            differences.append(f"  System info '{key}' missing in first manifest")
        elif key not in info2:
            differences.append(f"  System info '{key}' missing in second manifest")
        elif info1[key] != info2[key]:
            differences.append(f"  {key}: {info1[key]} → {info2[key]}")
    
    return differences


def compare_custom_nodes(nodes1: List[Dict], nodes2: List[Dict]) -> List[str]:
    """Compare custom nodes sections"""
    differences = []
    
    # Create dictionaries keyed by node name for easier comparison
    nodes1_dict = {node['name']: node for node in nodes1}
    nodes2_dict = {node['name']: node for node in nodes2}
    
    all_node_names = set(nodes1_dict.keys()) | set(nodes2_dict.keys())
    
    for name in sorted(all_node_names):
        if name not in nodes1_dict:
            differences.append(f"  + {name} (added)")
        elif name not in nodes2_dict:
            differences.append(f"  - {name} (removed)")
        else:
            node1, node2 = nodes1_dict[name], nodes2_dict[name]
            
            # Compare relevant fields
            for field in ['install_method', 'url', 'ref', 'has_post_install']:
                if field in node1 and field in node2:
                    if node1[field] != node2[field]:
                        differences.append(f"  ~ {name}.{field}: {node1[field]} → {node2[field]}")
                elif field in node1:
                    differences.append(f"  ~ {name}.{field}: {node1[field]} → (missing)")
                elif field in node2:
                    differences.append(f"  ~ {name}.{field}: (missing) → {node2[field]}")
    
    return differences


def compare_packages(packages1: Dict, packages2: Dict) -> List[str]:
    """Compare package dependencies"""
    differences = []
    
    all_packages = set(packages1.keys()) | set(packages2.keys())
    
    for package in sorted(all_packages):
        if package not in packages1:
            differences.append(f"  + {package}: {packages2[package]} (added)")
        elif package not in packages2:
            differences.append(f"  - {package}: {packages1[package]} (removed)")
        elif packages1[package] != packages2[package]:
            differences.append(f"  ~ {package}: {packages1[package]} → {packages2[package]}")
    
    return differences


def main():
    if len(sys.argv) != 3:
        print("Usage: python scripts/manifest_diff.py <test_env1> <test_env2>")
        print("Example: python scripts/manifest_diff.py test_1 test_2")
        sys.exit(1)
    
    test_env1, test_env2 = sys.argv[1], sys.argv[2]
    
    try:
        manifest1 = load_manifest(test_env1)
        manifest2 = load_manifest(test_env2)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        sys.exit(1)
    
    print(f"🔍 Comparing manifests: {test_env1} vs {test_env2}")
    print("=" * 60)
    
    # Compare schema versions
    if manifest1.get('schema_version') != manifest2.get('schema_version'):
        print(f"⚠️  Schema version: {manifest1.get('schema_version')} → {manifest2.get('schema_version')}")
        print()
    
    # Compare system info
    system_diffs = compare_system_info(
        manifest1.get('system_info', {}), 
        manifest2.get('system_info', {})
    )
    if system_diffs:
        print("📋 System Info Differences:")
        for diff in system_diffs:
            print(diff)
        print()
    
    # Compare custom nodes
    nodes_diffs = compare_custom_nodes(
        manifest1.get('custom_nodes', []), 
        manifest2.get('custom_nodes', [])
    )
    if nodes_diffs:
        print("🔌 Custom Nodes Differences:")
        for diff in nodes_diffs:
            print(diff)
        print()
    
    # Compare package dependencies
    packages_diffs = compare_packages(
        manifest1.get('dependencies', {}).get('packages', {}),
        manifest2.get('dependencies', {}).get('packages', {})
    )
    if packages_diffs:
        print("📦 Package Dependencies Differences:")
        for diff in packages_diffs:
            print(diff)
        print()
    
    # Summary
    total_diffs = len(system_diffs) + len(nodes_diffs) + len(packages_diffs)
    
    if total_diffs == 0:
        print("✅ No differences found - manifests are identical!")
    else:
        print(f"📊 Summary: {total_diffs} differences found")
        if system_diffs:
            print(f"   - {len(system_diffs)} system info differences")
        if nodes_diffs:
            print(f"   - {len(nodes_diffs)} custom node differences")
        if packages_diffs:
            print(f"   - {len(packages_diffs)} package dependency differences")


if __name__ == "__main__":
    main()