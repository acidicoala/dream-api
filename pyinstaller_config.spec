# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.building.api import *
from PyInstaller.building.build_main import Analysis


a = Analysis(
		['src/main.py'],
		pathex=['src'],
		binaries=[],
		datas=[("./resources", "resources")],
		hiddenimports=[],
		hookspath=[],
		runtime_hooks=[],
		excludes=[],
		win_no_prefer_redirects=False,
		win_private_assemblies=False,
		noarchive=False
)

pyz = PYZ(
		a.pure,
		a.zipped_data,
)

exe = EXE(
		pyz,
		a.scripts,
		[],
		exclude_binaries=True,
		name='DreamAPI',
		icon='./resources/icon.ico',
		debug=False,
		bootloader_ignore_signals=False,
		strip=False,
		upx=True,
		console=False,
		uac_admin=True,
		version='version_info.py',
)

coll = COLLECT(
		exe,
		a.binaries,
		a.zipfiles,
		a.datas,
		strip=False,
		upx=True,
		upx_exclude=[],
		name='main'
)

# Portable executable
exe = EXE(
		pyz,
		a.scripts,
		a.binaries,
		a.zipfiles,
		a.datas,
		[],
		name='DreamAPIPortable',
		icon='./resources/icon.ico',
		debug=False,
		bootloader_ignore_signals=False,
		strip=False,
		upx=True,
		upx_exclude=[],
		console=False,
		uac_admin=True,
		version='version_info.py',
)
