import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, Callable
import os

from ..models.sync_profile import SyncProfile, SyncLocation, SyncMode, SyncDirection, SyncRule
from ..config.profile_manager import ProfileManager


class ProfileEditorDialog:
    """Dialog for creating and editing sync profiles"""
    
    def __init__(self, parent, profile_manager: ProfileManager, profile: Optional[SyncProfile] = None):
        self.parent = parent
        self.profile_manager = profile_manager
        self.profile = profile
        self.result = None
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit Profile" if profile else "New Profile")
        self.dialog.geometry("800x700")
        self.dialog.resizable(True, True)
        
        # Make modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Variables
        self.name_var = tk.StringVar(value=profile.name if profile else "")
        self.description_var = tk.StringVar(value=profile.description if profile else "")
        self.source_var = tk.StringVar(value=profile.source.path if profile and profile.source else "")
        self.dest_var = tk.StringVar(value=profile.destination.path if profile and profile.destination else "")
        self.mode_var = tk.StringVar(value=profile.sync_mode.value if profile else SyncMode.UPDATE.value)
        self.direction_var = tk.StringVar(value=profile.sync_direction.value if profile else SyncDirection.REMOTE_TO_LOCAL.value)
        
        # Advanced options
        self.preserve_perms_var = tk.BooleanVar(value=profile.preserve_permissions if profile else True)
        self.preserve_times_var = tk.BooleanVar(value=profile.preserve_timestamps if profile else True)
        self.follow_links_var = tk.BooleanVar(value=profile.follow_symlinks if profile else False)
        self.retry_var = tk.IntVar(value=profile.retry_count if profile else 3)
        self.bandwidth_var = tk.StringVar(value=str(profile.bandwidth_limit) if profile and profile.bandwidth_limit else "")
        
        # Git options
        self.is_git_var = tk.BooleanVar(value=profile.is_git_repo if profile else False)
        self.auto_pull_var = tk.BooleanVar(value=profile.auto_pull if profile else True)
        self.auto_commit_var = tk.BooleanVar(value=profile.auto_commit if profile else False)
        
        # Rules
        self.exclude_hidden_var = tk.BooleanVar(value=profile.rules.exclude_hidden if profile else True)
        
        self._create_widgets()
        self._load_profile_data()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """Create the dialog widgets"""
        # Main container with padding
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # Basic Information Section
        ttk.Label(main_frame, text="Basic Information", font=('', 12, 'bold')).grid(
            row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        row += 1
        
        # Name
        ttk.Label(main_frame, text="Profile Name:").grid(row=row, column=0, sticky=tk.W, padx=(20, 0))
        ttk.Entry(main_frame, textvariable=self.name_var, width=40).grid(
            row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        row += 1
        
        # Description
        ttk.Label(main_frame, text="Description:").grid(row=row, column=0, sticky=tk.W, padx=(20, 0))
        ttk.Entry(main_frame, textvariable=self.description_var, width=40).grid(
            row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        row += 1
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)
        row += 1
        
        # Sync Locations Section
        ttk.Label(main_frame, text="Sync Locations", font=('', 12, 'bold')).grid(
            row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        row += 1
        
        # Source
        ttk.Label(main_frame, text="Source:").grid(row=row, column=0, sticky=tk.W, padx=(20, 0))
        source_frame = ttk.Frame(main_frame)
        source_frame.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Entry(source_frame, textvariable=self.source_var, width=30).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(source_frame, text="Browse", command=self._browse_source).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(source_frame, text="FHNW Drive", command=self._use_fhnw_source).pack(side=tk.LEFT, padx=(5, 0))
        row += 1
        
        # Destination
        ttk.Label(main_frame, text="Destination:").grid(row=row, column=0, sticky=tk.W, padx=(20, 0))
        dest_frame = ttk.Frame(main_frame)
        dest_frame.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Entry(dest_frame, textvariable=self.dest_var, width=35).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(dest_frame, text="Browse", command=self._browse_dest).pack(side=tk.LEFT, padx=(5, 0))
        row += 1
        
        # Sync Direction
        ttk.Label(main_frame, text="Direction:").grid(row=row, column=0, sticky=tk.W, padx=(20, 0))
        direction_frame = ttk.Frame(main_frame)
        direction_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        for value, text in [
            (SyncDirection.REMOTE_TO_LOCAL.value, "Remote → Local"),
            (SyncDirection.LOCAL_TO_REMOTE.value, "Local → Remote"),
            (SyncDirection.BIDIRECTIONAL.value, "Bidirectional")
        ]:
            ttk.Radiobutton(direction_frame, text=text, variable=self.direction_var, 
                           value=value).pack(side=tk.LEFT, padx=(0, 10))
        row += 1
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)
        row += 1
        
        # Sync Options Section
        ttk.Label(main_frame, text="Sync Options", font=('', 12, 'bold')).grid(
            row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        row += 1
        
        # Sync Mode
        ttk.Label(main_frame, text="Sync Mode:").grid(row=row, column=0, sticky=tk.W, padx=(20, 0))
        mode_frame = ttk.Frame(main_frame)
        mode_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        for value, text, tooltip in [
            (SyncMode.UPDATE.value, "Update", "Only copy newer files"),
            (SyncMode.MIRROR.value, "Mirror", "Make destination exactly match source")
        ]:
            btn = ttk.Radiobutton(mode_frame, text=text, variable=self.mode_var, value=value)
            btn.pack(side=tk.LEFT, padx=(0, 10))
        row += 1
        
        # Advanced options in notebook
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        row += 1
        
        # Advanced tab
        advanced_frame = ttk.Frame(notebook, padding="10")
        notebook.add(advanced_frame, text="Advanced")
        
        adv_row = 0
        ttk.Checkbutton(advanced_frame, text="Preserve file permissions", 
                       variable=self.preserve_perms_var).grid(row=adv_row, column=0, sticky=tk.W)
        adv_row += 1
        
        ttk.Checkbutton(advanced_frame, text="Preserve timestamps", 
                       variable=self.preserve_times_var).grid(row=adv_row, column=0, sticky=tk.W)
        adv_row += 1
        
        ttk.Checkbutton(advanced_frame, text="Follow symbolic links", 
                       variable=self.follow_links_var).grid(row=adv_row, column=0, sticky=tk.W)
        adv_row += 1
        
        # Retry count
        retry_frame = ttk.Frame(advanced_frame)
        retry_frame.grid(row=adv_row, column=0, sticky=tk.W, pady=5)
        ttk.Label(retry_frame, text="Retry count:").pack(side=tk.LEFT)
        ttk.Spinbox(retry_frame, from_=0, to=10, textvariable=self.retry_var, 
                   width=10).pack(side=tk.LEFT, padx=(5, 0))
        adv_row += 1
        
        # Bandwidth limit
        bw_frame = ttk.Frame(advanced_frame)
        bw_frame.grid(row=adv_row, column=0, sticky=tk.W, pady=5)
        ttk.Label(bw_frame, text="Bandwidth limit (KB/s):").pack(side=tk.LEFT)
        ttk.Entry(bw_frame, textvariable=self.bandwidth_var, width=10).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(bw_frame, text="(empty for unlimited)").pack(side=tk.LEFT, padx=(5, 0))
        
        # Filters tab
        filters_frame = ttk.Frame(notebook, padding="10")
        notebook.add(filters_frame, text="Filters")
        
        ttk.Checkbutton(filters_frame, text="Exclude hidden files", 
                       variable=self.exclude_hidden_var).grid(row=0, column=0, sticky=tk.W)
        
        # Include patterns
        ttk.Label(filters_frame, text="Include patterns (one per line):").grid(row=1, column=0, sticky=tk.W, pady=(10, 5))
        self.include_text = tk.Text(filters_frame, height=4, width=40)
        self.include_text.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        # Exclude patterns
        ttk.Label(filters_frame, text="Exclude patterns (one per line):").grid(row=3, column=0, sticky=tk.W, pady=(10, 5))
        self.exclude_text = tk.Text(filters_frame, height=4, width=40)
        self.exclude_text.grid(row=4, column=0, sticky=(tk.W, tk.E))
        
        # Git tab
        git_frame = ttk.Frame(notebook, padding="10")
        notebook.add(git_frame, text="Git")
        
        ttk.Checkbutton(git_frame, text="This is a Git repository", 
                       variable=self.is_git_var, command=self._toggle_git_options).grid(row=0, column=0, sticky=tk.W)
        
        self.git_options_frame = ttk.Frame(git_frame)
        self.git_options_frame.grid(row=1, column=0, sticky=tk.W, padx=(20, 0), pady=(5, 0))
        
        ttk.Checkbutton(self.git_options_frame, text="Auto pull before sync", 
                       variable=self.auto_pull_var).grid(row=0, column=0, sticky=tk.W)
        ttk.Checkbutton(self.git_options_frame, text="Auto commit after sync", 
                       variable=self.auto_commit_var).grid(row=1, column=0, sticky=tk.W)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=3, pady=(20, 0))
        
        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Save", command=self._save, style="Accent.TButton").pack(side=tk.RIGHT)
        
        # Initial state
        self._toggle_git_options()
    
    def _browse_source(self):
        """Browse for source directory"""
        path = filedialog.askdirectory(
            parent=self.dialog,
            title="Select Source Directory",
            initialdir=self.source_var.get() or os.path.expanduser("~")
        )
        if path:
            self.source_var.set(path)
    
    def _browse_dest(self):
        """Browse for destination directory"""
        path = filedialog.askdirectory(
            parent=self.dialog,
            title="Select Destination Directory",
            initialdir=self.dest_var.get() or os.path.expanduser("~")
        )
        if path:
            self.dest_var.set(path)
    
    def _use_fhnw_source(self):
        """Set source to FHNW network drive"""
        from ..utils.network import get_network_manager
        
        network_manager = get_network_manager()
        
        # Check if FHNW drive is mounted and get actual mount point
        if network_manager.check_smb_mount():
            mount_point = network_manager.get_fhnw_mount_point()
            if mount_point:
                self.source_var.set(mount_point)
                messagebox.showinfo(
                    "FHNW Network Drive",
                    f"Source set to FHNW network drive.\n\n"
                    f"Mount point: {mount_point}\n\n"
                    f"The network drive is currently connected.",
                    parent=self.dialog
                )
            else:
                # Fallback to default
                self.source_var.set("/Volumes/data")
                messagebox.showinfo(
                    "FHNW Network Drive",
                    "Source set to FHNW network drive.\n\n"
                    "Mount point: /Volumes/data (default)\n\n"
                    "Note: Connect to VPN and mount the drive first.",
                    parent=self.dialog
                )
        else:
            # Not mounted, use default and show help
            self.source_var.set("/Volumes/data")
            result = messagebox.askyesno(
                "FHNW Network Drive Not Connected",
                "The FHNW network drive is not currently mounted.\n\n"
                "Source has been set to the default location: /Volumes/data\n\n"
                "Would you like to see connection instructions?",
                parent=self.dialog
            )
            
            if result:
                self._show_connection_help()
    
    def _show_connection_help(self):
        """Show connection help for FHNW network"""
        from ..utils.network import get_network_manager
        
        network_manager = get_network_manager()
        
        # Create help dialog
        help_dialog = tk.Toplevel(self.dialog)
        help_dialog.title("FHNW Connection Help")
        help_dialog.geometry("600x400")
        help_dialog.transient(self.dialog)
        
        main_frame = ttk.Frame(help_dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # VPN Section
        ttk.Label(main_frame, text="Step 1: Connect to VPN", 
                 font=('', 12, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        
        vpn_text = tk.Text(main_frame, height=6, wrap=tk.WORD)
        vpn_text.pack(fill=tk.X, pady=(0, 10))
        vpn_text.insert(1.0, network_manager.get_vpn_help_instructions())
        vpn_text.configure(state='disabled')
        
        # SMB Section
        ttk.Label(main_frame, text="Step 2: Connect to Network Drive", 
                 font=('', 12, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        
        smb_text = tk.Text(main_frame, height=8, wrap=tk.WORD)
        smb_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        smb_text.insert(1.0, network_manager.get_smb_help_instructions())
        smb_text.configure(state='disabled')
        
        ttk.Button(main_frame, text="Close", command=help_dialog.destroy).pack()
    
    def _toggle_git_options(self):
        """Enable/disable git options based on checkbox"""
        if self.is_git_var.get():
            for child in self.git_options_frame.winfo_children():
                child.configure(state='normal')
        else:
            for child in self.git_options_frame.winfo_children():
                child.configure(state='disabled')
    
    def _load_profile_data(self):
        """Load existing profile data into form"""
        if not self.profile:
            return
        
        # Load filter patterns
        if self.profile.rules:
            self.include_text.delete(1.0, tk.END)
            self.include_text.insert(1.0, '\n'.join(self.profile.rules.include_patterns))
            
            self.exclude_text.delete(1.0, tk.END)
            self.exclude_text.insert(1.0, '\n'.join(self.profile.rules.exclude_patterns))
    
    def _save(self):
        """Save the profile"""
        # Validate required fields
        if not self.name_var.get().strip():
            messagebox.showerror("Error", "Profile name is required", parent=self.dialog)
            return
        
        if not self.source_var.get().strip():
            messagebox.showerror("Error", "Source path is required", parent=self.dialog)
            return
        
        if not self.dest_var.get().strip():
            messagebox.showerror("Error", "Destination path is required", parent=self.dialog)
            return
        
        # Create or update profile
        if self.profile:
            profile = self.profile
        else:
            profile = self.profile_manager.create_profile(self.name_var.get())
        
        # Update basic info
        profile.name = self.name_var.get()
        profile.description = self.description_var.get()
        
        # Update locations
        source_path = self.source_var.get()
        
        # Check if this is FHNW network drive
        if (source_path.startswith("/Volumes/data") or 
            "fs.edu.ds.fhnw.ch" in source_path or
            source_path.startswith("\\\\fs.edu.ds.fhnw.ch")):
            profile.source = SyncLocation.create_fhnw_location(source_path)
        else:
            profile.source = SyncLocation(
                path=source_path,
                name="Source",
                is_remote=not os.path.exists(source_path)
            )
        
        profile.destination = SyncLocation(
            path=self.dest_var.get(),
            name="Destination",
            is_remote=False
        )
        
        # Update sync settings
        profile.sync_mode = SyncMode(self.mode_var.get())
        profile.sync_direction = SyncDirection(self.direction_var.get())
        
        # Update advanced options
        profile.preserve_permissions = self.preserve_perms_var.get()
        profile.preserve_timestamps = self.preserve_times_var.get()
        profile.follow_symlinks = self.follow_links_var.get()
        profile.retry_count = self.retry_var.get()
        
        try:
            profile.bandwidth_limit = int(self.bandwidth_var.get()) if self.bandwidth_var.get() else None
        except ValueError:
            profile.bandwidth_limit = None
        
        # Update Git options
        profile.is_git_repo = self.is_git_var.get()
        profile.auto_pull = self.auto_pull_var.get()
        profile.auto_commit = self.auto_commit_var.get()
        
        # Update rules
        include_patterns = [p.strip() for p in self.include_text.get(1.0, tk.END).strip().split('\n') if p.strip()]
        exclude_patterns = [p.strip() for p in self.exclude_text.get(1.0, tk.END).strip().split('\n') if p.strip()]
        
        profile.rules = SyncRule(
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            exclude_hidden=self.exclude_hidden_var.get()
        )
        
        # Validate profile
        errors = profile.validate()
        if errors:
            messagebox.showerror("Validation Error", '\n'.join(errors), parent=self.dialog)
            return
        
        # Save profile
        if self.profile_manager.save_profile(profile):
            self.result = profile
            self.dialog.destroy()
        else:
            messagebox.showerror("Error", "Failed to save profile", parent=self.dialog)
    
    def _cancel(self):
        """Cancel the dialog"""
        self.dialog.destroy()
    
    def show(self) -> Optional[SyncProfile]:
        """Show the dialog and return the result"""
        self.dialog.wait_window()
        return self.result