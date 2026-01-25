@echo off
setlocal

echo Building Image Optimizer for Windows...

if not exist "venv" (
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install -q --upgrade pip
pip install -q PyQt5 Pillow pillow-heif pyinstaller

if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

pyinstaller image_optimizer.spec

echo.
echo Done: dist\image_optimizer.exe
pause
