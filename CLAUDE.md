# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FHNW File Sync Dashboard v2.0 is a modern Python GUI application with modular architecture that automates file synchronization. It features profile management, FHNW network integration, and a clean Tkinter interface with Sun Valley theme.

Key improvements in v2.0:
- Complete modular rewrite with separation of concerns
- Multiple sync profile management
- FHNW VPN and SMB network integration
- Advanced filtering and sync options
- Modern UI with dark/light themes

## Key Commands

### Installation
```bash
pip install -r requirements.txt
```

### Running the Application
- Main application: `python main.py`

### Development Commands
- No linting configuration exists - consider using `ruff` or `flake8`
- No test framework configured - project currently lacks tests
- No build/packaging configuration

## Architecture

### Version 2.0 - Modular Architecture

The new modular structure in `src/` provides better separation of concerns:

1. **src/core/sync_engine.py** - Core synchronization engine
   - Platform-agnostic sync operations
   - Support for multiple sync modes (Mirror, Update)
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

### Legacy Support

The legacy v1.0 components (gui.py, sync_fhnw.py, config.txt) have been removed in favor of the new modular architecture. The profile manager includes automatic migration from old config.txt files to the new profile system.

### Key Integration Points

- **Profile-Based Architecture**: All sync operations are based on configurable profiles
- **Network Integration**: Automatic VPN and SMB connection management for FHNW
- **GUI-Sync Communication**: Threaded sync operations with real-time progress callbacks
- **Credential Storage**: Secure keychain storage using `keyring` library
- **Theme System**: Sun Valley theme bundled in `sv_ttk/` directory

### Important Implementation Details

- **Thread Safety**: Sync operations run in separate threads with queue-based communication
- **Network Management**: Automatic detection and connection to FHNW VPN/SMB resources
- **Profile Storage**: JSON-based profile storage in `~/.fhnw_sync/profiles/`
- **Migration Support**: Automatic migration from legacy config.txt format
- **Cross-Platform**: Platform-specific sync tools (rsync/robocopy) selected automatically
- **Error Handling**: Comprehensive retry logic and user-friendly error messages

## Platform-Specific Notes

- **macOS**: Primary platform with full VPN/mount support
- **Windows**: Basic sync functionality with robocopy
- **Linux**: Limited support, uses rsync like macOS

## Security Considerations

- Never store credentials in config.txt - use keyring
- VPN credentials use browser-based SSO authentication
- SMB mount requires system privileges (sudo)