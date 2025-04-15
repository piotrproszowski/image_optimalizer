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
                            QComboBox, QScrollArea, QTextEdit)
from PyQt5.QtCore import Qt, QMimeData
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
        self.setGeometry(100, 100, 600, 550) # Adjusted height for new option
        
        self.author_label = QLabel("© 2024 Piotr Proszowski")
        self.author_label.setAlignment(Qt.AlignRight)
        # Style will be applied in apply_styles

        app = QApplication.instance()
        try:
            if app:
                self.is_dark_mode = app.palette().window().color().lightness() < 128
            else:
                self.is_dark_mode = False 
        except Exception:
             self.is_dark_mode = False

        # --- Central Widget and Layout ---
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(15) # Add more vertical spacing
        layout.setContentsMargins(20, 20, 20, 20) # Add padding around window content

        # --- Folder Selection ---
        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(10)
        self.folder_input = DragDropLineEdit()
        self.folder_input.setPlaceholderText("Drag & drop folder or click Browse...")
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_folder)
        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(browse_button)
        layout.addLayout(folder_layout)

        # --- Resolution Settings ---
        resolution_group_layout = QHBoxLayout() # Group preset and custom inputs
        resolution_group_layout.setSpacing(10)

        # Presets
        self.resolution_presets = {
            'Original': None, # Add option to keep original size (only crop/quality/format changes)
            'HD (1280x720)': (1280, 720),
            'Full HD (1920x1080)': (1920, 1080),
            '2K (2560x1440)': (2560, 1440),
            '4K (3840x2160)': (3840, 2160),
            'Custom': (-1, -1) # Use -1 to signify custom input needed
        }
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(self.resolution_presets.keys())
        self.resolution_combo.setCurrentText('Full HD (1920x1080)') # Default preset
        self.resolution_combo.currentTextChanged.connect(self.on_resolution_changed)
        resolution_group_layout.addWidget(QLabel("Max Resolution:"))
        resolution_group_layout.addWidget(self.resolution_combo, 1) # Give combo more space

        # Custom Inputs (initially hidden)
        self.custom_resolution_widget = QWidget()
        custom_resolution_layout = QHBoxLayout(self.custom_resolution_widget)
        custom_resolution_layout.setContentsMargins(0, 0, 0, 0) # Remove margins for tighter fit
        custom_resolution_layout.setSpacing(5)
        self.width_input = QLineEdit()
        self.height_input = QLineEdit()
        custom_resolution_layout.addWidget(QLabel("W:"))
        custom_resolution_layout.addWidget(self.width_input)
        custom_resolution_layout.addWidget(QLabel("H:"))
        custom_resolution_layout.addWidget(self.height_input)
        resolution_group_layout.addWidget(self.custom_resolution_widget)
        self.custom_resolution_widget.setVisible(False) # Start hidden

        layout.addLayout(resolution_group_layout)
        self.on_resolution_changed(self.resolution_combo.currentText()) # Set initial state

        # --- Cropping Options ---
        crop_layout = QHBoxLayout()
        crop_layout.setSpacing(10)
        self.crop_checkbox = QCheckBox("Center Crop:")
        self.crop_checkbox.stateChanged.connect(self.on_crop_toggled)
        crop_layout.addWidget(self.crop_checkbox)

        self.crop_dimensions_widget = QWidget()
        crop_dimensions_layout = QHBoxLayout(self.crop_dimensions_widget)
        crop_dimensions_layout.setContentsMargins(0, 0, 0, 0)
        crop_dimensions_layout.setSpacing(5)
        self.crop_width_input = QLineEdit("800")
        self.crop_height_input = QLineEdit("800")
        crop_dimensions_layout.addWidget(QLabel("W:"))
        crop_dimensions_layout.addWidget(self.crop_width_input)
        crop_dimensions_layout.addWidget(QLabel("H:"))
        crop_dimensions_layout.addWidget(self.crop_height_input)
        self.crop_dimensions_widget.setVisible(False) # Initially hidden
        crop_layout.addWidget(self.crop_dimensions_widget, 1) # Allow crop inputs to expand

        layout.addLayout(crop_layout)

        # --- Other Settings ---
        settings_layout = QHBoxLayout()
        settings_layout.setSpacing(10)
        settings_layout.addWidget(QLabel("Quality (1-100):"))
        self.quality_input = QLineEdit("85")
        fm = QFontMetrics(self.quality_input.font())
        self.quality_input.setFixedWidth(fm.horizontalAdvance("100") + 15) # Set fixed width based on "100"
        settings_layout.addWidget(self.quality_input)
        settings_layout.addStretch(1) # Push subsequent items to the right

        self.webp_checkbox = QCheckBox("Convert to WebP")
        self.webp_checkbox.setChecked(True)
        self.webp_checkbox.stateChanged.connect(self._update_option_states) # Connect state change
        settings_layout.addWidget(self.webp_checkbox)
        layout.addLayout(settings_layout)

        # --- Processing Options ---
        processing_options_layout = QHBoxLayout()
        processing_options_layout.setSpacing(10)
        self.recursive_checkbox = QCheckBox("Process Subfolders")
        self.recursive_checkbox.setChecked(True)
        processing_options_layout.addWidget(self.recursive_checkbox)
        processing_options_layout.addStretch(1)

        self.overwrite_checkbox = QCheckBox("Overwrite Originals") # NEW Checkbox
        self.overwrite_checkbox.setChecked(False)
        self.overwrite_checkbox.setToolTip("Replace original files. Disabled if 'Convert to WebP' is checked.")
        self.overwrite_checkbox.stateChanged.connect(self._update_option_states) # Connect state change
        processing_options_layout.addWidget(self.overwrite_checkbox)
        layout.addLayout(processing_options_layout)

        self._update_option_states() # Set initial enabled/disabled states

        # --- Progress Bar and Status ---
        layout.addSpacing(10) # Add space before progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        layout.addSpacing(10) # Add space before start button

        # --- Start Button ---
        start_button = QPushButton("Start Optimization")
        start_button.setObjectName("StartButton") # Assign object name for specific styling
        start_button.clicked.connect(self.start_optimization)
        layout.addWidget(start_button)

        # --- Author Label ---
        layout.addStretch(1) # Push author label to bottom
        layout.addWidget(self.author_label)
        
        # --- Apply Styles ---
        self.apply_styles() # Apply after all widgets are created

    def _update_option_states(self):
        """Enable/disable WebP and Overwrite checkboxes based on each other's state."""
        # Store current states before potential changes
        overwrite_was_checked = self.overwrite_checkbox.isChecked()
        webp_was_checked = self.webp_checkbox.isChecked()

        # Temporarily block signals to avoid recursive loops
        self.overwrite_checkbox.blockSignals(True)
        self.webp_checkbox.blockSignals(True)

        try:
            if self.overwrite_checkbox.isChecked():
                self.webp_checkbox.setChecked(False)
                self.webp_checkbox.setEnabled(False)
                self.webp_checkbox.setToolTip("Disabled because 'Overwrite Originals' is checked.")
            else:
                self.webp_checkbox.setEnabled(True)
                self.webp_checkbox.setToolTip("")

            if self.webp_checkbox.isChecked():
                self.overwrite_checkbox.setChecked(False)
                self.overwrite_checkbox.setEnabled(False)
                self.overwrite_checkbox.setToolTip("Disabled because 'Convert to WebP' is checked.")
            else:
                self.overwrite_checkbox.setEnabled(True)
                self.overwrite_checkbox.setToolTip("Replace original files. Cannot be used with 'Convert to WebP'.")
        finally:
            # Always unblock signals
            self.overwrite_checkbox.blockSignals(False)
            self.webp_checkbox.blockSignals(False)

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
        
        # Adjust colors for better contrast if needed, especially for dark mode

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {background_color};
                font-family: {font_family};
            }}
            QWidget {{ /* Default font for all widgets unless overridden */
                 font-family: {font_family};
            }}
            QLabel {{
                color: {text_color};
                font-size: 14px; /* Adjust as needed */
            }}
            QLineEdit {{
                background-color: {control_bg_color};
                color: {text_color};
                border: 1px solid {control_border_color};
                border-radius: 8px;
                padding: 8px 10px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 1px solid {accent_color};
            }}
            QPushButton {{
                background-color: {control_bg_color};
                color: {accent_color}; /* Standard buttons have blue text */
                border: 1px solid {control_border_color};
                border-radius: 8px;
                padding: 8px 15px;
                font-size: 15px;
                font-weight: 500; /* Medium weight */
                min-width: 70px;
            }}
             QPushButton#StartButton {{ /* Style the main action button differently */
                 background-color: {accent_color};
                 color: {button_text_color};
                 border: none;
                 font-weight: 600; /* Semibold */
             }}
            QPushButton:hover {{
                background-color: #E5E5EA; /* Light gray hover for standard buttons */
            }}
             QPushButton#StartButton:hover {{
                 background-color: #005ECC; /* Darker blue hover for start button */
             }}
            QPushButton:disabled {{
                 background-color: #E5E5EA;
                 color: {secondary_text_color};
                 border: 1px solid #E0E0E0;
             }}
             QPushButton#StartButton:disabled {{
                  background-color: #A0A0A0; /* Gray out disabled start button */
                  color: #F0F0F0;
                  border: none;
             }}
            QComboBox {{
                background-color: {control_bg_color};
                color: {text_color};
                border: 1px solid {control_border_color};
                border-radius: 8px;
                padding: 8px 10px;
                font-size: 14px;
                min-height: 1.8em; /* Ensure height matches LineEdit */
            }}
            QComboBox::drop-down {{
                 border: none; /* Remove default dropdown button border */
                 width: 20px; /* Space for arrow */
                 /* Consider adding a custom arrow image if needed */
             }}
             QComboBox::down-arrow {{
                 /* You might need to provide an image for a custom arrow */
                 /* image: url(:/icons/down_arrow.png); */
             }}
            QComboBox QAbstractItemView {{ /* Style dropdown list */
                background-color: {control_bg_color};
                color: {text_color};
                border: 1px solid {control_border_color};
                selection-background-color: {accent_color};
                selection-color: {button_text_color};
                padding: 5px;
                border-radius: 8px; /* May not work on all platforms */
            }}
            QCheckBox {{
                color: {text_color};
                font-size: 14px;
                spacing: 8px; /* Space between indicator and text */
            }}
            QCheckBox::indicator {{ /* iOS-like switch attempt (basic) */
                border-radius: 9px; /* Round */
                background-color: #E9E9EB; /* Off state color */
                width: 36px;
                height: 18px;
                border: 1px solid {control_border_color};
             }}
             QCheckBox::indicator:checked {{
                 background-color: #34C759; /* Green 'on' state */
                 border: 1px solid #34C759;
             }}
             /* Indicator handle (tricky with QSS) */
             /* QCheckBox::indicator:checked::handle { subcontrol-position: center right; } */
             /* QCheckBox::indicator:unchecked::handle { subcontrol-position: center left; } */

             QCheckBox:disabled {{
                 color: {secondary_text_color};
             }}
              QCheckBox::indicator:disabled {{
                  background-color: #D0D0D0;
                  border-color: #C0C0C0;
              }}

            QProgressBar {{
                border: 1px solid {control_border_color};
                border-radius: 8px;
                text-align: center;
                background-color: {control_bg_color};
                color: {secondary_text_color};
                font-size: 12px;
                height: 10px; /* Slimmer progress bar */
             }}
             QProgressBar::chunk {{
                 background-color: {accent_color};
                 border-radius: 7px; /* Match outer radius */
                 margin: 1px; /* Inset the chunk slightly */
             }}
             #AuthorLabel {{ /* Specific styling for author if needed */
                  color: {secondary_text_color};
                  padding: 5px;
                  font-size: 12px;
             }}
        """)
        # Apply object name to author label for specific styling if desired
        self.author_label.setObjectName("AuthorLabel")
        self.author_label.setStyleSheet(f"color: {secondary_text_color}; padding: 5px; font-size: 12px;")

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
        
        # Disable max width/height inputs if 'Original' is selected
        # Ensure inputs exist before trying to access them
        if hasattr(self, 'width_input') and hasattr(self, 'height_input'):
            self.width_input.setEnabled(not is_original)
            self.height_input.setEnabled(not is_original)
        
        if not is_custom and not is_original:
            try:
                width, height = self.resolution_presets[text]
                if hasattr(self, 'width_input') and hasattr(self, 'height_input'):
                    self.width_input.setText(str(width))
                    self.height_input.setText(str(height))
            except KeyError:
                 pass
        elif is_original:
             # Clear or set placeholder for original size? Clear for now.
             if hasattr(self, 'width_input') and hasattr(self, 'height_input'):
                 self.width_input.setText("") 
                 self.height_input.setText("")
        elif is_custom:
             # Optionally set default custom values or leave as is
             if hasattr(self, 'width_input') and hasattr(self, 'height_input'):
                 if not self.width_input.text(): self.width_input.setText("1920")
                 if not self.height_input.text(): self.height_input.setText("1080")

    def on_crop_toggled(self, state):
        self.crop_dimensions_widget.setVisible(state == Qt.Checked)

    def get_all_image_files(self, directory, recursive=False):
        """Get all image files in the directory, optionally recursively."""
        image_files = []
        
        # Use os.scandir for potentially better performance, especially on Windows
        try:
            if recursive:
                for root, _, files in os.walk(directory):
                    # Skip files in our own output directory if overwriting is off
                    # Check if overwrite_checkbox exists before accessing it
                    is_overwriting = hasattr(self, 'overwrite_checkbox') and self.overwrite_checkbox.isChecked()
                    if not is_overwriting and "optimized" in root.split(os.sep):
                         continue
                    for filename in files:
                        full_path = os.path.join(root, filename)
                        try:
                             if os.path.isfile(full_path) and is_image_file(filename):
                                 rel_path = os.path.relpath(full_path, directory)
                                 image_files.append((full_path, rel_path))
                        except Exception: 
                             pass 
            else:
                # Avoid processing the 'optimized' directory when not recursive and not overwriting
                optimized_dir_path = os.path.join(directory, "optimized")
                is_overwriting = hasattr(self, 'overwrite_checkbox') and self.overwrite_checkbox.isChecked()
                for entry in os.scandir(directory):
                     # Skip the 'optimized' directory itself
                     if not is_overwriting and entry.is_dir() and entry.path == optimized_dir_path:
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
        directory = self.folder_input.text()
        if not directory or not os.path.isdir(directory):
            self.show_error("Please select a valid directory.")
            return

        # Input validation
        try:
            # Resolution
            selected_resolution = self.resolution_combo.currentText()
            max_width, max_height = -1, -1 # Default to -1 (will signify 'original' in optimize_image)
            
            if selected_resolution == 'Custom':
                max_width = int(self.width_input.text())
                max_height = int(self.height_input.text())
                if not (0 < max_width): raise ValueError("Max Width must be positive")
                if not (0 < max_height): raise ValueError("Max Height must be positive")
            elif selected_resolution != 'Original':
                 max_width, max_height = self.resolution_presets[selected_resolution]
            
            # Quality
            quality = int(self.quality_input.text())
            if not (1 <= quality <= 100): raise ValueError("Quality must be between 1 and 100")
            
            # Cropping parameters
            crop_enabled = self.crop_checkbox.isChecked()
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

            # Processing options
            recursive = self.recursive_checkbox.isChecked()
            convert_to_webp = self.webp_checkbox.isChecked()
            overwrite_originals = self.overwrite_checkbox.isChecked()

            # Ensure consistency (already handled by _update_option_states, but double check)
            if overwrite_originals and convert_to_webp:
                 # This state should ideally not be reachable due to _update_option_states
                 # but check defensively.
                 self.show_error("Configuration error: Cannot Overwrite and Convert to WebP.")
                 return 
                
        except ValueError as e:
            self.show_error(f"Invalid input: {str(e)}")
            return
        except Exception as e: 
             self.show_error(f"An unexpected error occurred during setup: {str(e)}")
             return

        # Get image files (handle potential errors)
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
            self.show_info(f"No images found to process in '{directory}'" + 
                           (" or its subfolders" if recursive else ""))
            return

        # --- Confirmation for Overwrite ---
        if overwrite_originals:
            reply = QMessageBox.warning(self, "Confirm Overwrite",
                                       f"You are about to permanently overwrite {total_images} original image(s) in '{directory}' " +
                                       f"{'and its subfolders' if recursive else ''}.\n\n" +
                                       "This action cannot be undone. Are you sure you want to continue?",
                                       QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                self.status_label.setText("Ready")
                return
        # --- End Confirmation ---

        # Process images
        processed = 0
        errors = 0
        error_messages = [] 
        self.progress_bar.setMaximum(total_images)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Starting optimization for {total_images} images...")
        QApplication.processEvents() 

        output_base_dir = os.path.join(directory, "optimized") if not overwrite_originals else directory

        for input_path, rel_path in image_files:
            if overwrite_originals:
                output_path = input_path # Output is the same as input
            else:
                # Construct output path preserving structure relative to output_base_dir
                output_path = os.path.join(output_base_dir, rel_path)
            
            # Ensure the output directory exists if *not* overwriting
            if not overwrite_originals:
                try:
                     os.makedirs(os.path.dirname(output_path), exist_ok=True)
                except OSError as e:
                     errors += 1
                     error_messages.append(f"- Could not create output directory for {rel_path}: {e}")
                     processed += 1 
                     self.progress_bar.setValue(processed)
                     self.status_label.setText(f"Error creating dir for {os.path.basename(input_path)}...")
                     QApplication.processEvents()
                     continue 

            # --- Adjust max_width/height for 'Original' setting ---            
            current_max_width = -1
            current_max_height = -1
            use_original_size = selected_resolution == 'Original'

            if use_original_size:
                 # If cropping is enabled, we still need target dimensions for thumbnail after crop
                 # Let optimize_image handle potential resizing *after* cropping based on original size.
                 # If not cropping, get original size to prevent thumbnail from resizing.
                 if not crop_enabled:
                     try:
                         with Image.open(input_path) as img_size_check:
                             current_max_width, current_max_height = img_size_check.size
                     except Exception as size_e:
                         errors += 1
                         error_messages.append(f"- Could not read dimensions for {os.path.basename(input_path)}: {size_e}")
                         processed += 1
                         self.progress_bar.setValue(processed)
                         QApplication.processEvents()
                         continue # Skip this file
                 else:
                      # If cropping original size, pass -1 so optimize_image uses original dims for thumbnail
                      current_max_width = -1 
                      current_max_height = -1
            elif selected_resolution == 'Custom':
                current_max_width = int(self.width_input.text()) # Re-read in case it changed
                current_max_height = int(self.height_input.text())
            else: # Preset selected
                 current_max_width, current_max_height = self.resolution_presets[selected_resolution]
            

            # Call optimize_image 
            result = optimize_image(\
                input_path, output_path, \
                current_max_width, current_max_height, quality, \
                convert_to_webp, # Will be False if overwrite_originals is True
                crop_enabled, crop_width, crop_height\
            )
            
            processed += 1
            if result is not True:
                errors += 1
                error_msg_str = str(result) if result is not None else "Unknown error"
                error_messages.append(f"- {os.path.basename(input_path)}: {error_msg_str}") 
                self.status_label.setText(f"Error processing {os.path.basename(input_path)}...")
            else:
                 # Update status only on success to keep error messages visible longer
                 self.status_label.setText(f"Processed: {processed}/{total_images} - {os.path.basename(input_path)}")

            self.progress_bar.setValue(processed)
            QApplication.processEvents() 

        # Final status update (Error reporting logic remains the same)
        success_count = processed - errors
        summary_message = f"Optimization complete.\nSuccessfully processed: {success_count}\nErrors: {errors}"
        
        if errors > 0:
            detailed_errors = "\n".join(error_messages)
            # Use a scrollable text area in the message box for many errors
            # (Assuming the previous scrollable error box implementation is sufficient)
            try:
                # Try reusing the advanced error box code
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
                     # Import QSizePolicy if available
                     try:
                         from PyQt5.QtWidgets import QSizePolicy
                         text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                     except ImportError:
                         pass # Sizing policy is optional
                     lay.addWidget(text_edit)
                     content.setLayout(lay)
                     msg_box_layout = msg_box.layout()
                     # Check if layout has addWidget method before calling it
                     if hasattr(msg_box_layout, 'addWidget'):
                        # AddWidget(widget, row, column, rowSpan, columnSpan)
                        row_count = msg_box_layout.rowCount() if hasattr(msg_box_layout, 'rowCount') else 2 # Guess row count
                        col_count = msg_box_layout.columnCount() if hasattr(msg_box_layout, 'columnCount') else 1 # Guess col count
                        msg_box_layout.addWidget(scroll, row_count, 0, 1, col_count) 
                     else: # Fallback if layout is not grid-like
                         # Add scroll area below the main text (may not look perfect)
                         vbox = QVBoxLayout()
                         # Find the label and add scroll below it if possible
                         for i in range(msg_box_layout.count()):
                             widget = msg_box_layout.itemAt(i).widget()
                             if widget:
                                 vbox.addWidget(widget)
                         vbox.addWidget(scroll)
                         # Replace original layout (might be risky)
                         # Instead, just add detailed text
                         msg_box.setDetailedText(detailed_errors)

                     # Make the message box resizable if possible
                     if hasattr(msg_box, 'setSizeGripEnabled'):
                        msg_box.setSizeGripEnabled(True)
                     msg_box.exec_()
                else: 
                    msg_box = QMessageBox(self)
                    msg_box.setIcon(QMessageBox.Warning)
                    msg_box.setWindowTitle("Optimization Report with Errors")
                    msg_box.setText(summary_message)
                    msg_box.setDetailedText(detailed_errors)
                    msg_box.exec_()
            except NameError: # Fallback if QSizePolicy wasn't imported correctly earlier
                 msg_box = QMessageBox(self)
                 msg_box.setIcon(QMessageBox.Warning)
                 msg_box.setWindowTitle("Optimization Report with Errors")
                 msg_box.setText(summary_message)
                 msg_box.setDetailedText(detailed_errors + "\n(Install PyQt5 for better error view)")
                 msg_box.exec_()
            except Exception as report_e: # Generic fallback
                self.show_error(summary_message + f"\nCould not display detailed errors: {report_e}")

        else:
            self.show_info(summary_message) 
            
        self.status_label.setText("Ready")
        self.progress_bar.setValue(0)

def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    
    # Import QSizePolicy here, needed for the error reporting dialog
    # Make it global so it can be accessed in the class method if needed
    # Although direct import within the method is cleaner if possible
    # global QSizePolicy 
    # from PyQt5.QtWidgets import QSizePolicy 

    window = ImageOptimizerWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
     # No longer need the import here, moved to main() or handled inside class
     main()
