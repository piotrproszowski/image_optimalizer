#!/bin/bash
set -e

echo "Building Image Optimizer for macOS..."

# Create venv if needed
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate and install
source venv/bin/activate
pip install -q --upgrade pip
pip install -q PyQt5 Pillow pillow-heif pyinstaller

# Clean and build
rm -rf dist build
pyinstaller image_optimizer.spec

# Remove quarantine
xattr -cr dist/image_optimizer.app 2>/dev/null || true

echo "✓ Done: dist/image_optimizer.app"
