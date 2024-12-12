# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['todolist.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('todolist.ico', '.'),
        ('ui/*', 'ui/'),
        ('firebase_config.json', '.'),
        ('serviceAccountkey.json', '.'),
        ('.env', '.'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'firebase_admin',
        'requests',
        'python-dotenv',
        'cryptography'
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
    name='TaskMaster',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='todolist.ico'
)
