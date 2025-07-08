import os
import platform
import subprocess
import shutil
from typing import Callable, Optional, List, Tuple
from datetime import datetime
import threading
import time

from ..models.sync_profile import SyncProfile, SyncMode, SyncDirection
from ..utils.logger import get_logger


class SyncEngine:
    """Core synchronization engine that handles the actual file sync operations"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.platform = platform.system()
        self._cancel_flag = threading.Event()
        self._current_process = None
    
    def sync(self, profile: SyncProfile, progress_callback: Optional[Callable] = None, 
             dry_run: bool = False) -> Tuple[bool, str]:
        """
        Execute a sync operation based on the given profile
        
        Args:
            profile: The sync profile to execute
            progress_callback: Optional callback for progress updates
            dry_run: If True, only simulate the sync without making changes
            
        Returns:
            Tuple of (success, message)
        """
        # Reset cancel flag
        self._cancel_flag.clear()
        
        # Validate profile
        errors = profile.validate()
        if errors:
            return False, f"Profile validation failed: {'; '.join(errors)}"
        
        # Check if source exists
        if not self._check_path_exists(profile.source.path, profile.source.is_remote):
            return False, f"Source path does not exist: {profile.source.path}"
        
        # Ensure destination directory exists
        if not profile.destination.is_remote and not dry_run:
            os.makedirs(profile.destination.path, exist_ok=True)
        
        # Perform sync based on platform
        if self.platform == "Windows":
            return self._sync_windows(profile, progress_callback, dry_run)
        else:
            return self._sync_unix(profile, progress_callback, dry_run)
    
    def cancel(self):
        """Cancel the current sync operation"""
        self._cancel_flag.set()
        if self._current_process:
            try:
                self._current_process.terminate()
            except:
                pass
    
    def _check_path_exists(self, path: str, is_remote: bool) -> bool:
        """Check if a path exists"""
        if is_remote:
            # For remote paths, we'll assume they exist if they look valid
            # In a real implementation, you'd check mount status
            return True
        return os.path.exists(path)
    
    def _build_rsync_command(self, profile: SyncProfile, dry_run: bool) -> List[str]:
        """Build rsync command based on profile settings"""
        cmd = ["rsync"]
        
        # Basic options
        cmd.extend(["-av", "--progress"])
        
        if dry_run:
            cmd.append("--dry-run")
        
        # Sync mode options
        if profile.sync_mode == SyncMode.MIRROR:
            cmd.append("--delete")
        elif profile.sync_mode == SyncMode.UPDATE:
            cmd.append("--update")
        
        # Preservation options
        if profile.preserve_permissions:
            cmd.append("-p")
        if profile.preserve_timestamps:
            cmd.append("-t")
        
        # Symlink handling
        if profile.follow_symlinks:
            cmd.append("-L")
        else:
            cmd.append("-l")
        
        # Bandwidth limit
        if profile.bandwidth_limit:
            cmd.extend(["--bwlimit", str(profile.bandwidth_limit)])
        
        # Exclude patterns
        for pattern in profile.rules.exclude_patterns:
            cmd.extend(["--exclude", pattern])
        
        # Include patterns
        for pattern in profile.rules.include_patterns:
            cmd.extend(["--include", pattern])
        
        # Hidden files
        if profile.rules.exclude_hidden:
            cmd.extend(["--exclude", ".*"])
        
        # File size limits
        if profile.rules.min_file_size:
            cmd.extend(["--min-size", str(profile.rules.min_file_size)])
        if profile.rules.max_file_size:
            cmd.extend(["--max-size", str(profile.rules.max_file_size)])
        
        # Source and destination
        src = profile.source.path
        dst = profile.destination.path
        
        # Ensure trailing slash for directory sync
        if not src.endswith('/'):
            src += '/'
        
        cmd.extend([src, dst])
        
        return cmd
    
    def _build_robocopy_command(self, profile: SyncProfile, dry_run: bool) -> List[str]:
        """Build robocopy command for Windows"""
        cmd = ["robocopy"]
        
        # Source and destination
        cmd.extend([profile.source.path, profile.destination.path])
        
        # File selection
        if profile.rules.file_extensions:
            patterns = [f"*{ext}" for ext in profile.rules.file_extensions]
            cmd.extend(patterns)
        else:
            cmd.append("*.*")
        
        # Options
        cmd.extend(["/E"])  # Copy subdirectories
        
        if profile.sync_mode == SyncMode.MIRROR:
            cmd.append("/MIR")  # Mirror mode
        
        if dry_run:
            cmd.append("/L")  # List only
        
        # Exclude patterns
        if profile.rules.exclude_patterns:
            cmd.extend(["/XF"] + profile.rules.exclude_patterns)
        
        # Exclude hidden
        if profile.rules.exclude_hidden:
            cmd.extend(["/XA:H"])
        
        # Retry settings
        cmd.extend(["/R:" + str(profile.retry_count), "/W:5"])
        
        return cmd
    
    def _sync_unix(self, profile: SyncProfile, progress_callback: Optional[Callable], 
                   dry_run: bool) -> Tuple[bool, str]:
        """Perform sync on Unix-like systems using rsync"""
        cmd = self._build_rsync_command(profile, dry_run)
        
        self.logger.info(f"Executing rsync command: {' '.join(cmd)}")
        
        try:
            self._current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            # Process output
            total_files = 0
            processed_files = 0
            
            for line in iter(self._current_process.stdout.readline, ''):
                if self._cancel_flag.is_set():
                    self._current_process.terminate()
                    return False, "Sync cancelled by user"
                
                line = line.strip()
                if line:
                    # Parse rsync progress
                    if line.startswith("sending incremental file list"):
                        if progress_callback:
                            progress_callback("Analyzing files...", 0)
                    elif "/" in line and not line.startswith("sent"):
                        processed_files += 1
                        if progress_callback:
                            progress_callback(f"Syncing: {line}", 
                                            (processed_files / max(total_files, 1)) * 100)
            
            self._current_process.wait()
            
            if self._current_process.returncode == 0:
                return True, "Sync completed successfully"
            else:
                stderr = self._current_process.stderr.read()
                return False, f"Sync failed: {stderr}"
                
        except Exception as e:
            self.logger.error(f"Sync error: {str(e)}")
            return False, f"Sync error: {str(e)}"
        finally:
            self._current_process = None
    
    def _sync_windows(self, profile: SyncProfile, progress_callback: Optional[Callable], 
                      dry_run: bool) -> Tuple[bool, str]:
        """Perform sync on Windows using robocopy"""
        cmd = self._build_robocopy_command(profile, dry_run)
        
        self.logger.info(f"Executing robocopy command: {' '.join(cmd)}")
        
        try:
            self._current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            for line in iter(self._current_process.stdout.readline, ''):
                if self._cancel_flag.is_set():
                    self._current_process.terminate()
                    return False, "Sync cancelled by user"
                
                line = line.strip()
                if line and progress_callback:
                    # Parse robocopy output
                    if "%" in line:
                        try:
                            percent = float(line.split("%")[0].split()[-1])
                            progress_callback(f"Progress: {line}", percent)
                        except:
                            progress_callback(line, -1)
                    else:
                        progress_callback(line, -1)
            
            self._current_process.wait()
            
            # Robocopy returns different codes
            if self._current_process.returncode < 8:
                return True, "Sync completed successfully"
            else:
                stderr = self._current_process.stderr.read()
                return False, f"Sync failed: {stderr}"
                
        except Exception as e:
            self.logger.error(f"Sync error: {str(e)}")
            return False, f"Sync error: {str(e)}"
        finally:
            self._current_process = None
    
    def estimate_sync_size(self, profile: SyncProfile) -> Tuple[int, int]:
        """
        Estimate the number of files and total size to sync
        
        Returns:
            Tuple of (file_count, total_size_bytes)
        """
        # This is a simplified estimation
        # In a real implementation, you'd run rsync with --dry-run and parse output
        try:
            total_size = 0
            file_count = 0
            
            if not profile.source.is_remote and os.path.exists(profile.source.path):
                for root, dirs, files in os.walk(profile.source.path):
                    # Apply exclude rules
                    if profile.rules.exclude_hidden:
                        dirs[:] = [d for d in dirs if not d.startswith('.')]
                        files = [f for f in files if not f.startswith('.')]
                    
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            size = os.path.getsize(file_path)
                            
                            # Apply size filters
                            if profile.rules.min_file_size and size < profile.rules.min_file_size:
                                continue
                            if profile.rules.max_file_size and size > profile.rules.max_file_size:
                                continue
                            
                            # Apply extension filters
                            if profile.rules.file_extensions:
                                ext = os.path.splitext(file)[1]
                                if ext not in profile.rules.file_extensions:
                                    continue
                            
                            total_size += size
                            file_count += 1
                        except:
                            pass
            
            return file_count, total_size
        except Exception as e:
            self.logger.error(f"Error estimating sync size: {e}")
            return 0, 0