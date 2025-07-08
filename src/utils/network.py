import os
import platform
import subprocess
import socket
import time
from typing import Tuple, Optional, Callable
import threading
import keyring
from urllib.parse import quote

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
    
    def get_vpn_help_instructions(self) -> str:
        """Get platform-specific VPN connection instructions"""
        if self.platform == "Darwin":  # macOS
            return """To connect to FHNW VPN on macOS:

1. Download and install Cisco AnyConnect from:
   https://vpn.fhnw.ch

2. Open Cisco AnyConnect Secure Mobility Client

3. Enter server address: vpn.fhnw.ch

4. Click Connect

5. Enter your FHNW credentials when prompted

6. Your browser will open for authentication

7. Complete the login process

8. The VPN connection will be established automatically"""
        
        elif self.platform == "Windows":
            return """To connect to FHNW VPN on Windows:

1. Download and install Cisco AnyConnect from:
   https://vpn.fhnw.ch

2. Open Cisco AnyConnect Secure Mobility Client

3. Enter server address: vpn.fhnw.ch

4. Click Connect

5. Enter your FHNW credentials when prompted

6. Your browser will open for authentication

7. Complete the login process

8. The VPN connection will be established automatically"""
        
        else:  # Linux
            return """To connect to FHNW VPN on Linux:

1. Install openconnect:
   sudo apt install openconnect (Ubuntu/Debian)
   sudo dnf install openconnect (Fedora)

2. Connect using command line:
   sudo openconnect --protocol=anyconnect vpn.fhnw.ch

3. Enter your FHNW credentials when prompted

4. Complete browser authentication if required

Alternative: Install Cisco AnyConnect if available for your distribution"""
    
    def get_smb_help_instructions(self) -> str:
        """Get platform-specific SMB mounting instructions"""
        if self.platform == "Darwin":  # macOS
            return """To connect to FHNW network drive on macOS:

1. Make sure you're connected to FHNW VPN first

2. Open Finder

3. Press Cmd+K (or Go → Connect to Server...)

4. Enter server address:
   smb://fs.edu.ds.fhnw.ch/data

5. Click Connect

6. Choose "Registered User"

7. Enter your FHNW credentials:
   - Username: your.name@students.fhnw.ch
   - Password: your FHNW password

8. Check "Remember this password in my keychain"

9. Click Connect

10. The network drive will appear in Finder sidebar
    and be accessible at /Volumes/data"""
        
        elif self.platform == "Windows":
            return """To connect to FHNW network drive on Windows:

1. Make sure you're connected to FHNW VPN first

2. Open File Explorer

3. Right-click on "This PC" → "Map network drive..."

4. Choose an available drive letter (e.g., Z:)

5. Enter folder path:
   \\\\fs.edu.ds.fhnw.ch\\data

6. Check "Connect using different credentials"

7. Check "Reconnect at sign-in" (optional)

8. Click Finish

9. Enter your FHNW credentials:
   - Username: your.name@students.fhnw.ch
   - Password: your FHNW password

10. Check "Remember my credentials"

11. Click OK

12. The network drive will appear as a mapped drive"""
        
        else:  # Linux
            return """To connect to FHNW network drive on Linux:

1. Make sure you're connected to FHNW VPN first

2. Install cifs-utils:
   sudo apt install cifs-utils (Ubuntu/Debian)
   sudo dnf install cifs-utils (Fedora)

3. Create a mount point:
   sudo mkdir /mnt/fhnw

4. Mount the share:
   sudo mount -t cifs //fs.edu.ds.fhnw.ch/data /mnt/fhnw -o username=your.name@students.fhnw.ch

5. Enter your FHNW password when prompted

6. The network drive will be accessible at /mnt/fhnw

For GUI access, use your file manager's "Connect to Server" 
option with: smb://fs.edu.ds.fhnw.ch/data"""
    
    
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
    


# Singleton instance
_network_manager = None

def get_network_manager() -> NetworkManager:
    """Get the singleton NetworkManager instance"""
    global _network_manager
    if _network_manager is None:
        _network_manager = NetworkManager()
    return _network_manager