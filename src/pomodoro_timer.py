"""Core Pomodoro timer logic."""

import time
from typing import Optional, Callable
from src.constants import (
    TimerState,
    DEFAULT_WORK_MINUTES,
    DEFAULT_SHORT_BREAK_MINUTES,
    DEFAULT_LONG_BREAK_MINUTES,
    DEFAULT_POMODOROS_UNTIL_LONG_BREAK
)
from src.exceptions import TimerStateError


class PomodoroTimer:
    """Manages the Pomodoro timer state and logic."""
    
    def __init__(
        self,
        work_minutes: float = DEFAULT_WORK_MINUTES,
        short_break_minutes: float = DEFAULT_SHORT_BREAK_MINUTES,
        long_break_minutes: float = DEFAULT_LONG_BREAK_MINUTES,
        pomodoros_until_long_break: int = DEFAULT_POMODOROS_UNTIL_LONG_BREAK
    ):
        """Initialize the Pomodoro timer.
        
        Args:
            work_minutes: Duration of work sessions in minutes (can be fractional)
            short_break_minutes: Duration of short breaks in minutes (can be fractional)
            long_break_minutes: Duration of long breaks in minutes (can be fractional)
            pomodoros_until_long_break: Number of pomodoros before a long break
        
        Raises:
            ValueError: If any duration is <= 0
        """
        if work_minutes <= 0:
            raise ValueError("Work minutes must be positive")
        if short_break_minutes <= 0:
            raise ValueError("Short break minutes must be positive")
        if long_break_minutes <= 0:
            raise ValueError("Long break minutes must be positive")
        if pomodoros_until_long_break <= 0:
            raise ValueError("Pomodoros until long break must be positive")
        
        self.work_minutes = work_minutes
        self.short_break_minutes = short_break_minutes
        self.long_break_minutes = long_break_minutes
        self.pomodoros_until_long_break = pomodoros_until_long_break
        
        self.state = TimerState.IDLE
        self.previous_state: Optional[TimerState] = None
        self.completed_pomodoros = 0
        self.remaining_seconds = 0
        self.total_seconds = 0
        
        # Session tracking
        self.current_session_id: Optional[int] = None
        self.last_session_id: Optional[int] = None
        self.extend_count = 0
        self.last_completed_session: Optional[TimerState] = None
        
        # Pause tracking
        self.pause_start_time: Optional[float] = None  # When pause started (time.time())
        self.total_pause_seconds: int = 0  # Total seconds spent paused in current session
        self.pause_count: int = 0  # Number of times paused in current session
        self.session_start_seconds: int = 0  # Initial duration when session started
        
        # Callbacks
        self.on_timer_complete: Optional[Callable[[], None]] = None
        self.on_state_change: Optional[Callable[[TimerState, TimerState], None]] = None
        self.on_tick: Optional[Callable[[int], None]] = None
        self.on_session_start: Optional[Callable[[str, int], int]] = None
        self.on_session_end: Optional[Callable[[bool], None]] = None
        self.on_extend: Optional[Callable[[], None]] = None
    
    def _change_state(self, new_state: TimerState) -> None:
        """Change the timer state and trigger callback.
        
        Args:
            new_state: The new timer state
        """
        old_state = self.state
        self.state = new_state
        
        if self.on_state_change:
            self.on_state_change(old_state, new_state)
    
    def start_work(self) -> None:
        """Start a work session.
        
        Raises:
            TimerStateError: If not in IDLE state
        """
        if self.state != TimerState.IDLE:
            raise TimerStateError(f"Cannot start work from {self.state} state")
        
        self.total_seconds = int(self.work_minutes * 60)
        self.remaining_seconds = self.total_seconds
        self.extend_count = 0
        
        # Reset pause tracking for new session
        self.pause_start_time = None
        self.total_pause_seconds = 0
        self.pause_count = 0
        self.session_start_seconds = self.remaining_seconds
        
        # Start session tracking
        if self.on_session_start:
            self.current_session_id = self.on_session_start('work', self.work_minutes)
        
        self._change_state(TimerState.WORKING)
    
    def start_break(self) -> None:
        """Start a break session (short or long based on completed pomodoros)."""
        # Reset pause tracking for new session
        self.pause_start_time = None
        self.total_pause_seconds = 0
        self.pause_count = 0
        
        
        if self.is_long_break_time():
            self.total_seconds = int(self.long_break_minutes * 60)
            session_type = 'long_break'
            planned_duration = self.long_break_minutes
            self._change_state(TimerState.LONG_BREAK)
        else:
            self.total_seconds = int(self.short_break_minutes * 60)
            session_type = 'short_break'
            planned_duration = self.short_break_minutes
            self._change_state(TimerState.SHORT_BREAK)
        
        self.remaining_seconds = self.total_seconds
        self.extend_count = 0
        self.session_start_seconds = self.remaining_seconds
        
        # Start session tracking
        if self.on_session_start:
            self.current_session_id = self.on_session_start(session_type, planned_duration)
    
    def tick(self) -> None:
        """Decrement the timer by one second."""
        if self.state in (TimerState.WORKING, TimerState.SHORT_BREAK, TimerState.LONG_BREAK):
            self.remaining_seconds -= 1
            
            if self.on_tick:
                self.on_tick(self.remaining_seconds)
            
            if self.remaining_seconds <= 0:
                self._handle_timer_complete()
    
    def _handle_timer_complete(self) -> None:
        """Handle timer completion."""
        was_working = self.state == TimerState.WORKING
        was_long_break = self.state == TimerState.LONG_BREAK
        was_short_break = self.state == TimerState.SHORT_BREAK
        
        # Store the completed session type and ID before changing state
        self.last_completed_session = self.state
        self.last_session_id = self.current_session_id
        
        # End session tracking
        if self.on_session_end:
            self.on_session_end(True)  # completed=True
        
        if was_working:
            self.completed_pomodoros += 1
        elif was_long_break:
            self.completed_pomodoros = 0
        
        self._change_state(TimerState.IDLE)
        self.remaining_seconds = 0
        
        if self.on_timer_complete:
            self.on_timer_complete()
    
    def pause(self) -> None:
        """Pause the timer."""
        if self.state in (TimerState.WORKING, TimerState.SHORT_BREAK, TimerState.LONG_BREAK):
            self.previous_state = self.state
            self._change_state(TimerState.PAUSED)
            # Track when pause started
            self.pause_start_time = time.time()
            self.pause_count += 1
    
    def resume(self) -> None:
        """Resume the timer from paused state."""
        if self.state == TimerState.PAUSED and self.previous_state:
            # Calculate pause duration and add to total
            if self.pause_start_time:
                pause_duration = int(time.time() - self.pause_start_time)
                self.total_pause_seconds += pause_duration
                self.pause_start_time = None
            
            self._change_state(self.previous_state)
            self.previous_state = None
    
    def stop(self) -> None:
        """Stop the timer and return to idle state."""
        # If currently paused, count that pause time
        if self.state == TimerState.PAUSED and self.pause_start_time:
            pause_duration = int(time.time() - self.pause_start_time)
            self.total_pause_seconds += pause_duration
            self.pause_start_time = None
        
        # End session tracking as interrupted
        if self.on_session_end and self.current_session_id:
            self.on_session_end(False)  # completed=False
        
        self._change_state(TimerState.IDLE)
        self.remaining_seconds = 0
        self.current_session_id = None
    
    def reset(self) -> None:
        """Reset the timer completely."""
        # If currently paused, count that pause time
        if self.state == TimerState.PAUSED and self.pause_start_time:
            pause_duration = int(time.time() - self.pause_start_time)
            self.total_pause_seconds += pause_duration
            self.pause_start_time = None
        
        # End session tracking as interrupted if active
        if self.on_session_end and self.current_session_id:
            self.on_session_end(False)  # completed=False
        
        self._change_state(TimerState.IDLE)
        self.remaining_seconds = 0
        self.total_seconds = 0
        self.completed_pomodoros = 0
        self.previous_state = None
        self.current_session_id = None
        self.extend_count = 0
        
        # Reset pause tracking
        self.total_pause_seconds = 0
        self.pause_count = 0
        self.session_start_seconds = 0
    
    def extend(self, minutes: float) -> None:
        """Extend the current timer by specified minutes.
        
        Args:
            minutes: Number of minutes to add (can be fractional)
        """
        if self.state in (TimerState.WORKING, TimerState.SHORT_BREAK, TimerState.LONG_BREAK):
            self.remaining_seconds += int(minutes * 60)
            self.extend_count += 1
            
            # Track extend in database
            if self.on_extend:
                self.on_extend()
    
    def extend_completed_session(self, minutes: float, session_id: int) -> None:
        """Extend a session that just completed by reopening it.
        
        Args:
            minutes: Number of minutes to add (can be fractional)
            session_id: The session ID to reopen and extend
        """
        if self.state != TimerState.IDLE:
            return
        
        if self.last_completed_session == TimerState.WORKING:
            self._change_state(TimerState.WORKING)
        elif self.last_completed_session == TimerState.SHORT_BREAK:
            self._change_state(TimerState.SHORT_BREAK)
        elif self.last_completed_session == TimerState.LONG_BREAK:
            self._change_state(TimerState.LONG_BREAK)
        else:
            return
        
        # Set the timer with just the extension time
        self.remaining_seconds = int(minutes * 60)
        self.total_seconds = int(minutes * 60)
        self.current_session_id = session_id
        self.extend_count += 1
    
    def skip_break(self) -> None:
        """Skip the current break."""
        if self.state in (TimerState.SHORT_BREAK, TimerState.LONG_BREAK):
            # If skipping a long break, reset the pomodoro counter
            # Otherwise we'll get another long break after the next work session
            if self.state == TimerState.LONG_BREAK:
                self.completed_pomodoros = 0
            
            # End session tracking as interrupted
            if self.on_session_end and self.current_session_id:
                self.on_session_end(False)  # completed=False
            
            self._change_state(TimerState.IDLE)
            self.remaining_seconds = 0
            self.current_session_id = None
    
    def is_break_time(self) -> bool:
        """Check if it's time for a break.
        
        Returns:
            True if completed pomodoros > 0
        """
        return self.completed_pomodoros > 0
    
    def is_long_break_time(self) -> bool:
        """Check if it's time for a long break.
        
        Returns:
            True if completed pomodoros equals or exceeds pomodoros_until_long_break
        """
        return self.completed_pomodoros >= self.pomodoros_until_long_break and self.completed_pomodoros > 0
    
    def get_progress_percentage(self) -> int:
        """Get the progress percentage of the current timer.
        
        Returns:
            Progress percentage (0-100)
        """
        if not self.total_seconds or self.total_seconds == 0:
            return 0
        
        if self.remaining_seconds is None or self.remaining_seconds < 0:
            return 100
        
        elapsed = self.total_seconds - self.remaining_seconds
        percentage = int((elapsed / self.total_seconds) * 100)
        return min(max(percentage, 0), 100)
    
    def get_actual_worked_seconds(self) -> int:
        """Get the actual time worked/breaked, excluding pause time.
        
        Returns:
            Actual seconds of active timer time (not including pauses)
        """
        if self.session_start_seconds == 0:
            return 0
        
        # Calculate how much time has actually been consumed
        time_consumed = self.session_start_seconds - self.remaining_seconds
        
        # Don't count paused time
        actual_worked = time_consumed - self.total_pause_seconds
        
        # If currently paused, also subtract current pause duration
        if self.state == TimerState.PAUSED and self.pause_start_time:
            current_pause = int(time.time() - self.pause_start_time)
            actual_worked -= current_pause
        
        return max(0, actual_worked)
    
    def get_time_remaining_string(self) -> str:
        """Get formatted string of remaining time.
        
        Returns:
            Time string in MM:SS format
        """
        # Handle edge cases
        if self.remaining_seconds is None or self.remaining_seconds < 0:
            return "00:00"
        
        minutes = int(self.remaining_seconds // 60)
        seconds = int(self.remaining_seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"