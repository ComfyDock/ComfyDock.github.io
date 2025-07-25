#!/usr/bin/env python3
"""
UV CLI - A command-line interface for testing UVInterface operations.

This script provides a CLI wrapper around the UVInterface class to test
various UV package manager operations.

Usage examples:
    python uv-cli.py venv ./.venv --python 3.12
    python uv-cli.py python --venv /path/to/.venv "print('hello!')"
    python uv-cli.py pip list --venv /path/to/.venv
    python uv-cli.py pip install --venv /path/to/.venv --uv-cache /path/to/uv_cache requests
"""

import argparse
import sys
from pathlib import Path

# Import the hypothetical UVInterface class
# In actual implementation, this would be: from uv_interface import UVInterface
from comfyui_detector.integrations.uv import UVInterface


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        description="UV CLI - Test interface for UV package manager operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a virtual environment
  %(prog)s venv ./.venv --python 3.12

  # Run Python code in a venv
  %(prog)s python --venv /path/to/.venv "print('hello!')"

  # List packages in a venv
  %(prog)s pip list --venv /path/to/.venv

  # Install packages
  %(prog)s pip install --venv /path/to/.venv requests numpy
        """
    )
    
    # Global options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress non-error output"
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # venv command
    venv_parser = subparsers.add_parser(
        "venv",
        help="Create a virtual environment"
    )
    venv_parser.add_argument(
        "path",
        type=Path,
        help="Path where the virtual environment should be created"
    )
    venv_parser.add_argument(
        "--python",
        type=str,
        help="Python version to use (e.g., 3.12, 3.11.7)"
    )
    venv_parser.add_argument(
        "--system-site-packages",
        action="store_true",
        help="Give the virtual environment access to system site packages"
    )
    venv_parser.add_argument(
        "--seed",
        action="store_true",
        help="Install seed packages (pip, setuptools, wheel) into the virtual environment"
    )
    
    # python command
    python_parser = subparsers.add_parser(
        "python",
        help="Run Python code in a virtual environment"
    )
    python_parser.add_argument(
        "code",
        help="Python code to execute or path to Python script"
    )
    python_parser.add_argument(
        "--venv",
        type=Path,
        required=True,
        help="Path to the virtual environment"
    )
    python_parser.add_argument(
        "--args",
        nargs=argparse.REMAINDER,
        help="Additional arguments to pass to the Python script"
    )
    
    # pip subcommand
    pip_parser = subparsers.add_parser(
        "pip",
        help="Package management commands"
    )
    pip_subparsers = pip_parser.add_subparsers(dest="pip_command", help="pip commands")
    
    # pip list
    pip_list_parser = pip_subparsers.add_parser(
        "list",
        help="List installed packages"
    )
    pip_list_parser.add_argument(
        "--venv",
        type=Path,
        required=True,
        help="Path to the virtual environment"
    )
    pip_list_parser.add_argument(
        "--format",
        choices=["columns", "freeze", "json"],
        default="columns",
        help="Output format"
    )
    pip_list_parser.add_argument(
        "--outdated",
        action="store_true",
        help="List only outdated packages"
    )
    
    # pip install
    pip_install_parser = pip_subparsers.add_parser(
        "install",
        help="Install packages"
    )
    pip_install_parser.add_argument(
        "packages",
        nargs="+",
        help="Packages to install"
    )
    pip_install_parser.add_argument(
        "--venv",
        type=Path,
        required=True,
        help="Path to the virtual environment"
    )
    pip_install_parser.add_argument(
        "--uv-cache",
        type=Path,
        help="Path to UV cache directory"
    )
    pip_install_parser.add_argument(
        "--index-url",
        type=str,
        help="Base URL of the Python Package Index"
    )
    pip_install_parser.add_argument(
        "--upgrade",
        action="store_true",
        help="Upgrade packages to the newest available version"
    )
    pip_install_parser.add_argument(
        "--requirements", "-r",
        type=Path,
        help="Install from the given requirements file"
    )
    
    # pip uninstall
    pip_uninstall_parser = pip_subparsers.add_parser(
        "uninstall",
        help="Uninstall packages"
    )
    pip_uninstall_parser.add_argument(
        "packages",
        nargs="+",
        help="Packages to uninstall"
    )
    pip_uninstall_parser.add_argument(
        "--venv",
        type=Path,
        required=True,
        help="Path to the virtual environment"
    )
    
    # pip freeze
    pip_freeze_parser = pip_subparsers.add_parser(
        "freeze",
        help="Output installed packages in requirements format"
    )
    pip_freeze_parser.add_argument(
        "--venv",
        type=Path,
        required=True,
        help="Path to the virtual environment"
    )
    pip_freeze_parser.add_argument(
        "--all",
        action="store_true",
        help="Include all packages including pip, setuptools, etc."
    )
    
    # lock command
    lock_parser = subparsers.add_parser(
        "lock",
        help="Generate or update a lockfile"
    )
    lock_parser.add_argument(
        "--project",
        type=Path,
        default=Path.cwd(),
        help="Path to the project directory"
    )
    lock_parser.add_argument(
        "--upgrade",
        action="store_true",
        help="Upgrade all dependencies to their latest versions"
    )
    lock_parser.add_argument(
        "--upgrade-package",
        action="append",
        help="Upgrade specific package(s) to latest version"
    )
    
    # sync command
    sync_parser = subparsers.add_parser(
        "sync",
        help="Sync the environment with the lockfile"
    )
    sync_parser.add_argument(
        "--project",
        type=Path,
        default=Path.cwd(),
        help="Path to the project directory"
    )
    sync_parser.add_argument(
        "--venv",
        type=Path,
        help="Path to the virtual environment"
    )
    
    return parser


def handle_venv_command(args: argparse.Namespace, uv: UVInterface) -> int:
    """Handle the venv creation command."""
    try:
        if args.verbose:
            print(f"Creating virtual environment at: {args.path}")
            if args.python:
                print(f"Using Python version: {args.python}")
        
        # Call UVInterface to create venv
        result = uv.create_venv(
            path=args.path,
            python_version=args.python,
            system_site_packages=args.system_site_packages,
            seed=args.seed
        )
        
        if result.success:
            if not args.quiet:
                print(f"✓ Virtual environment created successfully at: {args.path}")
            return 0
        else:
            print(f"✗ Failed to create virtual environment: {result.error}", file=sys.stderr)
            return 1
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def handle_python_command(args: argparse.Namespace, uv: UVInterface) -> int:
    """Handle the python execution command."""
    try:
        if args.verbose:
            print(f"Running Python code in venv: {args.venv}")
            print(f"Code: {args.code}")
        
        # Check if code is a file path or actual code
        code_path = Path(args.code)
        if code_path.exists() and code_path.is_file():
            # It's a file, read the content
            with open(code_path, 'r') as f:
                code = f.read()
            is_file = True
        else:
            # It's actual code
            code = args.code
            is_file = False
        
        # Call UVInterface to run Python code
        result = uv.run_python(
            venv_path=args.venv,
            code=code,
            args=args.args or [],
            is_file=is_file
        )
        
        if result.success:
            # Print the output from the Python execution
            if result.output:
                print(result.output, end='')
            return 0
        else:
            print(f"✗ Failed to execute Python code: {result.error}", file=sys.stderr)
            return 1
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def handle_pip_list_command(args: argparse.Namespace, uv: UVInterface) -> int:
    """Handle the pip list command."""
    try:
        if args.verbose:
            print(f"Listing packages in venv: {args.venv}")
        
        # Call UVInterface to list packages
        result = uv.list_packages(
            venv_path=args.venv,
            format=args.format,
            outdated=args.outdated
        )
        
        if result.success:
            if args.format == "json":
                # Pretty print JSON
                import json
                packages = json.loads(result.output)
                print(json.dumps(packages, indent=2))
            else:
                print(result.output, end='')
            return 0
        else:
            print(f"✗ Failed to list packages: {result.error}", file=sys.stderr)
            return 1
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def handle_pip_install_command(args: argparse.Namespace, uv: UVInterface) -> int:
    """Handle the pip install command."""
    try:
        if args.verbose:
            print(f"Installing packages to venv: {args.venv}")
            print(f"Packages: {', '.join(args.packages)}")
            if args.uv_cache:
                print(f"Using UV cache: {args.uv_cache}")
        
        # Handle requirements file
        if args.requirements:
            # Call UVInterface with requirements file
            result = uv.install_requirements(
                venv_path=args.venv,
                requirements_file=args.requirements,
                uv_cache=args.uv_cache,
                index_url=args.index_url,
                upgrade=args.upgrade
            )
        else:
            # Call UVInterface to install packages
            result = uv.install_packages(
                venv_path=args.venv,
                packages=args.packages,
                uv_cache=args.uv_cache,
                index_url=args.index_url,
                upgrade=args.upgrade
            )
        
        if result.success:
            if not args.quiet:
                print("✓ Successfully installed packages")
                if result.output:
                    print(result.output)
            return 0
        else:
            print(f"✗ Failed to install packages: {result.error}", file=sys.stderr)
            return 1
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def handle_pip_uninstall_command(args: argparse.Namespace, uv: UVInterface) -> int:
    """Handle the pip uninstall command."""
    try:
        if args.verbose:
            print(f"Uninstalling packages from venv: {args.venv}")
            print(f"Packages: {', '.join(args.packages)}")
        
        # Call UVInterface to uninstall packages
        result = uv.uninstall_packages(
            venv_path=args.venv,
            packages=args.packages
        )
        
        if result.success:
            if not args.quiet:
                print("✓ Successfully uninstalled packages")
            return 0
        else:
            print(f"✗ Failed to uninstall packages: {result.error}", file=sys.stderr)
            return 1
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def handle_pip_freeze_command(args: argparse.Namespace, uv: UVInterface) -> int:
    """Handle the pip freeze command."""
    try:
        if args.verbose:
            print(f"Freezing packages in venv: {args.venv}")
        
        # Call UVInterface to freeze packages
        result = uv.freeze_packages(
            venv_path=args.venv,
            all_packages=args.all
        )
        
        if result.success:
            print(result.output, end='')
            return 0
        else:
            print(f"✗ Failed to freeze packages: {result.error}", file=sys.stderr)
            return 1
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def handle_lock_command(args: argparse.Namespace, uv: UVInterface) -> int:
    """Handle the lock command."""
    try:
        if args.verbose:
            print(f"Generating lockfile for project: {args.project}")
        
        # Call UVInterface to generate lockfile
        result = uv.generate_lockfile(
            project_path=args.project,
            upgrade=args.upgrade,
            upgrade_packages=args.upgrade_package
        )
        
        if result.success:
            if not args.quiet:
                print("✓ Lockfile generated successfully")
            return 0
        else:
            print(f"✗ Failed to generate lockfile: {result.error}", file=sys.stderr)
            return 1
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def handle_sync_command(args: argparse.Namespace, uv: UVInterface) -> int:
    """Handle the sync command."""
    try:
        if args.verbose:
            print(f"Syncing environment with lockfile for project: {args.project}")
        
        # Call UVInterface to sync environment
        result = uv.sync_environment(
            project_path=args.project,
            venv_path=args.venv
        )
        
        if result.success:
            if not args.quiet:
                print("✓ Environment synced successfully")
            return 0
        else:
            print(f"✗ Failed to sync environment: {result.error}", file=sys.stderr)
            return 1
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main():
    """Main entry point for the UV CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Check if a command was provided
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize UVInterface
    try:
        uv = UVInterface(verbose=args.verbose, quiet=args.quiet)
    except Exception as e:
        print(f"Failed to initialize UVInterface: {e}", file=sys.stderr)
        return 1
    
    # Route to appropriate handler based on command
    if args.command == "venv":
        return handle_venv_command(args, uv)
    
    elif args.command == "python":
        return handle_python_command(args, uv)
    
    elif args.command == "pip":
        if not args.pip_command:
            print("Error: pip command requires a subcommand (list, install, uninstall, freeze)", file=sys.stderr)
            return 1
        
        if args.pip_command == "list":
            return handle_pip_list_command(args, uv)
        elif args.pip_command == "install":
            return handle_pip_install_command(args, uv)
        elif args.pip_command == "uninstall":
            return handle_pip_uninstall_command(args, uv)
        elif args.pip_command == "freeze":
            return handle_pip_freeze_command(args, uv)
        else:
            print(f"Error: Unknown pip command: {args.pip_command}", file=sys.stderr)
            return 1
    
    elif args.command == "lock":
        return handle_lock_command(args, uv)
    
    elif args.command == "sync":
        return handle_sync_command(args, uv)
    
    else:
        print(f"Error: Unknown command: {args.command}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())