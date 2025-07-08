# FHNW File Sync Dashboard (Currently in BETA)

## Screenshots
![Sync Settings Interface](./screenshots/sync_settings_screenshot_v0.5.png)

A GUI application for automating the annoying task of syncing course materials from FHNW (Fachhochschule Nordwestschweiz - University of Applied Sciences and Arts Northwestern Switzerland) network drive to your local machine. This tool is specifically designed for FHNW students to efficiently manage their course materials.

## Features

1. **Modern User Interface**
   - Clean, intuitive dashboard design
   - Dark theme with Sun Valley styling
   - Real-time sync progress monitoring
   - Visual status indicators and spinner
   - Settings management interface

2. **Sync Capabilities**
   - One-click sync operation
   - Uses `rsync` (macOS/Linux) or `robocopy` (Windows) for efficient file transfer
   - Implements retry mechanism
   - Handles vanishing files gracefully
   - Preserves file attributes
   - Cross-platform support with automatic tool selection

3. **Git Integration**
   - Automatic `git pull` for specified repositories
   - Configurable through settings
   - Error handling for git operations

4. **SWEGL Integration**
   - Optional SWEGL script execution
   - Configurable through settings

## Prerequisites

- Python 3.x
- `rsync` installed (should be on your mac by default)
- `git` installed
- Network drive mounted at `/Volumes/data` (SMB share: `smb://fs.edu.ds.fhnw.ch/data` once you're connected to cisco vpn at vpn.fhnw.ch)
- Python packages:
  - `tkinter` (usually comes with Python)
  - `sv_ttk` (Sun Valley theme - included in repo)

## Installation

1. Clone this repository
2. Ensure all prerequisites are installed
3. Create a `config.txt` file (see Configuration section)
4. Run `python gui.py`

## Configuration

The dashboard uses a `config.txt` file for settings:

```ini
[DEFAULT]
destination = /Users/your/local/path
source_paths = /path/to/source1,
              /path/to/source2
oop_repo_path = /path/to/oopI2/repo
swegl_script_path = /path/to/swegl/script
enable_git_pull = True
enable_swegl_script = True
log_level = INFO
max_rsync_retries = 3
```

All settings can be managed through the GUI's Settings dialog:

- **Destination Directory**: Where files will be synced to
- **Source Paths**: List of paths to sync (one per line in settings)
- **OOP Repository Path**: Path to OOP Git repository
- **SWEGL Script Path**: Path to SWEGL script
- **Enable Git Pull**: Toggle automatic git pull
- **Enable SWEGL Script**: Toggle SWEGL script execution
- **Log Level**: Set logging verbosity
- **Max Retries**: Number of sync retry attempts

## Usage

### GUI Dashboard (Recommended)

1. Launch the dashboard:
```bash
python gui.py
```

2. Use the interface:
   - Click "Sync Now" to start synchronization
   - Use "Clear Output" to reset the log display
   - Access "Settings" to configure the application
   - Monitor progress through the status indicator and output log

### Command Line (Alternative)

For automation or server environments:
```bash
python sync_fhnw.py
```

## Error Handling

The dashboard handles various scenarios:
- Missing prerequisites
- Network drive not mounted
- File permission issues
- Git repository errors
- Vanishing files during sync
- Script execution failures

All errors are displayed in the output log with appropriate status indicators.

## Development

The application consists of three main components:

1. **GUI Dashboard** (`gui.py`)
   - Modern interface using `tkinter` and Sun Valley theme
   - Real-time sync progress display
   - Settings management
   - Async operation handling

2. **Sync Engine** (`sync_fhnw.py`)
   - Core synchronization logic
   - File system operations
   - Git integration
   - Error handling

3. **Configuration** (`config.txt`)
   - External settings storage
   - User-configurable options
   - Persistent preferences

## Note

Course material folders are ignored in Git tracking - this repository only contains the application code and configuration files.
