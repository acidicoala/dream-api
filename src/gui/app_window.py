from tkinter import *
from tkinter.ttk import *
from typing import Callable

from setup.config import config_path, Config
from util.info import version
from util.log import log_path
from util.resource import get_bundle_path
from util.util import open_file_in_os


class ApplicationWindow(Tk):
	def __init__(self):
		super().__init__()

		style = Style()
		style.theme_use('vista')

		self.protocol("WM_DELETE_WINDOW", self.hide_window)

		self.on_shutdown_callback = None

	def start(self):
		if Config().start_minimized:
			self.withdraw()

		self.title(f"DreamAPI {version}")
		self.iconbitmap(str(get_bundle_path('icon.ico')))
		self.minsize(300, 0)
		self.resizable(
				width=False,
				height=False
		)
		self.frame = Frame(self)
		self.init_widgets()
		self.frame.pack(fill=BOTH)

		self.mainloop()

	def hide_window(self):
		self.update()
		self.withdraw()

	def init_widgets(self):
		Label(
				self.frame,
				text=f"DreamAPI is running on port {Config().port}"
		).pack(side=TOP, pady=16)

		Separator(
				self.frame,
				orient=HORIZONTAL
		).pack(side=TOP, fill=BOTH)

		Button(
				self.frame,
				text="Options",
				takefocus=False,
				command=lambda: open_file_in_os(config_path.absolute())
		).pack(side=TOP, pady=8)

		Button(
				self.frame,
				text="Logs",
				takefocus=False,
				command=lambda: open_file_in_os(log_path.absolute())
		).pack(side=TOP, pady=8)

		Separator(
				self.frame,
				orient=HORIZONTAL
		).pack(side=TOP, fill=BOTH)

		Button(
				self.frame,
				text="Shutdown",
				takefocus=False,
				command=self.on_shutdown_callback
		).pack(side=TOP, pady=8)

	def set_on_shutdown_callback(self, on_shutdown_callback: Callable):
		self.on_shutdown_callback = on_shutdown_callback
