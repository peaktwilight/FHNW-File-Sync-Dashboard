import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
from typing import Optional
import os
from datetime import datetime

import sv_ttk

from ..config.profile_manager import ProfileManager
from ..core.sync_engine import SyncEngine
from ..models.sync_profile import SyncProfile
from ..utils.logger import setup_logging, SyncLogger
from .profile_editor import ProfileEditorDialog
from .sync_preview import SyncPreviewDialog
from .connection_status import ConnectionStatusWidget
from .network_settings import NetworkSettingsDialog


class MainWindow:
    """Main application window with modern UI and profile management"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FHNW File Sync Dashboard")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Initialize components
        self.profile_manager = ProfileManager()
        self.sync_engine = SyncEngine()
        self.current_profile: Optional[SyncProfile] = None
        self.sync_thread: Optional[threading.Thread] = None
        self.progress_queue = queue.Queue()
        
        # Setup logging
        config = self.profile_manager.get_general_config()
        setup_logging(config.get('log_level', 'INFO'))
        
        # Apply theme
        sv_ttk.set_theme(config.get('theme', 'dark'))
        
        # Create UI
        self._create_menu()
        self._create_widgets()
        self._load_profiles()
        
        # Start progress monitor
        self._monitor_progress()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Profile", command=self._new_profile, accelerator="Ctrl+N")
        file_menu.add_command(label="Import Profile...", command=self._import_profile)
        file_menu.add_command(label="Export Profile...", command=self._export_profile)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close, accelerator="Ctrl+Q")
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Edit Profile", command=self._edit_profile, accelerator="Ctrl+E")
        edit_menu.add_command(label="Duplicate Profile", command=self._duplicate_profile)
        edit_menu.add_command(label="Delete Profile", command=self._delete_profile, accelerator="Delete")
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Toggle Theme", command=self._toggle_theme)
        view_menu.add_command(label="View Logs", command=self._view_logs)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Sync Preview", command=self._preview_sync)
        tools_menu.add_command(label="Dry Run", command=lambda: self._start_sync(dry_run=True))
        tools_menu.add_separator()
        tools_menu.add_command(label="Network Settings", command=self._open_network_settings)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
        
        # Bind keyboard shortcuts
        self.root.bind('<Control-n>', lambda e: self._new_profile())
        self.root.bind('<Control-e>', lambda e: self._edit_profile())
        self.root.bind('<Control-q>', lambda e: self._on_close())
        self.root.bind('<Delete>', lambda e: self._delete_profile())
    
    def _create_widgets(self):
        """Create main window widgets"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Left sidebar
        sidebar = ttk.Frame(main_frame, width=250)
        sidebar.grid(row=0, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 5), pady=10)
        sidebar.columnconfigure(0, weight=1)
        sidebar.rowconfigure(1, weight=1)
        
        # Profile section
        profile_header = ttk.Frame(sidebar)
        profile_header.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        profile_header.columnconfigure(0, weight=1)
        
        ttk.Label(profile_header, text="Sync Profiles", font=('', 12, 'bold')).grid(row=0, column=0, sticky=tk.W)
        
        # Profile list
        list_frame = ttk.Frame(sidebar)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Treeview for profiles
        self.profile_tree = ttk.Treeview(list_frame, selectmode='browse', show='tree')
        self.profile_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.profile_tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.profile_tree.configure(yscrollcommand=scrollbar.set)
        
        # Profile buttons
        button_frame = ttk.Frame(sidebar)
        button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(button_frame, text="New", command=self._new_profile).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Edit", command=self._edit_profile).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Delete", command=self._delete_profile).pack(side=tk.LEFT)
        
        # Connection status widget
        self.connection_widget = ConnectionStatusWidget(sidebar, self._on_connection_change)
        self.connection_widget.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(20, 0))
        
        # Right side - main content
        content_frame = ttk.Frame(main_frame)
        content_frame.grid(row=0, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 10), pady=10)
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(2, weight=1)
        
        # Profile details
        details_frame = ttk.LabelFrame(content_frame, text="Profile Details", padding="10")
        details_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        details_frame.columnconfigure(1, weight=1)
        
        # Profile info labels
        self.info_labels = {}
        info_items = [
            ("Name:", "name"),
            ("Source:", "source"),
            ("Destination:", "destination"),
            ("Mode:", "mode"),
            ("Last Sync:", "last_sync"),
            ("Status:", "status")
        ]
        
        for i, (label, key) in enumerate(info_items):
            ttk.Label(details_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=2)
            self.info_labels[key] = ttk.Label(details_frame, text="-")
            self.info_labels[key].grid(row=i, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Action buttons
        action_frame = ttk.Frame(content_frame)
        action_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.sync_button = ttk.Button(action_frame, text="Sync Now", command=self._start_sync, 
                                     style="Accent.TButton", state='disabled')
        self.sync_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.preview_button = ttk.Button(action_frame, text="Preview", command=self._preview_sync, 
                                        state='disabled')
        self.preview_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(action_frame, text="Stop", command=self._stop_sync, 
                                     state='disabled')
        self.stop_button.pack(side=tk.LEFT)
        
        # Progress section
        progress_frame = ttk.LabelFrame(content_frame, text="Progress", padding="10")
        progress_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        progress_frame.columnconfigure(0, weight=1)
        progress_frame.rowconfigure(0, weight=1)
        
        # Progress bar
        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           mode='determinate')
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(progress_frame, text="Ready")
        self.status_label.grid(row=1, column=0, sticky=tk.W)
        
        # Output text
        output_frame = ttk.Frame(progress_frame)
        output_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        
        self.output_text = tk.Text(output_frame, height=10, wrap=tk.WORD)
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        output_scroll = ttk.Scrollbar(output_frame, orient='vertical', command=self.output_text.yview)
        output_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.output_text.configure(yscrollcommand=output_scroll.set)
        
        # Clear button
        ttk.Button(progress_frame, text="Clear Output", 
                  command=lambda: self.output_text.delete(1.0, tk.END)).grid(
            row=3, column=0, sticky=tk.E, pady=(5, 0))
        
        # Bind tree selection
        self.profile_tree.bind('<<TreeviewSelect>>', self._on_profile_select)
    
    def _load_profiles(self):
        """Load profiles into the tree view"""
        # Clear existing items
        for item in self.profile_tree.get_children():
            self.profile_tree.delete(item)
        
        # Load profiles
        profiles = self.profile_manager.load_all_profiles()
        default_profile = self.profile_manager.get_default_profile()
        
        for profile in profiles:
            text = profile.name
            if default_profile and profile.id == default_profile.id:
                text += " (default)"
            
            item = self.profile_tree.insert('', 'end', text=text, tags=(profile.id,))
            
            # Select default or first profile
            if (default_profile and profile.id == default_profile.id) or (not default_profile and not self.current_profile):
                self.profile_tree.selection_set(item)
                self.profile_tree.focus(item)
    
    def _on_profile_select(self, event):
        """Handle profile selection"""
        selection = self.profile_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        tags = self.profile_tree.item(item, 'tags')
        if tags:
            profile_id = tags[0]
            self.current_profile = self.profile_manager.load_profile(profile_id)
            self._update_profile_display()
    
    def _on_connection_change(self, vpn_connected: bool, smb_mounted: bool):
        """Handle connection status changes"""
        self._update_profile_display()
    
    def _update_profile_display(self):
        """Update the profile details display"""
        if not self.current_profile:
            # Clear display
            for label in self.info_labels.values():
                label.config(text="-")
            self.sync_button.config(state='disabled')
            self.preview_button.config(state='disabled')
            return
        
        # Update labels
        self.info_labels['name'].config(text=self.current_profile.name)
        self.info_labels['source'].config(text=self.current_profile.source.path if self.current_profile.source else "-")
        self.info_labels['destination'].config(text=self.current_profile.destination.path if self.current_profile.destination else "-")
        self.info_labels['mode'].config(text=self.current_profile.sync_mode.value)
        
        if self.current_profile.last_sync:
            last_sync = self.current_profile.last_sync.strftime("%Y-%m-%d %H:%M:%S")
        else:
            last_sync = "Never"
        self.info_labels['last_sync'].config(text=last_sync)
        
        # Check connection requirements for sync availability
        can_sync = self.current_profile.enabled
        if can_sync and hasattr(self.current_profile.source, 'requires_vpn'):
            if self.current_profile.source.requires_vpn and not self.sync_engine.network_manager.check_vpn_connection():
                can_sync = False
        if can_sync and hasattr(self.current_profile.source, 'requires_smb'):
            if self.current_profile.source.requires_smb and not self.sync_engine.network_manager.check_smb_mount():
                # Allow sync if auto-connect is enabled
                can_sync = self.connection_widget.get_auto_connect()
        
        status_text = "Enabled" if self.current_profile.enabled else "Disabled"
        if self.current_profile.enabled and not can_sync:
            status_text += " (Network Required)"
        
        self.info_labels['status'].config(text=status_text)
        
        # Enable buttons
        self.sync_button.config(state='normal' if can_sync else 'disabled')
        self.preview_button.config(state='normal')
    
    def _new_profile(self):
        """Create a new profile"""
        dialog = ProfileEditorDialog(self.root, self.profile_manager)
        profile = dialog.show()
        if profile:
            self._load_profiles()
            # Select the new profile
            for item in self.profile_tree.get_children():
                if profile.id in self.profile_tree.item(item, 'tags'):
                    self.profile_tree.selection_set(item)
                    self.profile_tree.focus(item)
                    break
    
    def _edit_profile(self):
        """Edit the selected profile"""
        if not self.current_profile:
            return
        
        dialog = ProfileEditorDialog(self.root, self.profile_manager, self.current_profile)
        profile = dialog.show()
        if profile:
            self._load_profiles()
            self._update_profile_display()
    
    def _delete_profile(self):
        """Delete the selected profile"""
        if not self.current_profile:
            return
        
        if messagebox.askyesno("Confirm Delete", 
                              f"Are you sure you want to delete the profile '{self.current_profile.name}'?",
                              parent=self.root):
            self.profile_manager.delete_profile(self.current_profile.id)
            self.current_profile = None
            self._load_profiles()
    
    def _duplicate_profile(self):
        """Duplicate the selected profile"""
        if not self.current_profile:
            return
        
        new_name = f"{self.current_profile.name} (Copy)"
        new_profile = self.profile_manager.duplicate_profile(self.current_profile.id, new_name)
        if new_profile:
            self._load_profiles()
    
    def _import_profile(self):
        """Import a profile from file"""
        from tkinter import filedialog
        
        filename = filedialog.askopenfilename(
            parent=self.root,
            title="Import Profile",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            profile = self.profile_manager.import_profile(filename)
            if profile:
                self._load_profiles()
                messagebox.showinfo("Success", "Profile imported successfully", parent=self.root)
            else:
                messagebox.showerror("Error", "Failed to import profile", parent=self.root)
    
    def _export_profile(self):
        """Export the selected profile"""
        if not self.current_profile:
            return
        
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            parent=self.root,
            title="Export Profile",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"{self.current_profile.name}.json"
        )
        
        if filename:
            if self.profile_manager.export_profile(self.current_profile.id, filename):
                messagebox.showinfo("Success", "Profile exported successfully", parent=self.root)
            else:
                messagebox.showerror("Error", "Failed to export profile", parent=self.root)
    
    def _toggle_theme(self):
        """Toggle between light and dark theme"""
        current_theme = sv_ttk.get_theme()
        new_theme = "light" if current_theme == "dark" else "dark"
        sv_ttk.set_theme(new_theme)
        
        # Save preference
        config = self.profile_manager.get_general_config()
        config['theme'] = new_theme
        self.profile_manager._save_general_config(config)
    
    def _view_logs(self):
        """Open logs directory"""
        import webbrowser
        log_dir = os.path.expanduser("~/.fhnw_sync/logs")
        if os.path.exists(log_dir):
            webbrowser.open(f"file://{log_dir}")
    
    def _open_network_settings(self):
        """Open network settings dialog"""
        dialog = NetworkSettingsDialog(self.root)
        dialog.show()
    
    def _preview_sync(self):
        """Show sync preview dialog"""
        if not self.current_profile:
            return
        
        dialog = SyncPreviewDialog(self.root, self.sync_engine, self.current_profile)
        dialog.show()
    
    def _start_sync(self, dry_run: bool = False):
        """Start sync operation"""
        if not self.current_profile or self.sync_thread and self.sync_thread.is_alive():
            return
        
        # Clear output
        self.output_text.delete(1.0, tk.END)
        self.progress_var.set(0)
        
        # Update UI
        self.sync_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.status_label.config(text="Starting sync..." if not dry_run else "Starting dry run...")
        
        # Start sync in thread
        self.sync_thread = threading.Thread(
            target=self._sync_worker,
            args=(self.current_profile, dry_run),
            daemon=True
        )
        self.sync_thread.start()
    
    def _sync_worker(self, profile: SyncProfile, dry_run: bool):
        """Worker thread for sync operation"""
        sync_logger = SyncLogger(profile.id)
        
        try:
            sync_logger.log_start(
                profile.source.path if profile.source else "Unknown",
                profile.destination.path if profile.destination else "Unknown"
            )
            
            # Progress callback
            def progress_callback(message: str, percent: float):
                self.progress_queue.put(('progress', message, percent))
                sync_logger.log_progress(message, percent)
            
            # Check and ensure connections if auto-connect is enabled
            auto_connect = self.connection_widget.get_auto_connect()
            if auto_connect:
                self.progress_queue.put(('status', 'Ensuring connections...', 0))
                success, message = self.sync_engine.ensure_connections(profile, progress_callback, auto_connect)
                if not success:
                    sync_logger.log_error(message)
                    self.progress_queue.put(('error', message, 0))
                    return
            
            # Perform sync
            self.progress_queue.put(('status', 'Syncing...', 25 if auto_connect else 0))
            success, message = self.sync_engine.sync(profile, progress_callback, dry_run)
            
            # Update profile last sync time
            if success and not dry_run:
                profile.last_sync = datetime.now()
                self.profile_manager.save_profile(profile)
            
            sync_logger.log_complete(success, message)
            
            # Update UI
            status = "Sync completed" if success else "Sync failed"
            if dry_run:
                status = "Dry run " + status.lower()
            
            self.progress_queue.put(('complete', status, 100 if success else 0))
            self.progress_queue.put(('message', message, 0))
            
        except Exception as e:
            sync_logger.log_error(str(e))
            self.progress_queue.put(('error', f"Error: {str(e)}", 0))
        finally:
            self.progress_queue.put(('done', '', 0))
    
    def _stop_sync(self):
        """Stop the current sync operation"""
        self.sync_engine.cancel()
        self.stop_button.config(state='disabled')
        self.status_label.config(text="Cancelling...")
    
    def _monitor_progress(self):
        """Monitor progress queue and update UI"""
        try:
            while True:
                msg_type, message, value = self.progress_queue.get_nowait()
                
                if msg_type == 'progress':
                    self.output_text.insert(tk.END, message + '\n')
                    self.output_text.see(tk.END)
                    if value >= 0:
                        self.progress_var.set(int(value))
                
                elif msg_type == 'status':
                    self.status_label.config(text=message)
                
                elif msg_type == 'message':
                    self.output_text.insert(tk.END, '\n' + message + '\n')
                    self.output_text.see(tk.END)
                
                elif msg_type == 'error':
                    self.output_text.insert(tk.END, f'\nERROR: {message}\n')
                    self.output_text.see(tk.END)
                    self.status_label.config(text="Error")
                
                elif msg_type == 'complete':
                    self.status_label.config(text=message)
                    self.progress_var.set(int(value))
                
                elif msg_type == 'done':
                    self.sync_button.config(state='normal')
                    self.stop_button.config(state='disabled')
                    self._update_profile_display()
                
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self._monitor_progress)
    
    def _show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About",
            "FHNW File Sync Dashboard\n\n"
            "Version 2.0\n\n"
            "A modern file synchronization tool with profile management\n\n"
            "© 2024 FHNW Sync Tool",
            parent=self.root
        )
    
    def _on_close(self):
        """Handle window close"""
        if self.sync_thread and self.sync_thread.is_alive():
            if messagebox.askyesno("Confirm Exit", 
                                  "A sync operation is in progress. Are you sure you want to exit?",
                                  parent=self.root):
                self.sync_engine.cancel()
                self.root.quit()
        else:
            self.root.quit()
    
    def run(self):
        """Run the application"""
        self.root.mainloop()


def main():
    """Main entry point"""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()