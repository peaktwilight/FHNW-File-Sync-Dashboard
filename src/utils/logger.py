import logging
import os
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for terminal output"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Set up logging configuration"""
    
    # Create logs directory if needed
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler()
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)


class SyncLogger:
    """Specialized logger for sync operations with structured logging"""
    
    def __init__(self, profile_id: str, log_dir: str = None):
        self.profile_id = profile_id
        self.logger = get_logger(f"sync.{profile_id}")
        
        # Set up sync-specific log file
        if log_dir is None:
            log_dir = os.path.expanduser("~/.fhnw_sync/logs")
        
        os.makedirs(log_dir, exist_ok=True)
        
        # Create a file handler for this sync session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"sync_{profile_id}_{timestamp}.log")
        
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        self.log_file = log_file
        self.start_time = datetime.now()
        self.files_synced = 0
        self.bytes_transferred = 0
        self.errors = []
    
    def log_start(self, source: str, destination: str):
        """Log sync start"""
        self.logger.info(f"Starting sync: {source} -> {destination}")
        self.logger.info(f"Profile ID: {self.profile_id}")
    
    def log_progress(self, message: str, percent: float = -1):
        """Log progress update"""
        if percent >= 0:
            self.logger.debug(f"Progress: {percent:.1f}% - {message}")
        else:
            self.logger.debug(f"Progress: {message}")
    
    def log_file_synced(self, file_path: str, size: int = 0):
        """Log individual file sync"""
        self.files_synced += 1
        self.bytes_transferred += size
        self.logger.debug(f"Synced: {file_path} ({size} bytes)")
    
    def log_error(self, error: str):
        """Log error"""
        self.errors.append(error)
        self.logger.error(error)
    
    def log_complete(self, success: bool, message: str = ""):
        """Log sync completion"""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if success:
            self.logger.info(f"Sync completed successfully in {duration:.1f} seconds")
        else:
            self.logger.error(f"Sync failed after {duration:.1f} seconds: {message}")
        
        self.logger.info(f"Files synced: {self.files_synced}")
        self.logger.info(f"Data transferred: {self._format_bytes(self.bytes_transferred)}")
        
        if self.errors:
            self.logger.warning(f"Errors encountered: {len(self.errors)}")
            for error in self.errors:
                self.logger.warning(f"  - {error}")
    
    def get_summary(self) -> dict:
        """Get sync summary"""
        return {
            'profile_id': self.profile_id,
            'start_time': self.start_time,
            'duration': (datetime.now() - self.start_time).total_seconds(),
            'files_synced': self.files_synced,
            'bytes_transferred': self.bytes_transferred,
            'errors': self.errors,
            'log_file': self.log_file
        }
    
    @staticmethod
    def _format_bytes(bytes_count: int) -> str:
        """Format bytes to human readable string"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_count < 1024.0:
                return f"{bytes_count:.2f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.2f} PB"