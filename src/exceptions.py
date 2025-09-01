"""Custom exceptions for Pomodoro Timer."""


class PomodoroTimerError(Exception):
    """Base exception for Pomodoro Timer."""
    pass


class ConfigurationError(PomodoroTimerError):
    """Raised when there's an error with configuration."""
    pass


class TimerStateError(PomodoroTimerError):
    """Raised when timer state transition is invalid."""
    pass


class IconGenerationError(PomodoroTimerError):
    """Raised when icon generation fails."""
    pass


class NotificationError(PomodoroTimerError):
    """Raised when notification system fails."""
    pass