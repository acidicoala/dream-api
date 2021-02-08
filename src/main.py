import ctypes

import win32con

from gui.app_window import ApplicationWindow
from gui.tray_icon import AppTrayIcon
from mitm.dream_api_master import DreamAPIMaster
from setup.cert import *
from util.info import version
from util.log import log

if __name__ == '__main__':
	try:
		log.info(f"DreamAPI {version}")

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

		log.info('Successful exit')
	except BaseException as e:
		title = e.message if hasattr(e, 'message') else e.strerror if hasattr(e, 'strerror') else 'Error'
		log.exception(str(e))

		MessageBox = ctypes.windll.user32.MessageBoxW
		MessageBox(None, str(e), title, win32con.MB_OK | win32con.MB_ICONERROR)
