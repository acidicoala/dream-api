cd /D "%~dp0"
cd ..

rem This script compiles DreamAPI installer using Inno Setup

iscc inno_setup.iss
