"""Command-line interface for ComfyUI environment detection."""

import argparse
import json
import os
import sys
from pathlib import Path

from ..constants import DEFAULT_REGISTRY_URL
from ..core.detector import ComfyUIEnvironmentDetector
from ..core.recreator import EnvironmentRecreator
from ..models.models import MigrationManifest
from ..progress import ProgressReporter
from ..utils.custom_node_cache import CustomNodeCacheManager
from ..common import format_size


def main():
    """Main entry point for the ComfyUI Environment Capture (CEC) tool."""
    parser = argparse.ArgumentParser(
        description="ComfyUI Environment Capture (CEC) tool for environment detection and recreation",
        prog="cec",
    )

    # Add subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Detect subcommand
    detect_parser = subparsers.add_parser(
        "detect", help="Detect and capture ComfyUI environment"
    )
    detect_parser.add_argument(
        "comfyui_path", type=str, help="Path to the ComfyUI installation directory"
    )
    detect_parser.add_argument(
        "--python",
        type=str, 
        help="Python executable used to run ComfyUI (auto-detected if not provided)"
    )
    detect_parser.add_argument(
        "--output-dir",
        type=str,
        default=".",
        help="Directory to save output files (default: current directory)",
    )
    detect_parser.add_argument(
        "--validate-registry",
        action="store_true",
        help="Validate custom nodes against the Comfy Registry API and GitHub",
    )
    detect_parser.add_argument(
        "--registry-url",
        type=str,
        default=DEFAULT_REGISTRY_URL,
        help=f"Comfy Registry API URL (default: {DEFAULT_REGISTRY_URL})",
    )
    detect_parser.add_argument(
        "--skip-custom-nodes",
        action="store_true",
        help="Skip custom node scanning and requirements detection",
    )

    # Recreate subcommand
    recreate_parser = subparsers.add_parser(
        "recreate", help="Recreate ComfyUI environment from a migration manifest"
    )
    recreate_parser.add_argument(
        "manifest_path", type=str, help="Path to the migration manifest JSON file"
    )
    recreate_parser.add_argument(
        "target_path",
        type=str,
        help="Directory where the environment will be recreated",
    )
    recreate_parser.add_argument(
        "--uv-cache-path", type=str, help="Path to UV cache directory (optional)"
    )
    recreate_parser.add_argument(
        "--python-install-path",
        type=str,
        help="Path to UV python installations (optional)",
    )
    recreate_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable custom node caching"
    )

    # Cache management subcommand
    cache_parser = subparsers.add_parser(
        "cache", help="Manage custom node cache"
    )

    # Add cache subcommands
    cache_subparsers = cache_parser.add_subparsers(
        dest="cache_command", help="Cache management commands"
    )

    # Cache list command
    cache_list_parser = cache_subparsers.add_parser(
        "list", help="List cached custom nodes"
    )
    cache_list_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed information"
    )

    # Cache stats command
    cache_subparsers.add_parser(
        "stats", help="Show cache statistics"
    )

    # Cache clear command
    cache_clear_parser = cache_subparsers.add_parser(
        "clear", help="Clear cache entries"
    )
    cache_clear_parser.add_argument(
        "node_name",
        nargs="?",
        help="Specific node name to clear (omit to clear all)"
    )
    cache_clear_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Skip confirmation prompt"
    )

    # Cache verify command
    cache_subparsers.add_parser(
        "verify", help="Verify cache integrity"
    )

    args = parser.parse_args()

    # Check if no command was provided
    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Handle commands
    if args.command == "detect":
        run_detect(args)
    elif args.command == "recreate":
        run_recreate(args)
    elif args.command == "cache":
        run_cache_command(args)


def run_detect(args):
    """Run the environment detection command."""
    # Check for environment variable as well
    validate_registry = args.validate_registry or os.environ.get(
        "COMFYUI_VALIDATE_REGISTRY", ""
    ).lower() in ["true", "1", "yes"]

    # Validate ComfyUI path
    comfyui_path = Path(args.comfyui_path).resolve()
    if not comfyui_path.exists():
        print(f"❌ Error: Path does not exist: {comfyui_path}")
        sys.exit(1)

    if not (comfyui_path / "main.py").exists():
        print("❌ Error: Not a valid ComfyUI installation (main.py not found)")
        print(f"   Path: {comfyui_path}")
        sys.exit(1)

    # Handle --python with proper path expansion and resolution BEFORE changing directories
    python_hint = None
    if args.python:
        # Expand ~ and resolve the path properly (before changing directories)
        python_path = Path(args.python).expanduser().absolute()
        
        # Verify the python executable exists
        if not python_path.exists():
            print(f"❌ Error: Python executable not found: {args.python}")
            print(f"   Resolved to: {python_path}")
            sys.exit(1)
            
        if not python_path.is_file():
            print(f"❌ Error: Python path is not a file: {python_path}")
            sys.exit(1)
            
        python_hint = python_path
        print(f"Using Python executable: {python_hint}")

    # Change to output directory (after resolving python path)
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(output_dir)
    
    # Create progress reporter
    progress = ProgressReporter(verbose=args.__dict__.get('verbose', False))
        
    detector = ComfyUIEnvironmentDetector(
        comfyui_path, 
        python_hint=python_hint,
        validate_registry=validate_registry,
        skip_custom_nodes=args.skip_custom_nodes,
        progress_reporter=progress
    )

    # Set custom registry URL if provided
    if validate_registry and args.registry_url != DEFAULT_REGISTRY_URL and detector.custom_node_scanner:
        detector.custom_node_scanner.registry_validator.base_url = args.registry_url

    config = detector.detect_all()

    # Print summary based on the lean manifest
    print_detection_summary(config)

    print("\n📁 Output files:")
    print("  - comfyui_migration.json      (lean manifest for environment recreation)")
    print("  - comfyui_detection_log.json  (detailed analysis for debugging)")
    print("  - comfyui_requirements.txt    (Python packages)")

    print("\n✨ Migration manifest ready!")
    print("   Use 'comfyui_migration.json' to recreate this environment")

    # If validation was performed, mention it
    if validate_registry:
        print("\n📌 Note: Registry/GitHub validation was performed.")
        print("   Check 'comfyui_detection_log.json' for detailed validation results.")


def print_detection_summary(config: dict):
    """Print a summary of the detection results."""
    print("\n📋 Summary:")
    print(f"  Python: {config['system_info']['python_version']}")
    print(f"  CUDA: {config['system_info']['cuda_version'] or 'Not detected'}")
    print(f"  PyTorch: {config['system_info']['torch_version'] or 'Not detected'}")
    print(f"  ComfyUI: {config['system_info']['comfyui_version']}")

    # Analyze custom nodes by install method
    install_methods = {}
    for node in config["custom_nodes"]:
        method = node.get("install_method", "unknown")
        install_methods[method] = install_methods.get(method, 0) + 1

    print(f"\n  Custom nodes: {len(config['custom_nodes'])}")
    for method, count in sorted(install_methods.items()):
        print(f"    - {method}: {count}")

    # Package counts
    regular_packages = len(config["dependencies"].get("packages", {}))
    pytorch_packages = len(
        config["dependencies"].get("pytorch", {}).get("packages", {})
    )
    editable = len(config["dependencies"].get("editable_installs", []))
    git_reqs = len(config["dependencies"].get("git_requirements", []))

    print("\n  Dependencies:")
    print(f"    - Regular packages: {regular_packages}")
    if pytorch_packages > 0:
        print(f"    - PyTorch packages: {pytorch_packages}")
    if editable > 0:
        print(f"    - Editable installs: {editable}")
    if git_reqs > 0:
        print(f"    - Git requirements: {git_reqs}")


def run_recreate(args):
    """Run the environment recreation command."""
    # Validate manifest path
    manifest_path = Path(args.manifest_path).resolve()
    if not manifest_path.exists():
        print(f"❌ Error: Manifest file not found: {manifest_path}", file=sys.stderr)
        sys.exit(1)

    # Try to load and validate the manifest
    try:
        manifest_content = manifest_path.read_text()
        # Validate manifest by attempting to parse it
        MigrationManifest.from_json(manifest_content)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in manifest file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: Failed to parse manifest: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate target path
    target_path = Path(args.target_path).resolve()
    if target_path.exists() and any(target_path.iterdir()):
        print(
            f"❌ Error: Target directory already exists and is not empty: {target_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Set up paths with defaults
    if args.uv_cache_path:
        uv_cache_path = Path(args.uv_cache_path).resolve()
    else:
        # Use UV's default cache location
        uv_cache_path = Path.home() / ".cache" / "uv"

    if args.python_install_path:
        python_install_path = Path(args.python_install_path).resolve()
    else:
        # Use UV's default python location
        python_install_path = Path.home() / ".local" / "share" / "uv" / "python"

    # Create the recreator
    try:
        # Create progress reporter
        progress = ProgressReporter(verbose=args.__dict__.get('verbose', False))
        
        recreator = EnvironmentRecreator(
            manifest_path=manifest_path,
            target_path=target_path,
            uv_cache_path=uv_cache_path,
            python_install_path=python_install_path,
            progress_reporter=progress,
            enable_cache=not args.no_cache
        )
    except Exception as e:
        print(f"❌ Error: Failed to initialize recreator: {e}", file=sys.stderr)
        sys.exit(1)

    # Perform the recreation
    print(f"🔄 Recreating environment from: {manifest_path}")
    print(f"📁 Target directory: {target_path}")

    try:
        result = recreator.recreate()
    except Exception as e:
        print(f"❌ Error: Recreation failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Display results
    if result.success:
        print(f"\n✅ Successfully recreated environment at: {result.environment_path}")
        print(f"   Virtual environment: {result.venv_path}")
        print(f"   ComfyUI: {result.comfyui_path}")

        if result.installed_packages:
            print(f"📦 Installed {len(result.installed_packages)} Python packages")

        if result.installed_nodes:
            print(f"🔌 Installed {len(result.installed_nodes)} custom nodes")

        if result.warnings:
            print("\n⚠️  Warnings:")
            for warning in result.warnings:
                print(f"   - {warning}")

        print(f"\n⏱️  Completed in {result.duration_seconds:.1f} seconds")
        sys.exit(0)
    else:
        print("\n❌ Failed to recreate environment", file=sys.stderr)

        if result.errors:
            print("\n🚨 Errors:", file=sys.stderr)
            for error in result.errors:
                print(f"   - {error}", file=sys.stderr)

        if result.warnings:
            print("\n⚠️  Warnings:", file=sys.stderr)
            for warning in result.warnings:
                print(f"   - {warning}", file=sys.stderr)

        sys.exit(1)


def run_cache_command(args):
    """Handle cache management commands."""
    cache_manager = CustomNodeCacheManager()
    
    if args.cache_command == "list":
        list_cached_nodes(cache_manager, args.verbose)
    elif args.cache_command == "stats":
        show_cache_stats(cache_manager)
    elif args.cache_command == "clear":
        clear_cache(cache_manager, args.node_name, args.force)
    elif args.cache_command == "verify":
        verify_cache(cache_manager)
    else:
        print("Please specify a cache subcommand: list, stats, clear, verify")
        sys.exit(1)


def list_cached_nodes(cache_manager: CustomNodeCacheManager, verbose: bool = False):
    """List all cached custom nodes."""
    nodes = cache_manager.list_cached_nodes()
    
    if not nodes:
        print("No custom nodes cached.")
        return
    
    # Sort by name
    nodes.sort(key=lambda x: x.name)
    
    print(f"\n📦 Cached Custom Nodes ({len(nodes)} total):")
    print("=" * 70)
    
    if verbose:
        # Detailed view
        for node in nodes:
            print(f"\n📌 {node.name}")
            print(f"   Cache Key: {node.cache_key}")
            print(f"   Method: {node.install_method}")
            print(f"   URL: {node.url}")
            if node.ref:
                print(f"   Ref: {node.ref}")
            print(f"   Size: {format_size(node.size_bytes)}")
            print(f"   Cached: {node.cached_at}")
            print(f"   Accessed: {node.access_count} times")
            print(f"   Last Access: {node.last_accessed}")
    else:
        # Simple table view
        print(f"{'Name':<30} {'Method':<10} {'Size':<10} {'Accessed':<10}")
        print("-" * 70)
        for node in nodes:
            print(f"{node.name:<30} {node.install_method:<10} "
                  f"{format_size(node.size_bytes):<10} {node.access_count:<10}")
    
    # Show total size
    total_size = sum(node.size_bytes for node in nodes)
    print("-" * 70)
    print(f"Total cache size: {format_size(total_size)}")


def show_cache_stats(cache_manager: CustomNodeCacheManager):
    """Show cache statistics."""
    stats = cache_manager.get_cache_stats()
    
    print("\n📊 Cache Statistics")
    print("=" * 50)
    print(f"Cache Directory: {stats['cache_directory']}")
    print(f"Total Nodes: {stats['total_nodes']}")
    print(f"Total Size: {stats['total_size_human']}")
    
    # Nodes by method
    print("\nNodes by Install Method:")
    for method, count in stats['nodes_by_method'].items():
        print(f"  - {method}: {count}")
    
    # Most accessed
    if stats['most_accessed']:
        print("\nMost Accessed Nodes:")
        for node in stats['most_accessed']:
            print(f"  - {node['name']}: {node['access_count']} times ({node['size']})")
    
    # Recently cached
    if stats['recently_cached']:
        print("\nRecently Cached:")
        for node in stats['recently_cached']:
            print(f"  - {node['name']}: {node['cached_at']} ({node['size']})")


def clear_cache(cache_manager: CustomNodeCacheManager, node_name: str = None, force: bool = False):
    """Clear cache entries."""
    if node_name:
        # Check if the node exists in cache
        nodes = [n for n in cache_manager.list_cached_nodes() if n.name == node_name]
        if not nodes:
            print(f"❌ No cached entries found for: {node_name}")
            return
        
        # Calculate size to be freed
        size_to_free = sum(n.size_bytes for n in nodes)
        
        if not force:
            response = input(f"Clear cache for '{node_name}' ({format_size(size_to_free)})? [y/N]: ")
            if response.lower() != 'y':
                print("Cancelled.")
                return
    else:
        # Clear all cache
        stats = cache_manager.get_cache_stats()
        total_size = stats['total_size_human']
        total_nodes = stats['total_nodes']
        
        if not force:
            response = input(f"Clear entire cache ({total_nodes} nodes, {total_size})? [y/N]: ")
            if response.lower() != 'y':
                print("Cancelled.")
                return
    
    # Perform the clear
    cleared = cache_manager.clear_cache(node_name)
    
    if node_name:
        print(f"✅ Cleared cache for {node_name} ({cleared} entries)")
    else:
        print(f"✅ Cleared entire cache ({cleared} entries)")


def verify_cache(cache_manager: CustomNodeCacheManager):
    """Verify cache integrity."""
    nodes = cache_manager.list_cached_nodes()
    
    if not nodes:
        print("No cached nodes to verify.")
        return
    
    print(f"\n🔍 Verifying {len(nodes)} cached nodes...")
    
    valid_count = 0
    invalid_nodes = []
    
    for node in nodes:
        if cache_manager.verify_cache_integrity(node.cache_key):
            valid_count += 1
        else:
            invalid_nodes.append(node.name)
    
    print(f"\n✅ Valid: {valid_count}/{len(nodes)}")
    
    if invalid_nodes:
        print(f"❌ Invalid: {len(invalid_nodes)}")
        for name in invalid_nodes:
            print(f"   - {name}")
        
        response = input("\nRemove invalid entries? [y/N]: ")
        if response.lower() == 'y':
            for name in invalid_nodes:
                cache_manager.clear_cache(name)
            print(f"Removed {len(invalid_nodes)} invalid entries.")
    else:
        print("All cached nodes are valid!")


if __name__ == "__main__":
    main()
