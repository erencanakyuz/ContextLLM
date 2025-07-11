#!/usr/bin/env python3
"""
Enhanced Template Manager Dialog for PyQt6
Supports section-based template organization with professional UI
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QListWidget, QListWidgetItem, QTextEdit, QLineEdit, QComboBox,
    QPushButton, QLabel, QMessageBox, QSplitter, QGroupBox, QTreeWidget,
    QTreeWidgetItem, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon

from core.template_manager import template_manager

class TemplateManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🛠️ Professional Template Manager")
        self.setMinimumSize(1200, 800)
        self.selected_template = None
        self.current_section_id = None
        self.init_ui()
        self.load_sections()
        
    def init_ui(self):
        """Initialize the enhanced template manager UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("🎯 Expert Prompt Templates")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Template stats
        self.stats_label = QLabel()
        self.update_stats()
        header_layout.addWidget(self.stats_label)
        
        layout.addLayout(header_layout)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Browse tab
        self.create_browse_tab()
        
        # Create tab
        self.create_custom_tab()
        
        # Import/Export tab
        self.create_import_export_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_all)
        button_layout.addWidget(refresh_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("✅ Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
    def create_browse_tab(self):
        """Create enhanced browse templates tab with sections"""
        browse_widget = QWidget()
        layout = QVBoxLayout(browse_widget)
        
        # Search and filter
        search_layout = QHBoxLayout()
        
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("🔍 Search templates across all sections...")
        self.search_entry.textChanged.connect(self.search_templates)
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_entry)
        
        layout.addLayout(search_layout)
        
        # Main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: Sections tree
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        section_label = QLabel("📂 Template Categories")
        section_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        left_layout.addWidget(section_label)
        
        self.section_tree = QTreeWidget()
        self.section_tree.setHeaderLabel("Sections")
        self.section_tree.itemSelectionChanged.connect(self.on_section_selected)
        left_layout.addWidget(self.section_tree)
        
        main_splitter.addWidget(left_panel)
        
        # Middle panel: Template list
        middle_panel = QWidget()
        middle_layout = QVBoxLayout(middle_panel)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        
        template_label = QLabel("📝 Templates")
        template_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        middle_layout.addWidget(template_label)
        
        self.template_list = QListWidget()
        self.template_list.itemSelectionChanged.connect(self.on_template_selected)
        middle_layout.addWidget(self.template_list)
        
        main_splitter.addWidget(middle_panel)
        
        # Right panel: Preview
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Preview header
        preview_header = QHBoxLayout()
        self.preview_label = QLabel("💡 Select a template to preview")
        self.preview_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        preview_header.addWidget(self.preview_label)
        preview_header.addStretch()
        
        right_layout.addLayout(preview_header)
        
        # Template info
        self.template_info = QLabel()
        self.template_info.setWordWrap(True)
        self.template_info.setStyleSheet("color: gray; font-style: italic; padding: 5px;")
        right_layout.addWidget(self.template_info)
        
        # Preview content
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont("Consolas", 10))
        right_layout.addWidget(self.preview_text)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.select_btn = QPushButton("✅ Select & Use")
        self.select_btn.setEnabled(False)
        self.select_btn.clicked.connect(self.select_template)
        button_layout.addWidget(self.select_btn)
        
        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.setEnabled(False)
        self.edit_btn.clicked.connect(self.edit_template)
        button_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.delete_template)
        button_layout.addWidget(self.delete_btn)
        
        right_layout.addLayout(button_layout)
        
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([250, 300, 500])
        
        layout.addWidget(main_splitter)
        self.tab_widget.addTab(browse_widget, "📚 Browse Templates")
        
    def create_custom_tab(self):
        """Create enhanced custom template creation tab"""
        custom_widget = QWidget()
        layout = QVBoxLayout(custom_widget)
        
        # Template info
        info_group = QGroupBox("📝 Template Information")
        info_layout = QVBoxLayout(info_group)
        
        # Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_entry = QLineEdit()
        self.name_entry.setPlaceholderText("Enter descriptive template name...")
        name_layout.addWidget(self.name_entry)
        info_layout.addLayout(name_layout)
        
        # Description
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Description:"))
        self.description_entry = QLineEdit()
        self.description_entry.setPlaceholderText("Brief description of what this template does...")
        desc_layout.addWidget(self.description_entry)
        info_layout.addLayout(desc_layout)
        
        # Section
        section_layout = QHBoxLayout()
        section_layout.addWidget(QLabel("Category:"))
        self.section_combo = QComboBox()
        self.section_combo.setEditable(True)
        self.update_section_combo()
        section_layout.addWidget(self.section_combo)
        info_layout.addLayout(section_layout)
        
        layout.addWidget(info_group)
        
        # Content
        content_group = QGroupBox("📄 Template Content")
        content_layout = QVBoxLayout(content_group)
        
        # Tips
        tips_frame = QFrame()
        tips_frame.setStyleSheet("background-color: #f0f8ff; border: 1px solid #ccc; border-radius: 4px;")
        tips_layout = QVBoxLayout(tips_frame)
        
        tips_label = QLabel("💡 Expert Template Tips:")
        tips_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        tips_layout.addWidget(tips_label)
        
        tips_text = QLabel("""• Start with role definition: "You are an expert [role] with [experience]..."
• Use structured sections with clear headers (🔍 Analysis:, ⚡ Performance:, etc.)
• Include specific instructions for output format
• Add verification steps to prevent hallucinations
• Use {user_input} placeholder for dynamic content""")
        tips_text.setWordWrap(True)
        tips_text.setStyleSheet("margin: 5px; font-size: 9pt;")
        tips_layout.addWidget(tips_text)
        
        content_layout.addWidget(tips_frame)
        
        self.content_text = QTextEdit()
        self.content_text.setFont(QFont("Consolas", 11))
        self.content_text.setPlainText("""You are an expert [ROLE] with 15+ years of experience in [DOMAIN].

Please analyze the following content with focus on:

🔍 **Analysis Framework:**
- [Specific analysis points]
- [Key evaluation criteria]
- [Quality metrics to assess]

⚡ **Key Recommendations:**
- [Actionable suggestions]
- [Best practices to follow]
- [Common pitfalls to avoid]

📊 **Output Format:**
- Provide specific, actionable feedback
- Include examples where applicable
- Prioritize critical issues

Content to analyze: {user_input}""")
        content_layout.addWidget(self.content_text)
        
        layout.addWidget(content_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Save Template")
        save_btn.clicked.connect(self.save_template)
        button_layout.addWidget(save_btn)
        
        clear_btn = QPushButton("🗑️ Clear Form")
        clear_btn.clicked.connect(self.clear_form)
        button_layout.addWidget(clear_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.tab_widget.addTab(custom_widget, "➕ Create Custom")
        
    def create_import_export_tab(self):
        """Create import/export tab for template management"""
        import_widget = QWidget()
        layout = QVBoxLayout(import_widget)
        
        # Export section
        export_group = QGroupBox("📤 Export Templates")
        export_layout = QVBoxLayout(export_group)
        
        export_label = QLabel("Export individual templates as JSON files for backup or sharing:")
        export_layout.addWidget(export_label)
        
        export_btn_layout = QHBoxLayout()
        self.export_template_btn = QPushButton("📄 Export Selected Template")
        self.export_template_btn.setEnabled(False)
        self.export_template_btn.clicked.connect(self.export_template)
        export_btn_layout.addWidget(self.export_template_btn)
        export_btn_layout.addStretch()
        
        export_layout.addLayout(export_btn_layout)
        layout.addWidget(export_group)
        
        # Import section
        import_group = QGroupBox("📥 Import Templates")
        import_layout = QVBoxLayout(import_group)
        
        import_label = QLabel("Import templates from JSON files:")
        import_layout.addWidget(import_label)
        
        import_btn_layout = QHBoxLayout()
        import_btn = QPushButton("📁 Import Template File")
        import_btn.clicked.connect(self.import_template)
        import_btn_layout.addWidget(import_btn)
        import_btn_layout.addStretch()
        
        import_layout.addLayout(import_btn_layout)
        layout.addWidget(import_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(import_widget, "⚙️ Import/Export")
    
    def load_sections(self):
        """Load sections into the tree"""
        self.section_tree.clear()
        sections = template_manager.get_all_sections()
        
        for section in sections:
            item = QTreeWidgetItem()
            item.setText(0, f"{section['name']} ({section['template_count']})")
            item.setData(0, Qt.ItemDataRole.UserRole, section['id'])
            self.section_tree.addTopLevelItem(item)
    
    def update_section_combo(self):
        """Update section combo for custom template creation"""
        self.section_combo.clear()
        sections = template_manager.get_all_sections()
        
        for section in sections:
            self.section_combo.addItem(section['name'], section['id'])
        
        # Add custom option
        self.section_combo.addItem("custom", "custom")
    
    def on_section_selected(self):
        """Handle section selection"""
        current_item = self.section_tree.currentItem()
        if not current_item:
            return
        
        self.current_section_id = current_item.data(0, Qt.ItemDataRole.UserRole)
        self.load_templates_for_section()
    
    def load_templates_for_section(self):
        """Load templates for selected section"""
        if not self.current_section_id:
            return
        
        self.template_list.clear()
        templates = template_manager.get_section_templates(self.current_section_id)
        
        for template in templates:
            item = QListWidgetItem()
            item.setText(template['name'])
            item.setData(Qt.ItemDataRole.UserRole, template)
            self.template_list.addItem(item)
    
    def on_template_selected(self):
        """Handle template selection"""
        current_item = self.template_list.currentItem()
        if not current_item:
            self.clear_preview()
            return
        
        template = current_item.data(Qt.ItemDataRole.UserRole)
        self.show_template_preview(template)
        
        # Enable buttons
        self.select_btn.setEnabled(True)
        self.edit_btn.setEnabled(True)
        self.delete_btn.setEnabled(template.get('section_id') == 'custom')  # Only allow deleting custom templates
        self.export_template_btn.setEnabled(True)
    
    def show_template_preview(self, template):
        """Show template preview"""
        self.preview_label.setText(f"📝 {template['name']}")
        
        # Show template info
        section_name = template.get('section_name', 'Unknown')
        description = template.get('description', 'No description available.')
        info_text = f"Category: {section_name}\nDescription: {description}"
        self.template_info.setText(info_text)
        
        # Show template content
        self.preview_text.setPlainText(template.get('template', ''))
    
    def clear_preview(self):
        """Clear preview area"""
        self.preview_label.setText("💡 Select a template to preview")
        self.template_info.setText("")
        self.preview_text.clear()
        
        # Disable buttons
        self.select_btn.setEnabled(False)
        self.edit_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.export_template_btn.setEnabled(False)
    
    def search_templates(self):
        """Search templates across all sections"""
        query = self.search_entry.text()
        if not query:
            # Clear search, reload current section
            if self.current_section_id:
                self.load_templates_for_section()
            return
        
        # Search across all templates
        results = template_manager.search_templates(query)
        
        self.template_list.clear()
        for template in results:
            item = QListWidgetItem()
            item.setText(f"{template['name']} ({template['section_name']})")
            item.setData(Qt.ItemDataRole.UserRole, template)
            self.template_list.addItem(item)
    
    def select_template(self):
        """Select template and close dialog"""
        current_item = self.template_list.currentItem()
        if current_item:
            self.selected_template = current_item.data(Qt.ItemDataRole.UserRole)
            self.accept()
    
    def edit_template(self):
        """Edit selected template"""
        current_item = self.template_list.currentItem()
        if not current_item:
            return
        
        template = current_item.data(Qt.ItemDataRole.UserRole)
        
        # Switch to create tab and populate with template data
        self.tab_widget.setCurrentIndex(1)  # Create tab
        
        self.name_entry.setText(template['name'])
        self.description_entry.setText(template.get('description', ''))
        self.content_text.setPlainText(template.get('template', ''))
        
        # Set section
        section_id = template.get('section_id', 'custom')
        index = self.section_combo.findData(section_id)
        if index >= 0:
            self.section_combo.setCurrentIndex(index)
    
    def delete_template(self):
        """Delete selected template (custom only)"""
        current_item = self.template_list.currentItem()
        if not current_item:
            return
        
        template = current_item.data(Qt.ItemDataRole.UserRole)
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, 
            "Delete Template",
            f"Are you sure you want to delete '{template['name']}'?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            section_id = template.get('section_id')
            template_id = template.get('id')
            
            if template_manager.delete_template(section_id, template_id):
                QMessageBox.information(self, "Success", "Template deleted successfully!")
                self.refresh_all()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete template.")
    
    def save_template(self):
        """Save custom template"""
        name = self.name_entry.text().strip()
        description = self.description_entry.text().strip()
        content = self.content_text.toPlainText().strip()
        section_id = self.section_combo.currentData() or self.section_combo.currentText()
        
        if not name or not content:
            QMessageBox.warning(self, "Validation Error", "Name and content are required.")
            return
        
        # Generate template ID
        template_id = name.lower().replace(' ', '_').replace('-', '_')
        template_id = ''.join(c for c in template_id if c.isalnum() or c == '_')
        
        if template_manager.add_custom_template(section_id, template_id, name, description, content):
            QMessageBox.information(self, "Success", "Template saved successfully!")
            self.clear_form()
            self.refresh_all()
        else:
            QMessageBox.warning(self, "Error", "Failed to save template.")
    
    def clear_form(self):
        """Clear create form"""
        self.name_entry.clear()
        self.description_entry.clear()
        self.content_text.clear()
        self.section_combo.setCurrentIndex(0)
        
        # Clear previous template from the list when adding new one
        if hasattr(self, 'template_list') and self.template_list:
            self.template_list.clearSelection()
    
    def export_template(self):
        """Export selected template"""
        current_item = self.template_list.currentItem()
        if not current_item:
            return
        
        template = current_item.data(Qt.ItemDataRole.UserRole)
        
        from PyQt6.QtWidgets import QFileDialog
        import json
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Template",
            f"{template['name']}.json",
            "JSON Files (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(template, f, indent=2, ensure_ascii=False)
                QMessageBox.information(self, "Success", f"Template exported to {filename}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to export template: {str(e)}")
    
    def import_template(self):
        """Import template from file"""
        from PyQt6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Import Template",
            "",
            "JSON Files (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if template_manager.import_template(content):
                    QMessageBox.information(self, "Success", "Template imported successfully!")
                    self.refresh_all()
                else:
                    QMessageBox.warning(self, "Error", "Failed to import template.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to import template: {str(e)}")
    
    def refresh_all(self):
        """Refresh all data"""
        self.load_sections()
        self.update_section_combo()
        self.update_stats()
        self.clear_preview()
        self.template_list.clear()
    
    def update_stats(self):
        """Update template statistics"""
        stats = template_manager.get_template_stats()
        self.stats_label.setText(
            f"📊 {stats['total_sections']} categories • {stats['total_templates']} templates"
        )