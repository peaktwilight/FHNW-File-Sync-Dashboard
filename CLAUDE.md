# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FHNW File Sync Dashboard is a Python GUI application that automates syncing course materials from FHNW network drives to local machines. It features a modern Tkinter interface with Sun Valley theme, system tray integration, and cross-platform file synchronization.

Version 2.0 introduces a modular architecture with profile management, allowing users to create multiple sync configurations with advanced filtering and sync options.

## Key Commands

### Installation
```bash
pip install -r requirements.txt
```

### Running the Application
- New modular GUI: `python main.py`
- Legacy GUI mode: `python gui.py`
- CLI mode: `python sync_fhnw.py`
- CLI with skip checks: `python sync_fhnw.py --skip-checks`

### Development Commands
- No linting configuration exists - consider using `ruff` or `flake8`
- No test framework configured - project currently lacks tests
- No build/packaging configuration

## Architecture

### Version 2.0 - Modular Architecture

The new modular structure in `src/` provides better separation of concerns:

1. **src/core/sync_engine.py** - Core synchronization engine
   - Platform-agnostic sync operations
   - Support for multiple sync modes (Mirror, Update, Additive)
   - Dry-run capability for previewing changes
   - Progress reporting with cancellation support
   - File filtering and bandwidth limiting

2. **src/models/sync_profile.py** - Data models
   - SyncProfile: Complete sync configuration with validation
   - SyncLocation: Source/destination abstraction
   - SyncRule: Advanced filtering options
   - SyncMode/SyncDirection enums

3. **src/config/profile_manager.py** - Configuration management
   - Profile CRUD operations
   - Import/export functionality
   - Legacy config.txt migration
   - Persistent storage in ~/.fhnw_sync/

4. **src/ui/main_window.py** - Modern GUI application
   - Profile-based interface with sidebar navigation
   - Real-time sync monitoring
   - Theme switching (dark/light)
   - Keyboard shortcuts and menus

5. **src/ui/profile_editor.py** - Profile editing dialog
   - Intuitive form-based editing
   - Folder browsing with validation
   - Advanced options in tabbed interface

6. **src/utils/logger.py** - Logging utilities
   - Colored console output
   - Per-sync log files
   - Structured sync logging with metrics

### Legacy Components (v1.0)

1. **gui.py** - Original GUI application (692 lines)
   - Single-profile configuration
   - Basic sync functionality
   - System tray integration

2. **sync_fhnw.py** - Original sync engine (373 lines)
   - FHNW-specific features (VPN, SMB mounts)
   - Basic rsync/robocopy wrapper

3. **config.txt** - Legacy configuration format

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