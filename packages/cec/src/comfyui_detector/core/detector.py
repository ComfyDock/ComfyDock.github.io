"""Main ComfyUI environment detector class."""

from pathlib import Path
from typing import Dict, Optional

from ..detection.system_detector import SystemDetector
from ..detection.package_detector import PackageDetector
from ..detection.custom_node_scanner import CustomNodeScanner
from .manifest_generator import ManifestGenerator
from ..logging_config import get_logger
from ..progress import ProgressReporter


class ComfyUIEnvironmentDetector:
    """Detects and captures all system dependencies and requirements from an existing ComfyUI setup."""
    
    def __init__(self, comfyui_path: Path, python_hint: Path = None, validate_registry: bool = False, skip_custom_nodes: bool = False, progress_reporter: Optional[ProgressReporter] = None):
        self.logger = get_logger(__name__)
        self.comfyui_path = Path(comfyui_path).resolve()
        self.python_hint = Path(python_hint) if python_hint else None
        self.validate_registry = validate_registry
        self.skip_custom_nodes = skip_custom_nodes
        self.progress = progress_reporter or ProgressReporter()
        
        print(f"ComfyUI path: {self.comfyui_path}")
        if self.python_hint:
            print(f"Python hint: {self.python_hint}")
        if self.skip_custom_nodes:
            print("Skipping custom node scanning")
        
        # Initialize component detectors
        self.system_detector = SystemDetector(self.comfyui_path, python_hint=self.python_hint)
        self.package_detector = None  # Will be initialized after system detection
        self.custom_node_scanner = None if skip_custom_nodes else CustomNodeScanner(self.comfyui_path, validate_registry)
        self.manifest_generator = ManifestGenerator(self.comfyui_path)
        
    def detect_all(self) -> Dict:
        """Main detection method that runs all detection routines."""
        self.logger.info("Starting ComfyUI environment detection...")
        self.logger.info(f"ComfyUI path: {self.comfyui_path}")
        
        self.progress.start_phase("Environment Detection")
        
        # 1. Detect system information
        self.progress.start_task("Detecting system information")
        system_info = self.system_detector.detect_all()
        self.progress.complete_task(f"Python {system_info['python_version']}, "
                                  f"CUDA {system_info.get('cuda_version', 'None')}")
        
        # 2. Initialize package detector with detected Python executable
        self.package_detector = PackageDetector(
            self.comfyui_path,
            self.system_detector.python_executable
        )
        
        # 3. Detect packages and requirements
        self.progress.start_task("Detecting installed packages")
        package_info = self.package_detector.detect_all()
        total_pkgs = len(package_info.get('installed_packages', {}))
        self.progress.complete_task(f"{total_pkgs} packages found")
        
        # 4. Scan custom nodes for requirements (if not skipped)
        custom_node_reqs = {}
        custom_nodes_info = {}
        
        if not self.skip_custom_nodes and self.custom_node_scanner:
            self.custom_node_scanner.progress = self.progress  # Set progress reporter
            custom_node_reqs = self.custom_node_scanner.scan_requirements()
            
            # Add custom node requirements to package detector
            for _, node_reqs in custom_node_reqs.get('requirements', {}).items():
                for package, versions in node_reqs.items():
                    self.package_detector.add_custom_node_requirements(package, versions)
            
            # Store nodes with install scripts in package info
            if custom_node_reqs.get('nodes_with_install_scripts'):
                package_info['nodes_with_install_scripts'] = custom_node_reqs['nodes_with_install_scripts']
            
            # 5. Scan custom nodes in detail
            custom_nodes_info = self.custom_node_scanner.scan_all()
        
        # Re-resolve conflicts after adding custom node requirements
        package_info['resolved_requirements'] = self.package_detector.resolve_requirement_conflicts()
        package_info['conflicts'] = self.package_detector.conflicts
        
        # 6. Generate manifest
        self.progress.start_task("Generating manifest files")
        manifest = self.manifest_generator.generate(
            system_info, 
            custom_nodes_info, 
            package_info,
            self.package_detector.conflicts
        )
        self.progress.complete_task("3 files generated")
        
        return manifest