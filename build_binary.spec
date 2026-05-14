# PyInstaller spec for CreatorAgent — single-file executable for all platforms.
# Build: pyinstaller build_binary.spec
import sys
from pathlib import Path

block_cipher = None

# Hidden imports — providers loaded lazily, PyInstaller won't auto-detect them
hiddenimports = [
    'rich.console', 'rich.panel', 'rich.text', 'rich.prompt', 'rich.table',
    'anthropic', 'google.genai', 'google.genai.types', 'groq',
]

# Try to import each provider; skip if not installed (build still succeeds)
optional_imports = ['anthropic', 'google.genai', 'groq']
for mod in optional_imports:
    try:
        __import__(mod)
    except ImportError:
        if mod in hiddenimports:
            hiddenimports.remove(mod)

a = Analysis(
    ['creatoragent/agent.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Trim size — exclude things we don't use
        'tkinter', 'matplotlib', 'numpy', 'pandas', 'scipy',
        'PIL', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
        'IPython', 'jupyter', 'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Single-file executable. Name differs per platform automatically.
exe_name = 'creatoragent'
if sys.platform == 'win32':
    exe_name = 'creatoragent.exe'

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=exe_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,           # CLI app — keep terminal
    disable_windowed_traceback=False,
    target_arch=None,       # auto-detect (universal2 on macOS if available)
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # add an .ico/.icns later if you want a custom icon
)

# macOS-only: bundle as .app for .dmg packaging
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='CreatorAgent.app',
        icon=None,
        bundle_identifier='com.creatoragent.cli',
        info_plist={
            'CFBundleName': 'CreatorAgent',
            'CFBundleDisplayName': 'CreatorAgent',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
        },
    )
