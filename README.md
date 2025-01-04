# FHNW (Fachhochschule Nordwestschweiz) Course Material Sync Script

A comprehensive solution for syncing course materials from FHNW (Fachhochschule Nordwestschweiz - University of Applied Sciences and Arts Northwestern Switzerland) network drive to your local machine. This tool is specifically designed for FHNW students to efficiently manage their course materials. The primary script is written in Python (`sync_fhnw.py`). The Bash script (`sync_fhnw.sh`) is still available but may be deprecated in the future in favor of the more flexible Python version.

## Prerequisites

- Python 3.x
- `rsync` installed
- `git` installed
- Network drive mounted at `/Volumes/data` (SMB share: `smb://fs.edu.ds.fhnw.ch/data`)
- Python packages (for GUI version):
  - `tkinter`
  - `sv_ttk` (Sun Valley theme for modern UI - already integrated to this repo dw!)

## Configuration

The script's behavior is configured through the `config.txt` file.

```ini
[DEFAULT]
destination = /Users/your/local/path
source_paths = /path/to/source1, /path/to/source2
oop_repo_path = /path/to/oopI2/repo
swegl_script_path = /path/to/swegl/script
enable_git_pull = True
enable_swegl_script = True
log_level = INFO
max_rsync_retries = 3
```

- `destination`: The local directory where the course materials will be synced.
- `source_paths`: A comma-separated list of network paths to the course materials.
- `oop_repo_path`: The local path to the `oopI2` Git repository. If provided, the script will perform a `git pull`.
- `swegl_script_path`: The local path to the `fetch_from_origin.sh` script for SWEGL. If provided, the script will execute it.
- `enable_git_pull`: Set to `True` to enable or disable automatic `git pull` for the `oop_repo_path`. Defaults to `True`.
- `enable_swegl_script`: Set to `True` to enable or disable the execution of the SWEGL script. Defaults to `True`.
- `log_level`: Defines the verbosity of the logs (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).
- `max_rsync_retries`: The number of times `rsync` will retry on failure (specifically exit code 24).

It is recommended to use the `sync_fhnw.py` script as it offers more flexibility through this configuration file.

## Features

1. **User Interface Options**
   - Modern GUI with Sun Valley theme
   - Real-time sync progress monitoring
   - Command-line interface for automation
   - Visual status indicators

2. **Robust Syncing**
   - Uses `rsync` for efficient file transfer
   - Implements retry mechanism (up to 3 attempts)
   - Handles vanishing files gracefully
   - Preserves file attributes

3. **Git Integration**
   - Automatic `git pull` for specified repositories (configurable in Python version)
   - Handles repository state verification
   - Error handling for git operations

4. **Error Handling**
   - Comprehensive error checking
   - Detailed logging (configurable in Python version)
   - Prerequisites verification
   - Path existence validation

## Usage

### GUI Version (Recommended)

Launch the graphical interface by running:

```bash
python gui.py
```

The GUI provides:
- Simple one-click sync operation
- Real-time sync progress display
- Clear output functionality
- Modern dark theme interface
- Visual sync status indicator

### Command Line Version

To run the script without GUI:

```bash
python sync_fhnw.py
```

The script reads the configuration from `config.txt`. Ensure this file is correctly configured before running the script.

The Python version offers:
- Configurable logging levels via `config.txt`.
- Ability to enable/disable git pull and script execution via `config.txt`.
- External configuration file for all settings.
- More detailed error reporting.
- Modular and maintainable code structure.

The shell script (`sync_fhnw.sh`) is still available for basic syncing but its configuration is embedded within the script and it lacks the flexibility of the Python version.

## Implementation Details

### GUI Version (`gui.py`)

Key features:
- Modern dark theme interface using `sv_ttk`
- Real-time sync progress display
- Async operation handling
- Visual spinner during sync
- Output text display with scroll capability
- Clear output functionality

### Python Version (`sync_fhnw.py`)

Key functions:

- `check_prerequisites()`: Verifies required tools
- `load_config()`: Loads configuration from file
- `retry_rsync()`: Handles file synchronization with retries
- `git_pull()`: Manages Git repository updates
- `execute_script()`: Runs additional scripts (e.g., for sweGL)
- `setup_logging()`: Configures logging system

### Shell Version (`sync_fhnw.sh`)

Key components:

- Strict mode with `set -euo pipefail`
- Retry mechanism for rsync operations
- Git repository handling
- Timestamp-based logging
- Array-based source path configuration

## Error Handling

Both versions handle common scenarios:
- Missing prerequisites
- Network drive not mounted
- File permission issues
- Git repository errors
- Vanishing files during sync
- Script execution failures

## Note

Course material folders are ignored in Git tracking - this repository only contains the sync scripts and their configuration. Choose the version (Python or Shell) that best fits your needs and system setup.

## Screenshots

The GUI version provides a modern interface with:
- Dark theme support
- Progress indicator
- Clear, readable output display
- Simple two-button interface
