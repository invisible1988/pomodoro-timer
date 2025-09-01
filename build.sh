#!/bin/bash

# Build script for Pomodoro Timer macOS app

echo "🍅 Building Pomodoro Timer..."

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist *.egg-info

# Install dependencies
echo "Installing dependencies..."
pip3 install -q py2app rumps Pillow

# Build the app
echo "Building application..."
python3 setup.py py2app

# Check if build succeeded
if [ -d "dist/Pomodoro Timer.app" ]; then
    echo "✅ Build successful!"
    echo "📦 App location: dist/Pomodoro Timer.app"
    
    # Create DMG (optional)
    read -p "Create DMG installer? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Creating DMG..."
        hdiutil create -volname "Pomodoro Timer" \
                       -srcfolder dist \
                       -ov \
                       -format UDZO \
                       PomodoroTimer.dmg
        echo "✅ DMG created: PomodoroTimer.dmg"
    fi
else
    echo "❌ Build failed!"
    exit 1
fi

echo "🎉 Done!"