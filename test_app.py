#!/usr/bin/env python3
"""Quick test script to verify Pomodoro Timer functionality."""

import time
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pomodoro_timer import PomodoroTimer, TimerState
from config_manager import ConfigManager
from statistics_db import StatisticsDB
from pathlib import Path

def test_timer():
    """Test basic timer functionality."""
    print("Testing Pomodoro Timer Core...")
    
    # Test timer initialization
    timer = PomodoroTimer(work_minutes=25, short_break_minutes=5, long_break_minutes=15)
    assert timer.state == TimerState.IDLE
    print("✅ Timer initialization")
    
    # Test starting work
    timer.start_work()
    assert timer.state == TimerState.WORKING
    assert timer.remaining_seconds == 25 * 60
    print("✅ Start work session")
    
    # Test pause/resume
    timer.pause()
    assert timer.state == TimerState.PAUSED
    timer.resume()
    assert timer.state == TimerState.WORKING
    print("✅ Pause/Resume")
    
    # Test stop
    timer.stop()
    assert timer.state == TimerState.IDLE
    print("✅ Stop timer")
    
    # Test break
    timer.start_break()
    assert timer.state in (TimerState.SHORT_BREAK, TimerState.LONG_BREAK)
    print("✅ Start break")
    
    return True

def test_config():
    """Test configuration management."""
    print("\nTesting Configuration Manager...")
    
    config = ConfigManager()
    
    # Test loading config
    assert config.get('current_profile') is not None
    print("✅ Load configuration")
    
    # Test profile access
    profiles = config.get_profiles()
    assert 'default' in profiles
    print("✅ Access profiles")
    
    # Test getting timer values
    work_minutes = config.get('timers.work_minutes')
    assert work_minutes > 0
    print("✅ Get timer values")
    
    return True

def test_database():
    """Test database functionality."""
    print("\nTesting Statistics Database...")
    
    db_path = Path.home() / '.config' / 'pomodoro-timer' / 'test_stats.db'
    db = StatisticsDB(db_path)
    
    # Test starting a session
    session_id = db.start_session('work', 25, 'default')
    assert session_id is not None
    print("✅ Start session")
    
    # Test ending a session
    db.end_session(session_id, completed=True)
    print("✅ End session")
    
    # Test getting stats
    today_stats = db.get_today_stats()
    assert 'completed_pomodoros' in today_stats
    print("✅ Get statistics")
    
    # Clean up test database
    db_path.unlink(missing_ok=True)
    
    return True

def main():
    """Run all tests."""
    print("=" * 50)
    print("POMODORO TIMER FUNCTIONALITY TEST")
    print("=" * 50)
    
    try:
        # Test core components
        test_timer()
        test_config()
        test_database()
        
        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED!")
        print("=" * 50)
        print("\nThe app should be running in your menu bar.")
        print("Look for the 🍅 icon and click it to access controls.")
        print("\nAvailable actions:")
        print("- Start (25 min) - Begin a work session")
        print("- Pause/Resume - Control the running timer")
        print("- Stop - End the current session")
        print("- Reset - Reset all progress")
        print("- Extend X min - Add time to current session")
        print("- Skip Break - Skip break and start work")
        print("- Switch Profile - Change timer settings")
        print("- Settings - Configure timer durations")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())