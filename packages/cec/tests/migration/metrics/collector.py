#!/usr/bin/env python3
"""
Metrics collection and reporting for ComfyUI migration tests
"""

import json
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from dataclasses import dataclass, field
import statistics


@dataclass
class TestMetrics:
    """Metrics for a single test"""
    test_id: str
    comfyui_version: str
    scenario: str
    timestamp: datetime
    
    # Package metrics
    total_packages: int = 0
    matched_packages: int = 0
    missing_packages: int = 0
    package_accuracy: float = 0.0
    
    # Import metrics
    total_custom_nodes: int = 0
    successful_imports: int = 0
    failed_imports: int = 0
    import_success_rate: float = 0.0
    
    # Overall metrics
    migration_success: bool = False
    accuracy_score: float = 0.0
    execution_time: float = 0.0
    error_count: int = 0
    
    # Error details
    errors: List[Dict[str, Any]] = field(default_factory=list)
    recovery_actions: List[Dict[str, Any]] = field(default_factory=list)


class MetricsCollector:
    """Collects and aggregates test metrics"""
    
    def __init__(self):
        self.logger = logging.getLogger('migration_test.metrics')
        self.metrics_data: List[TestMetrics] = []
        self.failures: List[Dict[str, Any]] = []
        
    def record_test_result(self, test_context: Dict, validation_result: Dict):
        """Record metrics for a single test"""
        metrics = TestMetrics(
            test_id=test_context['test_id'],
            comfyui_version=test_context['comfyui_version']['version'],
            scenario=test_context['scenario']['name'],
            timestamp=test_context['start_time'],
            
            # Package metrics
            total_packages=validation_result['package_comparison']['total'],
            matched_packages=validation_result['package_comparison']['matched'],
            missing_packages=validation_result['package_comparison']['missing'],
            package_accuracy=validation_result['package_comparison']['accuracy'],
            
            # Import metrics
            total_custom_nodes=validation_result['import_validation']['total_nodes'],
            successful_imports=validation_result['import_validation']['successful'],
            failed_imports=validation_result['import_validation']['failed'],
            import_success_rate=validation_result['import_validation']['success_rate'],
            
            # Overall metrics
            migration_success=validation_result['success'],
            accuracy_score=validation_result['accuracy_score'],
            execution_time=validation_result['execution_time'],
            error_count=validation_result['error_count']
        )
        
        self.metrics_data.append(metrics)
        self.logger.info(f"Recorded metrics for {metrics.test_id}")
        
    def record_failure(self, test_context: Dict, error: Exception):
        """Record a test failure"""
        failure = {
            'test_id': test_context['test_id'],
            'comfyui_version': test_context['comfyui_version']['version'],
            'scenario': test_context['scenario']['name'],
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error)
        }
        
        self.failures.append(failure)
        self.logger.error(f"Recorded failure for {test_context['test_id']}: {error}")
        
    def get_all_metrics(self) -> List[Dict[str, Any]]:
        """Get all collected metrics as dictionaries"""
        return [
            {
                'test_id': m.test_id,
                'comfyui_version': m.comfyui_version,
                'scenario': m.scenario,
                'timestamp': m.timestamp.isoformat(),
                'total_packages': m.total_packages,
                'matched_packages': m.matched_packages,
                'missing_packages': m.missing_packages,
                'package_accuracy': m.package_accuracy,
                'total_custom_nodes': m.total_custom_nodes,
                'successful_imports': m.successful_imports,
                'failed_imports': m.failed_imports,
                'import_success_rate': m.import_success_rate,
                'migration_success': m.migration_success,
                'accuracy_score': m.accuracy_score,
                'execution_time': m.execution_time,
                'error_count': m.error_count
            }
            for m in self.metrics_data
        ]
        
    def generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics"""
        # Include both metrics_data and failures in total count
        total_tests = len(self.metrics_data) + len(self.failures)
        
        if total_tests == 0:
            return {
                'total_tests': 0,
                'successful_tests': 0,
                'failed_tests': 0,
                'overall_accuracy': 0.0
            }
            
        successful_tests = sum(1 for m in self.metrics_data if m.migration_success)
        # Failed tests include both failed metrics and recorded failures
        failed_tests = total_tests - successful_tests
        
        accuracy_scores = [m.accuracy_score for m in self.metrics_data]
        package_accuracies = [m.package_accuracy for m in self.metrics_data]
        import_success_rates = [m.import_success_rate for m in self.metrics_data]
        execution_times = [m.execution_time for m in self.metrics_data]
        
        # Group by version
        version_stats = {}
        for metric in self.metrics_data:
            version = metric.comfyui_version
            if version not in version_stats:
                version_stats[version] = {
                    'total': 0,
                    'successful': 0,
                    'accuracy_scores': []
                }
            version_stats[version]['total'] += 1
            if metric.migration_success:
                version_stats[version]['successful'] += 1
            version_stats[version]['accuracy_scores'].append(metric.accuracy_score)
            
        # Calculate version summaries
        summary_by_version = {}
        for version, stats in version_stats.items():
            summary_by_version[version] = {
                'success_rate': stats['successful'] / stats['total'] if stats['total'] > 0 else 0,
                'accuracy': statistics.mean(stats['accuracy_scores']) if stats['accuracy_scores'] else 0
            }
            
        # Find common issues
        common_issues = self._analyze_common_issues()
        
        # Calculate execution time only if we have any
        if execution_times:
            execution_time_str = f"{sum(execution_times)/60:.2f} minutes"
        else:
            execution_time_str = "N/A"
            
        return {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': failed_tests,
            'overall_accuracy': statistics.mean(accuracy_scores) if accuracy_scores else 0,
            'execution_time': execution_time_str,
            'summary_by_version': summary_by_version,
            'common_issues': common_issues,
            'statistics': {
                'package_accuracy': {
                    'mean': statistics.mean(package_accuracies) if package_accuracies else 0,
                    'median': statistics.median(package_accuracies) if package_accuracies else 0,
                    'min': min(package_accuracies) if package_accuracies else 0,
                    'max': max(package_accuracies) if package_accuracies else 0
                },
                'import_success_rate': {
                    'mean': statistics.mean(import_success_rates) if import_success_rates else 0,
                    'median': statistics.median(import_success_rates) if import_success_rates else 0,
                    'min': min(import_success_rates) if import_success_rates else 0,
                    'max': max(import_success_rates) if import_success_rates else 0
                },
                'execution_time': {
                    'mean': statistics.mean(execution_times) if execution_times else 0,
                    'median': statistics.median(execution_times) if execution_times else 0,
                    'min': min(execution_times) if execution_times else 0,
                    'max': max(execution_times) if execution_times else 0
                }
            }
        }
        
    def _analyze_common_issues(self) -> List[Dict[str, Any]]:
        """Analyze common issues across tests"""
        issue_counts = {}
        
        # Count package issues
        for metric in self.metrics_data:
            if metric.missing_packages > 0:
                issue = "missing_packages"
                if issue not in issue_counts:
                    issue_counts[issue] = 0
                issue_counts[issue] += 1
                
            if metric.failed_imports > 0:
                issue = "import_failures"
                if issue not in issue_counts:
                    issue_counts[issue] = 0
                issue_counts[issue] += 1
                
        # Count failure types
        for failure in self.failures:
            issue = failure['error_type']
            if issue not in issue_counts:
                issue_counts[issue] = 0
            issue_counts[issue] += 1
            
        # Sort by frequency
        common_issues = []
        for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
            common_issues.append({
                'issue': issue,
                'frequency': count,
                'percentage': count / len(self.metrics_data) * 100 if self.metrics_data else 0
            })
            
        return common_issues[:10]  # Top 10 issues
        
    def generate_report(self, output_dir: Path):
        """Generate comprehensive test report"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate summary report
        summary = self.generate_summary()
        summary_file = output_dir / 'summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
            
        # Generate CSV report
        self._generate_csv_report(output_dir / 'metrics.csv')
        
        # Generate detailed JSON report
        detailed_report = {
            'summary': summary,
            'metrics': self.get_all_metrics(),
            'failures': self.failures
        }
        detailed_file = output_dir / 'detailed_report.json'
        with open(detailed_file, 'w') as f:
            json.dump(detailed_report, f, indent=2)
            
        # Generate markdown report
        self._generate_markdown_report(output_dir / 'report.md', summary)
        
        self.logger.info(f"Reports generated in {output_dir}")
        
    def _generate_csv_report(self, csv_file: Path):
        """Generate CSV report of metrics"""
        if not self.metrics_data:
            return
            
        fieldnames = [
            'test_id', 'comfyui_version', 'scenario', 'timestamp',
            'total_packages', 'matched_packages', 'missing_packages', 'package_accuracy',
            'total_custom_nodes', 'successful_imports', 'failed_imports', 'import_success_rate',
            'migration_success', 'accuracy_score', 'execution_time', 'error_count'
        ]
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for metric in self.get_all_metrics():
                writer.writerow(metric)
                
    def _generate_markdown_report(self, md_file: Path, summary: Dict[str, Any]):
        """Generate markdown report"""
        with open(md_file, 'w') as f:
            f.write("# ComfyUI Migration Test Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Summary
            f.write("## Summary\n\n")
            f.write(f"- Total Tests: {summary['total_tests']}\n")
            f.write(f"- Successful: {summary['successful_tests']}\n")
            f.write(f"- Failed: {summary['failed_tests']}\n")
            f.write(f"- Overall Accuracy: {summary['overall_accuracy']:.1%}\n")
            if 'execution_time' in summary:
                f.write(f"- Total Execution Time: {summary['execution_time']}\n\n")
            else:
                f.write("- Total Execution Time: N/A (no completed tests)\n\n")
            
            # Results by version
            f.write("## Results by ComfyUI Version\n\n")
            f.write("| Version | Success Rate | Accuracy |\n")
            f.write("|---------|--------------|----------|\n")
            
            for version, stats in summary['summary_by_version'].items():
                f.write(f"| {version} | {stats['success_rate']:.1%} | {stats['accuracy']:.1%} |\n")
                
            # Common issues
            if summary['common_issues']:
                f.write("\n## Common Issues\n\n")
                f.write("| Issue | Frequency | Percentage |\n")
                f.write("|-------|-----------|------------|\n")
                
                for issue in summary['common_issues']:
                    f.write(f"| {issue['issue']} | {issue['frequency']} | {issue['percentage']:.1f}% |\n")
                    
            # Statistics
            f.write("\n## Detailed Statistics\n\n")
            f.write("### Package Accuracy\n")
            stats = summary['statistics']['package_accuracy']
            f.write(f"- Mean: {stats['mean']:.1%}\n")
            f.write(f"- Median: {stats['median']:.1%}\n")
            f.write(f"- Range: {stats['min']:.1%} - {stats['max']:.1%}\n\n")
            
            f.write("### Import Success Rate\n")
            stats = summary['statistics']['import_success_rate']
            f.write(f"- Mean: {stats['mean']:.1%}\n")
            f.write(f"- Median: {stats['median']:.1%}\n")
            f.write(f"- Range: {stats['min']:.1%} - {stats['max']:.1%}\n\n")
            
            f.write("### Execution Time (seconds)\n")
            stats = summary['statistics']['execution_time']
            f.write(f"- Mean: {stats['mean']:.1f}s\n")
            f.write(f"- Median: {stats['median']:.1f}s\n")
            f.write(f"- Range: {stats['min']:.1f}s - {stats['max']:.1f}s\n")