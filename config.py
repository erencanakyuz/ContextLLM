#!/usr/bin/env python3
"""
Configuration and Settings Module
Contains application constants, default settings, and configuration management.
"""

import os
from typing import Dict, Set, Tuple

# Application Information
APP_NAME = "ContextLLM Pro"
APP_VERSION = "v3.0"
APP_DESCRIPTION = "Professional file content aggregation tool for LLMs"

# Default Window Settings (Smart sizing for most screens)
DEFAULT_WINDOW_SIZE = (1400, 900)  # Reduced from 1600x1000
MIN_WINDOW_SIZE = (1200, 800)
SMALL_WINDOW_SIZE = (1100, 700)   # For smaller screens
SMALL_MIN_SIZE = (1000, 650)

# Window constraints (percentage of screen size)
MAX_SCREEN_RATIO = 0.85  # Maximum 85% of screen
MIN_SCREEN_RATIO = 0.6   # Minimum 60% of screen

# UI Settings
HEADER_HEIGHT = 80
STATUS_BAR_HEIGHT = 60
LEFT_PANEL_WIDTH = 400
COLLAPSED_PANEL_WIDTH = 50

# Modern Light Theme Settings (GitHub inspired)
# Professional Color Palette - Light Mode Only
COLORS = {
    # Main Theme Colors
    "primary": "#0969da",           # GitHub Blue
    "success": "#1a7f37",          # GitHub Green
    "warning": "#d1242f",          # GitHub Red  
    "info": "#0969da",             # GitHub Blue
    
    # Background Colors
    "bg_primary": "#ffffff",        # Main background
    "bg_secondary": "#f6f8fa",      # Secondary background
    "bg_tertiary": "#f8f8f8",       # Cards/panels
    "bg_hover": "#f3f4f6",          # Hover states
    
    # Text Colors
    "text_primary": "#24292f",      # Main text
    "text_secondary": "#656d76",    # Secondary text  
    "text_muted": "#8c959f",        # Muted text
    "text_link": "#0969da",         # Links
    
    # Border Colors
    "border_primary": "#d0d7de",    # Main borders
    "border_muted": "#e0e0e0",      # Subtle borders
    
    # Status Colors
    "online": "#23a559",           # Online/success
    "away": "#f79c42",             # Warning/away
    "busy": "#f23f42",             # Error/busy
    "offline": "#80848e",          # Offline/disabled
}

# Header specific colors
HEADER_COLOR = COLORS["bg_tertiary"]
HEADER_TEXT_COLOR = COLORS["text_primary"] 
HEADER_SUBTITLE_COLOR = COLORS["text_secondary"]

# File Processing Settings
DEFAULT_EXCLUDE_PATTERNS = {
    '.git', 'node_modules', '__pycache__', '.vscode', '.idea', 
    'dist', 'build', '.next', '.nuxt', 'coverage', '.pytest_cache',
    '.tox', '.env', '.venv', 'venv', 'env', '.DS_Store', 'Thumbs.db'
}

# Problematic file extensions and patterns (using set for O(1) lookups)
PROBLEMATIC_FILE_PATTERNS = {
    '.meta',     # Unity meta files
    '.pyc',      # Python compiled
    '.pyo',      # Python optimized
    '.pyd',      # Python extension
    '.so',       # Shared object
    '.dll',      # Dynamic library
    '.exe',      # Executable
    '.bin',      # Binary
    '.obj',      # Object file
    '.o',        # Object file
    '.a',        # Archive
    '.lib',      # Library
    '.zip',      # Archive
    '.tar',      # Archive
    '.gz',       # Compressed
    '.rar',      # Archive
    '.7z',       # Archive
    '.pdf',      # Documents
    '.doc',      # Documents
    '.docx',     # Documents
    '.xls',      # Spreadsheet
    '.xlsx',     # Spreadsheet
    '.ppt',      # Presentation
    '.pptx',     # Presentation
    '.mp3',      # Audio
    '.mp4',      # Video
    '.avi',      # Video
    '.mov',      # Video
    '.wmv',      # Video
    '.mkv',      # Video
    '.jpg',      # Image
    '.jpeg',     # Image
    '.png',      # Image
    '.gif',      # Image
    '.bmp',      # Image
    '.tiff',     # Image
    '.svg',      # Image
    '.ico',      # Icon
    '.woff',     # Font
    '.woff2',    # Font
    '.ttf',      # Font
    '.otf',      # Font
    '.eot',      # Font
    '.db',       # Database
    '.sqlite',   # Database
    '.mdb',      # Database
    '.accdb',    # Database
    '.log',      # Log files
    '.tmp',      # Temporary files
    '.temp',     # Temporary files
    '.cache',    # Cache files
    '.lock',     # Lock files
    '.DS_Store', # macOS
    'Thumbs.db', # Windows
    '.gitignore',     # Git
    '.gitmodules',    # Git
    '.gitattributes', # Git
}

# File icons mapping
FILE_ICON_MAP = {
    '.py': '🐍',
    '.js': '💛',
    '.ts': '🔷',
    '.tsx': '⚛️',
    '.jsx': '⚛️',
    '.html': '🌐',
    '.css': '🎨',
    '.scss': '🎨',
    '.sass': '🎨',
    '.less': '🎨',
    '.json': '📄',
    '.xml': '📄',
    '.yaml': '📄',
    '.yml': '📄',
    '.md': '📝',
    '.txt': '📝',
    '.java': '☕',
    '.c': '🔧',
    '.cpp': '🔧',
    '.h': '🔧',
    '.cs': '🔷',
    '.php': '🐘',
    '.rb': '💎',
    '.go': '🐹',
    '.rs': '🦀',
    '.kt': '🟣',
    '.swift': '🦉',
    '.sql': '🗃️',
    '.sh': '🐚',
    '.bat': '🪟',
    '.ps1': '🔷',
    '.dockerfile': '🐳',
}

# Default model settings
DEFAULT_MODEL = "claude-4-sonnet"
AVAILABLE_MODELS = [
    # Latest 2025 AI Models
    "claude-4-sonnet",
    "claude-3-7-sonnet", 
    "gpt-4.5",
    "gpt-o3-pro",
    "gpt-o4-mini",
    "gemini-2-5-pro",
    "gemini-2-5-flash",
    "grok-3",
    "grok-3-mini",
    "deepseek-r1",
    
    # Existing proven models
    "gpt-4o",
    "gpt-4-turbo", 
    "gpt-o3",
    "claude-3-5-sonnet",
    "gemini-2-0-flash",
    "gpt-3.5-turbo",
    "gpt-4.1"
]

# Asset paths
ASSETS_DIR = "assets"
ICON_FILE = "icon.ico"
PRICING_DATA_FILE = "pricing_data.json"
TEMPLATES_FILE = "prompt_templates.json"

# Content validation settings
MIN_PRINTABLE_RATIO = 0.7  # At least 70% printable characters
MAX_NULL_RATIO = 0.01      # Less than 1% null bytes

# UI Messages
MESSAGES = {
    'no_folder_selected': "No folder selected. Please select a folder first.",
    'no_files_found': "No files found in the selected folder.",
    'no_extensions_selected': "No file extensions selected. Please select at least one extension.",
    'processing_complete': "Processing complete!",
    'content_copied': "Content copied to clipboard!",
    'file_saved': "File saved successfully!",
    'error_occurred': "An error occurred",
    'drag_drop_folder': "📁 Drag & drop a folder here or click 'Select Folder'",
    'drag_drop_disabled': "📁 Drag & drop not available - click 'Select Folder'",
}

# Status message types
STATUS_TYPES = {
    'info': 'info',
    'success': 'success', 
    'error': 'error',
    'warning': 'warning'
}

class Settings:
    """Application settings manager"""
    
    def __init__(self):
        self.selected_model = DEFAULT_MODEL
        self.comment_removal_enabled = False
        self.show_cost_estimation = True
        self.window_size = DEFAULT_WINDOW_SIZE
        self.left_panel_collapsed = False
        
    def get_asset_path(self, filename: str) -> str:
        """Get full path to asset file"""
        return os.path.join(ASSETS_DIR, filename)
    
    def get_icon_path(self) -> str:
        """Get path to application icon"""
        return self.get_asset_path(ICON_FILE)
    
    def get_pricing_data_path(self) -> str:
        """Get path to pricing data file"""
        return self.get_asset_path(PRICING_DATA_FILE)
    
    def get_templates_path(self) -> str:
        """Get path to templates file"""
        return self.get_asset_path(TEMPLATES_FILE)
    
    def get_exclude_patterns(self) -> Set[str]:
        """Get default exclude patterns"""
        return DEFAULT_EXCLUDE_PATTERNS.copy()
    
    def get_problematic_patterns(self) -> set:
        """Get problematic file patterns"""
        return PROBLEMATIC_FILE_PATTERNS.copy()
    
    def get_file_icon(self, extension: str) -> str:
        """Get emoji icon for file extension"""
        return FILE_ICON_MAP.get(extension.lower(), '📄')
    
    def get_window_dimensions(self) -> Tuple[int, int, int, int]:
        """Get smart window size and position based on screen size"""
        try:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtGui import QGuiApplication
            
            # Get primary screen dimensions
            screen = QGuiApplication.primaryScreen()
            if screen:
                screen_rect = screen.availableGeometry()
                screen_width = screen_rect.width()
                screen_height = screen_rect.height()
                
                # Calculate smart window size (85% max, 60% min of screen)
                max_width = int(screen_width * MAX_SCREEN_RATIO)
                max_height = int(screen_height * MAX_SCREEN_RATIO)
                min_width = int(screen_width * MIN_SCREEN_RATIO)
                min_height = int(screen_height * MIN_SCREEN_RATIO)
                
                # Use default size but constrain to screen
                width = min(max(DEFAULT_WINDOW_SIZE[0], min_width), max_width)
                height = min(max(DEFAULT_WINDOW_SIZE[1], min_height), max_height)
                
                # Center on screen
                x = (screen_width - width) // 2
                y = (screen_height - height) // 2
                
                return (width, height, x, y)
        except:
            pass
        
        # Fallback to default if screen detection fails
        return (*DEFAULT_WINDOW_SIZE, 100, 100)  # width, height, x, y
    
    def set_model(self, model: str):
        """Set the selected model"""
        if model in AVAILABLE_MODELS:
            self.selected_model = model
    
    def toggle_comment_removal(self):
        """Toggle comment removal setting"""
        self.comment_removal_enabled = not self.comment_removal_enabled
    
    def toggle_cost_estimation(self):
        """Toggle cost estimation display"""
        self.show_cost_estimation = not self.show_cost_estimation
    
    def get_color(self, color_name: str) -> str:
        """Get color value for specified color name"""
        return COLORS.get(color_name, COLORS["text_primary"])
    
    def get_theme_colors(self) -> Dict[str, str]:
        """Get all theme colors"""
        return COLORS.copy()

# Global settings instance
settings = Settings()