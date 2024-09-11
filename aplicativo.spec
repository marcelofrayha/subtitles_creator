# -*- mode: python ; coding: utf-8 -*-


import ssl
import os
import sys
import certifi
import pandas

block_cipher = None

# Get the path to the certifi cacert.pem file
cacert_path = certifi.where()

a = Analysis(
    ['aplicativo.py'],
    pathex=[],
    binaries=[
        (ssl._ssl.__file__, '.'),
        ('/usr/local/Cellar/python@3.12/3.12.6/Frameworks/Python.framework/Versions/3.12/lib/python3.12/lib-dynload/_ssl.cpython-312-darwin.so', '.'),
    ],
    datas=[
        (cacert_path, 'certifi'),
    ],
    hiddenimports=['_ssl', 'cryptography', 'certifi'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['ssl_hook.py'],  # Add this line
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

def get_pandas_path():
    pandas_path = os.path.dirname(pandas.__file__)
    return pandas_path

dict_tree = Tree(get_pandas_path(), prefix='pandas', excludes=["*.pyc"])
a.datas += dict_tree
a.binaries = filter(lambda x: 'pandas' not in x[0], a.binaries)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='RosettaStone',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RosettaStone',
)
