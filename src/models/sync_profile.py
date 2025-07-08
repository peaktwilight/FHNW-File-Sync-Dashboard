from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
import json
import os
from datetime import datetime


class SyncDirection(Enum):
    LOCAL_TO_REMOTE = "local_to_remote"
    REMOTE_TO_LOCAL = "remote_to_local"
    BIDIRECTIONAL = "bidirectional"


class SyncMode(Enum):
    MIRROR = "mirror"  # Exact copy, delete extra files
    UPDATE = "update"  # Only update newer files
    ADDITIVE = "additive"  # Only add new files, never delete


@dataclass
class SyncRule:
    """Defines rules for file filtering during sync"""
    include_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    exclude_hidden: bool = True
    min_file_size: Optional[int] = None  # bytes
    max_file_size: Optional[int] = None  # bytes
    file_extensions: List[str] = field(default_factory=list)  # e.g., ['.pdf', '.docx']
    
    def to_dict(self) -> Dict:
        return {
            'include_patterns': self.include_patterns,
            'exclude_patterns': self.exclude_patterns,
            'exclude_hidden': self.exclude_hidden,
            'min_file_size': self.min_file_size,
            'max_file_size': self.max_file_size,
            'file_extensions': self.file_extensions
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SyncRule':
        return cls(**data)


@dataclass
class SyncLocation:
    """Represents a source or destination location"""
    path: str
    name: str
    is_remote: bool = False
    requires_auth: bool = False
    mount_point: Optional[str] = None  # For network drives
    
    def to_dict(self) -> Dict:
        return {
            'path': self.path,
            'name': self.name,
            'is_remote': self.is_remote,
            'requires_auth': self.requires_auth,
            'mount_point': self.mount_point
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SyncLocation':
        return cls(**data)


@dataclass
class SyncProfile:
    """A complete sync configuration profile"""
    id: str
    name: str
    description: str = ""
    source: SyncLocation = None
    destination: SyncLocation = None
    sync_mode: SyncMode = SyncMode.UPDATE
    sync_direction: SyncDirection = SyncDirection.REMOTE_TO_LOCAL
    rules: SyncRule = field(default_factory=SyncRule)
    enabled: bool = True
    schedule: Optional[str] = None  # cron expression
    last_sync: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Advanced options
    preserve_permissions: bool = True
    preserve_timestamps: bool = True
    follow_symlinks: bool = False
    retry_count: int = 3
    bandwidth_limit: Optional[int] = None  # KB/s
    
    # Git integration
    is_git_repo: bool = False
    auto_commit: bool = False
    auto_pull: bool = True
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'source': self.source.to_dict() if self.source else None,
            'destination': self.destination.to_dict() if self.destination else None,
            'sync_mode': self.sync_mode.value,
            'sync_direction': self.sync_direction.value,
            'rules': self.rules.to_dict(),
            'enabled': self.enabled,
            'schedule': self.schedule,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'preserve_permissions': self.preserve_permissions,
            'preserve_timestamps': self.preserve_timestamps,
            'follow_symlinks': self.follow_symlinks,
            'retry_count': self.retry_count,
            'bandwidth_limit': self.bandwidth_limit,
            'is_git_repo': self.is_git_repo,
            'auto_commit': self.auto_commit,
            'auto_pull': self.auto_pull
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SyncProfile':
        data = data.copy()
        if data.get('source'):
            data['source'] = SyncLocation.from_dict(data['source'])
        if data.get('destination'):
            data['destination'] = SyncLocation.from_dict(data['destination'])
        if data.get('sync_mode'):
            data['sync_mode'] = SyncMode(data['sync_mode'])
        if data.get('sync_direction'):
            data['sync_direction'] = SyncDirection(data['sync_direction'])
        if data.get('rules'):
            data['rules'] = SyncRule.from_dict(data['rules'])
        if data.get('last_sync'):
            data['last_sync'] = datetime.fromisoformat(data['last_sync'])
        if data.get('created_at'):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at'):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)
    
    def validate(self) -> List[str]:
        """Validate the sync profile configuration"""
        errors = []
        
        if not self.source or not self.source.path:
            errors.append("Source location is required")
        if not self.destination or not self.destination.path:
            errors.append("Destination location is required")
        
        if self.source and self.destination:
            if os.path.normpath(self.source.path) == os.path.normpath(self.destination.path):
                errors.append("Source and destination cannot be the same")
        
        if self.bandwidth_limit and self.bandwidth_limit <= 0:
            errors.append("Bandwidth limit must be positive")
        
        if self.retry_count < 0:
            errors.append("Retry count cannot be negative")
        
        return errors