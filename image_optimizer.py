"""
Image Optimizer
Author: Piotr Proszowski
"""

from PIL import Image, UnidentifiedImageError
import os
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                            QProgressBar, QCheckBox, QFileDialog, QMessageBox,
                            QComboBox, QScrollArea, QTextEdit, QGroupBox)
from PyQt5.QtCore import Qt, QMimeData, QSize
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QFontMetrics

def optimize_image(input_path, output_path, max_width, max_height, quality, 
                   convert_to_webp=False, crop_enabled=False, crop_width=None, crop_height=None):
    """Optimize the image by optionally cropping, resizing, and optionally converting to webp format."""
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with Image.open(input_path) as img:
            img_width, img_height = img.size

            # --- Cropping Logic ---
            if crop_enabled and crop_width is not None and crop_height is not None:
                # Ensure crop dimensions are positive and not larger than the image
                crop_width = min(abs(crop_width), img_width)
                crop_height = min(abs(crop_height), img_height)

                if crop_width > 0 and crop_height > 0:
                    # Calculate coordinates for center crop
                    left = (img_width - crop_width) / 2
                    top = (img_height - crop_height) / 2
                    right = (img_width + crop_width) / 2
                    bottom = (img_height + crop_height) / 2
                    
                    # Perform crop
                    img = img.crop((int(left), int(top), int(right), int(bottom)))
            # --- End Cropping Logic ---

            # Resize the (potentially cropped) image
            img.thumbnail((max_width, max_height))
            
            if convert_to_webp:
                # Ensure the output path ends with .webp if conversion is enabled
                base, _ = os.path.splitext(output_path)
                output_path = base + ".webp"
            else:
                # Ensure the output path matches the original extension if not converting
                _, ext = os.path.splitext(input_path)
                base, _ = os.path.splitext(output_path)
                output_path = base + ext.lower() # Use original extension
            
            # Save the optimized image
            # Handle potential transparency for PNG -> WebP conversion
            save_kwargs = {'optimize': True, 'quality': quality}
            if convert_to_webp and img.mode in ('RGBA', 'LA'):
                 # Pillow's WebP saver handles RGBA correctly with 'lossless' or by setting background
                 # For lossy, transparency is tricky. Let's try saving as is, might need adjustments
                 pass # Pillow attempts to handle transparency
            
            img.save(output_path, **save_kwargs)
        return True
    except UnidentifiedImageError:
        return f"Cannot identify image file: {os.path.basename(input_path)}"
    except Exception as e:
        # Provide more specific error feedback
        return f"Error processing {os.path.basename(input_path)}: {type(e).__name__} - {str(e)}"

def is_image_file(filename):
    """Check if a file is an image based on its extension."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    return os.path.splitext(filename)[1].lower() in image_extensions

class DragDropLineEdit(QLineEdit):
    """Custom QLineEdit that accepts drag and drop of folders."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events for the line edit."""
        if event.mimeData().hasUrls():
            # Check if at least one URL is a directory
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isdir(path):
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

class ImageOptimizerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Optimizer")
        self.setGeometry(100, 100, 600, 620) # Slightly taller for quality row
        
        self.author_label = QLabel("© 2024 Piotr Proszowski")
        self.author_label.setAlignment(Qt.AlignRight)
        # Style will be applied in apply_styles

        app = QApplication.instance()
        try:
            if app:
                self.is_dark_mode = app.palette().window().color().lightness() < 128
                # Get standard icons based on style
                self.style_icons = {
                     # Use standard icons - appearance might vary by OS/theme
                    'save': app.style().standardIcon(QStyle.SP_DialogSaveButton),
                    'overwrite': app.style().standardIcon(QStyle.SP_DialogApplyButton), # Or SP_DialogSaveButton
                    'folder': app.style().standardIcon(QStyle.SP_DirOpenIcon),
                    'crop': app.style().standardIcon(QStyle.SP_FileDialogListView), # Alternative crop icon
                    'convert': app.style().standardIcon(QStyle.SP_ArrowForward), # Conversion arrow?
                    'quality': app.style().standardIcon(QStyle.SP_FileDialogDetailedView), # Icon for quality
                    'browse': app.style().standardIcon(QStyle.SP_DialogOpenButton),
                    'info': app.style().standardIcon(QStyle.SP_MessageBoxInformation), # For tooltips? Not directly used
                    'warning': app.style().standardIcon(QStyle.SP_MessageBoxWarning) # For tooltips?
                }
            else:
                self.is_dark_mode = False
                self.style_icons = {} # No icons if no app instance
        except Exception:
             self.is_dark_mode = False
             self.style_icons = {}

        # --- Central Widget and Layout ---
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(12) # Adjust spacing
        layout.setContentsMargins(15, 15, 15, 15) # Adjust margins

        # --- Input Folder ---
        input_group = QGroupBox("Input Folder")
        input_group.setToolTip("Select the source folder containing images to optimize.")
        input_layout = QHBoxLayout(input_group)
        input_layout.setSpacing(10)
        self.folder_input = DragDropLineEdit()
        self.folder_input.setPlaceholderText("Drag & drop folder or click Browse...")
        self.folder_input.setToolTip("Path to the folder containing images. You can also drag and drop a folder here.")
        browse_button = QPushButton("Browse")
        browse_button.setToolTip("Open a dialog to select the input folder.")
        if 'browse' in self.style_icons:
            browse_button.setIcon(self.style_icons['browse'])
        browse_button.clicked.connect(self.browse_folder)
        input_layout.addWidget(self.folder_input)
        input_layout.addWidget(browse_button)
        layout.addWidget(input_group)

        # --- Processing Settings Group ---
        settings_group = QGroupBox("Processing Settings")
        settings_group.setToolTip("Configure image resizing, cropping, and quality.")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setSpacing(10)

        # Resolution
        resolution_layout = QHBoxLayout()
        resolution_layout.setSpacing(10)
        self.resolution_presets = {
            'Original': None, 
            'HD (1280x720)': (1280, 720), 'Full HD (1920x1080)': (1920, 1080),
            '2K (2560x1440)': (2560, 1440), '4K (3840x2160)': (3840, 2160),
            'Custom': (-1, -1)
        }
        resolution_label = QLabel("Max Resolution:")
        resolution_label.setToolTip("Set maximum dimensions for optimized images. 'Original' keeps original size (unless cropped).")
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(self.resolution_presets.keys())
        self.resolution_combo.setCurrentText('Full HD (1920x1080)')
        self.resolution_combo.currentTextChanged.connect(self.on_resolution_changed)
        self.resolution_combo.setToolTip("Select a preset maximum resolution or 'Custom'.")
        resolution_layout.addWidget(resolution_label)
        resolution_layout.addWidget(self.resolution_combo, 1)

        # Custom Inputs
        self.custom_resolution_widget = QWidget()
        self.custom_resolution_widget.setToolTip("Define custom maximum width and height when 'Custom' resolution is selected.")
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

        # Crop Row
        crop_layout = QHBoxLayout()
        crop_layout.setSpacing(10)
        self.crop_button = QPushButton("Center Crop")
        self.crop_button.setCheckable(True)
        self.crop_button.setToolTip("Enable to crop images to the specified dimensions from the center before resizing.")
        if 'crop' in self.style_icons:
             self.crop_button.setIcon(self.style_icons['crop'])
             self.crop_button.setIconSize(QSize(16, 16))
        self.crop_button.toggled.connect(self.on_crop_toggled)
        crop_layout.addWidget(self.crop_button)

        self.crop_dimensions_widget = QWidget()
        self.crop_dimensions_widget.setToolTip("Define the target width and height for cropping.")
        crop_dimensions_layout = QHBoxLayout(self.crop_dimensions_widget)
        crop_dimensions_layout.setContentsMargins(0, 0, 0, 0)
        crop_dimensions_layout.setSpacing(5)
        self.crop_width_input = QLineEdit("800")
        self.crop_width_input.setToolTip("Target crop width in pixels.")
        self.crop_height_input = QLineEdit("800")
        self.crop_height_input.setToolTip("Target crop height in pixels.")
        crop_dimensions_layout.addWidget(QLabel("W:"))
        crop_dimensions_layout.addWidget(self.crop_width_input)
        crop_dimensions_layout.addWidget(QLabel("H:"))
        crop_dimensions_layout.addWidget(self.crop_height_input)
        self.crop_dimensions_widget.setVisible(False)
        crop_layout.addWidget(self.crop_dimensions_widget, 1) # Allow inputs to expand
        settings_layout.addLayout(crop_layout) # Add crop layout to settings group

        # Quality Row - Moved to its own row
        quality_layout = QHBoxLayout()
        quality_layout.setSpacing(10)
        quality_label = QLabel("Quality:")
        # Use setPixmap to add icon to QLabel if possible
        # if 'quality' in self.style_icons: quality_label.setPixmap(self.style_icons['quality'].pixmap(16, 16)) 
        quality_label.setToolTip("Set the image quality for saving (1-100). Lower values mean smaller files but lower quality.")
        self.quality_input = QLineEdit("85")
        self.quality_input.setToolTip("Enter a value between 1 (lowest quality) and 100 (highest quality). Default is 85.")
        fm = QFontMetrics(self.quality_input.font())
        self.quality_input.setFixedWidth(fm.horizontalAdvance("100") + 20) # Adjusted width slightly
        quality_layout.addWidget(quality_label)
        quality_layout.addWidget(self.quality_input)
        quality_layout.addStretch(1) # Push to left
        settings_layout.addLayout(quality_layout) # Add quality layout to settings group

        layout.addWidget(settings_group)

        # --- Output & Scope Group ---
        output_scope_group = QGroupBox("Output & Scope")
        output_scope_group.setToolTip("Configure output format, file handling, and folder scope.")
        output_scope_layout = QHBoxLayout(output_scope_group)
        output_scope_layout.setSpacing(10)

        # WebP Button
        self.webp_button = QPushButton("Convert to WebP")
        self.webp_button.setCheckable(True)
        self.webp_button.setChecked(True)
        self.webp_button.setToolTip("Convert output images to the WebP format (cannot be used with 'Overwrite Originals').")
        if 'convert' in self.style_icons:
             self.webp_button.setIcon(self.style_icons['convert'])
             self.webp_button.setIconSize(QSize(16, 16))
        self.webp_button.toggled.connect(self._update_option_states)
        output_scope_layout.addWidget(self.webp_button)

        # Overwrite Button
        self.overwrite_button = QPushButton("Overwrite Originals")
        self.overwrite_button.setCheckable(True)
        self.overwrite_button.setChecked(False)
        # Tooltip updated slightly for clarity
        self.overwrite_button.setToolTip("Replace original files with optimized versions (cannot be used with 'Convert to WebP').\\nWARNING: This action cannot be undone.")
        if 'overwrite' in self.style_icons:
             self.overwrite_button.setIcon(self.style_icons['overwrite'])
             self.overwrite_button.setIconSize(QSize(16, 16))
        self.overwrite_button.toggled.connect(self._update_option_states)
        output_scope_layout.addWidget(self.overwrite_button)
        
        output_scope_layout.addStretch(1) # Push recursive button to the right

        # Recursive Button
        self.recursive_button = QPushButton("Process Subfolders")
        self.recursive_button.setCheckable(True)
        self.recursive_button.setChecked(True)
        self.recursive_button.setToolTip("Include images found in subfolders of the selected input folder.")
        if 'folder' in self.style_icons:
             self.recursive_button.setIcon(self.style_icons['folder'])
             self.recursive_button.setIconSize(QSize(16, 16))
        output_scope_layout.addWidget(self.recursive_button)

        layout.addWidget(output_scope_group)
        self._update_option_states() # Set initial states

        # --- Progress Bar and Status ---
        layout.addSpacing(5) # Reduced spacing
        self.progress_bar = QProgressBar()
        self.progress_bar.setToolTip("Shows the progress of the optimization process.")
        layout.addWidget(self.progress_bar)
        self.status_label = QLabel("Ready")
        self.status_label.setToolTip("Displays the current status or the result of the last operation.")
        layout.addWidget(self.status_label)
        layout.addSpacing(5) # Reduced spacing

        # --- Start Button ---
        start_button = QPushButton("Start Optimization")
        start_button.setObjectName("StartButton")
        start_button.setToolTip("Begin processing images with the selected settings.")
        # Consider adding a 'play' or 'rocket' icon?
        # start_button.setIcon(app.style().standardIcon(QStyle.SP_MediaPlay))
        start_button.clicked.connect(self.start_optimization)
        layout.addWidget(start_button)

        # --- Author Label ---
        layout.addStretch(1)
        self.author_label.setToolTip("Application author information.") # Added tooltip
        layout.addWidget(self.author_label)
        
        # --- Apply Styles ---
        self.apply_styles() # Apply after all widgets are created

    def _update_option_states(self):
        """Enable/disable WebP and Overwrite buttons based on each other's state."""
        # Block signals to prevent infinite loops during state changes
        self.overwrite_button.blockSignals(True)
        self.webp_button.blockSignals(True)

        try:
            if self.overwrite_button.isChecked():
                # If overwrite is ON, turn OFF WebP and disable it
                if self.webp_button.isChecked():
                    self.webp_button.setChecked(False) # Turn off WebP
                self.webp_button.setEnabled(False)
                self.webp_button.setToolTip("Disabled because 'Overwrite Originals' is active.")
            else:
                # If overwrite is OFF, enable WebP
                self.webp_button.setEnabled(True)
                self.webp_button.setToolTip("Convert output images to the WebP format (cannot be used with 'Overwrite Originals').")

            if self.webp_button.isChecked():
                # If WebP is ON, turn OFF Overwrite and disable it
                if self.overwrite_button.isChecked():
                    self.overwrite_button.setChecked(False) # Turn off Overwrite
                self.overwrite_button.setEnabled(False)
                self.overwrite_button.setToolTip("Disabled because 'Convert to WebP' is active.")
            else:
                # If WebP is OFF, enable Overwrite
                self.overwrite_button.setEnabled(True)
                # Tooltip for overwrite when enabled
                self.overwrite_button.setToolTip("Replace original files with optimized versions (cannot be used with 'Convert to WebP').\\nWARNING: This action cannot be undone.")
        finally:
            # Always re-enable signals
            self.overwrite_button.blockSignals(False)
            self.webp_button.blockSignals(False)

    def apply_styles(self):
        # --- iOS Style Attempt ---
        font_family = "System" # Use system font, closest to San Francisco on macOS
        background_color = "#F2F2F7" if not self.is_dark_mode else "#1C1C1E"
        text_color = "#000000" if not self.is_dark_mode else "#FFFFFF"
        secondary_text_color = "#8A8A8E" if not self.is_dark_mode else "#8D8D92"
        accent_color = "#007AFF" # iOS Blue
        button_text_color = "#FFFFFF"
        control_bg_color = "#FFFFFF" if not self.is_dark_mode else "#2C2C2E"
        control_border_color = "#C6C6C8" if not self.is_dark_mode else "#3A3A3C"
        separator_color = "#D1D1D6" if not self.is_dark_mode else "#38383A"
        checked_button_bg_color = "#D1E7FF" if not self.is_dark_mode else "#004080" # Light blue / Darker blue for checked
        checked_button_border_color = accent_color
        
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {background_color};
                font-family: {font_family};
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
             #AuthorLabel {{ color: {secondary_text_color}; padding: 5px; font-size: 12px; }}
        """)
        self.author_label.setObjectName("AuthorLabel")
        # Styles for author label are now in the main stylesheet via #AuthorLabel

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Directory")
        if folder:
            self.folder_input.setText(folder)

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)

    def show_info(self, message):
        QMessageBox.information(self, "Information", message)

    def on_resolution_changed(self, text):
        is_custom = text == 'Custom'
        is_original = text == 'Original'
        self.custom_resolution_widget.setVisible(is_custom)
        if hasattr(self, 'width_input') and hasattr(self, 'height_input'):
            self.width_input.setEnabled(not is_original)
            self.height_input.setEnabled(not is_original)
        if not is_custom and not is_original:
            try:
                width, height = self.resolution_presets[text]
                if hasattr(self, 'width_input') and hasattr(self, 'height_input'):
                    self.width_input.setText(str(width))
                    self.height_input.setText(str(height))
            except KeyError: pass
        elif is_original:
             if hasattr(self, 'width_input') and hasattr(self, 'height_input'):
                 self.width_input.setText("") 
                 self.height_input.setText("")
        elif is_custom:
             if hasattr(self, 'width_input') and hasattr(self, 'height_input'):
                 if not self.width_input.text(): self.width_input.setText("1920")
                 if not self.height_input.text(): self.height_input.setText("1080")

    def on_crop_toggled(self, checked): # Slot for toggled signal receives boolean
        """Show/hide crop dimension inputs based on button state."""
        self.crop_dimensions_widget.setVisible(checked)

    def get_all_image_files(self, directory, recursive=False):
        """Get all image files, skipping 'optimized' dir if not overwriting."""
        image_files = []
        is_overwriting = self.overwrite_button.isChecked() # Check button state
        optimized_dir_name = "optimized" # Define once
        
        try:
            if recursive:
                for root, dirs, files in os.walk(directory, topdown=True):
                    # Exclude the optimized directory from recursion if not overwriting
                    if not is_overwriting and optimized_dir_name in dirs:
                        dirs.remove(optimized_dir_name) 
                        
                    for filename in files:
                        full_path = os.path.join(root, filename)
                        try:
                             if os.path.isfile(full_path) and is_image_file(filename):
                                 rel_path = os.path.relpath(full_path, directory)
                                 image_files.append((full_path, rel_path))
                        except Exception: pass 
            else:
                # Scan only the top directory
                optimized_dir_path = os.path.join(directory, optimized_dir_name)
                for entry in os.scandir(directory):
                     # Skip the optimized directory itself if not overwriting
                     if not is_overwriting and entry.is_dir() and entry.path == optimized_dir_path:
                          continue
                     if entry.is_file():
                        try:
                            if is_image_file(entry.name):
                                full_path = entry.path
                                rel_path = entry.name 
                                image_files.append((full_path, rel_path))
                        except Exception: pass 
        except OSError as e:
             raise OSError(f"Could not read directory \'{directory}\': {e}")
                    
        return image_files

    def start_optimization(self):
        directory = self.folder_input.text()
        if not directory or not os.path.isdir(directory):
            self.show_error("Please select a valid directory.")
            return

        try:
            # Resolution (logic remains the same)
            selected_resolution = self.resolution_combo.currentText()
            max_width, max_height = -1, -1 
            if selected_resolution == 'Custom':
                max_width = int(self.width_input.text())
                max_height = int(self.height_input.text())
                if not (0 < max_width): raise ValueError("Max Width must be positive")
                if not (0 < max_height): raise ValueError("Max Height must be positive")
            elif selected_resolution != 'Original':
                 max_width, max_height = self.resolution_presets[selected_resolution]
            
            # Quality (logic remains the same)
            quality = int(self.quality_input.text())
            if not (1 <= quality <= 100): raise ValueError("Quality must be between 1 and 100")
            
            # Cropping parameters - check button state
            crop_enabled = self.crop_button.isChecked() 
            crop_width = None
            crop_height = None
            if crop_enabled:
                crop_width_text = self.crop_width_input.text()
                crop_height_text = self.crop_height_input.text()
                if not crop_width_text or not crop_height_text:
                     raise ValueError("Crop dimensions cannot be empty when cropping is enabled")
                crop_width = int(crop_width_text)
                crop_height = int(crop_height_text)
                if not (0 < crop_width): raise ValueError("Crop Width must be positive")
                if not (0 < crop_height): raise ValueError("Crop Height must be positive")

            # Processing options - check button states
            recursive = self.recursive_button.isChecked()
            convert_to_webp = self.webp_button.isChecked()
            overwrite_originals = self.overwrite_button.isChecked()

            # Consistency check (already handled by _update_option_states)
            if overwrite_originals and convert_to_webp:
                 self.show_error("Configuration error: Cannot Overwrite and Convert to WebP.")
                 return 
                 
        except ValueError as e:
            self.show_error(f"Invalid input: {str(e)}")
            return
        except Exception as e: 
             self.show_error(f"An unexpected error occurred during setup: {str(e)}")
             return

        # Get image files (error handling remains)
        try:
            image_files = self.get_all_image_files(directory, recursive)
        except OSError as e:
             self.show_error(str(e)) 
             return
        except Exception as e:
             self.show_error(f"Error reading directory contents: {str(e)}")
             return

        total_images = len(image_files)
        if total_images == 0:
            self.show_info(f"No images found to process in \'{directory}\'" + 
                           (" or its subfolders" if recursive else ""))
            return
            
        # Confirmation for Overwrite (remains the same)
        if overwrite_originals:
            reply = QMessageBox.warning(self, "Confirm Overwrite",
                                       f"You are about to permanently overwrite {total_images} original image(s) in \'{directory}\' " +
                                       f"{'and its subfolders' if recursive else ''}.\\n\\n" +
                                       "This action cannot be undone. Are you sure you want to continue?",
                                       QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                self.status_label.setText("Ready")
                return

        # Process images (core loop logic remains similar, just path definition changes)
        processed = 0
        errors = 0
        error_messages = [] 
        self.progress_bar.setMaximum(total_images)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Starting optimization for {total_images} images...")
        QApplication.processEvents() 

        output_base_dir = directory if overwrite_originals else os.path.join(directory, "optimized")

        for input_path, rel_path in image_files:
            output_path = os.path.join(output_base_dir, rel_path) # Determine output path based on overwrite flag
            
            # Ensure the output directory exists only if *not* overwriting
            if not overwrite_originals:
                try:
                     os.makedirs(os.path.dirname(output_path), exist_ok=True)
                except OSError as e:
                     errors += 1; processed += 1; error_messages.append(f"- Dir Error {rel_path}: {e}")
                     self.progress_bar.setValue(processed)
                     self.status_label.setText(f"Error creating dir for {os.path.basename(input_path)}...")
                     QApplication.processEvents(); continue 

            # Adjust max_width/height for 'Original' (logic remains the same)
            current_max_width, current_max_height = -1, -1
            use_original_size = selected_resolution == 'Original'
            if use_original_size:
                 if not crop_enabled:
                     try:
                         with Image.open(input_path) as img_size_check: current_max_width, current_max_height = img_size_check.size
                     except Exception as size_e:
                         errors += 1; processed += 1; error_messages.append(f"- Size Error {os.path.basename(input_path)}: {size_e}")
                         self.progress_bar.setValue(processed); QApplication.processEvents(); continue
                 # else: If cropping original, keep -1,-1 for optimize_image
            elif selected_resolution == 'Custom':
                try: # Re-read in case values were invalid during initial check but fixed
                     current_max_width = int(self.width_input.text())
                     current_max_height = int(self.height_input.text())
                     if not (0 < current_max_width and 0 < current_max_height): raise ValueError("Invalid custom dims")
                except ValueError:
                      errors += 1; processed += 1; error_messages.append(f"- Invalid Custom Dims for {os.path.basename(input_path)}")
                      self.progress_bar.setValue(processed); QApplication.processEvents(); continue
            else: 
                 current_max_width, current_max_height = self.resolution_presets[selected_resolution]

            # Call optimize_image (remains the same)
            result = optimize_image(
                input_path, output_path, 
                current_max_width, current_max_height, quality, 
                convert_to_webp, 
                crop_enabled, crop_width, crop_height
            )
            
            processed += 1
            if result is not True:
                errors += 1
                error_msg_str = str(result) if result is not None else "Unknown error"
                error_messages.append(f"- {os.path.basename(input_path)}: {error_msg_str}") 
                self.status_label.setText(f"Error processing {os.path.basename(input_path)}...")
            else:
                 self.status_label.setText(f"Processed: {processed}/{total_images} - {os.path.basename(input_path)}")

            self.progress_bar.setValue(processed)
            QApplication.processEvents() 

        # Final status update & error reporting (logic remains the same)
        success_count = processed - errors
        summary_message = f"Optimization complete.\\nSuccessfully processed: {success_count}\\nErrors: {errors}"
        if errors > 0:
            detailed_errors = "\\n".join(error_messages)
            try: # Reuse advanced error box
                if len(error_messages) > 10:
                     msg_box = QMessageBox(self); msg_box.setIcon(QMessageBox.Warning)
                     msg_box.setWindowTitle("Optimization Report with Errors")
                     msg_box.setText(summary_message + "\\n\\nError details:")
                     scroll = QScrollArea(msg_box); scroll.setWidgetResizable(True); scroll.setMinimumSize(400, 150)
                     content = QWidget(); scroll.setWidget(content); lay = QVBoxLayout(content)
                     text_edit = QTextEdit(); text_edit.setPlainText(detailed_errors); text_edit.setReadOnly(True)
                     try:
                         from PyQt5.QtWidgets import QSizePolicy
                         text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                     except ImportError: pass 
                     lay.addWidget(text_edit); content.setLayout(lay)
                     msg_box_layout = msg_box.layout()
                     if hasattr(msg_box_layout, 'addWidget'):
                        row_count = msg_box_layout.rowCount() if hasattr(msg_box_layout, 'rowCount') else 2
                        col_count = msg_box_layout.columnCount() if hasattr(msg_box_layout, 'columnCount') else 1
                        msg_box_layout.addWidget(scroll, row_count, 0, 1, col_count) 
                     else: msg_box.setDetailedText(detailed_errors)
                     if hasattr(msg_box, 'setSizeGripEnabled'): msg_box.setSizeGripEnabled(True)
                     msg_box.exec_()
                else: 
                    msg_box = QMessageBox(self); msg_box.setIcon(QMessageBox.Warning)
                    msg_box.setWindowTitle("Optimization Report with Errors")
                    msg_box.setText(summary_message); msg_box.setDetailedText(detailed_errors)
                    msg_box.exec_()
            except Exception as report_e: 
                self.show_error(summary_message + f"\\nCould not display detailed errors: {report_e}")
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
