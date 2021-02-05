import ctypes

import win32con

from gui.app_window import ApplicationWindow
from gui.tray_icon import AppTrayIcon
from mitm.dream_api_master import DreamAPIMaster
from setup.cert import *
from setup.config import Config
from util.info import version
from util.log import Log

if __name__ == '__main__':
	try:
		Log().info(f"DreamAPI {version}")
		Config()

		# Certificates
		if not is_cert_installed():
			auto_install_cert()

		# mitmproxy master
		master = DreamAPIMaster()

		# Tkinter window
		window = ApplicationWindow()

		# Tray icon
		tray = AppTrayIcon(master, window)
		tray.start()

		Log().info('Successful exit')
	except BaseException as e:
		title = e.message if hasattr(e, 'message') else e.strerror if hasattr(e, 'strerror') else 'Error'
		Log().exception(str(e))

		MessageBox = ctypes.windll.user32.MessageBoxW
		MessageBox(None, str(e), title, win32con.MB_OK | win32con.MB_ICONERROR)
