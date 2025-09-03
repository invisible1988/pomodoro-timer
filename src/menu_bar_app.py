"""Main menu bar application for Pomodoro Timer."""

import rumps
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from src.pomodoro_timer import PomodoroTimer
from src.config_manager import ConfigManager
from src.notification_manager import NotificationManager
from src.json_settings import JsonSettings
from src.statistics_db import StatisticsDB
from src.completion_dialog import CompletionDialog
from src.work_completion_dialog import WorkCompletionDialog
from src.break_completion_dialog import BreakCompletionDialog
from src.state_manager import StateManager
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
    NOTIFICATION_LONG_BREAK_COMPLETE,
    DB_FILE_PATH,
    DAILY_GOAL
)


class PomodoroMenuBarApp(rumps.App):
    """Menu bar application for Pomodoro Timer."""
    
    def __init__(self):
        """Initialize the menu bar application."""
        # Initialize with simple title first
        super().__init__("PT", quit_button=None)
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.statistics_db = StatisticsDB(DB_FILE_PATH)
        self.state_manager = StateManager()
        self.timer = PomodoroTimer(
            work_minutes=self.config_manager.get('timers.work_minutes'),
            short_break_minutes=self.config_manager.get('timers.short_break_minutes'),
            long_break_minutes=self.config_manager.get('timers.long_break_minutes'),
            pomodoros_until_long_break=self.config_manager.get('timers.pomodoros_until_long_break')
        )
        self.notification_manager = NotificationManager(self.config_manager)
        
        # Thread safety lock for timer operations - use RLock to allow reentrant locking
        self.timer_lock = threading.RLock()
        
        # Set up callbacks
        self.timer.on_tick = self._on_timer_tick
        self.timer.on_timer_complete = self._on_timer_complete
        self.timer.on_state_change = self._on_state_change
        # Pass profile name when starting sessions
        self.timer.on_session_start = lambda session_type, duration: self.statistics_db.start_session(
            session_type, duration, self._get_current_profile_name()
        )
        self.timer.on_session_end = lambda completed: self.statistics_db.end_session(
            completed=completed,
            actual_seconds=self.timer.get_actual_worked_seconds(),
            pause_count=self.timer.pause_count,
            pause_seconds=self.timer.total_pause_seconds
        )
        self.timer.on_extend = lambda: self.statistics_db.add_extend()
        
        # Set up menu
        self._setup_menu()
        
        # Update icon
        self._update_icon()
        
        # Start timer in background thread
        self.timer_thread_running = True
        self.timer_thread = threading.Thread(target=self._background_timer_loop, daemon=True)
        self.timer_thread.start()
        
        # Flag for pending completion dialog
        self.pending_completion = False
        
        # Track current dialog
        self.current_dialog = None
        
        # Use rumps timer for UI updates only
        rumps.Timer(self._ui_update, 0.5).start()
        
        # Check for config changes every 2 seconds
        rumps.Timer(self._check_config_changes, 2).start()
        self.last_config_mtime = None
        
        # Save state periodically for crash recovery (every 30 seconds)
        rumps.Timer(self._save_state_periodically, 30).start()
        
        # Check for orphaned sessions from crashes
        self._check_orphaned_sessions()
    
    def _check_orphaned_sessions(self):
        """Check for orphaned sessions from crashes and handle them."""
        orphaned = self.statistics_db.get_orphaned_sessions()
        
        if orphaned:
            # Get the most recent orphaned session
            most_recent = orphaned[0]
            session_id = most_recent['id']
            session_type = most_recent['session_type']
            start_time_str = most_recent['start_time']
            
            # Calculate how long ago it was
            from datetime import datetime
            start_time = datetime.fromisoformat(start_time_str)
            time_ago = datetime.now() - start_time
            hours_ago = time_ago.total_seconds() / 3600
            
            # If it was less than 24 hours ago, ask user what to do
            if hours_ago < 24:
                if hours_ago < 1:
                    time_desc = f"{int(time_ago.total_seconds() / 60)} minutes ago"
                else:
                    time_desc = f"{int(hours_ago)} hours ago"
                
                response = rumps.alert(
                    title="Previous Session Interrupted",
                    message=f"A {session_type} session from {time_desc} wasn't completed properly. What would you like to do?",
                    ok="Mark as Incomplete",
                    cancel="Delete Session"
                )
                
                if response == 1:  # Mark as incomplete
                    self.statistics_db.mark_session_as_crashed(session_id)
                    self.notification_manager.show_notification(
                        "Session Recovered",
                        f"Previous {session_type} session marked as incomplete",
                        sound=False
                    )
                else:  # Delete session
                    # For now, just mark it as crashed with 0 duration
                    import sqlite3
                    with sqlite3.connect(self.statistics_db.db_path) as conn:
                        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
                        conn.commit()
            else:
                # Automatically mark very old sessions as crashed
                for session in orphaned:
                    self.statistics_db.mark_session_as_crashed(session['id'])
    
    def _get_timer_snapshot(self):
        """Get a snapshot of timer state while holding the lock."""
        with self.timer_lock:
            return {
                'state': self.timer.state,
                'time_remaining': self.timer.get_time_remaining_string(),
                'completed_pomodoros': self.timer.completed_pomodoros,
                'pomodoros_until_long': self.timer.pomodoros_until_long_break,
                'is_break_time': self.timer.is_break_time()
            }
    
    def _setup_menu(self):
        """Set up the menu items."""
        # Ensure this runs on main thread
        if not threading.current_thread() is threading.main_thread():
            print("Warning: _setup_menu called from background thread, skipping")
            return
            
        try:
            self.menu.clear()
            
            # Combined status display: profile and timer state
            current_profile = self.config_manager.get_current_profile()
            profiles = self.config_manager.get_profiles()
            current_profile_name = profiles[current_profile]['name'] if current_profile in profiles else 'Default'
            
            # Get timer snapshot
            snapshot = self._get_timer_snapshot()
            timer_state = snapshot['state']
            time_remaining = snapshot['time_remaining']
            completed_pomodoros = snapshot['completed_pomodoros']
            pomodoros_until_long = snapshot['pomodoros_until_long']
            is_break_time = snapshot['is_break_time']
            
            # Simple status display without time (time is in menu bar)
            if timer_state == TimerState.IDLE:
                status_text = f"{current_profile_name} • Ready"
            elif timer_state == TimerState.PAUSED:
                status_text = f"{current_profile_name} • Paused"
            elif timer_state == TimerState.WORKING:
                status_text = f"{current_profile_name} • Working"
            elif timer_state in (TimerState.SHORT_BREAK, TimerState.LONG_BREAK):
                status_text = f"{current_profile_name} • On Break"
            else:
                status_text = current_profile_name
            
            status_display = rumps.MenuItem(status_text, callback=None)
            status_display.set_callback(None)
            self.menu.add(status_display)
        except Exception as e:
            print(f"Error setting up menu status: {e}")
            # Add a fallback status
            self.menu.add(rumps.MenuItem("Pomodoro Timer", callback=None))
        
        # Continue with the rest of the menu setup
        try:
            # Separator
            self.menu.add(rumps.separator)
            
            # Control buttons with duration info
            if timer_state == TimerState.IDLE:
                # If it's break time but user hasn't started break, show both options
                if is_break_time:
                    # Determine break duration
                    if completed_pomodoros % pomodoros_until_long == 0 and completed_pomodoros > 0:
                        break_duration = self.config_manager.get('timers.long_break_minutes')
                        break_type = "Long Break"
                    else:
                        break_duration = self.config_manager.get('timers.short_break_minutes')
                        break_type = "Break"
                    work_duration = self.config_manager.get('timers.work_minutes')
                    
                    start_break_item = rumps.MenuItem(f"Start {break_type} ({break_duration} min)", callback=self.start_break)
                    self.menu.add(start_break_item)
                    # Start Work without shortcut to avoid conflict
                    self.menu.add(rumps.MenuItem(f"Start Work ({work_duration} min)", callback=self.start_work))
                else:
                    work_duration = self.config_manager.get('timers.work_minutes')
                    start_item = rumps.MenuItem(f"{MENU_START} ({work_duration} min)", callback=self.start_timer)
                    self.menu.add(start_item)
            elif timer_state == TimerState.PAUSED:
                resume_item = rumps.MenuItem(MENU_RESUME, callback=self.resume_timer)
                self.menu.add(resume_item)
                self.menu.add(rumps.MenuItem(MENU_STOP, callback=self.stop_timer))
            else:
                pause_item = rumps.MenuItem(MENU_PAUSE, callback=self.pause_timer)
                self.menu.add(pause_item)
                self.menu.add(rumps.MenuItem(MENU_STOP, callback=self.stop_timer))
            
            # Separator
            self.menu.add(rumps.separator)
            
            # Quick actions
            if timer_state in (TimerState.WORKING, TimerState.SHORT_BREAK, TimerState.LONG_BREAK):
                # Use different extend time for work vs breaks
                if timer_state == TimerState.WORKING:
                    extend_minutes = self.config_manager.get('timers.extend_minutes', 5)
                else:
                    extend_minutes = self.config_manager.get('timers.extend_break_minutes', 5)
                extend_item = rumps.MenuItem(f"Extend {extend_minutes} min", callback=self.extend_timer)
                self.menu.add(extend_item)
            
            if timer_state in (TimerState.SHORT_BREAK, TimerState.LONG_BREAK):
                self.menu.add(rumps.MenuItem("Skip Break", callback=self.skip_break))
            
            # Profiles submenu
            profiles_menu = rumps.MenuItem("Switch Profile")
            
            for profile_key, profile_data in profiles.items():
                profile_item = rumps.MenuItem(
                    profile_data['name'],
                    callback=lambda sender, key=profile_key: self.switch_profile(key)
                )
                # Add checkmark to current profile
                if profile_key == current_profile:
                    profile_item.state = 1
                profiles_menu.add(profile_item)
            
            # Add separator and new profile option
            profiles_menu.add(rumps.separator)
            profiles_menu.add(rumps.MenuItem("Add Profile...", callback=self.add_profile))
            
            self.menu.add(profiles_menu)
            
            # Settings submenu
            settings_menu = rumps.MenuItem("Settings")
            settings_menu.add(rumps.MenuItem("Configure Timers...", callback=self.show_settings))
            settings_menu.add(rumps.separator)
            settings_menu.add(rumps.MenuItem("Reset All Progress", callback=self.reset_timer))
            self.menu.add(settings_menu)
            
            # Statistics
            today_stats = self.statistics_db.get_today_stats()
            all_time_stats = self.statistics_db.get_all_time_stats()
            stats_text = f"Today: {today_stats['completed_pomodoros']}/{DAILY_GOAL} | Total: {all_time_stats['total_pomodoros']}"
            stats_item = rumps.MenuItem(stats_text, callback=None)
            self.menu.add(stats_item)
            
            # Separator before quit
            self.menu.add(rumps.separator)
            
            # Add quit button
            self.menu.add(rumps.MenuItem(MENU_QUIT, callback=self.quit_app))
        except Exception as e:
            # If menu setup fails, log error and create minimal menu
            print(f"Error setting up menu: {e}")
            # Ensure quit button is always available
            self.menu.add(rumps.MenuItem(MENU_QUIT, callback=self.quit_app))
    
    def _background_timer_loop(self):
        """Background thread that runs the timer logic."""
        while self.timer_thread_running:
            # Only tick if timer is running
            with self.timer_lock:
                if self.timer.state in (TimerState.WORKING, TimerState.SHORT_BREAK, TimerState.LONG_BREAK):
                    self.timer.tick()
            time.sleep(1)  # Sleep for 1 second
    
    def _ui_update(self, _):
        """Update UI elements (runs on main thread)."""
        # Check for pending completion dialog
        if self.pending_completion:
            self.pending_completion = False
            self._show_completion_dialog()
            # Refresh menu after showing dialog
            self._setup_menu()
        
        # Update time display and icon
        if self.timer.state in (TimerState.WORKING, TimerState.SHORT_BREAK, TimerState.LONG_BREAK):
            self._update_time_display()
            self._update_icon()
        elif self.timer.state == TimerState.IDLE:
            # Also update when idle to reflect any state changes
            self._update_time_display()
            self._update_icon()
    
    def _show_completion_dialog(self):
        """Show completion dialog on main thread."""
        
        if self.timer.last_completed_session == TimerState.WORKING:
            # Work session completed - offer break
            print("Showing work completion dialog...")
            
            # Get today's statistics
            today_stats = self.statistics_db.get_today_stats()
            stats = {
                'completed_pomodoros': today_stats.get('completed_pomodoros', 0),
                'work_minutes': today_stats.get('work_minutes', 0)
            }
            
            # Use work extend time for work sessions
            extend_minutes = self.config_manager.get('timers.extend_minutes', 5)
            
            # Play sound first
            self.notification_manager.play_sound()
            
            # Create and show enhanced work completion dialog
            self.current_dialog = WorkCompletionDialog(
                stats=stats,
                extend_minutes=extend_minutes
            )
            
            def handle_response(response, custom_minutes):
                print(f"Dialog response: {response}, custom_minutes: {custom_minutes}")
                self.current_dialog = None  # Clear reference after response
                
                if response == 1:  # Take Break (primary button)
                    print("User selected: Take Break")
                    self._start_break()
                    # Refresh menu after starting break
                    self._setup_menu()
                elif response == -1:  # Extend with custom time
                    extend_time = custom_minutes if custom_minutes else extend_minutes
                    print(f"User selected: Extend {extend_time} minutes")
                    print(f"Timer state: {self.timer.state}, Last session ID: {self.timer.last_session_id}")
                    self._extend_current(extend_time)
                    # Refresh menu after extending
                    self._setup_menu()
                elif response == 0:  # Skip Break
                    print("User selected: Skip Break")
                    # Skip break and go to next work session
                    with self.timer_lock:
                        if self.timer.state == TimerState.IDLE:
                            self.timer.start_work()
                    # Refresh menu after skipping break
                    self._setup_menu()
                else:  # Window closed (red X or ESC)
                    print("Dialog dismissed via close button")
                    # User dismissed dialog, they can decide later what to do
                    # Don't change anything - let them use menu to choose
            
            self.current_dialog.show(callback=handle_response)
                
        elif self.timer.last_completed_session in (TimerState.SHORT_BREAK, TimerState.LONG_BREAK):
            # Break completed - offer to start work
            print("Showing break completion dialog...")
            
            # Use break extend time for break sessions
            extend_break_minutes = self.config_manager.get('timers.extend_break_minutes', 5)
            
            # Play sound first
            self.notification_manager.play_sound()
            
            is_long = self.timer.last_completed_session == TimerState.LONG_BREAK
            
            # Create and show enhanced break completion dialog
            self.current_dialog = BreakCompletionDialog(
                is_long_break=is_long,
                extend_minutes=extend_break_minutes
            )
            
            def handle_response(response, custom_minutes):
                print(f"Dialog response: {response}, custom_minutes: {custom_minutes}")
                self.current_dialog = None  # Clear reference after response
                
                if response == 1:  # Start Work (primary button)
                    print("User selected: Start Work")
                    # Use the proper method that handles state correctly
                    with self.timer_lock:
                        if self.timer.state == TimerState.IDLE:
                            self.timer.start_work()
                    # Refresh menu after starting work
                    self._setup_menu()
                elif response == -1:  # Extend with custom time
                    extend_time = custom_minutes if custom_minutes else extend_break_minutes
                    print(f"User selected: Extend {extend_time} minutes")
                    self._extend_current(extend_time)
                    # Refresh menu after extending
                    self._setup_menu()
                elif response == 0:  # Dismiss
                    print("User selected: Dismiss")
                    # Do nothing - just dismiss
                else:  # Window closed (red X)
                    print("Dialog dismissed via close button")
                    # Do nothing - just dismiss
            
            self.current_dialog.show(callback=handle_response)
    
    def _save_state_periodically(self, _):
        """Save timer state periodically for crash recovery."""
        with self.timer_lock:
            # Only save state if timer is running
            if self.timer.state in (TimerState.WORKING, TimerState.SHORT_BREAK, TimerState.LONG_BREAK, TimerState.PAUSED):
                pause_info = {
                    'total_pause_seconds': self.timer.total_pause_seconds,
                    'pause_count': self.timer.pause_count,
                    'is_paused': self.timer.state == TimerState.PAUSED
                }
                
                self.state_manager.save_state(
                    timer_state=self.timer.state.value,
                    remaining_seconds=self.timer.remaining_seconds,
                    session_id=self.timer.current_session_id,
                    completed_pomodoros=self.timer.completed_pomodoros,
                    pause_info=pause_info
                )
            elif self.timer.state == TimerState.IDLE:
                # Clear state when idle
                self.state_manager.clear_state()
    
    def _check_config_changes(self, _):
        """Check if config file has changed and reload if needed."""
        try:
            if self.config_manager.config_path.exists():
                mtime = os.path.getmtime(self.config_manager.config_path)
                if self.last_config_mtime and mtime > self.last_config_mtime:
                    # Config has changed, reload
                    self.config_manager.config = self.config_manager.load()
                    self._on_settings_saved()
                self.last_config_mtime = mtime
        except:
            pass  # Ignore errors in config checking
    
    def _on_timer_tick(self, remaining_seconds: int):
        """Handle timer tick events."""
        self._update_time_display()
        # Update icon every second for real-time feedback
        self._update_icon()
    
    def _on_timer_complete(self):
        """Handle timer completion - called from background thread."""
        print(f"Timer complete! Last session: {self.timer.last_completed_session}, Completed pomodoros: {self.timer.completed_pomodoros}")
        # Clear saved state since session completed normally
        self.state_manager.clear_state()
        # Set flag to show dialog on main thread
        self.pending_completion = True
        # Don't update UI from background thread - the UI timer will handle it
    
    def _on_state_change(self, old_state: TimerState, new_state: TimerState):
        """Handle state change events - called from background thread."""
        # Don't update UI from background thread, let the main thread handle it
        # The UI timer will pick up the changes
        pass
    
    def _update_time_display(self):
        """Update the status display in the menu."""
        # Get current profile name
        current_profile = self.config_manager.get_current_profile()
        profiles = self.config_manager.get_profiles()
        current_profile_name = profiles[current_profile]['name'] if current_profile in profiles else 'Default'
        
        # Get timer snapshot
        snapshot = self._get_timer_snapshot()
        timer_state = snapshot['state']
        
        # Simple status without time (time is in menu bar)
        if timer_state == TimerState.IDLE:
            display_text = f"{current_profile_name} • Ready"
        elif timer_state == TimerState.PAUSED:
            display_text = f"{current_profile_name} • Paused"
        elif timer_state == TimerState.WORKING:
            display_text = f"{current_profile_name} • Working"
        elif timer_state in (TimerState.SHORT_BREAK, TimerState.LONG_BREAK):
            display_text = f"{current_profile_name} • On Break"
        else:
            display_text = current_profile_name
        
        # Update first menu item
        if self.menu.values():
            first_item = list(self.menu.values())[0]
            first_item.title = display_text
    
    def _update_icon(self):
        """Update the menu bar icon."""
        # Always use emoji icons
        self._update_emoji_icon()
    
    def _update_emoji_icon(self):
        """Update with emoji icons showing visual progress."""
        # Get timer snapshot
        with self.timer_lock:
            timer_state = self.timer.state
            remaining_seconds = self.timer.remaining_seconds
            progress = self.timer.get_progress_percentage()
        
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        
        if timer_state == TimerState.IDLE:
            # Use filled tomato when idle
            self.title = "🍅"
        elif timer_state == TimerState.PAUSED:
            # Paused state - show full time
            if minutes > 0:
                self.title = f"⏸ {minutes}:{seconds:02d}"
            else:
                self.title = f"⏸ {seconds}s"
        elif timer_state == TimerState.WORKING:
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
            
            # Show seconds when less than 1 minute remaining
            if minutes > 0:
                self.title = f"{clock} {minutes}:{seconds:02d}"
            else:
                self.title = f"{clock} {seconds}s"
            
        elif timer_state in (TimerState.SHORT_BREAK, TimerState.LONG_BREAK):
            # Break session - use different emoji
            if progress < 50:
                icon = "☕"  # Coffee for break
            else:
                icon = "✨"  # Almost done with break
            
            # Show seconds when less than 1 minute remaining
            if minutes > 0:
                self.title = f"{icon} {minutes}:{seconds:02d}"
            else:
                self.title = f"{icon} {seconds}s"
    
    
    def _close_current_dialog(self):
        """Close the current dialog if one is open."""
        if self.current_dialog and self.current_dialog.window:
            self.current_dialog.close()
            self.current_dialog = None
    
    def _start_break(self):
        """Start break session."""
        with self.timer_lock:
            self.timer.start_break()
    
    def _extend_current(self, minutes: float):
        """Extend current timer or restart last session with extra time."""
        print(f"_extend_current called with {minutes} minutes")
        
        with self.timer_lock:
            timer_state = self.timer.state
            last_session_id = self.timer.last_session_id
            last_completed_session = self.timer.last_completed_session
            print(f"Current state: {timer_state}, Last session ID: {last_session_id}")
            
            if timer_state in (TimerState.WORKING, TimerState.SHORT_BREAK, TimerState.LONG_BREAK):
                # Timer is still running, just extend it
                print("Timer is running, extending...")
                self.timer.extend(minutes)
                self.notification_manager.show_notification(
                    "Timer Extended",
                    f"Added {minutes} minutes to current session",
                    sound=False
                )
            elif timer_state == TimerState.IDLE and last_session_id:
                # Timer completed, reopen and extend the last session
                # This avoids creating a new session in the statistics
                print(f"Timer is IDLE, reopening session {last_session_id}")
                
                # Reopen the completed session in the database
                self.statistics_db.reopen_session(last_session_id)
                
                # Continue the timer with just the extension time
                self.timer.extend_completed_session(minutes, last_session_id)
                
                print(f"After extending: state={self.timer.state}, remaining={self.timer.remaining_seconds}")
                
                if last_completed_session == TimerState.WORKING:
                    self.notification_manager.show_notification(
                        "Work Extended",
                        f"Continuing work for {minutes} more minutes",
                        sound=False
                    )
                else:
                    self.notification_manager.show_notification(
                        "Break Extended",
                        f"Continuing break for {minutes} more minutes",
                        sound=False
                    )
            else:
                print(f"Cannot extend: state={timer_state}, last_session_id={last_session_id}")
    
    def _skip_to_work(self):
        """Skip break and start next work session."""
        with self.timer_lock:
            # If we're in a break, skip it
            if self.timer.state in (TimerState.SHORT_BREAK, TimerState.LONG_BREAK):
                self.timer.skip_break()
            # Start next work session immediately
            if self.timer.state == TimerState.IDLE:
                self.timer.start_work()
    
    def start_timer(self, _):
        """Start the timer."""
        with self.timer_lock:
            if self.timer.state == TimerState.IDLE:
                if self.timer.is_break_time():
                    self.timer.start_break()
                else:
                    self.timer.start_work()
        # Refresh menu to show pause/stop buttons
        self._setup_menu()
    
    def start_work(self, _):
        """Explicitly start a work session."""
        self._close_current_dialog()  # Close dialog if open
        with self.timer_lock:
            if self.timer.state == TimerState.IDLE:
                self.timer.start_work()
        # Refresh menu to show pause/stop buttons
        self._setup_menu()
    
    def start_break(self, _):
        """Explicitly start a break session."""
        self._close_current_dialog()  # Close dialog if open
        with self.timer_lock:
            if self.timer.state == TimerState.IDLE:
                print(f"DEBUG: start_break menu action - current completed_pomodoros: {self.timer.completed_pomodoros}")
                self.timer.start_break()
        # Refresh menu to show pause/stop buttons
        self._setup_menu()
    
    def stop_timer(self, _):
        """Stop the timer."""
        # Ask for confirmation before stopping
        response = rumps.alert(
            title="Stop Current Session?",
            message="This will end your current session and mark it as incomplete. Continue?",
            ok="Stop Session",
            cancel="Keep Going"
        )
        if response == 1:  # User confirmed
            with self.timer_lock:
                self.timer.stop()
            # Refresh menu to show start button
            self._setup_menu()
    
    def reset_timer(self, _):
        """Reset the timer."""
        response = rumps.alert(
            title="Reset All Progress?",
            message="This will reset your current session, pomodoro count, and return to the beginning. This cannot be undone.",
            ok="Reset Everything",
            cancel="Cancel"
        )
        if response == 1:
            with self.timer_lock:
                self.timer.reset()
            # Refresh menu after reset
            self._setup_menu()
            # Show confirmation
            self.notification_manager.show_notification(
                "Progress Reset",
                "All progress has been reset. Starting fresh!",
                sound=False
            )
    
    def pause_timer(self, _):
        """Pause the timer."""
        with self.timer_lock:
            self.timer.pause()
        # Refresh menu to show resume button
        self._setup_menu()
    
    def resume_timer(self, _):
        """Resume the timer."""
        with self.timer_lock:
            self.timer.resume()
        # Refresh menu to show pause button
        self._setup_menu()
    
    def extend_timer(self, sender):
        """Extend timer by configured minutes."""
        # Use different extend time for work vs breaks
        with self.timer_lock:
            if self.timer.state == TimerState.WORKING:
                extend_minutes = self.config_manager.get('timers.extend_minutes', 5)
            else:
                extend_minutes = self.config_manager.get('timers.extend_break_minutes', 5)
            
            self.timer.extend(extend_minutes)
        
        self.notification_manager.show_notification(
            "Timer Extended",
            f"Added {extend_minutes} minutes",
            sound=False  # No sound for extend
        )
    
    def skip_break(self, _):
        """Skip the current break and start next work session."""
        with self.timer_lock:
            self.timer.skip_break()
            # Automatically start the next work session
            if self.timer.state == TimerState.IDLE:
                print("DEBUG: Skip break - auto-starting next work session")
                self.timer.start_work()
        # Refresh menu after skipping break
        self._setup_menu()
    
    def switch_profile(self, profile_name: str):
        """Switch to a different timer profile.
        
        Args:
            profile_name: Name of the profile to switch to
        """
        if self.config_manager.set_current_profile(profile_name):
            # Update timer with new profile values
            self._update_timer_from_config()
            # Refresh menu to show new checkmark
            self._setup_menu()
            
            # Show notification
            profile_display_name = self.config_manager.get_profiles()[profile_name]['name']
            self.notification_manager.show_notification(
                "Profile Changed",
                f"Switched to '{profile_display_name}' profile",
                sound=False
            )
    
    def add_profile(self, _):
        """Show dialog to add a new profile."""
        # Get current profile values to use as defaults
        current_profile = self.config_manager.get_current_profile()
        current_timers = self.config_manager.get_profiles()[current_profile]['timers']
        
        # Prepare default text with current values
        default_text = (f"Name: My Profile\n"
                       f"Work: {current_timers.get('work_minutes', 25)} min\n"
                       f"Short Break: {current_timers.get('short_break_minutes', 5)} min\n"
                       f"Long Break: {current_timers.get('long_break_minutes', 15)} min\n"
                       f"Pomodoros until long: {current_timers.get('pomodoros_until_long_break', 4)}\n"
                       f"Extend Work: {current_timers.get('extend_minutes', 5)} min\n"
                       f"Extend Break: {current_timers.get('extend_break_minutes', 5)} min")
        
        # Ask for profile details
        response = rumps.Window(
            title="New Profile",
            message="Enter profile details (edit the values below):",
            default_text=default_text,
            ok="Create",
            cancel="Cancel",
            dimensions=(350, 180)
        ).run()
        
        if response.clicked:
            # Parse the input text
            lines = response.text.strip().split('\n')
            profile_data = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == 'name':
                        profile_data['name'] = value
                    elif 'work' in key:
                        try:
                            profile_data['work_minutes'] = float(value.replace('min', '').strip())
                        except ValueError:
                            pass
                    elif 'short' in key:
                        try:
                            profile_data['short_break_minutes'] = float(value.replace('min', '').strip())
                        except ValueError:
                            pass
                    elif 'long' in key and 'break' in key:
                        try:
                            profile_data['long_break_minutes'] = float(value.replace('min', '').strip())
                        except ValueError:
                            pass
                    elif 'pomodoro' in key:
                        try:
                            profile_data['pomodoros_until_long_break'] = int(value)
                        except ValueError:
                            pass
                    elif 'extend' in key:
                        if 'break' in key:
                            try:
                                profile_data['extend_break_minutes'] = float(value.replace('min', '').strip())
                            except ValueError:
                                pass
                        else:
                            try:
                                profile_data['extend_minutes'] = float(value.replace('min', '').strip())
                            except ValueError:
                                pass
            
            if profile_data.get('name'):
                profile_name = profile_data['name']
                # Create profile key from name (lowercase, replace spaces with underscores)
                profile_key = profile_name.lower().replace(' ', '_')
                
                # Prepare timers dict with parsed values or defaults
                timers = {
                    'work_minutes': profile_data.get('work_minutes', current_timers.get('work_minutes', 25)),
                    'short_break_minutes': profile_data.get('short_break_minutes', current_timers.get('short_break_minutes', 5)),
                    'long_break_minutes': profile_data.get('long_break_minutes', current_timers.get('long_break_minutes', 15)),
                    'pomodoros_until_long_break': profile_data.get('pomodoros_until_long_break', current_timers.get('pomodoros_until_long_break', 4)),
                    'extend_minutes': profile_data.get('extend_minutes', current_timers.get('extend_minutes', 5)),
                    'extend_break_minutes': profile_data.get('extend_break_minutes', current_timers.get('extend_break_minutes', 5))
                }
                
                if self.config_manager.create_profile(profile_key, profile_name, timers):
                    # Switch to new profile
                    self.switch_profile(profile_key)
                else:
                    rumps.alert(
                        title="Profile Exists",
                        message=f"A profile named '{profile_name}' already exists."
                    )
            else:
                rumps.alert(
                    title="Invalid Input",
                    message="Please provide a profile name."
                )
    
    def _get_current_profile_name(self):
        """Get the display name of the current profile."""
        current_profile = self.config_manager.get_current_profile()
        profiles = self.config_manager.get_profiles()
        return profiles[current_profile]['name'] if current_profile in profiles else 'Default'
    
    def _update_timer_from_config(self):
        """Update timer with values from current profile."""
        work_minutes = self.config_manager.get('timers.work_minutes')
        short_break_minutes = self.config_manager.get('timers.short_break_minutes')
        long_break_minutes = self.config_manager.get('timers.long_break_minutes')
        pomodoros_until_long_break = self.config_manager.get('timers.pomodoros_until_long_break')
        
        print(f"DEBUG: Updating timer from config - work: {work_minutes}, "
              f"short_break: {short_break_minutes}, long_break: {long_break_minutes}, "
              f"pomodoros_until_long: {pomodoros_until_long_break}")
        
        self.timer.work_minutes = work_minutes
        self.timer.short_break_minutes = short_break_minutes
        self.timer.long_break_minutes = long_break_minutes
        self.timer.pomodoros_until_long_break = pomodoros_until_long_break
    
    def show_settings(self, _):
        """Show settings dialog."""
        # Use JSON settings editor
        settings = JsonSettings(self.config_manager)
        settings.show()
        
        # Reload config after settings window closes
        self.config_manager.config = self.config_manager.load()
        self._on_settings_saved()
    
    def quit_app(self, _):
        """Quit the application."""
        # Stop the timer thread
        self.timer_thread_running = False
        
        # End any active session before quitting
        if self.timer.current_session_id:
            self.statistics_db.end_session(completed=False)
        
        rumps.quit_application()
    
    def _on_settings_saved(self):
        """Called when settings are saved."""
        # Update timer with new values from current profile
        self._update_timer_from_config()
        
        # Refresh menu to show new settings
        self._setup_menu()
        
        # Update icon style if changed
        self._update_icon()
        
        # Don't show notification - too slow
    


def main():
    """Main entry point."""
    # Set up app icon before creating the app
    try:
        import AppKit
        import os
        
        # Initialize the shared application
        app_instance = AppKit.NSApplication.sharedApplication()
        
        # Set the app icon to tomato emoji
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'tomato.png')
        if os.path.exists(icon_path):
            image = AppKit.NSImage.alloc().initWithContentsOfFile_(icon_path)
            if image:
                app_instance.setApplicationIconImage_(image)
    except:
        pass
    
    # Create our Pomodoro app
    app = PomodoroMenuBarApp()
    
    # Hide from dock after app is created
    try:
        import AppKit
        AppKit.NSApp.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
    except:
        pass
    
    app.run()


if __name__ == "__main__":
    main()