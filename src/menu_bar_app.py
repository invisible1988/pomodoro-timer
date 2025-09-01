"""Main menu bar application for Pomodoro Timer."""

import rumps
import os
from datetime import datetime
from src.pomodoro_timer import PomodoroTimer
from src.icon_generator import IconGenerator
from src.config_manager import ConfigManager
from src.notification_manager import NotificationManager
from src.constants import (
    APP_NAME,
    TimerState,
    MENU_START,
    MENU_STOP,
    MENU_RESET,
    MENU_PAUSE,
    MENU_RESUME,
    MENU_SETTINGS,
    MENU_QUIT,
    NOTIFICATION_WORK_COMPLETE,
    NOTIFICATION_BREAK_COMPLETE,
    NOTIFICATION_LONG_BREAK_COMPLETE
)


class PomodoroMenuBarApp(rumps.App):
    """Menu bar application for Pomodoro Timer."""
    
    def __init__(self):
        """Initialize the menu bar application."""
        # Initialize with simple title first
        super().__init__("PT", quit_button=None)
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.timer = PomodoroTimer(
            work_minutes=self.config_manager.get('timers.work_minutes'),
            short_break_minutes=self.config_manager.get('timers.short_break_minutes'),
            long_break_minutes=self.config_manager.get('timers.long_break_minutes'),
            pomodoros_until_long_break=self.config_manager.get('timers.pomodoros_until_long_break')
        )
        self.icon_generator = IconGenerator()
        self.notification_manager = NotificationManager(self.config_manager)
        
        # Set up callbacks
        self.timer.on_tick = self._on_timer_tick
        self.timer.on_timer_complete = self._on_timer_complete
        self.timer.on_state_change = self._on_state_change
        
        # Set up menu
        self._setup_menu()
        
        # Update icon
        self._update_icon()
        
        # Start timer loop
        rumps.Timer(self._timer_loop, 1).start()
    
    def _setup_menu(self):
        """Set up the menu items."""
        self.menu.clear()
        
        # Time display (non-clickable)
        time_display = rumps.MenuItem("Ready", callback=None)
        time_display.set_callback(None)
        self.menu.add(time_display)
        
        # Separator
        self.menu.add(rumps.separator)
        
        # Control buttons
        if self.timer.state == TimerState.IDLE:
            self.menu.add(rumps.MenuItem(MENU_START, self.start_timer))
        elif self.timer.state == TimerState.PAUSED:
            self.menu.add(rumps.MenuItem(MENU_RESUME, self.resume_timer))
            self.menu.add(rumps.MenuItem(MENU_STOP, self.stop_timer))
        else:
            self.menu.add(rumps.MenuItem(MENU_PAUSE, self.pause_timer))
            self.menu.add(rumps.MenuItem(MENU_STOP, self.stop_timer))
        
        self.menu.add(rumps.MenuItem(MENU_RESET, self.reset_timer))
        
        # Separator
        self.menu.add(rumps.separator)
        
        # Quick actions
        if self.timer.state in (TimerState.WORKING, TimerState.SHORT_BREAK, TimerState.LONG_BREAK):
            extend_minutes = self.config_manager.get('timers.extend_minutes', 5)
            self.menu.add(rumps.MenuItem(f"Extend {extend_minutes} min", self.extend_timer))
        
        if self.timer.state in (TimerState.SHORT_BREAK, TimerState.LONG_BREAK):
            self.menu.add(rumps.MenuItem("Skip Break", self.skip_break))
        
        # Settings
        self.menu.add(rumps.MenuItem(MENU_SETTINGS, self.show_settings))
        
        # Statistics
        total_pomodoros = self.config_manager.get('statistics.total_pomodoros', 0)
        daily_goal = self.config_manager.get('statistics.daily_goal', 8)
        stats_text = f"Today: {self.timer.completed_pomodoros}/{daily_goal} | Total: {total_pomodoros}"
        stats_item = rumps.MenuItem(stats_text, callback=None)
        self.menu.add(stats_item)
        
        # Separator
        self.menu.add(rumps.separator)
        
        # Quit
        self.menu.add(rumps.MenuItem(MENU_QUIT, rumps.quit_application))
    
    def _timer_loop(self, _):
        """Timer loop that runs every second."""
        self.timer.tick()
    
    def _on_timer_tick(self, remaining_seconds: int):
        """Handle timer tick events."""
        self._update_time_display()
        # Update icon every second for real-time feedback
        self._update_icon()
    
    def _on_timer_complete(self):
        """Handle timer completion."""
        # Update statistics if work session completed
        if self.timer.completed_pomodoros > 0:
            self.config_manager.update_statistics(
                pomodoros=1,
                work_minutes=self.timer.work_minutes
            )
        
        # Show appropriate dialog
        if self.timer.state == TimerState.IDLE:
            # Work session completed
            if self.timer.is_break_time():
                extend_minutes = self.config_manager.get('timers.extend_minutes', 5)
                self.notification_manager.show_work_complete_dialog(
                    on_break=self._start_break,
                    on_extend=lambda: self._extend_current(extend_minutes),
                    on_skip=self._skip_to_work,
                    extend_minutes=extend_minutes
                )
            else:
                # All pomodoros done
                self.notification_manager.show_notification(
                    "All Done!",
                    "Great work! You've completed your pomodoro session."
                )
        
        self._setup_menu()
        self._update_icon()
    
    def _on_state_change(self, old_state: TimerState, new_state: TimerState):
        """Handle state change events."""
        self._setup_menu()
        self._update_time_display()
        self._update_icon()
    
    def _update_time_display(self):
        """Update the time display in the menu."""
        if self.timer.state == TimerState.IDLE:
            display_text = "Ready"
        elif self.timer.state == TimerState.PAUSED:
            display_text = f"Paused - {self.timer.get_time_remaining_string()}"
        elif self.timer.state == TimerState.WORKING:
            display_text = f"Work - {self.timer.get_time_remaining_string()}"
        elif self.timer.state in (TimerState.SHORT_BREAK, TimerState.LONG_BREAK):
            display_text = f"Break - {self.timer.get_time_remaining_string()}"
        else:
            display_text = self.timer.get_time_remaining_string()
        
        # Update first menu item
        if self.menu.values():
            first_item = list(self.menu.values())[0]
            first_item.title = display_text
    
    def _update_icon(self):
        """Update the menu bar icon."""
        icon_style = self.config_manager.get('appearance.menu_bar_icon_style', 'emoji')
        
        if icon_style == 'emoji':
            # Use emoji icons with visual progress
            self._update_emoji_icon()
        elif icon_style == 'progress':
            # Try to use image icon files
            try:
                progress = self.timer.get_progress_percentage()
                icon_path = self.icon_generator.get_icon_path(
                    progress=progress,
                    state=self.timer.state,
                    use_template=True
                )
                
                if icon_path and os.path.exists(icon_path):
                    self.icon = icon_path
                    if self.timer.state in (TimerState.WORKING, TimerState.SHORT_BREAK, TimerState.LONG_BREAK):
                        minutes = self.timer.remaining_seconds // 60
                        self.title = f"{minutes}m" if minutes > 0 else "< 1m"
                    else:
                        self.title = ""
                else:
                    self._update_text_icon()
            except Exception as e:
                print(f"Icon update error: {e}")
                self._update_text_icon()
        else:
            self._update_text_icon()
    
    def _update_emoji_icon(self):
        """Update with emoji icons showing visual progress."""
        progress = self.timer.get_progress_percentage()
        minutes = self.timer.remaining_seconds // 60
        
        if self.timer.state == TimerState.IDLE:
            # Use filled tomato when idle
            self.title = "🍅"
        elif self.timer.state == TimerState.PAUSED:
            # Paused state
            self.title = f"⏸ {minutes}"
        elif self.timer.state == TimerState.WORKING:
            # Work session - use clock faces to show progress
            # More time = darker/filled, less time = lighter/empty
            if progress < 25:
                clock = "🕐"  # 1 o'clock - just started
            elif progress < 50:
                clock = "🕓"  # 4 o'clock - quarter done
            elif progress < 75:
                clock = "🕕"  # 6 o'clock - half done
            else:
                clock = "🕘"  # 9 o'clock - almost done
            
            self.title = f"{clock} {minutes}"
            
        elif self.timer.state in (TimerState.SHORT_BREAK, TimerState.LONG_BREAK):
            # Break session - use different emoji
            if progress < 50:
                icon = "☕"  # Coffee for break
            else:
                icon = "✨"  # Almost done with break
            
            self.title = f"{icon} {minutes}"
    
    def _update_text_icon(self):
        """Update with text-based icon."""
        # Use text-only icons for compatibility
        if self.timer.state == TimerState.IDLE:
            self.title = "PT"  # Pomodoro Timer
        elif self.timer.state == TimerState.WORKING:
            minutes = self.timer.remaining_seconds // 60
            if minutes > 0:
                self.title = f"W:{minutes}"
            else:
                self.title = "W:0"
        elif self.timer.state in (TimerState.SHORT_BREAK, TimerState.LONG_BREAK):
            minutes = self.timer.remaining_seconds // 60
            if minutes > 0:
                self.title = f"B:{minutes}"
            else:
                self.title = "B:0"
        elif self.timer.state == TimerState.PAUSED:
            self.title = "||"
    
    def _start_break(self):
        """Start break session."""
        self.timer.start_break()
    
    def _extend_current(self, minutes: int):
        """Extend current timer."""
        self.timer.extend(minutes)
        self.notification_manager.show_notification(
            "Timer Extended",
            f"Added {minutes} minutes to current session"
        )
    
    def _skip_to_work(self):
        """Skip break and prepare for work."""
        if self.timer.state in (TimerState.SHORT_BREAK, TimerState.LONG_BREAK):
            self.timer.skip_break()
    
    @rumps.clicked(MENU_START)
    def start_timer(self, _):
        """Start the timer."""
        if self.timer.state == TimerState.IDLE:
            if self.timer.is_break_time():
                self.timer.start_break()
            else:
                self.timer.start_work()
    
    @rumps.clicked(MENU_STOP)
    def stop_timer(self, _):
        """Stop the timer."""
        self.timer.stop()
    
    @rumps.clicked(MENU_RESET)
    def reset_timer(self, _):
        """Reset the timer."""
        response = rumps.alert(
            title="Reset Timer?",
            message="This will reset all progress and pomodoro count.",
            ok="Reset",
            cancel="Cancel"
        )
        if response == 1:
            self.timer.reset()
    
    @rumps.clicked(MENU_PAUSE)
    def pause_timer(self, _):
        """Pause the timer."""
        self.timer.pause()
    
    @rumps.clicked(MENU_RESUME)
    def resume_timer(self, _):
        """Resume the timer."""
        self.timer.resume()
    
    def extend_timer(self, _):
        """Extend timer by configured minutes."""
        extend_minutes = self.config_manager.get('timers.extend_minutes', 5)
        self.timer.extend(extend_minutes)
        self.notification_manager.show_notification(
            "Timer Extended",
            f"Added {extend_minutes} minutes"
        )
    
    @rumps.clicked("Skip Break")
    def skip_break(self, _):
        """Skip the current break."""
        self.timer.skip_break()
    
    @rumps.clicked(MENU_SETTINGS)
    def show_settings(self, _):
        """Show settings dialog."""
        # Enhanced settings dialog
        current_settings = (
            f"Work: {self.config_manager.get('timers.work_minutes')} min\n"
            f"Short Break: {self.config_manager.get('timers.short_break_minutes')} min\n"
            f"Long Break: {self.config_manager.get('timers.long_break_minutes')} min\n"
            f"Extend Time: {self.config_manager.get('timers.extend_minutes')} min\n"
            f"Daily Goal: {self.config_manager.get('statistics.daily_goal')} pomodoros"
        )
        
        window = rumps.Window(
            title="Settings",
            message="Configure timer durations and goals:",
            default_text=current_settings,
            ok="Save",
            cancel="Cancel",
            dimensions=(400, 150)
        )
        
        response = window.run()
        if response.clicked:
            self._parse_settings(response.text)
    
    def _parse_settings(self, text: str):
        """Parse and apply settings from text input."""
        try:
            lines = text.strip().split('\n')
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value_str = value.strip().replace('min', '').replace('pomodoros', '').strip()
                    
                    try:
                        value = int(value_str)
                    except ValueError:
                        continue
                    
                    if 'work' in key:
                        self.config_manager.set('timers.work_minutes', value)
                        self.timer.work_minutes = value
                    elif 'short' in key:
                        self.config_manager.set('timers.short_break_minutes', value)
                        self.timer.short_break_minutes = value
                    elif 'long' in key:
                        self.config_manager.set('timers.long_break_minutes', value)
                        self.timer.long_break_minutes = value
                    elif 'extend' in key:
                        self.config_manager.set('timers.extend_minutes', value)
                    elif 'goal' in key:
                        self.config_manager.set('statistics.daily_goal', value)
            
            self.notification_manager.show_notification(
                "Settings Saved",
                "Timer settings have been updated"
            )
            
            # Refresh menu to show new settings
            self._setup_menu()
            
        except Exception as e:
            rumps.alert("Error", f"Invalid settings format: {e}")


def main():
    """Main entry point."""
    app = PomodoroMenuBarApp()
    
    # Hide from dock after app is created
    try:
        import AppKit
        AppKit.NSApp.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
    except:
        # If AppKit not available, app will still work but show in dock
        pass
    
    app.run()


if __name__ == "__main__":
    main()