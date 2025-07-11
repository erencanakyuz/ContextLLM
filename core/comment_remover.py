#!/usr/bin/env python3


import re
import os
from typing import Dict, List, Tuple

class CommentRemover:
    def __init__(self):
        # Define comment patterns for different file types
        self.comment_patterns = {
            # Python, Shell, Ruby, etc.
            '.py': [
                (r'"""[\s\S]*?"""', ''),  # Triple quoted strings (docstrings)
                (r"'''[\s\S]*?'''", ''),  # Triple quoted strings
                (r'#.*$', ''),            # Single line comments
            ],
            '.sh': [
                (r'#.*$', ''),            # Shell comments
            ],
            '.rb': [
                (r'#.*$', ''),            # Ruby comments
                (r'=begin[\s\S]*?=end', ''),  # Multi-line comments
            ],
            
            # JavaScript, TypeScript, C, C++, Java, etc.
            '.js': [
                (r'/\*[\s\S]*?\*/', ''),  # Multi-line comments
                (r'//.*$', ''),           # Single line comments
            ],
            '.ts': [
                (r'/\*[\s\S]*?\*/', ''),  # Multi-line comments
                (r'//.*$', ''),           # Single line comments
            ],
            '.tsx': [
                (r'/\*[\s\S]*?\*/', ''),  # Multi-line comments
                (r'//.*$', ''),           # Single line comments
            ],
            '.jsx': [
                (r'/\*[\s\S]*?\*/', ''),  # Multi-line comments
                (r'//.*$', ''),           # Single line comments
            ],
            '.c': [
                (r'/\*[\s\S]*?\*/', ''),  # Multi-line comments
                (r'//.*$', ''),           # Single line comments
            ],
            '.cpp': [
                (r'/\*[\s\S]*?\*/', ''),  # Multi-line comments
                (r'//.*$', ''),           # Single line comments
            ],
            '.h': [
                (r'/\*[\s\S]*?\*/', ''),  # Multi-line comments
                (r'//.*$', ''),           # Single line comments
            ],
            '.java': [
                (r'/\*[\s\S]*?\*/', ''),  # Multi-line comments
                (r'//.*$', ''),           # Single line comments
            ],
            '.cs': [
                (r'/\*[\s\S]*?\*/', ''),  # Multi-line comments
                (r'//.*$', ''),           # Single line comments
                (r'///.*$', ''),          # XML documentation comments
            ],
            
            # HTML, XML
            '.html': [
                (r'<!--[\s\S]*?-->', ''), # HTML comments
            ],
            '.xml': [
                (r'<!--[\s\S]*?-->', ''), # XML comments
            ],
            
            # CSS, SCSS, LESS
            '.css': [
                (r'/\*[\s\S]*?\*/', ''),  # CSS comments
            ],
            '.scss': [
                (r'/\*[\s\S]*?\*/', ''),  # Multi-line comments
                (r'//.*$', ''),           # Single line comments
            ],
            '.less': [
                (r'/\*[\s\S]*?\*/', ''),  # Multi-line comments
                (r'//.*$', ''),           # Single line comments
            ],
            
            # SQL
            '.sql': [
                (r'--.*$', ''),           # SQL single line comments
                (r'/\*[\s\S]*?\*/', ''),  # SQL multi-line comments
            ],
            
            # PHP
            '.php': [
                (r'/\*[\s\S]*?\*/', ''),  # Multi-line comments
                (r'//.*$', ''),           # Single line comments
                (r'#.*$', ''),            # Shell-style comments
            ],
            
            # Go
            '.go': [
                (r'/\*[\s\S]*?\*/', ''),  # Multi-line comments
                (r'//.*$', ''),           # Single line comments
            ],
            
            # Rust
            '.rs': [
                (r'/\*[\s\S]*?\*/', ''),  # Multi-line comments
                (r'//.*$', ''),           # Single line comments
                (r'///.*$', ''),          # Documentation comments
            ],
            
            # Swift
            '.swift': [
                (r'/\*[\s\S]*?\*/', ''),  # Multi-line comments
                (r'//.*$', ''),           # Single line comments
            ],
            
            # Kotlin
            '.kt': [
                (r'/\*[\s\S]*?\*/', ''),  # Multi-line comments
                (r'//.*$', ''),           # Single line comments
            ],
            
            # YAML
            '.yml': [
                (r'#.*$', ''),            # YAML comments
            ],
            '.yaml': [
                (r'#.*$', ''),            # YAML comments
            ],
            
            # Configuration files
            '.ini': [
                (r'[;#].*$', ''),         # INI comments
            ],
            '.conf': [
                (r'#.*$', ''),            # Config comments
            ],
            
            # Batch files
            '.bat': [
                (r'REM.*$', ''),          # Batch REM comments
                (r'::.*$', ''),           # Batch :: comments
            ],
            
            # PowerShell
            '.ps1': [
                (r'#.*$', ''),            # PowerShell comments
                (r'<#[\s\S]*?#>', ''),    # PowerShell block comments
            ],
        }
    
    def get_file_extension(self, filename: str) -> str:
        """
        Get file extension from filename.
        Uses os.path.splitext for robust handling of paths and filenames.
        """
        # The original implementation using split('.') was buggy for paths containing dots.
        # os.path.splitext is the correct and robust way to get a file extension.
        return os.path.splitext(filename)[1].lower()
    
    def remove_comments_from_text(self, text: str, file_extension: str) -> Tuple[str, int, int]:
        """
        Remove comments from text based on file extension
        Returns: (cleaned_text, original_lines, cleaned_lines)
        """
        if not text:
            return text, 0, 0
        
        original_lines = len(text.splitlines())
        
        # Get patterns for this file type
        patterns = self.comment_patterns.get(file_extension, [])
        
        if not patterns:
            # No patterns found, return original text
            return text, original_lines, original_lines
        
        cleaned_text = text
        
        # Apply each pattern
        for pattern, replacement in patterns:
            if pattern.endswith('$'):  # Line-based patterns
                # Process line by line to preserve structure
                lines = cleaned_text.splitlines()
                cleaned_lines = []
                
                for line in lines:
                    cleaned_line = re.sub(pattern, replacement, line, flags=re.MULTILINE)
                    # Only keep the line if it has content after cleaning
                    if cleaned_line.strip() or not line.strip():
                        cleaned_lines.append(cleaned_line)
                
                cleaned_text = '\n'.join(cleaned_lines)
            else:
                # Multi-line patterns
                cleaned_text = re.sub(pattern, replacement, cleaned_text, flags=re.DOTALL)
        
        # Clean up excessive empty lines
        cleaned_text = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_text)
        cleaned_text = cleaned_text.strip()
        
        cleaned_lines = len(cleaned_text.splitlines()) if cleaned_text else 0
        
        return cleaned_text, original_lines, cleaned_lines
    
    def get_comment_stats(self, original_text: str, cleaned_text: str) -> Dict:
        """Get statistics about comment removal"""
        original_chars = len(original_text)
        cleaned_chars = len(cleaned_text)
        chars_removed = original_chars - cleaned_chars
        
        original_lines = len(original_text.splitlines())
        cleaned_lines = len(cleaned_text.splitlines()) if cleaned_text else 0
        lines_removed = original_lines - cleaned_lines
        
        return {
            'original_chars': original_chars,
            'cleaned_chars': cleaned_chars,
            'chars_removed': chars_removed,
            'chars_saved_percent': (chars_removed / original_chars * 100) if original_chars > 0 else 0,
            'original_lines': original_lines,
            'cleaned_lines': cleaned_lines,
            'lines_removed': lines_removed,
            'lines_saved_percent': (lines_removed / original_lines * 100) if original_lines > 0 else 0
        }
    
    def is_supported_file_type(self, filename: str) -> bool:
        """Check if file type is supported for comment removal"""
        extension = self.get_file_extension(filename)
        return extension in self.comment_patterns
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions"""
        return list(self.comment_patterns.keys())
    
    def preview_comment_removal(self, text: str, filename: str) -> Dict:
        """Preview what comment removal would do without actually removing"""
        extension = self.get_file_extension(filename)
        
        if not self.is_supported_file_type(filename):
            return {
                'supported': False,
                'message': f'File type {extension} not supported for comment removal'
            }
        
        cleaned_text, original_lines, cleaned_lines = self.remove_comments_from_text(text, extension)
        stats = self.get_comment_stats(text, cleaned_text)
        
        return {
            'supported': True,
            'stats': stats,
            'preview_text': cleaned_text[:500] + '...' if len(cleaned_text) > 500 else cleaned_text
        }

# Global instance
comment_remover = CommentRemover()

def remove_comments(text: str, filename: str) -> Tuple[str, Dict]:
    """Quick function to remove comments and get stats"""
    extension = comment_remover.get_file_extension(filename)
    cleaned_text, _, _ = comment_remover.remove_comments_from_text(text, extension)
    stats = comment_remover.get_comment_stats(text, cleaned_text)
    return cleaned_text, stats 