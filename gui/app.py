#!/usr/bin/env python3
"""
ContextLLM PyQt6 GUI Application
Modern interface for file content aggregation tool.
"""

import sys
import os
import platform
from typing import Set

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QTabWidget, QTextEdit, QCheckBox, QComboBox, QPushButton, 
    QLabel, QLineEdit, QProgressBar, QGroupBox, QScrollArea, QFrame, 
    QMessageBox, QFileDialog, QStatusBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSettings
from PyQt6.QtGui import QIcon, QFont, QAction, QKeySequence, QShortcut

# Import core functionality
from core.file_processor import FileProcessor
from core.github_processor import GitHubProcessor
from core.template_manager import template_manager
from utils.helpers import file_utils, token_utils, validation_utils
from utils.logger import setup_logging, get_logger, log_user_action, log_error_with_context, emergency_flush, log_critical_error
from config import settings, APP_NAME, APP_VERSION, DEFAULT_MODEL, MIN_WINDOW_SIZE, DEFAULT_WINDOW_SIZE

class ProcessingThread(QThread):
    """Thread for background file processing"""
    progress_updated = pyqtSignal(float)
    processing_finished = pyqtSignal(str, list)
    processing_error = pyqtSignal(str)
    
    def __init__(self, file_processor, selected_extensions, github_processor=None):
        super().__init__()
        self.file_processor = file_processor
        self.selected_extensions = selected_extensions
        self.github_processor = github_processor
        
    def run(self):
        try:
            def progress_callback(progress):
                self.progress_updated.emit(progress)
            
            content, processed_files = self.file_processor.aggregate_content(
                self.selected_extensions, progress_callback, self.github_processor
            )
            
            self.processing_finished.emit(content, processed_files)
            
        except Exception as e:
            self.processing_error.emit(f"Processing failed: {str(e)}")

class ScanningThread(QThread):
    """Thread for background directory scanning"""
    scanning_finished = pyqtSignal(set)
    scanning_error = pyqtSignal(str)
    
    def __init__(self, file_processor, folder_path, exclude_patterns):
        super().__init__()
        self.file_processor = file_processor
        self.folder_path = folder_path
        self.exclude_patterns = exclude_patterns
        
    def run(self):
        try:
            all_files, extensions = self.file_processor.scan_directory(
                self.folder_path, self.exclude_patterns
            )
            self.scanning_finished.emit(extensions)
            
        except Exception as e:
            self.scanning_error.emit(f"Failed to scan directory: {str(e)}")

class GitHubThread(QThread):
    """Thread for background GitHub repository loading"""
    github_loaded = pyqtSignal(list, set, str)
    github_error = pyqtSignal(str)
    
    def __init__(self, github_processor, repo_info):
        super().__init__()
        self.github_processor = github_processor
        self.repo_info = repo_info
        
    def run(self):
        try:
            # Verify repository exists
            is_valid, message = self.github_processor.verify_repository(
                self.repo_info['owner'], self.repo_info['repo']
            )
            
            if not is_valid:
                self.github_error.emit(message)
                return
            
            # Get repository tree
            files_list, extensions, status_message = self.github_processor.get_repository_tree(
                self.repo_info['owner'], self.repo_info['repo'], self.repo_info['branch']
            )
            
            # Check for rate limit issues
            if "Rate limit exceeded" in status_message:
                self.github_error.emit(status_message)
                return
            
            self.github_loaded.emit(files_list, extensions, status_message)
            
        except Exception as e:
            self.github_error.emit(f"Failed to load GitHub repository: {str(e)}")

class ContextLLMApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize logging first
        self.logger = get_logger("GUI")
        self.logger.info("Initializing ContextLLM GUI Application")
        
        # Windows-specific optimizations
        if platform.system() == "Windows":
            self.logger.info("Applied Windows-specific optimizations")
        
        try:
            # Initialize core components
            self.logger.info("Initializing core components")
            self.file_processor = FileProcessor()
            self.github_processor = GitHubProcessor()
            
            # Application state
            self.selected_folder = None
            self.selected_model = DEFAULT_MODEL
            self.aggregated_content = ""
            self.current_template = None
            self.current_source_type = "local"  # "local" or "github"
            self.current_github_info = None
            
            # UI components
            self.extension_checkboxes = {}
            self.processing_thread = None
            self.scanning_thread = None
            
            # Settings
            self.settings = QSettings("ContextLLM", "ContextLLM")
            self.logger.info("Application state initialized")
            
            # Initialize UI
            self.logger.info("Setting up user interface")
            self.init_ui()
            self.setup_styles()
            
            # Restore settings and apply theme
            self.restore_settings()
            self.logger.info("GUI initialization completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}")
            log_critical_error(e, "ContextLLMApp.__init__")
            raise
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        
        # Set up smart window sizing first
        self.setup_smart_window()
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create header
        self.create_header(main_layout)
        
        # Create main content area
        self.create_main_content(main_layout)
        
        # Create status bar
        self.create_status_bar()
        
        # Create menu bar
        self.create_menu_bar()
        
        # Setup styles
        self.setup_styles()
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()
        
        # Setup tooltips
        self.setup_tooltips()
        
    def setup_smart_window(self):
        """Set up smart window sizing and positioning"""
        try:
            # Set window icon first
            try:
                icon_path = settings.get_icon_path()
                if os.path.exists(icon_path):
                    self.setWindowIcon(QIcon(icon_path))
            except Exception:
                pass
            
            # Get smart window dimensions
            width, height, x, y = settings.get_window_dimensions()
            
            # Set window size and position
            self.setGeometry(x, y, width, height)
            
            # Set minimum size constraints
            screen = QApplication.primaryScreen()
            if screen:
                screen_rect = screen.availableGeometry()
                # Dynamic minimum size based on screen
                min_width = max(MIN_WINDOW_SIZE[0], int(screen_rect.width() * 0.4))
                min_height = max(MIN_WINDOW_SIZE[1], int(screen_rect.height() * 0.4))
                self.setMinimumSize(min_width, min_height)
                
                self.logger.info(f"Smart window setup: {width}x{height} at ({x}, {y}), min: {min_width}x{min_height}")
            else:
                self.setMinimumSize(*MIN_WINDOW_SIZE)
                self.logger.warning("Could not detect screen, using default minimum size")
                
        except Exception as e:
            self.logger.error(f"Smart window setup failed: {e}")
            # Fallback to safe defaults
            self.setMinimumSize(*MIN_WINDOW_SIZE)
            self.resize(*DEFAULT_WINDOW_SIZE)
    
    def create_header(self, parent_layout):
        """Create modern header section"""
        header_frame = QFrame()
        header_frame.setFixedHeight(80)
        header_frame.setObjectName("headerFrame")
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        # Left side - Title and version
        title_layout = QHBoxLayout()
        
        # App title
        title_label = QLabel("ContextLLM")
        title_label.setObjectName("titleLabel")
        title_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title_layout.addWidget(title_label)
        
        # Pro badge
        pro_badge = QLabel("PRO")
        pro_badge.setObjectName("proBadge")
        pro_badge.setFixedSize(40, 24)
        pro_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pro_badge.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        title_layout.addWidget(pro_badge)
        
        # Version
        version_label = QLabel("v3.0")
        version_label.setObjectName("versionLabel")
        version_label.setFont(QFont("Segoe UI", 11))
        title_layout.addWidget(version_label)
        
        title_layout.addStretch()
        
        # Right side - Controls
        controls_layout = QHBoxLayout()
        
        # File and token stats (moved from status bar)
        self.files_label = QLabel("📁 0 files")
        self.files_label.setObjectName("statsLabel")
        self.files_label.setFont(QFont("Segoe UI", 11))
        controls_layout.addWidget(self.files_label)
        
        controls_layout.addWidget(QLabel("|"))
        
        self.tokens_label = QLabel("🔢 0 tokens")
        self.tokens_label.setObjectName("statsLabel")
        self.tokens_label.setFont(QFont("Segoe UI", 11))
        controls_layout.addWidget(self.tokens_label)
        
        controls_layout.addWidget(QLabel("|"))
        
        # GitHub status
        self.github_status_label = QLabel("⚡ GitHub Ready")
        self.github_status_label.setObjectName("githubStatus")
        self.github_status_label.setFont(QFont("Segoe UI", 11))
        controls_layout.addWidget(self.github_status_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_layout.addLayout(controls_layout)
        
        parent_layout.addWidget(header_frame)
        
    def create_main_content(self, parent_layout):
        """Create main content area with splitter"""
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        
        # Left panel - Controls
        self.create_left_panel(splitter)
        
        # Right panel - Content
        self.create_content_panel(splitter)
        
        # Set splitter sizes (30% left, 70% right)
        splitter.setSizes([420, 980])
        
        parent_layout.addWidget(splitter, 1)
        
    def create_left_panel(self, parent_splitter):
        """Create left control panel"""
        left_panel = QWidget()
        left_panel.setObjectName("leftPanel")
        left_panel.setMinimumWidth(400)
        left_panel.setMaximumWidth(500)
        
        layout = QVBoxLayout(left_panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(25)  # Increased from 20 to prevent section overlap
        scroll_layout.setContentsMargins(10, 10, 10, 20)  # Add margins around content
        
        # Source selection section
        self.create_source_section(scroll_layout)
        
        # Model selection section
        self.create_model_section(scroll_layout)
        
        # File extensions section
        self.create_extensions_section(scroll_layout)
        
        # Settings section
        self.create_settings_section(scroll_layout)
        
        # Templates section
        self.create_templates_section(scroll_layout)
        
        # Actions section
        self.create_actions_section(scroll_layout)
        
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        parent_splitter.addWidget(left_panel)
        
    def create_source_section(self, parent_layout):
        """Create source selection section"""
        group = QGroupBox("📁 Source Selection")
        group.setObjectName("sourceGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(15)  # Increased from default to prevent overlap
        layout.setContentsMargins(15, 20, 15, 15)  # Add more top margin
        
        # Local folder button
        self.select_folder_btn = QPushButton("📂 Select Local Folder")
        self.select_folder_btn.setObjectName("primaryBtn")
        self.select_folder_btn.setMinimumHeight(44)
        self.select_folder_btn.clicked.connect(self.select_folder)
        layout.addWidget(self.select_folder_btn)
        
        # Add spacing between local and GitHub sections
        layout.addSpacing(10)
        
        # GitHub section
        github_frame = QFrame()
        github_frame.setObjectName("githubFrame")
        github_layout = QVBoxLayout(github_frame)
        github_layout.setSpacing(12)  # Increased spacing between GitHub elements
        github_layout.setContentsMargins(12, 12, 12, 12)  # Add padding inside frame
        
        # GitHub URL input with proper spacing
        github_url_label = QLabel("🐙 GitHub Repository URL:")
        github_layout.addWidget(github_url_label)
        github_layout.addSpacing(5)  # Small gap after label
        
        self.github_url_entry = QLineEdit()
        self.github_url_entry.setPlaceholderText("https://github.com/username/repository")
        self.github_url_entry.setMinimumHeight(36)
        github_layout.addWidget(self.github_url_entry)
        
        github_layout.addSpacing(8)  # Gap before controls
        
        # GitHub controls
        github_controls = QHBoxLayout()
        github_controls.setSpacing(8)  # Space between branch input and button
        
        self.github_branch_entry = QLineEdit()
        self.github_branch_entry.setPlaceholderText("main")
        self.github_branch_entry.setMaximumWidth(90)
        github_controls.addWidget(self.github_branch_entry)
        
        self.load_github_btn = QPushButton("📥 Load Repo")
        self.load_github_btn.setObjectName("successBtn")
        self.load_github_btn.setMinimumHeight(32)
        self.load_github_btn.clicked.connect(self.load_github_repository)
        github_controls.addWidget(self.load_github_btn)
        
        github_layout.addLayout(github_controls)
        
        github_layout.addSpacing(8)  # Gap before rate limit status
        
        # Rate limit status
        self.rate_limit_label = QLabel("👤 Anonymous: Ready")
        self.rate_limit_label.setObjectName("statusText")
        github_layout.addWidget(self.rate_limit_label)
        
        layout.addWidget(github_frame)
        
        # Add spacing between GitHub and exclude patterns
        layout.addSpacing(12)
        
        # Exclude patterns with proper spacing
        exclude_label = QLabel("Exclude Patterns (comma-separated):")
        layout.addWidget(exclude_label)
        layout.addSpacing(5)  # Small gap after label
        
        self.exclude_entry = QLineEdit()
        self.exclude_entry.setPlaceholderText("e.g., node_modules, .git, __pycache__")
        self.exclude_entry.setText("node_modules, .git, __pycache__, .vscode")
        self.exclude_entry.setMinimumHeight(36)  # Ensure consistent height
        layout.addWidget(self.exclude_entry)
        
        parent_layout.addWidget(group)
        
    def create_model_section(self, parent_layout):
        """Create model selection section"""
        group = QGroupBox("🤖 Estimated Token Model Selection")
        group.setObjectName("modelGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)  # Add spacing between elements
        layout.setContentsMargins(15, 20, 15, 15)  # Add margins for better layout
        
        self.model_dropdown = QComboBox()
        self.model_dropdown.addItems([
            # Latest 2025 AI Models (Premium)
            "claude-4-sonnet", "claude-3-7-sonnet", "gpt-4.5", "gpt-o3-pro",
            
            # High Performance Models
            "gpt-4o", "gpt-4-turbo", "claude-3-5-sonnet", "gemini-2-5-pro",
            
            # Fast & Efficient Models  
            "gpt-o4-mini", "gemini-2-5-flash", "grok-3", "grok-3-mini", 
            "deepseek-r1", "gemini-2-0-flash",
            
            # Specialized Models
            "gpt-o3", "gpt-3.5-turbo", "gpt-4.1"
        ])
        self.model_dropdown.setCurrentText(DEFAULT_MODEL)
        self.model_dropdown.currentTextChanged.connect(self.on_model_change)
        self.model_dropdown.setMinimumHeight(36)
        layout.addWidget(self.model_dropdown)
        
        parent_layout.addWidget(group)
        
    def create_extensions_section(self, parent_layout):
        """Create file extensions section"""
        group = QGroupBox("📄 File Extensions")
        group.setObjectName("extensionsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)  # Add spacing between elements
        layout.setContentsMargins(15, 20, 15, 15)  # Add margins for better layout
        
        # Toggle all button
        self.toggle_all_btn = QPushButton("Toggle All")
        self.toggle_all_btn.setEnabled(False)
        self.toggle_all_btn.setMinimumHeight(32)  # Consistent button height
        self.toggle_all_btn.clicked.connect(self.toggle_all_extensions)
        layout.addWidget(self.toggle_all_btn)
        
        layout.addSpacing(8)  # Gap before scroll area
        
        # Scroll area for checkboxes
        self.extensions_scroll = QScrollArea()
        self.extensions_scroll.setMinimumHeight(200)
        self.extensions_scroll.setMaximumHeight(300)
        self.extensions_scroll.setWidgetResizable(True)
        
        self.extensions_widget = QWidget()
        self.extensions_layout = QVBoxLayout(self.extensions_widget)
        self.extensions_layout.setSpacing(6)  # Space between checkboxes
        self.extensions_scroll.setWidget(self.extensions_widget)
        
        layout.addWidget(self.extensions_scroll)
        
        parent_layout.addWidget(group)
        
    def create_settings_section(self, parent_layout):
        """Create settings section"""
        group = QGroupBox("⚙️ Settings")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)  # Add spacing between elements
        layout.setContentsMargins(15, 20, 15, 15)  # Add margins for better layout
        
        # Comment removal checkbox
        self.comment_removal_checkbox = QCheckBox("Remove Comments & Docstrings")
        self.comment_removal_checkbox.toggled.connect(self.toggle_comment_removal)
        layout.addWidget(self.comment_removal_checkbox)
        
        layout.addSpacing(6)  # Gap before info label
        
        # Info label
        info_label = QLabel("💡 Removes comments, docstrings from code files")
        info_label.setObjectName("infoText")
        layout.addWidget(info_label)
        
        parent_layout.addWidget(group)
        
    def create_templates_section(self, parent_layout):
        """Create enhanced templates section with sections"""
        group = QGroupBox("📝 Expert Prompt Templates")
        group.setObjectName("templatesGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)  # Add spacing between elements
        layout.setContentsMargins(15, 20, 15, 15)  # Add margins for better layout
        
        # Section selector
        section_label = QLabel("Category:")
        layout.addWidget(section_label)
        layout.addSpacing(5)  # Small gap after label
        
        self.section_dropdown = QComboBox()
        self.section_dropdown.setMinimumHeight(36)  # Consistent height
        self.section_dropdown.currentTextChanged.connect(self.on_section_select)
        layout.addWidget(self.section_dropdown)
        
        layout.addSpacing(8)  # Gap between dropdowns
        
        # Template selector
        template_label = QLabel("Template:")
        layout.addWidget(template_label)
        layout.addSpacing(5)  # Small gap after label
        
        self.template_dropdown = QComboBox()
        self.template_dropdown.setMinimumHeight(36)  # Consistent height
        self.template_dropdown.currentTextChanged.connect(self.on_template_select)
        layout.addWidget(self.template_dropdown)
        
        layout.addSpacing(8)  # Gap before description
        
        # Template description
        self.template_description = QLabel("")
        self.template_description.setWordWrap(True)
        self.template_description.setObjectName("templateDescription")
        self.template_description.setMaximumHeight(50)  # Increased height slightly
        layout.addWidget(self.template_description)
        
        # Update dropdowns
        self.update_template_dropdowns()
        
        layout.addSpacing(10)  # Gap before buttons
        
        # Template buttons
        template_buttons = QHBoxLayout()
        template_buttons.setSpacing(8)  # Space between buttons
        
        apply_btn = QPushButton("✨ Apply Template")
        apply_btn.setMinimumHeight(32)  # Consistent button height
        apply_btn.clicked.connect(self.apply_template)
        template_buttons.addWidget(apply_btn)
        
        manage_btn = QPushButton("🛠️ Manage")
        manage_btn.setMinimumHeight(32)  # Consistent button height
        manage_btn.clicked.connect(self.show_template_manager)
        template_buttons.addWidget(manage_btn)
        
        layout.addLayout(template_buttons)
        
        parent_layout.addWidget(group)
        
    def create_actions_section(self, parent_layout):
        """Create actions section"""
        group = QGroupBox("🚀 Actions")
        group.setObjectName("actionsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)  # Add spacing between elements
        layout.setContentsMargins(15, 20, 15, 15)  # Add margins for better layout
        
        # Action buttons
        action_buttons = QHBoxLayout()
        action_buttons.setSpacing(8)  # Space between buttons
        
        self.save_btn = QPushButton("💾 Save")
        self.save_btn.setMinimumHeight(32)  # Consistent button height
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_content_as_file)
        action_buttons.addWidget(self.save_btn)
        
        self.copy_btn = QPushButton("📋 Copy")
        self.copy_btn.setMinimumHeight(32)  # Consistent button height
        self.copy_btn.setEnabled(False)
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        action_buttons.addWidget(self.copy_btn)
        
        layout.addLayout(action_buttons)
        
        layout.addSpacing(8)  # Gap before utility buttons
        
        # Utility buttons
        utility_buttons = QHBoxLayout()
        utility_buttons.setSpacing(8)  # Space between buttons
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setMinimumHeight(32)  # Consistent button height
        self.refresh_btn.clicked.connect(self.refresh_current_folder)
        utility_buttons.addWidget(self.refresh_btn)
        
        self.tree_btn = QPushButton("🌳 Tree View")
        self.tree_btn.setMinimumHeight(32)  # Consistent button height
        self.tree_btn.setEnabled(False)
        self.tree_btn.clicked.connect(self.show_tree_view)
        utility_buttons.addWidget(self.tree_btn)
        
        layout.addLayout(utility_buttons)
        
        parent_layout.addWidget(group)
        
    def create_content_panel(self, parent_splitter):
        """Create main content panel with tabs"""
        content_widget = QWidget()
        content_widget.setObjectName("contentPanel")
        
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("mainTabs")
        
        # Content tab
        content_tab = QWidget()
        content_layout = QVBoxLayout(content_tab)
        
        # Content header with colorful toolbar
        content_header_layout = QHBoxLayout()
        
        content_header = QLabel("📄 Aggregated Content")
        content_header.setObjectName("contentHeader")
        content_header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        content_header_layout.addWidget(content_header)
        
        content_header_layout.addStretch()
        
        # Colorful Toolbar with multiple buttons
        toolbar_frame = QFrame()
        toolbar_frame.setObjectName("colorfulToolbar")
        toolbar_frame.setFixedHeight(50)
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setSpacing(8)
        toolbar_layout.setContentsMargins(15, 8, 15, 8)
        
        # Reset button (moved from actions section)
        self.toolbar_process_btn = QPushButton("🔄 Reset")
        self.toolbar_process_btn.setObjectName("toolbarProcessBtn")
        self.toolbar_process_btn.setMinimumWidth(90)
        self.toolbar_process_btn.setMinimumHeight(32)
        self.toolbar_process_btn.setEnabled(False)
        self.toolbar_process_btn.clicked.connect(self.process_files)
        toolbar_layout.addWidget(self.toolbar_process_btn)
        
        # Copy button
        self.content_copy_btn = QPushButton("📋 Copy")
        self.content_copy_btn.setObjectName("toolbarCopyBtn")
        self.content_copy_btn.setToolTip("Copy content to clipboard")
        self.content_copy_btn.clicked.connect(self.copy_to_clipboard)
        self.content_copy_btn.setMinimumWidth(80)
        self.content_copy_btn.setMinimumHeight(32)
        self.content_copy_btn.setEnabled(False)
        toolbar_layout.addWidget(self.content_copy_btn)
        
        # Save button
        self.toolbar_save_btn = QPushButton("💾 Save")
        self.toolbar_save_btn.setObjectName("toolbarSaveBtn")
        self.toolbar_save_btn.setToolTip("Save content to file")
        self.toolbar_save_btn.clicked.connect(self.save_content_as_file)
        self.toolbar_save_btn.setMinimumWidth(80)
        self.toolbar_save_btn.setMinimumHeight(32)
        self.toolbar_save_btn.setEnabled(False)
        toolbar_layout.addWidget(self.toolbar_save_btn)
        
        # Tree View button
        self.toolbar_tree_btn = QPushButton("🌳 Tree")
        self.toolbar_tree_btn.setObjectName("toolbarTreeBtn")
        self.toolbar_tree_btn.setToolTip("Open tree view")
        self.toolbar_tree_btn.clicked.connect(self.show_tree_view)
        self.toolbar_tree_btn.setMinimumWidth(80)
        self.toolbar_tree_btn.setMinimumHeight(32)
        self.toolbar_tree_btn.setEnabled(False)
        toolbar_layout.addWidget(self.toolbar_tree_btn)
        
        content_header_layout.addWidget(toolbar_frame)
        
        content_layout.addLayout(content_header_layout)
        
        # Content text area
        self.content_textbox = QTextEdit()
        self.content_textbox.setObjectName("contentTextbox")
        self.content_textbox.setFont(QFont("Consolas", 12))
        self.content_textbox.setPlainText("Select a folder and process files to see aggregated content here...")
        
        # Connect textbox changes to sync internal state
        self.content_textbox.textChanged.connect(self.sync_content_state)
        
        content_layout.addWidget(self.content_textbox)
        
        self.tab_widget.addTab(content_tab, "📄 Content")
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setObjectName("progressBar")
        
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.tab_widget)
        
        parent_splitter.addWidget(content_widget)
        
    def create_status_bar(self):
        """Create simplified status bar"""
        status_bar = QStatusBar()
        status_bar.setObjectName("statusBar")
        
        # Status messages
        self.status_message_label = QLabel("Ready to process files...")
        self.status_message_label.setObjectName("statusMessage")
        status_bar.addWidget(self.status_message_label)
        
        # Cost estimate (moved to right side)
        self.cost_label = QLabel("💰 $0.000")
        self.cost_label.setObjectName("costLabel")
        status_bar.addPermanentWidget(self.cost_label)
        
        self.setStatusBar(status_bar)
        
    def create_menu_bar(self):
        """Create enhanced menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("📁 File")
        
        # Source selection
        open_folder_action = QAction("📂 Open Folder...", self)
        open_folder_action.setShortcut("Ctrl+O")
        open_folder_action.triggered.connect(self.select_folder)
        file_menu.addAction(open_folder_action)
        
        file_menu.addSeparator()
        
        # Reset Files - moved from actions section
        self.process_files_action = QAction("🔄 Reset Files", self)
        self.process_files_action.setShortcut("Ctrl+Return")
        self.process_files_action.setEnabled(False)
        self.process_files_action.triggered.connect(self.process_files)
        file_menu.addAction(self.process_files_action)
        
        file_menu.addSeparator()
        
        # Export options
        save_action = QAction("💾 Save Content...", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_content_as_file)
        file_menu.addAction(save_action)
        
        copy_action = QAction("📋 Copy to Clipboard", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy_to_clipboard)
        file_menu.addAction(copy_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("❌ Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("👁️ View")
        
        tree_action = QAction("🌳 Tree View", self)
        tree_action.setShortcut("Ctrl+T")
        tree_action.triggered.connect(self.show_tree_view)
        view_menu.addAction(tree_action)
        
        template_action = QAction("📝 Template Manager", self)
        template_action.triggered.connect(self.show_template_manager)
        view_menu.addAction(template_action)
        
        view_menu.addSeparator()
        
        refresh_action = QAction("🔄 Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_current_folder)
        view_menu.addAction(refresh_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("🔧 Tools")
        
        settings_action = QAction("⚙️ Settings", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # Help menu
        help_menu = menubar.addMenu("❓ Help")
        
        about_action = QAction("ℹ️ About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # File operations
        QShortcut(QKeySequence("Ctrl+O"), self, self.select_folder)
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_content_as_file)
        QShortcut(QKeySequence("Ctrl+C"), self, self.copy_to_clipboard)
        QShortcut(QKeySequence("F5"), self, self.refresh_current_folder)
        
        # Processing
        QShortcut(QKeySequence("Ctrl+Return"), self, self.process_files)
        QShortcut(QKeySequence("Ctrl+Enter"), self, self.process_files)
        
        # View
        QShortcut(QKeySequence("Ctrl+T"), self, self.show_tree_view)
        
        # Application
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)
        QShortcut(QKeySequence("F1"), self, self.show_about)
    
    def setup_tooltips(self):
        """Setup tooltips for UI elements"""
        # Left panel buttons
        self.select_folder_btn.setToolTip("Select a local folder to process (Ctrl+O)")
        self.load_github_btn.setToolTip("Load files from GitHub repository")
        
        # Left panel buttons (if they exist)
        if hasattr(self, 'save_btn'):
            self.save_btn.setToolTip("Save aggregated content to file (Ctrl+S)")
        if hasattr(self, 'copy_btn'):
            self.copy_btn.setToolTip("Copy content to clipboard (Ctrl+C)")
        if hasattr(self, 'refresh_btn'):
            self.refresh_btn.setToolTip("Refresh current source (F5)")
        if hasattr(self, 'tree_btn'):
            self.tree_btn.setToolTip("Show detailed file tree view (Ctrl+T)")
        
        # Toolbar buttons (new)
        if hasattr(self, 'toolbar_process_btn'):
            self.toolbar_process_btn.setToolTip("Reset selected files (Ctrl+Enter)")
        if hasattr(self, 'toolbar_save_btn'):
            self.toolbar_save_btn.setToolTip("Save aggregated content to file (Ctrl+S)")
        if hasattr(self, 'toolbar_tree_btn'):
            self.toolbar_tree_btn.setToolTip("Show detailed file tree view (Ctrl+T)")
        if hasattr(self, 'content_copy_btn'):
            self.content_copy_btn.setToolTip("Copy content to clipboard (Ctrl+C)")
        
        # Dropdowns and inputs
        self.model_dropdown.setToolTip("Select AI model for cost estimation")
        self.comment_removal_checkbox.setToolTip("Remove comments and docstrings from code files")
        self.template_dropdown.setToolTip("Choose a prompt template to apply")
        
        self.github_url_entry.setToolTip("Enter GitHub repository URL (e.g., https://github.com/user/repo)")
        self.github_branch_entry.setToolTip("Specify branch name (default: main)")
        self.exclude_entry.setToolTip("Comma-separated patterns to exclude from processing")
        
    def force_light_palette(self):
        """Force light color palette to override Windows dark mode"""
        from PyQt6.QtGui import QPalette, QColor
        from PyQt6.QtCore import Qt
        
        try:
            palette = QPalette()
            colors = settings.get_theme_colors()
            
            # Convert string colors to QColor objects
            bg_primary = QColor(colors['bg_primary'])
            bg_secondary = QColor(colors['bg_secondary'])
            text_primary = QColor(colors['text_primary'])
            primary_color = QColor(colors['primary'])
            
            # Set window colors
            palette.setColor(QPalette.ColorRole.Window, bg_primary)
            palette.setColor(QPalette.ColorRole.WindowText, text_primary)
            
            # Set base colors (for input fields)
            palette.setColor(QPalette.ColorRole.Base, bg_primary)
            palette.setColor(QPalette.ColorRole.AlternateBase, bg_secondary)
            
            # Set text colors
            palette.setColor(QPalette.ColorRole.Text, text_primary)
            palette.setColor(QPalette.ColorRole.BrightText, text_primary)
            
            # Set button colors
            palette.setColor(QPalette.ColorRole.Button, bg_secondary)
            palette.setColor(QPalette.ColorRole.ButtonText, text_primary)
            
            # Set highlight colors
            palette.setColor(QPalette.ColorRole.Highlight, primary_color)
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
            
            # Set disabled colors
            text_muted = QColor(colors['text_muted'])
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, text_muted)
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, text_muted)
            palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, text_muted)
            
            # Apply the palette to the application
            QApplication.instance().setPalette(palette)
            
            self.logger.info("✅ Successfully forced light palette to override Windows dark mode")
            
        except Exception as e:
            self.logger.error(f"Failed to force light palette: {e}")
            # Fallback - try to disable system theme detection
            try:
                QApplication.instance().setStyle("Fusion")
                self.logger.info("Applied Fusion style as fallback")
            except:
                pass
        
    def setup_styles(self):
        """Setup modern light theme styling using theme system"""
        colors = settings.get_theme_colors()
        
        # FORCE LIGHT PALETTE - Override Windows dark mode
        self.force_light_palette()
        
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {colors['bg_primary']};
                color: {colors['text_primary']};
            }}
            
            #headerFrame {{
                background-color: {colors['bg_secondary']};
                border-bottom: 1px solid {colors['border_primary']};
            }}
            
            #titleLabel {{
                color: {colors['text_primary']};
            }}
            
            #proBadge {{
                background-color: {colors['primary']};
                color: #ffffff;
                border-radius: 12px;
            }}
            
            #versionLabel, #githubStatus, #statusText, #infoText, #statsLabel {{
                color: {colors['text_secondary']};
            }}
            
            QGroupBox {{
                background-color: {colors['bg_tertiary']};
                border: 1px solid {colors['border_primary']};
                border-radius: 6px;
                margin: 10px 0;
                padding: 0 8px 0 8px;
                color: {colors['text_primary']};
            }}
            
            #primaryBtn {{
                background-color: {colors['primary']};
                border: none;
                color: #ffffff;
                padding: 12px;
                border-radius: 6px;
                font-weight: bold;
            }}
            
            #primaryBtn:hover {{
                background-color: {colors['bg_hover']};
            }}
            
            #primaryBtn:disabled {{
                background-color: {colors['border_muted']};
                color: {colors['text_muted']};
            }}
            
            #successBtn {{
                background-color: {colors['success']};
                border: none;
                color: #ffffff;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }}
            
            #successBtn:hover {{
                background-color: {colors['online']};
            }}
            
            QPushButton {{
                background-color: {colors['border_muted']};
                border: 1px solid {colors['border_primary']};
                color: {colors['text_primary']};
                padding: 8px 12px;
                border-radius: 4px;
            }}
            
            QPushButton:hover {{
                background-color: {colors['bg_hover']};
            }}
            
            QPushButton:disabled {{
                background-color: {colors['bg_secondary']};
                color: {colors['text_muted']};
            }}
            
            QLineEdit, QComboBox {{
                background-color: {colors['bg_primary']};
                border: 1px solid {colors['border_primary']};
                color: {colors['text_primary']};
                padding: 8px;
                border-radius: 4px;
            }}
            
            QLineEdit:focus, QComboBox:focus {{
                border-color: {colors['primary']};
            }}
            
            #contentTextbox {{
                background-color: {colors['bg_primary']};
                border: 1px solid {colors['border_primary']};
                color: {colors['text_primary']};
                selection-background-color: {colors['bg_hover']};
            }}
            
            #templateDescription {{
                color: {colors['text_secondary']};
                font-style: italic;
                padding: 4px;
                background-color: {colors['bg_secondary']};
                border-radius: 4px;
                border: 1px solid {colors['border_muted']};
            }}
            
            #contentHeader {{
                color: {colors['text_primary']};
                padding: 10px;
            }}
            
            QTabWidget::pane {{
                border: 1px solid {colors['border_primary']};
                background-color: {colors['bg_primary']};
            }}
            
            QTabBar::tab {{
                background-color: {colors['bg_secondary']};
                color: {colors['text_secondary']};
                padding: 8px 16px;
                border: 1px solid {colors['border_primary']};
                border-bottom: none;
            }}
            
            QTabBar::tab:selected {{
                background-color: {colors['bg_primary']};
                color: {colors['text_primary']};
            }}
            
            QTabBar::tab:hover {{
                background-color: {colors['bg_hover']};
            }}
            
            #statusBar {{
                background-color: {colors['bg_secondary']};
                border-top: 1px solid {colors['border_primary']};
                color: {colors['text_secondary']};
            }}
            
            #progressBar {{
                border: 1px solid {colors['border_primary']};
                border-radius: 4px;
                text-align: center;
                background-color: {colors['bg_primary']};
            }}
            
            #progressBar::chunk {{
                background-color: {colors['primary']};
                border-radius: 3px;
            }}
            
            QCheckBox {{
                color: {colors['text_primary']};
                spacing: 8px;
            }}
            
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {colors['border_primary']};
                border-radius: 3px;
                background-color: {colors['bg_primary']};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {colors['primary']};
                border-color: {colors['primary']};
            }}
            
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            
            QScrollBar:vertical {{
                background-color: {colors['bg_secondary']};
                width: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {colors['border_primary']};
                border-radius: 6px;
                min-height: 20px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {colors['text_muted']};
            }}
            
            #githubFrame {{
                background-color: {colors['bg_tertiary']};
                border: 1px solid {colors['border_primary']};
                border-radius: 6px;
                padding: 12px;
            }}
            
            QWidget {{
                font-family: "Segoe UI", "Calibri", "Arial", sans-serif;
            }}
            
            QMenuBar {{
                background-color: {colors['bg_secondary']};
                color: {colors['text_primary']};
                border-bottom: 1px solid {colors['border_primary']};
            }}
            
            QMenuBar::item {{
                background-color: transparent;
                padding: 6px 12px;
            }}
            
            QMenuBar::item:selected {{
                background-color: {colors['bg_hover']};
            }}
            
            QMenu {{
                background-color: {colors['bg_primary']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border_primary']};
            }}
            
            QMenu::item {{
                padding: 6px 12px;
            }}
            
            QMenu::item:selected {{
                background-color: {colors['bg_hover']};
            }}
            
            QToolTip {{
                background-color: {colors['bg_primary']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border_primary']};
                padding: 4px;
                border-radius: 4px;
            }}
            
            /* Colorful Toolbar Styling - Transparent Background */
            #colorfulToolbar {{
                background: transparent;
                border: none;
                border-radius: 0px;
                margin: 0px;
            }}
            
            /* Toolbar Button Styles */
            #toolbarProcessBtn {{
                background-color: rgba(255, 255, 255, 0.9);
                border: 2px solid #4CAF50;
                color: #2E7D32;
                font-weight: bold;
                border-radius: 16px;
                padding: 6px 12px;
            }}
            
            #toolbarProcessBtn:hover {{
                background-color: #4CAF50;
                color: white;
                transform: scale(1.05);
            }}
            
            #toolbarProcessBtn:disabled {{
                background-color: rgba(255, 255, 255, 0.5);
                border-color: #CCCCCC;
                color: #999999;
            }}
            
            #toolbarCopyBtn {{
                background-color: rgba(255, 255, 255, 0.9);
                border: 2px solid #2196F3;
                color: #1565C0;
                font-weight: bold;
                border-radius: 16px;
                padding: 6px 12px;
            }}
            
            #toolbarCopyBtn:hover {{
                background-color: #2196F3;
                color: white;
                transform: scale(1.05);
            }}
            
            #toolbarCopyBtn:disabled {{
                background-color: rgba(255, 255, 255, 0.5);
                border-color: #CCCCCC;
                color: #999999;
            }}
            
            #toolbarSaveBtn {{
                background-color: rgba(255, 255, 255, 0.9);
                border: 2px solid #FF9800;
                color: #E65100;
                font-weight: bold;
                border-radius: 16px;
                padding: 6px 12px;
            }}
            
            #toolbarSaveBtn:hover {{
                background-color: #FF9800;
                color: white;
                transform: scale(1.05);
            }}
            
            #toolbarSaveBtn:disabled {{
                background-color: rgba(255, 255, 255, 0.5);
                border-color: #CCCCCC;
                color: #999999;
            }}
            
            #toolbarTreeBtn {{
                background-color: rgba(255, 255, 255, 0.9);
                border: 2px solid #9C27B0;
                color: #7B1FA2;
                font-weight: bold;
                border-radius: 16px;
                padding: 6px 12px;
            }}
            
            #toolbarTreeBtn:hover {{
                background-color: #9C27B0;
                color: white;
                transform: scale(1.05);
            }}
            
            #toolbarTreeBtn:disabled {{
                background-color: rgba(255, 255, 255, 0.5);
                border-color: #CCCCCC;
                color: #999999;
            }}
        """)
        self.logger.info("Applied light theme styling using theme system")
    
    def select_folder(self):
        """Select folder dialog"""
        self.logger.info("User initiated folder selection")
        log_user_action("Select Folder", "Opening folder dialog")
        
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Process")
        if folder:
            self.selected_folder = folder
            self.current_source_type = "local"
            self.logger.info(f"Folder selected: {folder}")
            log_user_action("Folder Selected", f"Path: {folder}")
            self.scan_directory()
        else:
            self.logger.info("Folder selection cancelled by user")
    
    def scan_directory(self):
        """Scan selected directory for files"""
        if not self.selected_folder:
            return
        
        self.show_progress("Scanning directory...")
        
        exclude_text = self.exclude_entry.text()
        exclude_patterns = self.file_processor.get_exclude_patterns(exclude_text)
        
        self.scanning_thread = ScanningThread(
            self.file_processor, self.selected_folder, exclude_patterns
        )
        self.scanning_thread.scanning_finished.connect(self.on_scanning_finished)
        self.scanning_thread.scanning_error.connect(self.on_scanning_error)
        self.scanning_thread.start()
    
    def on_scanning_finished(self, extensions):
        """Handle scanning completion"""
        self.hide_progress()
        self.update_extensions_ui(extensions)
        self.update_button_states(has_files=True)
        self.show_status_message("Directory scanned successfully!", "success")
        
        # Auto-select important extensions
        self.auto_select_extensions(extensions)
    
    def on_scanning_error(self, error_msg):
        """Handle scanning error"""
        self.hide_progress()
        QMessageBox.warning(self, "Scanning Error", error_msg)
    
    def update_extensions_ui(self, extensions: Set[str]):
        """Update extension checkboxes UI"""
        # Clear existing checkboxes
        for i in reversed(range(self.extensions_layout.count())):
            child = self.extensions_layout.itemAt(i).widget()
            if child:
                child.deleteLater()
        
        self.extension_checkboxes = {}
        
        if not extensions:
            label = QLabel("No files found with extensions")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.extensions_layout.addWidget(label)
            return
        
        # Create checkboxes for each extension
        for ext in sorted(extensions):
            checkbox = QCheckBox(f"{ext} files")
            checkbox.toggled.connect(self.on_extension_change)
            self.extensions_layout.addWidget(checkbox)
            self.extension_checkboxes[ext] = checkbox
        
        self.toggle_all_btn.setEnabled(True)
    
    def auto_select_extensions(self, extensions: Set[str]):
        """Auto-select important extensions"""
        important_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb', '.go', '.rs'}
        moderately_important = {'.html', '.css', '.scss', '.sass', '.less', '.json', '.xml', '.yaml', '.yml', '.sql'}
        
        auto_selected = set()
        
        # Always select important extensions
        for ext in important_extensions.intersection(extensions):
            if ext in self.extension_checkboxes:
                self.extension_checkboxes[ext].setChecked(True)
                auto_selected.add(ext)
        
        # Select moderately important if no important ones found
        if not auto_selected:
            for ext in moderately_important.intersection(extensions):
                if ext in self.extension_checkboxes:
                    self.extension_checkboxes[ext].setChecked(True)
                    auto_selected.add(ext)
        
        if auto_selected:
            selected_names = ", ".join(auto_selected)
            self.show_status_message(f"🎯 Auto-selected: {selected_names}", "info")
            
            # Auto-process after delay
            QTimer.singleShot(2000, self.auto_process_files)
    
    def auto_process_files(self):
        """Auto-process files if conditions are met"""
        selected_extensions = self.get_selected_extensions()
        if selected_extensions and self.selected_folder:
            self.show_status_message("🚀 Auto-processing selected file types...", "info")
            QTimer.singleShot(1000, self.process_files)
    
    def process_files(self):
        """Process selected files"""
        import time
        start_time = time.time()
        self.logger.info("User initiated file processing")
        
        if not self.selected_folder:
            self.logger.warning("Process files called without folder selection")
            QMessageBox.warning(self, "Warning", "No folder selected.")
            return
        
        selected_extensions = self.get_selected_extensions()
        if not selected_extensions:
            self.logger.warning("Process files called without extension selection")
            QMessageBox.warning(self, "Warning", "No file extensions selected.")
            return
        
        # Log processing details
        ext_list = ", ".join(selected_extensions)
        comment_removal = self.comment_removal_checkbox.isChecked()
        source_type = self.current_source_type
        
        log_user_action("Process Files", f"Extensions: {ext_list}, Comments: {comment_removal}, Source: {source_type}")
        self.logger.info(f"Starting file processing - Extensions: {ext_list}, Comment removal: {comment_removal}")
        
        # Debug: Log how many files match selected extensions
        matching_files = [f for f in self.file_processor.all_files if f['extension'] in selected_extensions]
        self.logger.info(f"Found {len(matching_files)} files matching selected extensions: {ext_list}")
        
        # Store start time for duration calculation
        self._processing_start_time = start_time
        
        self.show_progress("Processing files...")
        
        # Set comment removal setting
        self.file_processor.set_comment_removal(comment_removal)
        
        # Process in thread
        github_proc = self.github_processor if self.current_source_type == "github" else None
        
        self.processing_thread = ProcessingThread(
            self.file_processor, selected_extensions, github_proc
        )
        self.processing_thread.progress_updated.connect(self.update_progress)
        self.processing_thread.processing_finished.connect(self.on_processing_finished)
        self.processing_thread.processing_error.connect(self.on_processing_error)
        self.processing_thread.start()
    
    def on_processing_finished(self, content, processed_files):
        """Handle processing completion"""
        self.hide_progress()
        self.aggregated_content = content
        # Store original content for template application
        self.original_aggregated_content = content
        
        # Calculate processing time if available
        processing_time = "unknown"
        if hasattr(self, '_processing_start_time'):
            import time
            duration = time.time() - self._processing_start_time
            processing_time = f"{duration:.2f}s"
        
        # Log completion details
        file_count = len(processed_files)
        content_length = len(content)
        
        # Check for error files and show detailed warning
        error_files = getattr(self.file_processor, 'error_files', [])
        if error_files:
            self.logger.warning(f"{len(error_files)} files had errors during processing:")
            for error_file in error_files[:5]:  # Log first 5 errors
                self.logger.warning(f"  {error_file['path']}: {error_file['error']}")
            if len(error_files) > 5:
                self.logger.warning(f"  ... and {len(error_files) - 5} more errors")
            
            # Show detailed warning popup
            self.show_file_errors_dialog(error_files, file_count)
        
        self.logger.info(f"File processing completed in {processing_time} - {file_count} files processed, {content_length} characters generated")
        log_user_action("Processing Completed", f"Files: {file_count}, Content size: {content_length} chars, Time: {processing_time}")
        
        self.update_content_display()
        self.show_status_message("Processing complete!", "success")
    
    def on_processing_error(self, error_msg):
        """Handle processing error"""
        self.hide_progress()
        self.logger.error(f"File processing failed: {error_msg}")
        log_user_action("Processing Failed", f"Error: {error_msg}")
        QMessageBox.critical(self, "Processing Error", error_msg)
    
    def update_content_display(self):
        """Update content display and statistics"""
        # Update content textbox
        self.content_textbox.setPlainText(self.aggregated_content)
        
        # Calculate statistics
        token_count = token_utils.calculate_tokens(self.aggregated_content, self.selected_model)
        cost, _ = token_utils.calculate_cost_estimation(token_count, self.selected_model)
        file_count = len(self.file_processor.get_processed_files())
        
        # Update status bar
        self.files_label.setText(f"📁 {file_count} files")
        self.tokens_label.setText(f"🔢 {token_count:,} tokens")
        formatted_cost = token_utils.format_cost(cost)
        self.cost_label.setText(f"💰 {formatted_cost}")
        
        # Update button states
        self.update_button_states(has_files=True, has_content=True)
    
    def sync_content_state(self):
        """Sync internal content state with textbox content"""
        current_content = self.content_textbox.toPlainText()
        
        # Only sync if content is meaningful (not the placeholder text)
        if current_content and current_content.strip() != "Select a folder and process files to see aggregated content here...":
            self.aggregated_content = current_content
    
    def get_selected_extensions(self) -> Set[str]:
        """Get selected file extensions"""
        selected = set()
        for ext, checkbox in self.extension_checkboxes.items():
            if checkbox.isChecked():
                selected.add(ext)
        return selected
    
    def toggle_all_extensions(self):
        """Toggle all extension checkboxes"""
        if not self.extension_checkboxes:
            return
        
        # Check if any are selected
        any_selected = any(cb.isChecked() for cb in self.extension_checkboxes.values())
        new_state = not any_selected
        
        for checkbox in self.extension_checkboxes.values():
            checkbox.setChecked(new_state)
    
    def on_extension_change(self):
        """Handle extension checkbox change"""
        selected_extensions = self.get_selected_extensions()
        self.update_button_states(has_files=bool(self.extension_checkboxes), has_content=False)
        
        # Auto-process if extensions are selected and folder is available
        if selected_extensions and self.selected_folder:
            self.process_files()
    
    def on_model_change(self, model_name: str):
        """Handle model selection change"""
        if validation_utils.validate_model_name(model_name):
            self.selected_model = model_name
            settings.set_model(model_name)
            
            # Recalculate cost if content exists
            if self.aggregated_content:
                self.update_content_display()
    
    
    def toggle_comment_removal(self):
        """Toggle comment removal setting and auto-reprocess if content exists"""
        settings.toggle_comment_removal()
        
        # Auto-reprocess if we have selected extensions and a folder
        selected_extensions = self.get_selected_extensions()
        if selected_extensions and self.selected_folder:
            self.process_files()
    
    def update_button_states(self, has_files: bool = False, has_content: bool = False):
        """Update button states"""
        # Traditional buttons in left panel (only if they exist)
        if hasattr(self, 'save_btn'):
            self.save_btn.setEnabled(has_content)
        if hasattr(self, 'copy_btn'):
            self.copy_btn.setEnabled(has_content)
        if hasattr(self, 'tree_btn'):
            self.tree_btn.setEnabled(has_files)
        
        # Toolbar buttons in content panel
        if hasattr(self, 'toolbar_process_btn'):
            self.toolbar_process_btn.setEnabled(has_files)
        if hasattr(self, 'toolbar_save_btn'):
            self.toolbar_save_btn.setEnabled(has_content)
        if hasattr(self, 'toolbar_tree_btn'):
            self.toolbar_tree_btn.setEnabled(has_files)
        if hasattr(self, 'content_copy_btn'):
            self.content_copy_btn.setEnabled(has_content)
        
        # Menu actions
        if hasattr(self, 'process_files_action'):
            self.process_files_action.setEnabled(has_files)
    
    def save_content_as_file(self):
        """Save content to file"""
        # Get current content from textbox (always up-to-date)
        current_content = self.content_textbox.toPlainText()
        
        if not current_content or current_content.strip() == "Select a folder and process files to see aggregated content here...":
            self.logger.warning("Save attempted with no content")
            QMessageBox.warning(self, "Warning", "No content to save.")
            return
        
        # Update internal state to match current display
        self.aggregated_content = current_content
        
        content_size = len(current_content)
        self.logger.info(f"User initiated save - Content size: {content_size} characters")
        log_user_action("Save Content", f"Size: {content_size} chars")
        
        success = file_utils.save_content_to_file(current_content, self)
        if success:
            self.logger.info("Content saved successfully")
            self.show_status_message("✅ File saved successfully!", "success")
            self.animate_button_feedback(self.save_btn, "💾 Save", "✅ Saved!")
        else:
            self.logger.warning("Content save failed or cancelled")
    
    def copy_to_clipboard(self):
        """Copy content to clipboard"""
        # Get current content from textbox (always up-to-date)
        current_content = self.content_textbox.toPlainText()
        
        if not current_content or current_content.strip() == "Select a folder and process files to see aggregated content here...":
            self.logger.warning("Copy attempted with no content")
            QMessageBox.warning(self, "Warning", "No content to copy.")
            return
        
        # Update internal state to match current display
        self.aggregated_content = current_content
        
        content_size = len(current_content)
        self.logger.info(f"User copied content to clipboard - Size: {content_size} characters")
        log_user_action("Copy to Clipboard", f"Size: {content_size} chars")
        
        clipboard = QApplication.clipboard()
        clipboard.setText(current_content)
        self.show_status_message("✅ Content copied to clipboard!", "success")
        self.animate_button_feedback(self.copy_btn, "📋 Copy", "✅ Copied!")
    
    def refresh_current_folder(self):
        """Refresh current folder"""
        if self.current_source_type == "local" and self.selected_folder:
            self.aggregated_content = ""
            self.file_processor.all_files = []
            self.file_processor.file_extensions = set()
            self.clear_content()
            self.scan_directory()
        elif self.current_source_type == "github" and self.current_github_info:
            self.load_github_repository()
        else:
            QMessageBox.warning(self, "Warning", "No source selected to refresh.")
    
    def clear_content(self):
        """Clear content display"""
        self.content_textbox.setPlainText("Select a folder and process files to see aggregated content here...")
        self.files_label.setText("📁 0 files")
        self.tokens_label.setText("🔢 0 tokens")
        self.cost_label.setText("💰 $0.000")
        
        # Clear extension checkboxes
        for i in reversed(range(self.extensions_layout.count())):
            child = self.extensions_layout.itemAt(i).widget()
            if child:
                child.deleteLater()
        self.extension_checkboxes = {}
        self.toggle_all_btn.setEnabled(False)
        
        self.update_button_states(has_files=False, has_content=False)
    
    # GitHub methods
    def load_github_repository(self):
        """Load GitHub repository"""
        github_url = self.github_url_entry.text().strip()
        if not github_url:
            QMessageBox.warning(self, "Warning", "Please enter a GitHub repository URL.")
            return
        
        # Parse GitHub URL
        repo_info = self.github_processor.parse_github_url(github_url)
        if not repo_info:
            QMessageBox.critical(self, "Error", "Invalid GitHub URL format.")
            return
        
        # Get branch from input (default to main)
        branch = self.github_branch_entry.text().strip()
        if not branch:
            branch = "main"
        
        repo_info['branch'] = branch
        
        # Update rate limit status
        self.update_rate_limit_status()
        
        # Show progress
        self.show_progress("Loading GitHub repository...")
        
        # Load in thread
        self.github_thread = GitHubThread(self.github_processor, repo_info)
        self.github_thread.github_loaded.connect(self.on_github_loaded)
        self.github_thread.github_error.connect(self.on_github_error)
        self.github_thread.start()
    
    def update_rate_limit_status(self):
        """Update rate limit status in UI"""
        status = self.github_processor.get_rate_limit_status()
        self.rate_limit_label.setText(status)
    
    def on_github_loaded(self, files_list, extensions, status_message):
        """Handle GitHub repository loaded"""
        self.hide_progress()
        
        # Update file processor with GitHub files
        self.file_processor.all_files = files_list
        self.file_processor.file_extensions = extensions
        
        # Store GitHub info
        self.current_github_info = self.github_thread.repo_info
        self.current_source_type = "github"
        self.selected_folder = f"GitHub: {self.current_github_info['owner']}/{self.current_github_info['repo']}:{self.current_github_info['branch']}"
        
        # Update UI
        self.update_extensions_ui(extensions)
        self.update_button_states(has_files=True)
        self.update_rate_limit_status()
        self.show_status_message(status_message, "success")
        
        # Auto-select extensions
        self.auto_select_extensions(extensions)
    
    def on_github_error(self, error_msg):
        """Handle GitHub loading error"""
        self.hide_progress()
        
        if "Rate limit exceeded" in error_msg:
            self.show_rate_limit_warning()
        else:
            QMessageBox.critical(self, "GitHub Error", error_msg)
    
    def show_rate_limit_warning(self):
        """Show rate limit warning to user"""
        import os
        
        status = self.github_processor.check_user_rate_limit()
        reset_time = status['reset_time']
        
        if self.github_processor.is_authenticated:
            # Authenticated user hit GitHub's limit
            QMessageBox.warning(
                self, "GitHub Rate Limit Exceeded",
                f"Your GitHub token's rate limit exceeded.\n\n"
                f"Rate limit will reset at: {reset_time}\n\n"
                f"Please wait before making new requests."
            )
        else:
            # Anonymous user hit our session limit
            has_token = bool(os.getenv('GITHUB_TOKEN', ''))
            
            if has_token:
                msg = (
                    f"Session limit exceeded ({self.github_processor.user_request_limit} requests).\n\n"
                    f"Session resets at: {reset_time}\n\n"
                    f"Note: You have GITHUB_TOKEN set but it may be invalid."
                )
            else:
                msg = (
                    f"Anonymous rate limit exceeded ({self.github_processor.user_request_limit} requests/hour).\n\n"
                    f"Rate limit resets at: {reset_time}\n\n"
                    f"💡 For unlimited access (5000 requests/hour):\n"
                    f"1. Get GitHub Personal Access Token\n"
                    f"2. Set GITHUB_TOKEN environment variable\n"
                    f"3. Restart application"
                )
            
            QMessageBox.warning(self, "Rate Limit Exceeded", msg)
        
        # Update status in UI
        self.update_rate_limit_status()
    
    # Template methods (simplified for now)
    def update_template_dropdowns(self):
        """Update both section and template dropdowns"""
        # Update section dropdown
        self.section_dropdown.clear()
        self.section_dropdown.addItem("Select Category...")
        
        sections = template_manager.get_all_sections()
        for section in sections:
            display_name = f"{section['name']} ({section['template_count']})"
            self.section_dropdown.addItem(display_name, section['id'])
        
        # Clear template dropdown initially
        self.template_dropdown.clear()
        self.template_dropdown.addItem("Select Template...")
        self.template_description.setText("")
    
    def on_section_select(self, section_display: str):
        """Handle section selection"""
        self.template_dropdown.clear()
        self.template_dropdown.addItem("Select Template...")
        self.template_description.setText("")
        self.current_template = None
        
        # Get section ID from combobox data
        section_id = self.section_dropdown.currentData()
        if not section_id:
            return
        
        # Load templates for selected section
        templates = template_manager.get_section_templates(section_id)
        for template in templates:
            self.template_dropdown.addItem(template['name'], (section_id, template['id']))
    
    def on_template_select(self, template_name: str):
        """Handle template selection"""
        if template_name == "Select Template...":
            self.current_template = None
            self.template_description.setText("")
            return
        
        # Get template data from combobox
        template_data = self.template_dropdown.currentData()
        if not template_data:
            return
        
        section_id, template_id = template_data
        template = template_manager.get_template(section_id, template_id)
        
        if template:
            self.current_template = template
            # Update description
            description = template.get('description', 'No description available.')
            self.template_description.setText(f"💡 {description}")
        else:
            self.current_template = None
            self.template_description.setText("")
    
    def apply_template(self):
        """Apply selected template to original content (replaces any previous template)"""
        if not self.current_template:
            QMessageBox.warning(self, "Warning", "No template selected.")
            return
        
        # Get original processed content (without any previously applied templates)
        original_content = getattr(self, 'original_aggregated_content', self.aggregated_content)
        
        if not original_content:
            QMessageBox.warning(self, "Warning", "No content available.")
            return
        
        template_text = self.current_template.get('template', '')
        combined_content = f"{template_text}\n\n{original_content}"
        
        self.content_textbox.setPlainText(combined_content)
        self.aggregated_content = combined_content
        self.update_content_display()
    
    def show_template_manager(self):
        """Show template management window"""
        from .template_manager import TemplateManagerDialog
        
        dialog = TemplateManagerDialog(self)
        if dialog.exec():
            # Refresh template dropdowns
            self.update_template_dropdowns()
            
            # If a template was selected, update the dropdown selection
            if hasattr(dialog, 'selected_template') and dialog.selected_template:
                template = dialog.selected_template
                section_id = template.get('section_id')
                template_name = template.get('name')
                
                # Select section first
                if section_id:
                    for i in range(self.section_dropdown.count()):
                        if self.section_dropdown.itemData(i) == section_id:
                            self.section_dropdown.setCurrentIndex(i)
                            break
                    
                    # Then select template
                    if template_name:
                        index = self.template_dropdown.findText(template_name)
                        if index >= 0:
                            self.template_dropdown.setCurrentIndex(index)
                            self.current_template = template
    
    def show_tree_view(self):
        """Show detailed tree view"""
        from .tree_view import TreeViewDialog
        
        if not self.file_processor.all_files:
            QMessageBox.warning(self, "Warning", "No files loaded. Please select a folder first.")
            return
        
        dialog = TreeViewDialog(self, self.file_processor.all_files)
        if dialog.exec():
            # Check if we have selected files for direct processing
            if hasattr(dialog, 'selected_file_info') and dialog.selected_file_info:
                self.logger.info(f"Tree view: Processing {len(dialog.selected_file_info)} selected files directly")
                log_user_action("Tree View Process", f"Files: {len(dialog.selected_file_info)}")
                
                # Process selected files directly
                self.process_selected_files_from_tree(dialog.selected_file_info)
            else:
                # Fallback: Apply extension selection to checkboxes
                selected_extensions = dialog.get_selected_extensions()
                
                # Update extension checkboxes in main interface
                for ext, checkbox in self.extension_checkboxes.items():
                    checkbox.setChecked(ext in selected_extensions)
                
                QMessageBox.information(self, "Success", 
                                      f"Applied selection: {len(selected_extensions)} extensions")
    
    def process_selected_files_from_tree(self, selected_files):
        """Process specific files selected from tree view"""
        import time
        start_time = time.time()
        
        try:
            self.logger.info(f"Processing {len(selected_files)} files selected from tree view")
            
            # Show progress
            self.show_progress(f"Processing {len(selected_files)} selected files...")
            
            # Store start time for duration calculation
            self._processing_start_time = start_time
            
            # Process files using the common method
            self.process_specific_files(selected_files)
            
        except Exception as e:
            self.hide_progress()
            self.logger.error(f"Tree view processing failed: {e}")
            log_error_with_context(e, "process_selected_files_from_tree")
            QMessageBox.critical(self, "Processing Error", f"Failed to process selected files: {str(e)}")
    
    def process_specific_files(self, selected_files):
        """Process specific files without extension filtering"""
        try:
            # Set comment removal setting on main processor
            self.file_processor.set_comment_removal(self.comment_removal_checkbox.isChecked())
            
            # Use main file processor with specific file list
            # Pass empty set for extensions since we're providing specific files
            content, processed_files = self.file_processor.aggregate_content(
                set(),  # Empty extensions set since we're providing specific files
                progress_callback=self.update_progress,
                github_processor=self.github_processor if self.current_source_type == "github" else None,
                files_to_process=selected_files
            )
            
            # Handle completion
            self.on_processing_finished(content, processed_files)
            
        except Exception as e:
            self.on_processing_error(str(e))
    
    # UI helper methods
    def show_progress(self, message="Processing..."):
        """Show progress bar"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.show_status_message(message, "info")
    
    def hide_progress(self):
        """Hide progress bar"""
        self.progress_bar.setVisible(False)
    
    def update_progress(self, value):
        """Update progress bar value"""
        if self.progress_bar.maximum() == 0:
            self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(int(value * 100))
    
    def show_status_message(self, message, msg_type="info"):
        """Show status message with animation"""
        self.status_message_label.setText(message)
        
        # Add color based on message type
        if msg_type == "success":
            self.status_message_label.setStyleSheet("color: #28a745; font-weight: bold;")
        elif msg_type == "error":
            self.status_message_label.setStyleSheet("color: #dc3545; font-weight: bold;")
        elif msg_type == "info":
            self.status_message_label.setStyleSheet("color: #007acc; font-weight: bold;")
        else:
            self.status_message_label.setStyleSheet("color: inherit;")
        
        # Auto-clear after delay
        QTimer.singleShot(3000, lambda: (
            self.status_message_label.setText("Ready"),
            self.status_message_label.setStyleSheet("color: inherit;")
        ))
    
    def animate_button_feedback(self, button, original_text, feedback_text, duration=2000):
        """Animate button feedback"""
        button.setText(feedback_text)
        button.setEnabled(False)
        
        QTimer.singleShot(duration, lambda: (
            button.setText(original_text),
            button.setEnabled(True)
        ))
    
    def show_file_errors_dialog(self, error_files, successful_count):
        """Show detailed file errors dialog"""
        total_errors = len(error_files)
        
        # Categorize errors
        binary_files = []
        encoding_files = []
        access_files = []
        other_files = []
        
        for error in error_files:
            error_msg = error['error'].lower()
            if 'binary' in error_msg or 'corrupted' in error_msg or 'invalid content' in error_msg:
                binary_files.append(error)
            elif 'encoding' in error_msg or 'unicode' in error_msg:
                encoding_files.append(error)
            elif 'access' in error_msg or 'permission' in error_msg:
                access_files.append(error)
            else:
                other_files.append(error)
        
        # Build detailed message
        title = f"⚠️ File Processing Warning"
        
        message = f"""
        <h3>Processing Summary:</h3>
        <p>✅ <strong>{successful_count} files processed successfully</strong><br>
        ❌ <strong>{total_errors} files had issues</strong></p>
        
        <h4>Issue Categories:</h4>
        """
        
        if binary_files:
            message += f"<p>📄 <strong>Binary/Corrupted Files ({len(binary_files)}):</strong><br>"
            for error in binary_files[:3]:
                message += f"• {error['path']}<br>"
            if len(binary_files) > 3:
                message += f"• ... and {len(binary_files) - 3} more<br>"
            message += "</p>"
        
        if encoding_files:
            message += f"<p>🔤 <strong>Encoding Issues ({len(encoding_files)}):</strong><br>"
            for error in encoding_files[:3]:
                message += f"• {error['path']}<br>"
            if len(encoding_files) > 3:
                message += f"• ... and {len(encoding_files) - 3} more<br>"
            message += "</p>"
        
        if access_files:
            message += f"<p>🔐 <strong>Access Issues ({len(access_files)}):</strong><br>"
            for error in access_files[:3]:
                message += f"• {error['path']}<br>"
            if len(access_files) > 3:
                message += f"• ... and {len(access_files) - 3} more<br>"
            message += "</p>"
        
        if other_files:
            message += f"<p>❓ <strong>Other Issues ({len(other_files)}):</strong><br>"
            for error in other_files[:3]:
                message += f"• {error['path']}<br>"
            if len(other_files) > 3:
                message += f"• ... and {len(other_files) - 3} more<br>"
            message += "</p>"
        
        message += """
        <hr>
        <p style="font-size: 11px; color: #666; font-style: italic;">
        ⚠️ <strong>AI Copy Warning:</strong> Some files contain corrupted characters or binary data.<br>
        You can't copy this corrupted content to AI systems as it may cause issues.<br>
        Only successfully processed files are included in the final output.
        </p>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(message)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def show_settings(self):
        """Show settings dialog"""
        import os
        
        msg = QMessageBox(self)
        msg.setWindowTitle("⚙️ Settings")
        msg.setIcon(QMessageBox.Icon.Information)
        
        settings_text = f"""
        <h3>⚙️ ContextLLM Settings</h3>
        
        <p><strong>Current Configuration:</strong></p>
        <ul>
        <li><b>Model:</b> {self.selected_model}</li>
        <li><b>Comment Removal:</b> {'Enabled' if self.comment_removal_checkbox.isChecked() else 'Disabled'}</li>
        <li><b>Source Type:</b> {self.current_source_type.title()}</li>
        <li><b>Window Size:</b> {self.width()}x{self.height()}</li>
        </ul>
        
        <p><strong>Advanced Settings:</strong></p>
        <ul>
        <li><b>Theme:</b> Light (Fixed for Windows compatibility)</li>
        <li><b>GitHub Token:</b> {'Configured' if os.getenv('GITHUB_TOKEN') else 'Not configured'}</li>
        <li><b>Default Exclusions:</b> {self.exclude_entry.text()}</li>
        </ul>
        
        <hr>
        <p style="font-size: 11px; color: #666;">
        💡 Most settings are auto-configured for optimal performance.<br>
        For GitHub token setup, set the GITHUB_TOKEN environment variable.
        </p>
        """
        
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(settings_text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def show_about(self):
        """Show enhanced about dialog"""
        about_text = f"""
        <h2>🚀 {APP_NAME} {APP_VERSION}</h2>
        <p><strong>Professional file content aggregation tool for LLMs</strong></p>
        
        <h3>✨ Key Features:</h3>
        <ul>
        <li>🎨 Modern PyQt6 Interface with clean design</li>
        <li>📁 Local folder processing with smart file selection</li>
        <li>🐙 GitHub repository integration (anonymous + authenticated)</li>
        <li>📝 Advanced template system with custom templates</li>
        <li>🔢 Token cost estimation for all major AI models</li>
        <li>🌳 Detailed tree view for precise file selection</li>
        </ul>
        
        <h3>⌨️ Keyboard Shortcuts:</h3>
        <ul>
        <li><code>Ctrl+O</code> - Select folder</li>
                        <li><code>Ctrl+Enter</code> - Reset files</li>
        <li><code>Ctrl+S</code> - Save content</li>
        <li><code>Ctrl+C</code> - Copy to clipboard</li>
        <li><code>F5</code> - Refresh</li>
        </ul>
        
        <p><strong>Created by:</strong> erencanakyuz</p>
        <p><em>If you like this app, please consider giving it a ⭐ on GitHub!</em></p>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("About ContextLLM")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(about_text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
    
    def center_window(self):
        """Center window on screen with smart sizing"""
        try:
            # Get smart window dimensions from settings
            width, height, x, y = settings.get_window_dimensions()
            
            # Apply the calculated size and position
            self.setGeometry(x, y, width, height)
            
            # Set minimum size based on screen size
            screen = QApplication.primaryScreen().availableGeometry()
            if screen:
                # Minimum size should be reasonable for the screen
                min_width = max(MIN_WINDOW_SIZE[0], int(screen.width() * 0.5))
                min_height = max(MIN_WINDOW_SIZE[1], int(screen.height() * 0.5))
                self.setMinimumSize(min_width, min_height)
            else:
                self.setMinimumSize(*MIN_WINDOW_SIZE)
                
            self.logger.info(f"Window sized to {width}x{height} at position ({x}, {y})")
            
        except Exception as e:
            self.logger.warning(f"Smart sizing failed, using fallback: {e}")
            # Fallback to basic centering
            self.setMinimumSize(*MIN_WINDOW_SIZE)
            frame_geometry = self.frameGeometry()
            screen = QApplication.primaryScreen().availableGeometry()
            center_point = screen.center()
            frame_geometry.moveCenter(center_point)
            self.move(frame_geometry.topLeft())
    
    def save_settings(self):
        """Save application settings"""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        # Settings saved
    
    def restore_settings(self):
        """Restore application settings"""
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        window_state = self.settings.value("windowState")
        if window_state:
            self.restoreState(window_state)
        
        # Apply light theme
        self.setup_styles()
        
    def closeEvent(self, event):
        """Handle application close"""
        try:
            self.logger.info("Application closing - saving settings")
            self.save_settings()
            self.logger.info("Application closed successfully")
            emergency_flush()  # Ensure all logs are written
        except Exception as e:
            log_critical_error(e, "closeEvent")
        finally:
            event.accept()
    
    def run(self):
        """Start the application"""
        self.show()


def main():
    """Main entry point with Windows optimizations and logging"""
    try:
        # Setup logging before anything else
        log_system = setup_logging("INFO")
        logger = get_logger("Main")
        logger.info("Starting ContextLLM application")
        
        # Windows-specific DPI awareness
        if platform.system() == "Windows":
            try:
                # Try new PyQt6 6.8+ attributes first
                try:
                    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
                    logger.info("Applied modern DPI scaling policy")
                except:
                    pass
                
                # PyQt6 enables high DPI scaling by default - no need for legacy attributes
                
                logger.info("Windows DPI optimizations completed")
            except Exception as e:
                logger.warning(f"DPI optimization error: {e}")
        
        app = QApplication(sys.argv)
        app.setApplicationName("ContextLLM")
        app.setApplicationVersion("3.0")
        app.setOrganizationName("ContextLLM")
        
        # Set application style for better Windows integration
        if platform.system() == "Windows":
            try:
                # Try to detect Windows version for better compatibility
                win_version = sys.getwindowsversion()
                
                if win_version.build >= 22000:  # Windows 11
                    app.setStyle("Fusion")  # Works great on Win11
                    logger.info("Set Fusion style for Windows 11")
                else:  # Windows 10 and older
                    app.setStyle("WindowsVista")  # More compatible with Win10
                    logger.info("Set WindowsVista style for Windows 10")
            except:
                # Safe fallback
                app.setStyle("Windows")
                logger.info("Set fallback Windows style")
        
        logger.info("Creating main application window")
        window = ContextLLMApp()
        window.run()
        
        logger.info("Application started successfully, entering event loop")
        exit_code = app.exec()
        
        logger.info(f"Application exiting with code: {exit_code}")
        log_system.cleanup_old_logs()  # Cleanup old logs on exit
        
        sys.exit(exit_code)
        
    except Exception as e:
        # Emergency logging if main logging fails
        print(f"CRITICAL ERROR: Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        
        # Try to log the error if possible
        try:
            logger = get_logger("Main")
            log_critical_error(e, "main()")
        except:
            pass
        
        sys.exit(1)


if __name__ == "__main__":
    main()