# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for jr-dev (Developer Macro Engine)
Build with: pyinstaller --clean jr-dev.spec
"""

import os
import sys
from pathlib import Path

block_cipher = None

# Get project root
SPEC_ROOT = Path(SPECPATH)

# Collect all Python files from features, core, ui, utils, inputs, runtime
a = Analysis(
    ['main.py'],
    pathex=[str(SPEC_ROOT)],
    binaries=[],
    datas=[
        # Include config files
        ('config', 'config'),
        # Include any asset files if needed
    ],
    hiddenimports=[
        # Tkinter
        'tkinter',
        'tkinter.ttk',
        # pynput
        'pynput',
        'pynput.keyboard',
        'pynput.keyboard._win32',
        # pystray
        'pystray',
        'pystray._win32',
        # PIL for icons
        'PIL',
        'PIL.Image',
        # pyperclip
        'pyperclip',
        # All our modules
        'core',
        'core.config',
        'core.config.config_manager',
        'core.commands',
        'core.commands.command_executor',
        'core.events',
        'core.events.event_router',
        'core.events.input_event',
        'core.modes',
        'core.modes.mode_manager',
        'core.snippets',
        'core.snippets.snippet_manager',
        'core.features',
        'core.features.base_feature',
        'core.features.feature_registry',
        'features',
        'features.ai_assistant',
        'features.clone_project',
        'features.frontend_runner',
        'features.git_commit',
        'features.git_status',
        'features.mode_switcher',
        'features.shortcut_guide',
        'features.snippet_tool',
        'features.terminal_quick',
        'inputs',
        'inputs.base_input',
        'inputs.keyboard_provider',
        'runtime',
        'runtime.bootstrap',
        'ui',
        'ui.dialogs',
        'ui.popup_runner',
        'ui.quick_panel',
        'ui.settings_dialog',
        'ui.snippet_selector',
        'ui.system_tray',
        'ui.visual_feedback',
        'utils',
        'utils.logger',
        'utils.statistics',
        'utils.windows_utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='jr-dev',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add path to .ico file if you have one
)
