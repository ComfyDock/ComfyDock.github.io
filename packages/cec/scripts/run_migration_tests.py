#!/usr/bin/env python3
"""
Simplified migration test runner for CEC detection validation
"""

import logging
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import modules after path setup (ruff E402 exception needed for dynamic imports)
from comfyui_detector import ComfyUIEnvironmentDetector  # noqa: E402
from tests.migration.builders.environment_builder import TestEnvironmentBuilder  # noqa: E402  
from tests.migration.config.test_config import load_test_config  # noqa: E402
from tests.migration.metrics.collector import MetricsCollector  # noqa: E402
from tests.migration.utils.error_handler import ErrorRecoveryHandler  # noqa: E402


class DetectionTestOrchestrator:
    """Simplified test orchestrator for CEC detection validation"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.logger = logging.getLogger('migration_test.orchestrator')
        self.config = load_test_config(config_path)
        self.builder = TestEnvironmentBuilder()
        self.error_handler = ErrorRecoveryHandler()
        self.metrics = MetricsCollector()
        
    def run_detection_tests(self) -> Dict:
        """Run detection validation tests on various ComfyUI setups"""
        self.logger.info("Starting CEC detection validation tests")
        
        results = {
            'test_scenarios': [],
            'overall_success': True,
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0
        }
        
        # Get test scenarios from config
        test_scenarios = self.config.get('test_scenarios', [])
        
        for scenario in test_scenarios:
            self.logger.info(f"Running test scenario: {scenario.get('name', 'Unknown')}")
            
            scenario_result = self._run_scenario(scenario)
            results['test_scenarios'].append(scenario_result)
            results['total_tests'] += 1
            
            if scenario_result['success']:
                results['passed_tests'] += 1
            else:
                results['failed_tests'] += 1
                results['overall_success'] = False
                
        self.logger.info(f"Detection tests completed: {results['passed_tests']}/{results['total_tests']} passed")
        return results
        
    def _run_scenario(self, scenario: Dict) -> Dict:
        """Run a single test scenario"""
        scenario_name = scenario.get('name', 'Unknown')
        comfyui_version = scenario.get('comfyui_version', {})
        custom_nodes = scenario.get('custom_nodes', [])
        python_version = scenario.get('python_version', '3.10')
        
        result = {
            'scenario_name': scenario_name,
            'success': False,
            'detection_result': None,
            'environment_path': None,
            'error': None,
            'metrics': {}
        }
        
        temp_env = None
        try:
            # Build test environment
            self.logger.info(f"Building test environment for {scenario_name}")
            temp_env = self.builder.create_environment(
                comfyui_version=comfyui_version,
                python_version=python_version,
                custom_nodes=custom_nodes
            )
            result['environment_path'] = str(temp_env)
            
            # Run CEC detection on the test environment
            self.logger.info(f"Running CEC detection on {scenario_name}")
            detection_result = self._run_cec_detection(temp_env)
            result['detection_result'] = detection_result
            
            # Validate detection results
            self.logger.info(f"Validating detection results for {scenario_name}")
            validation_result = self._validate_detection(detection_result, custom_nodes)
            result['metrics'] = validation_result
            
            result['success'] = validation_result.get('overall_accuracy', 0) >= 0.8
            
        except Exception as e:
            self.logger.error(f"Scenario {scenario_name} failed: {e}", exc_info=True)
            result['error'] = str(e)
            
        finally:
            # Clean up environment if requested
            if temp_env and self.config.get('cleanup_after_test', True):
                try:
                    shutil.rmtree(temp_env, ignore_errors=True)
                except Exception as e:
                    self.logger.warning(f"Failed to cleanup {temp_env}: {e}")
                    
        return result
        
    def _run_cec_detection(self, env_path: Path) -> Dict:
        """Run CEC ComfyUI environment detection"""
        comfyui_path = env_path / "ComfyUI"
        
        if not comfyui_path.exists():
            raise ValueError(f"ComfyUI not found in {env_path}")
            
        # Initialize CEC detector
        detector = ComfyUIEnvironmentDetector(comfyui_path=str(comfyui_path))
        
        # Run detection
        detection_results = detector.detect_all()
        
        # Generate migration manifest
        manifest = detector.generate_migration_config()
        
        return {
            'detection_results': detection_results,
            'migration_manifest': manifest.dict() if hasattr(manifest, 'dict') else manifest,
            'comfyui_path': str(comfyui_path)
        }
        
    def _validate_detection(self, detection_result: Dict, 
                          expected_nodes: List[str]) -> Dict:
        """Validate that detection results are accurate"""
        validation = {
            'custom_nodes_accuracy': 0.0,
            'packages_detected': 0,
            'python_version_detected': False,
            'pytorch_detected': False,
            'overall_accuracy': 0.0,
            'details': {}
        }
        
        try:
            manifest = detection_result.get('migration_manifest', {})
            
            # Validate custom nodes detection
            detected_nodes = manifest.get('custom_nodes', [])
            detected_node_names = [node.get('name', '') for node in detected_nodes]
            
            # Calculate custom nodes accuracy
            expected_set = set(expected_nodes)
            detected_set = set(detected_node_names)
            
            if expected_set:
                matched = expected_set & detected_set
                validation['custom_nodes_accuracy'] = len(matched) / len(expected_set)
                validation['details']['expected_nodes'] = list(expected_set)
                validation['details']['detected_nodes'] = list(detected_set)
                validation['details']['matched_nodes'] = list(matched)
                validation['details']['missing_nodes'] = list(expected_set - detected_set)
                validation['details']['extra_nodes'] = list(detected_set - expected_set)
            else:
                validation['custom_nodes_accuracy'] = 1.0  # No nodes expected, none needed
                
            # Validate package detection
            packages = manifest.get('packages', [])
            validation['packages_detected'] = len(packages)
            
            # Validate system info detection
            system_info = manifest.get('system_info', {})
            validation['python_version_detected'] = bool(system_info.get('python_version'))
            validation['pytorch_detected'] = bool(system_info.get('pytorch_version'))
            
            # Calculate overall accuracy
            accuracy_components = [
                validation['custom_nodes_accuracy'],
                1.0 if validation['packages_detected'] > 0 else 0.0,
                1.0 if validation['python_version_detected'] else 0.0,
                1.0 if validation['pytorch_detected'] else 0.0
            ]
            validation['overall_accuracy'] = sum(accuracy_components) / len(accuracy_components)
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}", exc_info=True)
            validation['details']['validation_error'] = str(e)
            
        return validation


def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    config_path = None
    if len(sys.argv) > 1:
        config_path = Path(sys.argv[1])
        
    orchestrator = DetectionTestOrchestrator(config_path)
    results = orchestrator.run_detection_tests()
    
    # Print summary
    print(f"\n{'='*50}")
    print("CEC Detection Validation Results")
    print(f"{'='*50}")
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed_tests']}")
    print(f"Failed: {results['failed_tests']}")
    print(f"Overall Success: {results['overall_success']}")
    
    # Exit with appropriate code
    sys.exit(0 if results['overall_success'] else 1)


if __name__ == '__main__':
    main()