import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
import threading

from ..utils.network import get_network_manager


class ConnectionStatusWidget:
    """Widget to display and manage VPN/SMB connection status"""
    
    def __init__(self, parent, on_connection_change: Optional[Callable] = None):
        self.parent = parent
        self.network_manager = get_network_manager()
        self.on_connection_change = on_connection_change
        
        # Create main frame
        self.frame = ttk.LabelFrame(parent, text="Connection Status", padding="10")
        
        # Status variables
        self.vpn_status_var = tk.StringVar(value="Checking...")
        self.smb_status_var = tk.StringVar(value="Checking...")
        
        self._create_widgets()
        self._update_status()
        
        # Register for status updates
        self.network_manager.register_connection_callback(self._on_status_change)
        
        # Start periodic updates
        self._start_status_monitor()
    
    def _create_widgets(self):
        """Create status widgets"""
        # VPN Status
        vpn_frame = ttk.Frame(self.frame)
        vpn_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        vpn_frame.columnconfigure(1, weight=1)
        
        ttk.Label(vpn_frame, text="FHNW VPN:").grid(row=0, column=0, sticky=tk.W)
        self.vpn_status_label = ttk.Label(vpn_frame, textvariable=self.vpn_status_var)
        self.vpn_status_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        self.vpn_connect_btn = ttk.Button(vpn_frame, text="Connect", 
                                         command=self._connect_vpn, width=10)
        self.vpn_connect_btn.grid(row=0, column=2, padx=(10, 0))
        
        self.vpn_disconnect_btn = ttk.Button(vpn_frame, text="Disconnect", 
                                           command=self._disconnect_vpn, width=10)
        self.vpn_disconnect_btn.grid(row=0, column=3, padx=(5, 0))
        
        # SMB Status
        smb_frame = ttk.Frame(self.frame)
        smb_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        smb_frame.columnconfigure(1, weight=1)
        
        ttk.Label(smb_frame, text="Network Drive:").grid(row=0, column=0, sticky=tk.W)
        self.smb_status_label = ttk.Label(smb_frame, textvariable=self.smb_status_var)
        self.smb_status_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        self.smb_mount_btn = ttk.Button(smb_frame, text="Mount", 
                                       command=self._mount_smb, width=10)
        self.smb_mount_btn.grid(row=0, column=2, padx=(10, 0))
        
        self.smb_unmount_btn = ttk.Button(smb_frame, text="Unmount", 
                                         command=self._unmount_smb, width=10)
        self.smb_unmount_btn.grid(row=0, column=3, padx=(5, 0))
        
        # Auto-connect checkbox
        self.auto_connect_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.frame, text="Auto-connect when syncing", 
                       variable=self.auto_connect_var).grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
    
    def _update_status(self):
        """Update connection status display"""
        def check_status():
            vpn_connected = self.network_manager.check_vpn_connection()
            smb_mounted = self.network_manager.check_smb_mount()
            
            # Update UI in main thread
            self.parent.after(0, self._update_ui, vpn_connected, smb_mounted)
        
        thread = threading.Thread(target=check_status, daemon=True)
        thread.start()
    
    def _update_ui(self, vpn_connected: bool, smb_mounted: bool):
        """Update UI elements based on connection status"""
        # VPN Status
        if vpn_connected:
            self.vpn_status_var.set("✅ Connected")
            self.vpn_status_label.configure(foreground="green")
            self.vpn_connect_btn.configure(state='disabled')
            self.vpn_disconnect_btn.configure(state='normal')
        else:
            self.vpn_status_var.set("❌ Disconnected")
            self.vpn_status_label.configure(foreground="red")
            self.vpn_connect_btn.configure(state='normal')
            self.vpn_disconnect_btn.configure(state='disabled')
        
        # SMB Status
        if smb_mounted:
            self.smb_status_var.set("✅ Mounted")
            self.smb_status_label.configure(foreground="green")
            self.smb_mount_btn.configure(state='disabled')
            self.smb_unmount_btn.configure(state='normal')
        else:
            self.smb_status_var.set("❌ Not Mounted")
            self.smb_status_label.configure(foreground="red")
            self.smb_mount_btn.configure(state='normal' if vpn_connected else 'disabled')
            self.smb_unmount_btn.configure(state='disabled')
        
        # Notify callback of status change
        if self.on_connection_change:
            self.on_connection_change(vpn_connected, smb_mounted)
    
    def _on_status_change(self, vpn_connected: bool, smb_mounted: bool):
        """Callback for network status changes"""
        self.parent.after(0, self._update_ui, vpn_connected, smb_mounted)
    
    def _connect_vpn(self):
        """Connect to VPN"""
        def connect():
            try:
                self.parent.after(0, lambda: self.vpn_status_var.set("Connecting..."))
                success, message = self.network_manager.connect_vpn()
                
                if success:
                    self.parent.after(0, lambda: messagebox.showinfo("Success", message, parent=self.parent))
                else:
                    self.parent.after(0, lambda: messagebox.showerror("Error", message, parent=self.parent))
                
                self.parent.after(0, self._update_status)
            except Exception as e:
                self.parent.after(0, lambda: messagebox.showerror("Error", f"Connection failed: {str(e)}", parent=self.parent))
                self.parent.after(0, self._update_status)
        
        thread = threading.Thread(target=connect, daemon=True)
        thread.start()
    
    def _disconnect_vpn(self):
        """Disconnect from VPN"""
        def disconnect():
            try:
                self.parent.after(0, lambda: self.vpn_status_var.set("Disconnecting..."))
                success, message = self.network_manager.disconnect_vpn()
                
                if success:
                    self.parent.after(0, lambda: messagebox.showinfo("Success", message, parent=self.parent))
                else:
                    self.parent.after(0, lambda: messagebox.showerror("Error", message, parent=self.parent))
                
                self.parent.after(0, self._update_status)
            except Exception as e:
                self.parent.after(0, lambda: messagebox.showerror("Error", f"Disconnection failed: {str(e)}", parent=self.parent))
                self.parent.after(0, self._update_status)
        
        thread = threading.Thread(target=disconnect, daemon=True)
        thread.start()
    
    def _mount_smb(self):
        """Mount SMB share"""
        def mount():
            try:
                # Show initial status
                self.parent.after(0, lambda: self.smb_status_var.set("Mounting..."))
                
                # Progress callback for UI updates
                def progress_callback(message):
                    self.parent.after(0, lambda: self.smb_status_var.set(message))
                
                success, message = self.network_manager.mount_smb_share(progress_callback=progress_callback)
                
                if success:
                    self.parent.after(0, lambda: messagebox.showinfo("Success", message, parent=self.parent))
                else:
                    # Show informative error messages
                    if "Please check your credentials" in message:
                        self.parent.after(0, lambda: messagebox.showerror(
                            "Authentication Error", 
                            f"{message}\n\nGo to Tools → Network Settings to update your credentials.",
                            parent=self.parent))
                    elif "run the application with appropriate privileges" in message:
                        self.parent.after(0, lambda: messagebox.showerror(
                            "Permission Error", 
                            f"{message}\n\nThe application needs administrator privileges to mount network drives on macOS.",
                            parent=self.parent))
                    else:
                        self.parent.after(0, lambda: messagebox.showerror("Mount Error", message, parent=self.parent))
                
                self.parent.after(0, self._update_status)
            except Exception as e:
                self.parent.after(0, lambda: messagebox.showerror("Error", f"Mount failed: {str(e)}", parent=self.parent))
                self.parent.after(0, self._update_status)
        
        thread = threading.Thread(target=mount, daemon=True)
        thread.start()
    
    def _unmount_smb(self):
        """Unmount SMB share"""
        def unmount():
            try:
                self.parent.after(0, lambda: self.smb_status_var.set("Unmounting..."))
                success, message = self.network_manager.unmount_smb_share()
                
                if success:
                    self.parent.after(0, lambda: messagebox.showinfo("Success", message, parent=self.parent))
                else:
                    self.parent.after(0, lambda: messagebox.showerror("Error", message, parent=self.parent))
                
                self.parent.after(0, self._update_status)
            except Exception as e:
                self.parent.after(0, lambda: messagebox.showerror("Error", f"Unmount failed: {str(e)}", parent=self.parent))
                self.parent.after(0, self._update_status)
        
        thread = threading.Thread(target=unmount, daemon=True)
        thread.start()
    
    def _start_status_monitor(self):
        """Start periodic status monitoring"""
        def monitor():
            self._update_status()
            self.parent.after(30000, monitor)  # Check every 30 seconds
        
        self.parent.after(1000, monitor)  # Start after 1 second
    
    def get_auto_connect(self) -> bool:
        """Get auto-connect preference"""
        return self.auto_connect_var.get()
    
    def grid(self, **kwargs):
        """Grid the main frame"""
        self.frame.grid(**kwargs)
    
    def pack(self, **kwargs):
        """Pack the main frame"""
        self.frame.pack(**kwargs)
    
    def destroy(self):
        """Clean up the widget"""
        self.network_manager.unregister_connection_callback(self._on_status_change)
        self.frame.destroy()