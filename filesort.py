import os
import shutil
import sys
import json
import copy
import winreg
import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import QProgressBar, QMessageBox, QFileDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QTabWidget, QListWidget, QListWidgetItem, QPushButton, QLabel, QLineEdit, QCheckBox, QSpinBox, QComboBox, QTextEdit, QSplitter, QWidget


# -----------------------------
# CONFIGURATION MANAGEMENT
# -----------------------------
class ConfigManager:
    def __init__(self):
        self.config_file = os.path.join(os.path.expanduser("~"), "AppData", "Local", "FileSort", "config.json")
        self.ensure_config_dir()
        self.default_config = {
            "categories": {
                "Documents": [".pdf", ".docx", ".txt", ".rtf", ".odt", ".pptx", ".xlsx", ".csv", ".doc", ".ppt"],
                "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".svg", ".ico"],
                "Videos": [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".m4v", ".webm"],
                "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"],
                "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"],
                "Installers": [".exe", ".msi", ".bat", ".cmd", ".appx", ".msix"],
                "Code": [".py", ".cpp", ".c", ".h", ".js", ".html", ".css", ".java", ".json", ".xml", ".ts", ".php", ".rb", ".go"],
                "Spreadsheets": [".xls", ".xlsx", ".ods", ".csv"],
                "Misc": []
            },
            "settings": {
                "default_source": os.path.join(os.path.expanduser("~"), "Downloads"),
                "default_dest": os.path.join(os.path.expanduser("~"), "Downloads"),
                "create_date_folders": False,
                "skip_duplicates": False,
                "log_level": "INFO"
            },
            "recent_operations": []
        }
        self.config = self.load_config()
    
    def ensure_config_dir(self):
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
    
    def load_config(self):
        try:
            # Always start with a fresh copy of default config
            default_copy = copy.deepcopy(self.default_config)
            
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults for any missing keys
                return self.merge_configs(default_copy, config)
            return default_copy
        except Exception as e:
            logging.error(f"Failed to load config: {e}")
            return copy.deepcopy(self.default_config)
    
    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save config: {e}")
    
    def merge_configs(self, default, user):
        """Recursively merge user config with defaults"""
        result = copy.deepcopy(default)
        for key, value in user.items():
            if key in result:
                if isinstance(value, dict) and isinstance(result[key], dict):
                    result[key] = self.merge_configs(result[key], value)
                else:
                    result[key] = value
            else:
                result[key] = value
        return result

# Global config manager
config_manager = ConfigManager()


# -----------------------------
# ENHANCED FILE ORGANIZATION LOGIC
# -----------------------------
class FileOrganizer(QThread):
    progress_updated = pyqtSignal(int, int)  # current, total
    file_processed = pyqtSignal(str, str)  # filename, status
    operation_completed = pyqtSignal(dict)  # results summary
    
    def __init__(self, source_folder, destination_folder, options):
        super().__init__()
        self.source_folder = source_folder
        self.destination_folder = destination_folder
        self.options = options
        self.should_stop = False
        
    def stop(self):
        self.should_stop = True
        
    def run(self):
        try:
            results = self.organize_files()
            self.operation_completed.emit(results)
        except Exception as e:
            logging.error(f"Organization failed: {e}")
            self.operation_completed.emit({"error": str(e)})
    
    def organize_files(self):
        results = {
            "total_files": 0,
            "processed": 0,
            "skipped": 0,
            "errors": 0,
            "categories_created": set(),
            "errors_list": [],
            "moved_files": []  # Track movements for revert
        }
        
        # Collect all files first for progress tracking
        all_files = []
        for root, dirs, files in os.walk(self.source_folder):
            for file in files:
                file_path = os.path.join(root, file)
                all_files.append(file_path)
            if not self.options.get("recursive", True):
                break
        
        results["total_files"] = len(all_files)
        
        for i, file_path in enumerate(all_files):
            if self.should_stop:
                break
                
            try:
                filename = os.path.basename(file_path)
                _, ext = os.path.splitext(filename)
                
                # Skip files without extensions if configured
                if not ext and self.options.get("skip_no_extension", True):
                    results["skipped"] += 1
                    logging.info(f"Skipped file (no extension): {file_path}")
                    self.file_processed.emit(filename, "Skipped (no extension)")
                    continue
                
                # Determine category
                category = self.get_file_category(ext)
                
                # Create destination path
                dest_path = self.create_destination_path(category, filename)
                
                # Handle duplicates
                if os.path.exists(dest_path):
                    if self.options.get("skip_duplicates", True):
                        # Move to duplicates folder instead of skipping
                        duplicates_dir = os.path.join(self.destination_folder, "duplicates")
                        dest_path = os.path.join(duplicates_dir, filename)
                        
                        # If duplicate also exists in duplicates folder, make it unique
                        if os.path.exists(dest_path):
                            dest_path = self.get_unique_filename(dest_path)
                        
                        category = "duplicates"
                    else:
                        dest_path = self.get_unique_filename(dest_path)
                
                # Move file
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.move(file_path, dest_path)
                
                # Track the movement for revert
                results["moved_files"].append({
                    "source": file_path,
                    "destination": dest_path,
                    "filename": filename
                })
                
                results["processed"] += 1
                results["categories_created"].add(category)
                
                # Enhanced logging
                logging.info(f"Moved file: {file_path} -> {dest_path}")
                self.file_processed.emit(filename, f"Moved to {category} folder")
                
            except Exception as e:
                results["errors"] += 1
                error_msg = f"Failed to move {filename}: {str(e)}"
                results["errors_list"].append(error_msg)
                logging.error(error_msg)
                self.file_processed.emit(filename, f"Error: {str(e)}")
            
            # Update progress
            self.progress_updated.emit(i + 1, results["total_files"])
        
        return results
    
    def get_file_category(self, ext):
        """Determine file category based on extension"""
        categories = config_manager.config["categories"]
        ext_lower = ext.lower()
        
        for category, extensions in categories.items():
            if ext_lower in extensions:
                return category
        return "Misc"
    
    def create_destination_path(self, category, filename):
        """Create destination path with optional date folders"""
        base_path = os.path.join(self.destination_folder, category)
        
        if self.options.get("create_date_folders", False):
            today = datetime.now().strftime("%Y-%m-%d")
            base_path = os.path.join(base_path, today)
        
        return os.path.join(base_path, filename)
    
    def get_unique_filename(self, filepath):
        """Generate unique filename if file exists"""
        base, ext = os.path.splitext(filepath)
        counter = 1
        while os.path.exists(filepath):
            filepath = f"{base}_{counter}{ext}"
            counter += 1
        return filepath


# -----------------------------
# STARTUP GUIDANCE (Microsoft Store Compatible)
# -----------------------------
def show_startup_guidance():
    """Show guidance for manual startup configuration"""
    guidance_text = """
To enable FileSort Pro to start with Windows:

1. Right-click on the Start button
2. Select "Run" from the menu
3. Type: shell:startup
4. Press Enter
5. Copy a shortcut to FileSort Pro into this folder

Alternative method:
1. Press Windows + R
2. Type: shell:startup
3. Press Enter
4. Copy FileSort Pro shortcut here

This method is safer and more reliable than registry modifications.
    """
    return guidance_text.strip()


# -----------------------------
# ENHANCED MAIN APPLICATION WINDOW
# -----------------------------
class FileSortApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_logging()
        self.setup_ui()
        self.setup_tray()
        self.load_settings()
        self.organizer_thread = None
        self.last_operation_moves = []  # Store last operation's file movements
        
    def setup_logging(self):
        """Setup logging for the application"""
        log_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "FileSort", "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"filesort_{datetime.now().strftime('%Y%m%d')}.log")
        
        # Get root logger and clear any existing handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Set logging level
        root_logger.setLevel(getattr(logging, config_manager.config["settings"]["log_level"]))
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # Add file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # Log application startup
        logging.info("=" * 50)
        logging.info("FileSort Pro application started")
        logging.info(f"Log level: {config_manager.config['settings']['log_level']}")
        logging.info("=" * 50)
    
    def setup_ui(self):
        """Setup the main user interface"""
        self.setWindowTitle("FileSort Pro - Smart File Organizer")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
        # Create central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_organize_tab()
        self.create_categories_tab()
        self.create_settings_tab()
        self.create_logs_tab()
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
    
    def create_organize_tab(self):
        """Create the main organization tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Source folder selection
        source_group = QGroupBox("Source Folder")
        source_layout = QVBoxLayout(source_group)
        
        source_input_layout = QHBoxLayout()
        self.source_input = QLineEdit()
        self.source_input.setText(config_manager.config["settings"]["default_source"])
        self.source_btn = QPushButton("Browse")
        self.source_btn.clicked.connect(self.browse_source)
        
        source_input_layout.addWidget(self.source_input)
        source_input_layout.addWidget(self.source_btn)
        source_layout.addLayout(source_input_layout)
        
        # Destination folder selection
        dest_group = QGroupBox("Destination Folder")
        dest_layout = QVBoxLayout(dest_group)
        
        dest_input_layout = QHBoxLayout()
        self.dest_input = QLineEdit()
        self.dest_input.setText(config_manager.config["settings"]["default_dest"])
        self.dest_btn = QPushButton("Browse")
        self.dest_btn.clicked.connect(self.browse_dest)
        
        dest_input_layout.addWidget(self.dest_input)
        dest_input_layout.addWidget(self.dest_btn)
        dest_layout.addLayout(dest_input_layout)
        
        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        
        self.recursive_chk = QCheckBox("Include subfolders")
        self.recursive_chk.setChecked(True)
        
        self.date_folders_chk = QCheckBox("Create date-based subfolders")
        self.date_folders_chk.setChecked(config_manager.config["settings"].get("create_date_folders", False))
        
        self.skip_duplicates_chk = QCheckBox("Move duplicate files to duplicates folder")
        self.skip_duplicates_chk.setChecked(config_manager.config["settings"].get("skip_duplicates", False))
        
        self.preview_chk = QCheckBox("Preview before organizing")
        self.preview_chk.setChecked(True)
        
        options_layout.addWidget(self.recursive_chk)
        options_layout.addWidget(self.date_folders_chk)
        options_layout.addWidget(self.skip_duplicates_chk)
        options_layout.addWidget(self.preview_chk)
        
        # Action buttons
        button_layout = QHBoxLayout()
        self.run_btn = QPushButton("Organize Files")
        self.run_btn.clicked.connect(self.run_sort)
        self.run_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; }")
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_organization)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; padding: 10px; }")
        
        self.revert_btn = QPushButton("Revert Last Organization")
        self.revert_btn.clicked.connect(self.revert_last_operation)
        self.revert_btn.setEnabled(False)
        self.revert_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; font-weight: bold; padding: 10px; }")
        
        button_layout.addWidget(self.run_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.revert_btn)
        button_layout.addStretch()
        
        # Results area
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(150)
        self.results_text.setReadOnly(True)
        results_layout.addWidget(self.results_text)
        
        # Add to main layout
        layout.addWidget(source_group)
        layout.addWidget(dest_group)
        layout.addWidget(options_group)
        layout.addLayout(button_layout)
        layout.addWidget(results_group)
        
        self.tab_widget.addTab(tab, "Organize Files")
    
    def create_categories_tab(self):
        """Create the categories management tab"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        # Left side - categories list
        left_panel = QVBoxLayout()
        
        categories_group = QGroupBox("File Categories")
        categories_layout = QVBoxLayout(categories_group)
        
        self.categories_list = QListWidget()
        self.populate_categories_list()
        self.categories_list.currentItemChanged.connect(self.on_category_selected)
        categories_layout.addWidget(self.categories_list)
        
        # Category buttons
        cat_buttons_layout = QHBoxLayout()
        self.add_category_btn = QPushButton("Add Category")
        self.add_category_btn.clicked.connect(self.add_category)
        self.remove_category_btn = QPushButton("Remove Category")
        self.remove_category_btn.clicked.connect(self.remove_category)
        
        cat_buttons_layout.addWidget(self.add_category_btn)
        cat_buttons_layout.addWidget(self.remove_category_btn)
        categories_layout.addLayout(cat_buttons_layout)
        
        left_panel.addWidget(categories_group)
        
        # Right side - extensions management
        right_panel = QVBoxLayout()
        
        extensions_group = QGroupBox("File Extensions")
        extensions_layout = QVBoxLayout(extensions_group)
        
        # Current category label
        self.current_category_label = QLabel("Select a category")
        extensions_layout.addWidget(self.current_category_label)
        
        # Extensions list
        self.extensions_list = QListWidget()
        extensions_layout.addWidget(self.extensions_list)
        
        # Extension management
        ext_input_layout = QHBoxLayout()
        self.extension_input = QLineEdit()
        self.extension_input.setPlaceholderText("Enter extension (e.g., .pdf)")
        self.add_extension_btn = QPushButton("Add")
        self.add_extension_btn.clicked.connect(self.add_extension)
        self.remove_extension_btn = QPushButton("Remove")
        self.remove_extension_btn.clicked.connect(self.remove_extension)
        
        ext_input_layout.addWidget(self.extension_input)
        ext_input_layout.addWidget(self.add_extension_btn)
        ext_input_layout.addWidget(self.remove_extension_btn)
        extensions_layout.addLayout(ext_input_layout)
        
        right_panel.addWidget(extensions_group)
        
        # Add panels to main layout
        layout.addLayout(left_panel, 1)
        layout.addLayout(right_panel, 1)
        
        self.tab_widget.addTab(tab, "Categories")
    
    def create_settings_tab(self):
        """Create the settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # General settings
        general_group = QGroupBox("General Settings")
        general_layout = QVBoxLayout(general_group)
        
        # Startup guidance section
        startup_layout = QHBoxLayout()
        self.startup_chk = QCheckBox("Start with Windows")
        self.startup_chk.setChecked(False)  # Always start unchecked
        self.startup_chk.setEnabled(False)  # Disable the checkbox
        self.startup_chk.setToolTip("Click 'Setup Startup' button for manual configuration")
        
        self.startup_help_btn = QPushButton("Setup Startup")
        self.startup_help_btn.clicked.connect(self.show_startup_help)
        self.startup_help_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; font-weight: bold; padding: 5px; }")
        
        startup_layout.addWidget(self.startup_chk)
        startup_layout.addWidget(self.startup_help_btn)
        startup_layout.addStretch()
        
        general_layout.addLayout(startup_layout)
        
        # Advanced settings
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QVBoxLayout(advanced_group)
        
        # Log level
        log_layout = QHBoxLayout()
        log_layout.addWidget(QLabel("Log Level:"))
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText(config_manager.config["settings"]["log_level"])
        log_layout.addWidget(self.log_level_combo)
        log_layout.addStretch()
        advanced_layout.addLayout(log_layout)
        
        # Save settings button
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        save_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 8px; }")
        
        layout.addWidget(general_group)
        layout.addWidget(advanced_group)
        layout.addWidget(save_btn)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Settings")
    
    def create_logs_tab(self):
        """Create the logs tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QtGui.QFont("Consolas", 9))
        layout.addWidget(self.log_display)
        
        # Log controls
        log_controls = QHBoxLayout()
        refresh_logs_btn = QPushButton("Refresh Logs")
        refresh_logs_btn.clicked.connect(self.refresh_logs)
        clear_logs_btn = QPushButton("Clear Logs")
        clear_logs_btn.clicked.connect(self.clear_logs)
        
        log_controls.addWidget(refresh_logs_btn)
        log_controls.addWidget(clear_logs_btn)
        log_controls.addStretch()
        
        layout.addLayout(log_controls)
        
        self.tab_widget.addTab(tab, "Logs")
        
        # Connect tab change signal to auto-refresh logs
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # Load logs initially
        self.refresh_logs()
    
    def setup_tray(self):
        """Setup system tray integration"""
        if QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QtWidgets.QSystemTrayIcon(self)
            self.tray_icon.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon))
            
            tray_menu = QtWidgets.QMenu()
            tray_menu.addAction("Open FileSort", self.show_window)
            tray_menu.addAction("Organize Now", self.run_sort)
            tray_menu.addSeparator()
            tray_menu.addAction("Exit", self.close)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self.tray_icon_activated)
            self.tray_icon.show()
    
    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QtWidgets.QSystemTrayIcon.DoubleClick:
            self.show_window()
    
    def show_window(self):
        """Show and activate the main window"""
        self.showNormal()
        self.activateWindow()
        self.raise_()
    
    def load_settings(self):
        """Load settings from configuration"""
        settings = config_manager.config["settings"]
        self.source_input.setText(settings.get("default_source", os.path.join(os.path.expanduser("~"), "Downloads")))
        self.dest_input.setText(settings.get("default_dest", os.path.join(os.path.expanduser("~"), "Downloads")))
        
        # Also save source and dest when they're changed
        self.source_input.textChanged.connect(self.save_default_paths)
        self.dest_input.textChanged.connect(self.save_default_paths)
    
    def save_default_paths(self):
        """Save source and destination paths to config"""
        config_manager.config["settings"]["default_source"] = self.source_input.text()
        config_manager.config["settings"]["default_dest"] = self.dest_input.text()
        config_manager.save_config()
    
    def save_settings(self):
        """Save current settings to configuration"""
        config_manager.config["settings"]["log_level"] = self.log_level_combo.currentText()
        config_manager.config["settings"]["create_date_folders"] = self.date_folders_chk.isChecked()
        config_manager.config["settings"]["skip_duplicates"] = self.skip_duplicates_chk.isChecked()
        config_manager.config["settings"]["default_source"] = self.source_input.text()
        config_manager.config["settings"]["default_dest"] = self.dest_input.text()
        config_manager.save_config()
        
        QMessageBox.information(self, "Settings", "Settings saved successfully!")
    
    def browse_source(self):
        """Browse for source folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select source folder")
        if folder:
            self.source_input.setText(folder)
    
    def browse_dest(self):
        """Browse for destination folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select destination folder")
        if folder:
            self.dest_input.setText(folder)
    
    def show_startup_help(self):
        """Show startup configuration guidance"""
        guidance = show_startup_guidance()
        
        # Create a custom dialog with the guidance
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Startup Configuration Guide")
        dialog.setText("How to enable FileSort Pro to start with Windows:")
        dialog.setDetailedText(guidance)
        dialog.setIcon(QMessageBox.Information)
        
        # Add a button to open the startup folder
        open_folder_btn = dialog.addButton("Open Startup Folder", QMessageBox.ActionRole)
        dialog.addButton(QMessageBox.Ok)
        
        result = dialog.exec_()
        
        if result == 0:  # Open Startup Folder button clicked
            try:
                import subprocess
                subprocess.run(['explorer', 'shell:startup'], check=True)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not open startup folder: {e}")
    
    def run_sort(self):
        """Start file organization process"""
        src = self.source_input.text()
        dst = self.dest_input.text()
        
        if not src or not dst:
            QMessageBox.warning(self, "Error", "Please select both source and destination folders.")
            return
        
        if not os.path.exists(src):
            QMessageBox.warning(self, "Error", "Source folder does not exist.")
            return
        
        # Prepare options
        options = {
            "recursive": self.recursive_chk.isChecked(),
            "create_date_folders": self.date_folders_chk.isChecked(),
            "skip_duplicates": self.skip_duplicates_chk.isChecked(),
            "skip_no_extension": True
        }
        
        # Start organization thread
        self.organizer_thread = FileOrganizer(src, dst, options)
        self.organizer_thread.progress_updated.connect(self.update_progress)
        self.organizer_thread.file_processed.connect(self.log_file_processed)
        self.organizer_thread.operation_completed.connect(self.organization_completed)
        
        self.organizer_thread.start()
        
        # Update UI
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.results_text.clear()
        self.status_bar.showMessage("Organizing files...")
    
    def stop_organization(self):
        """Stop the organization process"""
        if self.organizer_thread:
            self.organizer_thread.stop()
            self.organizer_thread.wait()
            self.organization_completed({"stopped": True})
    
    def update_progress(self, current, total):
        """Update progress bar"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
    
    def log_file_processed(self, filename, status):
        """Log file processing status"""
        self.results_text.append(f"{filename}: {status}")
        self.results_text.ensureCursorVisible()
    
    def organization_completed(self, results):
        """Handle organization completion"""
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        if "error" in results:
            QMessageBox.critical(self, "Error", f"Organization failed: {results['error']}")
            self.status_bar.showMessage("Organization failed")
        elif results.get("stopped"):
            self.status_bar.showMessage("Organization stopped")
        else:
            # Show results summary
            summary = f"Organization completed!\n\n"
            summary += f"Total files: {results['total_files']}\n"
            summary += f"Processed: {results['processed']}\n"
            summary += f"Skipped: {results['skipped']}\n"
            summary += f"Errors: {results['errors']}\n"
            
            if results['errors'] > 0:
                summary += f"\nErrors:\n" + "\n".join(results['errors_list'][:5])
                if len(results['errors_list']) > 5:
                    summary += f"\n... and {len(results['errors_list']) - 5} more errors"
            
            QMessageBox.information(self, "Organization Complete", summary)
            self.status_bar.showMessage("Organization completed successfully")
            
            # Store the file movements for revert
            if "moved_files" in results and len(results["moved_files"]) > 0:
                self.last_operation_moves = results["moved_files"]
                self.revert_btn.setEnabled(True)
                logging.info(f"Stored {len(self.last_operation_moves)} file movements for revert")
            
            # Save operation to recent operations
            config_manager.config["recent_operations"].append({
                "timestamp": datetime.now().isoformat(),
                "source": self.source_input.text(),
                "destination": self.dest_input.text(),
                "results": results
            })
            config_manager.save_config()
    
    def populate_categories_list(self):
        """Populate the categories list widget"""
        self.categories_list.clear()
        for category in config_manager.config["categories"].keys():
            self.categories_list.addItem(category)
    
    def on_category_selected(self, current, previous):
        """Handle category selection"""
        if current:
            category = current.text()
            self.current_category_label.setText(f"Extensions for: {category}")
            self.populate_extensions_list(category)
    
    def populate_extensions_list(self, category):
        """Populate extensions list for selected category"""
        self.extensions_list.clear()
        extensions = config_manager.config["categories"].get(category, [])
        for ext in sorted(extensions):
            self.extensions_list.addItem(ext)
    
    def add_category(self):
        """Add a new category"""
        name, ok = QtWidgets.QInputDialog.getText(self, "Add Category", "Category name:")
        if ok and name:
            if name not in config_manager.config["categories"]:
                config_manager.config["categories"][name] = []
                config_manager.save_config()
                self.populate_categories_list()
            else:
                QMessageBox.warning(self, "Error", "Category already exists!")
    
    def remove_category(self):
        """Remove selected category"""
        current = self.categories_list.currentItem()
        if current:
            category = current.text()
            if category == "Misc":
                QMessageBox.warning(self, "Error", "Cannot remove the Misc category!")
                return
            
            reply = QMessageBox.question(self, "Confirm", f"Remove category '{category}'?")
            if reply == QMessageBox.Yes:
                del config_manager.config["categories"][category]
                config_manager.save_config()
                self.populate_categories_list()
    
    def add_extension(self):
        """Add extension to current category"""
        current = self.categories_list.currentItem()
        if not current:
            QMessageBox.warning(self, "Error", "Please select a category first!")
            return
        
        extension = self.extension_input.text().strip()
        if not extension:
            return
        
        if not extension.startswith('.'):
            extension = '.' + extension
        
        category = current.text()
        if extension not in config_manager.config["categories"][category]:
            config_manager.config["categories"][category].append(extension)
            config_manager.save_config()
            self.populate_extensions_list(category)
            self.extension_input.clear()
        else:
            QMessageBox.warning(self, "Error", "Extension already exists in this category!")
    
    def remove_extension(self):
        """Remove selected extension"""
        current_ext = self.extensions_list.currentItem()
        current_cat = self.categories_list.currentItem()
        
        if current_ext and current_cat:
            extension = current_ext.text()
            category = current_cat.text()
            
            config_manager.config["categories"][category].remove(extension)
            config_manager.save_config()
            self.populate_extensions_list(category)
    
    def on_tab_changed(self, index):
        """Handle tab change - refresh logs when logs tab is selected"""
        tab_name = self.tab_widget.tabText(index)
        if tab_name == "Logs":
            self.refresh_logs()
    
    def refresh_logs(self):
        """Refresh the log display"""
        log_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "FileSort", "logs")
        log_file = os.path.join(log_dir, f"filesort_{datetime.now().strftime('%Y%m%d')}.log")
        
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        self.log_display.setPlainText(content)
                        # Scroll to bottom to show most recent logs
                        cursor = self.log_display.textCursor()
                        cursor.movePosition(cursor.End)
                        self.log_display.setTextCursor(cursor)
                    else:
                        self.log_display.setPlainText("Log file exists but is empty.")
            except Exception as e:
                self.log_display.setPlainText(f"Error reading log file: {str(e)}")
        else:
            self.log_display.setPlainText("No log file found for today.\nLogs will appear here after you organize files.")
    
    def clear_logs(self):
        """Clear the log display"""
        self.log_display.clear()
    
    def revert_last_operation(self):
        """Revert the last file organization operation"""
        if not self.last_operation_moves:
            QMessageBox.warning(self, "No Operation", "No previous operation to revert.")
            return
        
        reply = QMessageBox.question(self, "Confirm Revert", 
                                    f"Are you sure you want to revert the last organization?\n\n"
                                    f"This will move {len(self.last_operation_moves)} files back to their original locations.",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.No:
            return
        
        # Create revert progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.last_operation_moves))
        self.progress_bar.setValue(0)
        self.revert_btn.setEnabled(False)
        self.results_text.clear()
        self.status_bar.showMessage("Reverting operation...")
        
        reverted = 0
        errors = 0
        
        for idx, move in enumerate(self.last_operation_moves):
            try:
                # Move file back from destination to source
                source = move["destination"]
                dest = move["source"]
                
                # Make sure source exists
                if not os.path.exists(source):
                    logging.warning(f"Source file not found during revert: {source}")
                    errors += 1
                    continue
                
                # Create destination directory if it doesn't exist
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                
                # Handle if destination already exists
                if os.path.exists(dest):
                    dest = self.get_unique_filename(dest)
                
                # Move file back
                shutil.move(source, dest)
                reverted += 1
                logging.info(f"Reverted: {source} -> {dest}")
                self.results_text.append(f"{move['filename']}: Reverted successfully")
                self.results_text.ensureCursorVisible()
                
            except Exception as e:
                errors += 1
                error_msg = f"Failed to revert {move['filename']}: {str(e)}"
                logging.error(error_msg)
                self.results_text.append(f"{move['filename']}: Error - {str(e)}")
                self.results_text.ensureCursorVisible()
            
            # Update progress
            self.progress_bar.setValue(idx + 1)
        
        # Show completion
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage(f"Revert complete: {reverted} files reverted, {errors} errors")
        
        summary = f"Revert completed!\n\n"
        summary += f"Reverted: {reverted} files\n"
        summary += f"Errors: {errors}"
        
        QMessageBox.information(self, "Revert Complete", summary)
        
        # Clear the stored moves
        self.last_operation_moves = []
    
    def get_unique_filename(self, filepath):
        """Generate unique filename if file exists"""
        base, ext = os.path.splitext(filepath)
        counter = 1
        while os.path.exists(filepath):
            filepath = f"{base}_{counter}{ext}"
            counter += 1
        return filepath
    
    def closeEvent(self, event):
        """Handle application close event"""
        if self.organizer_thread and self.organizer_thread.isRunning():
            reply = QMessageBox.question(self, "Confirm Exit", 
                                       "Organization is in progress. Are you sure you want to exit?")
            if reply == QMessageBox.Yes:
                self.organizer_thread.stop()
                self.organizer_thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


# -----------------------------
# APP ENTRY POINT
# -----------------------------
def main():
    """Main application entry point"""
    # Create application
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("FileSort Pro")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("FileSort Solutions")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = FileSortApp()
    window.show()
    
    # Handle system tray
    if not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "System Tray", 
                            "System tray is not available on this system.")
        return 1
    
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
