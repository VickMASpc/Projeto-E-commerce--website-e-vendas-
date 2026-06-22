# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec para gerar o launcher headless GrandParfumServer.exe.

Uso recomendado, a partir da raiz do repositório:
    pyinstaller "Sistema de vendas/pyinstaller_server.spec"

Este spec NAO embute serviceAccountKey.json, .env ou server_config.json real.
O executável continua recebendo configuração externa por arquivo arrastado,
variáveis de ambiente ou credencial copiada para %APPDATA%\\GrandParfum\\.
"""

from pathlib import Path

project_root = Path(SPECPATH).parent.parent
sales_dir = project_root / "Sistema de vendas"

block_cipher = None


a = Analysis(
    [str(sales_dir / "launcher.py")],
    pathex=[str(sales_dir)],
    binaries=[],
    datas=[
        (str(sales_dir / "db_mock.json"), "."),
        (str(sales_dir / "serviceAccountKey.example.json"), "."),
        (str(sales_dir / "server_config.example.json"), "."),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="GrandParfumServer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
