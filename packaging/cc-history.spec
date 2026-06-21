# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

ROOT = Path.cwd()


a = Analysis(
    [str(ROOT / "src" / "cc_history" / "app.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=[
        (str(ROOT / "src" / "cc_history" / "templates"), "cc_history/templates"),
        (str(ROOT / "src" / "cc_history" / "static"), "cc_history/static"),
        (str(ROOT / "cat.ico"), "."),
    ],
    hiddenimports=[
        "bottle",
        "clr_loader",
        "proxy_tools",
        "pythonnet",
        "webview",
        "webview.platforms.winforms",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="CC History",
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
    icon=str(ROOT / "cat.ico"),
)

