#!/usr/bin/env python3
"""
File Processing Module
Handles file scanning, filtering, and content aggregation.
"""

import os
from typing import List, Dict, Set, Optional, Tuple, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from .github_processor import GitHubProcessor

# Import comment removal functionality
try:
    from .comment_remover import comment_remover, remove_comments
    COMMENT_REMOVER_AVAILABLE = True
except ImportError:
    COMMENT_REMOVER_AVAILABLE = False

class FileProcessor:
    def __init__(self):
        self.all_files = []
        self.file_extensions = set()
        self.processed_files = []
        self.error_files = []
        self.selected_folder = None
        self.comment_removal_enabled = False
        
        # Import default patterns from config
        from config import DEFAULT_EXCLUDE_PATTERNS, PROBLEMATIC_FILE_PATTERNS
        self.default_excludes = DEFAULT_EXCLUDE_PATTERNS
        self.problematic_patterns = PROBLEMATIC_FILE_PATTERNS
    
    def scan_directory(self, folder_path: str, exclude_patterns: Optional[Set[str]] = None) -> Tuple[List[Dict], Set[str]]:
        """
        Recursively scan directory for files and identify extensions
        Returns: (all_files, file_extensions)
        """
        try:
            self.selected_folder = folder_path
            self.all_files = []
            self.file_extensions = set()
            
            # Use provided exclude patterns or defaults
            if exclude_patterns is None:
                exclude_patterns = self.default_excludes
            
            # Get all files recursively
            if folder_path:
                for root, dirs, files in os.walk(folder_path):
                    # Filter out excluded directories
                    dirs[:] = [d for d in dirs if not self.should_exclude(d, exclude_patterns)]
                    
                    for file in files:
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, folder_path)
                        
                        # Skip excluded files
                        if self.should_exclude(relative_path, exclude_patterns):
                            continue
                        
                        # Get file extension
                        _, ext = os.path.splitext(file)
                        
                        # Important extensionless files to include
                        important_extensionless = {
                            'Makefile', 'Dockerfile', 'README', 'LICENSE', 'CHANGELOG',
                            'Vagrantfile', 'Jenkinsfile', 'Procfile', '.gitignore', '.env'
                        }
                        
                        if ext or file in important_extensionless:  # Include files with extensions or important extensionless files
                            self.all_files.append({
                                'path': file_path,
                                'relative_path': relative_path,
                                'extension': ext.lower()
                            })
                            self.file_extensions.add(ext.lower())
            
            return self.all_files, self.file_extensions
            
        except Exception as e:
            raise Exception(f"Failed to scan directory: {str(e)}")
    
    def should_exclude(self, path: str, exclude_patterns: Set[str]) -> bool:
        """Check if a path should be excluded based on patterns"""
        path_parts = path.split(os.sep)
        
        for pattern in exclude_patterns:
            # Check if any part of path matches pattern
            if any(pattern in part for part in path_parts):
                return True
            # Check if path starts with pattern
            if path.startswith(pattern):
                return True
        
        return False
    
    def is_problematic_file(self, filepath: str) -> bool:
        """Check if file has problematic patterns that should be skipped"""
        filepath_lower = filepath.lower()
        
        # Check file extension
        _, ext = os.path.splitext(filepath_lower)
        if ext in self.problematic_patterns:
            return True
        
        # Check filename patterns
        filename = os.path.basename(filepath_lower)
        for pattern in self.problematic_patterns:
            if pattern in filename:
                return True
        
        return False
    
    def is_valid_content(self, content: str) -> bool:
        """Check if content is valid text content - very lenient for maximum compatibility"""
        if not content:
            return False
        
        # Check for binary content (very lenient heuristic)
        try:
            # Skip encoding check - we already handled it in file reading
            
            # Only check for excessive null bytes (clear binary indicator)
            null_ratio = content.count('\x00') / len(content)
            if null_ratio > 0.3:  # More than 30% null bytes - clearly binary
                return False
            
            # Much more lenient printable character check
            # Count printable chars, spaces, tabs, newlines, and common special chars
            valid_chars = sum(1 for c in content if (
                c.isprintable() or 
                c.isspace() or 
                ord(c) < 127 or  # ASCII range
                c in '•→←↑↓★☆♀♂©®™°±×÷'  # Common special characters
            ))
            
            valid_ratio = valid_chars / len(content)
            
            # Very lenient - only reject if less than 30% valid characters
            return valid_ratio > 0.3
            
        except Exception:
            # If any error occurs, assume it's valid text
            return True
    
    def aggregate_content(self, selected_extensions: Set[str], 
                         progress_callback: Optional[Callable[[float], None]] = None,
                         github_processor: Optional['GitHubProcessor'] = None,
                         files_to_process: Optional[List[Dict]] = None) -> Tuple[str, List[Dict]]:
        """
        Aggregate content from selected files
        
        Args:
            selected_extensions: Set of file extensions to process
            progress_callback: Optional callback for progress updates
            github_processor: Optional GitHub processor for remote files
            files_to_process: Optional specific list of files to process (bypasses extension filtering)
            
        Returns: (aggregated_content, processed_files)
        """
        try:
            # Reset error tracking
            self.error_files = []
            
            # Use provided file list or filter by extensions
            if files_to_process is not None:
                selected_files = files_to_process
            else:
                # Filter files by selected extensions
                selected_files = [f for f in self.all_files if f['extension'] in selected_extensions]
            
            # Generate directory tree
            tree_content = self.generate_directory_tree(selected_files)
            
            # Aggregate content
            content_parts = [tree_content]  # Start with tree
            processed_files = []
            
            for i, file_info in enumerate(selected_files):
                try:
                    # Update progress
                    if progress_callback:
                        progress = (i + 1) / len(selected_files)
                        progress_callback(progress)
                    
                    # Check for problematic file patterns (warning only, don't skip)
                    _ = self.is_problematic_file(file_info['relative_path'])
                    
                    # Check file accessibility
                    try:
                        if github_processor and 'download_url' in file_info:
                            # Use size from GitHub API
                            file_size = file_info.get('size', 0)
                        else:
                            # Get local file size
                            file_size = os.path.getsize(file_info['path'])
                    except OSError as e:
                        self.error_files.append({
                            'path': file_info['relative_path'],
                            'error': f'Cannot access file: {str(e)}'
                        })
                        continue
                    
                    # Read file content
                    try:
                        if github_processor and 'download_url' in file_info:
                            # Download from GitHub
                            content = github_processor.download_file_content(file_info['download_url'])
                            if content is None:
                                self.error_files.append({
                                    'path': file_info['relative_path'],
                                    'error': 'Failed to download from GitHub'
                                })
                                continue
                        else:
                            # Read local file with multiple encoding attempts
                            content = None
                            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
                            
                            for encoding in encodings:
                                try:
                                    with open(file_info['path'], 'r', encoding=encoding, errors='ignore') as f:
                                        content = f.read()
                                    break  # Success, exit encoding loop
                                except (UnicodeDecodeError, UnicodeError):
                                    continue
                            
                            if content is None:
                                # Last resort: read as binary and decode with errors='replace'
                                with open(file_info['path'], 'rb') as f:
                                    raw_content = f.read()
                                content = raw_content.decode('utf-8', errors='replace')
                    except Exception as e:
                        self.error_files.append({
                            'path': file_info['relative_path'],
                            'error': f'Cannot read file: {str(e)}'
                        })
                        continue
                    
                    # Validate content
                    if not self.is_valid_content(content):
                        # Debug info for content validation failure
                        null_count = content.count('\x00')
                        printable_count = sum(1 for c in content if c.isprintable() or c.isspace())
                        total_chars = len(content)
                        printable_ratio = printable_count / total_chars if total_chars > 0 else 0
                        
                        self.error_files.append({
                            'path': file_info['relative_path'],
                            'error': f'Invalid content: {null_count} nulls, {printable_ratio:.2%} printable chars, {total_chars} total'
                        })
                        continue
                    
                    # Apply comment removal if enabled
                    original_content = content
                    if self.comment_removal_enabled and COMMENT_REMOVER_AVAILABLE:
                        try:
                            content, stats = remove_comments(content, file_info['relative_path'])
                        except Exception as e:
                            content = original_content
                    
                    # Add file header and content
                    file_header = f"=== FILE: {file_info['relative_path']} ===\n"
                    content_parts.append(file_header + content + "\n\n")
                    
                    # Track processed file
                    processed_files.append({
                        'path': file_info['relative_path'],
                        'size': file_size,
                        'extension': file_info['extension'],
                        'original_size': len(original_content),
                        'processed_size': len(content)
                    })
                    
                except Exception as e:
                    self.error_files.append({
                        'path': file_info['relative_path'],
                        'error': f'Processing error: {str(e)}'
                    })
                    continue
            
            # Join all content
            aggregated_content = "\n".join(content_parts)
            self.processed_files = processed_files
            
            return aggregated_content, processed_files
            
        except Exception as e:
            raise Exception(f"Content aggregation failed: {str(e)}")
    
    def generate_directory_tree(self, files: List[Dict]) -> str:
        """Generate a visual directory tree from selected files"""
        if not files:
            return "=== DIRECTORY TREE ===\n(No files selected)\n\n"
        
        # Build tree structure
        tree_dict = {}
        for file_info in files:
            path_parts = file_info['relative_path'].split(os.sep)
            current = tree_dict
            
            for part in path_parts[:-1]:  # Directories
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Add file
            filename = path_parts[-1]
            current[filename] = file_info['extension']
        
        # Generate tree string
        tree_lines = ["=== DIRECTORY TREE ==="]
        folder_name = os.path.basename(self.selected_folder) if self.selected_folder else "Unknown"
        tree_lines.append(f"📁 {folder_name}/")
        
        def build_tree_lines(node, prefix="", is_last=True):
            if isinstance(node, dict):
                items = sorted(node.items(), key=lambda x: (isinstance(x[1], str), x[0]))
                for i, (name, value) in enumerate(items):
                    is_last_item = (i == len(items) - 1)
                    connector = "└── " if is_last_item else "├── "
                    
                    if isinstance(value, dict):  # Directory
                        tree_lines.append(f"{prefix}{connector}📁 {name}/")
                        extension = "    " if is_last_item else "│   "
                        build_tree_lines(value, prefix + extension, is_last_item)
                    else:  # File
                        icon = self.get_file_icon(value)
                        tree_lines.append(f"{prefix}{connector}{icon} {name}")
        
        build_tree_lines(tree_dict)
        tree_lines.append("")  # Empty line
        return "\n".join(tree_lines) + "\n"
    
    def get_file_icon(self, extension: str) -> str:
        """Get emoji icon for file extension"""
        from config import settings
        return settings.get_file_icon(extension)
    
    def get_exclude_patterns(self, exclude_text: str = "") -> Set[str]:
        """Get exclude patterns from text input"""
        patterns = set(self.default_excludes)  # Start with defaults
        
        if exclude_text:
            # Add user patterns
            user_patterns = [p.strip() for p in exclude_text.split(',') if p.strip()]
            patterns.update(user_patterns)
        
        return patterns
    
    def get_error_files(self) -> List[Dict]:
        """Get list of files that had processing errors"""
        return self.error_files
    
    def get_processed_files(self) -> List[Dict]:
        """Get list of successfully processed files"""
        return self.processed_files
    
    def set_comment_removal(self, enabled: bool):
        """Enable or disable comment removal"""
        self.comment_removal_enabled = enabled and COMMENT_REMOVER_AVAILABLE