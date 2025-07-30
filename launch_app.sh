#!/bin/bash

APP_DIR="$(dirname "$0")" # Get the directory where the script is located
MAIN_APP_PATH="$APP_DIR/main.py"
HOTKEY_LISTENER_PATH="$APP_DIR/hotkey_listener.py"

# Get the user's site-packages directory where 'keyboard' and other user-installed packages reside
# This ensures sudo can find modules installed in ~/.local/
USER_SITE_PACKAGES=$(python3 -c "import site; print(site.getusersitepackages())")

echo "Launching Floating Correction App in background..."
# Use nohup to run in background and detach from terminal
# Redirect stdout/stderr to files for debugging
nohup python3 "$MAIN_APP_PATH" > "$APP_DIR/app_output.log" 2>&1 &
echo "Floating Correction App launched. Check app_output.log for logs."

echo "Launching Hotkey Listener in background (requires sudo for global hotkeys and custom PYTHONPATH)..."

# Prompt for password before launching the hotkey listener with sudo
read -s -p "Enter your sudo password for the hotkey listener: " SUDO_PASSWORD
echo # Add a newline after the password prompt

# Use sudo -S to read password from standard input (provided by 'echo $SUDO_PASSWORD')
# Use 'env' to set PYTHONPATH for the sudo command, combining it with existing PYTHONPATH if any
# Explicitly call python3 (from user's PATH) to ensure the correct interpreter is used
echo "$SUDO_PASSWORD" | nohup sudo -S env PYTHONPATH="$USER_SITE_PACKAGES:$PYTHONPATH" python3 "$HOTKEY_LISTENER_PATH" > "$APP_DIR/hotkey_listener_output.log" 2>&1 &

# Clear the password variable for security
unset SUDO_PASSWORD

echo "Hotkey Listener launched. Check hotkey_listener_output.log for logs."

echo "Use the hotkey (Ctrl+Alt+G) to toggle the app's visibility."
echo "To stop the apps, you might need to find and kill the Python processes."
echo "Example (Linux): pkill -f main.py; pkill -f hotkey_listener.py"
