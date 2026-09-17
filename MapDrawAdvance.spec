# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = [('templates', 'templates'), ('static', 'static'), ('escala-color.jpg', '.'), ('portada.jpg', '.'), ('icons', 'icons'), ('projects', 'projects'), ('data.xls', '.')]
datas += collect_data_files('folium')
datas += collect_data_files('branca')


a = Analysis(
    ['server.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['flask', 'werkzeug', 'jinja2', 'folium', 'folium.plugins', 'branca', 'branca.element', 'pandas', 'openpyxl', 'xlrd', 'pyproj', 'mpu', 'matplotlib', 'numpy', 'geocoder', 'functions', 'eqa2utm', 'distAndAngle', 'scaletemplate', 'main'],
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
    name='MapDrawAdvance',
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
