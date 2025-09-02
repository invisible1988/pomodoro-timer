"""Custom completion dialog window using PyObjC/AppKit."""

import AppKit
from typing import Optional, Callable


class CompletionDialog:
    """Custom dialog window for session completion notifications."""
    
    def __init__(self, title: str, message: str, primary_text: str, secondary_text: str = "Dismiss", extend_text: str = "Extend 5 min"):
        """Initialize the completion dialog.
        
        Args:
            title: Dialog title
            message: Dialog message
            primary_text: Primary button text (e.g., "Take Break", "Start Work")
            secondary_text: Secondary button text (e.g., "Skip Break", "Dismiss")
            extend_text: Extend button text
        """
        self.title = title
        self.message = message
        self.primary_text = primary_text
        self.secondary_text = secondary_text
        self.extend_text = extend_text
        self.response = None
        self.window = None
        self.callback = None
        
    def show(self, callback: Optional[Callable[[int], None]] = None):
        """Show the dialog window.
        
        Args:
            callback: Optional callback function that receives the response:
                     1 = primary button, 0 = secondary/dismiss, -1 = extend, None = window closed
        """
        self.callback = callback
        
        # Create window
        rect = AppKit.NSMakeRect(0, 0, 400, 200)
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
            AppKit.NSMakeRect(20, 140, 360, 30)
        )
        title_label.setStringValue_(self.title)
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
            AppKit.NSMakeRect(20, 80, 360, 50)
        )
        message_label.setStringValue_(self.message)
        message_label.setBezeled_(False)
        message_label.setDrawsBackground_(False)
        message_label.setEditable_(False)
        message_label.setSelectable_(False)
        message_label.setAlignment_(AppKit.NSTextAlignmentCenter)
        
        # Create buttons
        button_width = 100
        button_height = 32
        button_spacing = 10
        total_width = (button_width * 3) + (button_spacing * 2)
        start_x = (400 - total_width) / 2
        button_y = 20
        
        # Primary button (blue, default)
        primary_btn = AppKit.NSButton.alloc().initWithFrame_(
            AppKit.NSMakeRect(start_x, button_y, button_width, button_height)
        )
        primary_btn.setTitle_(self.primary_text)
        primary_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        primary_btn.setTarget_(self)
        primary_btn.setAction_("primaryAction:")
        
        # Secondary button
        secondary_btn = AppKit.NSButton.alloc().initWithFrame_(
            AppKit.NSMakeRect(start_x + button_width + button_spacing, button_y, button_width, button_height)
        )
        secondary_btn.setTitle_(self.secondary_text)
        secondary_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        secondary_btn.setTarget_(self)
        secondary_btn.setAction_("secondaryAction:")
        
        # Extend button
        extend_btn = AppKit.NSButton.alloc().initWithFrame_(
            AppKit.NSMakeRect(start_x + (button_width + button_spacing) * 2, button_y, button_width, button_height)
        )
        extend_btn.setTitle_(self.extend_text)
        extend_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        extend_btn.setTarget_(self)
        extend_btn.setAction_("extendAction:")
        
        # Add subviews
        content_view.addSubview_(title_label)
        content_view.addSubview_(message_label)
        content_view.addSubview_(primary_btn)
        content_view.addSubview_(secondary_btn)
        content_view.addSubview_(extend_btn)
        
        # Set content view
        self.window.setContentView_(content_view)
        
        # Show window
        self.window.makeKeyAndOrderFront_(None)
        
        # Make sure window is active
        AppKit.NSApp.activateIgnoringOtherApps_(True)
        
    def primaryAction_(self, sender):
        """Handle primary button click."""
        self.response = 1
        self.close()
        
    def secondaryAction_(self, sender):
        """Handle secondary button click."""
        self.response = 0
        self.close()
        
    def extendAction_(self, sender):
        """Handle extend button click."""
        self.response = -1
        self.close()
        
    def close(self):
        """Close the window and trigger callback."""
        if self.window:
            self.window.close()
            if self.callback:
                self.callback(self.response)