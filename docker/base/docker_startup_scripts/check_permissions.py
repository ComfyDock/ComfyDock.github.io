#!/usr/bin/env python3
"""
Python script to check permissions on bind-mounted volumes
"""

import os
from pathlib import Path
from typing import List, Set
from concurrent.futures import ProcessPoolExecutor, as_completed

from utils.base_utils import Logger, EnvironmentManager, CommandRunner
from utils.permission_utils import MountDetector, PermissionChecker


class ComfyUIPermissionChecker:
    """Main class for checking ComfyUI permissions"""
    
    def __init__(self):
        self.comfy_uid, self.comfy_gid = EnvironmentManager.get_comfy_user_info()
        self.container_id = EnvironmentManager.get_container_id()
        self.comfyui_directory = EnvironmentManager.get_comfyui_directory()
        self.permission_checker = PermissionChecker(self.comfy_uid, self.comfy_gid)
        
        # Configure parallel processing
        self.parallel_jobs = int(os.environ.get('PERMISSION_CHECK_PARALLEL_JOBS', '4'))
        self.files_per_batch = int(os.environ.get('PERMISSION_CHECK_FILES_PER_BATCH', '20'))
        self.dirs_per_batch = int(os.environ.get('PERMISSION_CHECK_DIRS_PER_BATCH', '10'))
    
    def get_comfyui_directories(self) -> List[str]:
        """Get all ComfyUI directories to check"""
        dirs_to_check = []
        
        # Check symlink location
        if os.path.exists('/app/ComfyUI'):
            base_dirs = [
                '/app/ComfyUI/custom_nodes',
                '/app/ComfyUI/web/extensions', 
                '/app/ComfyUI/models',
                '/app/ComfyUI/input',
                '/app/ComfyUI/output',
                '/app/ComfyUI/user'
            ]
            dirs_to_check.extend([d for d in base_dirs if os.path.exists(d)])
        
        # Check actual ComfyUI directory if different
        if os.path.exists(self.comfyui_directory) and self.comfyui_directory != '/app/ComfyUI':
            base_dirs = [
                f'{self.comfyui_directory}/custom_nodes',
                f'{self.comfyui_directory}/web/extensions',
                f'{self.comfyui_directory}/models', 
                f'{self.comfyui_directory}/input',
                f'{self.comfyui_directory}/output',
                f'{self.comfyui_directory}/user'
            ]
            dirs_to_check.extend([d for d in base_dirs if os.path.exists(d)])
        
        return list(set(dirs_to_check))
    
    def process_file_batch(self, args):
        """Process a batch of files for permission issues"""
        files, comfy_uid, comfy_gid = args
        problem_files = []
        
        checker = PermissionChecker(comfy_uid, comfy_gid)
        
        for file_path in files:
            if os.path.isfile(file_path):
                if checker.check_path_permissions(file_path):
                    problem_files.append(file_path)
        
        return problem_files
    
    def process_dir_batch(self, args):
        """Process a batch of directories for permission issues"""
        dirs, comfy_uid, comfy_gid = args
        problem_dirs = []
        
        checker = PermissionChecker(comfy_uid, comfy_gid)
        
        for dir_path in dirs:
            if os.path.isdir(dir_path):
                if checker.check_path_permissions(dir_path):
                    problem_dirs.append(dir_path)
        
        return problem_dirs
    
    def check_directory_parallel(self, directory):
        """Check directory permissions with parallel processing"""
        problem_files = []
        problem_dirs = []
        
        # Get all files and directories
        all_files = []
        all_dirs = []
        
        try:
            for root, dirs, files in os.walk(directory):
                # Add directories
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    if not os.path.islink(dir_path):
                        all_dirs.append(dir_path)
                
                # Add files
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    if not os.path.islink(file_path):
                        all_files.append(file_path)
                        
                        # Limit to prevent memory issues
                        if len(all_files) > 50000:
                            break
                
                # Limit directories too
                if len(all_dirs) > 25000:
                    break
        
        except (OSError, IOError):
            Logger.warning(f"Could not scan directory {directory}")
            return problem_files, problem_dirs
        
        # Process files in parallel
        if all_files:
            file_batches = [
                all_files[i:i + self.files_per_batch] 
                for i in range(0, len(all_files), self.files_per_batch)
            ]
            
            batch_args = [(batch, self.comfy_uid, self.comfy_gid) for batch in file_batches]
            
            with ProcessPoolExecutor(max_workers=self.parallel_jobs) as executor:
                futures = [executor.submit(self.process_file_batch, args) for args in batch_args]
                for future in as_completed(futures):
                    try:
                        batch_problems = future.result()
                        problem_files.extend(batch_problems)
                    except Exception as e:
                        Logger.warning(f"File batch processing failed: {e}")
        
        # Process directories in parallel
        if all_dirs:
            dir_batches = [
                all_dirs[i:i + self.dirs_per_batch] 
                for i in range(0, len(all_dirs), self.dirs_per_batch)
            ]
            
            batch_args = [(batch, self.comfy_uid, self.comfy_gid) for batch in dir_batches]
            
            with ProcessPoolExecutor(max_workers=self.parallel_jobs) as executor:
                futures = [executor.submit(self.process_dir_batch, args) for args in batch_args]
                for future in as_completed(futures):
                    try:
                        batch_problems = future.result()
                        problem_dirs.extend(batch_problems)
                    except Exception as e:
                        Logger.warning(f"Directory batch processing failed: {e}")
        
        return problem_files, problem_dirs
    
    def write_results(self, problem_files: List[str], problem_dirs: List[str]) -> None:
        """Write results to files and create summary"""
        # Write results
        if problem_files:
            with open('/tmp/problem-files.txt', 'w') as f:
                for file_path in problem_files:
                    f.write(f"{file_path}\n")
        
        if problem_dirs:
            with open('/tmp/problem-dirs.txt', 'w') as f:
                for dir_path in problem_dirs:
                    f.write(f"{dir_path}\n")
        
        # Report results
        Logger.log("")
        Logger.log("Permission check complete!")
        
        if problem_files:
            Logger.log(f"❌ Found {len(problem_files)} files with permission issues")
            Logger.log("   See: /tmp/problem-files.txt")
        else:
            Logger.log("✅ No file permission issues found")
            # Remove empty file
            try:
                os.remove('/tmp/problem-files.txt')
            except OSError:
                pass
        
        if problem_dirs:
            Logger.log(f"❌ Found {len(problem_dirs)} directories with permission issues")
            Logger.log("   See: /tmp/problem-dirs.txt")
        else:
            Logger.log("✅ No directory permission issues found")
            # Remove empty file
            try:
                os.remove('/tmp/problem-dirs.txt')
            except OSError:
                pass
        
        # Create summary if issues found
        if problem_files or problem_dirs:
            self._create_summary(problem_files, problem_dirs)
    
    def _create_summary(self, problem_files: List[str], problem_dirs: List[str]) -> None:
        """Create a summary file of permission issues"""
        with open('/tmp/permission-issues-summary.txt', 'w') as f:
            f.write("Permission Issues Summary\n")
            f.write("=========================\n")
            f.write(f"User: comfy (UID={self.comfy_uid}, GID={self.comfy_gid})\n")
            f.write(f"Timestamp: {CommandRunner.run(['date']).stdout.strip()}\n")
            f.write("\n")
            
            if problem_dirs:
                f.write("Problematic Directories:\n")
                for dir_path in problem_dirs:
                    f.write(f"  - {dir_path}\n")
                f.write("\n")
            
            if problem_files:
                f.write("Problematic Files:\n")
                for file_path in problem_files:
                    f.write(f"  - {file_path}\n")
        
        Logger.log("")
        Logger.log("📄 Full summary available at: /tmp/permission-issues-summary.txt")
    
    def run(self) -> None:
        """Main execution method"""
        Logger.log(f"Checking permissions for user comfy (UID={self.comfy_uid}, GID={self.comfy_gid})")
        Logger.log(f"Using {self.parallel_jobs} parallel processes")
        
        # Clear previous problem files
        Path('/tmp/problem-files.txt').write_text('')
        Path('/tmp/problem-dirs.txt').write_text('')
        
        all_problem_files = []
        all_problem_dirs = []
        checked_dirs = set()
        
        # Detect and check bind mounts
        Logger.log("Detecting bind-mounted volumes...")
        bind_mounts = MountDetector.detect_bind_mounts()
        
        if not bind_mounts:
            Logger.log("No bind mounts detected in /app, /home, or /env directories")
        else:
            Logger.log("Found bind mounts:")
            for mount in bind_mounts:
                Logger.log(mount)
            
            Logger.log("")
            Logger.log("Checking permissions on bind-mounted volumes...")
            
            for mount in bind_mounts:
                if os.path.isdir(mount):
                    Logger.log(f"Checking: {mount}")
                    problem_files, problem_dirs = self.check_directory_parallel(mount)
                    all_problem_files.extend(problem_files)
                    all_problem_dirs.extend(problem_dirs)
                    checked_dirs.add(mount)
        
        # Check ComfyUI directories not already checked
        Logger.log("")
        Logger.log("Checking ComfyUI directories...")
        comfyui_dirs = self.get_comfyui_directories()
        
        for directory in comfyui_dirs:
            # Check if already processed as bind mount
            already_checked = False
            
            if directory in checked_dirs:
                already_checked = True
            else:
                # Check if subdirectory of checked bind mount
                for checked_dir in checked_dirs:
                    if directory.startswith(checked_dir + '/'):
                        already_checked = True
                        break
            
            if not already_checked:
                Logger.log(f"Checking: {directory}")
                problem_files, problem_dirs = self.check_directory_parallel(directory)
                all_problem_files.extend(problem_files)
                all_problem_dirs.extend(problem_dirs)
            else:
                Logger.log(f"Skipping {directory} (already checked as bind mount)")
        
        # Write results
        self.write_results(all_problem_files, all_problem_dirs)


def main():
    """Main function"""
    checker = ComfyUIPermissionChecker()
    checker.run()


if __name__ == '__main__':
    main()