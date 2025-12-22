# Image Optimizer - Copilot Instructions

## Project Overview
Single-file Python desktop application for image optimization (single files or batch folders) using PyQt5 and Pillow.
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
- **HEIC Support:** Uses `pillow_heif.register_heif_opener()` globally at module level.
- **Processing Order:** Crop → Resize → Format Conversion → Save
- **Cropping Logic:**
  - Center-crop: calculates `(left, top, right, bottom)` from image center.
  - Validates crop dimensions against actual image size (`min(crop, actual)`).
  - Updates dimensions after crop for subsequent resize calculations.
- **Resizing Strategy:**
  - Uses `thumbnail()` only if target < current size (never upscales).
  - Prefers `Image.Resampling.LANCZOS`, falls back to `Image.ANTIALIAS` for older Pillow versions.
- **Transparency Handling:**
  - `JPEG`: Flattens RGBA/LA/P to white background via `Image.new("RGB", ...)` + `paste()`.
  - `WebP/PNG`: Preserves RGBA directly (Pillow handles natively).
  - Others: Converts to RGB (loses transparency).
- **Format-Specific Save Options:**
  - `JPEG`: `quality`, `optimize=True`, `progressive=True`.
  - `PNG`: `optimize=True`.
  - `WebP`: `quality`, `method=6` (slowest, best compression).

### 3. UI & Theming
- **Styling:** Custom "iOS-like" theme applied in `ImageOptimizerWindow.apply_styles()`.
- **Custom Widgets:** `DragDropLineEdit` handles both file and folder drag-and-drop events.
- **Input Methods:** Two browse buttons ("Folder" and "File") plus drag & drop support.
- **Icons:** Uses `QStyle.SP_*` standard icons where possible.

### 4. File Discovery (`get_all_image_files` / Single File Mode)
- **Folder Mode:** Returns list of `(absolute_path, relative_path)` tuples.
  - **Exclusion Logic:** Automatically skips `optimized/` folder when not overwriting.
  - Recursive mode: Uses `dirs.remove("optimized")` in `os.walk()` to prune traversal.
  - Non-recursive: Uses `os.scandir()` for efficiency, filters by path comparison.
- **Single File Mode:** Detects if input is a file via `os.path.isfile()`, creates single-item list `[(full_path, filename)]`.
  - Output path for single files: adds `_optimized` suffix when not overwriting (e.g., `photo.jpg` → `photo_optimized.jpg`).
- **Error Handling:** Silently skips individual file errors (e.g., permission issues), raises `OSError` only for directory read failures.

### 5. State Management (`_update_option_states`)
- **Mutual Exclusivity:** "Overwrite Originals" button is disabled when output format ≠ "Original".
- Prevents invalid configuration (can't overwrite with format change).
- Called on format combo change and overwrite button toggle.

### 6. Error Reporting Pattern
- **Collection:** Errors accumulated in `error_messages` list during batch processing.
- **Advanced UI (>10 errors):** Custom `QMessageBox` with embedded `QScrollArea` + `QTextEdit`.
- **Simple UI (≤10 errors):** Standard `QMessageBox.setDetailedText()`.
- **Per-file context:** Each error includes filename and operation context.

## Critical Workflows

### Development
- **Run:** `python3 image_optimizer.py` (macOS) or `python image_optimizer.py` (Windows)
- **Dependencies:** `pip install -r requirements.txt` (PyQt5, Pillow, pillow-heif, pyinstaller)

### Build (PyInstaller)
- **macOS ARM:** `./build_macos.sh` → outputs `dist/image_optimizer.app`
- **Windows x64:** `build_windows.bat` → outputs `dist\image_optimizer.exe`
- **Note:** PyInstaller cannot cross-compile - must build on target platform
- **Spec:** Configured for windowed application (`console=False`), single executable with `upx=True`

## Common Tasks & Snippets

### Adding a New Format
1. Update `optimize_image` format detection logic (~L76-98) to map extension to PIL format string.
2. Add format-specific save kwargs (~L126-154) if needed.
3. Update `ImageOptimizerWindow.__init__` output_format_combo items (~L350).
4. Update file dialog filter in `browse_file()` method to include new extension.
5. Ensure Pillow supports the format or add registration hook (like `pillow_heif.register_heif_opener()`).

### File Processing Pattern
```python
# Single file mode detection
is_single_file = os.path.isfile(input_path)
if is_single_file:
    # Single file: [(full_path, filename)]
    image_files = [(input_path, os.path.basename(input_path))]
    # Output: same dir with "_optimized" suffix if not overwriting
else:
    # Folder mode: returns (absolute_path, relative_path) tuples
    image_files = self.get_all_image_files(directory, recursive=True)
    # Returns: [("/full/path/to/image.jpg", "image.jpg"),
    #           ("/full/path/to/subdir/photo.png", "subdir/photo.png")]

# start_optimization reconstructs paths maintaining structure
for input_file_path, rel_path in image_files:
    output_path = os.path.join(output_base_dir, rel_path)
    # Folder: creates 'optimized/subdir/photo.png' mirroring source
    # Single file: creates 'photo_optimized.jpg' in same directory
```

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
