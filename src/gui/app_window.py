from tkinter import *
from tkinter.ttk import *
from typing import Callable

from setup.config import config_path, config
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
        if config.start_minimized:
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
        self.update_idletasks()
        w = self.winfo_screenwidth()
        h = self.winfo_screenheight()
        size = tuple(int(_) for _ in self.geometry().split('+')[0].split('x'))
        x = w/2 - size[0]/2
        y = h/2 - size[1]/2
        self.geometry("%dx%d+%d+%d" % (size + (x, y)))

        self.mainloop()

    def hide_window(self):
        self.update()
        self.withdraw()

    def init_widgets(self):
        if config.languages == "english":
            first_label = f"DreamAPI is running on port {config.port}"
        elif config.languages == "spanish":
            first_label = f"DreamAPI está funcionando en el puerto {config.port}"
        Label(
                self.frame,
                text= first_label
            ).pack(side=TOP, pady=16)

        Separator(
                self.frame,
                orient=HORIZONTAL
        ).pack(side=TOP, fill=BOTH)

        if config.languages == "english":
            first_button = "Options"
        elif config.languages == "spanish":
            first_button = "Opciones"
        Button(
                self.frame,
                text= first_button,
                takefocus=False,
                command=lambda: open_file_in_os(config_path.absolute())
            ).pack(side=TOP, pady=8)
        
        if config.languages == "english":
            second_button = "Logs"
        elif config.languages == "spanish":
            second_button = "Registros"
        Button(
                self.frame,
                text=second_button,
                takefocus=False,
                command=lambda: open_file_in_os(log_path.absolute())
            ).pack(side=TOP, pady=8)

        Separator(
                self.frame,
                orient=HORIZONTAL
        ).pack(side=TOP, fill=BOTH)

        if config.languages == "english":
            third_button = "Shutdown"
        elif config.languages == "spanish":
            third_button = "Apagar"
        Button(
                self.frame,
                text=third_button,
                takefocus=False,
                command=self.on_shutdown_callback
            ).pack(side=TOP, pady=8)

    def set_on_shutdown_callback(self, on_shutdown_callback: Callable):
        self.on_shutdown_callback = on_shutdown_callback


