cd /D "%~dp0"
cd ..

rem This script builds DreamAPI executables using PyInstaller

CALL venv\Scripts\activate.bat
pyinstaller pyinstaller_config.spec --noconfirm
