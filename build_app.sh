#!/bin/bash

echo "Building Pomodoro Timer macOS App..."

# Create icons directory if it doesn't exist
mkdir -p assets

# Convert PNG to ICNS (macOS icon format)
echo "Creating app icon..."
if [ -f assets/tomato.png ]; then
    # Create iconset directory
    mkdir -p assets/tomato.iconset
    
    # Generate different sizes needed for macOS icons
    sips -z 16 16     assets/tomato.png --out assets/tomato.iconset/icon_16x16.png
    sips -z 32 32     assets/tomato.png --out assets/tomato.iconset/icon_16x16@2x.png
    sips -z 32 32     assets/tomato.png --out assets/tomato.iconset/icon_32x32.png
    sips -z 64 64     assets/tomato.png --out assets/tomato.iconset/icon_32x32@2x.png
    sips -z 128 128   assets/tomato.png --out assets/tomato.iconset/icon_128x128.png
    sips -z 256 256   assets/tomato.png --out assets/tomato.iconset/icon_128x128@2x.png
    sips -z 256 256   assets/tomato.png --out assets/tomato.iconset/icon_256x256.png
    sips -z 512 512   assets/tomato.png --out assets/tomato.iconset/icon_256x256@2x.png
    sips -z 512 512   assets/tomato.png --out assets/tomato.iconset/icon_512x512.png
    sips -z 1024 1024 assets/tomato.png --out assets/tomato.iconset/icon_512x512@2x.png
    
    # Convert to icns
    iconutil -c icns assets/tomato.iconset -o assets/tomato.icns
    
    # Clean up
    rm -rf assets/tomato.iconset
    
    echo "Icon created successfully!"
else
    echo "Warning: tomato.png not found, using default icon"
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist

# Install py2app if not installed
echo "Checking dependencies..."
/usr/bin/pip3 install -q py2app setuptools

# Build the app
echo "Building app bundle..."
/usr/bin/python3 setup.py py2app

# Check if build was successful
if [ -d "dist/Pomodoro Timer.app" ]; then
    echo "✅ Build successful!"
    echo "App location: dist/Pomodoro Timer.app"
    echo ""
    echo "To install:"
    echo "  cp -r 'dist/Pomodoro Timer.app' /Applications/"
    echo ""
    echo "To run:"
    echo "  open 'dist/Pomodoro Timer.app'"
else
    echo "❌ Build failed. Check the output above for errors."
fi