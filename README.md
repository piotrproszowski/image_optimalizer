# Next-Gen Batch Image Processor (macOS ARM)

A high-performance image processing application built with Tauri v2, Rust, and React, optimized for Apple Silicon.

## Prerequisites

Before running the application, ensure you have the following installed via Homebrew:

```bash
# Core dependencies
brew install vips protobuf pkg-config

# Verify installation
vips --version
pkg-config --libs vips
```

## Development Setup

1.  **Install Frontend Dependencies**:
    ```bash
    npm install
    ```

2.  **Run Development Server**:
    ```bash
    npm run tauri dev
    ```

## Architecture

-   **Backend**: Rust (src-tauri)
    -   `libvips`: Image processing engine (dynamically linked).
    -   `ort`: AI Inference (ONNX Runtime) with CoreML acceleration.
    -   `Tauri v2`: Application framework.
-   **Frontend**: React + TypeScript + Vite
    -   `Shadcn/UI`: Component library.
    -   `TanStack Query`: State management.
    -   `Tailwind CSS`: Styling.

## Troubleshooting

-   **Linker Errors**: If you see errors about missing `vips` or `glib`, ensure `.cargo/config.toml` exists and points validly to `/opt/homebrew/lib/pkgconfig`.
-   **Permissions**: If "Open Folder" doesn't work, check `System Settings > Privacy & Security > Files and Folders`.