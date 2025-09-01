# Pomodoro Timer - macOS Menu Bar App

A minimalist Pomodoro timer that lives in your macOS menu bar.

## Features

### Core Features
- 🍅 **Menu Bar Only** - Runs exclusively in menu bar (hidden from dock)
- ⏱️ **Dynamic Icon** - Shows work/break status with remaining minutes
- 🔔 **Smart Notifications** - Center-screen popups with sound alerts
- ⚙️ **Fully Customizable** - Configure all timer durations and goals
- 💾 **Persistent Settings** - Comprehensive configuration saved to JSON
- 📊 **Statistics Tracking** - Track daily and total pomodoros

### Enhanced Features
- **Configurable Extend Time** - Set custom extend minutes (not just 5)
- **Daily Goals** - Set and track daily pomodoro targets
- **Center-Screen Dialogs** - Beautiful popup notifications on completion
- **Sound Alerts** - System sounds play on timer completion
- **Auto-Hide from Dock** - True menu bar app experience
- **Smart Break Management** - Auto-detect short vs long breaks

## Quick Start

### Prerequisites
- macOS 10.15 or later
- Python 3.9+

### Installation

1. Clone the repository:
```bash
cd /Users/paul/Projects/pomodoro-timer
```

2. Install dependencies:
```bash
pip3 install rumps Pillow
```

3. Run the app:
```bash
python3 main.py
```

## Usage

1. Click the 🍅 icon in your menu bar
2. Select "Start" to begin a 25-minute work session
3. Take a 5-minute break when prompted
4. After 4 pomodoros, enjoy a 15-minute long break

### Controls

- **Start** - Begin work or break session
- **Pause/Resume** - Pause and resume timer
- **Stop** - Stop current session
- **Reset** - Reset all progress
- **Extend 5 min** - Add 5 minutes to current timer
- **Skip Break** - Skip break and prepare for work
- **Settings** - Configure timer durations

### Icon States

- **PT** - Idle/Ready (Pomodoro Timer)
- **W:25** - Working (25 minutes remaining)
- **B:5** - Break (5 minutes remaining)  
- **||** - Paused

## Configuration

Settings are saved to `~/.pomodoro-config.json`

Default durations:
- Work: 25 minutes
- Short Break: 5 minutes
- Long Break: 15 minutes
- Long Break After: 4 pomodoros

## Development

### Project Structure
```
pomodoro-timer/
├── src/
│   ├── pomodoro_timer.py    # Core timer logic
│   ├── menu_bar_app.py      # Menu bar UI
│   ├── icon_generator.py    # Dynamic icons
│   └── constants.py         # Configuration
├── tests/                    # Test suite
├── main.py                   # Entry point
└── SPECIFICATION.md          # Technical docs
```

### Running Tests
```bash
python3 -m pytest tests/ -v
```

## Building for Distribution

### Quick Build
```bash
./build.sh
```

### Manual Build
```bash
# Install py2app
pip3 install py2app

# Build the app
python3 setup.py py2app

# The app will be in dist/Pomodoro Timer.app
```

### Creating DMG
```bash
hdiutil create -volname "Pomodoro Timer" \
               -srcfolder dist \
               -ov -format UDZO \
               PomodoroTimer.dmg
```

## License

MIT License