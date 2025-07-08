import tkinter as tk
from tkinter import ttk
import threading
from typing import List, Tuple

from ..core.sync_engine import SyncEngine
from ..models.sync_profile import SyncProfile


class SyncPreviewDialog:
    """Dialog to preview what will be synced"""
    
    def __init__(self, parent, sync_engine: SyncEngine, profile: SyncProfile):
        self.parent = parent
        self.sync_engine = sync_engine
        self.profile = profile
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Sync Preview")
        self.dialog.geometry("700x500")
        self.dialog.resizable(True, True)
        
        # Make modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        self._start_analysis()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """Create dialog widgets"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        header_frame.columnconfigure(1, weight=1)
        
        ttk.Label(header_frame, text="Profile:", font=('', 10, 'bold')).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(header_frame, text=self.profile.name).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(header_frame, text="Source:", font=('', 10, 'bold')).grid(row=1, column=0, sticky=tk.W)
        ttk.Label(header_frame, text=self.profile.source.path if self.profile.source else "-").grid(
            row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(header_frame, text="Destination:", font=('', 10, 'bold')).grid(row=2, column=0, sticky=tk.W)
        ttk.Label(header_frame, text=self.profile.destination.path if self.profile.destination else "-").grid(
            row=2, column=1, sticky=tk.W, padx=(10, 0))
        
        # Status
        self.status_label = ttk.Label(main_frame, text="Analyzing...")
        self.status_label.grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        
        # Progress
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.progress.start()
        
        # Results notebook
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Summary tab
        summary_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(summary_frame, text="Summary")
        
        self.summary_text = tk.Text(summary_frame, wrap=tk.WORD, height=15)
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        
        # Files tab
        files_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(files_frame, text="Files to Sync")
        
        # Tree for files
        tree_frame = ttk.Frame(files_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.files_tree = ttk.Treeview(tree_frame, columns=('size', 'action'), show='tree headings')
        self.files_tree.heading('#0', text='File')
        self.files_tree.heading('size', text='Size')
        self.files_tree.heading('action', text='Action')
        self.files_tree.column('size', width=100)
        self.files_tree.column('action', width=100)
        
        self.files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.files_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.files_tree.configure(yscrollcommand=scrollbar.set)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, sticky=(tk.W, tk.E))
        
        ttk.Button(button_frame, text="Close", command=self.dialog.destroy).pack(side=tk.RIGHT)
        self.sync_button = ttk.Button(button_frame, text="Sync Now", command=self._sync_now, 
                                     style="Accent.TButton", state='disabled')
        self.sync_button.pack(side=tk.RIGHT, padx=(0, 10))
    
    def _start_analysis(self):
        """Start analyzing what will be synced"""
        thread = threading.Thread(target=self._analyze_sync, daemon=True)
        thread.start()
    
    def _analyze_sync(self):
        """Analyze what will be synced"""
        try:
            # Get size estimate
            file_count, total_size = self.sync_engine.estimate_sync_size(self.profile)
            
            # Run dry-run to get detailed info
            def progress_callback(message: str, percent: float):
                # Collect file information
                pass
            
            success, message = self.sync_engine.sync(self.profile, progress_callback, dry_run=True)
            
            # Update UI in main thread
            self.dialog.after(0, self._update_results, file_count, total_size, success, message)
            
        except Exception as e:
            self.dialog.after(0, self._update_error, str(e))
    
    def _update_results(self, file_count: int, total_size: int, success: bool, message: str):
        """Update UI with analysis results"""
        self.progress.stop()
        self.progress.grid_remove()
        
        if success:
            self.status_label.config(text=f"Analysis complete: {file_count} files, {self._format_size(total_size)}")
            self.sync_button.config(state='normal')
            
            # Update summary
            summary = f"""Sync Preview Summary
===================

Profile: {self.profile.name}
Mode: {self.profile.sync_mode.value}
Direction: {self.profile.sync_direction.value}

Files to sync: {file_count}
Total size: {self._format_size(total_size)}

Options:
- Preserve permissions: {'Yes' if self.profile.preserve_permissions else 'No'}
- Preserve timestamps: {'Yes' if self.profile.preserve_timestamps else 'No'}
- Follow symlinks: {'Yes' if self.profile.follow_symlinks else 'No'}
- Retry count: {self.profile.retry_count}
- Bandwidth limit: {f'{self.profile.bandwidth_limit} KB/s' if self.profile.bandwidth_limit else 'Unlimited'}

Filters:
- Exclude hidden: {'Yes' if self.profile.rules.exclude_hidden else 'No'}
- Include patterns: {len(self.profile.rules.include_patterns)}
- Exclude patterns: {len(self.profile.rules.exclude_patterns)}
"""
            self.summary_text.delete(1.0, tk.END)
            self.summary_text.insert(1.0, summary)
            
        else:
            self.status_label.config(text=f"Analysis failed: {message}")
            self.summary_text.delete(1.0, tk.END)
            self.summary_text.insert(1.0, f"Error: {message}")
    
    def _update_error(self, error: str):
        """Update UI with error"""
        self.progress.stop()
        self.progress.grid_remove()
        self.status_label.config(text=f"Error: {error}")
    
    def _format_size(self, size: int) -> str:
        """Format size in bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
    
    def _sync_now(self):
        """Close dialog and trigger sync"""
        self.dialog.destroy()
        # The parent window should handle the actual sync
    
    def show(self):
        """Show the dialog"""
        self.dialog.wait_window()