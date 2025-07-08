import tkinter as tk
from tkinter import ttk, messagebox
import keyring
from typing import Optional


class NetworkSettingsDialog:
    """Dialog for configuring VPN and SMB credentials"""
    
    def __init__(self, parent):
        self.parent = parent
        self.result = False
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Network Settings")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        
        # Make modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Variables
        self.vpn_username_var = tk.StringVar()
        self.smb_username_var = tk.StringVar()
        self.vpn_password_var = tk.StringVar()
        self.smb_password_var = tk.StringVar()
        self.save_credentials_var = tk.BooleanVar(value=True)
        
        self._create_widgets()
        self._load_existing_credentials()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """Create dialog widgets"""
        # Main container
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # Header
        ttk.Label(main_frame, text="FHNW Network Credentials", 
                 font=('', 14, 'bold')).grid(row=row, column=0, columnspan=2, pady=(0, 20))
        row += 1
        
        # Info text
        info_text = """Configure your FHNW credentials for automatic VPN connection and network drive mounting.
        
Your credentials will be stored securely in the system keychain."""
        
        info_label = ttk.Label(main_frame, text=info_text, wraplength=450, justify=tk.LEFT)
        info_label.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        row += 1
        
        # VPN Section
        ttk.Label(main_frame, text="VPN Settings", font=('', 12, 'bold')).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        row += 1
        
        ttk.Label(main_frame, text="Username:").grid(row=row, column=0, sticky=tk.W, padx=(20, 0))
        ttk.Entry(main_frame, textvariable=self.vpn_username_var, width=30).grid(
            row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        row += 1
        
        ttk.Label(main_frame, text="Password:").grid(row=row, column=0, sticky=tk.W, padx=(20, 0))
        ttk.Entry(main_frame, textvariable=self.vpn_password_var, show="*", width=30).grid(
            row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        row += 1
        
        # Note about VPN authentication
        note_text = "Note: FHNW VPN uses browser-based authentication. Password is optional."
        ttk.Label(main_frame, text=note_text, font=('', 9), foreground="gray").grid(
            row=row, column=0, columnspan=2, sticky=tk.W, padx=(20, 0), pady=(2, 10))
        row += 1
        
        # SMB Section
        ttk.Label(main_frame, text="Network Drive Settings", font=('', 12, 'bold')).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=(10, 10))
        row += 1
        
        ttk.Label(main_frame, text="Username:").grid(row=row, column=0, sticky=tk.W, padx=(20, 0))
        ttk.Entry(main_frame, textvariable=self.smb_username_var, width=30).grid(
            row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        row += 1
        
        ttk.Label(main_frame, text="Password:").grid(row=row, column=0, sticky=tk.W, padx=(20, 0))
        ttk.Entry(main_frame, textvariable=self.smb_password_var, show="*", width=30).grid(
            row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        row += 1
        
        # Save credentials option
        ttk.Checkbutton(main_frame, text="Save credentials securely in system keychain", 
                       variable=self.save_credentials_var).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=(20, 0))
        row += 1
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(20, 20))
        row += 1
        
        # Test connections section
        ttk.Label(main_frame, text="Test Connections", font=('', 12, 'bold')).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        row += 1
        
        test_frame = ttk.Frame(main_frame)
        test_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        ttk.Button(test_frame, text="Test VPN Connection", 
                  command=self._test_vpn).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(test_frame, text="Test SMB Mount", 
                  command=self._test_smb).pack(side=tk.LEFT)
        row += 1
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Save", command=self._save, 
                  style="Accent.TButton").pack(side=tk.RIGHT)
    
    def _load_existing_credentials(self):
        """Load existing credentials from keychain"""
        try:
            vpn_username = keyring.get_password("fhnw_sync", "vpn_username")
            if vpn_username:
                self.vpn_username_var.set(vpn_username)
            
            smb_username = keyring.get_password("fhnw_sync", "smb_username")
            if smb_username:
                self.smb_username_var.set(smb_username)
        except Exception as e:
            print(f"Error loading credentials: {e}")
    
    def _save(self):
        """Save credentials to keychain"""
        try:
            if self.save_credentials_var.get():
                # Save VPN credentials
                if self.vpn_username_var.get():
                    keyring.set_password("fhnw_sync", "vpn_username", self.vpn_username_var.get())
                    if self.vpn_password_var.get():
                        keyring.set_password("fhnw_sync", f"vpn_password_{self.vpn_username_var.get()}", 
                                           self.vpn_password_var.get())
                
                # Save SMB credentials
                if self.smb_username_var.get():
                    keyring.set_password("fhnw_sync", "smb_username", self.smb_username_var.get())
                    if self.smb_password_var.get():
                        keyring.set_password("fhnw_sync", f"smb_password_{self.smb_username_var.get()}", 
                                           self.smb_password_var.get())
                
                messagebox.showinfo("Success", "Credentials saved successfully", parent=self.dialog)
            else:
                # Clear saved credentials
                try:
                    keyring.delete_password("fhnw_sync", "vpn_username")
                    keyring.delete_password("fhnw_sync", "smb_username")
                except:
                    pass
                
                messagebox.showinfo("Success", "Credentials cleared", parent=self.dialog)
            
            self.result = True
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save credentials: {str(e)}", parent=self.dialog)
    
    def _cancel(self):
        """Cancel the dialog"""
        self.dialog.destroy()
    
    def _test_vpn(self):
        """Test VPN connection"""
        from ..utils.network import get_network_manager
        
        network_manager = get_network_manager()
        
        def test():
            try:
                if network_manager.check_vpn_connection():
                    self.dialog.after(0, lambda: messagebox.showinfo(
                        "VPN Test", "✅ VPN connection is active", parent=self.dialog))
                else:
                    self.dialog.after(0, lambda: messagebox.showwarning(
                        "VPN Test", "❌ VPN is not connected", parent=self.dialog))
            except Exception as e:
                self.dialog.after(0, lambda: messagebox.showerror(
                    "VPN Test", f"Error testing VPN: {str(e)}", parent=self.dialog))
        
        import threading
        threading.Thread(target=test, daemon=True).start()
    
    def _test_smb(self):
        """Test SMB mount"""
        from ..utils.network import get_network_manager
        
        network_manager = get_network_manager()
        
        def test():
            try:
                if network_manager.check_smb_mount():
                    self.dialog.after(0, lambda: messagebox.showinfo(
                        "SMB Test", "✅ Network drive is mounted", parent=self.dialog))
                else:
                    self.dialog.after(0, lambda: messagebox.showwarning(
                        "SMB Test", "❌ Network drive is not mounted", parent=self.dialog))
            except Exception as e:
                self.dialog.after(0, lambda: messagebox.showerror(
                    "SMB Test", f"Error testing SMB: {str(e)}", parent=self.dialog))
        
        import threading
        threading.Thread(target=test, daemon=True).start()
    
    def show(self) -> bool:
        """Show the dialog and return result"""
        self.dialog.wait_window()
        return self.result