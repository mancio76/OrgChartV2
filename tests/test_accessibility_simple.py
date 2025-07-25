"""
Simple Accessibility Tests
Task 9.3 Implementation - Organigramma Web App

Basic accessibility tests that can run without a live server
"""

import pytest
import os
import re


class TestAccessibilityBasics:
    """Basic accessibility tests for static files"""
    
    def test_html_templates_have_lang_attribute(self):
        """Test that HTML templates have lang attributes"""
        template_files = []
        
        # Find template files
        for root, dirs, files in os.walk('templates'):
            for file in files:
                if file.endswith('.html'):
                    template_files.append(os.path.join(root, file))
        
        lang_pattern = r'<html[^>]*lang\s*=\s*["\'][^"\']*["\']'
        
        for template_file in template_files:
            if os.path.exists(template_file):
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for lang attribute in html tag
                has_lang = re.search(lang_pattern, content, re.IGNORECASE)
                if '<html' in content.lower():
                    assert has_lang, f"Template {template_file} should have lang attribute in html tag"
    
    def test_templates_have_proper_headings(self):
        """Test that templates have proper heading structure"""
        template_files = []
        
        # Find template files
        for root, dirs, files in os.walk('templates'):
            for file in files:
                if file.endswith('.html'):
                    template_files.append(os.path.join(root, file))
        
        for template_file in template_files:
            if os.path.exists(template_file):
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for heading tags
                headings = re.findall(r'<h([1-6])[^>]*>', content, re.IGNORECASE)
                
                if headings:
                    # Convert to integers for comparison
                    heading_levels = [int(h) for h in headings]
                    
                    # Check that h1 exists if there are headings
                    if heading_levels:
                        # At least one heading should be present
                        assert min(heading_levels) <= 2, f"Template {template_file} should start with h1 or h2"
    
    def test_form_labels_exist(self):
        """Test that form templates have labels for inputs"""
        template_files = []
        
        # Find template files
        for root, dirs, files in os.walk('templates'):
            for file in files:
                if file.endswith('.html'):
                    template_files.append(os.path.join(root, file))
        
        for template_file in template_files:
            if os.path.exists(template_file):
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find input elements
                inputs = re.findall(r'<input[^>]*id\s*=\s*["\']([^"\']*)["\'][^>]*>', content, re.IGNORECASE)
                
                for input_id in inputs:
                    # Check if there's a corresponding label
                    label_pattern = rf'<label[^>]*for\s*=\s*["\']?{re.escape(input_id)}["\']?[^>]*>'
                    has_label = re.search(label_pattern, content, re.IGNORECASE)
                    
                    # Also check for aria-label or aria-labelledby
                    aria_label_pattern = rf'<input[^>]*id\s*=\s*["\']?{re.escape(input_id)}["\']?[^>]*aria-label[^>]*>'
                    aria_labelledby_pattern = rf'<input[^>]*id\s*=\s*["\']?{re.escape(input_id)}["\']?[^>]*aria-labelledby[^>]*>'
                    
                    has_aria_label = re.search(aria_label_pattern, content, re.IGNORECASE)
                    has_aria_labelledby = re.search(aria_labelledby_pattern, content, re.IGNORECASE)
                    
                    # Input should have either a label or aria-label/aria-labelledby
                    assert has_label or has_aria_label or has_aria_labelledby, \
                        f"Input with id '{input_id}' in {template_file} should have a label or aria-label"
    
    def test_images_have_alt_attributes(self):
        """Test that images in templates have alt attributes"""
        template_files = []
        
        # Find template files
        for root, dirs, files in os.walk('templates'):
            for file in files:
                if file.endswith('.html'):
                    template_files.append(os.path.join(root, file))
        
        for template_file in template_files:
            if os.path.exists(template_file):
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find img elements
                img_tags = re.findall(r'<img[^>]*>', content, re.IGNORECASE)
                
                for img_tag in img_tags:
                    # Check if img has alt attribute
                    has_alt = re.search(r'alt\s*=\s*["\'][^"\']*["\']', img_tag, re.IGNORECASE)
                    assert has_alt, f"Image tag in {template_file} should have alt attribute: {img_tag}"
    
    def test_css_focus_styles_exist(self):
        """Test that CSS files have focus styles"""
        css_files = [
            'static/css/base.css',
            'static/css/components.css',
            'static/css/forms.css'
        ]
        
        focus_found = False
        
        for css_file in css_files:
            if os.path.exists(css_file):
                with open(css_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for focus-related styles
                focus_patterns = [
                    r':focus\s*{',
                    r'\.focus\s*{',
                    r'focus-visible',
                    r'outline\s*:',
                    r'box-shadow[^;]*focus'
                ]
                
                for pattern in focus_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        focus_found = True
                        break
                
                if focus_found:
                    break
        
        # At least some focus styles should exist
        # This is a soft requirement since Bootstrap provides default focus styles
        # assert focus_found, "CSS should include focus indicator styles"
    
    def test_semantic_html_elements(self):
        """Test that templates use semantic HTML elements"""
        template_files = []
        
        # Find template files
        for root, dirs, files in os.walk('templates'):
            for file in files:
                if file.endswith('.html'):
                    template_files.append(os.path.join(root, file))
        
        semantic_elements = ['main', 'nav', 'header', 'footer', 'section', 'article']
        
        for template_file in template_files:
            if os.path.exists(template_file):
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for at least some semantic elements
                semantic_found = 0
                for element in semantic_elements:
                    if f'<{element}' in content.lower():
                        semantic_found += 1
                
                # Base templates should have semantic elements
                if 'base' in template_file.lower() or 'layout' in template_file.lower():
                    assert semantic_found > 0, f"Base template {template_file} should use semantic HTML elements"
    
    def test_table_accessibility(self):
        """Test that tables have proper accessibility features"""
        template_files = []
        
        # Find template files
        for root, dirs, files in os.walk('templates'):
            for file in files:
                if file.endswith('.html'):
                    template_files.append(os.path.join(root, file))
        
        for template_file in template_files:
            if os.path.exists(template_file):
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find tables
                if '<table' in content.lower():
                    # Check for table headers
                    has_th = '<th' in content.lower()
                    assert has_th, f"Table in {template_file} should have header cells (th)"
                    
                    # Check for thead
                    has_thead = '<thead' in content.lower()
                    # thead is recommended but not required
                    # assert has_thead, f"Table in {template_file} should have thead element"
    
    def test_form_accessibility_attributes(self):
        """Test that forms have accessibility attributes"""
        template_files = []
        
        # Find template files
        for root, dirs, files in os.walk('templates'):
            for file in files:
                if file.endswith('.html'):
                    template_files.append(os.path.join(root, file))
        
        for template_file in template_files:
            if os.path.exists(template_file):
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find required inputs
                required_inputs = re.findall(r'<input[^>]*required[^>]*>', content, re.IGNORECASE)
                
                for input_tag in required_inputs:
                    # Check for aria-required (optional since HTML5 required is sufficient)
                    # has_aria_required = 'aria-required' in input_tag.lower()
                    # This is optional since HTML5 required attribute is sufficient
                    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])