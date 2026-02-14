# Next-Gen Batch Image Processor

A high-performance image processing application built with Tauri v2, Rust, and React, optimized for Apple Silicon.

**Now available in two modes:**
- **Desktop Application**: Native macOS/Windows/Linux app using Tauri
- **Web Application**: Server-deployed, browser-accessible version

## Deployment Modes

### Desktop Mode (Original)
Traditional desktop application with native file system access and local processing.

### Web Mode (New!)
Server-deployed application accessible via web browser. Perfect for:
- Centralized image processing services
- Team collaboration
- Cloud deployment
- No installation required for end users

📖 **See [DEPLOYMENT.md](./DEPLOYMENT.md) for complete web deployment guide**

## Prerequisites

### For Desktop Development

Before running the application, ensure you have the following installed via Homebrew:

```bash
# Core dependencies
brew install vips protobuf pkg-config

# Verify installation
vips --version
pkg-config --libs vips
```

### For Web Deployment

```bash
# macOS
brew install vips

# Ubuntu/Debian
sudo apt-get install libvips-dev

# Or use Docker (recommended)
docker-compose up
```

## Development Setup

### Desktop Application

1.  **Install Frontend Dependencies**:
    ```bash
    npm install
    ```

2.  **Run Development Server**:
    ```bash
    npm run tauri dev
    ```

### Web Application

1.  **Install Dependencies**:
    ```bash
    npm install
    ```

2.  **Run Development Servers**:
    ```bash
    # Terminal 1: Backend server
    npm run server:dev
    
    # Terminal 2: Frontend dev server
    npm run dev:web
    ```

3.  **Access**: Open http://localhost:1420

## Quick Deploy (Docker)

```bash
# Build and run with Docker
docker-compose up -d

# Access at http://localhost:3000
```

## Architecture

-   **Backend**: Rust (src-tauri for desktop, server for web)
    -   `libvips`: Image processing engine (dynamically linked).
    -   `ort`: AI Inference (ONNX Runtime) with CoreML acceleration.
    -   `Tauri v2`: Desktop framework (desktop mode).
    -   `Axum`: Web framework (web mode).
-   **Frontend**: React + TypeScript + Vite
    -   `Shadcn/UI`: Component library.
    -   `TanStack Query`: State management.
    -   `Tailwind CSS`: Styling.
    -   Dual-mode support: Desktop (Tauri APIs) and Web (HTTP APIs)

## Features

- ✨ High-performance image processing with libvips
- 🎨 Multiple output formats: WebP, AVIF, PNG, JPEG
- 🔧 Adjustable quality and compression settings
- 📏 Smart resizing with dimension limits
- 🔒 Privacy-focused metadata stripping
- 📦 Batch processing support
- 🎯 Drag-and-drop interface
- 🌐 Web deployment ready

## Troubleshooting

-   **Linker Errors**: If you see errors about missing `vips` or `glib`, ensure `.cargo/config.toml` exists and points validly to `/opt/homebrew/lib/pkgconfig`.
-   **Permissions**: If "Open Folder" doesn't work, check `System Settings > Privacy & Security > Files and Folders`.
-   **Web Mode CORS**: Configure CORS settings in server if accessing from different origin.
-   **Docker Issues**: Ensure libvips is properly installed in container.

## Documentation

- [Web Deployment Guide](./DEPLOYMENT.md) - Complete guide for server deployment
- [API Documentation](./DEPLOYMENT.md#api-endpoints) - REST API reference
- [Configuration](./DEPLOYMENT.md#environment-variables) - Environment setup

## License

See LICENSE file for details.