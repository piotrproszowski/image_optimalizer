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
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

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
        self.setGeometry(100, 100, 600, 500) # Increased height slightly for new options
        
        # Add author info label
        self.author_label = QLabel("© 2024 Piotr Proszowski")
        self.author_label.setAlignment(Qt.AlignRight)
        self.author_label.setStyleSheet("color: #666666; padding: 5px;")
        
        # Detect system theme
        app = QApplication.instance()
        try:
            # Check if running within a QApplication instance
            if app:
                self.is_dark_mode = app.palette().window().color().lightness() < 128
            else:
                # Fallback if no QApplication instance exists (e.g., testing)
                self.is_dark_mode = False 
        except Exception:
             # Fallback in case palette access fails
             self.is_dark_mode = False
        
        # Set theme-dependent styles
        self.apply_styles()

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Folder selection with drag and drop support
        folder_layout = QHBoxLayout()
        self.folder_input = DragDropLineEdit()
        self.folder_input.setPlaceholderText("Select images folder or drag & drop folder here...")
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_folder)
        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(browse_button)
        layout.addLayout(folder_layout)

        # Presets for resolutions
        self.resolution_presets = {
            'HD (1280x720)': (1280, 720),
            'Full HD (1920x1080)': (1920, 1080),
            '2K (2560x1440)': (2560, 1440),
            '4K (3840x2160)': (3840, 2160),
            'Custom': None
        }

        # Resolution selection (Max dimensions)
        resolution_layout = QHBoxLayout()
        resolution_label = QLabel("Max Resolution:") # Clarified label
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(self.resolution_presets.keys())
        self.resolution_combo.currentTextChanged.connect(self.on_resolution_changed)
        resolution_layout.addWidget(resolution_label)
        resolution_layout.addWidget(self.resolution_combo)
        layout.addLayout(resolution_layout)

        # Custom Max Resolution inputs
        self.custom_resolution_widget = QWidget() # Renamed widget
        custom_resolution_layout = QHBoxLayout(self.custom_resolution_widget) # Renamed layout
        self.width_input = QLineEdit("1920") # Default to Full HD width
        self.height_input = QLineEdit("1080") # Default to Full HD height
        custom_resolution_layout.addWidget(QLabel("Max Width:")) # Clarified label
        custom_resolution_layout.addWidget(self.width_input)
        custom_resolution_layout.addWidget(QLabel("Max Height:")) # Clarified label
        custom_resolution_layout.addWidget(self.height_input)
        self.custom_resolution_widget.setVisible(False) # Initially hidden
        layout.addWidget(self.custom_resolution_widget)
        # Set initial resolution based on combo default
        self.on_resolution_changed(self.resolution_combo.currentText())

        # --- Cropping Options ---
        self.crop_checkbox = QCheckBox("Enable Center Cropping")
        self.crop_checkbox.stateChanged.connect(self.on_crop_toggled)
        layout.addWidget(self.crop_checkbox)

        self.crop_dimensions_widget = QWidget()
        crop_layout = QHBoxLayout(self.crop_dimensions_widget)
        self.crop_width_input = QLineEdit("800")
        self.crop_height_input = QLineEdit("800")
        crop_layout.addWidget(QLabel("Crop Width:"))
        crop_layout.addWidget(self.crop_width_input)
        crop_layout.addWidget(QLabel("Crop Height:"))
        crop_layout.addWidget(self.crop_height_input)
        self.crop_dimensions_widget.setVisible(False) # Initially hidden
        layout.addWidget(self.crop_dimensions_widget)
        # --- End Cropping Options ---

        # Other Settings
        settings_layout = QHBoxLayout() # Group quality and webp
        settings_layout.addWidget(QLabel("Quality (1-100):"))
        self.quality_input = QLineEdit("85")
        settings_layout.addWidget(self.quality_input)
        self.webp_checkbox = QCheckBox("Convert to WebP")
        self.webp_checkbox.setChecked(True)
        settings_layout.addWidget(self.webp_checkbox)
        layout.addLayout(settings_layout)
        
        self.recursive_checkbox = QCheckBox("Process subfolders recursively")
        self.recursive_checkbox.setChecked(True)
        layout.addWidget(self.recursive_checkbox) # Place recursive checkbox separately

        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

        # Start button
        start_button = QPushButton("Start Optimization")
        start_button.clicked.connect(self.start_optimization)
        layout.addWidget(start_button)

        # Add author label at the bottom
        layout.addWidget(self.author_label)

    def apply_styles(self):
        # Encapsulate style setting
        # Assume self.is_dark_mode is set
        base_style = """
            QPushButton {
                background-color: #4CAF50; color: white; padding: 8px 15px;
                border-radius: 4px; min-width: 80px; border: none;
            }
            QPushButton:hover { background-color: #45a049; }
            QLineEdit { padding: 8px; border-radius: 4px; }
            QProgressBar { border-radius: 4px; text-align: center; }
            QProgressBar::chunk { background-color: #4CAF50; border-radius: 3px; }
            QCheckBox::indicator { width: 18px; height: 18px; border-radius: 2px; }
            QComboBox { padding: 8px; border-radius: 4px; min-height: 1.5em; }
        """
        if self.is_dark_mode:
            dark_style = """
                QMainWindow { background-color: #1e1e1e; }
                QLineEdit { border: 1px solid #333; background-color: #2d2d2d; color: #ffffff; }
                QLineEdit:focus { border: 1px solid #4CAF50; background-color: #363636; }
                QProgressBar { border: 1px solid #333; background-color: #2d2d2d; color: #ffffff; }
                QLabel, QCheckBox { color: #ffffff; }
                QCheckBox::indicator { background-color: #2d2d2d; border: 1px solid #333; }
                QCheckBox::indicator:checked { background-color: #4CAF50; }
                QComboBox { border: 1px solid #333; background-color: #2d2d2d; color: #ffffff; }
                QComboBox::drop-down { border: none; }
                QComboBox QAbstractItemView { background-color: #2d2d2d; color: #ffffff; selection-background-color: #4CAF50; }
            """
            self.setStyleSheet(base_style + dark_style)
        else:
            light_style = """
                QMainWindow { background-color: #ffffff; }
                QLineEdit { border: 1px solid #ddd; background-color: #fafafa; color: #333333; }
                QLineEdit:focus { border: 1px solid #4CAF50; background-color: white; }
                QProgressBar { border: 1px solid #ddd; background-color: #fafafa; color: #333333; }
                QLabel, QCheckBox { color: #333333; }
                QCheckBox::indicator { background-color: #fafafa; border: 1px solid #ccc; }
                QCheckBox::indicator:checked { background-color: #4CAF50; border: none; }
                QComboBox { border: 1px solid #ddd; background-color: #fafafa; color: #333333; }
                QComboBox::drop-down { border: 1px solid #ddd; }
                QComboBox QAbstractItemView { background-color: #ffffff; color: #333333; selection-background-color: #d3d3d3; }
            """
            self.setStyleSheet(base_style + light_style)

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
        self.custom_resolution_widget.setVisible(is_custom) # Use renamed widget
        
        if not is_custom:
            # Update max width/height inputs even if hidden
            try:
                width, height = self.resolution_presets[text]
                self.width_input.setText(str(width))
                self.height_input.setText(str(height))
            except KeyError: # Handle case where text might not be in presets (e.g., during init)
                 pass 

    def on_crop_toggled(self, state):
        """Show/hide crop dimension inputs based on checkbox state."""
        self.crop_dimensions_widget.setVisible(state == Qt.Checked)

    def get_all_image_files(self, directory, recursive=False):
        """Get all image files in the directory, optionally recursively."""
        image_files = []
        
        # Use os.scandir for potentially better performance, especially on Windows
        try:
            if recursive:
                for root, _, files in os.walk(directory):
                    for filename in files:
                        full_path = os.path.join(root, filename)
                        # Check if it's a file and an image
                        # Use try-except for is_image_file in case of weird filenames
                        try:
                             if os.path.isfile(full_path) and is_image_file(filename):
                                 rel_path = os.path.relpath(full_path, directory)
                                 image_files.append((full_path, rel_path))
                        except Exception: # Ignore files causing issues with extension check
                             pass 
            else:
                for entry in os.scandir(directory):
                     if entry.is_file():
                        try:
                            if is_image_file(entry.name):
                                full_path = entry.path
                                rel_path = entry.name # Relative path is just the filename
                                image_files.append((full_path, rel_path))
                        except Exception:
                             pass # Ignore files causing issues with extension check
        except OSError as e:
             # Raise the error to be caught in start_optimization
             raise OSError(f"Could not read directory '{directory}': {e}")
                   
        return image_files

    def start_optimization(self):
        directory = self.folder_input.text()
        if not directory or not os.path.isdir(directory):
            self.show_error("Please select a valid directory")
            return

        # Input validation
        try:
            max_width = int(self.width_input.text())
            max_height = int(self.height_input.text())
            quality = int(self.quality_input.text())
            
            if not (0 < max_width): raise ValueError("Max Width must be positive")
            if not (0 < max_height): raise ValueError("Max Height must be positive")
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

            recursive = self.recursive_checkbox.isChecked()
            convert_to_webp = self.webp_checkbox.isChecked()
            
        except ValueError as e:
            self.show_error(f"Invalid input: {str(e)}")
            return
        except Exception as e: # Catch other potential errors during setup
             self.show_error(f"An unexpected error occurred during setup: {str(e)}")
             return

        # Get image files
        try:
            image_files = self.get_all_image_files(directory, recursive)
        except OSError as e:
             self.show_error(str(e)) # Display the specific OS error
             return
        except Exception as e:
             self.show_error(f"Error reading directory contents: {str(e)}")
             return

        total_images = len(image_files)
        if total_images == 0:
            self.show_info(f"No images found in '{directory}'" + 
                           (" or its subfolders" if recursive else ""))
            return

        # Process images
        processed = 0
        errors = 0
        error_messages = [] # Collect specific errors
        self.progress_bar.setMaximum(total_images)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Starting optimization for {total_images} images...")
        QApplication.processEvents() # Update UI before loop

        output_base_dir = os.path.join(directory, "optimized")

        for input_path, rel_path in image_files:
            # Construct output path preserving structure relative to output_base_dir
            output_path = os.path.join(output_base_dir, rel_path)
            
            # Ensure the output directory for the specific file exists
            try:
                 os.makedirs(os.path.dirname(output_path), exist_ok=True)
            except OSError as e:
                 errors += 1
                 error_messages.append(f"- Could not create output directory for {rel_path}: {e}")
                 processed += 1 # Count as processed (even though failed)
                 self.progress_bar.setValue(processed)
                 self.status_label.setText(f"Error creating dir for {os.path.basename(input_path)}...")
                 QApplication.processEvents()
                 continue # Skip processing this file

            # Call the updated optimize_image function
            result = optimize_image(\
                input_path, output_path, \
                max_width, max_height, quality, \
                convert_to_webp, \
                crop_enabled, crop_width, crop_height # Pass crop parameters
            )
            
            processed += 1
            if result is not True:
                errors += 1
                # Ensure result is a string before appending
                error_msg_str = str(result) if result is not None else "Unknown error"
                error_messages.append(f"- {os.path.basename(input_path)}: {error_msg_str}") 
                self.status_label.setText(f"Error on {os.path.basename(input_path)}...")
            else:
                self.status_label.setText(f"Processed: {processed}/{total_images} - {os.path.basename(input_path)}")

            self.progress_bar.setValue(processed)
            QApplication.processEvents() # Keep UI responsive

        # Final status update
        success_count = processed - errors
        summary_message = f"Optimization complete.\nSuccessfully processed: {success_count}\nErrors: {errors}"
        
        if errors > 0:
            # Show detailed errors if any occurred
            detailed_errors = "\n".join(error_messages)
            # Use a scrollable text area in the message box for many errors
            if len(error_messages) > 10: 
                 msg_box = QMessageBox(self)
                 msg_box.setIcon(QMessageBox.Warning)
                 msg_box.setWindowTitle("Optimization Report with Errors")
                 msg_box.setText(summary_message + "\n\nError details:")
                 
                 scroll = QScrollArea(msg_box)
                 scroll.setWidgetResizable(True)
                 # Use fixed size for scroll area content to prevent overly large message box
                 scroll.setMinimumSize(400, 150)
                 content = QWidget()
                 scroll.setWidget(content)
                 lay = QVBoxLayout(content)
                 
                 text_edit = QTextEdit()
                 text_edit.setPlainText(detailed_errors)
                 text_edit.setReadOnly(True)
                 # Ensure text edit grows vertically but not excessively horizontally
                 text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                 lay.addWidget(text_edit)
                 content.setLayout(lay) # Set layout on the content widget
                 
                 # Add the scroll area to the message box layout
                 msg_box_layout = msg_box.layout()
                 # AddWidget(widget, row, column, rowSpan, columnSpan)
                 msg_box_layout.addWidget(scroll, msg_box_layout.rowCount(), 0, 1, msg_box_layout.columnCount()) 
                 # Make the message box resizable
                 msg_box.setSizeGripEnabled(True)
                 msg_box.exec_()
            else: # Fewer errors, standard detailed text is fine
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle("Optimization Report with Errors")
                msg_box.setText(summary_message)
                msg_box.setDetailedText(detailed_errors)
                msg_box.exec_()

        else:
            self.show_info(summary_message) # Show simple info if no errors
            
        self.status_label.setText("Ready")
        self.progress_bar.setValue(0)

def main():
    # Ensure high DPI scaling is handled correctly
    # Use methods available in PyQt5
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    
    # Check if an instance already exists (e.g., in interactive environments)
    # if QApplication.instance() is None:
    #      app = QApplication(sys.argv)
    # else:
    #      app = QApplication.instance()
        
    window = ImageOptimizerWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    # Add import for QSizePolicy potentially needed in error reporting
    from PyQt5.QtWidgets import QSizePolicy 
    main()
