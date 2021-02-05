cd /D "%~dp0"
cd ..

rem This script installs necessary python packages using pip

CALL venv\Scripts\activate.bat
pip install wheel
pip install -r requirements.txt