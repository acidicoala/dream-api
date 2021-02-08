rem This script calls all other scripts in the correct order
rem in order to build end-user artifacts

cd /D "%~dp0"
CALL ..\venv\Scripts\activate.bat
python update_versions.py

cd /D "%~dp0"
call build_executables.bat

cd /D "%~dp0"
call build_installer.bat
