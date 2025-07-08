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
        
        self.vpn_help_btn = ttk.Button(vpn_frame, text="Help", 
                                      command=self._show_vpn_help, width=10)
        self.vpn_help_btn.grid(row=0, column=2, padx=(10, 0))
        
        # SMB Status
        smb_frame = ttk.Frame(self.frame)
        smb_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        smb_frame.columnconfigure(1, weight=1)
        
        ttk.Label(smb_frame, text="Network Drive:").grid(row=0, column=0, sticky=tk.W)
        self.smb_status_label = ttk.Label(smb_frame, textvariable=self.smb_status_var)
        self.smb_status_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        self.smb_help_btn = ttk.Button(smb_frame, text="Help", 
                                      command=self._show_smb_help, width=10)
        self.smb_help_btn.grid(row=0, column=2, padx=(10, 0))
        
        # Info text
        info_text = "Use the Help buttons above for connection instructions"
        ttk.Label(self.frame, text=info_text, font=('', 9), foreground="gray").grid(
            row=2, column=0, sticky=tk.W, pady=(10, 0))
    
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
        else:
            self.vpn_status_var.set("❌ Disconnected")
            self.vpn_status_label.configure(foreground="red")
        
        # SMB Status
        if smb_mounted:
            self.smb_status_var.set("✅ Mounted")
            self.smb_status_label.configure(foreground="green")
        else:
            self.smb_status_var.set("❌ Not Mounted")
            self.smb_status_label.configure(foreground="red")
        
        # Notify callback of status change
        if self.on_connection_change:
            self.on_connection_change(vpn_connected, smb_mounted)
    
    def _on_status_change(self, vpn_connected: bool, smb_mounted: bool):
        """Callback for network status changes"""
        self.parent.after(0, self._update_ui, vpn_connected, smb_mounted)
    
    def _show_vpn_help(self):
        """Show VPN connection help"""
        help_text = self.network_manager.get_vpn_help_instructions()
        
        # Create help dialog
        help_dialog = tk.Toplevel(self.parent)
        help_dialog.title("VPN Connection Help")
        help_dialog.geometry("600x500")
        help_dialog.resizable(True, True)
        help_dialog.transient(self.parent)
        
        # Main frame with padding
        main_frame = ttk.Frame(help_dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="How to Connect to FHNW VPN", 
                 font=('', 14, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        # Help text in scrollable text widget
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=('', 11))
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.insert(1.0, help_text)
        text_widget.configure(state='disabled')
        
        # Close button
        ttk.Button(main_frame, text="Close", command=help_dialog.destroy).pack(pady=(10, 0))
        
        # Center dialog
        help_dialog.update_idletasks()
        x = (help_dialog.winfo_screenwidth() // 2) - (help_dialog.winfo_width() // 2)
        y = (help_dialog.winfo_screenheight() // 2) - (help_dialog.winfo_height() // 2)
        help_dialog.geometry(f"+{x}+{y}")
    
    def _show_smb_help(self):
        """Show SMB connection help"""
        help_text = self.network_manager.get_smb_help_instructions()
        
        # Create help dialog
        help_dialog = tk.Toplevel(self.parent)
        help_dialog.title("Network Drive Connection Help")
        help_dialog.geometry("600x500")
        help_dialog.resizable(True, True)
        help_dialog.transient(self.parent)
        
        # Main frame with padding
        main_frame = ttk.Frame(help_dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="How to Connect to FHNW Network Drive", 
                 font=('', 14, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        # Help text in scrollable text widget
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=('', 11))
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.insert(1.0, help_text)
        text_widget.configure(state='disabled')
        
        # Close button
        ttk.Button(main_frame, text="Close", command=help_dialog.destroy).pack(pady=(10, 0))
        
        # Center dialog
        help_dialog.update_idletasks()
        x = (help_dialog.winfo_screenwidth() // 2) - (help_dialog.winfo_width() // 2)
        y = (help_dialog.winfo_screenheight() // 2) - (help_dialog.winfo_height() // 2)
        help_dialog.geometry(f"+{x}+{y}")
    
    def _start_status_monitor(self):
        """Start periodic status monitoring"""
        def monitor():
            self._update_status()
            self.parent.after(30000, monitor)  # Check every 30 seconds
        
        self.parent.after(1000, monitor)  # Start after 1 second
    
    
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