#!/usr/bin/env python3
"""
Docker utilities for migration testing
"""

import subprocess
import json
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class DockerManager:
    """Manage Docker operations for testing"""
    
    def __init__(self):
        self.logger = logging.getLogger('migration_test.docker')
        # Container tracking
        self._current_container_name: Optional[str] = None
        self._current_container_id: Optional[str] = None
        self._current_container_venv: Optional[str] = None
        
    @property
    def container_name(self) -> Optional[str]:
        """Get current container name"""
        return self._current_container_name
        
    @property
    def container_id(self) -> Optional[str]:
        """Get current container ID"""
        return self._current_container_id
        
    @property
    def container_venv(self) -> Optional[str]:
        """Get current ComfyUI venv path in container"""
        return self._current_container_venv
        
    def set_current_container(self, container_name: str, container_id: str, 
                            container_venv: Optional[str] = None):
        """Set the current container context"""
        self._current_container_name = container_name
        self._current_container_id = container_id
        if container_venv:
            self._current_container_venv = container_venv
        else:
            # Default venv path in container
            self._current_container_venv = f"/env/{container_id}/.venv"
            
    def clear_current_container(self):
        """Clear current container context"""
        self._current_container_name = None
        self._current_container_id = None
        self._current_container_venv = None
        
    def container_exists(self, container_name: str) -> bool:
        """Check if container exists"""
        result = subprocess.run(
            ['docker', 'ps', '-a', '--format', '{{.Names}}'],
            capture_output=True,
            text=True
        )
        return container_name in result.stdout.split('\n')
        
    def get_container_status(self, container_name: str) -> Tuple[bool, str]:
        """Get container status and state"""
        # Check if container exists
        result = subprocess.run(
            ['docker', 'ps', '-a', '--filter', f'name={container_name}', '--format', '{{.Status}}'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return False, "not found"
            
        status = result.stdout.strip()
        if not status:
            return False, "not found"
            
        # Check if running
        result = subprocess.run(
            ['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Status}}'],
            capture_output=True,
            text=True
        )
        
        is_running = bool(result.stdout.strip())
        return is_running, status
        
    def get_container_exit_code(self, container_name: str) -> int:
        """Get container exit code"""
        result = subprocess.run(
            ['docker', 'inspect', container_name, '--format', '{{.State.ExitCode}}'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            try:
                return int(result.stdout.strip())
            except ValueError:
                return -1
        return -1
        
    def run_container(self, docker_cmd: List[str]) -> subprocess.CompletedProcess:
        """Run a new container with the given docker run command"""
        self.logger.debug(f"Running container: {' '.join(docker_cmd)}")
        return subprocess.run(docker_cmd, capture_output=True, text=True)
        
    def start_container(self, container_name: str) -> subprocess.CompletedProcess:
        """Start a stopped container"""
        return subprocess.run(
            ['docker', 'start', container_name],
            capture_output=True,
            text=True
        )
        
    def stop_container(self, container_name: str):
        """Stop a running container"""
        if self.container_exists(container_name):
            self.logger.debug(f"Stopping container {container_name}")
            subprocess.run(
                ['docker', 'stop', container_name],
                capture_output=True,
                check=False
            )
            
    def remove_container(self, container_name: str):
        """Remove a container"""
        if self.container_exists(container_name):
            self.logger.debug(f"Removing container {container_name}")
            subprocess.run(
                ['docker', 'rm', '-f', container_name],
                capture_output=True,
                check=False
            )
            
    def get_container_logs(self, container_name: str, tail: int = 100) -> str:
        """Get container logs"""
        result = subprocess.run(
            ['docker', 'logs', container_name, '--tail', str(tail)],
            capture_output=True,
            text=True
        )
        return result.stdout + result.stderr
        
    def exec_command(self, container_name: str, command: List[str],
                     env_vars: Optional[Dict[str, str]] = None,
                     capture_output: bool = True) -> subprocess.CompletedProcess:
        """Execute command in container with optional environment variables"""
        docker_cmd = ['docker', 'exec']
        
        # Add environment variables
        if env_vars:
            for key, value in env_vars.items():
                docker_cmd.extend(['-e', f'{key}={value}'])
        
        # Add container name and command
        docker_cmd.append(container_name)
        docker_cmd.extend(command)
        
        self.logger.debug(f"Executing in container: {' '.join(docker_cmd)}")
        
        return subprocess.run(
            docker_cmd,
            capture_output=capture_output,
            text=True
        )
        
    def get_container_info(self, container_name: str) -> Dict:
        """Get detailed container information"""
        result = subprocess.run(
            ['docker', 'inspect', container_name],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            info = json.loads(result.stdout)
            return info[0] if info else {}
        return {}
        
    def get_container_environment(self, container_name: str) -> Dict[str, str]:
        """Get all environment variables from a running container"""
        result = subprocess.run(
            ['docker', 'exec', container_name, 'env'],
            capture_output=True,
            text=True
        )
        
        env_vars = {}
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
                    
        return env_vars
        
    def copy_from_container(self, container_name: str, src_path: str, 
                           dest_path: Path):
        """Copy file from container"""
        subprocess.run(
            ['docker', 'cp', f'{container_name}:{src_path}', str(dest_path)],
            check=True
        )
        
    def copy_to_container(self, src_path: Path, container_name: str, 
                         dest_path: str):
        """Copy file to container"""
        subprocess.run(
            ['docker', 'cp', str(src_path), f'{container_name}:{dest_path}'],
            check=True
        )
        
    def wait_for_container(self, container_name: str, timeout: int = 300) -> int:
        """Wait for container to exit"""
        result = subprocess.run(
            ['docker', 'wait', container_name],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode == 0:
            return int(result.stdout.strip())
        return -1
        
    def list_containers_by_pattern(self, name_pattern: str) -> List[str]:
        """List containers matching a name pattern"""
        result = subprocess.run(
            ['docker', 'ps', '-a', '--filter', f'name={name_pattern}', '--format', '{{.Names}}'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return [name for name in result.stdout.strip().split('\n') if name]
        return []
        
    def cleanup_containers(self, containers: List[str]):
        """Clean up multiple containers"""
        for container in containers:
            if container:  # Skip empty lines
                self.logger.debug(f"Cleaning up container: {container}")
                self.stop_container(container)
                self.remove_container(container)
                
    def get_gpu_info(self) -> Dict:
        """Get GPU information from nvidia-smi"""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total,driver_version', 
                 '--format=csv,noheader'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                gpus = []
                for line in lines:
                    parts = line.split(', ')
                    if len(parts) >= 3:
                        gpus.append({
                            'name': parts[0],
                            'memory': parts[1],
                            'driver': parts[2]
                        })
                return {'available': True, 'gpus': gpus}
        except FileNotFoundError:
            pass
            
        return {'available': False, 'gpus': []}
    
