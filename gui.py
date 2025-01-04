import tkinter as tk
from tkinter import ttk
import subprocess
import threading
import queue
import sv_ttk
import itertools
import time

# --- Constants ---
WINDOW_TITLE = "FHNW File Sync Dashboard BETA v0.2"
SYNC_BUTTON_TEXT = "Sync Now"
CLEAR_BUTTON_TEXT = "Clear Output"
SPINNER_CHARS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
# --- End Constants ---

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

def run_sync_script(output_queue):
    # Disable both buttons immediately
    sync_button.config(state=tk.DISABLED)
    clear_button.config(state=tk.DISABLED)
    
    # Clear previous output
    output_text.config(state=tk.NORMAL)
    output_text.delete(1.0, tk.END)
    output_text.config(state=tk.DISABLED)

    # Start the spinner
    global spinner_thread
    spinner_thread = SpinnerThread(status_label)
    spinner_thread.start()

    def handle_output(process, output_queue):
        for line in iter(process.stdout.readline, ""):
            output_queue.put(line)
        for line in iter(process.stderr.readline, ""):
            output_queue.put(f"Error: {line}")

    def start_process(output_queue):
        try:
            process = subprocess.Popen(
                ["python3", "sync_fhnw.py"],
                cwd=".",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            handle_output(process, output_queue)
            process.wait()  # Wait for the process to complete

        except FileNotFoundError:
            output_queue.put("Error: sync_fhnw.py not found.\n")
        except subprocess.CalledProcessError as e:
            output_queue.put(f"Error: sync_fhnw.py exited with code {e.returncode}\n")
        except PermissionError as e:
            output_queue.put(f"Error: Permission denied - {e}\n")
        except Exception as e:
            output_queue.put(f"An unexpected error occurred: {e}\n")
        finally:
            output_queue.put(None)  # Signal that the process is done

    thread = threading.Thread(target=start_process, args=(output_queue,))
    thread.start()

def update_output_text(output_queue):
    try:
        while True:
            line = output_queue.get(block=False)
            if line is None:  # Check for the end signal
                # Stop the spinner and enable buttons
                if 'spinner_thread' in globals():
                    spinner_thread.stop()
                sync_button.config(state=tk.NORMAL)
                clear_button.config(state=tk.NORMAL)
                break
            output_text.config(state=tk.NORMAL)
            output_text.insert(tk.END, line)
            output_text.see(tk.END)
            output_text.config(state=tk.DISABLED)
    except queue.Empty:
        window.after(100, update_output_text, output_queue)  # Schedule the next update

def clear_output():
    output_text.config(state=tk.NORMAL)
    output_text.delete(1.0, tk.END)
    output_text.config(state=tk.DISABLED)

# --- GUI Setup ---
window = tk.Tk()
window.title(WINDOW_TITLE)
window.geometry("500x400")  # Adjusted size

# --- Set the Sun Valley Theme ---
sv_ttk.set_theme("dark")

# --- Use the ttk Style ---
style = ttk.Style(window)

# Title label
title_label = ttk.Label(
    window, text=WINDOW_TITLE, font=("Helvetica", 16, "bold")
)
title_label.grid(row=0, column=0, columnspan=2, pady=(15, 5), padx=10, sticky="w")

# Status label for spinner
status_label = ttk.Label(
    window, text="", font=("Helvetica", 10)
)
status_label.grid(row=0, column=1, pady=(15, 5), padx=10, sticky="e")

# Output frame
output_frame = ttk.Frame(window, padding=(10, 5))
output_frame.grid(row=1, column=0, columnspan=2, pady=5, padx=10, sticky="nsew")

# Create the queue
output_queue = queue.Queue()

# Sync button
sync_button = ttk.Button(
    window,
    text=SYNC_BUTTON_TEXT,
    command=lambda: run_sync_script(output_queue)
)
sync_button.grid(row=2, column=0, pady=5, padx=10, sticky="ew")

# Clear button
clear_button = ttk.Button(
    window, text=CLEAR_BUTTON_TEXT, command=clear_output
)
clear_button.grid(row=2, column=1, pady=5, padx=10, sticky="ew")

# Output text (within the frame)
output_text = tk.Text(
    output_frame,
    wrap=tk.WORD,
    state=tk.DISABLED,
    height=10,
    font=("Courier New", 10),
    borderwidth=0,
)
output_text.pack(expand=True, fill="both")

# Configure grid weights to allow resizing
window.columnconfigure(0, weight=1)
window.columnconfigure(1, weight=1)
window.rowconfigure(1, weight=1)

# Start the periodic update of the text widget
window.after(100, update_output_text, output_queue)

window.mainloop()
# --- End GUI Setup ---
