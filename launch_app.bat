@echo off
set "APP_DIR=%~dp0"
set "MAIN_APP_PATH=%APP_DIR%main.py"
set "HOTKEY_LISTENER_PATH=%APP_DIR%hotkey_listener.py"
set "APP_LOG=%APP_DIR%app_output.log"
set "HOTKEY_LOG=%APP_DIR%hotkey_listener_output.log"

echo Launching Floating Correction App in background...
REM Use pythonw.exe to run without a console window
start "" "pythonw.exe" "%MAIN_APP_PATH%" > "%APP_LOG%" 2>&1

echo Launching Hotkey Listener in background...
start "" "pythonw.exe" "%HOTKEY_LISTENER_PATH%" > "%HOTKEY_LOG%" 2>&1

echo Floating Correction App and Hotkey Listener launched.
echo Check %APP_LOG% and %HOTKEY_LOG% for logs.
echo Use the hotkey (Ctrl+Alt+G) to toggle the app's visibility.
echo To stop the apps, open Task Manager and end the 'pythonw.exe' processes.
pause
