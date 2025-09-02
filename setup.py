"""
Setup script for building Pomodoro Timer as a macOS app bundle.
"""

from setuptools import setup

APP = ['main.py']
DATA_FILES = [
    ('assets', ['assets/tomato.png'])
]
OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'assets/tomato.icns',  # We'll create this
    'plist': {
        'CFBundleName': 'Pomodoro Timer',
        'CFBundleDisplayName': 'Pomodoro Timer',
        'CFBundleGetInfoString': "A minimalist Pomodoro timer for macOS",
        'CFBundleIdentifier': "com.pomodoro.timer",
        'CFBundleVersion': "1.0.0",
        'CFBundleShortVersionString': "1.0.0",
        'NSHumanReadableCopyright': "MIT License",
        'LSUIElement': True,  # Hide from dock
        'NSHighResolutionCapable': True,
    },
    'packages': ['rumps', 'AppKit'],
    'includes': ['src', 'src.menu_bar_app', 'src.pomodoro_timer', 'src.config_manager', 
                 'src.statistics_db', 'src.notification_manager', 'src.json_settings',
                 'src.constants', 'src.exceptions', 'src.work_completion_dialog',
                 'src.break_completion_dialog', 'objc'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)