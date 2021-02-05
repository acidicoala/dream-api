# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# noinspection PyUnresolvedReferences
a = Analysis(
		['main.py'],
		pathex=['src'],
		binaries=[],
		datas=[("./resources", "resources")],
		hiddenimports=[],
		hookspath=[],
		runtime_hooks=[],
		excludes=[],
		win_no_prefer_redirects=False,
		win_private_assemblies=False,
		cipher=block_cipher,
		noarchive=False
)

# noinspection PyUnresolvedReferences
pyz = PYZ(
		a.pure,
		a.zipped_data,
		cipher=block_cipher
)

# noinspection PyUnresolvedReferences
exe = EXE(
		pyz,
		a.scripts,
		a.binaries,
		a.zipfiles,
		a.datas,
		[],
		name='DreamAPI',
		icon='./resources/icon.ico',
		debug=False,
		bootloader_ignore_signals=False,
		strip=False,
		upx=True,
		upx_exclude=[],
		# runtime_tmpdir=None,
		console=False,
		uac_admin=True
)
