# Image Optimizer - Copilot Instructions

## Project Overview

Single-file Python desktop application for batch image optimization using PyQt5 and Pillow.

- **Core Logic:** `image_optimizer.py` contains both GUI and processing logic.
- **Build System:** PyInstaller (`image_optimizer.spec`).

## Architecture & Patterns

### 1. Application Structure

- **Monolithic Script:** `image_optimizer.py` houses `ImageOptimizerWindow` (GUI), `optimize_image` (Logic), and custom widgets.
- **Processing Loop:**
    - Runs on the **Main Thread**.
    - Uses `QApplication.processEvents()` inside the processing loop to maintain UI responsiveness.
    - **Constraint:** Do not refactor to `QThread` unless explicitly requested (keeps architecture simple).

### 2. Image Processing (`optimize_image`)

- **Return Pattern:** Returns `True` on success, or a `str` error message on failure.
- **HEIC Support:** Uses `pillow_heif.register_heif_opener()` globally.
- **Transparency:**
    - `JPEG`: Flattens to white background.
    - `WebP/PNG`: Preserves transparency (Pillow handles RGBA).
    - Others: Converts to RGB (loses transparency).

### 3. UI & Theming

- **Styling:** Custom "iOS-like" theme applied in `ImageOptimizerWindow.apply_styles()`.
- **Custom Widgets:** `DragDropLineEdit` handles folder drag-and-drop events.
- **Icons:** Uses `QStyle.SP_*` standard icons where possible.

## Critical Workflows

### Development

- **Run:** `python image_optimizer.py`
- **Environment:** Requires `PyQt5`, `Pillow`, `pillow_heif`.

### Build (PyInstaller)

- **Command:** `pyinstaller image_optimizer.spec`
- **Output:** Generates `dist/image_optimizer` (or `.app` on macOS).
- **Spec:** Configured for a windowed application (`console=False`).

## Common Tasks & Snippets

### Adding a New Format

1. Update `optimize_image` logic to handle the new format string.
2. Update `ImageOptimizerWindow.output_format_combo` items.
3. Ensure `pillow` supports the format or add a registration hook.

### Error Handling Pattern

```python
# In optimize_image
try:
    # ... operation ...
    return True
except Exception as e:
    return f"Context: {str(e)}"

# In GUI Loop
result = optimize_image(...)
if result is not True:
    errors.append(result)
```
