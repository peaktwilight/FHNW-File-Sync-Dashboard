import tkinter as tk
from tkinter import ttk
import subprocess
import threading
import queue
import sv_ttk
import itertools
import time
from tkinter import messagebox
import json
import configparser
import os

# --- Constants ---
WINDOW_TITLE = "FHNW File Sync Dashboard BETA v0.2"
SYNC_BUTTON_TEXT = "Sync Now"
CLEAR_BUTTON_TEXT = "Clear Output"
SPINNER_CHARS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
CONFIG_FILE = "config.txt"

def load_config():
    """Loads the configuration from config.txt."""
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        messagebox.error("Error", "config.txt not found. Please create it and try again.")
        return None
    config.read(CONFIG_FILE)
    return config

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
        
        # Helper function for consistent label styling
        def create_label(text):
            return ttk.Label(scrollable_frame, text=text, font=("Helvetica", 11))
        
        # Helper function for consistent entry styling
        def create_entry():
            return ttk.Entry(scrollable_frame, width=80, font=("Courier", 10))
        
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
        self.settings['source_paths'] = tk.Text(scrollable_frame, height=6, width=80, font=("Courier", 10))
        source_paths = self.config['DEFAULT'].get('source_paths', '')
        # Format paths one per line
        formatted_paths = '\n'.join(path.strip() for path in source_paths.split(','))
        self.settings['source_paths'].insert('1.0', formatted_paths)
        self.settings['source_paths'].grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
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
        
        # Create a frame for checkboxes
        checkbox_frame = ttk.Frame(scrollable_frame)
        checkbox_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
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
        self.window.geometry("500x400")
        
        # Set the Sun Valley Theme
        sv_ttk.set_theme("dark")
        
        self.config = load_config()
        self.output_queue = queue.Queue()
        self.scheduled_update = None
        self.spinner_thread = None
        
        # Create GUI elements
        self.setup_gui()
        
        # Set up the window close handler
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_gui(self):
        # Title label
        self.title_label = ttk.Label(
            self.window, text=WINDOW_TITLE, font=("Helvetica", 16, "bold")
        )
        self.title_label.grid(row=0, column=0, columnspan=2, pady=(15, 5), padx=10, sticky="w")

        # Status label for spinner
        self.status_label = ttk.Label(
            self.window, text="", font=("Helvetica", 10)
        )
        self.status_label.grid(row=0, column=1, pady=(15, 5), padx=10, sticky="e")

        # Output frame
        output_frame = ttk.Frame(self.window, padding=(10, 5))
        output_frame.grid(row=1, column=0, columnspan=2, pady=5, padx=10, sticky="nsew")

        # Output text
        self.output_text = tk.Text(
            output_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            height=10,
            font=("Courier New", 10),
            borderwidth=0,
        )
        self.output_text.pack(expand=True, fill="both")

        # Buttons frame
        button_frame = ttk.Frame(self.window)
        button_frame.grid(row=2, column=0, columnspan=3, pady=5, padx=10, sticky="ew")

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

        # Settings button
        self.settings_button = ttk.Button(
            button_frame,
            text="Settings",
            command=self.open_settings
        )
        self.settings_button.pack(side=tk.LEFT, padx=5, expand=True)

        # Configure grid weights
        self.window.columnconfigure(0, weight=1)
        self.window.columnconfigure(1, weight=1)
        self.window.rowconfigure(1, weight=1)

    def run_sync_script(self):
        # Disable both buttons immediately
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
                process = subprocess.Popen(
                    ["python3", "sync_fhnw.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
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
                        return
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

    def on_closing(self):
        if self.scheduled_update:
            self.window.after_cancel(self.scheduled_update)
        if self.spinner_thread and self.spinner_thread.is_alive():
            self.spinner_thread.stop()
        self.window.destroy()

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = MainWindow()
    app.run()
