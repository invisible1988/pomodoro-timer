"""JSON-based settings editor for Pomodoro Timer."""

import rumps
import json
import subprocess
import os
from pathlib import Path
from src.config_manager import ConfigManager


class JsonSettings:
    """JSON settings editor."""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize settings."""
        self.config = config_manager
    
    def show(self):
        """Show JSON configuration in a text editor."""
        # Get the config file path
        config_path = self.config.config_path
        
        # Ensure config file exists with current values
        self.config.save()
        
        # Format the JSON nicely
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2, sort_keys=True)
        
        # Show current config in a window
        with open(config_path, 'r') as f:
            current_json = f.read()
        
        # Don't add comments - they slow down parsing
        
        window = rumps.Window(
            title="Pomodoro Timer Configuration (JSON)",
            message="Edit the configuration below:",
            default_text=current_json,
            ok="Save",
            cancel="Cancel",
            dimensions=(500, 400)
        )
        
        # Try to bring window to front and set icon
        try:
            import AppKit
            import os
            
            # Activate the app
            AppKit.NSApp.activateIgnoringOtherApps_(True)
            
            # Try to set the icon again for this window
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'tomato.png')
            if os.path.exists(icon_path):
                image = AppKit.NSImage.alloc().initWithContentsOfFile_(icon_path)
                if image:
                    AppKit.NSApp.setApplicationIconImage_(image)
        except:
            pass
        
        response = window.run()
        if response.clicked:
            try:
                # Parse and validate JSON
                new_config = json.loads(response.text)
                
                # Save the new configuration
                with open(config_path, 'w') as f:
                    json.dump(new_config, f, indent=2, sort_keys=True)
                
                # Reload config in manager
                self.config.config = new_config
                
                # Don't show notification - too slow
                
            except json.JSONDecodeError as e:
                rumps.alert(
                    "Invalid JSON",
                    f"Please check your JSON syntax:\n{str(e)}"
                )
            except Exception as e:
                rumps.alert(
                    "Error",
                    f"Failed to save configuration:\n{str(e)}"
                )