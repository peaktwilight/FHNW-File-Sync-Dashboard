import json
import os
from typing import List, Optional, Dict
import uuid
from datetime import datetime
import shutil

from ..models.sync_profile import SyncProfile, SyncLocation, SyncRule, SyncMode, SyncDirection


class ProfileManager:
    """Manages sync profiles - loading, saving, and CRUD operations"""
    
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            config_dir = os.path.expanduser("~/.fhnw_sync")
        self.config_dir = config_dir
        self.profiles_dir = os.path.join(config_dir, "profiles")
        self.config_file = os.path.join(config_dir, "config.json")
        self._ensure_directories()
        self._profiles_cache: Dict[str, SyncProfile] = {}
        self.load_all_profiles()
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist"""
        os.makedirs(self.profiles_dir, exist_ok=True)
        
        # Migrate old config.txt if it exists
        old_config = "config.txt"
        if os.path.exists(old_config) and not os.path.exists(self.config_file):
            self._migrate_old_config(old_config)
    
    def _migrate_old_config(self, old_config_path: str):
        """Migrate from old config.txt to new profile system"""
        import configparser
        config = configparser.ConfigParser()
        config.read(old_config_path)
        
        if 'DEFAULT' in config:
            old = config['DEFAULT']
            
            # Create a default profile from old config
            profile = SyncProfile(
                id=str(uuid.uuid4()),
                name="Migrated Profile",
                description="Automatically migrated from config.txt",
                sync_mode=SyncMode.UPDATE,
                sync_direction=SyncDirection.REMOTE_TO_LOCAL,
                retry_count=int(old.get('max_rsync_retries', '3'))
            )
            
            # Set up source paths
            source_paths = [p.strip() for p in old.get('source_paths', '').split(',') if p.strip()]
            if source_paths:
                # For now, just use the first source path
                profile.source = SyncLocation(
                    path=source_paths[0],
                    name="Network Drive",
                    is_remote=True
                )
            
            # Set up destination
            dest = old.get('destination', '').strip()
            if dest:
                profile.destination = SyncLocation(
                    path=dest,
                    name="Local Folder",
                    is_remote=False
                )
            
            # Git settings
            profile.is_git_repo = old.get('enable_git_pull', 'False').lower() == 'true'
            profile.auto_pull = profile.is_git_repo
            
            self.save_profile(profile)
            
            # Save general config
            general_config = {
                'default_profile': profile.id,
                'theme': old.get('theme', 'dark'),
                'log_level': old.get('log_level', 'INFO')
            }
            self._save_general_config(general_config)
    
    def _save_general_config(self, config: Dict):
        """Save general application configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def get_general_config(self) -> Dict:
        """Load general application configuration"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {
            'default_profile': None,
            'theme': 'dark',
            'log_level': 'INFO'
        }
    
    def create_profile(self, name: str, description: str = "") -> SyncProfile:
        """Create a new sync profile"""
        profile = SyncProfile(
            id=str(uuid.uuid4()),
            name=name,
            description=description
        )
        self.save_profile(profile)
        return profile
    
    def save_profile(self, profile: SyncProfile) -> bool:
        """Save a profile to disk"""
        profile.updated_at = datetime.now()
        profile_path = os.path.join(self.profiles_dir, f"{profile.id}.json")
        
        try:
            with open(profile_path, 'w') as f:
                json.dump(profile.to_dict(), f, indent=2)
            self._profiles_cache[profile.id] = profile
            return True
        except Exception as e:
            print(f"Error saving profile: {e}")
            return False
    
    def load_profile(self, profile_id: str) -> Optional[SyncProfile]:
        """Load a specific profile"""
        if profile_id in self._profiles_cache:
            return self._profiles_cache[profile_id]
        
        profile_path = os.path.join(self.profiles_dir, f"{profile_id}.json")
        if os.path.exists(profile_path):
            try:
                with open(profile_path, 'r') as f:
                    data = json.load(f)
                profile = SyncProfile.from_dict(data)
                self._profiles_cache[profile_id] = profile
                return profile
            except Exception as e:
                print(f"Error loading profile {profile_id}: {e}")
        return None
    
    def load_all_profiles(self) -> List[SyncProfile]:
        """Load all profiles from disk"""
        profiles = []
        self._profiles_cache.clear()
        
        if os.path.exists(self.profiles_dir):
            for filename in os.listdir(self.profiles_dir):
                if filename.endswith('.json'):
                    profile_id = filename[:-5]  # Remove .json
                    profile = self.load_profile(profile_id)
                    if profile:
                        profiles.append(profile)
        
        return profiles
    
    def delete_profile(self, profile_id: str) -> bool:
        """Delete a profile"""
        profile_path = os.path.join(self.profiles_dir, f"{profile_id}.json")
        
        try:
            if os.path.exists(profile_path):
                os.remove(profile_path)
            if profile_id in self._profiles_cache:
                del self._profiles_cache[profile_id]
            return True
        except Exception as e:
            print(f"Error deleting profile: {e}")
            return False
    
    def duplicate_profile(self, profile_id: str, new_name: str) -> Optional[SyncProfile]:
        """Create a copy of an existing profile"""
        original = self.load_profile(profile_id)
        if not original:
            return None
        
        new_profile = SyncProfile(
            id=str(uuid.uuid4()),
            name=new_name,
            description=f"Copy of {original.name}",
            source=original.source,
            destination=original.destination,
            sync_mode=original.sync_mode,
            sync_direction=original.sync_direction,
            rules=original.rules,
            enabled=True,
            schedule=original.schedule,
            preserve_permissions=original.preserve_permissions,
            preserve_timestamps=original.preserve_timestamps,
            follow_symlinks=original.follow_symlinks,
            retry_count=original.retry_count,
            bandwidth_limit=original.bandwidth_limit,
            is_git_repo=original.is_git_repo,
            auto_commit=original.auto_commit,
            auto_pull=original.auto_pull
        )
        
        self.save_profile(new_profile)
        return new_profile
    
    def export_profile(self, profile_id: str, export_path: str) -> bool:
        """Export a profile to a file"""
        profile = self.load_profile(profile_id)
        if not profile:
            return False
        
        try:
            with open(export_path, 'w') as f:
                json.dump(profile.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting profile: {e}")
            return False
    
    def import_profile(self, import_path: str) -> Optional[SyncProfile]:
        """Import a profile from a file"""
        try:
            with open(import_path, 'r') as f:
                data = json.load(f)
            
            # Generate new ID to avoid conflicts
            data['id'] = str(uuid.uuid4())
            data['created_at'] = datetime.now().isoformat()
            data['updated_at'] = datetime.now().isoformat()
            
            profile = SyncProfile.from_dict(data)
            self.save_profile(profile)
            return profile
        except Exception as e:
            print(f"Error importing profile: {e}")
            return None
    
    def get_default_profile(self) -> Optional[SyncProfile]:
        """Get the default profile if set"""
        config = self.get_general_config()
        default_id = config.get('default_profile')
        if default_id:
            return self.load_profile(default_id)
        
        # Return first profile if no default set
        profiles = self.load_all_profiles()
        return profiles[0] if profiles else None
    
    def set_default_profile(self, profile_id: str):
        """Set the default profile"""
        config = self.get_general_config()
        config['default_profile'] = profile_id
        self._save_general_config(config)