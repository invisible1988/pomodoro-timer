"""Test suite for PomodoroTimer class."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from src.constants import TimerState
from src.exceptions import TimerStateError


class TestPomodoroTimer:
    """Test cases for PomodoroTimer functionality."""
    
    def test_timer_initialization(self):
        """Test timer initializes with correct default values."""
        from src.pomodoro_timer import PomodoroTimer
        
        timer = PomodoroTimer()
        assert timer.state == TimerState.IDLE
        assert timer.work_minutes == 25
        assert timer.short_break_minutes == 5
        assert timer.long_break_minutes == 15
        assert timer.pomodoros_until_long_break == 4
        assert timer.completed_pomodoros == 0
        assert timer.remaining_seconds == 0
        assert timer.total_seconds == 0
    
    def test_timer_initialization_with_custom_values(self):
        """Test timer accepts custom duration values."""
        from src.pomodoro_timer import PomodoroTimer
        
        timer = PomodoroTimer(
            work_minutes=30,
            short_break_minutes=10,
            long_break_minutes=20,
            pomodoros_until_long_break=3
        )
        assert timer.work_minutes == 30
        assert timer.short_break_minutes == 10
        assert timer.long_break_minutes == 20
        assert timer.pomodoros_until_long_break == 3
    
    def test_start_work_session(self):
        """Test starting a work session."""
        from src.pomodoro_timer import PomodoroTimer
        
        timer = PomodoroTimer()
        timer.start_work()
        
        assert timer.state == TimerState.WORKING
        assert timer.remaining_seconds == 25 * 60
        assert timer.total_seconds == 25 * 60
    
    def test_start_work_from_invalid_state(self):
        """Test that starting work from working state raises error."""
        from src.pomodoro_timer import PomodoroTimer
        
        timer = PomodoroTimer()
        timer.start_work()
        
        with pytest.raises(TimerStateError):
            timer.start_work()
    
    def test_tick_decrements_time(self):
        """Test that tick decrements remaining time."""
        from src.pomodoro_timer import PomodoroTimer
        
        timer = PomodoroTimer()
        timer.start_work()
        initial_time = timer.remaining_seconds
        
        timer.tick()
        assert timer.remaining_seconds == initial_time - 1
    
    def test_tick_when_idle_does_nothing(self):
        """Test that tick in idle state doesn't change anything."""
        from src.pomodoro_timer import PomodoroTimer
        
        timer = PomodoroTimer()
        timer.tick()
        assert timer.remaining_seconds == 0
        assert timer.state == TimerState.IDLE
    
    def test_timer_completion(self):
        """Test timer completion triggers callback."""
        from src.pomodoro_timer import PomodoroTimer
        
        timer = PomodoroTimer()
        callback = Mock()
        timer.on_timer_complete = callback
        
        timer.start_work()
        timer.remaining_seconds = 1  # Set to 1 second remaining
        timer.tick()
        
        assert timer.state == TimerState.IDLE
        assert timer.remaining_seconds == 0
        callback.assert_called_once()
    
    def test_pause_and_resume(self):
        """Test pausing and resuming timer."""
        from src.pomodoro_timer import PomodoroTimer
        
        timer = PomodoroTimer()
        timer.start_work()
        
        timer.pause()
        assert timer.state == TimerState.PAUSED
        previous_state = timer.previous_state
        assert previous_state == TimerState.WORKING
        
        timer.resume()
        assert timer.state == TimerState.WORKING
    
    def test_reset_timer(self):
        """Test resetting timer to idle state."""
        from src.pomodoro_timer import PomodoroTimer
        
        timer = PomodoroTimer()
        timer.start_work()
        timer.tick()
        timer.tick()
        
        timer.reset()
        assert timer.state == TimerState.IDLE
        assert timer.remaining_seconds == 0
        assert timer.completed_pomodoros == 0
    
    def test_stop_timer(self):
        """Test stopping timer."""
        from src.pomodoro_timer import PomodoroTimer
        
        timer = PomodoroTimer()
        timer.start_work()
        
        timer.stop()
        assert timer.state == TimerState.IDLE
        assert timer.remaining_seconds == 0
    
    def test_work_completion_increments_pomodoro_count(self):
        """Test that completing work session increments pomodoro count."""
        from src.pomodoro_timer import PomodoroTimer
        
        timer = PomodoroTimer()
        timer.start_work()
        timer.remaining_seconds = 1
        timer.tick()
        
        assert timer.completed_pomodoros == 1
    
    def test_start_short_break(self):
        """Test starting a short break."""
        from src.pomodoro_timer import PomodoroTimer
        
        timer = PomodoroTimer()
        timer.completed_pomodoros = 1
        timer.start_break()
        
        assert timer.state == TimerState.SHORT_BREAK
        assert timer.remaining_seconds == 5 * 60
    
    def test_start_long_break_after_pomodoros(self):
        """Test long break starts after specified pomodoros."""
        from src.pomodoro_timer import PomodoroTimer
        
        timer = PomodoroTimer()
        timer.completed_pomodoros = 4
        timer.start_break()
        
        assert timer.state == TimerState.LONG_BREAK
        assert timer.remaining_seconds == 15 * 60
    
    def test_long_break_resets_pomodoro_count(self):
        """Test that completing long break resets pomodoro count."""
        from src.pomodoro_timer import PomodoroTimer
        
        timer = PomodoroTimer()
        timer.completed_pomodoros = 4
        timer.start_break()
        timer.remaining_seconds = 1
        timer.tick()
        
        assert timer.completed_pomodoros == 0
    
    def test_get_progress_percentage(self):
        """Test calculating progress percentage."""
        from src.pomodoro_timer import PomodoroTimer
        
        timer = PomodoroTimer()
        timer.start_work()
        
        # Full time remaining
        assert timer.get_progress_percentage() == 0
        
        # Half time elapsed
        timer.remaining_seconds = timer.total_seconds // 2
        assert timer.get_progress_percentage() == 50
        
        # Almost complete
        timer.remaining_seconds = 1
        assert timer.get_progress_percentage() == 99
    
    def test_get_time_remaining_string(self):
        """Test formatting remaining time as string."""
        from src.pomodoro_timer import PomodoroTimer
        
        timer = PomodoroTimer()
        timer.start_work()
        
        # Test initial time
        assert timer.get_time_remaining_string() == "25:00"
        
        # Test with seconds
        timer.remaining_seconds = 90
        assert timer.get_time_remaining_string() == "01:30"
        
        # Test under a minute
        timer.remaining_seconds = 45
        assert timer.get_time_remaining_string() == "00:45"
    
    def test_extend_timer(self):
        """Test extending timer by 5 minutes."""
        from src.pomodoro_timer import PomodoroTimer
        
        timer = PomodoroTimer()
        timer.start_work()
        initial_time = timer.remaining_seconds
        
        timer.extend(5)
        assert timer.remaining_seconds == initial_time + (5 * 60)
        assert timer.total_seconds == timer.total_seconds
    
    def test_skip_break(self):
        """Test skipping break and starting work."""
        from src.pomodoro_timer import PomodoroTimer
        
        timer = PomodoroTimer()
        timer.completed_pomodoros = 1
        timer.start_break()
        
        timer.skip_break()
        assert timer.state == TimerState.IDLE
        # Pomodoro count should remain for short break
        assert timer.completed_pomodoros == 1
        
        # Test skipping long break resets counter
        timer.completed_pomodoros = 4
        timer.start_break()  # This will be a long break
        assert timer.state == TimerState.LONG_BREAK
        
        timer.skip_break()
        assert timer.state == TimerState.IDLE
        # Pomodoro count should reset after skipping long break
        assert timer.completed_pomodoros == 0
    
    def test_is_break_time(self):
        """Test checking if it's time for a break."""
        from src.pomodoro_timer import PomodoroTimer
        
        timer = PomodoroTimer()
        
        # Not break time initially
        assert not timer.is_break_time()
        
        # After completing a pomodoro
        timer.completed_pomodoros = 1
        assert timer.is_break_time()
        
        # Long break time
        timer.completed_pomodoros = 4
        assert timer.is_long_break_time()
    
    def test_state_change_callback(self):
        """Test that state changes trigger callback."""
        from src.pomodoro_timer import PomodoroTimer
        
        timer = PomodoroTimer()
        callback = Mock()
        timer.on_state_change = callback
        
        timer.start_work()
        callback.assert_called_with(TimerState.IDLE, TimerState.WORKING)
        
        timer.pause()
        callback.assert_called_with(TimerState.WORKING, TimerState.PAUSED)
    
    def test_tick_callback(self):
        """Test that tick triggers callback."""
        from src.pomodoro_timer import PomodoroTimer
        
        timer = PomodoroTimer()
        callback = Mock()
        timer.on_tick = callback
        
        timer.start_work()
        timer.tick()
        
        callback.assert_called_with(timer.remaining_seconds)
    
    def test_invalid_timer_values(self):
        """Test that invalid timer values raise errors."""
        from src.pomodoro_timer import PomodoroTimer
        
        with pytest.raises(ValueError):
            PomodoroTimer(work_minutes=0)
        
        with pytest.raises(ValueError):
            PomodoroTimer(work_minutes=-5)
        
        with pytest.raises(ValueError):
            PomodoroTimer(pomodoros_until_long_break=0)