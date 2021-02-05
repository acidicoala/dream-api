from threading import Thread

from infi.systray import SysTrayIcon

from gui.app_window import ApplicationWindow
from mitm.dream_api_master import DreamAPIMaster
from setup.config import Config
from setup.registry import disable_proxy, enable_proxy
from util.resource import get_bundle_path


class AppTrayIcon(SysTrayIcon):
	pending_shutdown = False

	def __init__(self, master: DreamAPIMaster, window: ApplicationWindow):
		super().__init__(
				icon=str(get_bundle_path('icon.ico')),
				hover_text="DreamAPI",
				menu_options=(("Open DreamAPI", None, lambda *args: window.deiconify()),),
				on_quit=self.on_quit
		)

		self.master = master
		self.window = window

		window.set_on_shutdown_callback(self.shutdown)

	def on_quit(self, systray):
		""" Called when tray is destroyed """

		if self.pending_shutdown:
			return

		self.master.shutdown()  # stop proxy
		disable_proxy()

		# The following line attempts to destroy the tkinter window.
		# For some reason it crashes, but since it crashes in the callback,
		# The app still exists without issues with exit code 0xC000041D
		Thread(target=lambda: self.window.after(100, self.window.destroy)).start()

		self.pending_shutdown = True

	def start(self):
		super().start()  # start tray
		self.master.run_async()  # start mitmproxy
		enable_proxy(Config().port)  # enable proxy
		self.window.start()  # start window
