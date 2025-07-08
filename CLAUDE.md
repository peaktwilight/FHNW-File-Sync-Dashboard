# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FHNW File Sync Dashboard is a Python GUI application that automates syncing course materials from FHNW network drives to local machines. It features a modern Tkinter interface with Sun Valley theme, system tray integration, and cross-platform file synchronization.

## Key Commands

### Installation
```bash
pip install -r requirements.txt
```

### Running the Application
- GUI mode: `python gui.py`
- CLI mode: `python sync_fhnw.py`
- CLI with skip checks: `python sync_fhnw.py --skip-checks`

### Development Commands
- No linting configuration exists - consider using `ruff` or `flake8`
- No test framework configured - project currently lacks tests
- No build/packaging configuration

## Architecture

### Core Components

1. **gui.py** - Main GUI application (692 lines)
   - Modern Tkinter interface with Sun Valley theme
   - System tray integration with pystray
   - Asynchronous sync operation handling
   - Settings dialog for configuration management
   - Real-time progress monitoring

2. **sync_fhnw.py** - Sync engine (373 lines)
   - Cross-platform sync using `rsync` (Unix) or `robocopy` (Windows)
   - VPN connection handling via openconnect
   - SMB share mounting capabilities
   - Git repository synchronization
   - Retry mechanism for failed operations
   - Progress reporting to GUI via callback

3. **config.txt** - User configuration
   - Stores destination directory, source paths, feature toggles
   - Managed through GUI settings dialog
   - ConfigParser format with DEFAULT section

### Key Integration Points

- **GUI-Sync Communication**: The GUI calls sync functions with a progress callback that updates the UI in real-time
- **Credential Storage**: Uses `keyring` library for secure credential management
- **Platform Detection**: Automatic selection of sync tool based on OS (rsync vs robocopy)
- **Theme System**: Sun Valley theme bundled in `sv_ttk/` directory

### Important Implementation Details

- The sync process runs in a separate thread to keep the GUI responsive
- Progress updates use a queue to communicate between threads safely
- VPN/mount operations require sudo on macOS and use browser-based SSO
- Git operations are optional and controlled by config settings
- The application supports retry logic for handling transient network issues

## Platform-Specific Notes

- **macOS**: Primary platform with full VPN/mount support
- **Windows**: Basic sync functionality with robocopy
- **Linux**: Limited support, uses rsync like macOS

## Security Considerations

- Never store credentials in config.txt - use keyring
- VPN credentials use browser-based SSO authentication
- SMB mount requires system privileges (sudo)