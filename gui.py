import tkinter as tk
from tkinter import ttk
import subprocess
import platform
import threading
import queue
import sv_ttk
import logging
import itertools
import time
from tkinter import messagebox
import configparser
import os

# --- Constants ---
WINDOW_TITLE = "FHNW File Sync Dashboard BETA v0.5"
SYNC_BUTTON_TEXT = "Sync Now"
CLEAR_BUTTON_TEXT = "Clear Output"
SPINNER_CHARS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
CONFIG_FILE = "config.txt"
CONFIG_VERSION = "1.0"
REQUIRED_FIELDS = ['destination', 'source_paths']

def load_config():
    """Loads and validates the configuration from config.txt."""
    config = configparser.ConfigParser()
    
    # Create default config if it doesn't exist
    if not os.path.exists(CONFIG_FILE):
        config['DEFAULT'] = {
            'VERSION': CONFIG_VERSION,
            'destination': '',
            'source_paths': '',
            'log_level': 'INFO',
            'max_rsync_retries': '3',
            'enable_git_pull': 'True',
            'enable_swegl_script': 'True'
        }
        try:
            with open(CONFIG_FILE, 'w') as configfile:
                config.write(configfile)
            messagebox.showinfo("Config Created", 
                "A new config.txt file has been created with default values.\n"
                "Please edit it to set your sync paths and settings.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create config: {str(e)}")
            return None
    
    try:
        config.read(CONFIG_FILE)
        
        # Check config version
        if 'VERSION' not in config['DEFAULT']:
            config['DEFAULT']['VERSION'] = CONFIG_VERSION
            with open(CONFIG_FILE, 'w') as configfile:
                config.write(configfile)
        
        # Validate required fields
        missing_fields = [field for field in REQUIRED_FIELDS if field not in config['DEFAULT']]
        if missing_fields:
            messagebox.error("Error", 
                f"Config file is missing required fields: {', '.join(missing_fields)}")
            return None
            
        # Validate source paths
        source_paths = config['DEFAULT']['source_paths'].split(',')
        if not any(source_paths):
            messagebox.error("Error", "At least one source path must be specified")
            return None
            
        return config
    except Exception as e:
        messagebox.error("Error", f"Failed to load config: {str(e)}")
        return None

class SpinnerThread(threading.Thread):
    def __init__(self, label):
        super().__init__()
        self.label = label
        self._stop_event = threading.Event()
        self.daemon = True  # Thread will be killed when main program exits

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        for char in itertools.cycle(SPINNER_CHARS):
            if self.stopped():
                break
            self.label.config(text=f"{char} Syncing...")
            time.sleep(0.1)
        self.label.config(text="")  # Clear the spinner when done

class ConfigDialog(tk.Toplevel):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.title("Settings")
        self.config = config
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Create settings form
        self.create_form()
        
        # Set size and position
        self.geometry("800x600")
        self.resizable(True, True)
        self.minsize(600, 400)
        
        # Center the window
        self.center_window()
        
    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
        
    def create_form(self):
        # Create main frame with padding
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollable frame for settings
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Settings fields
        self.settings = {}
        row = 0
        
        # Section header style
        def create_section_header(text):
            header = ttk.Label(scrollable_frame, text=text, 
                             font=("Helvetica", 12, "bold"),
                             foreground="#4a90e2")
            header.grid(row=row, column=0, sticky="w", pady=(15, 10))
            return header
            
        # Helper function for consistent label styling
        def create_label(text):
            return ttk.Label(scrollable_frame, text=text, 
                           font=("Helvetica", 11),
                           padding=(10, 0, 0, 0))
        
        # Helper function for consistent entry styling
        def create_entry():
            entry = ttk.Entry(scrollable_frame, width=60, 
                            font=("Helvetica", 10))
            entry.configure(style='Custom.TEntry')
            return entry
            
        # Create section headers
        create_section_header("File Sync Settings")
        row += 1
        
        # Destination directory
        create_label("Destination Directory:").grid(row=row, column=0, sticky="w", pady=(0, 5))
        row += 1
        self.settings['destination'] = create_entry()
        self.settings['destination'].insert(0, self.config['DEFAULT'].get('destination', ''))
        self.settings['destination'].grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
        row += 1
        
        # Source paths - Format with one path per line
        create_label("Source Paths:").grid(row=row, column=0, sticky="w", pady=(0, 5))
        row += 1
        self.settings['source_paths'] = tk.Text(scrollable_frame, height=6, width=60, font=("Helvetica", 10))
        source_paths = self.config['DEFAULT'].get('source_paths', '')
        # Format paths one per line
        formatted_paths = '\n'.join(path.strip() for path in source_paths.split(','))
        self.settings['source_paths'].insert('1.0', formatted_paths)
        
        # Add scrollbar to source paths text area
        source_scroll = ttk.Scrollbar(scrollable_frame, orient="vertical", command=self.settings['source_paths'].yview)
        self.settings['source_paths'].configure(yscrollcommand=source_scroll.set)
        
        self.settings['source_paths'].grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        source_scroll.grid(row=row, column=2, sticky="ns")
        
        row += 1
        
        # Create section header for Git/SWEGL settings
        create_section_header("Repository & Script Settings")
        row += 1
        
        # OOP repo path
        create_label("OOP Repository Path:").grid(row=row, column=0, sticky="w", pady=(0, 5))
        row += 1
        self.settings['oop_repo_path'] = create_entry()
        self.settings['oop_repo_path'].insert(0, self.config['DEFAULT'].get('oop_repo_path', ''))
        self.settings['oop_repo_path'].grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
        row += 1
        
        # SWEGL script path
        create_label("SWEGL Script Path:").grid(row=row, column=0, sticky="w", pady=(0, 5))
        row += 1
        self.settings['swegl_script_path'] = create_entry()
        self.settings['swegl_script_path'].insert(0, self.config['DEFAULT'].get('swegl_script_path', ''))
        self.settings['swegl_script_path'].grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
        row += 1
        
        # Create section header for Advanced Settings
        create_section_header("Advanced Settings")
        row += 1
        
        # Create a frame for checkboxes with better spacing
        checkbox_frame = ttk.Frame(scrollable_frame)
        checkbox_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(10, 15))
        
        # Enable git pull
        self.settings['enable_git_pull'] = tk.BooleanVar(value=self.config['DEFAULT'].getboolean('enable_git_pull', True))
        ttk.Checkbutton(checkbox_frame, text="Enable Git Pull", 
                       variable=self.settings['enable_git_pull']).pack(side=tk.LEFT, padx=(0, 20))
        
        # Enable SWEGL script
        self.settings['enable_swegl_script'] = tk.BooleanVar(value=self.config['DEFAULT'].getboolean('enable_swegl_script', True))
        ttk.Checkbutton(checkbox_frame, text="Enable SWEGL Script", 
                       variable=self.settings['enable_swegl_script']).pack(side=tk.LEFT)
        
        row += 1
        
        # Create a frame for dropdown and number input
        options_frame = ttk.Frame(scrollable_frame)
        options_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
        # Log level
        ttk.Label(options_frame, text="Log Level:").pack(side=tk.LEFT, padx=(0, 10))
        self.settings['log_level'] = ttk.Combobox(options_frame, 
                                                 values=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                                                 width=15,
                                                 state="readonly")
        self.settings['log_level'].set(self.config['DEFAULT'].get('log_level', 'INFO'))
        self.settings['log_level'].pack(side=tk.LEFT, padx=(0, 20))
        
        # Max retries
        ttk.Label(options_frame, text="Max Retries:").pack(side=tk.LEFT, padx=(0, 10))
        self.settings['max_rsync_retries'] = ttk.Entry(options_frame, width=5)
        self.settings['max_rsync_retries'].insert(0, self.config['DEFAULT'].get('max_rsync_retries', '3'))
        self.settings['max_rsync_retries'].pack(side=tk.LEFT)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        ttk.Button(button_frame, text="Save", command=self.save_settings, style='Accent.TButton').pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Pack everything
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        button_frame.pack(side="bottom", pady=10, fill="x")
        
        # Configure grid weights
        scrollable_frame.grid_columnconfigure(1, weight=1)
        
    def save_settings(self):
        try:
            # Update config object
            self.config['DEFAULT']['destination'] = self.settings['destination'].get()
            # Join multiple lines back into comma-separated string
            source_paths = ','.join(
                line.strip() 
                for line in self.settings['source_paths'].get('1.0', tk.END).splitlines() 
                if line.strip()
            )
            self.config['DEFAULT']['source_paths'] = source_paths
            self.config['DEFAULT']['oop_repo_path'] = self.settings['oop_repo_path'].get()
            self.config['DEFAULT']['swegl_script_path'] = self.settings['swegl_script_path'].get()
            self.config['DEFAULT']['enable_git_pull'] = str(self.settings['enable_git_pull'].get())
            self.config['DEFAULT']['enable_swegl_script'] = str(self.settings['enable_swegl_script'].get())
            self.config['DEFAULT']['log_level'] = self.settings['log_level'].get()
            self.config['DEFAULT']['max_rsync_retries'] = self.settings['max_rsync_retries'].get()
            
            # Save to file
            with open(CONFIG_FILE, 'w') as configfile:
                self.config.write(configfile)
            
            messagebox.showinfo("Success", "Settings saved successfully!")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")

class MainWindow:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title(WINDOW_TITLE)
        self.window.geometry("600x500")
        self.window.minsize(500, 400)
        
        # Initialize theme
        self.current_theme = "dark"
        sv_ttk.set_theme(self.current_theme)
        
        # Window state
        self.window_visible = True
        
        # System tray icon
        self.tray_icon = None
        if platform.system() != "Linux":  # Linux has limited system tray support
            try:
                import pystray
                from PIL import Image, ImageDraw
                
                # Create a default icon if icon.png doesn't exist
                try:
                    icon = Image.open("icon.png")
                except FileNotFoundError:
                    # Create a simple colored square icon
                    icon = Image.new('RGB', (64, 64), color='#4a90e2')
                    draw = ImageDraw.Draw(icon)
                    # Add 'FS' text in white
                    draw.text((20, 20), 'FS', fill='white')
                    
                self.tray_icon = pystray.Icon(
                    "FHNW Sync",
                    icon,
                    menu=pystray.Menu(
                        pystray.MenuItem("Show/Hide", self.toggle_window),
                        pystray.MenuItem("Exit", self.on_closing)
                    )
                )
            except ImportError:
                pass
        
        self.config = load_config()
        self.output_queue = queue.Queue()
        self.scheduled_update = None
        self.spinner_thread = None
        
        # Add status indicators
        self.mount_status = False
        
        # Create GUI elements
        self.setup_gui()
        
        # Set up the window close handler
        self.window.protocol("WM_DELETE_WINDOW", self.hide_window)
        
        # Start status checker
        self.check_connection_status()
        
        # Start tray icon if available
        if self.tray_icon:
            self.tray_icon_thread = threading.Thread(target=self.tray_icon.run)
            self.tray_icon_thread.daemon = True
            self.tray_icon_thread.start()
    
    def show_window(self):
        """Show the window and bring it to front."""
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()
        self.window_visible = True
    
    def hide_window(self):
        """Hide the window to system tray if available, otherwise minimize."""
        if self.tray_icon:
            self.window.withdraw()
            self.window_visible = False
        else:
            self.window.iconify()
    
    def toggle_window(self):
        """Toggle window visibility."""
        if self.window_visible:
            self.hide_window()
        else:
            self.show_window()
    
    def on_closing(self):
        """Handle application exit."""
        if self.scheduled_update:
            self.window.after_cancel(self.scheduled_update)
        if self.spinner_thread and self.spinner_thread.is_alive():
            self.spinner_thread.stop()
        if self.tray_icon:
            self.tray_icon.stop()
        self.window.destroy()
    
    def check_connection_status(self):
        """Periodically checks mount status"""
        def check_status():
            try:
                # Check mount
                self.mount_status = os.path.ismount('/Volumes/data') if platform.system() == "Darwin" \
                                  else os.path.exists(r'\\fs.edu.ds.fhnw.ch\data')
                
                # Update status indicators
                self.mount_indicator.config(
                    text="🟢 Share Mounted" if self.mount_status else "🔴 Share Not Mounted"
                )
                
                # Enable/disable sync button based on status
                if self.mount_status:
                    self.sync_button.config(state=tk.NORMAL)
                else:
                    self.sync_button.config(state=tk.DISABLED)
                    
            except Exception as e:
                print(f"Error checking status: {str(e)}")
            
            # Schedule next check
            self.window.after(5000, check_status)
            
        # Start first check
        check_status()
    
    def setup_gui(self):
        # Create main container frame
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Title label
        self.title_label = ttk.Label(
            main_frame, text=WINDOW_TITLE, font=("Helvetica", 16, "bold")
        )
        self.title_label.pack(pady=(0, 10), anchor="w")
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Mount status indicator
        self.mount_indicator = ttk.Label(
            status_frame,
            text="🔴 Share Not Mounted",
            font=("Helvetica", 10)
        )
        self.mount_indicator.pack(side=tk.LEFT)

        # Progress frame
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Progress bar
        self.progress = ttk.Progressbar(
            progress_frame,
            orient="horizontal",
            length=400,
            mode="determinate"
        )
        self.progress.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))
        
        # Progress percentage label
        self.progress_label = ttk.Label(
            progress_frame,
            text="0%",
            font=("Helvetica", 10),
            width=4
        )
        self.progress_label.pack(side=tk.RIGHT)
        
        # Status label for spinner
        self.status_label = ttk.Label(
            main_frame, text="", font=("Helvetica", 10)
        )
        self.status_label.pack(pady=(0, 10), anchor="e")

        # Output frame
        output_frame = ttk.Frame(main_frame)
        output_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Output text
        self.output_text = tk.Text(
            output_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Courier New", 10),
            borderwidth=0,
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # Buttons frame at bottom
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        # Sync button
        self.sync_button = ttk.Button(
            button_frame,
            text=SYNC_BUTTON_TEXT,
            command=self.run_sync_script
        )
        self.sync_button.pack(side=tk.LEFT, padx=5, expand=True)

        # Clear button
        self.clear_button = ttk.Button(
            button_frame,
            text=CLEAR_BUTTON_TEXT,
            command=self.clear_output
        )
        self.clear_button.pack(side=tk.LEFT, padx=5, expand=True)

        # Theme toggle button
        self.theme_button = ttk.Button(
            button_frame,
            text="🌙",  # Moon emoji for dark theme
            command=self.toggle_theme,
            width=3
        )
        self.theme_button.pack(side=tk.LEFT, padx=5)

        # Settings button
        self.settings_button = ttk.Button(
            button_frame,
            text="Settings",
            command=self.open_settings
        )
        self.settings_button.pack(side=tk.LEFT, padx=5, expand=True)

    def run_sync_script(self):
        # Disable buttons immediately
        self.sync_button.config(state=tk.DISABLED)
        self.clear_button.config(state=tk.DISABLED)
        
        # Clear previous output
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)

        # Start the spinner
        self.spinner_thread = SpinnerThread(self.status_label)
        self.spinner_thread.start()

        def handle_output(process, output_queue):
            # Handle stdout in real-time with a separate thread for each stream
            def read_stream(stream, prefix=""):
                for line in iter(stream.readline, ''):
                    if line:
                        # Check for VPN login prompt
                        if "Press Enter after completing SSO login" in line:
                            # Show dialog to user
                            self.window.after(0, lambda: messagebox.showinfo(
                                "VPN Login Required",
                                "Please complete the SSO login in your browser and click OK to continue."
                            ))
                        output_queue.put(f"{prefix}{line}")
                        
            # Start threads for stdout and stderr
            stdout_thread = threading.Thread(
                target=read_stream, 
                args=(process.stdout, "")
            )
            stderr_thread = threading.Thread(
                target=read_stream, 
                args=(process.stderr, "Error: ")
            )
            
            stdout_thread.daemon = True
            stderr_thread.daemon = True
            
            stdout_thread.start()
            stderr_thread.start()
            
            # Wait for both streams to complete
            stdout_thread.join()
            stderr_thread.join()

        def start_process(output_queue):
            try:
                # Use platform-appropriate Python interpreter
                python_cmd = "python3" if platform.system() != "Windows" else "python"
                
                # Run with sudo if on macOS (needed for mount)
                if platform.system() == "Darwin":
                    process = subprocess.Popen(
                        ['sudo', python_cmd, "sync_fhnw.py"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE,  # Add stdin pipe for interaction
                        text=True,
                        bufsize=1,
                        universal_newlines=True
                    )
                else:
                    process = subprocess.Popen(
                        [python_cmd, "sync_fhnw.py"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE,  # Add stdin pipe for interaction
                        text=True,
                        bufsize=1,
                        universal_newlines=True
                    )
                handle_output(process, output_queue)
                process.wait()
            except Exception as e:
                output_queue.put(f"An error occurred: {str(e)}\n")
            finally:
                output_queue.put(None)

        thread = threading.Thread(target=start_process, args=(self.output_queue,))
        thread.daemon = True
        thread.start()
        self.schedule_update()

    def schedule_update(self):
        try:
            while True:
                try:
                    line = self.output_queue.get_nowait()
                    if line is None:  # End signal
                        if self.spinner_thread:
                            self.spinner_thread.stop()
                        self.sync_button.config(state=tk.NORMAL)
                        self.clear_button.config(state=tk.NORMAL)
                        self.reset_progress()
                        return
                        
                    # Handle progress updates
                    if line.startswith("PROGRESS:"):
                        try:
                            progress = int(line.split(":")[1].strip())
                            if 0 <= progress <= 100:
                                self.update_progress(progress)
                            continue
                        except (IndexError, ValueError):
                            logging.warning(f"Invalid progress update: {line}")
                            continue
                            
                    # Handle regular output
                    self.output_text.config(state=tk.NORMAL)
                    self.output_text.insert(tk.END, line)
                    self.output_text.see(tk.END)
                    self.output_text.config(state=tk.DISABLED)
                except queue.Empty:
                    break
        finally:
            # Schedule next update more frequently
            self.scheduled_update = self.window.after(50, self.schedule_update)

    def clear_output(self):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)

    def open_settings(self):
        ConfigDialog(self.window, self.config)

    def toggle_theme(self):
        """Toggle between dark and light themes"""
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        sv_ttk.set_theme(self.current_theme)
        # Update theme button icon
        self.theme_button.config(text="☀️" if self.current_theme == "light" else "🌙")
        # Save theme preference
        if self.config:
            self.config['DEFAULT']['theme'] = self.current_theme
            with open(CONFIG_FILE, 'w') as configfile:
                self.config.write(configfile)

    def update_progress(self, value):
        """Update the progress bar value"""
        self.progress['value'] = value
        self.progress_label.config(text=f"{value}%")
        self.window.update_idletasks()

    def reset_progress(self):
        """Reset the progress bar"""
        self.progress['value'] = 0
        self.progress_label.config(text="0%")
        self.window.update_idletasks()

    def run(self):
        # Load saved theme if exists
        if self.config and 'theme' in self.config['DEFAULT']:
            self.current_theme = self.config['DEFAULT']['theme']
            sv_ttk.set_theme(self.current_theme)
            self.theme_button.config(text="☀️" if self.current_theme == "light" else "🌙")
        self.window.mainloop()

if __name__ == "__main__":
    app = MainWindow()
    app.run()
