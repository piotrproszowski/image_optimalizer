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
                            QComboBox)
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

def optimize_image(input_path, output_path, max_width, max_height, quality, convert_to_webp=False):
    """Optimize the image by resizing and optionally converting to webp format."""
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with Image.open(input_path) as img:
            img.thumbnail((max_width, max_height))
            
            if convert_to_webp:
                output_path = os.path.splitext(output_path)[0] + ".webp"
            
            img.save(output_path, optimize=True, quality=quality)
        return True
    except Exception as e:
        return str(e)

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
        self.setGeometry(100, 100, 600, 400)
        
        # Add author info label
        self.author_label = QLabel("© 2024 Piotr Proszowski")
        self.author_label.setAlignment(Qt.AlignRight)
        self.author_label.setStyleSheet("color: #666666; padding: 5px;")
        
        # Detect system theme
        app = QApplication.instance()
        self.is_dark_mode = app.palette().window().color().lightness() < 128
        
        # Set theme-dependent styles
        if self.is_dark_mode:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1e1e1e;
                }
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    padding: 8px 15px;
                    border-radius: 4px;
                    min-width: 80px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QLineEdit {
                    padding: 8px;
                    border: 1px solid #333;
                    border-radius: 4px;
                    background-color: #2d2d2d;
                    color: #ffffff;
                }
                QLineEdit:focus {
                    border: 1px solid #4CAF50;
                    background-color: #363636;
                }
                QProgressBar {
                    border: 1px solid #333;
                    border-radius: 4px;
                    text-align: center;
                    background-color: #2d2d2d;
                    color: #ffffff;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    border-radius: 3px;
                }
                QLabel {
                    color: #ffffff;
                }
                QCheckBox {
                    color: #ffffff;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    background-color: #2d2d2d;
                    border: 1px solid #333;
                }
                QCheckBox::indicator:checked {
                    background-color: #4CAF50;
                    border-radius: 2px;
                }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #ffffff;
                }
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    padding: 8px 15px;
                    border-radius: 4px;
                    min-width: 80px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QLineEdit {
                    padding: 8px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background-color: #fafafa;
                }
                QLineEdit:focus {
                    border: 1px solid #4CAF50;
                    background-color: white;
                }
                QProgressBar {
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    text-align: center;
                    background-color: #fafafa;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    border-radius: 3px;
                }
                QLabel {
                    color: #333333;
                }
                QCheckBox {
                    color: #333333;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                }
                QCheckBox::indicator:checked {
                    background-color: #4CAF50;
                    border-radius: 2px;
                }
            """)

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

        # Resolution selection
        resolution_layout = QHBoxLayout()
        
        resolution_label = QLabel("Resolution:")
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(self.resolution_presets.keys())
        self.resolution_combo.currentTextChanged.connect(self.on_resolution_changed)
        
        resolution_layout.addWidget(resolution_label)
        resolution_layout.addWidget(self.resolution_combo)
        layout.addLayout(resolution_layout)

        # Custom resolution inputs (initially hidden)
        self.custom_resolution = QWidget()
        custom_layout = QHBoxLayout(self.custom_resolution)
        
        self.width_input = QLineEdit("800")
        self.height_input = QLineEdit("800")
        
        custom_layout.addWidget(QLabel("Width:"))
        custom_layout.addWidget(self.width_input)
        custom_layout.addWidget(QLabel("Height:"))
        custom_layout.addWidget(self.height_input)
        
        self.custom_resolution.setVisible(False)
        layout.addWidget(self.custom_resolution)

        # Settings
        self.quality_input = QLineEdit("85")
        self.webp_checkbox = QCheckBox("Convert to WebP")
        self.webp_checkbox.setChecked(True)
        
        # Add recursive option
        self.recursive_checkbox = QCheckBox("Process subfolders recursively")
        self.recursive_checkbox.setChecked(True)

        # Add settings to layout
        layout.addWidget(QLabel("Quality (1-100):"))
        layout.addWidget(self.quality_input)
        layout.addWidget(self.webp_checkbox)
        layout.addWidget(self.recursive_checkbox)

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
        self.custom_resolution.setVisible(is_custom)
        
        if not is_custom:
            width, height = self.resolution_presets[text]
            self.width_input.setText(str(width))
            self.height_input.setText(str(height))

    def get_all_image_files(self, directory, recursive=False):
        """Get all image files in the directory, optionally recursively."""
        image_files = []
        
        if recursive:
            # Walk through all directories and subdirectories
            for root, _, files in os.walk(directory):
                for filename in files:
                    if is_image_file(filename):
                        # Store the full path and relative path for processing
                        full_path = os.path.join(root, filename)
                        rel_path = os.path.relpath(full_path, directory)
                        image_files.append((full_path, rel_path))
        else:
            # Just process the files in the top directory
            for filename in os.listdir(directory):
                full_path = os.path.join(directory, filename)
                if os.path.isfile(full_path) and is_image_file(filename):
                    image_files.append((full_path, filename))
                    
        return image_files

    def start_optimization(self):
        directory = self.folder_input.text()
        if not os.path.isdir(directory):
            self.show_error("Please select a valid directory")
            return

        try:
            max_width = int(self.width_input.text() or 800)
            max_height = int(self.height_input.text() or 800)
            quality = int(self.quality_input.text() or 85)
            recursive = self.recursive_checkbox.isChecked()
            
            if max_width <= 0 or max_height <= 0:
                raise ValueError("Dimensions must be positive numbers")
                
        except ValueError as e:
            self.show_error(f"Invalid input: {str(e)}")
            return

        # Get all image files (potentially recursively)
        image_files = self.get_all_image_files(directory, recursive)
        
        total_images = len(image_files)
        
        if total_images == 0:
            self.show_info("No images found in selected directory")
            return

        processed = 0
        errors = 0
        self.progress_bar.setMaximum(total_images)
        self.progress_bar.setValue(0)

        for input_path, rel_path in image_files:
            # Create output path preserving directory structure
            output_path = os.path.join(directory, "optimized", rel_path)
            
            result = optimize_image(input_path, output_path, max_width, max_height, 
                                  quality, self.webp_checkbox.isChecked())
            
            if result is not True:
                self.show_error(f"Error processing {rel_path}: {result}")
                errors += 1
            
            processed += 1
            self.progress_bar.setValue(processed)
            self.status_label.setText(f"Processing: {processed}/{total_images}")
            QApplication.processEvents()

        success_count = processed - errors
        self.show_info(f"Optimized {success_count} images successfully" + 
                      (f", {errors} errors" if errors > 0 else ""))
        self.status_label.setText("Ready")
        self.progress_bar.setValue(0)

def main():
    app = QApplication(sys.argv)
    window = ImageOptimizerWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
