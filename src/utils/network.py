import os
import platform
import subprocess
import socket
import time
from typing import Tuple, Optional, Callable
import threading
import keyring

from .logger import get_logger


class NetworkManager:
    """Manages VPN connections and SMB mounts for FHNW network resources"""
    
    # FHNW specific constants
    VPN_HOST = "vpn.fhnw.ch"
    SMB_SHARE = "smb://fs.edu.ds.fhnw.ch/data"
    MOUNT_POINT = "/Volumes/data"  # macOS default
    VPN_CHECK_HOSTS = ["fs.edu.ds.fhnw.ch", "10.10.0.1"]  # Internal FHNW hosts
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.platform = platform.system()
        self._vpn_process = None
        self._connection_callbacks = []
        
    def register_connection_callback(self, callback: Callable[[bool, bool], None]):
        """Register a callback for connection status changes (vpn_connected, smb_mounted)"""
        self._connection_callbacks.append(callback)
        
    def unregister_connection_callback(self, callback: Callable[[bool, bool], None]):
        """Unregister a connection callback"""
        if callback in self._connection_callbacks:
            self._connection_callbacks.remove(callback)
    
    def _notify_callbacks(self, vpn_connected: bool, smb_mounted: bool):
        """Notify all registered callbacks of connection status"""
        for callback in self._connection_callbacks:
            try:
                callback(vpn_connected, smb_mounted)
            except Exception as e:
                self.logger.error(f"Error in connection callback: {e}")
    
    def check_vpn_connection(self) -> bool:
        """Check if connected to FHNW VPN"""
        # Try to resolve internal FHNW hostname
        for host in self.VPN_CHECK_HOSTS:
            try:
                # Try DNS resolution
                socket.gethostbyname(host)
                self.logger.debug(f"Successfully resolved {host} - VPN appears connected")
                return True
            except socket.gaierror:
                continue
        
        # Alternative: Check if we can ping the VPN gateway
        if self.platform != "Windows":
            try:
                result = subprocess.run(
                    ["ping", "-c", "1", "-t", "1", "fs.edu.ds.fhnw.ch"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return True
            except Exception as e:
                self.logger.debug(f"Ping check failed: {e}")
        
        return False
    
    def check_smb_mount(self) -> bool:
        """Check if FHNW SMB share is mounted"""
        if self.platform == "Darwin":  # macOS
            return os.path.ismount(self.MOUNT_POINT) and os.path.exists(self.MOUNT_POINT)
        elif self.platform == "Windows":
            # On Windows, check if network drive is mapped
            try:
                result = subprocess.run(
                    ["net", "use"],
                    capture_output=True,
                    text=True
                )
                return "fs.edu.ds.fhnw.ch" in result.stdout
            except:
                return False
        else:  # Linux
            # Check mount points
            try:
                with open('/proc/mounts', 'r') as f:
                    mounts = f.read()
                return "fs.edu.ds.fhnw.ch" in mounts
            except:
                return False
    
    def connect_vpn(self, username: Optional[str] = None, 
                    progress_callback: Optional[Callable[[str], None]] = None) -> Tuple[bool, str]:
        """Connect to FHNW VPN using openconnect"""
        if self.check_vpn_connection():
            return True, "Already connected to VPN"
        
        if self.platform != "Darwin":
            return False, "Automatic VPN connection only supported on macOS"
        
        try:
            if progress_callback:
                progress_callback("Connecting to FHNW VPN...")
            
            # Get stored credentials if not provided
            if not username:
                username = keyring.get_password("fhnw_sync", "vpn_username")
                if not username:
                    # Try to find system credentials
                    username = self._find_system_credentials()
                    if not username:
                        return False, "No VPN username found. Please configure in Tools → Network Settings."
            
            # Use openconnect with browser authentication
            cmd = [
                "sudo", "openconnect",
                "--protocol=anyconnect",
                "--server", self.VPN_HOST,
                "--user", username,
                "--authenticate"
            ]
            
            # Get auth cookie via browser
            if progress_callback:
                progress_callback("Opening browser for VPN authentication...")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return False, f"VPN authentication failed: {result.stderr}"
            
            # Parse the cookie and fingerprint from output
            cookie = None
            fingerprint = None
            for line in result.stdout.split('\n'):
                if line.startswith("COOKIE="):
                    cookie = line.split('=', 1)[1].strip("'")
                elif line.startswith("FINGERPRINT="):
                    fingerprint = line.split('=', 1)[1]
            
            if not cookie:
                return False, "Failed to obtain VPN authentication cookie"
            
            # Connect with the cookie
            connect_cmd = [
                "sudo", "openconnect",
                "--protocol=anyconnect",
                "--server", self.VPN_HOST,
                "--cookie", cookie,
                "--background"
            ]
            
            if fingerprint:
                connect_cmd.extend(["--servercert", fingerprint])
            
            if progress_callback:
                progress_callback("Establishing VPN connection...")
            
            self._vpn_process = subprocess.Popen(
                connect_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for connection to establish
            time.sleep(3)
            
            if self.check_vpn_connection():
                self._notify_callbacks(True, self.check_smb_mount())
                return True, "VPN connected successfully"
            else:
                return False, "VPN connection failed to establish"
                
        except Exception as e:
            self.logger.error(f"VPN connection error: {e}")
            return False, f"VPN connection error: {str(e)}"
    
    def disconnect_vpn(self) -> Tuple[bool, str]:
        """Disconnect from VPN"""
        if self.platform != "Darwin":
            return False, "Automatic VPN disconnection only supported on macOS"
        
        try:
            # Kill openconnect process
            subprocess.run(["sudo", "killall", "openconnect"], capture_output=True)
            
            if self._vpn_process:
                self._vpn_process.terminate()
                self._vpn_process = None
            
            time.sleep(2)
            
            if not self.check_vpn_connection():
                self._notify_callbacks(False, False)
                return True, "VPN disconnected"
            else:
                return False, "Failed to disconnect VPN"
                
        except Exception as e:
            self.logger.error(f"VPN disconnection error: {e}")
            return False, f"VPN disconnection error: {str(e)}"
    
    def mount_smb_share(self, username: Optional[str] = None,
                       progress_callback: Optional[Callable[[str], None]] = None) -> Tuple[bool, str]:
        """Mount FHNW SMB share"""
        if self.check_smb_mount():
            return True, "SMB share already mounted"
        
        if not self.check_vpn_connection():
            return False, "VPN connection required to mount SMB share"
        
        if self.platform == "Darwin":  # macOS
            try:
                if progress_callback:
                    progress_callback("Mounting FHNW network drive...")
                
                # Create mount point if it doesn't exist (requires sudo on macOS)
                if not os.path.exists(self.MOUNT_POINT):
                    try:
                        os.makedirs(self.MOUNT_POINT, exist_ok=True)
                    except PermissionError:
                        # Try with sudo
                        result = subprocess.run(
                            ["sudo", "mkdir", "-p", self.MOUNT_POINT],
                            capture_output=True,
                            text=True
                        )
                        if result.returncode != 0:
                            return False, f"Failed to create mount point: {result.stderr}"
                
                # Get credentials - check app-specific first, then system keychain
                if not username:
                    username = keyring.get_password("fhnw_sync", "smb_username")
                    if not username:
                        # Try to find existing system credentials for fs.edu.ds.fhnw.ch
                        username = self._find_system_credentials()
                        if not username:
                            return False, "No SMB username found. Please configure in Tools → Network Settings or connect to the network drive manually first."
                
                # Get password - try app-specific first, then system keychain
                password = keyring.get_password("fhnw_sync", f"smb_password_{username}")
                if not password:
                    password = self._get_system_password(username)
                
                # Build mount command with credentials
                if password:
                    mount_url = f"//{username}:{password}@fs.edu.ds.fhnw.ch/data"
                else:
                    mount_url = f"//{username}@fs.edu.ds.fhnw.ch/data"
                
                # Try mounting with sudo first (recommended for /Volumes on macOS)
                cmd = ["sudo", "mount_smbfs", mount_url, self.MOUNT_POINT]
                
                if progress_callback:
                    progress_callback("Authenticating and mounting drive...")
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self._notify_callbacks(True, True)
                    return True, "SMB share mounted successfully"
                else:
                    # If sudo failed, provide detailed error
                    error_msg = result.stderr.strip()
                    if "Authentication failed" in error_msg:
                        return False, "Authentication failed. Please check your credentials in Network Settings."
                    elif "mount_smbfs: server connection failed" in error_msg:
                        return False, "Connection to server failed. Please ensure VPN is connected."
                    elif "Operation not permitted" in error_msg:
                        return False, "Permission denied. Please run the application with appropriate privileges."
                    else:
                        return False, f"Failed to mount SMB share: {error_msg}"
                        
            except Exception as e:
                self.logger.error(f"SMB mount error: {e}")
                return False, f"SMB mount error: {str(e)}"
                
        elif self.platform == "Windows":
            # Windows net use command
            try:
                if not username:
                    username = keyring.get_password("fhnw_sync", "smb_username")
                    if not username:
                        return False, "No SMB username found"
                
                password = keyring.get_password("fhnw_sync", f"smb_password_{username}")
                
                # Find available drive letter
                import string
                for letter in string.ascii_uppercase[4:]:  # Start from E:
                    if not os.path.exists(f"{letter}:"):
                        drive_letter = f"{letter}:"
                        break
                else:
                    return False, "No available drive letters"
                
                cmd = ["net", "use", drive_letter, "\\\\fs.edu.ds.fhnw.ch\\data"]
                
                if password:
                    cmd.extend([f"/user:{username}", password])
                else:
                    cmd.append(f"/user:{username}")
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self._notify_callbacks(True, True)
                    return True, f"SMB share mounted to {drive_letter}"
                else:
                    return False, f"Failed to mount: {result.stderr}"
                    
            except Exception as e:
                return False, f"SMB mount error: {str(e)}"
                
        else:
            return False, "SMB mounting not implemented for Linux"
    
    def unmount_smb_share(self) -> Tuple[bool, str]:
        """Unmount SMB share"""
        if not self.check_smb_mount():
            return True, "SMB share not mounted"
        
        try:
            if self.platform == "Darwin":
                cmd = ["umount", self.MOUNT_POINT]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    # Try with sudo
                    cmd.insert(0, "sudo")
                    result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self._notify_callbacks(self.check_vpn_connection(), False)
                    return True, "SMB share unmounted"
                else:
                    return False, f"Failed to unmount: {result.stderr}"
                    
            elif self.platform == "Windows":
                # Find the mapped drive
                result = subprocess.run(["net", "use"], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if "fs.edu.ds.fhnw.ch" in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            drive = parts[1]
                            subprocess.run(["net", "use", drive, "/delete", "/y"])
                            self._notify_callbacks(self.check_vpn_connection(), False)
                            return True, "SMB share unmounted"
                
                return False, "Could not find mounted SMB share"
                
            else:
                return False, "SMB unmounting not implemented for Linux"
                
        except Exception as e:
            return False, f"Unmount error: {str(e)}"
    
    def ensure_connection(self, require_vpn: bool = True, require_smb: bool = True,
                         username: Optional[str] = None,
                         progress_callback: Optional[Callable[[str], None]] = None) -> Tuple[bool, str]:
        """Ensure VPN and SMB connections are established"""
        messages = []
        
        # Check/establish VPN connection
        if require_vpn and not self.check_vpn_connection():
            success, msg = self.connect_vpn(username, progress_callback)
            if not success:
                return False, f"VPN connection failed: {msg}"
            messages.append("VPN connected")
        
        # Check/establish SMB mount
        if require_smb and not self.check_smb_mount():
            if not self.check_vpn_connection():
                return False, "VPN connection required for SMB mount"
            
            success, msg = self.mount_smb_share(username, progress_callback)
            if not success:
                return False, f"SMB mount failed: {msg}"
            messages.append("SMB share mounted")
        
        if messages:
            return True, "; ".join(messages)
        else:
            return True, "All connections already established"
    
    def start_connection_monitor(self, interval: int = 30):
        """Start monitoring connection status in background"""
        def monitor():
            while True:
                vpn = self.check_vpn_connection()
                smb = self.check_smb_mount()
                self._notify_callbacks(vpn, smb)
                time.sleep(interval)
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
    def _find_system_credentials(self) -> Optional[str]:
        """Find existing system credentials for fs.edu.ds.fhnw.ch"""
        if self.platform != "Darwin":
            return None
        
        try:
            # Use security command to find existing keychain entries
            result = subprocess.run([
                "security", "find-internet-password",
                "-s", "fs.edu.ds.fhnw.ch",
                "-g"
            ], capture_output=True, text=True, stderr=subprocess.STDOUT)
            
            if result.returncode == 0:
                # Parse the output to find the account name
                for line in result.stdout.split('\n'):
                    if 'acct' in line and '"' in line:
                        # Extract account name from: "acct"<blob>="username"
                        start = line.find('"', line.find('acct')) + 1
                        end = line.find('"', start + 1)
                        if start > 0 and end > start:
                            username = line[start:end]
                            self.logger.info(f"Found system credentials for user: {username}")
                            return username
        except Exception as e:
            self.logger.debug(f"Could not find system credentials: {e}")
        
        return None
    
    def _get_system_password(self, username: str) -> Optional[str]:
        """Get password from system keychain for fs.edu.ds.fhnw.ch"""
        if self.platform != "Darwin":
            return None
        
        try:
            # Use security command to get password
            result = subprocess.run([
                "security", "find-internet-password",
                "-s", "fs.edu.ds.fhnw.ch",
                "-a", username,
                "-w"  # Print password only
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                password = result.stdout.strip()
                self.logger.info(f"Retrieved system password for user: {username}")
                return password
        except Exception as e:
            self.logger.debug(f"Could not get system password: {e}")
        
        return None


# Singleton instance
_network_manager = None

def get_network_manager() -> NetworkManager:
    """Get the singleton NetworkManager instance"""
    global _network_manager
    if _network_manager is None:
        _network_manager = NetworkManager()
    return _network_manager