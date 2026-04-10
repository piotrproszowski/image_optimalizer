---
description: This file provides a comprehensive map of the codebase structure, key components, and data flow for understanding the overall architecture.
applyTo: '**'
---

# Codebase Map

## 1. Global Context

- **Stack**: Vite + React + TypeScript + Tailwind CSS (frontend), Tauri (Rust backend), Libvips (image processing)
- **Entry Point**: Frontend `src/main.tsx`, Backend `src-tauri/src/main.rs`
- **Key Patterns**: Tauri command invocation, React Query provider, Libvips-based processing pipeline

## 2. Key Workflows (Data Flow)

1. **Image Processing**: UI action -> `process_images` Tauri command -> `ImageProcessor::process_image` -> Libvips save
2. **Progress Updates**: `process_images` emits `progress_update` events -> UI listener (Tauri event)

## 3. Directory Structure & Logic

- 📂 **src/**
    - 📄 **main.tsx**
        - **Role**: React entry point, mounts app and `QueryClientProvider`.
        - **Deps**: React, ReactDOM, React Query.

    - 📄 **App.tsx**
        - **Role**: Primary UI for drag-and-drop, settings, and processing flow.
        - **Key Types**: `ProcessingStats`, `AppSettings`.
        - **Flow**: User selects files/folders -> invokes `process_images` -> listens for progress events.

    - 📂 **lib/**
        - 📄 **utils.ts**
            - **Role**: Shared utility helpers.

- 📂 **src-tauri/**
    - 📄 **tauri.conf.json**
        - **Role**: Tauri app configuration, build hooks, window settings, and bundled resources.

    - 📂 **src/**
        - 📄 **main.rs**
            - **Role**: Tauri bootstrap, libvips initialization, global allocator setup.
            - **Flow**: Initializes libvips -> calls `run()` from `lib.rs`.

        - 📄 **lib.rs**
            - **Role**: Tauri command registration and processing orchestration.
            - **Key Commands**:
                - `process_images(files, config, window)`.

        - 📄 **processing.rs**
            - **Role**: Core image processing pipeline using libvips.
            - **Key Types**: `ProcessingConfig`, `ImageProcessor`.
            - **Key Functions**:
                - `ImageProcessor::process_image(path, output_path, config)`.

        - 📄 **inference.rs**
            - **Role**: Placeholder for AI inference integration.

- 📂 **public/**
    - 📄 **favicon.png**
        - **Role**: App icon for the frontend.

- 📂 **resources/** (within `src-tauri/`)
    - 📂 **models/**
        - **Role**: Bundled AI model files for future inference.

- 📄 **package.json**
    - **Role**: Frontend scripts and dependencies.
