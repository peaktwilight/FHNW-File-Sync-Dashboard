# FHNW File Sync Dashboard v2.0

A modern, modular file synchronization tool with profile management, designed for FHNW students and general use.

## New Features in v2.0

### 🎯 Profile Management
- **Multiple Sync Profiles**: Create and manage unlimited sync configurations
- **Import/Export Profiles**: Share configurations with others
- **Default Profile**: Set a default profile for quick access

### 📁 Enhanced Sync Options
- **Flexible Source/Destination**: Pick any folders with browse dialog
- **Sync Modes**:
  - **Update**: Only sync newer files
  - **Mirror**: Make destination exactly match source
  - **Additive**: Only add new files, never delete
- **Sync Directions**:
  - Remote → Local
  - Local → Remote
  - Bidirectional

### 🎨 Modern User Interface
- **Clean, Intuitive Design**: Easy-to-use interface with profile sidebar
- **Dark/Light Theme**: Toggle between themes
- **Real-time Progress**: Visual progress bars and detailed logs
- **Sync Preview**: See what will be synced before starting

### ⚙️ Advanced Features
- **File Filters**: Include/exclude patterns, file size limits, extensions
- **Bandwidth Limiting**: Control sync speed
- **Git Integration**: Auto pull/commit for repositories
- **Dry Run Mode**: Test sync without making changes
- **Sync History**: Track all sync operations with detailed logs

### 🌐 FHNW Network Integration
- **VPN Status Monitoring**: Real-time FHNW VPN connection status
- **Automatic SMB Mounting**: Auto-mount FHNW network drives
- **Connection Management**: Connect/disconnect VPN and mounts from UI
- **Credential Storage**: Secure keychain storage for login credentials
- **Auto-Connect**: Automatically connect when syncing if enabled

### 🔧 Technical Improvements
- **Modular Architecture**: Clean separation of concerns
- **Cross-platform**: Works on Windows, macOS, and Linux
- **Robust Error Handling**: Retry mechanisms and clear error messages
- **Extensible Design**: Easy to add new features

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/peaktwilight/FHNW-File-Sync-Dashboard.git
   cd FHNW-File-Sync-Dashboard
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

## Quick Start

1. **Create a Profile**:
   - Click "New" in the profiles sidebar
   - Enter a name and description
   - Select source and destination folders
   - Choose sync mode and options

2. **Configure Network** (for FHNW users):
   - Go to Tools → Network Settings
   - Enter your FHNW credentials
   - Test VPN and SMB connections

3. **Configure Sync**:
   - Set sync direction (Remote→Local, Local→Remote, or Bidirectional)
   - Add file filters if needed
   - Configure advanced options (permissions, bandwidth, etc.)
   - Use "FHNW Drive" button for easy network drive selection

4. **Run Sync**:
   - Select your profile
   - Check connection status in the sidebar
   - Enable "Auto-connect" for automatic VPN/SMB setup
   - Click "Preview" to see what will be synced
   - Click "Sync Now" to start

## Profile System

### Creating Profiles
Each profile contains:
- **Name & Description**: Identify your sync configurations
- **Source & Destination**: Any accessible folders
- **Sync Settings**: Mode, direction, and filters
- **Advanced Options**: Permissions, bandwidth, retry settings

### Managing Profiles
- **Edit**: Modify existing profiles
- **Duplicate**: Create copies with different settings
- **Import/Export**: Share profiles as JSON files
- **Delete**: Remove unused profiles

## Sync Modes Explained

### Update Mode
- Only copies files that are newer in the source
- Preserves existing files in destination
- Best for: Regular backups

### Mirror Mode
- Makes destination exactly match source
- Deletes files not in source
- Best for: Exact replicas

### Additive Mode
- Only adds new files to destination
- Never deletes anything
- Best for: Archiving

## Advanced Features

### File Filtering
- **Include Patterns**: Only sync matching files (e.g., `*.pdf`, `project_*`)
- **Exclude Patterns**: Skip matching files (e.g., `*.tmp`, `.DS_Store`)
- **Hidden Files**: Option to exclude hidden files
- **Size Limits**: Set minimum/maximum file sizes

### Git Integration
- Automatically pull before sync
- Option to commit after sync
- Useful for code repositories

### Bandwidth Control
- Limit sync speed in KB/s
- Useful for slow connections
- Leave empty for unlimited speed

## Keyboard Shortcuts
- `Ctrl+N`: New profile
- `Ctrl+E`: Edit profile
- `Delete`: Delete profile
- `Ctrl+Q`: Quit application

## Configuration

Settings are stored in `~/.fhnw_sync/`:
- `config.json`: General application settings
- `profiles/`: Individual profile configurations
- `logs/`: Sync operation logs

## Troubleshooting

### Common Issues

1. **"Source path does not exist"**
   - Ensure the source folder is accessible
   - Check network drive is mounted

2. **"Permission denied"**
   - Run with appropriate permissions
   - Check file/folder permissions

3. **Sync seems slow**
   - Check bandwidth limit settings
   - Verify network connection

### Logs
View detailed logs in `~/.fhnw_sync/logs/` or via View → View Logs

## Development

### Project Structure
```
FHNW_SYNC_TOOL/
├── src/
│   ├── core/           # Sync engine
│   ├── models/         # Data models
│   ├── config/         # Configuration management
│   ├── ui/             # User interface
│   └── utils/          # Utilities
├── main.py             # Entry point
└── requirements.txt    # Dependencies
```

### Adding Features
The modular design makes it easy to extend:
1. Add new sync modes in `sync_engine.py`
2. Create new UI dialogs in `ui/`
3. Extend profiles in `models/sync_profile.py`

## License
MIT License - See LICENSE file for details

## Changelog

### v2.0 (2024)
- Complete rewrite with modular architecture
- Profile management system
- Enhanced UI with themes
- Advanced filtering options
- Cross-platform improvements

### v1.0 (2023)
- Initial release
- Basic sync functionality
- Simple configuration file