#!/bin/bash

echo "Installing Python dependencies for the Floating Correction App..."

# Ensure pip is installed
if ! command -v pip &> /dev/null
then
    echo "pip not found, installing it..."
    sudo apt update
    sudo apt install python3-pip -y
fi

# Install required Python packages
pip install requests filelock keyboard PyQt6

echo "Installation complete."
echo "You can now run the launch script: ./launch_app.sh"
