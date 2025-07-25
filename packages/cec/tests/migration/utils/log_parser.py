#!/usr/bin/env python3
"""
Log parsing utilities for migration testing
"""

import re
import logging
from typing import Dict, List, Optional


class LogParser:
    """Parse ComfyUI and container logs for errors and information"""
    
    def __init__(self):
        self.logger = logging.getLogger('migration_test.logparser')
        
        # Common error patterns
        self.error_patterns = {
            'import_error': re.compile(r'ImportError: (.+)'),
            'module_not_found': re.compile(r'ModuleNotFoundError: (.+)'),
            'attribute_error': re.compile(r'AttributeError: (.+)'),
            'file_not_found': re.compile(r'FileNotFoundError: (.+)'),
            'permission_error': re.compile(r'PermissionError: (.+)'),
            'cuda_error': re.compile(r'CUDA error: (.+)'),
            'out_of_memory': re.compile(r'(CUDA out of memory|OutOfMemoryError)'),
            'package_conflict': re.compile(r'ERROR: pip\'s dependency resolver(.+)'),
            'git_error': re.compile(r'fatal: (.+)'),
            'connection_error': re.compile(r'(ConnectionError|URLError|HTTPError): (.+)'),
        }
        
        # Info patterns
        self.info_patterns = {
            'package_installed': re.compile(r'Successfully installed (.+)'),
            'requirement_satisfied': re.compile(r'Requirement already satisfied: (.+)'),
            'comfyui_version': re.compile(r'ComfyUI (v[\d.]+|[a-f0-9]+)'),
            'python_version': re.compile(r'Python ([\d.]+)'),
            'cuda_version': re.compile(r'CUDA Version: ([\d.]+)'),
            'torch_version': re.compile(r'torch==([\d.]+)'),
            'custom_node_loaded': re.compile(r'Loaded custom node from: (.+)'),
            'server_started': re.compile(r'Starting server on (.+)'),
        }
        
        # Progress patterns
        self.progress_patterns = {
            'downloading': re.compile(r'Downloading (.+) \((\d+\.?\d*[KMG]?B)\)'),
            'installing': re.compile(r'Installing (.+)'),
            'cloning': re.compile(r'Cloning into \'(.+)\''),
            'building': re.compile(r'Building wheel for (.+)'),
        }
        
    def parse_logs(self, log_content: str) -> Dict:
        """Parse log content and extract relevant information"""
        lines = log_content.split('\n')
        
        result = {
            'errors': [],
            'warnings': [],
            'info': {},
            'packages_installed': [],
            'custom_nodes_loaded': [],
            'progress': [],
            'summary': {}
        }
        
        for line in lines:
            # Check for errors
            error_info = self._parse_error_line(line)
            if error_info:
                result['errors'].append(error_info)
                
            # Check for warnings
            if 'WARNING' in line or 'WARN' in line:
                result['warnings'].append(line.strip())
                
            # Extract info
            info = self._parse_info_line(line)
            if info:
                for key, value in info.items():
                    if key == 'package_installed':
                        result['packages_installed'].extend(value)
                    elif key == 'custom_node_loaded':
                        result['custom_nodes_loaded'].append(value)
                    else:
                        result['info'][key] = value
                        
            # Track progress
            progress = self._parse_progress_line(line)
            if progress:
                result['progress'].append(progress)
                
        # Generate summary
        result['summary'] = self._generate_summary(result)
        
        return result
        
    def _parse_error_line(self, line: str) -> Optional[Dict]:
        """Parse error from log line"""
        for error_type, pattern in self.error_patterns.items():
            match = pattern.search(line)
            if match:
                return {
                    'type': error_type,
                    'message': match.group(1) if match.groups() else match.group(0),
                    'line': line.strip(),
                    'timestamp': self._extract_timestamp(line)
                }
        return None
        
    def _parse_info_line(self, line: str) -> Optional[Dict]:
        """Parse info from log line"""
        info = {}
        
        for info_type, pattern in self.info_patterns.items():
            match = pattern.search(line)
            if match:
                if info_type == 'package_installed':
                    # Parse package list
                    packages = match.group(1).split()
                    info[info_type] = [p.strip() for p in packages]
                else:
                    info[info_type] = match.group(1)
                    
        return info if info else None
        
    def _parse_progress_line(self, line: str) -> Optional[Dict]:
        """Parse progress information from log line"""
        for progress_type, pattern in self.progress_patterns.items():
            match = pattern.search(line)
            if match:
                return {
                    'type': progress_type,
                    'item': match.group(1),
                    'details': match.group(2) if len(match.groups()) > 1 else None,
                    'timestamp': self._extract_timestamp(line)
                }
        return None
        
    def _extract_timestamp(self, line: str) -> Optional[str]:
        """Extract timestamp from log line"""
        # Common timestamp patterns
        patterns = [
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',  # ISO format
            r'(\d{2}:\d{2}:\d{2})',  # Time only
            r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]',  # Bracketed
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(1)
        return None
        
    def _generate_summary(self, parsed_data: Dict) -> Dict:
        """Generate summary from parsed data"""
        return {
            'total_errors': len(parsed_data['errors']),
            'total_warnings': len(parsed_data['warnings']),
            'packages_installed': len(parsed_data['packages_installed']),
            'custom_nodes_loaded': len(parsed_data['custom_nodes_loaded']),
            'has_cuda_errors': any(e['type'] == 'cuda_error' for e in parsed_data['errors']),
            'has_import_errors': any(e['type'] in ['import_error', 'module_not_found'] 
                                   for e in parsed_data['errors']),
            'server_started': 'server_started' in parsed_data['info']
        }
        
    def find_critical_errors(self, log_content: str) -> List[Dict]:
        """Find critical errors that would prevent ComfyUI from running"""
        parsed = self.parse_logs(log_content)
        
        critical_errors = []
        critical_types = ['import_error', 'module_not_found', 'cuda_error', 
                         'out_of_memory', 'permission_error']
        
        for error in parsed['errors']:
            if error['type'] in critical_types:
                critical_errors.append(error)
                
        return critical_errors
        
    def extract_package_operations(self, log_content: str) -> Dict[str, List[str]]:
        """Extract package installation operations from logs"""
        operations = {
            'installed': [],
            'upgraded': [],
            'uninstalled': [],
            'failed': []
        }
        
        patterns = {
            'installed': re.compile(r'Successfully installed (.+)'),
            'upgraded': re.compile(r'Successfully upgraded (.+)'),
            'uninstalled': re.compile(r'Successfully uninstalled (.+)'),
            'failed': re.compile(r'ERROR: Failed (building wheel|to install) (.+)'),
        }
        
        for line in log_content.split('\n'):
            for op_type, pattern in patterns.items():
                match = pattern.search(line)
                if match:
                    if op_type == 'failed':
                        operations[op_type].append(match.group(2))
                    else:
                        packages = match.group(1).split()
                        operations[op_type].extend(packages)
                        
        return operations