"""Configuration management for Pomodoro Timer."""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from src.constants import (
    CONFIG_FILE_PATH,
    CONFIG_VERSION,
    DEFAULT_WORK_MINUTES,
    DEFAULT_SHORT_BREAK_MINUTES,
    DEFAULT_LONG_BREAK_MINUTES,
    DEFAULT_POMODOROS_UNTIL_LONG_BREAK
)
from src.exceptions import ConfigurationError


class ConfigManager:
    """Manages application configuration and persistence."""
    
    DEFAULT_CONFIG = {
        "current_profile": "default",
        "profiles": {
            "default": {
                "name": "Default",
                "timers": {
                    "work_minutes": DEFAULT_WORK_MINUTES,
                    "short_break_minutes": DEFAULT_SHORT_BREAK_MINUTES,
                    "long_break_minutes": DEFAULT_LONG_BREAK_MINUTES,
                    "pomodoros_until_long_break": DEFAULT_POMODOROS_UNTIL_LONG_BREAK,
                    "extend_minutes": 5,  # Default extend time for work sessions
                    "extend_break_minutes": 5  # Default extend time for breaks
                }
            },
            "develop": {
                "name": "Development",
                "timers": {
                    "work_minutes": 45,
                    "short_break_minutes": 10,
                    "long_break_minutes": 30,
                    "pomodoros_until_long_break": 3,
                    "extend_minutes": 10,
                    "extend_break_minutes": 5
                }
            }
        }
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager.
        
        Args:
            config_path: Optional custom config file path
        """
        self.config_path = config_path or CONFIG_FILE_PATH
        self.config = self.load()
    
    def load(self) -> Dict[str, Any]:
        """Load configuration from file.
        
        Returns:
            Configuration dictionary
        """
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    
                # Check if migration is needed (old format has 'timers' at root level)
                if 'timers' in loaded_config and 'profiles' not in loaded_config:
                    loaded_config = self._migrate_to_profiles(loaded_config)
                    
                # Merge with defaults to ensure all keys exist
                return self._merge_configs(self.DEFAULT_CONFIG, loaded_config)
                
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config: {e}, using defaults")
                return self.DEFAULT_CONFIG.copy()
        
        # Create default config
        self.save(self.DEFAULT_CONFIG)
        return self.DEFAULT_CONFIG.copy()
    
    def save(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Save configuration to file.
        
        Args:
            config: Configuration to save (uses self.config if None)
        """
        config = config or self.config
        
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2, default=str)
                
        except IOError as e:
            raise ConfigurationError(f"Failed to save config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key.
        
        For timer values, automatically fetches from current profile.
        
        Args:
            key: Configuration key (e.g., 'timers.work_minutes')
            default: Default value if key not found
        
        Returns:
            Configuration value
        """
        # If requesting timer values, redirect to current profile
        if key.startswith('timers.'):
            current_profile = self.config.get('current_profile', 'default')
            profile_key = f'profiles.{current_profile}.{key}'
            return self._get_nested(profile_key, default)
        
        return self._get_nested(key, default)
    
    def _get_nested(self, key: str, default: Any = None) -> Any:
        """Get nested configuration value by dot-notation key.
        
        Args:
            key: Configuration key
            default: Default value if key not found
        
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value by dot-notation key.
        
        Args:
            key: Configuration key (e.g., 'timers.work_minutes')
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        # Navigate to the parent dict
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        
        # Save to file
        self.save()
    
    
    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """Recursively merge loaded config with defaults.
        
        Args:
            default: Default configuration
            loaded: Loaded configuration
        
        Returns:
            Merged configuration
        """
        result = default.copy()
        
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _migrate_to_profiles(self, old_config: Dict) -> Dict:
        """Migrate old configuration format to profile-based structure.
        
        Args:
            old_config: Old configuration dictionary with timers at root
        
        Returns:
            Migrated configuration with profiles
        """
        new_config = {
            "current_profile": "default",
            "profiles": {
                "default": {
                    "name": "Default",
                    "timers": old_config.get("timers", self.DEFAULT_CONFIG["profiles"]["default"]["timers"])
                }
            }
        }
        
        # Save the migrated config
        self.save(new_config)
        return new_config
    
    # Profile management methods
    def get_profiles(self) -> Dict[str, Dict]:
        """Get all available profiles.
        
        Returns:
            Dictionary of profile name to profile data
        """
        return self.config.get('profiles', {})
    
    def get_current_profile(self) -> str:
        """Get the name of the current active profile.
        
        Returns:
            Current profile name
        """
        return self.config.get('current_profile', 'default')
    
    def set_current_profile(self, profile_name: str) -> bool:
        """Switch to a different profile.
        
        Args:
            profile_name: Name of the profile to switch to
            
        Returns:
            True if successful, False if profile doesn't exist
        """
        if profile_name in self.config.get('profiles', {}):
            self.config['current_profile'] = profile_name
            self.save()
            return True
        return False
    
    def create_profile(self, name: str, display_name: str, timers: Dict = None) -> bool:
        """Create a new profile.
        
        Args:
            name: Profile identifier (no spaces, used as key)
            display_name: User-friendly display name
            timers: Timer configuration (uses default if None)
            
        Returns:
            True if created, False if name already exists
        """
        if name in self.config.get('profiles', {}):
            return False
        
        if 'profiles' not in self.config:
            self.config['profiles'] = {}
        
        default_timers = self.DEFAULT_CONFIG["profiles"]["default"]["timers"].copy()
        if timers:
            default_timers.update(timers)
        
        self.config['profiles'][name] = {
            "name": display_name,
            "timers": default_timers
        }
        
        self.save()
        return True
    
    def delete_profile(self, name: str) -> bool:
        """Delete a profile.
        
        Args:
            name: Profile name to delete
            
        Returns:
            True if deleted, False if profile doesn't exist or is default
        """
        if name == 'default':
            return False  # Cannot delete default profile
        
        profiles = self.config.get('profiles', {})
        if name in profiles:
            del profiles[name]
            
            # If deleting current profile, switch to default
            if self.config.get('current_profile') == name:
                self.config['current_profile'] = 'default'
            
            self.save()
            return True
        
        return False
    
    def update_profile(self, name: str, timers: Dict) -> bool:
        """Update a profile's timer settings.
        
        Args:
            name: Profile name to update
            timers: New timer values
            
        Returns:
            True if updated, False if profile doesn't exist
        """
        profiles = self.config.get('profiles', {})
        if name in profiles:
            profiles[name]['timers'].update(timers)
            self.save()
            return True
        return False
    
    def validate(self) -> bool:
        """Validate configuration values.
        
        Returns:
            True if valid, raises ConfigurationError if not
        """
        timers = self.config.get('timers', {})
        
        # Validate timer values
        if timers.get('work_minutes', 0) <= 0:
            raise ConfigurationError("Work minutes must be positive")
        
        if timers.get('short_break_minutes', 0) <= 0:
            raise ConfigurationError("Short break minutes must be positive")
        
        if timers.get('long_break_minutes', 0) <= 0:
            raise ConfigurationError("Long break minutes must be positive")
        
        if timers.get('pomodoros_until_long_break', 0) <= 0:
            raise ConfigurationError("Pomodoros until long break must be positive")
        
        return True