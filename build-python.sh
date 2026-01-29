#!/bin/bash
# build-python.sh - Bundle Python backend for Unix (testing/local)
# For Windows distribution, use the build-python.ps1 script on a Windows machine.

echo "Bundling Python bridge with PyInstaller..."

# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Create standalone binary
pyinstaller --onefile --noconsole --name bridge backend/bridge.py

# Move to the distribution directory expected by electron-builder
mkdir -p backend/dist
mv dist/bridge backend/dist/

echo "Done! Python bridge binary is in backend/dist/"
