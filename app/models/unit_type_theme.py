"""
Unit Type Theme model
"""

import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from app.models.base import BaseModel, ValidationError


@dataclass
class UnitTypeTheme(BaseModel):
    """Unit Type Theme model for customizing unit type appearance"""
    
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    
    # Visual Properties
    icon_class: str = "diagram-2"
    emoji_fallback: str = "🏛️"
    
    # Color Scheme
    primary_color: str = "#0dcaf0"
    secondary_color: str = "#f0fdff"
    text_color: str = "#0dcaf0"
    border_color: Optional[str] = None
    
    # Layout Properties
    border_width: int = 2
    border_style: str = "solid"
    background_gradient: Optional[str] = None
    
    # CSS Generation
    css_class_suffix: str = "organizational"
    hover_shadow_color: Optional[str] = None
    hover_shadow_intensity: float = 0.25
    
    # Display Properties
    display_label: str = ""
    display_label_plural: Optional[str] = None
    
    # Accessibility
    high_contrast_mode: bool = False
    
    # Metadata
    is_default: bool = False
    is_active: bool = True
    created_by: Optional[str] = None
    
    # Computed fields (not stored in DB)
    usage_count: int = field(default=0, init=False)
    
    @property
    def computed_border_color(self) -> str:
        """Get border color, fallback to primary color"""
        return self.border_color or self.primary_color
    
    @property
    def computed_hover_shadow_color(self) -> str:
        """Get hover shadow color, fallback to primary color"""
        return self.hover_shadow_color or self.primary_color
    
    @property
    def computed_display_label_plural(self) -> str:
        """Get plural display label, fallback to singular + 's'"""
        if self.display_label_plural:
            return self.display_label_plural
        return f"{self.display_label}s" if self.display_label else ""
    
    def generate_css_class_name(self) -> str:
        """Generate CSS class name for this theme"""
        return f"unit-{self.css_class_suffix}"
    
    def to_css_variables(self) -> Dict[str, str]:
        """Generate CSS custom properties for this theme"""
        if not self.id:
            return {}
        
        return {
            f"--theme-{self.id}-primary": self.primary_color,
            f"--theme-{self.id}-secondary": self.secondary_color,
            f"--theme-{self.id}-text": self.text_color,
            f"--theme-{self.id}-border": self.computed_border_color,
            f"--theme-{self.id}-border-width": f"{self.border_width}px",
            f"--theme-{self.id}-hover-shadow": self.computed_hover_shadow_color,
        }
    
    def generate_css_rules(self) -> str:
        """Generate CSS rules for this theme"""
        class_name = self.generate_css_class_name()
        
        css_rules = []
        
        # Base styles
        base_rule = f"""
.{class_name} {{
    border: {self.border_width}px {self.border_style} {self.computed_border_color};
    background: linear-gradient(135deg, #ffffff 0%, {self.secondary_color} 100%);
}}"""
        css_rules.append(base_rule)
        
        # Hover effects
        hover_rule = f"""
.{class_name}:hover {{
    box-shadow: 0 1rem 2rem {self.computed_hover_shadow_color}{self.hover_shadow_intensity:02.0f};
    border-color: {self.primary_color};
}}"""
        css_rules.append(hover_rule)
        
        # Text color
        text_rule = f"""
.{class_name} .unit-name {{
    color: {self.text_color};
}}"""
        css_rules.append(text_rule)
        
        # Background gradient if specified
        if self.background_gradient:
            gradient_rule = f"""
.{class_name} {{
    background: {self.background_gradient};
}}"""
            css_rules.append(gradient_rule)
        
        return "\n".join(css_rules)
    
    def validate(self) -> List[ValidationError]:
        """Validate theme data"""
        errors = []
        
        # Required fields validation
        if not self.name or not self.name.strip():
            errors.append(ValidationError("name", "Nome del tema è obbligatorio"))
        
        if not self.display_label or not self.display_label.strip():
            errors.append(ValidationError("display_label", "Etichetta di visualizzazione è obbligatoria"))
        
        if not self.css_class_suffix or not self.css_class_suffix.strip():
            errors.append(ValidationError("css_class_suffix", "Suffisso classe CSS è obbligatorio"))
        
        # Color validation
        color_fields = [
            ("primary_color", self.primary_color),
            ("secondary_color", self.secondary_color),
            ("text_color", self.text_color),
        ]
        
        if self.border_color:
            color_fields.append(("border_color", self.border_color))
        
        if self.hover_shadow_color:
            color_fields.append(("hover_shadow_color", self.hover_shadow_color))
        
        for field_name, color_value in color_fields:
            if not self._is_valid_color(color_value):
                errors.append(ValidationError(field_name, f"Colore non valido: {color_value}"))
        
        # Icon class validation
        if not self._is_valid_icon_class(self.icon_class):
            errors.append(ValidationError("icon_class", f"Classe icona non valida: {self.icon_class}"))
        
        # CSS class suffix validation
        if not self._is_valid_css_class_suffix(self.css_class_suffix):
            errors.append(ValidationError("css_class_suffix", "Suffisso classe CSS deve contenere solo lettere, numeri e trattini"))
        
        # Border width validation
        if self.border_width < 0 or self.border_width > 20:
            errors.append(ValidationError("border_width", "Larghezza bordo deve essere tra 0 e 20 pixel"))
        
        # Border style validation
        valid_border_styles = ["solid", "dashed", "dotted", "double", "groove", "ridge", "inset", "outset"]
        if self.border_style not in valid_border_styles:
            errors.append(ValidationError("border_style", f"Stile bordo non valido. Valori consentiti: {', '.join(valid_border_styles)}"))
        
        # Hover shadow intensity validation
        if self.hover_shadow_intensity < 0 or self.hover_shadow_intensity > 1:
            errors.append(ValidationError("hover_shadow_intensity", "Intensità ombra hover deve essere tra 0 e 1"))
        
        # Background gradient validation
        if self.background_gradient and not self._is_valid_css_gradient(self.background_gradient):
            errors.append(ValidationError("background_gradient", "Gradiente CSS non valido"))
        
        return errors
    
    def _is_valid_color(self, color: str) -> bool:
        """Validate color format (hex, rgb, rgba, hsl, hsla, named colors)"""
        if not color:
            return False
        
        color = color.strip().lower()
        
        # Hex colors
        if re.match(r'^#([0-9a-f]{3}|[0-9a-f]{6})$', color):
            return True
        
        # RGB/RGBA colors - validate ranges
        rgb_match = re.match(r'^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([0-9.]+))?\s*\)$', color)
        if rgb_match:
            r, g, b, a = rgb_match.groups()
            if (0 <= int(r) <= 255 and 0 <= int(g) <= 255 and 0 <= int(b) <= 255):
                if a is None or (0 <= float(a) <= 1):
                    return True
        
        # HSL/HSLA colors - validate ranges
        hsl_match = re.match(r'^hsla?\(\s*(\d+)\s*,\s*(\d+)%\s*,\s*(\d+)%\s*(?:,\s*([0-9.]+))?\s*\)$', color)
        if hsl_match:
            h, s, l, a = hsl_match.groups()
            if (0 <= int(h) <= 360 and 0 <= int(s) <= 100 and 0 <= int(l) <= 100):
                if a is None or (0 <= float(a) <= 1):
                    return True
        
        # Named colors (basic set)
        named_colors = {
            'black', 'white', 'red', 'green', 'blue', 'yellow', 'cyan', 'magenta',
            'gray', 'grey', 'orange', 'purple', 'pink', 'brown', 'transparent'
        }
        if color in named_colors:
            return True
        
        return False
    
    def _is_valid_icon_class(self, icon_class: str) -> bool:
        """Validate Bootstrap icon class format"""
        if not icon_class:
            return False
        
        # Bootstrap icons are typically alphanumeric with hyphens
        return re.match(r'^[a-z0-9-]+$', icon_class.strip()) is not None
    
    def _is_valid_css_class_suffix(self, suffix: str) -> bool:
        """Validate CSS class suffix format"""
        if not suffix:
            return False
        
        # CSS class names can contain letters, numbers, hyphens, and underscores
        # but should start with a letter
        return re.match(r'^[a-z][a-z0-9-_]*$', suffix.strip().lower()) is not None
    
    def _is_valid_css_gradient(self, gradient: str) -> bool:
        """Basic validation for CSS gradient syntax"""
        if not gradient:
            return False
        
        gradient = gradient.strip().lower()
        
        # Check for basic gradient functions
        gradient_functions = ['linear-gradient', 'radial-gradient', 'conic-gradient']
        return any(gradient.startswith(func + '(') and gradient.endswith(')') 
                  for func in gradient_functions)
    
    @classmethod
    def from_sqlite_row(cls, row):
        """Create UnitTypeTheme instance from SQLite row"""
        if row is None:
            return None
        
        data = dict(row)
        
        # Extract computed fields (init=False fields)
        computed_fields = {
            'usage_count': data.pop('usage_count', 0)
        }
        
        # Create instance with regular fields
        instance = cls.from_dict(data)
        
        # Set computed fields
        for field_name, value in computed_fields.items():
            if hasattr(instance, field_name):
                setattr(instance, field_name, int(value) if value is not None else 0)
        
        return instance
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = super().to_dict()
        
        # Add computed properties
        result['computed_border_color'] = self.computed_border_color
        result['computed_hover_shadow_color'] = self.computed_hover_shadow_color
        result['computed_display_label_plural'] = self.computed_display_label_plural
        result['css_class_name'] = self.generate_css_class_name()
        
        return result