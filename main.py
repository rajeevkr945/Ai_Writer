import sys
import os
import json
import requests
from PyQt6.QtWidgets import QApplication, QWidget, QTextEdit, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QAbstractAnimation
from PyQt6.QtGui import QColor, QPalette
from filelock import FileLock, Timeout

# Define paths for the lock file and toggle signal file in the user's home directory
LOCK_FILE = os.path.join(os.path.expanduser("~"), ".floating_correction_app.lock")
TOGGLE_SIGNAL_FILE = os.path.join(os.path.expanduser("~"), ".floating_correction_toggle_signal")

class FloatingCorrectionWidget(QWidget):
    # Class-level variable to hold the single instance
    _instance = None
    # Class-level flag to track if __init__ has been fully executed for the instance
    _initialized_flag = False

    def __new__(cls, *args, **kwargs):
        # Implement singleton pattern to ensure only one instance
        if not cls._instance:
            cls._instance = super(FloatingCorrectionWidget, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Only execute the initialization logic if it hasn't been done for this instance yet
        if not FloatingCorrectionWidget._initialized_flag:
            super().__init__() # Call super().__init__() only once for the new instance
            FloatingCorrectionWidget._initialized_flag = True # Mark as initialized
            print("DEBUG: FloatingCorrectionWidget __init__ called for the first time.", file=sys.stderr)

            self.offset = QPoint()
            self.api_key = None 
            self.model_name = 'gemini-2.0-flash'

            # Animation setup
            self.opacity_effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(self.opacity_effect)
            self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
            self.animation.setDuration(300) # 300 milliseconds for animation
            self.animation.finished.connect(self._animation_finished) # Connect to a new finished handler
            self._is_animating = False # Flag to prevent rapid toggling

            # Lock file setup for single instance prevention
            self.lock_file_path = LOCK_FILE
            self.lock = FileLock(self.lock_file_path)

            # Attempt to acquire the lock. If another instance holds it, exit.
            if not self._acquire_lock():
                print("DEBUG: Another instance of FloatingCorrectionApp is already running. Exiting.", file=sys.stderr)
                # Use QTimer.singleShot to quit the app after a short delay
                # This ensures the QApplication event loop has a chance to start and process the quit.
                QTimer.singleShot(0, QApplication.instance().quit)
                return # Exit __init__ early to prevent further setup on an exiting app

            # Timer to check for the toggle signal file
            self.toggle_check_timer = QTimer(self)
            self.toggle_check_timer.setInterval(200) # Check every 200ms
            self.toggle_check_timer.timeout.connect(self._check_toggle_signal)
            self.toggle_check_timer.start() # Start checking immediately
            print("DEBUG: Toggle check timer started.", file=sys.stderr)

            self.init_ui()
            self.init_gemini()

            # Start hidden and fully transparent for daemon-like behavior
            self.hide()
            self.opacity_effect.setOpacity(0)
            print("DEBUG: Widget initialized and set to hidden with 0 opacity.", file=sys.stderr)
        else:
            print("DEBUG: FloatingCorrectionWidget __init__ called for existing instance (skipped re-init).", file=sys.stderr)


    def _acquire_lock(self):
        """Attempts to acquire the application lock."""
        try:
            # Try to acquire the lock without blocking (timeout=0.1s)
            self.lock.acquire(timeout=0.1)
            print(f"DEBUG: Lock acquired: {self.lock_file_path}", file=sys.stderr)
            return True
        except Timeout:
            # Lock is already held by another process
            return False
        except Exception as e:
            print(f"ERROR: Error acquiring lock: {e}", file=sys.stderr)
            return False

    def _release_lock(self):
        """Releases the application lock."""
        try:
            if self.lock.is_locked:
                self.lock.release()
                print(f"DEBUG: Lock released: {self.lock_file_path}", file=sys.stderr)
        except Exception as e:
            print(f"ERROR: Error releasing lock: {e}", file=sys.stderr)

    def closeEvent(self, event):
        """Overrides the close event to ensure proper cleanup."""
        print("DEBUG: Application close event triggered.", file=sys.stderr)
        self._release_lock() # Release the lock when the window is closed
        # Ensure animation is stopped and flag reset if closing during animation
        if self.animation.state() == QAbstractAnimation.State.Running:
            self.animation.stop()
        self._is_animating = False
        event.accept() # Accept the close event, allowing the app to exit

    def _animation_finished(self):
        """Handler for when the opacity animation finishes."""
        self._is_animating = False
        print("DEBUG: Animation finished. _is_animating set to False.", file=sys.stderr)
        # Only hide the widget if it faded out completely
        if self.opacity_effect.opacity() == 0.0:
            self.hide() 

    def _check_toggle_signal(self):
        """Checks for the existence of the toggle signal file."""
        if os.path.exists(TOGGLE_SIGNAL_FILE):
            if self._is_animating:
                print("DEBUG: Toggle signal detected but animation in progress. Skipping.", file=sys.stderr)
                return # Skip if an animation is currently running

            print(f"DEBUG: Toggle signal file detected: {TOGGLE_SIGNAL_FILE}", file=sys.stderr)
            try:
                os.remove(TOGGLE_SIGNAL_FILE) # Consume the signal
                print("DEBUG: Toggle signal received and file removed. Toggling visibility.", file=sys.stderr)
                self._toggle_visibility_animated()
            except OSError as e:
                print(f"ERROR: Error removing toggle signal file: {e}", file=sys.stderr)

    def init_ui(self):
        # Set window flags for floating behavior
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Set initial size and position
        self.setGeometry(100, 100, 400, 200)

        # Main Layout (Vertical)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Define Close Button
        self.close_button = QPushButton("X", self)
        self.close_button.setFixedSize(20, 20)
        self.close_button.clicked.connect(self._hide_animated) # Connect to animated hide
        self.close_button.setStyleSheet("background-color: red; color: white; border-radius: 10px;")

        # Top Bar Layout for Close Button
        top_bar_layout = QHBoxLayout()
        top_bar_layout.addStretch() # Pushes button to the right
        top_bar_layout.addWidget(self.close_button)
        self.layout.insertLayout(0, top_bar_layout) # Insert at the very top of the main layout

        # Input Text Box
        self.input_text = QTextEdit(self)
        self.input_text.setPlaceholderText("Type or paste text here for correction...")
        self.layout.addWidget(self.input_text)

        # Correct/Rephrase Button - This is now the ONLY trigger for API call
        self.correct_button = QPushButton("Correct / Rephrase", self)
        self.correct_button.clicked.connect(self.process_text)
        self.layout.addWidget(self.correct_button)

        # Output Text Box (Read-only)
        self.output_label = QLabel("Corrected/Rephrased Text:") 
        self.layout.addWidget(self.output_label)
        self.output_text = QTextEdit(self)
        self.output_text.setReadOnly(True)
        self.layout.addWidget(self.output_text)

        # Apply some basic styling
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(40, 44, 52, 0.8);
                border: 2px solid #61afef;
                border-radius: 10px;
            }
            QTextEdit {
                background-color: rgba(60, 65, 75, 0.9);
                color: #abb2bf;
                border: 1px solid #3e4452;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton {
                background-color: #56b6c2;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #61afef;
            }
            QLabel {
                color: #98c379;
                padding-top: 5px;
            }
        """)
        print("DEBUG: UI initialized.", file=sys.stderr)

    def init_gemini(self):
        # --- HARDCODING THE API KEY (as requested, disregarding security for immediate functionality) ---
        # !!! WARNING: This is INSECURE for production. Your API key will be visible in the code. !!!
        # For actual deployment, revert to environment variables or a secure secret management system.
        
        # Updated API key based on your successful curl command
        self.api_key = "AIzaSyCcUdKmCrqsKDWaTo0PfcR-UCoHXV7xgms" 
        
        if not self.api_key:
            self.output_text.setText("Error: API key is not set. Cannot initialize Gemini functionality.")
            self.correct_button.setEnabled(False)
            print("ERROR: API key is not set in init_gemini.", file=sys.stderr)
        else:
            self.output_label.setText("Corrected/Rephrased Text:") 
            self.correct_button.setEnabled(True)
            print("DEBUG: Gemini API key set and button enabled.", file=sys.stderr)

    def _show_animated(self):
        """Shows the widget with a fade-in animation."""
        print("DEBUG: _show_animated called.", file=sys.stderr)
        self._is_animating = True # Set flag when animation starts
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.show() # Make the widget visible before starting animation
        self.animation.start()
        self.activateWindow() # Bring to front and focus
        self.raise_() # Ensure it's on top of other windows

    def _hide_animated(self):
        """Hides the widget with a fade-out animation."""
        print("DEBUG: _hide_animated called.", file=sys.stderr)
        self._is_animating = True # Set flag when animation starts
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        # The animation.finished signal is connected in __init__ to _animation_finished
        # which will handle the actual hide() call if opacity reaches 0.0
        self.animation.start()

    def _toggle_visibility_animated(self):
        """Toggles the widget's visibility with animation."""
        print("DEBUG: _toggle_visibility_animated called.", file=sys.stderr)
        if self._is_animating:
            print("DEBUG: Toggle requested but animation already in progress. Skipping.", file=sys.stderr)
            return # Prevent re-triggering if an animation is already running

        if self.isVisible():
            self._hide_animated()
        else:
            self._show_animated()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(self.pos() + event.pos() - self.offset)

    def process_text(self):
        input_text_content = self.input_text.toPlainText().strip()
        if not input_text_content:
            self.output_text.setText("Please enter some text to process.")
            print("DEBUG: No input text to process.", file=sys.stderr)
            return

        if not self.api_key:
            self.output_text.setText("API key is missing. Cannot process text.")
            print("ERROR: API key is missing during process_text.", file=sys.stderr)
            return

        print(f"DEBUG: Processing text. Using API Key: {self.api_key[:5]}...{self.api_key[-5:]}", file=sys.stderr) 

        try:
            # Engineered prompt to get ONLY the corrected text
            prompt_text = (
                f"Correct the following text for grammar, spelling, and natural phrasing. "
                f"Provide ONLY the corrected text, with no introductory or concluding remarks, "
                f"and no other additional words. If the input is a single word, provide only "
                f"that word if it's correct, or its corrected form. Do not explain changes. "
                f"Just the corrected text:\n\n\"{input_text_content}\""
            )
            
            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"

            headers = {
                'Content-Type': 'application/json',
                'X-goog-api-key': self.api_key 
            }

            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt_text
                            }
                        ]
                    }
                ]
            }

            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status() 

            json_response = response.json()
            
            if json_response and "candidates" in json_response and len(json_response["candidates"]) > 0:
                generated_text = json_response["candidates"][0]["content"]["parts"][0]["text"]
                self.output_text.setText(generated_text.strip())
                print("DEBUG: Text processed successfully.", file=sys.stderr)
            else:
                self.output_text.setText(f"Error: No text generated. API response: {json.dumps(json_response, indent=2)}")
                print(f"ERROR: No text generated. API response: {json.dumps(json_response, indent=2)}", file=sys.stderr)

        except requests.exceptions.RequestException as req_err:
            self.output_text.setText(f"Network or API request error: {req_err}")
            print(f"ERROR: Network or API request error: {req_err}", file=sys.stderr)
            if hasattr(req_err, 'response') and req_err.response is not None:
                print(f"ERROR: API Response Content: {req_err.response.text}", file=sys.stderr)
        except json.JSONDecodeError as json_err:
            self.output_text.setText(f"Error parsing API response: {json_err}")
            print(f"ERROR: Error parsing API response: {json_err}", file=sys.stderr)
            print(f"ERROR: Raw API Response: {response.text if 'response' in locals() else 'No response'}", file=sys.stderr)
        except Exception as e:
            self.output_text.setText(f"An unexpected error occurred: {e}")
            print(f"ERROR: An unexpected error occurred: {e}", file=sys.stderr)

if __name__ == '__main__':
    # Ensure only one instance of QApplication is created
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    widget = FloatingCorrectionWidget()
    # If another instance was detected in __init__, widget will have called quit()
    # So we only proceed if the app is still running and hasn't quit
    # Check _initialized_flag to ensure the widget was fully set up
    if FloatingCorrectionWidget._initialized_flag and QApplication.instance() is not None:
        sys.exit(app.exec())
    else:
        # If initialization failed (e.g., lock not acquired), just exit
        sys.exit(0)
