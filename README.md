# 🐨 DreamAPI

### Welcome to the DreamAPI repository.

For user-friendly introduction or support, please check out the [official forum thread]. This document and repository
are meant for application developers.

## 🚀 App architecture

### Python

DreamAPI is written in Python 3. The latest stable python interpreter is bundled in distributable files. To run the
project locally, you would need Python 3.9.0+

### mitmproxy

At the core of DreamAPI lies [mitmproxy] - an interactive, SSL/TLS-capable intercepting proxy. It is written in python
and supports python addons, which is where DreamAPI comes in. DreamAPI initializes mitmproxy and registers itself as an
addon. This allows DreamAPI to intercept DLC requests made by various platforms to their services and modify responses.

### SSL certificate

Virtually all web requests these days are encrypted with TLS. Hence, an SSL certificate needs to be installed in the
Root Store, in order for mitmproxy to decrypt the encrypted traffic. DreamAPI tries to automatically install such a
certificate when it doesn't find one installed. You can view the installed location by hitting `Win+R`,
typing `certmgr.msc`, navigating to `Certificates - Current User` ➔ `Trusted Root Certification Authorities`
➔ `Certificates` and finding `mitmproxy` in this list.

### Web proxy

Since DreamAPI works as a web proxy, an operating system needs to be configured with appropriate proxy settings for
DreamAPI to work properly. DreamAPI does that automatically on every launch and shutdown of application. This is done by
writing to the `Computer\HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings` key of the
Windows registry. It is worth mentioning that DreamAPI intercepts requests only from specific domains, hence the
irrelevant traffic is not tampered with.

### GUI

For user convenience, DreamAPI provides a simple GUI built with [TkInter] with the help of [infi.systray] to manage the
tray icon.

### Packaging

To facilitate application distribution, python scripts and interpreter are bundled using [PyInstaller]. It produces both
portable and installable executables of DreamAPI. Installable executables are then bundled into a setup file
using [Inno Setup].

The [scripts] directory has several scripts that automate from start to end the process of packaging and bundling the
distributable files.

The scripts assume that there is a virtual environment located in the `venv` directory under the root of the project.

## 📄 License

This software is licensed under
[Zero Clause BSD] license, terms of which are available in [LICENSE.txt]

[official forum thread]: https://cs.rin.ru/forum/viewtopic.php?f=10&t=111520

[mitmproxy]: https://github.com/mitmproxy/mitmproxy

[TkInter]: https://wiki.python.org/moin/TkInter

[infi.systray]: https://github.com/Infinidat/infi.systray

[PyInstaller]: https://github.com/pyinstaller/pyinstaller

[Inno Setup]: https://github.com/jrsoftware/issrc

[scripts]: ./scripts

[Zero Clause BSD]: https://en.wikipedia.org/wiki/BSD_licenses#0-clause_license_(%22Zero_Clause_BSD%22)

[LICENSE.txt]: ./LICENSE.txt