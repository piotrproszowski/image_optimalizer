#!/bin/bash
# Quickstart script for web deployment

set -e

echo "🚀 Image Processor - Web Deployment Quickstart"
echo "=============================================="
echo

# Check for dependencies
echo "📦 Checking dependencies..."

if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install Node.js first."
    exit 1
fi

if ! command -v cargo &> /dev/null; then
    echo "❌ cargo is not installed. Please install Rust first."
    exit 1
fi

if ! pkg-config --exists vips 2>/dev/null; then
    echo "❌ libvips is not installed."
    echo "Please install it:"
    echo "  macOS: brew install vips"
    echo "  Ubuntu/Debian: sudo apt-get install libvips-dev"
    exit 1
fi

echo "✅ All dependencies found!"
echo

# Install frontend dependencies
echo "📥 Installing frontend dependencies..."
npm install
echo

# Build frontend
echo "🏗️  Building frontend..."
npm run build:web
echo

# Build backend
echo "🦀 Building Rust server..."
cd server
cargo build --release
cd ..
echo

echo "✅ Build complete!"
echo
echo "🎉 You can now run the server:"
echo "   cd server && ./target/release/image-processor-server"
echo
echo "Then open http://localhost:3000 in your browser"
echo
echo "Or use Docker:"
echo "   docker-compose up -d"
