#!/usr/bin/env python3
"""
Template Manager Module
Manages prompt templates for LLM context building.
Enhanced to support section-based template structure.
"""

import json
import os
from typing import Dict, List, Optional, Tuple

class TemplateManager:
    def __init__(self):
        self.templates_file = os.path.join(os.path.dirname(__file__), '..', 'assets', 'prompt_templates.json')
        self.templates = self.load_templates()
    
    def load_templates(self) -> Dict:
        """Load templates from JSON file"""
        if os.path.exists(self.templates_file):
            try:
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Return empty dict if file doesn't exist or is corrupted
        return {}
    
    def save_templates(self) -> bool:
        """Save templates to JSON file"""
        try:
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False
    
    def get_all_sections(self) -> List[Dict]:
        """Get all sections with their metadata"""
        sections = []
        for section_id, section_data in self.templates.items():
            section_info = {
                'id': section_id,
                'name': section_data.get('name', section_id),
                'description': section_data.get('description', ''),
                'template_count': len(section_data.get('templates', {}))
            }
            sections.append(section_info)
        return sections
    
    def get_section_templates(self, section_id: str) -> List[Dict]:
        """Get all templates in a specific section"""
        section = self.templates.get(section_id, {})
        templates = section.get('templates', {})
        
        template_list = []
        for template_id, template_data in templates.items():
            template_info = {
                'id': template_id,
                'name': template_data.get('name', template_id),
                'description': template_data.get('description', ''),
                'template': template_data.get('template', ''),
                'section_id': section_id,
                'section_name': section.get('name', section_id)
            }
            template_list.append(template_info)
        
        return template_list
    
    def get_template(self, section_id: str, template_id: str) -> Optional[Dict]:
        """Get a specific template by section and template ID"""
        section = self.templates.get(section_id, {})
        templates = section.get('templates', {})
        template_data = templates.get(template_id)
        
        if template_data:
            return {
                'id': template_id,
                'name': template_data.get('name', template_id),
                'description': template_data.get('description', ''),
                'template': template_data.get('template', ''),
                'section_id': section_id,
                'section_name': section.get('name', section_id)
            }
        return None
    
    def search_templates(self, query: str) -> List[Dict]:
        """Search templates across all sections"""
        results = []
        query_lower = query.lower()
        
        for section_id, section_data in self.templates.items():
            section_name = section_data.get('name', '')
            templates = section_data.get('templates', {})
            
            for template_id, template_data in templates.items():
                # Search in name, description, and template content
                searchable_text = f"{template_data.get('name', '')} {template_data.get('description', '')} {template_data.get('template', '')}"
                
                if query_lower in searchable_text.lower():
                    result = {
                        'id': template_id,
                        'name': template_data.get('name', template_id),
                        'description': template_data.get('description', ''),
                        'template': template_data.get('template', ''),
                        'section_id': section_id,
                        'section_name': section_name,
                        'relevance_score': searchable_text.lower().count(query_lower)
                    }
                    results.append(result)
        
        # Sort by relevance (number of matches)
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return results
    
    def add_custom_template(self, section_id: str, template_id: str, name: str, 
                          description: str, template_text: str) -> bool:
        """Add a custom template to a section (replaces existing if same ID)"""
        # Initialize section if it doesn't exist
        if section_id not in self.templates:
            self.templates[section_id] = {
                'name': f'Custom - {section_id}',
                'description': 'Custom templates',
                'templates': {}
            }
        
        # Initialize templates dict if it doesn't exist
        if 'templates' not in self.templates[section_id]:
            self.templates[section_id]['templates'] = {}
        
        # Add the new template (will replace if same ID exists)
        self.templates[section_id]['templates'][template_id] = {
            'name': name,
            'description': description,
            'template': template_text
        }
        
        return self.save_templates()
    
    def delete_template(self, section_id: str, template_id: str) -> bool:
        """Delete a template from a section"""
        if section_id in self.templates:
            templates = self.templates[section_id].get('templates', {})
            if template_id in templates:
                del templates[template_id]
                return self.save_templates()
        return False
    
    def update_template(self, section_id: str, template_id: str, **kwargs) -> bool:
        """Update template fields"""
        if section_id in self.templates:
            templates = self.templates[section_id].get('templates', {})
            if template_id in templates:
                template_data = templates[template_id]
                for key, value in kwargs.items():
                    if key in ['name', 'description', 'template']:
                        template_data[key] = value
                return self.save_templates()
        return False
    
    def get_template_suggestions(self, context: str = '') -> List[Dict]:
        """Get template suggestions based on context"""
        suggestions = []
        context_lower = context.lower()
        
        # Keyword-based suggestions
        keyword_mapping = {
            'code': ['coding_excellence'],
            'security': ['coding_excellence'],
            'review': ['coding_excellence'],
            'bug': ['coding_excellence'],
            'creative': ['creative_writing'],
            'story': ['creative_writing'],
            'write': ['creative_writing'],
            'research': ['analysis_research'],
            'analyze': ['analysis_research'],
            'data': ['analysis_research'],
            'professional': ['professional_tone'],
            'neutral': ['professional_tone'],
            'fact': ['accuracy_hallucination'],
            'verify': ['accuracy_hallucination'],
            'think': ['advanced_reasoning'],
            'reason': ['advanced_reasoning']
        }
        
        for keyword, section_ids in keyword_mapping.items():
            if keyword in context_lower:
                for section_id in section_ids:
                    if section_id in self.templates:
                        section_templates = self.get_section_templates(section_id)
                        suggestions.extend(section_templates[:2])  # Add top 2 from each relevant section
        
        # If no context matches, suggest popular templates
        if not suggestions:
            popular_templates = [
                ('accuracy_hallucination', 'search_before_answer'),
                ('professional_tone', 'stop_sycophancy'),
                ('advanced_reasoning', 'tree_of_thought'),
                ('coding_excellence', 'henry_coding')
            ]
            
            for section_id, template_id in popular_templates:
                template = self.get_template(section_id, template_id)
                if template:
                    suggestions.append(template)
        
        return suggestions[:6]  # Return max 6 suggestions
    
    def get_template_stats(self) -> Dict:
        """Get statistics about templates"""
        stats = {
            'total_sections': len(self.templates),
            'total_templates': 0,
            'sections': {}
        }
        
        for section_id, section_data in self.templates.items():
            template_count = len(section_data.get('templates', {}))
            stats['total_templates'] += template_count
            stats['sections'][section_id] = {
                'name': section_data.get('name', section_id),
                'template_count': template_count
            }
        
        return stats
    
    def export_template(self, section_id: str, template_id: str) -> Optional[str]:
        """Export template as JSON string"""
        template = self.get_template(section_id, template_id)
        if template:
            try:
                return json.dumps(template, indent=2, ensure_ascii=False)
            except:
                return None
        return None
    
    def import_template(self, json_data: str, target_section_id: str = 'custom') -> bool:
        """Import template from JSON string"""
        try:
            template_data = json.loads(json_data)
            return self.add_custom_template(
                target_section_id,
                template_data.get('id', 'imported_template'),
                template_data.get('name', 'Imported Template'),
                template_data.get('description', 'Imported from JSON'),
                template_data.get('template', '')
            )
        except:
            return False
    
    # Legacy methods for backward compatibility
    def get_templates_by_category(self) -> Dict[str, List[Dict]]:
        """Legacy method - maps sections to categories"""
        categories = {}
        for section_id, section_data in self.templates.items():
            category_name = section_data.get('name', section_id)
            categories[category_name] = self.get_section_templates(section_id)
        return categories
    
    def get_all_templates(self) -> List[Dict]:
        """Legacy method - get all templates flattened"""
        all_templates = []
        for section_id in self.templates:
            all_templates.extend(self.get_section_templates(section_id))
        return all_templates

# Global instance for backward compatibility
template_manager = TemplateManager() 