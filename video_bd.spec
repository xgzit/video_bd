# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_all

# ── 平台图标 ────────────────────────────────────────────────────
if sys.platform == 'win32':
    _icon = ['resources/icons/app_icon.ico']
elif sys.platform == 'darwin':
    _icns = 'resources/icons/app_icon.icns'
    _icon = [_icns] if os.path.exists(_icns) else []
else:
    _icon = []

# ── Windows DPI 感知 manifest ───────────────────────────────────
_manifest = None
if sys.platform == 'win32':
    _manifest = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0"
          xmlns:asmv3="urn:schemas-microsoft-com:asm.v3">
  <asmv3:application>
    <asmv3:windowsSettings>
      <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true/PM</dpiAware>
      <dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">PerMonitorV2,PerMonitor</dpiAwareness>
    </asmv3:windowsSettings>
  </asmv3:application>
</assembly>'''

# ── 依赖收集 ────────────────────────────────────────────────────
datas = [('resources', 'resources'), ('src/config', 'src/config')]
binaries = []
hiddenimports = [
    'PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets',
    'PyQt5.QtWebEngineWidgets', 'PyQt5.QtWebEngineCore', 'PyQt5.sip',
    'yt_dlp', 'yt_dlp.extractor', 'yt_dlp.downloader', 'yt_dlp.postprocessor',
    'json', 'urllib3', 'requests', 'certifi', 'charset_normalizer', 'idna',
    'pycryptodome', 'websockets', 'websocket',
]

tmp_ret = collect_all('yt_dlp')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('PyQt5')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# ── Analysis ────────────────────────────────────────────────────
a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['rthook_hidpi.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='video_bd',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=_icon,
    manifest=_manifest,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='video_bd',
)

# ── macOS .app bundle ───────────────────────────────────────────
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='video_bd.app',
        icon=_icon[0] if _icon else None,
        bundle_identifier='com.video_bd',
        info_plist={
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '10.13.0',
            'CFBundleDisplayName': 'Video Batch Downloader',
            'CFBundleVersion': '1.1.0',
            'CFBundleShortVersionString': '1.1.0',
        },
    )
