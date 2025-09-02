# Pomodoro Menu Bar Timer - Technical Specification

## Project Overview
A minimalist macOS menu bar application implementing the Pomodoro Technique with customizable work/break intervals, visual progress indication, and native notifications.

## Functional Requirements

### Core Features
1. **Menu Bar Integration**
   - Application runs exclusively in the macOS menu bar
   - Dynamic icon shows timer progress visually
   - Click menu icon to access controls

2. **Timer Functionality**
   - Configurable work interval (default: 25 minutes)
   - Configurable short break (default: 5 minutes)
   - Configurable long break (default: 15 minutes)
   - Long break after 4 pomodoros
   - Start/Stop/Reset controls
   - Pause/Resume capability

3. **Visual Feedback**
   - Menu bar icon fills/empties to show remaining time
   - Display exact time remaining in menu
   - Different icon states for work/break periods

4. **Notifications**
   - Native macOS notification when timer completes
   - Center-screen popup with options:
     - "Take Break" - Start break timer
     - "Extend 5 minutes" - Add 5 minutes to current timer
     - "Skip Break" - Start next work session

5. **Configuration**
   - Settings accessible from menu (JSON editor)
   - Persistent configuration in `~/.config/pomodoro-timer/config.json`
   - Multiple timer profiles support
   - Configurable parameters:
     - Work duration (minutes)
     - Short break duration (minutes)
     - Long break duration (minutes)
     - Pomodoros until long break
     - Separate extend minutes for work and breaks

6. **Statistics Tracking**
   - SQLite database at `~/.config/pomodoro-timer/stats.db`
   - Tracks every session with timestamps
   - Session data: type, duration (excluding pauses), completion status, extends, profile name
   - Actual work time tracking (pause time excluded)
   - Today's progress and all-time statistics
   - Profile-based statistics tracking

7. **Crash Recovery**
   - Periodic state saving every 30 seconds
   - Orphaned session detection on startup
   - Recovery dialog for interrupted sessions
   - State persistence in `~/.config/pomodoro-timer/timer_state.json`

## Non-Functional Requirements

### Performance
- CPU usage < 1% when idle
- Memory footprint < 50MB
- Instant menu response time
- Icon updates every second during countdown

### Usability
- Single-click access to all features
- Clear visual distinction between states
- Minimal configuration required
- Confirmation dialog for stopping active sessions
- Reset button safely located in Settings submenu

### Compatibility
- macOS 10.15 (Catalina) or later
- Native Apple Silicon support
- Automatic dark/light mode adaptation

## Architecture Design

### Design Pattern: MVC with Observer

```
┌─────────────────────────────────────────────────┐
│                  MenuBarApp                      │
│                    (View)                        │
│  - rumps.App                                     │
│  - Menu items                                    │
│  - Icon display                                  │
└────────────────────┬────────────────────────────┘
                     │
                     │ Observer Pattern
                     │
┌────────────────────▼────────────────────────────┐
│              TimerController                     │
│               (Controller)                       │
│  - Start/Stop/Reset logic                       │
│  - State management                             │
│  - Notification triggers                        │
└────────────────────┬────────────────────────────┘
                     │
        ┌────────────┴────────────┬───────────────┐
        │                         │               │
┌───────▼──────┐   ┌─────────────▼──────┐  ┌────▼─────┐
│PomodoroTimer │   │  ConfigManager     │  │Stats DB  │
│   (Model)    │   │    (Model)         │  │(Service) │
│              │   │                    │  │          │
│- Time logic  │   │- Load/Save config  │  │- Session │
│- Intervals   │   │- Validation        │  │  tracking│
│- State       │   │- Defaults          │  │- Reports │
└──────────────┘   └────────────────────┘  └──────────┘
```

### Component Responsibilities

#### PomodoroTimer (Model)
- Manages timer state (IDLE, WORKING, SHORT_BREAK, LONG_BREAK, PAUSED)
- Tracks elapsed time and remaining time
- Tracks actual work time (excluding pause duration)
- Counts completed pomodoros
- Emits events: timer_tick, timer_complete, state_change

#### TimerController (Controller)
- Mediates between Model and View
- Handles user actions
- Manages timer lifecycle
- Triggers notifications
- Updates icon based on state

#### MenuBarApp (View)
- Creates menu bar presence
- Displays menu items
- Shows current timer state
- Handles user input
- Updates icon display

#### IconGenerator (Service)
- Creates dynamic icons showing progress
- Generates different icons for each state
- Handles light/dark mode
- Caches generated icons

#### ConfigManager (Service)
- Loads/saves JSON configuration
- Validates configuration values
- Provides defaults
- Handles migration between versions

#### NotificationManager (Service)
- Shows macOS notifications
- Creates native PyObjC completion dialogs
- Handles notification permissions
- Manages sound playback

#### StateManager (Service)
- Periodic state saving for crash recovery
- Orphaned session detection
- Recovery dialog presentation
- State persistence and restoration

## Data Model

### Configuration Schema
```json
{
  "version": "1.0.0",
  "current_profile": "default",
  "profiles": {
    "default": {
      "timers": {
        "work_minutes": 25,
        "short_break_minutes": 5,
        "long_break_minutes": 15,
        "pomodoros_until_long_break": 4,
        "work_extend_minutes": 5,
        "break_extend_minutes": 5
      }
    }
  }
}
```

### Database Schema
```sql
CREATE TABLE sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_type TEXT NOT NULL,
  start_time TIMESTAMP NOT NULL,
  end_time TIMESTAMP,
  planned_duration INTEGER NOT NULL,
  actual_duration INTEGER,  -- Excludes pause time
  completed BOOLEAN DEFAULT 0,
  extend_count INTEGER DEFAULT 0,
  profile_name TEXT
);
```

### Timer States
```python
class TimerState(Enum):
    IDLE = "idle"
    WORKING = "working"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"
    PAUSED = "paused"
```

## Test Strategy

### Unit Tests
- Timer logic (state transitions, time calculations)
- Configuration management (load, save, validate)
- Icon generation (progress calculation, caching)
- Notification triggers

### Integration Tests
- Timer controller with model
- Menu updates with timer changes
- Configuration persistence
- Notification system

### Test Coverage Goals
- Core logic: 100%
- UI handlers: 80%
- Utilities: 90%
- Overall: 85%

## TODO List

### Phase 1: Setup & Foundation
- [x] Create project structure with src/ and tests/ directories
- [x] Create requirements.txt with dependencies (rumps, Pillow, pytest)
- [x] Set up pytest configuration and test structure
- [x] Create base exception classes and constants

### Phase 2: Core Timer Logic (TDD)
- [x] Write tests for TimerState enum and transitions
- [x] Write tests for PomodoroTimer initialization and configuration
- [x] Write tests for timer tick and time calculation
- [x] Write tests for pomodoro counting and break logic
- [x] Implement PomodoroTimer class passing all tests

### Phase 3: Configuration Management (TDD)
- [x] Write tests for ConfigManager initialization with defaults
- [x] Write tests for config file loading and parsing
- [x] Write tests for config validation and migration
- [x] Write tests for saving configuration changes
- [x] Implement ConfigManager class passing all tests

### Phase 4: Icon Generation System (TDD)
- [x] Write tests for progress calculation (0-100%)
- [x] Write tests for icon generation with different fill levels
- [x] Write tests for state-based icon selection
- [x] Write tests for icon caching mechanism
- [x] Implement IconGenerator class with progress visualization

### Phase 5: Timer Controller (TDD)
- [x] Write tests for controller initialization and timer binding
- [x] Write tests for start/stop/reset operations
- [x] Write tests for pause/resume functionality
- [x] Write tests for timer completion handling
- [x] Implement TimerController with state management

### Phase 6: Menu Bar Interface
- [x] Create MenuBarApp class with rumps.App
- [x] Implement menu structure (Start, Stop, Reset, Settings, Quit)
- [x] Connect menu actions to controller
- [x] Implement icon updates on timer tick (updating once per minute is sufficient)
- [x] Add time display in menu

### Phase 7: Settings Dialog
- [x] Create settings window with rumps.Window
- [x] Implement form validation
- [x] Connect to ConfigManager for persistence
- [x] Add configurable extend minutes and daily goal

### Phase 8: Notifications & Popups
- [x] Implement NotificationManager with macOS notifications
- [x] Create center-screen popup dialog with tkinter
- [x] Add "Take Break" and "Extend X min" buttons (configurable)
- [x] Implement notification permissions check
- [x] Add sound notifications (using system sounds)

### Phase 9: Statistics & Database
- [x] Create SQLite database for session tracking
- [x] Implement session start/end tracking
- [x] Track extends and completion status
- [x] Add today's statistics query
- [x] Add all-time statistics query

### Phase 10: Polish & Enhancement
- [x] Use emoji icons for visual progress
- [x] Add statistics tracking via SQLite
- [x] Implement real-time seconds display
- [x] JSON-based settings editor
- [x] Add timer profiles support (multiple timer configurations)
- [x] Separate extend times for work and break sessions
- [x] Enhanced completion dialogs with PyObjC integration
- [x] Thread-safe timer operations with RLock
- [x] Simplified menu display (removed redundant time)
- [x] Pause time tracking (actual work time calculation)
- [x] Crash recovery with orphaned session detection
- [x] State persistence for power outages
- [x] Stop confirmation dialog
- [x] Reset button moved to Settings submenu for safety

### Phase 11: Testing & Integration
- [ ] Run full test suite and achieve coverage goals
- [ ] Perform manual testing of all features
- [ ] Test on different macOS versions
- [ ] Test with various screen resolutions

### Phase 12: Packaging & Distribution
- [x] Create setup.py for py2app
- [x] Configure app bundle settings (LSUIElement for dock hiding)
- [x] Generate build script for .app bundle
- [ ] Create DMG installer script
- [x] Write user documentation (README.md)

## Development Guidelines

### Code Style
- Follow PEP 8 for Python code
- Use type hints for all functions
- Document all public methods
- Keep functions under 20 lines
- Maximum line length: 100 characters

### Git Workflow
- Feature branches for new functionality
- Commit messages: "type: description" (feat, fix, test, docs)
- All tests must pass before merge
- Code review for significant changes

### Testing Requirements
- Write tests before implementation (TDD)
- Each test should test one thing
- Use descriptive test names
- Mock external dependencies
- No test should take > 1 second

## Distribution

### Packaging with py2app
```python
# setup.py
from setuptools import setup

APP = ['src/main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'assets/icon.icns',
    'plist': {
        'CFBundleName': 'Pomodoro Timer',
        'CFBundleDisplayName': 'Pomodoro Timer',
        'CFBundleGetInfoString': "Pomodoro Timer for macOS",
        'CFBundleIdentifier': "com.pomodoro.timer",
        'CFBundleVersion': "1.0.0",
        'CFBundleShortVersionString': "1.0.0",
        'LSUIElement': True,  # Hide from dock
    },
    'packages': ['rumps', 'PIL'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
```

### Build Commands
```bash
# Development build
python setup.py py2app -A

# Production build
python setup.py py2app

# Create DMG
hdiutil create -volname "Pomodoro Timer" -srcfolder dist -ov -format UDZO PomodoroTimer.dmg
```

## Current Status

### Production Release v1.0.0 ✅
The application is now production-ready with:
- Core timer logic with work/break intervals
- Menu bar application with real-time emoji icons (updates every second)
- Start/Stop/Pause/Reset controls with thread-safe operations
- **Timer Profiles**: Multiple customizable timer configurations
- **Separate Extend Times**: Different extend durations for work and breaks
- **Enhanced Dialogs**: Native macOS dialogs using PyObjC
- **Thread Safety**: RLock implementation preventing deadlocks
- Enhanced ConfigManager with profile support
- NotificationManager with center-screen popups and sound alerts
- Statistics tracking with profile names in database
- Configurable extend minutes (separate for work/breaks) and daily goals
- Hidden from dock (menu bar only)
- **Built and packaged** with py2app

### Running the Application

#### Development
```bash
python3 main.py
```

#### Production (Built App)
```bash
open "dist/Pomodoro Timer.app"
```

#### Building from Source
```bash
/usr/bin/python3 setup.py py2app
```

## Version History
- v1.0.0 - Production release with all features, profiles, thread safety, and enhanced UI

## License
MIT License

## Author
Created for productive work sessions with the Pomodoro Technique.