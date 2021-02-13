import ctypes

import win32con

from gui.app_window import ApplicationWindow
from gui.tray_icon import AppTrayIcon
from mitm.dream_api_master import DreamAPIMaster
from setup.cert import *
from setup.config import config
from util.info import version
from util.log import log
from util.util import get_ex_msg

if __name__ == '__main__':
	try:
		log.info(f"DreamAPI {version}")

		# Certificates
		if not is_cert_installed():
			install_cert()

		# mitmproxy master
		master = DreamAPIMaster()

		# Tkinter window
		window = ApplicationWindow()

		# Tray icon
		tray = AppTrayIcon(master, window)
		tray.start()

		if config.delete_cert_on_exit:
			delete_cert()

		log.info('Successful exit')
	except BaseException as e:
		title = get_ex_msg(e)
		log.exception(str(e))

		MessageBox = ctypes.windll.user32.MessageBoxW
		MessageBox(None, str(e), title, win32con.MB_OK | win32con.MB_ICONERROR)
