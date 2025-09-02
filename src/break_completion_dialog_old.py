"""Enhanced break completion dialog with custom extend time."""

import AppKit
from typing import Optional, Callable


class BreakCompletionDialog:
    """Enhanced dialog window for break session completion."""
    
    def __init__(self, is_long_break: bool = False, extend_minutes: int = 5):
        """Initialize the break completion dialog.
        
        Args:
            is_long_break: Whether this was a long break
            extend_minutes: Default extend time in minutes
        """
        self.is_long_break = is_long_break
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
                     (1, None) = start work
                     (0, None) = dismiss  
                     (-1, minutes) = extend with custom minutes
                     (None, None) = window closed
        """
        self.callback = callback
        
        # Create window - compact size
        rect = AppKit.NSMakeRect(0, 0, 400, 180)
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
            AppKit.NSMakeRect(20, 135, 360, 25)
        )
        if self.is_long_break:
            title_label.setStringValue_("☕ Long Break Complete!")
        else:
            title_label.setStringValue_("✅ Break Complete!")
        title_label.setBezeled_(False)
        title_label.setDrawsBackground_(False)
        title_label.setEditable_(False)
        title_label.setSelectable_(False)
        title_label.setAlignment_(AppKit.NSTextAlignmentCenter)
        
        # Make title bold and larger
        font = AppKit.NSFont.boldSystemFontOfSize_(16)
        title_label.setFont_(font)
        
        # Message label
        message_label = AppKit.NSTextField.alloc().initWithFrame_(
            AppKit.NSMakeRect(20, 100, 360, 20)
        )
        if self.is_long_break:
            message_label.setStringValue_("Feeling refreshed? Ready to tackle the next session!")
        else:
            message_label.setStringValue_("Ready to get back to work?")
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
        
        # Primary button (Start Work) - leftmost and default
        primary_btn = AppKit.NSButton.alloc().initWithFrame_(
            AppKit.NSMakeRect(start_x, button_y, button_width, button_height)
        )
        primary_btn.setTitle_("Start Work")
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
        
        # Dismiss button - rightmost
        dismiss_btn = AppKit.NSButton.alloc().initWithFrame_(
            AppKit.NSMakeRect(start_x + (button_width + 10) * 2, button_y, button_width, button_height)
        )
        dismiss_btn.setTitle_("Dismiss")
        dismiss_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        dismiss_btn.setTarget_(self)
        dismiss_btn.setAction_("dismissAction:")
        
        # Add subviews
        content_view.addSubview_(title_label)
        content_view.addSubview_(message_label)
        content_view.addSubview_(extend_label)
        content_view.addSubview_(self.extend_field)
        content_view.addSubview_(min_label)
        content_view.addSubview_(primary_btn)
        content_view.addSubview_(extend_btn)
        content_view.addSubview_(dismiss_btn)
        
        # Set content view
        self.window.setContentView_(content_view)
        
        # Show window
        self.window.makeKeyAndOrderFront_(None)
        
        # Make sure window is active and focus on extend field
        AppKit.NSApp.activateIgnoringOtherApps_(True)
        self.window.makeFirstResponder_(self.extend_field)
        
    def primaryAction_(self, sender):
        """Handle Start Work button click."""
        self.response = 1
        self.close()
        
    def dismissAction_(self, sender):
        """Handle Dismiss button click."""
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