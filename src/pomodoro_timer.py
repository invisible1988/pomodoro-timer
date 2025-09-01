"""Core Pomodoro timer logic."""

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
        work_minutes: int = DEFAULT_WORK_MINUTES,
        short_break_minutes: int = DEFAULT_SHORT_BREAK_MINUTES,
        long_break_minutes: int = DEFAULT_LONG_BREAK_MINUTES,
        pomodoros_until_long_break: int = DEFAULT_POMODOROS_UNTIL_LONG_BREAK
    ):
        """Initialize the Pomodoro timer.
        
        Args:
            work_minutes: Duration of work sessions in minutes
            short_break_minutes: Duration of short breaks in minutes
            long_break_minutes: Duration of long breaks in minutes
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
        
        # Callbacks
        self.on_timer_complete: Optional[Callable[[], None]] = None
        self.on_state_change: Optional[Callable[[TimerState, TimerState], None]] = None
        self.on_tick: Optional[Callable[[int], None]] = None
    
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
        
        self.total_seconds = self.work_minutes * 60
        self.remaining_seconds = self.total_seconds
        self._change_state(TimerState.WORKING)
    
    def start_break(self) -> None:
        """Start a break session (short or long based on completed pomodoros)."""
        if self.is_long_break_time():
            self.total_seconds = self.long_break_minutes * 60
            self._change_state(TimerState.LONG_BREAK)
        else:
            self.total_seconds = self.short_break_minutes * 60
            self._change_state(TimerState.SHORT_BREAK)
        
        self.remaining_seconds = self.total_seconds
    
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
    
    def resume(self) -> None:
        """Resume the timer from paused state."""
        if self.state == TimerState.PAUSED and self.previous_state:
            self._change_state(self.previous_state)
            self.previous_state = None
    
    def stop(self) -> None:
        """Stop the timer and return to idle state."""
        self._change_state(TimerState.IDLE)
        self.remaining_seconds = 0
    
    def reset(self) -> None:
        """Reset the timer completely."""
        self._change_state(TimerState.IDLE)
        self.remaining_seconds = 0
        self.total_seconds = 0
        self.completed_pomodoros = 0
        self.previous_state = None
    
    def extend(self, minutes: int) -> None:
        """Extend the current timer by specified minutes.
        
        Args:
            minutes: Number of minutes to add
        """
        if self.state in (TimerState.WORKING, TimerState.SHORT_BREAK, TimerState.LONG_BREAK):
            self.remaining_seconds += minutes * 60
    
    def skip_break(self) -> None:
        """Skip the current break."""
        if self.state in (TimerState.SHORT_BREAK, TimerState.LONG_BREAK):
            self._change_state(TimerState.IDLE)
            self.remaining_seconds = 0
    
    def is_break_time(self) -> bool:
        """Check if it's time for a break.
        
        Returns:
            True if completed pomodoros > 0
        """
        return self.completed_pomodoros > 0
    
    def is_long_break_time(self) -> bool:
        """Check if it's time for a long break.
        
        Returns:
            True if completed pomodoros equals pomodoros_until_long_break
        """
        return self.completed_pomodoros >= self.pomodoros_until_long_break
    
    def get_progress_percentage(self) -> int:
        """Get the progress percentage of the current timer.
        
        Returns:
            Progress percentage (0-100)
        """
        if self.total_seconds == 0:
            return 0
        
        elapsed = self.total_seconds - self.remaining_seconds
        percentage = int((elapsed / self.total_seconds) * 100)
        return min(percentage, 100)
    
    def get_time_remaining_string(self) -> str:
        """Get formatted string of remaining time.
        
        Returns:
            Time string in MM:SS format
        """
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"