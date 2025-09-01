"""Constants and configuration for Pomodoro Timer."""

from enum import Enum
from pathlib import Path


class TimerState(Enum):
    """Possible states for the Pomodoro timer."""
    IDLE = "idle"
    WORKING = "working"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"
    PAUSED = "paused"


# Default timer durations (in minutes)
DEFAULT_WORK_MINUTES = 25
DEFAULT_SHORT_BREAK_MINUTES = 5
DEFAULT_LONG_BREAK_MINUTES = 15
DEFAULT_POMODOROS_UNTIL_LONG_BREAK = 4

# Configuration
CONFIG_FILE_PATH = Path.home() / ".pomodoro-config.json"
CONFIG_VERSION = "1.0.0"

# UI Constants
APP_NAME = "Pomodoro Timer"
ICON_SIZE = 22  # macOS menu bar icon size
UPDATE_INTERVAL = 1.0  # seconds

# Menu item titles
MENU_START = "Start"
MENU_STOP = "Stop"
MENU_RESET = "Reset"
MENU_PAUSE = "Pause"
MENU_RESUME = "Resume"
MENU_SETTINGS = "Settings..."
MENU_STATISTICS = "Statistics"
MENU_ABOUT = "About"
MENU_QUIT = "Quit"

# Notification messages
NOTIFICATION_WORK_COMPLETE = "Work session complete!"
NOTIFICATION_BREAK_COMPLETE = "Break complete!"
NOTIFICATION_LONG_BREAK_COMPLETE = "Long break complete!"

# Colors for icon generation (RGB)
COLOR_WORK = (255, 95, 95)      # Red for work
COLOR_BREAK = (95, 255, 95)     # Green for break
COLOR_IDLE = (128, 128, 128)    # Gray for idle
COLOR_PAUSED = (255, 195, 95)   # Orange for paused