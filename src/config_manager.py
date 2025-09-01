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
        "version": CONFIG_VERSION,
        "timers": {
            "work_minutes": DEFAULT_WORK_MINUTES,
            "short_break_minutes": DEFAULT_SHORT_BREAK_MINUTES,
            "long_break_minutes": DEFAULT_LONG_BREAK_MINUTES,
            "pomodoros_until_long_break": DEFAULT_POMODOROS_UNTIL_LONG_BREAK,
            "extend_minutes": 5  # Default extend time
        },
        "preferences": {
            "sound_enabled": True,
            "auto_start_breaks": False,
            "auto_start_pomodoros": False,
            "show_time_in_menu_bar": True,
            "use_24_hour_format": False,
            "play_ticking_sound": False,
            "volume": 50  # 0-100
        },
        "appearance": {
            "show_progress_bar": True,
            "menu_bar_icon_style": "emoji",  # "emoji", "progress", "simple"
            "dark_mode_auto": True
        },
        "statistics": {
            "total_pomodoros": 0,
            "total_work_minutes": 0,
            "daily_goal": 8,  # pomodoros per day
            "last_reset_date": None
        },
        "shortcuts": {
            "start_stop": "cmd+shift+p",
            "skip": "cmd+shift+s",
            "reset": "cmd+shift+r"
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
                    
                # Migrate if needed
                if loaded_config.get('version') != CONFIG_VERSION:
                    loaded_config = self._migrate_config(loaded_config)
                
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
        
        Args:
            key: Configuration key (e.g., 'timers.work_minutes')
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
    
    def update_statistics(self, pomodoros: int = 0, work_minutes: int = 0) -> None:
        """Update statistics.
        
        Args:
            pomodoros: Number of pomodoros to add
            work_minutes: Number of work minutes to add
        """
        stats = self.config.get('statistics', {})
        stats['total_pomodoros'] = stats.get('total_pomodoros', 0) + pomodoros
        stats['total_work_minutes'] = stats.get('total_work_minutes', 0) + work_minutes
        self.config['statistics'] = stats
        self.save()
    
    def reset_statistics(self) -> None:
        """Reset statistics to zero."""
        self.config['statistics']['total_pomodoros'] = 0
        self.config['statistics']['total_work_minutes'] = 0
        self.config['statistics']['last_reset_date'] = None
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
    
    def _migrate_config(self, old_config: Dict) -> Dict:
        """Migrate old configuration format to new version.
        
        Args:
            old_config: Old configuration dictionary
        
        Returns:
            Migrated configuration
        """
        # Simple migration - just update version
        # Add migration logic here for future versions
        old_config['version'] = CONFIG_VERSION
        return old_config
    
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