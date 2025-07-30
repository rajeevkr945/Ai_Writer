@echo off
echo Installing Python dependencies for the Floating Correction App...

REM Check if pip is installed
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo pip not found. Please install Python and pip.
    echo See: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Install required Python packages
pip install requests filelock keyboard PyQt6

echo Installation complete.
echo You can now run the launch script: launch_app.bat
pause
