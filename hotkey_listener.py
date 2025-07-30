import os
import time
import keyboard
import sys

# Determine the correct user's home directory
# If running with sudo, SUDO_USER will be set to the original user's name
# Otherwise, os.path.expanduser("~") works for the current user
if 'SUDO_USER' in os.environ:
    # Construct path for the original user's home directory
    USER_HOME_DIR = os.path.join('/home', os.environ['SUDO_USER'])
else:
    # Fallback for when not running with sudo (e.g., direct execution for testing)
    USER_HOME_DIR = os.path.expanduser("~")

# Define the path for the signal file in the determined user's home directory
TOGGLE_SIGNAL_FILE = os.path.join(USER_HOME_DIR, ".floating_correction_toggle_signal")
# Define the hotkey combination
HOTKEY_COMBINATION = "ctrl+alt+g"

def on_hotkey_pressed():
    """Callback function when the hotkey is pressed."""
    print(f"Hotkey '{HOTKEY_COMBINATION}' pressed. Creating signal file...", file=sys.stderr)
    try:
        # Create the signal file
        with open(TOGGLE_SIGNAL_FILE, 'w') as f:
            f.write("toggle")
        print(f"Signal file created: {TOGGLE_SIGNAL_FILE}", file=sys.stderr)
    except Exception as e:
        print(f"Error creating signal file: {e}", file=sys.stderr)

if __name__ == "__main__":
    print(f"Listening for hotkey: {HOTKEY_COMBINATION}", file=sys.stderr)
    print(f"Signal file path: {TOGGLE_SIGNAL_FILE}", file=sys.stderr) # Added for debugging
    print("Press Ctrl+C to stop the listener.", file=sys.stderr)
    
    # Register the hotkey
    keyboard.add_hotkey(HOTKEY_COMBINATION, on_hotkey_pressed)

    try:
        # Keep the script running to listen for hotkeys
        keyboard.wait() 
    except KeyboardInterrupt:
        print("\nHotkey listener stopped.", file=sys.stderr)
    except Exception as e:
        print(f"An error occurred in the hotkey listener: {e}", file=sys.stderr)

