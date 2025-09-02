"""Enhanced work completion dialog with statistics and custom extend time."""

import AppKit
from typing import Optional, Callable, Dict


class WorkCompletionDialog:
    """Enhanced dialog window for work session completion with statistics."""
    
    def __init__(self, stats: Dict, extend_minutes: int = 5):
        """Initialize the work completion dialog.
        
        Args:
            stats: Dictionary with today's statistics (pomodoros, work_time_minutes)
            extend_minutes: Default extend time in minutes
        """
        self.stats = stats
        self.extend_minutes = extend_minutes
        self.response = None
        self.custom_extend_minutes = None
        self.window = None
        self.callback = None
        self.extend_field = None
        
    def show(self, callback: Optional[Callable[[int, Optional[int]], None]] = None):
        """Show the dialog window.
        
        Args:
            callback: Optional callback function that receives the response and custom minutes:
                     (1, None) = take break
                     (0, None) = skip break  
                     (-1, minutes) = extend with custom minutes
                     (None, None) = window closed
        """
        self.callback = callback
        
        # Create window - more compact
        rect = AppKit.NSMakeRect(0, 0, 400, 240)
        style = (AppKit.NSWindowStyleMaskTitled | 
                AppKit.NSWindowStyleMaskClosable)
        
        self.window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, style, AppKit.NSBackingStoreBuffered, False
        )
        
        # Configure window
        self.window.setTitle_("")
        self.window.setLevel_(AppKit.NSFloatingWindowLevel)
        self.window.setReleasedWhenClosed_(False)
        
        # Center on screen
        self.window.center()
        
        # Create content view
        content_view = AppKit.NSView.alloc().initWithFrame_(rect)
        
        # Title label
        title_label = AppKit.NSTextField.alloc().initWithFrame_(
            AppKit.NSMakeRect(20, 195, 360, 25)
        )
        title_label.setStringValue_("🎉 Work Session Complete!")
        title_label.setBezeled_(False)
        title_label.setDrawsBackground_(False)
        title_label.setEditable_(False)
        title_label.setSelectable_(False)
        title_label.setAlignment_(AppKit.NSTextAlignmentCenter)
        
        # Make title bold and larger
        font = AppKit.NSFont.boldSystemFontOfSize_(16)
        title_label.setFont_(font)
        
        # Statistics section - single line
        stats_y = 160
        
        # Today's stats label
        stats_label = AppKit.NSTextField.alloc().initWithFrame_(
            AppKit.NSMakeRect(20, stats_y, 360, 20)
        )
        stats_label.setStringValue_("📊 Today's Progress")
        stats_label.setBezeled_(False)
        stats_label.setDrawsBackground_(False)
        stats_label.setEditable_(False)
        stats_label.setSelectable_(False)
        stats_label.setAlignment_(AppKit.NSTextAlignmentCenter)
        stats_font = AppKit.NSFont.systemFontOfSize_(13)
        stats_label.setFont_(stats_font)
        
        # Combined stats line
        combined_stats_label = AppKit.NSTextField.alloc().initWithFrame_(
            AppKit.NSMakeRect(20, stats_y - 25, 360, 20)
        )
        pomodoros_count = self.stats.get('completed_pomodoros', 0)
        work_minutes = self.stats.get('work_minutes', 0)
        hours = work_minutes // 60
        minutes = work_minutes % 60
        if hours > 0:
            time_str = f"{hours}h {minutes}m"
        else:
            time_str = f"{minutes} min"
        combined_stats_label.setStringValue_(f"🍅 Pomodoros: {pomodoros_count}    ⏱️ Work: {time_str}")
        combined_stats_label.setBezeled_(False)
        combined_stats_label.setDrawsBackground_(False)
        combined_stats_label.setEditable_(False)
        combined_stats_label.setSelectable_(False)
        combined_stats_label.setAlignment_(AppKit.NSTextAlignmentCenter)
        
        # Message label
        message_label = AppKit.NSTextField.alloc().initWithFrame_(
            AppKit.NSMakeRect(20, 100, 360, 20)
        )
        message_label.setStringValue_("Great job! Time for a well-deserved break.")
        message_label.setBezeled_(False)
        message_label.setDrawsBackground_(False)
        message_label.setEditable_(False)
        message_label.setSelectable_(False)
        message_label.setAlignment_(AppKit.NSTextAlignmentCenter)
        
        # Create buttons - all in one row
        button_width = 100
        button_height = 28
        button_y = 55
        total_width = (button_width * 3) + 20
        start_x = (400 - total_width) / 2
        
        # Extend section - below buttons
        extend_container_y = 20
        
        # Extend label
        extend_label = AppKit.NSTextField.alloc().initWithFrame_(
            AppKit.NSMakeRect(100, extend_container_y, 70, 22)
        )
        extend_label.setStringValue_("Extend by:")
        extend_label.setBezeled_(False)
        extend_label.setDrawsBackground_(False)
        extend_label.setEditable_(False)
        extend_label.setSelectable_(False)
        
        # Extend text field
        self.extend_field = AppKit.NSTextField.alloc().initWithFrame_(
            AppKit.NSMakeRect(175, extend_container_y, 50, 22)
        )
        self.extend_field.setStringValue_(str(self.extend_minutes))
        self.extend_field.setBezeled_(True)
        self.extend_field.setEditable_(True)
        self.extend_field.setAlignment_(AppKit.NSTextAlignmentCenter)
        
        # Minutes label
        min_label = AppKit.NSTextField.alloc().initWithFrame_(
            AppKit.NSMakeRect(230, extend_container_y, 70, 22)
        )
        min_label.setStringValue_("minutes")
        min_label.setBezeled_(False)
        min_label.setDrawsBackground_(False)
        min_label.setEditable_(False)
        min_label.setSelectable_(False)
        
        # Primary button (Take Break) - leftmost and default
        primary_btn = AppKit.NSButton.alloc().initWithFrame_(
            AppKit.NSMakeRect(start_x, button_y, button_width, button_height)
        )
        primary_btn.setTitle_("Take Break")
        primary_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        primary_btn.setTarget_(self)
        primary_btn.setAction_("primaryAction:")
        primary_btn.setKeyEquivalent_("\r")  # Make it the default (Enter key)
        
        # Extend button - middle
        extend_btn = AppKit.NSButton.alloc().initWithFrame_(
            AppKit.NSMakeRect(start_x + button_width + 10, button_y, button_width, button_height)
        )
        extend_btn.setTitle_("Extend")
        extend_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        extend_btn.setTarget_(self)
        extend_btn.setAction_("extendAction:")
        
        # Skip Break button - rightmost
        skip_btn = AppKit.NSButton.alloc().initWithFrame_(
            AppKit.NSMakeRect(start_x + (button_width + 10) * 2, button_y, button_width, button_height)
        )
        skip_btn.setTitle_("Skip Break")
        skip_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        skip_btn.setTarget_(self)
        skip_btn.setAction_("skipAction:")
        
        # Add subviews
        content_view.addSubview_(title_label)
        content_view.addSubview_(stats_label)
        content_view.addSubview_(combined_stats_label)
        content_view.addSubview_(message_label)
        content_view.addSubview_(extend_label)
        content_view.addSubview_(self.extend_field)
        content_view.addSubview_(min_label)
        content_view.addSubview_(primary_btn)
        content_view.addSubview_(extend_btn)
        content_view.addSubview_(skip_btn)
        
        # Set content view
        self.window.setContentView_(content_view)
        
        # Show window
        self.window.makeKeyAndOrderFront_(None)
        
        # Make sure window is active and focus on extend field
        AppKit.NSApp.activateIgnoringOtherApps_(True)
        self.window.makeFirstResponder_(self.extend_field)
        
    def primaryAction_(self, sender):
        """Handle Take Break button click."""
        self.response = 1
        self.close()
        
    def skipAction_(self, sender):
        """Handle Skip Break button click."""
        self.response = 0
        self.close()
        
    def extendAction_(self, sender):
        """Handle Extend button click."""
        # Get custom minutes from text field
        try:
            self.custom_extend_minutes = float(self.extend_field.stringValue())
            if self.custom_extend_minutes <= 0:
                self.custom_extend_minutes = self.extend_minutes
        except (ValueError, AttributeError):
            self.custom_extend_minutes = self.extend_minutes
        
        self.response = -1
        self.close()
        
    def close(self):
        """Close the window and trigger callback."""
        if self.window:
            self.window.close()
            if self.callback:
                if self.response == -1:
                    self.callback(self.response, self.custom_extend_minutes)
                else:
                    self.callback(self.response, None)