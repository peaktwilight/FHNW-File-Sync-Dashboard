#!/usr/bin/env python3
"""
Test script for network functionality
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.network import get_network_manager
from src.models.sync_profile import SyncLocation

def test_network_functionality():
    """Test network connectivity features"""
    print("Testing FHNW Network Functionality")
    print("=" * 40)
    
    # Get network manager
    network_manager = get_network_manager()
    
    # Test VPN connection check
    print("1. Checking VPN connection...")
    vpn_connected = network_manager.check_vpn_connection()
    print(f"   VPN Status: {'✅ Connected' if vpn_connected else '❌ Not Connected'}")
    
    # Test SMB mount check
    print("\n2. Checking SMB mount...")
    smb_mounted = network_manager.check_smb_mount()
    print(f"   SMB Status: {'✅ Mounted' if smb_mounted else '❌ Not Mounted'}")
    
    # Test FHNW location creation
    print("\n3. Testing FHNW location creation...")
    fhnw_location = SyncLocation.create_fhnw_location()
    print(f"   FHNW Location: {fhnw_location.path}")
    print(f"   Requires VPN: {fhnw_location.requires_vpn}")
    print(f"   Requires SMB: {fhnw_location.requires_smb}")
    print(f"   SMB Share: {fhnw_location.smb_share}")
    
    # Test connection requirements
    print("\n4. Testing connection requirements...")
    print(f"   Connection needed: VPN={fhnw_location.requires_vpn}, SMB={fhnw_location.requires_smb}")
    
    if vpn_connected and smb_mounted:
        print("\n✅ All connections ready for FHNW sync!")
    elif vpn_connected and not smb_mounted:
        print("\n⚠️ VPN connected but SMB not mounted")
        print("   Try mounting with: Tools → Network Settings")
    elif not vpn_connected:
        print("\n❌ VPN not connected")
        print("   Connect to VPN first: Tools → Network Settings")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_network_functionality()