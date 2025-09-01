"""Generate and manage icons for menu bar."""

import os
from pathlib import Path
from typing import Optional
from src.constants import TimerState


class IconGenerator:
    """Manages menu bar icons for timer states."""
    
    def __init__(self):
        """Initialize icon generator with paths to icon files."""
        self.icons_dir = Path(__file__).parent.parent / "assets" / "icons"
        self.cache = {}
        
    def get_icon_path(
        self,
        progress: int,
        state: TimerState,
        use_template: bool = True
    ) -> Optional[str]:
        """Get the path to the appropriate icon file.
        
        Args:
            progress: Progress percentage (0-100)
            state: Current timer state
            use_template: Use template icons for dark mode support
        
        Returns:
            Path to icon file or None if not found
        """
        # Special case for idle and paused
        if state == TimerState.IDLE:
            icon_path = self.icons_dir / "idle.png"
            return str(icon_path) if icon_path.exists() else None
            
        if state == TimerState.PAUSED:
            icon_path = self.icons_dir / "paused.png"
            return str(icon_path) if icon_path.exists() else None
        
        # Round progress to nearest level
        if progress <= 12:
            level = 0
        elif progress <= 37:
            level = 25
        elif progress <= 62:
            level = 50
        elif progress <= 87:
            level = 75
        else:
            level = 100
        
        # Choose icon based on state
        if use_template:
            # Template icons work better with dark mode
            filename = f"template_{level}.png"
        elif state == TimerState.WORKING:
            filename = f"work_{level}.png"
        elif state in (TimerState.SHORT_BREAK, TimerState.LONG_BREAK):
            filename = f"break_{level}.png"
        else:
            return None
        
        icon_path = self.icons_dir / filename
        return str(icon_path) if icon_path.exists() else None
    
    def get_progress_for_time(self, remaining_seconds: int, total_seconds: int) -> int:
        """Calculate progress percentage from time.
        
        Args:
            remaining_seconds: Seconds remaining
            total_seconds: Total seconds for timer
        
        Returns:
            Progress percentage (0-100)
        """
        if total_seconds == 0:
            return 0
        
        elapsed = total_seconds - remaining_seconds
        percentage = int((elapsed / total_seconds) * 100)
        return min(percentage, 100)