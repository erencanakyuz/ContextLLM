#!/usr/bin/env python3
"""
Utility Helper Functions
Contains various utility functions for file operations, UI helpers, and calculations.
"""

import os
from typing import Dict, Tuple, Optional
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QApplication
from PyQt6.QtGui import QClipboard
from config import FILE_ICON_MAP, settings
from .logger import get_logger

# Import token calculation if available
try:
    from core.token_calculator import estimate_tokens, estimate_cost
    TOKEN_CALC_AVAILABLE = True
except ImportError:
    TOKEN_CALC_AVAILABLE = False

# Import tiktoken if available
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

class FileUtils:
    """File-related utility functions"""
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except (OSError, FileNotFoundError) as e:
            # Log the error for debugging if needed
            # get_logger("FileUtils").debug(f"Could not get size for {file_path}: {e}")
            return 0
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024
            i += 1
        
        if i == 0:
            return f"{int(size)} {size_names[i]}"
        else:
            return f"{size:.1f} {size_names[i]}"
    
    @staticmethod
    def get_file_icon(extension: str) -> str:
        """Get emoji icon for file extension"""
        return FILE_ICON_MAP.get(extension.lower(), '📄')
    
    @staticmethod
    def save_content_to_file(content: str, parent_window=None) -> bool:
        """Save content to a file with dialog"""
        if not content:
            if parent_window:
                QMessageBox.warning(parent_window, "Warning", "No content to save.")
            return False
        
        try:
            filename, _ = QFileDialog.getSaveFileName(
                parent_window,
                "Save Content As",
                "",
                "Text files (*.txt);;Markdown files (*.md);;All files (*.*)"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            return False
                
        except Exception as e:
            if parent_window:
                QMessageBox.critical(parent_window, "Error", f"Failed to save file: {str(e)}")
            return False
    
    @staticmethod
    def copy_to_clipboard(content: str, root_window=None) -> bool:
        """Copy content to clipboard"""
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(content)
            return True
        except Exception:
            return False

class TokenUtils:
    """Token calculation and cost estimation utilities"""
    
    @staticmethod
    def calculate_tokens(text: str, model: str = "gpt-4o") -> int:
        """Calculate token count using enhanced LLM tokenizer or fallback methods"""
        if not text:
            return 0
        
        try:
            # Try enhanced token calculation first
            if TOKEN_CALC_AVAILABLE:
                try:
                    return estimate_tokens(text, model)
                except Exception as e:
                    get_logger("TokenUtils").warning(f"Enhanced token calculation failed: {e}")
            
            # Try tiktoken if available
            if TIKTOKEN_AVAILABLE:
                try:
                    # Use GPT-4 tokenizer for accurate count
                    encoding = tiktoken.encoding_for_model("gpt-4")
                    return len(encoding.encode(text))
                except Exception as e:
                    get_logger("TokenUtils").warning(f"GPT-4 tokenizer failed: {e}")
                    # Fallback to cl100k_base encoding
                    try:
                        encoding = tiktoken.get_encoding("cl100k_base")
                        return len(encoding.encode(text))
                    except Exception as e2:
                        get_logger("TokenUtils").warning(f"cl100k_base tokenizer failed: {e2}")
            
            # Fallback: estimate tokens using enhanced word count
            word_count = len(text.split())
            char_count = len(text)
            
            # More accurate estimation based on model type
            if 'claude' in model.lower():
                return int(char_count / 3.5)  # Claude tokenization
            elif 'gemini' in model.lower():
                return int(char_count / 4.0)  # Gemini tokenization
            else:
                return int(word_count * 1.3)  # Default GPT-style estimation
                
        except Exception as e:
            get_logger("TokenUtils").error(f"Token calculation failed completely: {e}")
            # Ultimate fallback - very basic estimation
            return max(1, len(text.split()))
    
    @staticmethod
    def calculate_cost_estimation(token_count: int, model: str = "gpt-4o") -> Tuple[float, Dict]:
        """Calculate cost estimation for the given model"""
        if TOKEN_CALC_AVAILABLE and token_count > 0:
            try:
                cost, details = estimate_cost(token_count, model)
                return cost, details
            except Exception:
                pass
        
        # Fallback cost estimation
        basic_cost_per_1k = 0.001  # Default estimate
        total_cost = (token_count / 1000) * basic_cost_per_1k
        
        return total_cost, {
            'total_cost': total_cost,
            'input_tokens': token_count,
            'estimated_output_tokens': int(token_count * 0.1),
            'model': model
        }
    
    @staticmethod
    def format_cost(cost: float) -> str:
        """Format cost for display"""
        if cost < 0.01:
            return f"${cost:.4f}"
        elif cost < 0.1:
            return f"${cost:.3f}"
        else:
            return f"${cost:.2f}"

class UIUtils:
    """UI-related utility functions for PyQt6"""
    
    @staticmethod
    def show_information_message(parent, title: str, message: str):
        """Show information message dialog"""
        QMessageBox.information(parent, title, message)
    
    @staticmethod
    def show_warning_message(parent, title: str, message: str):
        """Show warning message dialog"""
        QMessageBox.warning(parent, title, message)
    
    @staticmethod
    def show_error_message(parent, title: str, message: str):
        """Show error message dialog"""
        QMessageBox.critical(parent, title, message)
    
    @staticmethod
    def show_question_message(parent, title: str, message: str) -> bool:
        """Show question message dialog and return True if Yes was clicked"""
        reply = QMessageBox.question(parent, title, message, 
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        return reply == QMessageBox.StandardButton.Yes

class ValidationUtils:
    """Input validation utilities"""
    
    @staticmethod
    def is_valid_folder_path(path: str) -> bool:
        """Check if path is a valid folder"""
        return os.path.isdir(path) if path else False
    
    @staticmethod
    def is_valid_file_path(path: str) -> bool:
        """Check if path is a valid file"""
        return os.path.isfile(path) if path else False
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe file operations"""
        import re
        # Remove invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove leading/trailing whitespace and dots
        sanitized = sanitized.strip('. ')
        # Ensure not empty
        return sanitized if sanitized else 'untitled'
    
    @staticmethod
    def validate_model_name(model: str) -> bool:
        """Validate if model name is supported"""
        from config import AVAILABLE_MODELS
        return model in AVAILABLE_MODELS

# Convenience instances
file_utils = FileUtils()
token_utils = TokenUtils()
ui_utils = UIUtils()
validation_utils = ValidationUtils()