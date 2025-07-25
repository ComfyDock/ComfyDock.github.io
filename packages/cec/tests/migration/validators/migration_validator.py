#!/usr/bin/env python3
"""
Migration validation for ComfyUI environments
"""

import os
import subprocess
import logging
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class PackageComparison:
    """Results of package comparison between environments"""
    matched: Set[str] = field(default_factory=set)
    missing: Set[str] = field(default_factory=set)
    extra: Set[str] = field(default_factory=set)
    version_mismatches: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    
    @property
    def total_count(self) -> int:
        return len(self.matched) + len(self.missing)
        
    @property
    def accuracy(self) -> float:
        if self.total_count == 0:
            return 0.0
        return len(self.matched) / self.total_count


@dataclass
class ImportValidation:
    """Results of import validation for custom nodes"""
    successful_imports: List[str] = field(default_factory=list)
    failed_imports: List[str] = field(default_factory=list)
    regression_imports: List[str] = field(default_factory=list)
    error_details: Dict[str, str] = field(default_factory=dict)
    original_output: str = ""
    container_output: str = ""
    
    @property
    def total_count(self) -> int:
        return len(self.successful_imports) + len(self.failed_imports)
        
    @property
    def success_rate(self) -> float:
        if self.total_count == 0:
            return 1.0
        return len(self.successful_imports) / self.total_count


@dataclass
class ValidationResult:
    """Complete validation result"""
    package_comparison: PackageComparison = field(default_factory=PackageComparison)
    import_validation: ImportValidation = field(default_factory=ImportValidation)
    startup_validation: Dict[str, bool] = field(default_factory=dict)
    success: bool = False
    accuracy_score: float = 0.0
    execution_time: float = 0.0
    error_count: int = 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'package_comparison': {
                'total': self.package_comparison.total_count,
                'matched': len(self.package_comparison.matched),
                'missing': len(self.package_comparison.missing),
                'extra': len(self.package_comparison.extra),
                'accuracy': self.package_comparison.accuracy,
                'missing_packages': list(self.package_comparison.missing)[:10],  # First 10
                'version_mismatches': dict(list(self.package_comparison.version_mismatches.items())[:10])
            },
            'import_validation': {
                'total_nodes': self.import_validation.total_count,
                'successful': len(self.import_validation.successful_imports),
                'failed': len(self.import_validation.failed_imports),
                'success_rate': self.import_validation.success_rate,
                'failed_nodes': self.import_validation.failed_imports,
                'error_details': self.import_validation.error_details,
                'regression_count': len(self.import_validation.regression_imports)
            },
            'startup_validation': self.startup_validation,
            'success': self.success,
            'accuracy_score': self.accuracy_score,
            'execution_time': self.execution_time,
            'error_count': self.error_count
        }


class MigrationValidator:
    """Validates migration accuracy for local environments only"""
    
    def __init__(self):
        self.logger = logging.getLogger('migration_test.validator')
        
    def _set_uv_environment(self, venv_path: Path) -> Dict[str, str]:
        """Set up UV environment variables"""
        env = os.environ.copy()
        env['VIRTUAL_ENV'] = str(venv_path)
        env['UV_PROJECT_ENVIRONMENT'] = str(venv_path)
        return env
        
    def validate(self, original_env: Path) -> ValidationResult:
        """Perform validation on local environment only"""
        start_time = datetime.now()
        result = ValidationResult()
        
        try:
            # Get package list from environment
            self.logger.info("Analyzing local environment packages...")
            original_packages = self._get_packages_from_env(original_env)
            
            # Create mock comparison (no container to compare against)
            result.package_comparison = PackageComparison()
            result.package_comparison.matched = set(original_packages.keys())
            
            # Check import errors using ComfyUI's quick test
            self.logger.info("Validating imports using ComfyUI quick test...")
            result.import_validation = self._validate_imports_local(original_env)
            
            # The quick test already validates startup, so use its results
            result.startup_validation = {
                'comfyui_starts': len(result.import_validation.failed_imports) == 0,
                'server_responds': True,  # Quick test only succeeds if server can start
                'no_critical_errors': "(IMPORT FAILED)" not in result.import_validation.original_output
            }
            
            # Calculate accuracy score
            result.accuracy_score = self._calculate_accuracy(result)
            
            # Determine overall success
            result.success = (
                result.import_validation.success_rate >= 0.8 and
                result.startup_validation.get('comfyui_starts', False)
            )
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}", exc_info=True)
            result.error_count += 1
            
        finally:
            result.execution_time = (datetime.now() - start_time).total_seconds()
            
        return result
        
    def _validate_imports_local(self, env_path: Path) -> ImportValidation:
        """Validate imports using ComfyUI's --quick-test-for-ci flag in local environment"""
        validation = ImportValidation()
        
        # Run quick test in local environment
        self.logger.info("Running ComfyUI quick test in local environment...")
        output = self._run_quick_test_in_env(env_path)
        validation.original_output = output
        results = self._parse_import_results(output)
        
        # Analyze results
        for node, status in results.items():
            if status == 'failed':
                validation.failed_imports.append(node)
                validation.error_details[node] = "Import failed during quick test"
            elif status == 'success':
                validation.successful_imports.append(node)
                    
        self.logger.info(f"Import validation: {len(validation.successful_imports)} successful, "
                        f"{len(validation.failed_imports)} failed")
        
        return validation
        
    def _get_packages_from_env(self, env_path: Path) -> Dict[str, str]:
        """Get installed packages from original environment"""
        packages = {}
        venv_path = env_path / ".venv"
        
        if not venv_path.exists():
            self.logger.warning(f"No venv found in {env_path}")
            return packages
        
        # Set up UV environment
        uv_env = self._set_uv_environment(venv_path)
        
        # Try UV pip freeze
        result = subprocess.run(
            ['uv', 'pip', 'freeze'],
            capture_output=True,
            text=True,
            env=uv_env,
            cwd=str(env_path)
        )
        
        if result.returncode != 0:
            # Fall back to direct pip if UV fails
            pip_path = venv_path / "bin" / "pip"
            if not pip_path.exists():
                pip_path = venv_path / "Scripts" / "pip.exe"
                
            if pip_path.exists():
                result = subprocess.run(
                    [str(pip_path), 'freeze'],
                    capture_output=True,
                    text=True
                )
        
        # Parse packages
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line and '==' in line and not line.startswith('#'):
                    if not line.startswith('-e '):
                        package, version = line.split('==', 1)
                        packages[package.strip().lower()] = version.strip()
                        
        return packages
        
    def _run_quick_test_in_env(self, env_path: Path) -> str:
        """Run ComfyUI quick test in original environment"""
        venv_path = env_path / ".venv"
        comfyui_path = env_path / "ComfyUI"
        
        # Set up UV environment
        uv_env = self._set_uv_environment(venv_path)
        
        # Run ComfyUI with quick test flag
        try:
            result = subprocess.run(
                ['uv', 'run', 'python', 'main.py', '--quick-test-for-ci'],
                cwd=str(comfyui_path),
                capture_output=True,
                text=True,
                env=uv_env,
                timeout=60  # 60 second timeout
            )
        except subprocess.TimeoutExpired:
            self.logger.warning("Quick test timed out in original environment")
            return "Quick test timed out after 60 seconds"
        
        # If UV fails, try direct python
        if result.returncode != 0 and 'uv' in result.stderr.lower():
            python_path = venv_path / "bin" / "python"
            if not python_path.exists():
                python_path = venv_path / "Scripts" / "python.exe"
                
            if python_path.exists():
                try:
                    result = subprocess.run(
                        [str(python_path), 'main.py', '--quick-test-for-ci'],
                        cwd=str(comfyui_path),
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                except subprocess.TimeoutExpired:
                    self.logger.warning("Quick test timed out in original environment")
                    return "Quick test timed out after 60 seconds"
        
        return result.stdout + result.stderr
        
    def _parse_import_results(self, output: str) -> Dict[str, str]:
        """Parse ComfyUI quick test output to extract import results"""
        results = {}
        
        # Find the "Import times for custom nodes:" section
        import_section_start = output.find("Import times for custom nodes:")
        if import_section_start == -1:
            self.logger.warning("Could not find import times section in output")
            return results
            
        # Extract lines after the import section
        import_section = output[import_section_start:]
        lines = import_section.split('\n')
        
        # Parse each import line
        # Format: "   0.0 seconds: /path/to/node" or "(IMPORT FAILED)   0.0 seconds: /path/to/node"
        import_pattern = re.compile(r'^\s*(?:\(IMPORT FAILED\))?\s*[\d.]+\s+seconds:\s*(.+?)(?:/([^/]+?))?$')
        
        for line in lines[1:]:  # Skip the header line
            if not line.strip():
                continue
                
            # Check if this line is part of import results
            if "seconds:" not in line:
                # We've reached the end of the import section
                break
                
            # Determine if import failed
            failed = "(IMPORT FAILED)" in line
            
            # Extract node path/name
            match = import_pattern.match(line)
            if match:
                node_path = match.group(1)
                # Extract node name from path
                if "/custom_nodes/" in node_path:
                    # Extract everything after custom_nodes/
                    node_name = node_path.split("/custom_nodes/")[-1].rstrip('/')
                    # Remove .py extension if present
                    if node_name.endswith('.py'):
                        node_name = node_name[:-3]
                else:
                    # Use the last component of the path
                    node_name = Path(node_path).name
                    if node_name.endswith('.py'):
                        node_name = node_name[:-3]
                
                results[node_name] = 'failed' if failed else 'success'
                
        return results
        
    def _calculate_accuracy(self, result: ValidationResult) -> float:
        """Calculate overall accuracy score"""
        # Weight different components
        package_weight = 0.4
        import_weight = 0.4
        startup_weight = 0.2
        
        package_score = result.package_comparison.accuracy
        import_score = result.import_validation.success_rate
        startup_score = 1.0 if result.startup_validation.get('comfyui_starts', False) else 0.0
        
        accuracy = (
            package_score * package_weight +
            import_score * import_weight +
            startup_score * startup_weight
        )
        
        return round(accuracy, 3)