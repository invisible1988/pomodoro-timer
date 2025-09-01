"""Setup script for Pomodoro Timer macOS app."""

from setuptools import setup, find_packages
import sys
import os

# Ensure we're on macOS
if sys.platform != 'darwin':
    print("This application is only for macOS")
    sys.exit(1)

APP = ['main.py']
DATA_FILES = [
    ('assets', ['assets/complete.wav']),
]

OPTIONS = {
    'argv_emulation': False,  # Don't use argv emulation
    'iconfile': None,  # Will create icon later
    'plist': {
        'CFBundleName': 'Pomodoro Timer',
        'CFBundleDisplayName': 'Pomodoro Timer',
        'CFBundleIdentifier': 'com.pomodoro.timer',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleGetInfoString': 'Pomodoro Timer for macOS',
        'LSUIElement': True,  # Hide from dock - menu bar only
        'LSMinimumSystemVersion': '10.15.0',
        'NSHighResolutionCapable': True,
        'NSHumanReadableCopyright': 'Copyright © 2024 Pomodoro Timer',
        'NSRequiresAquaSystemAppearance': False,  # Support dark mode
    },
    'packages': [
        'rumps',
        'PIL',
        'tkinter',
    ],
    'includes': [
        'src',
        'src.pomodoro_timer',
        'src.menu_bar_app',
        'src.icon_generator',
        'src.config_manager',
        'src.notification_manager',
        'src.constants',
        'src.exceptions',
    ],
    'excludes': [
        'matplotlib',
        'numpy',
        'scipy',
        'pytest',
        'pip',
        'setuptools',
    ],
    'optimize': 2,
}

setup(
    name='PomodoroTimer',
    version='1.0.0',
    description='A minimalist Pomodoro timer for macOS menu bar',
    author='Pomodoro Timer',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    install_requires=[
        'rumps>=0.4.0',
        'Pillow>=10.0.0',
    ],
    python_requires='>=3.9',
)