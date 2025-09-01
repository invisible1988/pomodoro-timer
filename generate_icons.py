#!/usr/bin/env python3
"""Generate icon files for Pomodoro Timer."""

import os
from pathlib import Path
from PIL import Image, ImageDraw

# Icon settings
ICON_SIZE = 22  # macOS menu bar standard
ASSETS_DIR = Path(__file__).parent / "assets" / "icons"

# Colors
COLOR_WORK = (255, 95, 95)      # Red for work
COLOR_BREAK = (95, 255, 95)     # Green for break
COLOR_IDLE = (128, 128, 128)    # Gray for idle
COLOR_PAUSED = (255, 195, 95)   # Orange for paused

def generate_progress_icon(progress: int, color: tuple, name: str) -> None:
    """Generate a progress icon and save it."""
    # Create image with transparency
    img = Image.new('RGBA', (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw outer circle (border)
    border_color = (*color, 180)  # Semi-transparent
    draw.ellipse(
        [1, 1, ICON_SIZE - 1, ICON_SIZE - 1],
        outline=border_color,
        width=2
    )
    
    if progress > 0:
        # Calculate arc angle (0 degrees is at top)
        angle = int(360 * (progress / 100))
        
        # Draw filled arc
        fill_color = (*color, 255)
        draw.pieslice(
            [2, 2, ICON_SIZE - 2, ICON_SIZE - 2],
            start=-90,
            end=-90 + angle,
            fill=fill_color,
            outline=None
        )
        
        # Draw center dot for better visibility
        center = ICON_SIZE // 2
        dot_size = 3
        draw.ellipse(
            [center - dot_size, center - dot_size,
             center + dot_size, center + dot_size],
            fill=fill_color
        )
    
    # Save the icon
    filepath = ASSETS_DIR / name
    img.save(filepath, 'PNG')
    print(f"Generated: {filepath}")

def generate_all_icons():
    """Generate all icon variations."""
    # Create assets directory
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Progress levels to generate
    progress_levels = [0, 25, 50, 75, 100]
    
    # Generate work icons (red)
    for progress in progress_levels:
        generate_progress_icon(progress, COLOR_WORK, f"work_{progress}.png")
    
    # Generate break icons (green)
    for progress in progress_levels:
        generate_progress_icon(progress, COLOR_BREAK, f"break_{progress}.png")
    
    # Generate special icons
    generate_progress_icon(0, COLOR_IDLE, "idle.png")
    generate_progress_icon(50, COLOR_PAUSED, "paused.png")
    
    # Generate template icons for dark mode support
    # Template images should be black with alpha channel
    for progress in progress_levels:
        img = Image.new('RGBA', (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Black color for template
        color = (0, 0, 0)
        
        # Draw outer circle
        draw.ellipse(
            [1, 1, ICON_SIZE - 1, ICON_SIZE - 1],
            outline=(*color, 180),
            width=2
        )
        
        if progress > 0:
            angle = int(360 * (progress / 100))
            draw.pieslice(
                [2, 2, ICON_SIZE - 2, ICON_SIZE - 2],
                start=-90,
                end=-90 + angle,
                fill=(*color, 255),
                outline=None
            )
        
        filepath = ASSETS_DIR / f"template_{progress}.png"
        img.save(filepath, 'PNG')
        print(f"Generated template: {filepath}")

if __name__ == "__main__":
    generate_all_icons()
    print(f"\n✅ Generated all icons in {ASSETS_DIR}")