# FHNW (Fachhochschule Nordwestschweiz) Course Material Sync Script

A comprehensive solution for syncing course materials from FHNW (Fachhochschule Nordwestschweiz - University of Applied Sciences and Arts Northwestern Switzerland) network drive to your local machine. This tool is specifically designed for FHNW students to efficiently manage their course materials. The repository includes both Python (`sync_fhnw.py`) and Bash (`sync_fhnw.sh`) implementations.

## Prerequisites

- Python 3.x (for Python version)
- Bash shell (for Shell version)
- `rsync` installed
- `git` installed
- Network drive mounted at `/Volumes/data` (SMB share: `smb://fs.edu.ds.fhnw.ch/data`)

## Configuration

### Python Version (`sync_fhnw.py`)

Configuration is managed through `config.txt`:

```ini
[DEFAULT]
destination = /Users/your/local/path
source_paths = /path/to/source1, /path/to/source2
oop_repo_path = /path/to/oopI2/repo
swegl_script_path = /path/to/swegl/script
log_level = INFO
```

### Shell Version (`sync_fhnw.sh`)

Configuration is directly in the script:

```bash
DESTINATION="/Users/your/local/path"
SOURCE_PATHS=(
    "/Volumes/data/path/to/sweGL"
    "/Volumes/data/path/to/oopI2"
    # Add more paths as needed
)
```

## Features

Both scripts provide:

1. **Robust Syncing**
   - Uses `rsync` for efficient file transfer
   - Implements retry mechanism (up to 3 attempts)
   - Handles vanishing files gracefully
   - Preserves file attributes

2. **Git Integration**
   - Automatic `git pull` for specified repositories
   - Handles repository state verification
   - Error handling for git operations

3. **Error Handling**
   - Comprehensive error checking
   - Detailed logging
   - Prerequisites verification
   - Path existence validation

## Usage

### Python Version
```bash
python sync_fhnw.py
```

The Python version offers:
- Configurable logging levels
- External configuration file
- More detailed error reporting
- Modular code structure

### Shell Version
```bash
./sync_fhnw.sh
```

The Shell version provides:
- Faster execution
- No Python dependency
- Built-in timestamp logging
- Simplified configuration

## Implementation Details

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
