"""Notification management for Pomodoro Timer."""

import os
import subprocess
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk
import rumps
from typing import Optional, Callable
from src.constants import (
    NOTIFICATION_WORK_COMPLETE,
    NOTIFICATION_BREAK_COMPLETE,
    NOTIFICATION_LONG_BREAK_COMPLETE
)


class NotificationManager:
    """Manages notifications and popup dialogs."""
    
    def __init__(self, config_manager=None):
        """Initialize notification manager.
        
        Args:
            config_manager: ConfigManager instance for settings
        """
        self.config = config_manager
        self.sound_file = Path(__file__).parent.parent / "assets" / "complete.wav"
        
    def show_notification(
        self,
        title: str,
        message: str,
        sound: bool = True
    ) -> None:
        """Show a macOS notification.
        
        Args:
            title: Notification title
            message: Notification message
            sound: Whether to play sound
        """
        rumps.notification(
            title=title,
            subtitle="",
            message=message,
            sound=False  # We'll handle sound separately
        )
        
        if sound and self.config:
            if self.config.get('preferences.sound_enabled', True):
                self.play_sound()
    
    def play_sound(self, sound_file: Optional[Path] = None) -> None:
        """Play a sound file.
        
        Args:
            sound_file: Path to sound file (uses default if None)
        """
        sound_file = sound_file or self.sound_file
        
        # Use afplay on macOS (built-in audio player)
        if sound_file and sound_file.exists():
            try:
                subprocess.run(
                    ['afplay', str(sound_file)],
                    check=False,
                    capture_output=True
                )
            except Exception as e:
                print(f"Error playing sound: {e}")
        else:
            # Use system sound if no file
            try:
                subprocess.run(
                    ['afplay', '/System/Library/Sounds/Glass.aiff'],
                    check=False,
                    capture_output=True
                )
            except:
                pass
    
    def show_popup_dialog(
        self,
        title: str,
        message: str,
        on_break: Optional[Callable] = None,
        on_extend: Optional[Callable] = None,
        on_skip: Optional[Callable] = None,
        extend_minutes: int = 5
    ) -> None:
        """Show a center-screen popup dialog.
        
        Args:
            title: Dialog title
            message: Dialog message
            on_break: Callback for "Take Break" button
            on_extend: Callback for "Extend" button
            on_skip: Callback for "Skip" button
            extend_minutes: Number of minutes to extend
        """
        def create_dialog():
            # Create root window
            root = tk.Tk()
            root.withdraw()  # Hide the root window
            
            # Create dialog window
            dialog = tk.Toplevel(root)
            dialog.title(title)
            dialog.configure(bg='#f0f0f0')
            
            # Make it stay on top
            dialog.attributes('-topmost', True)
            dialog.lift()
            dialog.focus_force()
            
            # Center the window
            dialog.update_idletasks()
            width = 400
            height = 200
            x = (dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (dialog.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f'{width}x{height}+{x}+{y}')
            
            # Prevent resizing
            dialog.resizable(False, False)
            
            # Create content frame
            content_frame = tk.Frame(dialog, bg='#f0f0f0', padx=30, pady=20)
            content_frame.pack(fill=tk.BOTH, expand=True)
            
            # Title label
            title_label = tk.Label(
                content_frame,
                text=title,
                font=('SF Pro Display', 18, 'bold'),
                bg='#f0f0f0',
                fg='#333333'
            )
            title_label.pack(pady=(0, 10))
            
            # Message label
            message_label = tk.Label(
                content_frame,
                text=message,
                font=('SF Pro Text', 14),
                bg='#f0f0f0',
                fg='#666666',
                wraplength=340
            )
            message_label.pack(pady=(0, 20))
            
            # Button frame
            button_frame = tk.Frame(content_frame, bg='#f0f0f0')
            button_frame.pack(fill=tk.X)
            
            # Style for buttons
            style = ttk.Style()
            style.theme_use('aqua')
            
            def on_break_click():
                dialog.destroy()
                root.destroy()
                if on_break:
                    on_break()
            
            def on_extend_click():
                dialog.destroy()
                root.destroy()
                if on_extend:
                    on_extend()
            
            def on_skip_click():
                dialog.destroy()
                root.destroy()
                if on_skip:
                    on_skip()
            
            # Create buttons
            if on_break:
                break_btn = tk.Button(
                    button_frame,
                    text="Take Break",
                    command=on_break_click,
                    font=('SF Pro Text', 13),
                    bg='#007AFF',
                    fg='white',
                    activebackground='#0051D5',
                    activeforeground='white',
                    highlightthickness=0,
                    bd=0,
                    padx=20,
                    pady=8,
                    cursor='hand2'
                )
                break_btn.pack(side=tk.LEFT, padx=(0, 10))
            
            if on_extend:
                extend_btn = tk.Button(
                    button_frame,
                    text=f"Extend {extend_minutes} min",
                    command=on_extend_click,
                    font=('SF Pro Text', 13),
                    bg='#34C759',
                    fg='white',
                    activebackground='#2FA148',
                    activeforeground='white',
                    highlightthickness=0,
                    bd=0,
                    padx=20,
                    pady=8,
                    cursor='hand2'
                )
                extend_btn.pack(side=tk.LEFT, padx=(0, 10))
            
            if on_skip:
                skip_btn = tk.Button(
                    button_frame,
                    text="Skip",
                    command=on_skip_click,
                    font=('SF Pro Text', 13),
                    bg='#8E8E93',
                    fg='white',
                    activebackground='#636368',
                    activeforeground='white',
                    highlightthickness=0,
                    bd=0,
                    padx=20,
                    pady=8,
                    cursor='hand2'
                )
                skip_btn.pack(side=tk.LEFT)
            
            # Play sound when dialog appears
            self.play_sound()
            
            # Bind escape key to close
            dialog.bind('<Escape>', lambda e: on_skip_click() if on_skip else dialog.destroy())
            
            # Handle window close
            dialog.protocol("WM_DELETE_WINDOW", on_skip_click if on_skip else dialog.destroy)
            
            # Run the dialog
            dialog.mainloop()
        
        # Run in separate thread to not block
        thread = threading.Thread(target=create_dialog, daemon=True)
        thread.start()
    
    def show_work_complete_dialog(
        self,
        on_break: Callable,
        on_extend: Callable,
        on_skip: Callable,
        extend_minutes: int = 5
    ) -> None:
        """Show work completion dialog.
        
        Args:
            on_break: Callback for taking break
            on_extend: Callback for extending timer
            on_skip: Callback for skipping break
            extend_minutes: Minutes to extend
        """
        self.show_popup_dialog(
            title="🎉 Work Session Complete!",
            message="Great job! Time for a well-deserved break.",
            on_break=on_break,
            on_extend=on_extend,
            on_skip=on_skip,
            extend_minutes=extend_minutes
        )
    
    def show_break_complete_dialog(
        self,
        on_work: Callable,
        on_extend: Callable,
        is_long_break: bool = False
    ) -> None:
        """Show break completion dialog.
        
        Args:
            on_work: Callback for starting work
            on_extend: Callback for extending break
            is_long_break: Whether this was a long break
        """
        if is_long_break:
            title = "☕ Long Break Complete!"
            message = "Feeling refreshed? Ready to tackle the next session!"
        else:
            title = "✅ Break Complete!"
            message = "Ready to get back to work?"
        
        self.show_popup_dialog(
            title=title,
            message=message,
            on_break=on_work,  # "Start Work" button
            on_extend=on_extend,
            extend_minutes=5
        )