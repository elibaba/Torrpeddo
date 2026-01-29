# build-python.ps1 - Bundle Python backend for Windows
# Run this script on a Windows machine to prepare for Electron packaging.

Write-Host "Bundling Python bridge with PyInstaller for Windows..."

# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Create standalone binary (EXE)
# --onefile: single EXE
# --noconsole: hide focus window
# --name bridge: output as bridge.exe
pyinstaller --onefile --noconsole --name bridge backend/bridge.py

# Move to the distribution directory expected by electron-builder
if (-not (Test-Path "backend/dist")) { New-Item -ItemType Directory -Path "backend/dist" }
Move-Item "dist/bridge.exe" "backend/dist/" -Force

Write-Host "Done! bridge.exe is located in backend/dist/"
