"""Notification management for Pomodoro Timer."""

import os
import subprocess
from pathlib import Path
import rumps
from typing import Optional, Callable
from src.constants import (
    NOTIFICATION_WORK_COMPLETE,
    NOTIFICATION_BREAK_COMPLETE,
    NOTIFICATION_LONG_BREAK_COMPLETE
)


class NotificationManager:
    """Manages notifications and popup dialogs."""
    
    def __init__(self, config_manager=None):
        """Initialize notification manager.
        
        Args:
            config_manager: ConfigManager instance for settings
        """
        self.config = config_manager
        self.sound_file = Path(__file__).parent.parent / "assets" / "complete.wav"
        
    def show_notification(
        self,
        title: str,
        message: str,
        sound: bool = True
    ) -> None:
        """Show a macOS notification.
        
        Args:
            title: Notification title
            message: Notification message
            sound: Whether to play sound
        """
        rumps.notification(
            title=title,
            subtitle="",
            message=message,
            sound=False  # We'll handle sound separately
        )
        
        if sound:
            self.play_sound()
    
    def play_sound(self, sound_file: Optional[Path] = None) -> None:
        """Play a sound file.
        
        Args:
            sound_file: Path to sound file (uses default if None)
        """
        sound_file = sound_file or self.sound_file
        
        # Use afplay on macOS (built-in audio player)
        if sound_file and sound_file.exists():
            try:
                subprocess.run(
                    ['afplay', str(sound_file)],
                    check=False,
                    capture_output=True
                )
            except Exception as e:
                print(f"Error playing sound: {e}")
        else:
            # Use system sound if no file
            try:
                subprocess.run(
                    ['afplay', '/System/Library/Sounds/Glass.aiff'],
                    check=False,
                    capture_output=True
                )
            except:
                pass
    
    def show_popup_dialog(
        self,
        title: str,
        message: str,
        on_break: Optional[Callable] = None,
        on_extend: Optional[Callable] = None,
        on_skip: Optional[Callable] = None,
        extend_minutes: int = 5
    ) -> None:
        """Show a popup dialog using rumps.alert.
        
        Args:
            title: Dialog title
            message: Dialog message
            on_break: Callback for "Take Break" button
            on_extend: Callback for "Extend" button
            on_skip: Callback for "Skip" button
            extend_minutes: Number of minutes to extend
        """
        # Play sound
        self.play_sound()
        
        # Simple activation like the settings window
        try:
            import AppKit
            AppKit.NSApp.activateIgnoringOtherApps_(True)
        except:
            pass
        
        # Show rumps alert dialog directly - rumps handles the display
        response = rumps.alert(
            title=title,
            message=message,
            ok="Take Break" if on_break else "Start Work",
            cancel="Skip" if on_skip else "Cancel",
            other=f"Extend {extend_minutes} min" if on_extend else None
        )
        
        # Handle response
        if response == 1:  # OK button
            if on_break:
                on_break()
        elif response == 2:  # Other button (Extend)
            if on_extend:
                on_extend()
        elif response == 0:  # Cancel/Skip button
            if on_skip:
                on_skip()
    
    def show_work_complete_dialog(
        self,
        on_break: Callable,
        on_extend: Callable,
        on_skip: Callable,
        extend_minutes: int = 5
    ) -> None:
        """Show work completion dialog.
        
        Args:
            on_break: Callback for taking break
            on_extend: Callback for extending timer
            on_skip: Callback for skipping break
            extend_minutes: Minutes to extend
        """
        self.show_popup_dialog(
            title="🎉 Work Session Complete!",
            message="Great job! Time for a well-deserved break.",
            on_break=on_break,
            on_extend=on_extend,
            on_skip=on_skip,
            extend_minutes=extend_minutes
        )
    
    def show_break_complete_dialog(
        self,
        on_work: Callable,
        on_extend: Callable,
        is_long_break: bool = False
    ) -> None:
        """Show break completion dialog.
        
        Args:
            on_work: Callback for starting work
            on_extend: Callback for extending break
            is_long_break: Whether this was a long break
        """
        if is_long_break:
            title = "☕ Long Break Complete!"
            message = "Feeling refreshed? Ready to tackle the next session!"
        else:
            title = "✅ Break Complete!"
            message = "Ready to get back to work?"
        
        self.show_popup_dialog(
            title=title,
            message=message,
            on_break=on_work,  # "Start Work" button
            on_extend=on_extend,
            extend_minutes=5
        )