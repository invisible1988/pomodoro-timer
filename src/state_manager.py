"""State persistence for crash recovery."""

import json
import time
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime


class StateManager:
    """Manages saving and loading timer state for crash recovery."""
    
    def __init__(self, state_file: Optional[Path] = None):
        """Initialize state manager.
        
        Args:
            state_file: Path to state file (uses default if None)
        """
        if state_file is None:
            config_dir = Path.home() / '.config' / 'pomodoro-timer'
            config_dir.mkdir(parents=True, exist_ok=True)
            self.state_file = config_dir / 'timer_state.json'
        else:
            self.state_file = state_file
    
    def save_state(self, timer_state: str, remaining_seconds: int, 
                   session_id: Optional[int] = None, 
                   completed_pomodoros: int = 0,
                   pause_info: Optional[Dict] = None) -> None:
        """Save current timer state to file.
        
        Args:
            timer_state: Current timer state (WORKING, BREAK, etc.)
            remaining_seconds: Seconds remaining on timer
            session_id: Current database session ID
            completed_pomodoros: Number of completed pomodoros
            pause_info: Pause tracking information
        """
        state = {
            'timer_state': timer_state,
            'remaining_seconds': remaining_seconds,
            'session_id': session_id,
            'completed_pomodoros': completed_pomodoros,
            'last_save': datetime.now().isoformat(),
            'pause_info': pause_info or {}
        }
        
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            # Don't crash if we can't save state
            print(f"Warning: Could not save timer state: {e}")
    
    def load_state(self) -> Optional[Dict]:
        """Load saved timer state if it exists.
        
        Returns:
            Saved state dictionary or None if no valid state exists
        """
        if not self.state_file.exists():
            return None
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            # Check if state is recent (within last hour)
            last_save = datetime.fromisoformat(state['last_save'])
            age_hours = (datetime.now() - last_save).total_seconds() / 3600
            
            if age_hours > 1:
                # State is too old, ignore it
                self.clear_state()
                return None
            
            return state
        except Exception as e:
            print(f"Warning: Could not load timer state: {e}")
            self.clear_state()
            return None
    
    def clear_state(self) -> None:
        """Clear the saved state file."""
        try:
            if self.state_file.exists():
                self.state_file.unlink()
        except Exception as e:
            print(f"Warning: Could not clear timer state: {e}")