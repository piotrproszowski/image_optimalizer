"""
Image Optimizer
Author: Piotr Proszowski
"""

import os
import sys

# import pillow_heif  # Moved to lazy init
from PyQt5.QtCore import (
    QEasingCurve,
    QMimeData,
    QPropertyAnimation,
    QSettings,
    QSize,
    Qt,
    pyqtProperty,
    pyqtSignal,
)
from PyQt5.QtGui import (
    QColor,
    QDragEnterEvent,
    QDropEvent,
    QFontMetrics,
    QPainter,
    QPen,
)
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QStyle,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


def _lazy_init_heif():
    """Lazy initialization of HEIF support to speed up startup."""
    import pillow_heif

    pillow_heif.register_heif_opener()


_heif_initialized = False


def _ensure_heif_support():
    """Ensure HEIF support is initialized before processing images."""
    global _heif_initialized
    if not _heif_initialized:
        _lazy_init_heif()
        _heif_initialized = True


def optimize_image(
    input_path,
    output_path,
    max_width,
    max_height,
    quality,
    output_format="original",
    crop_enabled=False,
    crop_width=None,
    crop_height=None,
):
    """Optimize image: crop, resize, change format, and save."""
    _ensure_heif_support()

    if quality < 1 or quality > 100:
        return f"Invalid quality value: {quality} (must be 1-100)"

    if crop_enabled:
        if crop_width and (crop_width < 1 or crop_width > 50000):
            return f"Invalid crop width: {crop_width} (must be 1-50000)"
        if crop_height and (crop_height < 1 or crop_height > 50000):
            return f"Invalid crop height: {crop_height} (must be 1-50000)"

    if max_width > 0 and (max_width < 1 or max_width > 50000):
        return f"Invalid width: {max_width} (must be 1-50000)"
    if max_height > 0 and (max_height < 1 or max_height > 50000):
        return f"Invalid height: {max_height} (must be 1-50000)"

    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with Image.open(input_path) as img:
            original_mode = img.mode
            img_width, img_height = img.size

            if crop_enabled and crop_width and crop_height:
                actual_crop_width = min(crop_width, img_width)
                actual_crop_height = min(crop_height, img_height)
                if actual_crop_width > 0 and actual_crop_height > 0:
                    left = (img_width - actual_crop_width) / 2
                    top = (img_height - actual_crop_height) / 2
                    right = (img_width + crop_width) / 2
                    bottom = (img_height + crop_height) / 2
                    img = img.crop((int(left), int(top), int(right), int(bottom)))
                    img_width, img_height = img.size  # Update dimensions after crop

            target_width = (
                max_width if isinstance(max_width, int) and max_width > 0 else img_width
            )
            target_height = (
                max_height
                if isinstance(max_height, int) and max_height > 0
                else img_height
            )

            if target_width < img_width or target_height < img_height:
                try:
                    img.thumbnail(
                        (target_width, target_height), Image.Resampling.LANCZOS
                    )
                except AttributeError:  # Fallback for older Pillow versions
                    img.thumbnail((target_width, target_height), Image.ANTIALIAS)

            base, _ = os.path.splitext(output_path)
            save_format = str(output_format).lower()  # Ensure lowercase string

            if save_format == "original":
                _, ext = os.path.splitext(input_path)
                output_path = base + ext.lower()
                ext_lower = ext.lower()
                if ext_lower in (".jpg", ".jpeg"):
                    save_format = "jpeg"
                elif ext_lower == ".png":
                    save_format = "png"
                elif ext_lower == ".webp":
                    save_format = "webp"
                elif ext_lower in (".heic", ".heif"):
                    save_format = "heif"
                else:
                    try:
                        save_format = img.format  # Use PIL's detected format
                        if not save_format:  # If format is None
                            raise ValueError("Could not detect original format")
                    except Exception:
                        return f"Could not determine original save format for {os.path.basename(input_path)}"
            elif save_format in ["webp", "jpg", "jpeg", "png"]:
                file_ext = ".jpg" if save_format == "jpeg" else ("." + save_format)
                output_path = base + file_ext
                if save_format == "jpg":
                    save_format = "jpeg"  # Use JPEG for PIL
            else:
                return f"Unsupported output format specified: {output_format}"

            save_kwargs = {}
            img_to_save = img  # Start with the potentially resized/cropped image

            if save_format == "jpeg" and img_to_save.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", img_to_save.size, (255, 255, 255))
                try:
                    if img_to_save.mode == "P":
                        img_to_save = img_to_save.convert("RGBA")
                    background.paste(img_to_save, mask=img_to_save.split()[-1])
                    img_to_save = background  # Save the flattened image
                except (
                    IndexError
                ):  # Handle cases like LA where split might not have enough channels
                    img_to_save = img_to_save.convert(
                        "RGB"
                    )  # Fallback to simple conversion
                except Exception:
                    img_to_save = img_to_save.convert("RGB")
            else:
                if save_format == "webp" and img_to_save.mode in ("RGBA", "LA"):
                    pass  # Pillow handles RGBA correctly with 'lossless' or by setting background
                elif save_format == "png" and img_to_save.mode in ("RGBA", "LA"):
                    pass  # Pillow attempts to handle transparency
                else:
                    img_to_save = img_to_save.convert("RGB")

            pil_save_format = save_format.upper()  # PIL expects uppercase format string

            if pil_save_format == "JPEG":
                save_kwargs["quality"] = quality
                save_kwargs["optimize"] = True
                save_kwargs["progressive"] = True  # Often good for web jpegs
            elif pil_save_format == "PNG":
                save_kwargs["optimize"] = True
            elif pil_save_format == "WEBP":
                save_kwargs["quality"] = quality
                save_kwargs["method"] = (
                    6  # 0 (fastest) to 6 (slowest, best compression)
                )
                try:
                    if img_to_save.mode == "RGBA":
                        pass  # Assume Pillow handles RGBA correctly
                    img_to_save.save(output_path, format=pil_save_format, **save_kwargs)
                except OSError as webp_e:
                    if "cannot write mode RGBA" in str(webp_e):
                        img_rgb = img_to_save.convert("RGB")
                        img_rgb.save(output_path, format=pil_save_format, **save_kwargs)
                    else:
                        raise  # Re-raise other OS errors
                return True  # Return early for WebP after specific save logic

            img_to_save.save(output_path, format=pil_save_format, **save_kwargs)

        return True
    except PermissionError:
        return f"Cannot access file (check permissions): {os.path.basename(input_path)}"
    except OSError:
        return f"File system error: {os.path.basename(input_path)}"
    except MemoryError:
        return f"Image too large for available memory: {os.path.basename(input_path)}"
    except ValueError:
        return f"Invalid image data: {os.path.basename(input_path)}"
    except Exception as e:
        if "UnidentifiedImageError" in str(type(e).__name__):
            return f"Cannot identify image file: {os.path.basename(input_path)}"
        return (
            f"Error processing {os.path.basename(input_path)}: Unknown error occurred"
        )


def is_image_file(filename):
    """Check if a file is an image based on its extension."""
    image_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".tiff",
        ".webp",
        ".heic",
        ".heif",
    }
    return os.path.splitext(filename)[1].lower() in image_extensions


class DragDropLineEdit(QLineEdit):
    """Custom QLineEdit that accepts drag and drop of folders and files."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events for the line edit."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isdir(path) or (
                    os.path.isfile(path) and is_image_file(path)
                ):
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event: QDropEvent):
        """Handle drop events for the line edit."""
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isdir(path):
                self.setText(path)
                event.acceptProposedAction()
                return
            elif os.path.isfile(path) and is_image_file(path):
                self.setText(path)
                event.acceptProposedAction()
                return


class ToggleSwitch(QWidget):
    """Modern toggle switch widget with clear ON/OFF visual states."""

    toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self._thumb_position = 0.0
        self._is_initializing = True
        self.setFixedSize(50, 28)
        self.setCursor(Qt.PointingHandCursor)

        self._animation = QPropertyAnimation(self, b"thumb_position", self)
        self._animation.setEasingCurve(QEasingCurve.InOutCubic)
        self._animation.setDuration(200)
        self._is_initializing = False

    def _get_thumb_position(self):
        return self._thumb_position

    def _set_thumb_position(self, position):
        self._thumb_position = position
        self.update()

    thumb_position = pyqtProperty(float, _get_thumb_position, _set_thumb_position)

    def paintEvent(self, event):
        from PyQt5.QtCore import QRectF

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self._checked:
            track_color = QColor("#4CAF50")  # Green when ON
            thumb_color = QColor("#FFFFFF")
        else:
            track_color = QColor("#999999")  # Gray when OFF
            thumb_color = QColor("#FFFFFF")

        track_rect = QRectF(0, 0, self.width(), self.height())
        painter.setPen(Qt.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(track_rect, self.height() / 2, self.height() / 2)

        thumb_radius = (self.height() - 6) / 2
        left_pos = thumb_radius + 3
        right_pos = self.width() - thumb_radius - 3
        thumb_x = left_pos + (right_pos - left_pos) * self._thumb_position
        thumb_y = self.height() / 2

        painter.setBrush(thumb_color)
        painter.setPen(QPen(QColor("#E0E0E0"), 1))
        painter.drawEllipse(
            int(thumb_x - thumb_radius),
            int(thumb_y - thumb_radius),
            int(thumb_radius * 2),
            int(thumb_radius * 2),
        )

    def mousePressEvent(self, event):
        if self._animation.state() == QPropertyAnimation.Running:
            return

        self._checked = not self._checked
        self._animation.setStartValue(self._thumb_position)
        self._animation.setEndValue(1.0 if self._checked else 0.0)
        self._animation.start()
        self.toggled.emit(self._checked)

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            target_position = 1.0 if self._checked else 0.0

            if self._is_initializing or not self.isVisible():
                self._thumb_position = target_position
                self.update()
            else:
                self._animation.setStartValue(self._thumb_position)
                self._animation.setEndValue(target_position)
                self._animation.start()


class ImageOptimizerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Optimizer")
        self.setGeometry(100, 100, 600, 620)

        self.settings = QSettings("PiotrProszowski", "ImageOptimizer")
        self.is_dark_mode = self.settings.value("theme/dark_mode", True, type=bool)

        self.author_label = QLabel("© 2024 Piotr Proszowski")
        self.author_label.setAlignment(Qt.AlignRight)

        self._create_menu_bar()

        app = QApplication.instance()
        try:
            if app:
                self.style_icons = {
                    "save": app.style().standardIcon(QStyle.SP_DialogSaveButton),
                    "overwrite": app.style().standardIcon(
                        QStyle.SP_DialogApplyButton
                    ),  # Or SP_DialogSaveButton
                    "folder": app.style().standardIcon(QStyle.SP_DirOpenIcon),
                    "crop": app.style().standardIcon(
                        QStyle.SP_FileDialogListView
                    ),  # Alternative crop icon
                    "quality": app.style().standardIcon(
                        QStyle.SP_FileDialogDetailedView
                    ),  # Icon for quality
                    "browse": app.style().standardIcon(QStyle.SP_DialogOpenButton),
                    "info": app.style().standardIcon(
                        QStyle.SP_MessageBoxInformation
                    ),  # For tooltips? Not directly used
                    "warning": app.style().standardIcon(
                        QStyle.SP_MessageBoxWarning
                    ),  # For tooltips?
                    "format": app.style().standardIcon(
                        QStyle.SP_ComputerIcon
                    ),  # Icon for format dropdown
                }
            else:
                self.is_dark_mode = False
                self.style_icons = {}  # No icons if no app instance
        except Exception:
            self.style_icons = {}

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(12)  # Adjust spacing
        layout.setContentsMargins(15, 15, 15, 15)  # Adjust margins

        input_group = QGroupBox("Input")
        input_group.setToolTip("Select a folder or a single image file to optimize.")
        input_layout = QHBoxLayout(input_group)
        input_layout.setSpacing(10)
        self.folder_input = DragDropLineEdit()
        self.folder_input.setPlaceholderText(
            "Drag & drop folder/file or click Browse..."
        )
        self.folder_input.setToolTip(
            "Path to a folder or single image file. You can also drag and drop here."
        )
        browse_button = QPushButton("📁 Browse...")
        browse_button.setToolTip("Select a folder or single image file.")
        browse_button.clicked.connect(self.browse_smart)

        input_layout.addWidget(self.folder_input)
        input_layout.addWidget(browse_button)
        layout.addWidget(input_group)

        settings_group = QGroupBox("Processing Settings")
        settings_group.setToolTip("Configure image resizing, cropping, and quality.")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setSpacing(10)

        resolution_layout = QHBoxLayout()
        resolution_layout.setSpacing(10)
        self.resolution_presets = {
            "Original": None,
            "HD (1280x720)": (1280, 720),
            "Full HD (1920x1080)": (1920, 1080),
            "2K (2560x1440)": (2560, 1440),
            "4K (3840x2160)": (3840, 2160),
            "Custom": (-1, -1),
        }
        resolution_label = QLabel("Max Resolution:")
        resolution_label.setToolTip(
            "Set maximum dimensions for optimized images. 'Original' keeps original size (unless cropped)."
        )
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(self.resolution_presets.keys())
        self.resolution_combo.setCurrentText("Full HD (1920x1080)")
        self.resolution_combo.currentTextChanged.connect(self.on_resolution_changed)
        self.resolution_combo.setToolTip(
            "Select a preset maximum resolution or 'Custom'."
        )
        resolution_layout.addWidget(resolution_label)
        resolution_layout.addWidget(self.resolution_combo, 1)

        self.custom_resolution_widget = QWidget()
        self.custom_resolution_widget.setToolTip(
            "Define custom maximum width and height when 'Custom' resolution is selected."
        )
        custom_resolution_layout = QHBoxLayout(self.custom_resolution_widget)
        custom_resolution_layout.setContentsMargins(0, 0, 0, 0)
        custom_resolution_layout.setSpacing(5)
        self.width_input = QLineEdit()
        self.width_input.setToolTip("Maximum width in pixels.")
        self.height_input = QLineEdit()
        self.height_input.setToolTip("Maximum height in pixels.")
        custom_resolution_layout.addWidget(QLabel("W:"))
        custom_resolution_layout.addWidget(self.width_input)
        custom_resolution_layout.addWidget(QLabel("H:"))
        custom_resolution_layout.addWidget(self.height_input)
        resolution_layout.addWidget(self.custom_resolution_widget)
        self.custom_resolution_widget.setVisible(False)
        settings_layout.addLayout(resolution_layout)
        self.on_resolution_changed(self.resolution_combo.currentText())

        crop_main_layout = QVBoxLayout()
        crop_main_layout.setSpacing(8)

        crop_toggle_layout = QHBoxLayout()
        crop_toggle_layout.setSpacing(10)

        crop_label = QLabel("✂️ Crop to Size (center)")
        crop_label.setToolTip(
            "Enable to crop images to exact dimensions from center before resizing."
        )
        crop_toggle_layout.addWidget(crop_label)

        self.crop_switch = ToggleSwitch()
        self.crop_switch.setToolTip("Toggle to enable/disable center cropping")
        self.crop_switch.toggled.connect(self.on_crop_toggled)
        crop_toggle_layout.addWidget(self.crop_switch)
        crop_toggle_layout.addStretch(1)

        crop_main_layout.addLayout(crop_toggle_layout)

        self.crop_dimensions_widget = QWidget()
        self.crop_dimensions_widget.setToolTip(
            "Define the target width and height for cropping."
        )
        crop_dimensions_layout = QHBoxLayout(self.crop_dimensions_widget)
        crop_dimensions_layout.setContentsMargins(20, 0, 0, 0)
        crop_dimensions_layout.setSpacing(10)
        crop_dimensions_layout.addWidget(QLabel("Width:"))
        self.crop_width_input = QLineEdit("800")
        self.crop_width_input.setToolTip("Target crop width in pixels.")
        self.crop_width_input.setFixedWidth(80)
        crop_dimensions_layout.addWidget(self.crop_width_input)
        crop_dimensions_layout.addWidget(QLabel("Height:"))
        self.crop_height_input = QLineEdit("800")
        self.crop_height_input.setToolTip("Target crop height in pixels.")
        self.crop_height_input.setFixedWidth(80)
        crop_dimensions_layout.addWidget(self.crop_height_input)
        crop_dimensions_layout.addStretch(1)
        self.crop_dimensions_widget.setVisible(False)

        crop_main_layout.addWidget(self.crop_dimensions_widget)
        settings_layout.addLayout(crop_main_layout)

        quality_layout = QHBoxLayout()
        quality_layout.setSpacing(10)
        quality_label = QLabel("Quality:")
        quality_label.setToolTip(
            "Set the image quality for saving (1-100). Lower values mean smaller files but lower quality."
        )
        self.quality_input = QLineEdit("85")
        self.quality_input.setToolTip(
            "Enter a value between 1 (lowest quality) and 100 (highest quality). Default is 85."
        )
        fm = QFontMetrics(self.quality_input.font())
        self.quality_input.setFixedWidth(
            fm.horizontalAdvance("100") + 20
        )  # Adjusted width slightly
        quality_layout.addWidget(quality_label)
        quality_layout.addWidget(self.quality_input)
        quality_layout.addStretch(1)  # Push to left
        settings_layout.addLayout(
            quality_layout
        )  # Add quality layout to settings group

        layout.addWidget(settings_group)

        output_scope_group = QGroupBox("Output & Scope")
        output_scope_group.setToolTip(
            "Configure output format, file handling, and folder scope."
        )
        output_scope_layout = QVBoxLayout(
            output_scope_group
        )  # Changed to QVBoxLayout for format row
        output_scope_layout.setSpacing(10)

        format_layout = QHBoxLayout()  # New layout for format selection
        format_label = QLabel("Output Format:")
        if "format" in self.style_icons:
            try:
                pixmap = self.style_icons["format"].pixmap(16, 16)  # Try getting pixmap
                format_label.setPixmap(pixmap)
            except Exception:  # Catch potential errors during pixmap creation
                pass  # Ignore if icon cannot be set
        format_label.setToolTip("Choose the file format for the optimized images.")
        self.output_format_combo = QComboBox()  # NEW ComboBox
        self.output_format_combo.addItems(
            ["Original", "WebP", "JPG", "PNG"]
        )  # Standard formats
        self.output_format_combo.setCurrentText("WebP")  # Default to WebP
        self.output_format_combo.setToolTip(
            "Select output format. 'Original' keeps the source format.\\nNote: Overwrite is only possible with 'Original' format."
        )
        self.output_format_combo.currentTextChanged.connect(
            self._update_option_states
        )  # Connect signal
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.output_format_combo, 1)  # Allow combo to expand
        output_scope_layout.addLayout(format_layout)  # Add format row first

        overwrite_recursive_layout = (
            QHBoxLayout()
        )  # Layout for the buttons below format
        overwrite_recursive_layout.setSpacing(10)

        overwrite_label = QLabel("Overwrite Originals")
        overwrite_label.setToolTip(
            "Replace original files (only possible if output format is 'Original').\\nWARNING: This action cannot be undone."
        )
        overwrite_recursive_layout.addWidget(overwrite_label)

        self.overwrite_switch = ToggleSwitch()
        self.overwrite_switch.setChecked(False)
        self.overwrite_switch.setToolTip(
            "Toggle to enable/disable overwriting original files"
        )
        self.overwrite_switch.toggled.connect(self._update_option_states)
        overwrite_recursive_layout.addWidget(self.overwrite_switch)

        overwrite_recursive_layout.addStretch(1)

        subfolders_label = QLabel("Process Subfolders")
        subfolders_label.setToolTip(
            "Include images found in subfolders of the selected input folder."
        )
        overwrite_recursive_layout.addWidget(subfolders_label)

        self.recursive_switch = ToggleSwitch()
        self.recursive_switch.setChecked(True)
        self.recursive_switch.setToolTip(
            "Toggle to enable/disable recursive folder processing"
        )
        overwrite_recursive_layout.addWidget(self.recursive_switch)
        output_scope_layout.addLayout(overwrite_recursive_layout)  # Add button row

        layout.addWidget(output_scope_group)
        self._update_option_states()  # Set initial states

        layout.addSpacing(5)  # Reduced spacing
        self.progress_bar = QProgressBar()
        self.progress_bar.setToolTip("Shows the progress of the optimization process.")
        layout.addWidget(self.progress_bar)
        self.status_label = QLabel("Ready")
        self.status_label.setToolTip(
            "Displays the current status or the result of the last operation."
        )
        layout.addWidget(self.status_label)
        layout.addSpacing(5)  # Reduced spacing

        start_button = QPushButton("Start Optimization")
        start_button.setObjectName("StartButton")
        start_button.setToolTip("Begin processing images with the selected settings.")
        start_button.clicked.connect(self.start_optimization)
        layout.addWidget(start_button)

        layout.addStretch(1)
        self.author_label.setToolTip("Application author information.")  # Added tooltip
        layout.addWidget(self.author_label)

        self.apply_styles()  # Apply after all widgets are created

    def _update_option_states(self):
        """Enable/disable Overwrite button based on Output Format selection."""
        if hasattr(self, "overwrite_button"):
            self.overwrite_button.blockSignals(True)
        if hasattr(self, "output_format_combo"):
            self.output_format_combo.blockSignals(True)

        try:
            if hasattr(self, "output_format_combo"):
                selected_format = self.output_format_combo.currentText()
                is_original_format = selected_format == "Original"

                if hasattr(self, "overwrite_switch"):
                    if hasattr(self.overwrite_switch, "_animation"):
                        self.overwrite_switch._animation.stop()

                    if not is_original_format:
                        if self.overwrite_switch.isChecked():
                            self.overwrite_switch.setChecked(False)
                        self.overwrite_switch.setEnabled(False)
                        self.overwrite_switch.setToolTip(
                            "Disabled because output format is not 'Original'."
                        )
                    else:
                        self.overwrite_switch.setEnabled(True)
                        self.overwrite_switch.setToolTip(
                            "Toggle to enable/disable overwriting original files"
                        )
        finally:
            if hasattr(self, "overwrite_switch"):
                self.overwrite_switch.blockSignals(False)
            if hasattr(self, "output_format_combo"):
                self.output_format_combo.blockSignals(False)

    def _create_menu_bar(self):
        """Create menu bar with theme toggle."""
        menubar = self.menuBar()

        view_menu = menubar.addMenu("View")

        self.theme_action = QAction(
            "🌙 Dark Mode" if not self.is_dark_mode else "☀️ Light Mode", self
        )
        self.theme_action.setCheckable(False)
        self.theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(self.theme_action)

    def toggle_theme(self):
        """Toggle between light and dark theme."""
        self.is_dark_mode = not self.is_dark_mode
        self.settings.setValue("theme/dark_mode", self.is_dark_mode)
        self.theme_action.setText(
            "🌙 Dark Mode" if not self.is_dark_mode else "☀️ Light Mode"
        )
        self.apply_styles()

    def apply_styles(self):
        font_family = "System"  # Use system font, closest to San Francisco on macOS
        background_color = "#F2F2F7" if not self.is_dark_mode else "#1C1C1E"
        text_color = "#000000" if not self.is_dark_mode else "#FFFFFF"
        secondary_text_color = "#8A8A8E" if not self.is_dark_mode else "#8D8D92"
        accent_color = "#007AFF"  # iOS Blue
        button_text_color = "#FFFFFF"
        control_bg_color = "#FFFFFF" if not self.is_dark_mode else "#2C2C2E"
        control_border_color = "#C6C6C8" if not self.is_dark_mode else "#3A3A3C"
        separator_color = "#D1D1D6" if not self.is_dark_mode else "#38383A"
        menubar_bg = "#F2F2F7" if not self.is_dark_mode else "#1C1C1E"
        menubar_text = "#000000" if not self.is_dark_mode else "#FFFFFF"
        button_hover_color = "#E5E5EA" if not self.is_dark_mode else "#3A3A3C"
        menu_selected_bg = "#007AFF"
        checked_button_bg_color = (
            "#D1E7FF" if not self.is_dark_mode else "#004080"
        )  # Light blue / Darker blue for checked
        checked_button_border_color = accent_color

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {background_color};
                font-family: {font_family};
            }}
            QMenuBar {{
                background-color: {menubar_bg};
                color: {menubar_text};
                border-bottom: 1px solid {separator_color};
                padding: 4px;
            }}
            QMenuBar::item {{
                background-color: transparent;
                padding: 4px 8px;
                border-radius: 4px;
            }}
            QMenuBar::item:selected {{
                background-color: {button_hover_color};
            }}
            QMenu {{
                background-color: {control_bg_color};
                color: {text_color};
                border: 1px solid {control_border_color};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 24px 6px 8px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {menu_selected_bg};
                color: #FFFFFF;
            }}
            QWidget {{ font-family: {font_family}; }}
            QGroupBox {{
                 background-color: transparent; /* Make groupbox background transparent */
                 border: 1px solid {separator_color};
                 border-radius: 8px;
                 margin-top: 20px; /* Space for title */
                 font-size: 13px;
                 font-weight: 600; /* Semibold title */
                 color: {text_color};
             }}
             QGroupBox::title {{
                 subcontrol-origin: margin;
                 subcontrol-position: top left;
                 padding: 0 5px 5px 5px; /* Adjust padding */
                 margin-left: 10px; /* Indent title slightly */
                 color: {secondary_text_color};
                 background-color: {background_color}; /* Match window bg */
             }}
            QLabel {{
                color: {text_color};
                font-size: 14px;
                background-color: transparent; /* Ensure labels have transparent bg */
            }}
            QLineEdit {{
                background-color: {control_bg_color};
                color: {text_color};
                border: 1px solid {control_border_color};
                border-radius: 8px;
                padding: 8px 10px;
                font-size: 14px;
            }}
            QLineEdit:focus {{ border: 1px solid {accent_color}; }}
            QPushButton {{
                background-color: {control_bg_color};
                color: {accent_color};
                border: 1px solid {control_border_color};
                border-radius: 8px;
                padding: 8px 12px; /* Adjusted padding */
                font-size: 14px; /* Slightly smaller */
                font-weight: 500;
                min-width: 70px;
                text-align: center; /* Align text and icon center */
             }}
             /* Style for Toggle Buttons when Checked */
             QPushButton:checked {{
                 background-color: {checked_button_bg_color};
                 border: 1px solid {checked_button_border_color};
                 color: {accent_color}; /* Keep text color consistent */
                 font-weight: 600; /* Slightly bolder when checked */
             }}
             QPushButton#StartButton {{
                 background-color: {accent_color};
                 color: {button_text_color};
                 border: none;
                 padding: 10px 15px; /* Larger padding for main button */
                 font-size: 15px;
                 font-weight: 600;
             }}
             QPushButton#StartButton:hover {{ background-color: #005ECC; }}
             QPushButton:hover {{ background-color: #E5E5EA; }}
             QPushButton:checked:hover {{ background-color: #B8D9FF; }} /* Hover for checked state */

             QPushButton:disabled {{
                 background-color: #E5E5EA;
                 color: {secondary_text_color};
                 border: 1px solid #E0E0E0;
             }}
             QPushButton#StartButton:disabled {{
                  background-color: #A0A0A0;
                  color: #F0F0F0;
                  border: none;
             }}
             /* Ensure disabled checked buttons look distinct */
             QPushButton:checked:disabled {{
                   background-color: #D0D0D0;
                   border: 1px solid #C0C0C0;
                   color: {secondary_text_color};
             }}
             QComboBox {{ /* Styles remain similar */
                 background-color: {control_bg_color};
                 color: {text_color};
                 border: 1px solid {control_border_color};
                 border-radius: 8px;
                 padding: 8px 10px;
                 font-size: 14px;
                 min-height: 1.8em;
             }}
             QComboBox::drop-down {{ border: none; width: 20px; }}
             QComboBox QAbstractItemView {{
                 background-color: {control_bg_color}; color: {text_color};
                 border: 1px solid {control_border_color};
                 selection-background-color: {accent_color};
                 selection-color: {button_text_color};
                 padding: 5px; border-radius: 8px;
             }}
             QProgressBar {{ /* Styles remain similar */
                 border: 1px solid {control_border_color}; border-radius: 8px;
                 text-align: center; background-color: {control_bg_color};
                 color: {secondary_text_color}; font-size: 12px; height: 10px;
             }}
             QProgressBar::chunk {{
                 background-color: {accent_color}; border-radius: 7px; margin: 1px;
             }}
        """)
        self.author_label.setObjectName("AuthorLabel")

    def browse_smart(self):
        """Smart browse dialog that handles both files and folders."""
        dialog = QFileDialog(self)
        dialog.setWindowTitle("Select Folder or Image File")
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setOption(QFileDialog.ShowDirsOnly, False)
        dialog.setNameFilter(
            "Images (*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp *.heic *.heif);;All Files (*)"
        )

        if dialog.exec_():
            selected = dialog.selectedFiles()
            if selected:
                path = selected[0]
                if os.path.isdir(path) or (
                    os.path.isfile(path) and is_image_file(path)
                ):
                    self.folder_input.setText(path)

    def show_error(self, message):
        """Show styled error dialog."""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Error")
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)

        if self.is_dark_mode:
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #2C2C2E;
                    color: #FFFFFF;
                }
                QLabel {
                    color: #FFFFFF;
                    font-size: 14px;
                    min-width: 300px;
                }
                QPushButton {
                    background-color: #FF3B30;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 20px;
                    font-size: 14px;
                    font-weight: 600;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #CC2F26;
                }
            """)
        else:
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #FFFFFF;
                    color: #000000;
                }
                QLabel {
                    color: #000000;
                    font-size: 14px;
                    min-width: 300px;
                }
                QPushButton {
                    background-color: #FF3B30;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 20px;
                    font-size: 14px;
                    font-weight: 600;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #CC2F26;
                }
            """)

        msg_box.exec_()

    def show_info(self, message):
        """Show styled information dialog."""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle("Success")
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)

        if self.is_dark_mode:
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #2C2C2E;
                    color: #FFFFFF;
                }
                QLabel {
                    color: #FFFFFF;
                    font-size: 14px;
                    min-width: 300px;
                }
                QPushButton {
                    background-color: #007AFF;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 20px;
                    font-size: 14px;
                    font-weight: 600;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #005ECC;
                }
            """)
        else:
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #FFFFFF;
                    color: #000000;
                }
                QLabel {
                    color: #000000;
                    font-size: 14px;
                    min-width: 300px;
                }
                QPushButton {
                    background-color: #007AFF;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 20px;
                    font-size: 14px;
                    font-weight: 600;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #005ECC;
                }
            """)

        msg_box.exec_()

    def on_resolution_changed(self, text):
        is_custom = text == "Custom"
        is_original = text == "Original"
        self.custom_resolution_widget.setVisible(is_custom)
        if hasattr(self, "width_input") and hasattr(self, "height_input"):
            self.width_input.setEnabled(not is_original)
            self.height_input.setEnabled(not is_original)
        if not is_custom and not is_original:
            try:
                width, height = self.resolution_presets[text]
                if hasattr(self, "width_input") and hasattr(self, "height_input"):
                    self.width_input.setText(str(width))
                    self.height_input.setText(str(height))
            except KeyError:
                pass
        elif is_original:
            if hasattr(self, "width_input") and hasattr(self, "height_input"):
                self.width_input.setText("")
                self.height_input.setText("")
        elif is_custom:
            if hasattr(self, "width_input") and hasattr(self, "height_input"):
                if not self.width_input.text():
                    self.width_input.setText("1920")
                if not self.height_input.text():
                    self.height_input.setText("1080")

    def on_crop_toggled(self, checked):  # Slot for toggled signal receives boolean
        """Show/hide crop dimension inputs based on button state."""
        self.crop_dimensions_widget.setVisible(checked)

    def get_all_image_files(self, directory, recursive=False):
        """Get all image files, skipping 'optimized' dir if not overwriting."""
        image_files = []
        is_overwriting = self.overwrite_switch.isChecked()  # Check switch state
        optimized_dir_name = "optimized"  # Define once

        def handle_walk_error(error):
            pass

        try:
            if recursive:
                for root, dirs, files in os.walk(
                    directory, topdown=True, onerror=handle_walk_error
                ):
                    if not is_overwriting and optimized_dir_name in dirs:
                        dirs.remove(optimized_dir_name)

                    for filename in files:
                        full_path = os.path.join(root, filename)
                        try:
                            if os.path.isfile(full_path) and is_image_file(filename):
                                rel_path = os.path.relpath(full_path, directory)
                                image_files.append((full_path, rel_path))
                        except (OSError, PermissionError):
                            pass
            else:
                optimized_dir_path = os.path.join(directory, optimized_dir_name)
                for entry in os.scandir(directory):
                    if (
                        not is_overwriting
                        and entry.is_dir()
                        and entry.path == optimized_dir_path
                    ):
                        continue
                    if entry.is_file():
                        try:
                            if is_image_file(entry.name):
                                full_path = entry.path
                                rel_path = entry.name
                                image_files.append((full_path, rel_path))
                        except Exception:
                            pass
        except OSError as e:
            raise OSError(f"Could not read directory '{directory}': {e}")

        return image_files

    def start_optimization(self):
        input_path = self.folder_input.text()
        if not input_path or (
            not os.path.isdir(input_path) and not os.path.isfile(input_path)
        ):
            self.show_error("Please select a valid folder or image file.")
            return

        is_single_file = os.path.isfile(input_path)
        if is_single_file:
            if not is_image_file(input_path):
                self.show_error("Selected file is not a supported image format.")
                return
            directory = os.path.dirname(input_path)
            single_filename = os.path.basename(input_path)
        else:
            directory = input_path
            single_filename = None

        try:
            selected_resolution = self.resolution_combo.currentText()
            max_width, max_height = -1, -1
            if selected_resolution == "Custom":
                max_width = int(self.width_input.text())
                max_height = int(self.height_input.text())
                if not (0 < max_width):
                    raise ValueError("Max Width must be positive")
                if not (0 < max_height):
                    raise ValueError("Max Height must be positive")
            elif selected_resolution != "Original":
                max_width, max_height = self.resolution_presets[selected_resolution]

            quality = int(self.quality_input.text())
            if not (1 <= quality <= 100):
                raise ValueError("Quality must be between 1 and 100")

            crop_enabled = self.crop_switch.isChecked()
            crop_width = None
            crop_height = None
            if crop_enabled:
                crop_width_text = self.crop_width_input.text()
                crop_height_text = self.crop_height_input.text()
                if not crop_width_text or not crop_height_text:
                    raise ValueError(
                        "Crop dimensions cannot be empty when cropping is enabled"
                    )
                crop_width = int(crop_width_text)
                crop_height = int(crop_height_text)
                if not (0 < crop_width):
                    raise ValueError("Crop Width must be positive")
                if not (0 < crop_height):
                    raise ValueError("Crop Height must be positive")

            output_format = (
                self.output_format_combo.currentText().lower()
            )  # Get selected format
            overwrite_originals = self.overwrite_switch.isChecked()
            recursive = self.recursive_switch.isChecked()

            if overwrite_originals and output_format != "original":
                self.show_error(
                    "Configuration error: Can only overwrite originals if output format is 'Original'."
                )
                return

        except ValueError as e:
            self.show_error(f"Invalid input: {str(e)}")
            return
        except Exception as e:
            self.show_error(f"Setup error: {str(e)}")
            return

        try:
            if is_single_file:
                image_files = [(input_path, single_filename)]
            else:
                image_files = self.get_all_image_files(directory, recursive)
        except OSError as e:
            self.show_error(str(e))
            return
        except Exception as e:
            self.show_error(f"Directory read error: {str(e)}")
            return

        total_images = len(image_files)
        if total_images == 0:
            self.show_info(
                f"No images found to process in '{directory}'"
                + (" or its subfolders" if recursive else "")
            )
            return

        if overwrite_originals:
            if is_single_file:
                confirm_msg = f"You are about to permanently overwrite the original image '{single_filename}'.\\n\\nThis action cannot be undone. Are you sure you want to continue?"
            else:
                confirm_msg = (
                    f"You are about to permanently overwrite {total_images} original image(s) in '{directory}' "
                    + f"{'and its subfolders' if recursive else ''}.\\n\\n"
                    + "This action cannot be undone. Are you sure you want to continue?"
                )

            reply = QMessageBox.warning(
                self,
                "Confirm Overwrite",
                confirm_msg,
                QMessageBox.Yes | QMessageBox.Cancel,
                QMessageBox.Cancel,
            )
            if reply == QMessageBox.Cancel:
                self.status_label.setText("Ready")
                return

        processed = 0
        errors = 0
        error_messages = []
        self.progress_bar.setMaximum(total_images)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Starting optimization for {total_images} images...")
        QApplication.processEvents()

        if is_single_file:
            output_base_dir = directory if overwrite_originals else directory
        else:
            output_base_dir = (
                directory
                if overwrite_originals
                else os.path.join(directory, "optimized")
            )

        for input_file_path, rel_path in image_files:
            if is_single_file and not overwrite_originals:
                base_name, ext = os.path.splitext(single_filename)
                output_filename = f"{base_name}_optimized{ext}"
                output_path = os.path.join(output_base_dir, output_filename)
            else:
                output_path = os.path.join(output_base_dir, rel_path)

            if not overwrite_originals:
                try:
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                except OSError as e:
                    errors += 1
                    processed += 1
                    error_messages.append(f"- Dir Error {rel_path}: {e}")
                    self.progress_bar.setValue(processed)
                    self.status_label.setText(
                        f"Error creating dir for {os.path.basename(input_path)}..."
                    )
                    QApplication.processEvents()
                    continue

            current_max_width, current_max_height = -1, -1
            use_original_size = selected_resolution == "Original"
            if use_original_size:
                if not crop_enabled:
                    try:
                        with Image.open(input_file_path) as img_size_check:
                            current_max_width, current_max_height = img_size_check.size
                    except Exception as size_e:
                        errors += 1
                        processed += 1
                        error_messages.append(
                            f"- Size Error {os.path.basename(input_file_path)}: {size_e}"
                        )
                        self.progress_bar.setValue(processed)
                        QApplication.processEvents()
                        continue
            elif selected_resolution == "Custom":
                try:  # Re-read in case values were invalid during initial check but fixed
                    current_max_width = int(self.width_input.text())
                    current_max_height = int(self.height_input.text())
                    if not (0 < current_max_width and 0 < current_max_height):
                        raise ValueError("Invalid custom dims")
                except ValueError:
                    errors += 1
                    processed += 1
                    error_messages.append(
                        f"- Invalid Custom Dims for {os.path.basename(input_file_path)}"
                    )
                    self.progress_bar.setValue(processed)
                    QApplication.processEvents()
                    continue
            else:
                current_max_width, current_max_height = self.resolution_presets[
                    selected_resolution
                ]

            result = optimize_image(
                input_file_path,
                output_path,  # Pass base output path
                current_max_width,
                current_max_height,
                quality,
                output_format=output_format,  # Pass selected format
                crop_enabled=crop_enabled,
                crop_width=crop_width,
                crop_height=crop_height,
            )

            processed += 1
            if result is not True:
                errors += 1
                error_msg_str = str(result) if result is not None else "Unknown error"
                error_messages.append(
                    f"- {os.path.basename(input_file_path)}: {error_msg_str}"
                )
                self.status_label.setText(
                    f"Error processing {os.path.basename(input_file_path)}..."
                )
            else:
                self.status_label.setText(
                    f"Processed: {processed}/{total_images} - {os.path.basename(input_file_path)}"
                )

            self.progress_bar.setValue(processed)
            QApplication.processEvents()

        success_count = processed - errors
        summary_message = f"Optimization complete.\n\nSuccessfully processed: {success_count}\nErrors: {errors}"
        if errors > 0:
            detailed_errors = "\n".join(error_messages)
            try:  # Reuse advanced error box
                if len(error_messages) > 10:
                    msg_box = QMessageBox(self)
                    msg_box.setIcon(QMessageBox.Warning)
                    msg_box.setWindowTitle("Optimization Report with Errors")
                    msg_box.setText(summary_message + "\n\nError details:")
                    scroll = QScrollArea(msg_box)
                    scroll.setWidgetResizable(True)
                    scroll.setMinimumSize(400, 150)
                    content = QWidget()
                    scroll.setWidget(content)
                    lay = QVBoxLayout(content)
                    text_edit = QTextEdit()
                    text_edit.setPlainText(detailed_errors)
                    text_edit.setReadOnly(True)
                    try:
                        from PyQt5.QtWidgets import QSizePolicy

                        text_edit.setSizePolicy(
                            QSizePolicy.Expanding, QSizePolicy.Expanding
                        )
                    except ImportError:
                        pass
                    lay.addWidget(text_edit)
                    content.setLayout(lay)
                    msg_box_layout = msg_box.layout()
                    if hasattr(msg_box_layout, "addWidget"):
                        row_count = (
                            msg_box_layout.rowCount()
                            if hasattr(msg_box_layout, "rowCount")
                            else 2
                        )
                        col_count = (
                            msg_box_layout.columnCount()
                            if hasattr(msg_box_layout, "columnCount")
                            else 1
                        )
                        msg_box_layout.addWidget(scroll, row_count, 0, 1, col_count)
                    else:
                        msg_box.setDetailedText(detailed_errors)
                    if hasattr(msg_box, "setSizeGripEnabled"):
                        msg_box.setSizeGripEnabled(True)
                    msg_box.exec_()
                else:
                    msg_box = QMessageBox(self)
                    msg_box.setIcon(QMessageBox.Warning)
                    msg_box.setWindowTitle("Optimization Report with Errors")
                    msg_box.setText(summary_message)
                    msg_box.setDetailedText(detailed_errors)
                    msg_box.exec_()
            except Exception as report_e:
                self.show_error(
                    summary_message + f"\nCould not display detailed errors: {report_e}"
                )
        else:
            self.show_info(summary_message)

        self.status_label.setText("Ready")
        self.progress_bar.setValue(0)


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    window = ImageOptimizerWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
