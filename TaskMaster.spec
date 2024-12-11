# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('firebase_config.json', '.'),
        ('serviceAccountKey.json', '.'),
        ('ui/*.py', 'ui/'),
        ('.env', '.'),
        ('todolist.ico', '.'),
    ],
    hiddenimports=[
        'firebase_admin',
        'pyrebase4',
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'cryptography',
        'requests',
        'urllib3',
        'chardet',
        'idna',
        'python-dotenv',
        'dateutil.parser',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['_tkinter', 'Tkinter', 'tkinter'],
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
    name='TaskMaster',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='file_version_info.txt',
    icon='todolist.ico'
)
