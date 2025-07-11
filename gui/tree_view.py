#!/usr/bin/env python3
"""
Tree View Dialog for PyQt6
"""

import os
from typing import Set

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QCheckBox, QLineEdit, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from utils.helpers import file_utils

class TreeViewDialog(QDialog):
    def __init__(self, parent=None, files_list=None):
        super().__init__(parent)
        self.files_list = files_list or []
        self.file_checkboxes = {}
        
        self.setWindowTitle("🌳 Directory Tree View")
        self.setMinimumSize(900, 800)
        self.init_ui()
        self.build_tree()
        
    def init_ui(self):
        """Initialize the tree view UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("📁 Detailed Directory Tree with File Selection")
        header_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(header_label)
        
        # Controls
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        
        # File selection controls
        select_all_btn = QPushButton("✅ Select All Files")
        select_all_btn.clicked.connect(lambda: self.toggle_all_files(True))
        controls_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("❌ Deselect All Files")
        deselect_all_btn.clicked.connect(lambda: self.toggle_all_files(False))
        controls_layout.addWidget(deselect_all_btn)
        
        # Search
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("🔍 Search files...")
        self.search_entry.textChanged.connect(self.filter_tree)
        controls_layout.addWidget(self.search_entry)
        
        # Stats
        self.stats_label = QLabel("Selected: 0/0")
        controls_layout.addWidget(self.stats_label)
        
        layout.addWidget(controls_frame)
        
        # Tree widget
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Files", "Size", "Extension"])
        self.tree_widget.itemChanged.connect(self.update_stats)
        layout.addWidget(self.tree_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        apply_btn = QPushButton("🚀 Apply & Process Files")
        apply_btn.clicked.connect(self.apply_selection)
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #34c759;
            }
        """)
        button_layout.addWidget(apply_btn)
        
        export_btn = QPushButton("📋 Export Tree")
        export_btn.clicked.connect(self.export_tree)
        button_layout.addWidget(export_btn)
        
        close_btn = QPushButton("✖️ Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
    def build_tree(self):
        """Build the tree structure from files list"""
        if not self.files_list:
            no_files_item = QTreeWidgetItem(self.tree_widget)
            no_files_item.setText(0, "No files found in the selected directory")
            return
        
        # Group files by directory structure
        tree_dict = {}
        for file_info in self.files_list:
            path_parts = file_info['relative_path'].split(os.sep)
            current = tree_dict
            
            # Build directory structure
            for part in path_parts[:-1]:
                if part not in current:
                    current[part] = {'_is_dir': True, '_files': []}
                current = current[part]
            
            # Add file
            filename = path_parts[-1]
            if '_files' not in current:
                current['_files'] = []
            current['_files'].append(file_info)
        
        # Add root folder info
        if hasattr(self.parent(), 'selected_folder') and self.parent().selected_folder:
            folder_name = os.path.basename(self.parent().selected_folder)
        else:
            folder_name = "Project Files"
            
        root_item = QTreeWidgetItem(self.tree_widget)
        root_item.setText(0, f"📁 {folder_name}/ ({len(self.files_list)} files)")
        root_item.setExpanded(True)
        
        # Render tree
        self.render_tree_node(root_item, tree_dict)
        
        # Update initial stats
        self.update_stats()
    
    def render_tree_node(self, parent_item, node_dict):
        """Render a tree node with proper structure"""
        for name, content in sorted(node_dict.items()):
            if name.startswith('_'):
                continue
            
            if isinstance(content, dict) and content.get('_is_dir', False):
                # Directory
                dir_item = QTreeWidgetItem(parent_item)
                dir_item.setText(0, f"📁 {name}/")
                dir_item.setExpanded(True)
                
                # Render subdirectories and files
                self.render_tree_node(dir_item, content)
                
                # Render files in this directory
                if '_files' in content:
                    for file_info in sorted(content['_files'], key=lambda x: x['relative_path']):
                        self.render_file_item(dir_item, file_info)
    
    def render_file_item(self, parent_item, file_info):
        """Render a file item with checkbox"""
        file_item = QTreeWidgetItem(parent_item)
        
        # File icon and name
        icon = file_utils.get_file_icon(file_info.get('extension', ''))
        filename = os.path.basename(file_info['relative_path'])
        
        file_item.setText(0, f"{icon} {filename}")
        file_item.setText(1, file_utils.format_size(file_info.get('size', 0)))
        file_item.setText(2, file_info.get('extension', ''))
        
        # Make it checkable
        file_item.setFlags(file_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        file_item.setCheckState(0, Qt.CheckState.Checked)  # Default checked
        
        # Store file info
        file_item.setData(0, Qt.ItemDataRole.UserRole, file_info)
        
        # Store reference for easy access
        self.file_checkboxes[file_info['relative_path']] = file_item
    
    
    def toggle_all_files(self, select_all):
        """Toggle all file checkboxes"""
        for item in self.file_checkboxes.values():
            item.setCheckState(0, Qt.CheckState.Checked if select_all else Qt.CheckState.Unchecked)
        self.update_stats()
    
    def filter_tree(self):
        """Filter tree based on search text"""
        search_text = self.search_entry.text().lower()
        
        def filter_item(item):
            """Recursively filter tree items"""
            if not search_text:
                item.setHidden(False)
                return True
            
            # Check if this item or any child matches
            matches = False
            
            # Check item text
            if search_text in item.text(0).lower():
                matches = True
            
            # Check children
            child_matches = False
            for i in range(item.childCount()):
                child = item.child(i)
                if filter_item(child):
                    child_matches = True
            
            # Show item if it or any child matches
            show_item = matches or child_matches
            item.setHidden(not show_item)
            
            return show_item
        
        # Filter from root
        for i in range(self.tree_widget.topLevelItemCount()):
            filter_item(self.tree_widget.topLevelItem(i))
    
    def update_stats(self):
        """Update selection statistics"""
        selected = sum(1 for item in self.file_checkboxes.values() 
                      if item.checkState(0) == Qt.CheckState.Checked)
        total = len(self.file_checkboxes)
        self.stats_label.setText(f"Selected: {selected}/{total}")
    
    def get_selected_files(self):
        """Get list of selected file paths"""
        selected_files = []
        for path, item in self.file_checkboxes.items():
            if item.checkState(0) == Qt.CheckState.Checked:
                selected_files.append(path)
        return selected_files
    
    def get_selected_extensions(self) -> Set[str]:
        """Get set of selected file extensions"""
        selected_extensions = set()
        for path, item in self.file_checkboxes.items():
            if item.checkState(0) == Qt.CheckState.Checked:
                ext = os.path.splitext(path)[1]
                if ext:
                    selected_extensions.add(ext.lower())
        return selected_extensions
    
    def get_selected_file_info(self):
        """Get detailed info of selected files"""
        selected_files = []
        for path, item in self.file_checkboxes.items():
            if item.checkState(0) == Qt.CheckState.Checked:
                # Find the file info in parent's file list
                for file_info in self.files_list:
                    if file_info.get('relative_path') == path or file_info.get('path') == path:
                        selected_files.append(file_info)
                        break
        return selected_files
    
    def apply_selection(self):
        """Apply the file selection and process immediately"""
        selected_files = self.get_selected_files()
        
        if not selected_files:
            QMessageBox.warning(self, "Warning", "No files selected!")
            return
        
        # Get selected extensions
        selected_extensions = self.get_selected_extensions()
        
        # Store selected file info for direct processing
        self.selected_file_info = self.get_selected_file_info()
        
        # Close dialog and let parent process the files
        self.accept()
    
    def export_tree(self):
        """Export tree structure to clipboard"""
        selected_files = self.get_selected_files()
        
        tree_text = f"Selected Files ({len(selected_files)}):\n"
        tree_text += "=" * 40 + "\n"
        
        for file_path in sorted(selected_files):
            tree_text += f"✅ {file_path}\n"
        
        try:
            # Copy to clipboard
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(tree_text)
            QMessageBox.information(self, "Success", "Tree structure copied to clipboard!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to copy: {str(e)}")