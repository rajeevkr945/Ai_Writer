### How to Use Everything:

    Save all files:
```
        main.py (from Step 2)

        hotkey_listener.py (from Step 3)

        install.sh (Linux) or install.bat (Windows)

        launch_app.sh (Linux) or launch_app.bat (Windows)

        Make sure all these files are in the same directory.
```

    Install dependencies:
```
        Linux: Open terminal in the directory, run chmod +x install.sh then ./install.sh.

        Windows: Double-click install.bat.

    Launch the application and listener:

        Linux: Open terminal in the directory, run chmod +x launch_app.sh then ./launch_app.sh.

        Windows: Double-click launch_app.bat.
```
    Test the hotkey:

```        After launching, the app window should not appear immediately.

        Press Ctrl + Alt + G (the hotkey defined in hotkey_listener.py).

        The app window should fade in. Press Ctrl + Alt + G again, and it should fade out.
```
    Stopping the applications:
```
        Linux: Open a terminal and run pkill -f main.py; pkill -f hotkey_listener.py.

        Windows: Open Task Manager (Ctrl+Shift+Esc), go to the "Details" tab, find pythonw.exe processes (there should be two if both launched successfully), select them, and click "End task".
```        