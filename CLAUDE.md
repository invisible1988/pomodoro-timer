# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Core Commands

### Development & Testing
```bash
# Run the application
python3 main.py

# Run tests
python3 -m pytest tests/ -v

# Run specific test file
python3 -m pytest tests/test_timer.py -v

# Code formatting
black src/ tests/ main.py

# Type checking
mypy src/ --ignore-missing-imports

# Linting
pylint src/
```

### Building the macOS App
```bash
# Build .app bundle (creates in dist/)
python3 setup.py py2app

# Clean build artifacts
rm -rf build dist
```

## Architecture Overview

### Application Structure
This is a macOS menu bar Pomodoro timer application using the MVC pattern with Observer for state management:

- **Menu Bar UI Layer** (`src/menu_bar_app.py`): rumps.App-based UI that runs exclusively in the menu bar (LSUIElement=True), handles all user interactions
- **Timer Core** (`src/pomodoro_timer.py`): State machine managing timer logic, work/break cycles, and pomodoro counting
- **Data Persistence**: 
  - Configuration in `~/.config/pomodoro-timer/config.json` via `ConfigManager`
  - Session statistics in SQLite database via `StatisticsDB`
- **Notification System**: Native macOS notifications with custom completion dialogs using PyObjC/AppKit

### Key Design Patterns
1. **Thread Safety**: Timer runs in separate thread with proper locking for UI updates
2. **PyObjC Integration**: Custom dialogs use AppKit directly for native macOS experience
3. **State Management**: Enum-based state machine (IDLE, WORKING, BREAK, LONG_BREAK, PAUSED)
4. **Dynamic Icons**: Real-time progress indication using clock emojis (🕐-🕧) during work sessions

### Critical Implementation Details
- Button actions in PyObjC dialogs must use proper selector signatures to prevent crashes
- Float minute values need explicit integer conversion when creating time strings
- Thread safety is essential - all timer callbacks must use main thread for UI updates
- The app must hide from dock (LSUIElement=True) for true menu bar experience

## Dependencies
- **rumps**: Menu bar framework (v0.4.0)
- **Pillow**: Icon generation (v10.2.0)  
- **PyObjC**: Native macOS dialogs (bundled with macOS Python)
- **pytest**: Testing framework with mock and coverage plugins

## Database Schema
Sessions table tracks all timer activity:
- `session_type`: 'work', 'short_break', 'long_break'
- `start_time`, `end_time`: Timestamps for duration calculation
- `completed`: Boolean for session completion status
- `extend_count`: Number of times session was extended